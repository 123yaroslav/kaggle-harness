import json
import os

from .utilities.now import now

# в .md результат инструмента режется, целиком он лежит в .jsonl
md_result_len = 1500


class Trace(object):
    """
    Трейс одного прогона. Каждое событие (ход диспетчера, вызов субагента, ответ модели, вызов инструмента)
    сразу дописывается строкой в .jsonl: если прогон упадет, останется все, что было до падения.
    Из тех же событий в конце собирается .md, чтобы читать глазами
    """
    def __init__(self, trace_file_nm=None):
        """
        :param trace_file_nm: путь к .jsonl. Если None, события остаются только в памяти
        """
        self.trace_file_nm = trace_file_nm
        self.event_list = []
        self.step_num = None

        if trace_file_nm is not None:
            os.makedirs(os.path.dirname(os.path.abspath(trace_file_nm)), exist_ok=True)
            open(trace_file_nm, 'w', encoding='utf-8').close()
            # .md собирается только в конце прогона. Старый убираем сразу, чтобы после падения рядом с новым .jsonl не лежал чужой
            if os.path.isfile(self.get_md_file_nm()):
                os.remove(self.get_md_file_nm())

    def set_step(self, step_num):
        # номер шага диспетчера проставляется во все события субагента, сам субагент его не знает
        self.step_num = step_num

    def add(self, event_nm, actor_nm, **field_dict):
        """
        :param event_nm: тип события: request, dispatcher_prompt, dispatcher_turn, delegate, agent_start,
            model_answer, tool_call, agent_finish, finish, private_check
        :param actor_nm: кто его породил: harness, dispatcher или название субагента
        :param field_dict: поля события, у каждого типа свои
        """
        event = {'event_num': len(self.event_list) + 1, 'dttm': now(), 'event_nm': event_nm,
                 'actor_nm': actor_nm, 'step_num': self.step_num}
        event.update(field_dict)
        self.event_list.append(event)

        if self.trace_file_nm is not None:
            with open(self.trace_file_nm, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')

    def get_md_file_nm(self):
        return os.path.splitext(self.trace_file_nm)[0] + '.md'

    def save_md(self):
        """
        Тот же трейс в читаемом виде. Пользовательские промпты сюда не идут (они длинные и повторяют прошлые шаги),
        метапромпт диспетчера и системные промпты субагентов со скиллами идут целиком
        """
        line_list = []
        for event in self.event_list:
            event_nm = event['event_nm']
            actor_nm = event['actor_nm']

            if event_nm == 'request':
                line_list += [f"# Трейс кейса {event['case_nm']}", "",
                              f"Режим {event['llm_mode']}, модель {event['model_nm']}, скиллы: {'подключаются' if event['skill_flg'] else 'отключены'}. "
                              f"Полные промпты и результаты инструментов лежат рядом в .jsonl", "",
                              f"Запрос: {event['request_text']}", ""]
            elif event_nm == 'dispatcher_prompt':
                line_list += ["<details><summary>метапромпт диспетчера с каталогами субагентов и скиллов</summary>", "",
                              _code_block(event['system_prompt']), "", "</details>", ""]
            elif event_nm == 'dispatcher_turn':
                line_list += [f"## Диспетчер, ход {event['turn_cnt']}", ""]
                if event['harness_note'] is not None:
                    line_list += [f"Ответ не принят harness: {event['harness_note']}", "", _code_block(event['answer_text']), ""]
                else:
                    line_list += [_code_block(event['answer_text']), ""]
            elif event_nm == 'delegate':
                skill_nm_str = ', '.join(event['skill_nm_list']) if len(event['skill_nm_list']) > 0 else 'нет'
                line_list += [f"## Шаг {event['step_num']}: {event['agent_nm']}", "",
                              f"Скиллы, выбранные диспетчером: {skill_nm_str}. Контекст: шаги {event['context_step_list']}", ""]
            elif event_nm == 'agent_start':
                line_list += [f"Системный промпт: {len(event['system_prompt'])} символов, из них скиллы - {event['skill_char_cnt']}", "",
                              "<details><summary>системный промпт целиком</summary>", "", _code_block(event['system_prompt']), "", "</details>", "",
                              f"Подзадача: {event['subtask_text']}", ""]
            elif event_nm == 'model_answer':
                line_list += [f"### {actor_nm}, сообщение {event['message_num']}", "", _code_block(event['answer_text']), ""]
            elif event_nm == 'tool_call':
                result_text = event['result_text']
                if len(result_text) > md_result_len:
                    result_text = result_text[:md_result_len] + f"\n... (обрезано, всего {len(event['result_text'])} символов)"
                line_list += [f"Результат {event['tool_nm']}:", "", _code_block(result_text), ""]
            elif event_nm == 'agent_finish':
                line_list += [f"Вызовов инструментов: {event['tool_call_cnt']}"]
                for fact_text in event['fact_list']:
                    line_list.append(f"[harness] {fact_text}")
                line_list.append("")
            elif event_nm == 'finish':
                line_list += ["## Ответ диспетчера", "", event['final_answer'], ""]
            elif event_nm == 'private_check':
                line_list += ["## Сверка после прогона", "", _code_block(event['check_text']), ""]

        with open(self.get_md_file_nm(), 'w', encoding='utf-8') as f:
            f.write('\n'.join(line_list))


def _code_block(text):
    # в ответах модели встречаются свои ``` (код, json), поэтому ограда из четырех
    return f"````\n{text.strip()}\n````"
