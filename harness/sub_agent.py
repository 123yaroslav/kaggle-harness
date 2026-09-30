from typing import List

from langgraph.graph import StateGraph, START, END

from .schema import AgentState
from .skill import Skill
from .tool import extract_tool_call
from .utilities.now import now
from .utilities.extract_summary import extract_summary


system_prompt_template = """{role_prompt}

## Инструменты
{tool_desc_str}

## Как работать
Ты работаешь шагами. Каждое твое сообщение - либо один вызов инструмента, либо финальный ответ.

Вызов инструмента - блок в конце сообщения, перед ним одной-двумя фразами скажи, зачем он:
<tool name="read_file">{{"path": "journal.md"}}</tool>
Аргументы - JSON-объект внутри блока. Исключения - run_python и write_file: внутри блока сырой текст (код или содержимое файла), а остальные аргументы идут атрибутами тега:
<tool name="write_file" path="notes/plan.md">
текст файла
</tool>
Результат вызова придет следующим сообщением. Не выдумывай его сам и не вызывай больше одного инструмента за раз. На подзадачу у тебя не больше {max_turn_cnt} вызовов: трать их на то, без чего нельзя ответить.

Финальный ответ - сообщение без блока <tool>. Сначала по существу, в самом конце строка "ИТОГ:" и после нее 3-7 строк выжимки. Диспетчер читает только выжимку; полный ответ увидят те исполнители, которым диспетчер его передаст. Опирайся только на то, что видел в результатах инструментов и в контексте. Чего проверить не удалось - так и скажи, не додумывай.
{skill_block_str}"""

skill_block_template = """
=== МЕТОДИКА: {skill_nm} ===
Ниже методика, по которой нужно выполнить эту подзадачу. Она важнее твоих привычек по умолчанию. Если подзадачу нельзя выполнить, не нарушив методику, - скажи об этом в ответе, а не нарушай молча.

{skill_text}
=== КОНЕЦ МЕТОДИКИ: {skill_nm} ===
"""

user_prompt_template = """## Подзадача от диспетчера
{subtask_text}

## Рабочая папка
{file_tree_str}
{context_block_str}"""


class SubAgent(object):
    """
    Базовый класс субагента

    Субагент - это цикл "модель - инструмент": модель либо вызывает один из разрешенных ей инструментов,
    либо дает финальный ответ. Цикл собран как граф LangGraph из двух узлов:
        START -> think -> act -> think -> ... -> END
    think - вызов модели, act - вызов инструмента.

    Какие скиллы существуют, субагент не знает: текст скилла приходит в run и подмешивается
    в системный промпт на один шаг диспетчера
    """
    def __init__(self, agent_nm, agent_desc, role_prompt, tool_nm_list, llm_client, tool_storage, max_turn_cnt=10):
        """
        :param agent_nm: название субагента, по нему его вызывает диспетчер
        :param agent_desc: описание для каталога исполнителей - это все, что диспетчер знает о субагенте
        :param role_prompt: роль, постоянная часть системного промпта
        :param tool_nm_list: названия инструментов, которые разрешены этому субагенту
        :param llm_client: клиент модели с методом complete(system_prompt, user_prompt)
        :param tool_storage: общий набор инструментов
        :param max_turn_cnt: сколько вызовов инструментов можно сделать на одну подзадачу
        """
        self.agent_nm = agent_nm
        self.agent_desc = agent_desc
        self.role_prompt = role_prompt
        self.tool_nm_list = tool_nm_list
        self.llm_client = llm_client
        self.tool_storage = tool_storage
        self.max_turn_cnt = max_turn_cnt

    def get_name(self):
        return self.agent_nm

    def get_desc(self):
        return self.agent_desc

    def build_system_prompt(self, skill_list):
        skill_block_str = ''
        for skill in skill_list:
            skill_block_str += skill_block_template.format(skill_nm=skill.skill_nm, skill_text=skill.skill_text)

        return system_prompt_template.format(role_prompt=self.role_prompt,
                                             tool_desc_str=self.tool_storage.get_desc_str(self.tool_nm_list),
                                             max_turn_cnt=self.max_turn_cnt,
                                             skill_block_str=skill_block_str)

    def _build_graph(self, system_prompt, base_user_prompt, workspace, trace, verbose):
        def think_node(state: AgentState):
            # история хода целиком кладется в пользовательский промпт следующего вызова: клиенту модели достаточно
            # уметь complete(system, user), многоходовой диалог и function calling от провайдера не нужны
            user_prompt = base_user_prompt + state.turn_block_str
            if state.tool_call_cnt >= self.max_turn_cnt:
                user_prompt += "\n\nЛимит вызовов инструментов исчерпан. Дай финальный ответ по тому, что уже есть."

            answer_text = self.llm_client.complete(system_prompt=system_prompt, user_prompt=user_prompt)
            trace.add('model_answer', self.agent_nm, message_num=state.tool_call_cnt + 1, answer_text=answer_text)
            if verbose > 1:
                print(answer_text)

            try:
                tool_call = extract_tool_call(answer_text)
            except ValueError as exc:
                # блок <tool> есть, но не разобрался. Раньше такой ответ молча становился финальным
                return {'answer_text': answer_text, 'tool_nm': None, 'format_error': str(exc)}

            if tool_call is None:
                return {'answer_text': answer_text, 'tool_nm': None, 'format_error': None}

            tool_nm, attr_dict, body = tool_call
            return {'answer_text': answer_text, 'tool_nm': tool_nm, 'attr_dict': attr_dict, 'body': body, 'format_error': None}

        def route_after_think(state: AgentState):
            if state.tool_call_cnt >= self.max_turn_cnt:
                return END
            if state.tool_nm is None and state.format_error is None:
                return END
            return 'act'

        def act_node(state: AgentState):
            tool_call_cnt = state.tool_call_cnt + 1

            if state.format_error is not None:
                tool_nm = 'формат'
                result_text = f"Ошибка: {state.format_error}"
            else:
                tool_nm = state.tool_nm
                result_text = self.tool_storage.call(tool_nm=tool_nm, attr_dict=state.attr_dict, body=state.body,
                                                     workspace=workspace, tool_nm_list=self.tool_nm_list)

            trace.add('tool_call', self.agent_nm, tool_nm=tool_nm, attr_dict=state.attr_dict, body=state.body,
                      result_text=result_text)
            if verbose > 0:
                arg_str = ' '.join(f"{key}={value}" for key, value in state.attr_dict.items())
                body_str = ' '.join(state.body.split())[:90]
                print(f"{now()}: [{self.agent_nm}] инструмент {tool_nm} {arg_str} {body_str} -> {len(result_text)} симв.")
            if verbose > 1:
                print(result_text)

            turn_block_str = state.turn_block_str
            if tool_call_cnt == 1:
                turn_block_str = "\n\n## Ход работы"
            turn_block_str += (f"\n### Твое сообщение {tool_call_cnt}\n{state.answer_text.strip()}\n"
                               f"### Результат {tool_nm} (осталось вызовов: {self.max_turn_cnt - tool_call_cnt})\n{result_text}\n")

            return {'turn_block_str': turn_block_str, 'tool_call_cnt': tool_call_cnt,
                    'tool_nm': None, 'attr_dict': {}, 'body': '', 'format_error': None}

        graph = StateGraph(AgentState)
        graph.add_node('think', think_node)
        graph.add_node('act', act_node)
        graph.add_edge(START, 'think')
        graph.add_conditional_edges('think', route_after_think, {'act': 'act', END: END})
        graph.add_edge('act', 'think')

        return graph.compile()

    def run(self, subtask_text: str, context_text: str, skill_list: List[Skill], workspace, trace, verbose: int = 0) -> dict:
        """
        Запуск субагента на одной подзадаче

        :param subtask_text: текст подзадачи от диспетчера
        :param context_text: ответы прошлых шагов, которые диспетчер решил передать. Может быть пустым
        :param skill_list: список объектов Skill, которые подмешиваются в системный промпт
        :param workspace: объект Workspace
        :param trace: объект Trace, в него пишутся системный промпт со скиллами, ответы модели и вызовы инструментов
        :param verbose: уровень логирования
            - 0: без логирования
            - 1: кто вызван, с какими скиллами, какие инструменты дергал, итог
            - 2: плюс полные тексты промптов и ответов
        :return: словарь с ключами answer_text, summary_text, tool_call_cnt
        """
        system_prompt = self.build_system_prompt(skill_list)

        context_block_str = ''
        if len(context_text.strip()) > 0:
            context_block_str = f"\n## Ответы предыдущих шагов\n{context_text}"
        base_user_prompt = user_prompt_template.format(subtask_text=subtask_text,
                                                       file_tree_str=workspace.get_file_tree_str(),
                                                       context_block_str=context_block_str)

        skill_char_cnt = sum(len(skill.skill_text) for skill in skill_list)
        trace.add('agent_start', self.agent_nm, skill_nm_list=[skill.skill_nm for skill in skill_list],
                  skill_char_cnt=skill_char_cnt, subtask_text=subtask_text, system_prompt=system_prompt,
                  user_prompt=base_user_prompt)
        if verbose > 0:
            skill_nm_str = ', '.join(skill.skill_nm for skill in skill_list) if len(skill_list) > 0 else 'нет'
            print(f"{now()}: [{self.agent_nm}] вызван. Скиллы в системном промпте: {skill_nm_str} "
                  f"({skill_char_cnt} из {len(system_prompt)} символов)")
        if verbose > 1:
            print(system_prompt)
            print(base_user_prompt)

        app = self._build_graph(system_prompt=system_prompt, base_user_prompt=base_user_prompt,
                                workspace=workspace, trace=trace, verbose=verbose)
        # на один вызов инструмента уходит два узла
        res = app.invoke(AgentState(), config={'recursion_limit': 2 * self.max_turn_cnt + 10})

        answer_text = res['answer_text']
        tool_call_cnt = res['tool_call_cnt']
        summary_text = extract_summary(answer_text)

        # все, что инструменты за этот шаг записали в рабочую папку (вердикты, финальный выбор, новые прогоны),
        # дописываем к ответу от имени harness: диспетчер должен видеть факты, а не только слова исполнителя
        # на исчерпанном лимите модель иногда все равно присылает вызов инструмента. Он уже не выполняется,
        # и диспетчер должен это видеть: иначе такой текст приходит ему как обычный ответ
        if res['tool_nm'] is not None or res['format_error'] is not None:
            workspace.add_event(f"{self.agent_nm} исчерпал лимит в {self.max_turn_cnt} вызовов инструментов и финального ответа не дал: "
                                f"последний вызов не выполнен")
        event_list = workspace.pop_event_list()
        if len(event_list) > 0:
            fact_text = '\n'.join(f"[harness] {event}" for event in event_list)
            answer_text = f"{answer_text}\n\n{fact_text}"
            summary_text = f"{summary_text}\n{fact_text}"

        trace.add('agent_finish', self.agent_nm, tool_call_cnt=tool_call_cnt, summary_text=summary_text, fact_list=event_list)
        if verbose > 0:
            print(f"{now()}: [{self.agent_nm}] итог ({tool_call_cnt} вызовов инструментов): {summary_text}")

        return {'answer_text': answer_text, 'summary_text': summary_text, 'tool_call_cnt': tool_call_cnt}
