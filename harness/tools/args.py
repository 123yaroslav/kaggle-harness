from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Модели аргументов инструментов. Описания полей (description) попадают в системный промпт субагента как есть,
# а если модель прислала не то, по этим же классам собирается текст ошибки

verdict_list = ['принять', 'доработать', 'исключить']
team_decision_list = ['принято', 'закрыто']
review_verdict_list = ['обосновано', 'по шуму']
# то, что kaggle kernels list принимает в --sort-by (kaggle CLI 2.2.4), кроме relevance: она работает только с поиском
kernel_sort_list = ['hotness', 'commentCount', 'dateCreated', 'dateRun', 'scoreAscending', 'scoreDescending', 'viewCount', 'voteCount']

# сколько символов read_file отдает за один вызов. Должно быть заметно меньше max_result_len у ToolStorage (12000):
# иначе результат обрезается уже там, и подсказка, с какого offset читать дальше, теряется
max_read_len = 10000


def _check_choice(value, choice_list):
    if value not in choice_list:
        raise ValueError(f"неверное значение {value!r}, выбери одно из {choice_list}")
    return value


class ToolArgs(BaseModel):
    """
    Базовый класс аргументов инструмента
    """
    # лишний аргумент - ошибка: если его молча пропустить, модель будет считать, что он учтен
    # Числа вместо строк принимаются: название прогона вроде 12 модель может написать без кавычек
    model_config = ConfigDict(extra='forbid', coerce_numbers_to_str=True, str_strip_whitespace=True)


class NoArgs(ToolArgs):
    pass


class ReadFileArgs(ToolArgs):
    path: str = Field(min_length=1, description="путь к файлу от корня рабочей папки")
    offset: int = Field(default=0, ge=0, description="с какого символа читать")
    limit: int = Field(default=max_read_len, ge=1, description=f"сколько символов вернуть, за один вызов отдается не больше {max_read_len}")


class WriteFileArgs(ToolArgs):
    path: str = Field(min_length=1, description="путь к файлу от корня рабочей папки")
    body: str = Field(description="содержимое файла")

    @field_validator('body')
    @classmethod
    def check_body(cls, body):
        if len(body) == 0:
            raise ValueError('пустое содержимое. Текст файла пишется внутри блока <tool name="write_file" path="...">...</tool>')
        return body


class RunPythonArgs(ToolArgs):
    body: str = Field(description="код")

    @field_validator('body')
    @classmethod
    def check_body(cls, body):
        if len(body) == 0:
            raise ValueError('пустой код. Код пишется внутри блока <tool name="run_python">...</tool>')
        return body


class ListRunsArgs(ToolArgs):
    max_desc_len: int = Field(default=110, ge=0, description="до скольких символов обрезать описания прогонов")


class CompareRunsArgs(ToolArgs):
    base: str = Field(min_length=1, description="название прогона-базы")
    cand: str = Field(min_length=1, description="название прогона-кандидата")
    lane: str = Field(min_length=1, description="дорожка валидации")


class LbNoiseArgs(ToolArgs):
    base: str = Field(min_length=1, description="название прогона-базы")
    cand_list: List[str] = Field(min_length=1, description="список названий прогонов-кандидатов")
    lane: str = Field(min_length=1, description="дорожка валидации")


class SetVerdictArgs(ToolArgs):
    run_list: List[str] = Field(min_length=1, description="список названий прогонов")
    verdict: str = Field(description=' | '.join(verdict_list))
    reason: str = Field(min_length=1, description="причина, одна на все прогоны вызова")

    @field_validator('verdict')
    @classmethod
    def check_verdict(cls, verdict):
        return _check_choice(value=verdict, choice_list=verdict_list)


class FinalPick(ToolArgs):
    run: str = Field(min_length=1)
    reason: str = ''


class SetFinalPicksArgs(ToolArgs):
    pick_list: List[FinalPick] = Field(min_length=1, description="список объектов с полями run (название прогона) и reason")
    hypothesis: str = Field(min_length=1, description="гипотеза, на которой стоит выбор")
    expected_metric: str = Field(min_length=1, description="какой метрики ждешь")
    rule: str = Field(min_length=1, description="правило, по которому выбор мог бы измениться")


class LineReview(ToolArgs):
    cand: str = Field(min_length=1)
    base: str = Field(min_length=1)
    team_decision: str
    verdict: str
    reason: str = Field(min_length=1)

    @field_validator('team_decision')
    @classmethod
    def check_team_decision(cls, team_decision):
        return _check_choice(value=team_decision, choice_list=team_decision_list)

    @field_validator('verdict')
    @classmethod
    def check_verdict(cls, verdict):
        return _check_choice(value=verdict, choice_list=review_verdict_list)


class SetLineReviewArgs(ToolArgs):
    review_list: List[LineReview] = Field(min_length=1, description="список объектов с полями cand, base (названия прогонов), "
                                                                    f"team_decision ({' | '.join(team_decision_list)}), "
                                                                    f"verdict ({' | '.join(review_verdict_list)}), reason")


class RegisterRunArgs(ToolArgs):
    run: str = Field(min_length=1, description="название нового прогона")
    description: str = Field(min_length=1, description="что это за прогон и чем отличается от родителя")
    lane: str = Field(min_length=1, description="дорожка валидации, в которой получены результаты; одна из тех, что уже есть в реестре")
    result_file: str = Field(min_length=1, description="csv в рабочей папке, по строке на единицу, с теми же колонками, что у результатов "
                                                       "валидации остальных прогонов (каких колонок не хватает, скажет ошибка)")
    parent: str = Field(default='', description="название прогона-родителя из реестра")


class KagglePagesArgs(ToolArgs):
    page: Optional[str] = Field(default=None, description="название страницы; без него вернется список страниц")
    offset: int = Field(default=0, ge=0, description="с какого символа читать страницу")


class KaggleKernelsArgs(ToolArgs):
    sort_by: str = Field(default='voteCount', description='сортировка: ' + ' | '.join(kernel_sort_list))
    # в CLI максимум 200, но строка на ноутбук - около 100 символов, и больше сотни строк в результат инструмента не влезает
    page_size: int = Field(default=20, ge=1, le=100, description="сколько ноутбуков вернуть, не больше 100")

    @field_validator('sort_by')
    @classmethod
    def check_sort_by(cls, sort_by):
        return _check_choice(value=sort_by, choice_list=kernel_sort_list)


class KaggleKernelSourceArgs(ToolArgs):
    ref: str = Field(min_length=1, description="ссылка на ноутбук вида автор/название из kaggle_kernels")
    offset: int = Field(default=0, ge=0, description="с какого символа читать")


class KaggleCsvProfileArgs(ToolArgs):
    file: str = Field(min_length=1, description="имя csv-файла из списка файлов соревнования")
