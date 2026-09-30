from langgraph.graph import StateGraph, START, END
from pydantic import ValidationError

from .schema import DispatcherAction, DispatchState, Step
from .trace import Trace
from .utilities.now import now
from .utilities.parse_json_answer import parse_json_answer
from .utilities.validation_error_text import validation_error_text


# Метапромпт диспетчера. Каталоги исполнителей и скиллов подставляются при запуске:
# чтобы добавить субагента или скилл, этот текст править не нужно
dispatcher_prompt_template = """Ты - диспетчер команды, которая участвует в ML-соревновании на Kaggle. Сам ты задачу не решаешь: не читаешь материалы, не пишешь код, не считаешь метрики и не судишь, какой прогон лучше. Инструментов у тебя нет. Твоя работа - понять, что нужно пользователю, разложить это на шаги, отдать каждый шаг подходящему исполнителю с подходящей методикой, прочитать результат и решить, что делать дальше.

## Исполнители
{agent_catalog_str}

## Скиллы
Скилл - это методика, которую harness на один шаг подмешивает исполнителю в системный промпт. Ты видишь только названия и описания, сам текст увидит исполнитель.
{skill_catalog_str}

## Как работать
1. Сначала план. На первом ходу составь план под конкретный запрос и дальше веди его в plan_list: план с прошлого хода тебе показывают, обнови его по итогам шага. Не гоняй полный цикл, если просят часть, и не зови исполнителя, которому на этом запросе нечего делать.
2. Один шаг - один исполнитель - одна проверяемая подзадача. Исполнитель не видит ни запроса пользователя, ни истории шагов. Он получает subtask_text, список файлов рабочей папки, ответы шагов из context_step_list целиком и свои инструменты, которыми сам читает файлы и считает. В subtask_text напиши, что сделать, какие условия из запроса пользователя важны для этого шага и что должно быть в ответе. Это постановка, а не подсказка: не пиши в ней выводы, к которым исполнитель должен прийти сам по своим данным и методике, и не повторяй то, что он и так увидит в контексте. Не сужай сам круг прогонов, которые исполнитель должен рассмотреть, если этого не требует запрос: список "претендентов", который ты составил по публичному скору, - это уже решение, а решения принимаешь не ты. Охват определяет исполнитель по своей методике. Обычно хватает 3-7 предложений. В context_step_list клади только те шаги, без которых исполнитель не справится.
3. Скилл подключай, когда его описание подходит к тому, что делается на шаге. Обычно это один скилл, редко два. Если подходящего нет - пустой список: лишняя методика только размывает промпт.
4. После каждого шага читай итог и пересматривай план. Строки "[harness]" в итоге - это факты, которые записал сам harness (вердикты, финальный выбор, новые прогоны), им можно верить больше, чем словам исполнителя. Если исполнитель ответил не по существу или уперся в ограничение - переформулируй подзадачу, добавь контекст или отдай другому, не повторяй ту же формулировку.
5. Порядок, который нельзя нарушать:
   - решения не принимаются, пока не собраны факты: если про соревнование или про состояние команды чего-то не хватает - сначала разведчик;
   - цифрам валидации можно верить только после инженера валидации: какая дорожка честная и какой у нее шум;
   - прогон не идет в финальный выбор без вердикта аудитора;
   - помогло ли изменение, что отправлять и что финалить, решает стратег - не ты и не публичный лидерборд.
6. Заканчивай, когда запрос выполнен или когда кончается бюджет шагов. В final_answer - короткий ответ пользователю: что сделано, что выбрано и почему, что осталось под вопросом. Ответы исполнителей целиком не пересказывай.

## Формат ответа
Только один JSON-объект, без текста вокруг:
{{
  "thought": "1-3 фразы: что уже известно и почему следующий шаг именно такой",
  "plan_list": ["оставшиеся шаги, коротко, начиная с текущего"],
  "action": "delegate или finish",
  "agent_nm": "название исполнителя (для delegate)",
  "skill_nm_list": ["названия скиллов или пустой список (для delegate)"],
  "subtask_text": "подзадача исполнителю (для delegate)",
  "context_step_list": [номера прошлых шагов, ответы которых нужно передать исполнителю (для delegate)],
  "final_answer": "ответ пользователю (для finish)"
}}"""

state_prompt_template = """## Запрос пользователя
{request_text}

## Соревнование
{competition_desc}

## Рабочая папка
{file_tree_str}

## Выполненные шаги
{step_block_str}

## Твой план с прошлого хода
{plan_block_str}

## Реестр прогонов
{run_table_str}

Осталось шагов: {step_left_cnt} из {max_step_cnt}.{harness_note_str}"""


class Dispatcher(object):
    """
    Корневой агент. Сам задачу не решает и инструментов не имеет: на каждом ходу смотрит на состояние
    (запрос, итоги шагов, свой прошлый план, реестр прогонов) и либо делегирует следующий шаг субагенту
    с выбранными скиллами, либо заканчивает.

    Цикл собран как граф LangGraph из двух узлов:
        START -> plan -> delegate -> plan -> ... -> END
    plan - ход модели-диспетчера, delegate - запуск субагента. Из plan три выхода: delegate (ход принят),
    снова plan (ответ не разобрался или не прошел проверку, ошибка уходит модели) и END
    """
    def __init__(self, llm_client, agent_list, skill_storage, max_step_cnt=10, skill_flg=True):
        """
        :param llm_client: клиент модели
        :param agent_list: список субагентов
        :param skill_storage: каталог скиллов
        :param max_step_cnt: бюджет делегирований на один запрос
        :param skill_flg: подмешивать ли тексты скиллов субагентам. False нужен только для сравнения "со скиллом / без":
            диспетчер выбирает скиллы как обычно, но в промпт субагента они не попадают
        """
        self.llm_client = llm_client
        self.agent_list = agent_list
        self.skill_storage = skill_storage
        self.max_step_cnt = max_step_cnt
        self.skill_flg = skill_flg

    def _get_agent(self, agent_nm):
        res = list(filter(lambda agent: agent.get_name() == agent_nm, self.agent_list))
        if len(res) > 0:
            return res[0]
        else:
            return None

    def build_system_prompt(self):
        agent_desc_list = []
        for agent in self.agent_list:
            agent_desc_list.append(f"- {agent.get_name()}: {agent.get_desc()}")

        return dispatcher_prompt_template.format(agent_catalog_str='\n'.join(agent_desc_list),
                                                 skill_catalog_str=self.skill_storage.get_catalog_str())

    def _build_state_prompt(self, state, workspace):
        if len(state.step_list) == 0:
            step_block_str = "(пока ничего)"
        else:
            step_desc_list = []
            for step in state.step_list:
                skill_nm_str = ', '.join(step.skill_nm_list) if len(step.skill_nm_list) > 0 else 'нет'
                step_desc_list.append(
                    f"Шаг {step.step_num}. {step.agent_nm}, скиллы: {skill_nm_str}\n"
                    f"подзадача: {step.subtask_text}\n"
                    f"итог: {step.summary_text}"
                )
            step_block_str = '\n\n'.join(step_desc_list)

        if len(state.plan_list) == 0:
            plan_block_str = "(плана еще нет)"
        else:
            plan_block_str = '\n'.join(f"{plan_num}. {plan_desc}" for plan_num, plan_desc in enumerate(state.plan_list, start=1))

        harness_note_str = ''
        if state.harness_note is not None:
            harness_note_str = f"\n\nHarness не принял твой прошлый ответ: {state.harness_note}"

        return state_prompt_template.format(request_text=state.request_text,
                                            competition_desc=workspace.competition.summary,
                                            file_tree_str=workspace.get_file_tree_str(),
                                            step_block_str=step_block_str,
                                            plan_block_str=plan_block_str,
                                            run_table_str=workspace.get_run_table_str(),
                                            step_left_cnt=self.max_step_cnt - len(state.step_list),
                                            max_step_cnt=self.max_step_cnt,
                                            harness_note_str=harness_note_str)

    def _check_action(self, action, step_list):
        # то, чего pydantic проверить не может: исполнитель, скиллы и шаги должны существовать.
        # Возвращает текст ошибки или None. Ошибка уходит диспетчеру следующим ходом, прогон из-за нее не падает
        if action.action == 'finish':
            return None

        if len(step_list) >= self.max_step_cnt:
            return "Бюджет шагов исчерпан, остался только finish"

        if self._get_agent(action.agent_nm) is None:
            return f"Исполнитель {action.agent_nm!r} не найден. Есть: {[agent.get_name() for agent in self.agent_list]}"

        skill_nm_list = self.skill_storage.get_skill_nm_list()
        for skill_nm in action.skill_nm_list:
            if skill_nm not in skill_nm_list:
                return f"Скилл {skill_nm!r} не найден. Есть: {skill_nm_list}"

        step_num_list = [step.step_num for step in step_list]
        for step_num in action.context_step_list:
            if step_num not in step_num_list:
                return f"В context_step_list указан шаг {step_num!r}, которого нет. Выполненные шаги: {step_num_list}"

        return None

    def _build_graph(self, workspace, trace, verbose):
        """
        Граф одного запроса. Собирается на каждый запрос заново: узлы замыкают рабочую папку и уровень логирования,
        в состоянии графа лежит только то, что меняется от хода к ходу
        """
        system_prompt = self.build_system_prompt()
        trace.add('dispatcher_prompt', 'dispatcher', system_prompt=system_prompt)
        if verbose > 1:
            print(system_prompt)

        def plan_node(state: DispatchState):
            turn_cnt = state.turn_cnt + 1
            state_prompt = self._build_state_prompt(state, workspace)
            if verbose > 1:
                print(state_prompt)

            answer_text = self.llm_client.complete(system_prompt=system_prompt, user_prompt=state_prompt)

            action = None
            try:
                action = DispatcherAction(**parse_json_answer(answer_text))
                harness_note = self._check_action(action, state.step_list)
            except ValidationError as exc:
                harness_note = f"ответ не прошел проверку формата - {validation_error_text(exc)}"
            except ValueError as exc:
                harness_note = str(exc)

            trace.add('dispatcher_turn', 'dispatcher', turn_cnt=turn_cnt, state_prompt=state_prompt,
                      answer_text=answer_text, harness_note=harness_note)
            if harness_note is not None:
                if verbose > 0:
                    print(f"{now()}: [dispatcher] ход {turn_cnt}: ответ не принят - {harness_note}")
                return {'turn_cnt': turn_cnt, 'action': None, 'harness_note': harness_note,
                        'bad_answer_cnt': state.bad_answer_cnt + 1}

            if verbose > 0:
                print(f"{now()}: [dispatcher] ход {turn_cnt}: {action.thought}")
                for plan_num, plan_desc in enumerate(action.plan_list, start=1):
                    print(f"    план {plan_num}: {plan_desc}")

            update = {'turn_cnt': turn_cnt, 'action': action, 'harness_note': None, 'bad_answer_cnt': 0,
                      'plan_list': action.plan_list}
            if action.action == 'finish':
                update['final_answer'] = action.final_answer
                if verbose > 0:
                    print(f"{now()}: [dispatcher] закончил, шагов: {len(state.step_list)}")

            return update

        def route_after_plan(state: DispatchState):
            if state.action is None:
                # два раза подряд даем исправиться, дальше смысла нет: модель не держит формат
                if state.bad_answer_cnt > 2:
                    return 'give_up'
                return 'plan'
            if state.action.action == 'finish':
                return END
            return 'delegate'

        def delegate_node(state: DispatchState):
            action = state.action
            agent = self._get_agent(action.agent_nm)
            step_num = len(state.step_list) + 1

            if verbose > 0:
                skill_nm_str = ', '.join(action.skill_nm_list) if len(action.skill_nm_list) > 0 else 'нет'
                print(f"{now()}: [dispatcher] шаг {step_num} -> {agent.get_name()}, скиллы: {skill_nm_str}, "
                      f"контекст: шаги {action.context_step_list}")
                print(f"    подзадача: {action.subtask_text}")

            if self.skill_flg:
                skill_list = [self.skill_storage.get(skill_nm) for skill_nm in action.skill_nm_list]
            else:
                skill_list = []
                if verbose > 0 and len(action.skill_nm_list) > 0:
                    print(f"{now()}: [dispatcher] скиллы отключены флагом --no-skills, {action.skill_nm_list} в промпт не попадут")

            # субагент получает ответы только тех шагов, которые выбрал диспетчер, и целиком, а не выжимкой
            context_text = ''
            for step in state.step_list:
                if step.step_num in action.context_step_list:
                    context_text += f"### Шаг {step.step_num}, {step.agent_nm}\n{step.answer_text}\n\n"

            trace.set_step(step_num)
            trace.add('delegate', 'dispatcher', agent_nm=agent.get_name(), skill_nm_list=action.skill_nm_list,
                      context_step_list=action.context_step_list)
            step_result = agent.run(subtask_text=action.subtask_text, context_text=context_text,
                                    skill_list=skill_list, workspace=workspace, trace=trace, verbose=verbose)
            trace.set_step(None)

            step = Step(step_num=step_num, agent_nm=agent.get_name(), skill_nm_list=action.skill_nm_list,
                        subtask_text=action.subtask_text, answer_text=step_result['answer_text'],
                        summary_text=step_result['summary_text'], tool_call_cnt=step_result['tool_call_cnt'])

            return {'step_list': state.step_list + [step]}

        def give_up_node(state: DispatchState):
            # прогон не роняем: шаги уже выполнены, их результат и сверка нужны, даже если диспетчер сбился
            final_answer = (f"Диспетчер три раза подряд дал ответ, который нельзя исполнить. Последняя ошибка: {state.harness_note}. "
                            f"Выполнено шагов: {len(state.step_list)}, их итоги есть в логе.")
            if verbose > 0:
                print(f"{now()}: [dispatcher] остановлен harness: {state.harness_note}")
            return {'final_answer': final_answer}

        graph = StateGraph(DispatchState)
        graph.add_node('plan', plan_node)
        graph.add_node('delegate', delegate_node)
        graph.add_node('give_up', give_up_node)
        graph.add_edge(START, 'plan')
        graph.add_conditional_edges('plan', route_after_plan,
                                    {'plan': 'plan', 'delegate': 'delegate', 'give_up': 'give_up', END: END})
        graph.add_edge('delegate', 'plan')
        graph.add_edge('give_up', END)

        return graph.compile()

    def run(self, request_text: str, workspace, trace=None, verbose: int = 0) -> dict:
        """
        Выполнение одного запроса пользователя

        :param request_text: запрос пользователя
        :param workspace: объект Workspace с материалами соревнования и реестром прогонов
        :param trace: объект Trace, в него пишутся все ходы диспетчера и субагентов. Если None, трейс не сохраняется
        :param verbose: уровень логирования
            - 0: без логирования
            - 1: лог делегирования - план, кому и с каким скиллом отдан шаг, итог шага
            - 2: плюс полные тексты промптов и ответов
        :return: словарь с ключами final_answer и step_list (список объектов Step)
        """
        if trace is None:
            trace = Trace()
        app = self._build_graph(workspace=workspace, trace=trace, verbose=verbose)

        # на шаг уходит два узла (plan и delegate), плюс повторы plan после непринятых ответов
        res = app.invoke(DispatchState(request_text=request_text),
                         config={'recursion_limit': 4 * self.max_step_cnt + 20})

        trace.add('finish', 'dispatcher', final_answer=res['final_answer'], step_cnt=len(res['step_list']))

        return {'final_answer': res['final_answer'], 'step_list': res['step_list']}
