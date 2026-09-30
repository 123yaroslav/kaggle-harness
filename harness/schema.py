from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

action_list = ['delegate', 'finish']


class Case(BaseModel):
    """
    Тестовый кейс: на каком соревновании и с каким запросом запускается диспетчер
    """
    competition_nm: str = Field(description="папка соревнования внутри cases/")
    request_text: str = Field(description="запрос пользователя к диспетчеру")


class DispatcherAction(BaseModel):
    """
    Ход диспетчера. Модель отвечает JSON-объектом, он разбирается в этот класс;
    если разбор не прошел, текст ошибки уходит диспетчеру следующим ходом
    """
    thought: str = ''
    plan_list: List[str] = []
    action: str
    agent_nm: Optional[str] = None
    skill_nm_list: List[str] = []
    subtask_text: Optional[str] = None
    context_step_list: List[int] = []
    final_answer: Optional[str] = None

    @field_validator('action')
    @classmethod
    def check_action(cls, action):
        if action not in action_list:
            raise ValueError(f"неверное значение {action!r}, выбери одно из {action_list}")
        return action

    @model_validator(mode='after')
    def check_action_fields(self):
        if self.action == 'finish':
            if self.final_answer is None or len(self.final_answer.strip()) == 0:
                raise ValueError("для finish нужен непустой final_answer")
        else:
            if self.agent_nm is None or len(self.agent_nm.strip()) == 0:
                raise ValueError("для delegate нужен agent_nm")
            if self.subtask_text is None or len(self.subtask_text.strip()) == 0:
                raise ValueError("для delegate нужен непустой subtask_text")
        return self


class Step(BaseModel):
    """
    Выполненный шаг: кому диспетчер его отдал и что вернул субагент
    """
    step_num: int
    agent_nm: str
    skill_nm_list: List[str]
    subtask_text: str
    answer_text: str
    summary_text: str
    tool_call_cnt: int


class DispatchState(BaseModel):
    """
    Состояние графа диспетчера
    """
    request_text: str
    step_list: List[Step] = []
    plan_list: List[str] = []
    action: Optional[DispatcherAction] = None
    harness_note: Optional[str] = None
    bad_answer_cnt: int = 0
    turn_cnt: int = 0
    final_answer: Optional[str] = None


class AgentState(BaseModel):
    """
    Состояние графа субагента на одной подзадаче
    """
    turn_block_str: str = ''
    tool_call_cnt: int = 0
    answer_text: str = ''
    # разобранный вызов инструмента из последнего ответа модели: (название, атрибуты, тело)
    tool_nm: Optional[str] = None
    attr_dict: dict = {}
    body: str = ''
    format_error: Optional[str] = None
