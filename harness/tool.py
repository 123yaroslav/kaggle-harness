import json
import os
import re

from pydantic import ValidationError

from .utilities.parse_json_answer import parse_json_answer
from .utilities.validation_error_text import validation_error_text

# Открывающий тег <tool ...>. \b после tool нужен, чтобы не принять за вызов <tools> или <tool_call>
# Атрибуты читаются до первого ">", поэтому значение атрибута с ">" внутри тег порвет
# Оставил так: в путях и названиях этого символа не бывает, а остальные аргументы идут в теле блока
tool_open_re = re.compile(r'<tool\b([^>]*)>')
# значение атрибута в двойных или в одинарных кавычках: модели пишут и так, и так
tool_attr_re = re.compile(r'''(\w+)\s*=\s*(?:"([^"]*)"|'([^']*)')''')

tool_format_desc = 'Формат вызова: <tool name="название инструмента">аргументы</tool>, один блок на сообщение'


def extract_tool_call(answer_text):
    """
    Достает из ответа модели вызов инструмента вида <tool name="..." key="value">тело</tool>

    Если блоков несколько, берется первый: по правилам вызов в сообщении один.
    Самозакрывающийся тег <tool name="..."/> - это вызов с пустым телом

    :param answer_text: ответ модели
    :return: (tool_nm, attr_dict, body) или None, если вызова в ответе нет
    :raises ValueError: если вызов в ответе есть, но разобрать его нельзя. Текст ошибки написан для модели
    """
    if re.search(r'<tool\b', answer_text) is None:
        return None

    open_match_list = list(tool_open_re.finditer(answer_text))
    if len(open_match_list) == 0:
        raise ValueError(f'Вызов инструмента не разобран: тег <tool ... не закрыт символом ">". '
                         f"Если сообщение оборвалось, повтори вызов короче. {tool_format_desc}")

    # в тексте перед вызовом модель может упомянуть сам тег (<tool> без атрибутов), поэтому ищем первый тег с name
    tool_match = None
    attr_dict = {}
    for open_match in open_match_list:
        attr_dict = {}
        for key, double_quote_value, single_quote_value in tool_attr_re.findall(open_match.group(1)):
            attr_dict[key] = double_quote_value or single_quote_value
        if 'name' in attr_dict:
            tool_match = open_match
            break

    if tool_match is None:
        raise ValueError(f"Вызов инструмента не разобран: в теге <tool> нет атрибута name в кавычках. {tool_format_desc}")

    tool_nm = attr_dict.pop('name')

    if tool_match.group(1).rstrip().endswith('/'):
        return tool_nm, attr_dict, ''

    close_idx = answer_text.find('</tool>', tool_match.end())
    if close_idx == -1:
        # тело до конца ответа не берем: скорее всего ответ оборвался по лимиту токенов, и код или json в нем неполный
        raise ValueError(f"Вызов инструмента {tool_nm} не разобран: у блока нет закрывающего </tool>. "
                         f"Если сообщение оборвалось, повтори вызов короче. {tool_format_desc}")

    body = answer_text[tool_match.end():close_idx]

    return tool_nm, attr_dict, body.strip()


class Tool(object):
    """
    Класс инструмента субагента
    """
    def __init__(self, tool_nm, tool_desc, func, args_model, external_flg=False):
        """
        :param tool_nm: название, по нему модель вызывает инструмент
        :param tool_desc: что делает инструмент, для системного промпта. Аргументы сюда не пишутся, они берутся из args_model
        :param func: функция вида func(workspace, args), возвращает текст результата
        :param args_model: pydantic-модель аргументов. В func приходит уже проверенный объект этой модели.
            Если в модели есть поле body, тело вызова - сырой текст (код, содержимое файла), а не JSON, и попадает в это поле
        :param external_flg: ходит ли инструмент во внешний мир (Kaggle API). Результаты таких инструментов
            пишутся в запись вместе с ответами модели и в режиме replay берутся из нее
        """
        self.tool_nm = tool_nm
        self.tool_desc = tool_desc
        self.func = func
        self.args_model = args_model
        self.raw_body_flg = 'body' in args_model.model_fields
        self.external_flg = external_flg

    def get_arg_desc_str(self):
        arg_desc_list = []
        for field_nm, field in self.args_model.model_fields.items():
            if field_nm == 'body':
                continue

            arg_desc = f"{field_nm} - {field.description}"
            if not field.is_required():
                if field.default is None or field.default == '':
                    arg_desc += " (необязательный)"
                else:
                    arg_desc += f" (необязательный, по умолчанию {field.default})"
            arg_desc_list.append(arg_desc)

        if self.raw_body_flg:
            body_desc = f"Внутри блока - {self.args_model.model_fields['body'].description}"
            if len(arg_desc_list) == 0:
                return body_desc
            else:
                return f"Атрибуты тега: {'; '.join(arg_desc_list)}. {body_desc}"

        if len(arg_desc_list) == 0:
            return "Аргументов нет"
        else:
            return f"Аргументы: {'; '.join(arg_desc_list)}"

    def get_desc_str(self):
        return f"{self.tool_desc}. {self.get_arg_desc_str()}"


class ToolStorage(object):
    """
    Класс набора инструментов. Какие из них доступны конкретному субагенту, решает сам субагент (tool_nm_list)
    """
    def __init__(self, tool_list, external_mode='live', external_file_nm=None, max_result_len=12000):
        """
        :param tool_list: список объектов Tool
        :param external_mode: что делать с внешними инструментами:
            - live: вызывать по-настоящему
            - record: вызывать и сохранять результаты в external_file_nm
            - replay: не вызывать, отдавать сохраненные результаты по порядку
        :param external_file_nm: файл с результатами внешних инструментов
        :param max_result_len: до скольких символов обрезается результат инструмента перед отправкой модели
        """
        if external_mode not in ('live', 'record', 'replay'):
            raise ValueError(f"Неверное значение external_mode: {external_mode}. Выберите live, record или replay")
        if external_mode == 'record' and external_file_nm is None:
            raise ValueError("Для external_mode = record нужен external_file_nm - файл, куда писать результаты")

        self.tool_list = tool_list
        self.external_mode = external_mode
        self.external_file_nm = external_file_nm
        self.max_result_len = max_result_len

        self.external_result_list = []
        self.replay_call_cnt = 0
        if external_mode == 'replay' and external_file_nm is not None and os.path.isfile(external_file_nm):
            with open(external_file_nm, encoding='utf-8') as f:
                self.external_result_list = json.load(f)

    def get(self, tool_nm):
        res = list(filter(lambda tool: tool.tool_nm == tool_nm, self.tool_list))
        if len(res) > 0:
            return res[0]
        else:
            return None

    def get_desc_str(self, tool_nm_list):
        line_list = []
        for tool_nm in tool_nm_list:
            tool = self.get(tool_nm)
            if tool is None:
                raise KeyError(f"Инструмент '{tool_nm}' не найден. Есть: {[tool.tool_nm for tool in self.tool_list]}")
            line_list.append(f"- {tool.tool_nm}: {tool.get_desc_str()}")

        return '\n'.join(line_list)

    def _run(self, tool, workspace, args):
        # Любой сбой инструмента возвращается текстом: субагент должен увидеть, что пошло не так, и поправиться сам,
        # а падение одного инструмента не должно ронять весь прогон. ValueError - это наши собственные проверки,
        # текст у них уже написан для модели. Все остальное - сбой, которого мы не ждали, к нему дописывается тип исключения
        try:
            return str(tool.func(workspace, args))
        except ValueError as exc:
            return f"Ошибка: {exc}"
        except Exception as exc:
            error_text = str(exc).replace(workspace.work_dir, '.')
            return f"Ошибка: инструмент {tool.tool_nm} не отработал ({type(exc).__name__}: {error_text})"

    def _call_external(self, tool, workspace, args):
        if self.external_mode == 'replay':
            if self.replay_call_cnt >= len(self.external_result_list):
                return "Ошибка: в записи нет результата для этого вызова. Внешние инструменты в режиме replay не вызываются"
            result_text = self.external_result_list[self.replay_call_cnt]['result_text']
            self.replay_call_cnt += 1
            return result_text

        result_text = self._run(tool=tool, workspace=workspace, args=args)

        if self.external_mode == 'record':
            # в запись идет и текст ошибки: replay отдает результаты по порядку, и пропущенный вызов сдвинул бы все следующие
            self.external_result_list.append({'tool_nm': tool.tool_nm, 'arg_dict': args.model_dump(exclude_unset=True),
                                              'result_text': result_text})
            # пишем через временный файл: если прогон оборвется посреди записи, старый файл останется целым
            tmp_file_nm = self.external_file_nm + '.tmp'
            with open(tmp_file_nm, 'w', encoding='utf-8') as f:
                json.dump(self.external_result_list, f, ensure_ascii=False, indent=1)
            os.replace(tmp_file_nm, self.external_file_nm)

        return result_text

    def call(self, tool_nm, attr_dict, body, workspace, tool_nm_list):
        """
        Вызов инструмента от имени субагента

        Ошибки не поднимаются, а возвращаются текстом: субагент должен увидеть, что пошло не так, и поправиться сам

        :param tool_nm: название инструмента из ответа модели
        :param attr_dict: атрибуты тега <tool>
        :param body: тело тега
        :param workspace: объект Workspace
        :param tool_nm_list: инструменты, разрешенные этому субагенту
        :return: текст результата
        """
        tool = self.get(tool_nm)
        if tool is None or tool_nm not in tool_nm_list:
            return f"Ошибка: инструмент '{tool_nm}' тебе недоступен. Доступны: {tool_nm_list}"

        arg_dict = dict(attr_dict)
        if tool.raw_body_flg:
            arg_dict['body'] = body
        elif len(body) > 0:
            try:
                arg_dict.update(parse_json_answer(body))
            except ValueError as exc:
                return f"Ошибка: аргументы инструмента {tool_nm} должны быть JSON-объектом внутри блока. {exc}"

        # ошибки в аргументах до внешнего инструмента не доходят и в запись не попадают:
        # проверка одна и та же и при записи, и при replay, порядок результатов из-за нее не сдвигается
        try:
            args = tool.args_model.model_validate(arg_dict)
        except ValidationError as exc:
            return f"Ошибка в аргументах {tool_nm}: {validation_error_text(exc)}. {tool.get_arg_desc_str()}"

        if tool.external_flg:
            result_text = self._call_external(tool=tool, workspace=workspace, args=args)
        else:
            result_text = self._run(tool=tool, workspace=workspace, args=args)

        if len(result_text) > self.max_result_len:
            cut_len = len(result_text) - self.max_result_len
            result_text = result_text[:self.max_result_len] + f"\n... (обрезано, еще {cut_len} символов. Сузь запрос или читай частями)"

        return result_text
