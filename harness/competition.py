from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Competition(BaseModel):
    """
    Конфиг соревнования - competition.json в папке кейса

    Обязательны только описание и число финальных слотов. Все, что относится к локальной валидации по единицам
    и к Kaggle API, необязательно: в первый день соревнования валидации еще нет, а у разбора на замороженном
    состоянии нет Kaggle. Инструмент, которому такое поле нужно, берет его через get_required
    """
    # опечатка в названии ключа должна быть ошибкой, иначе она молча превращается в "поле не задано"
    model_config = ConfigDict(extra='forbid')

    summary: str = Field(description="что это за соревнование и что лежит в рабочей папке, этот текст видит диспетчер")
    final_slot_cnt: int = Field(ge=1, description="сколько финальных сабмитов можно отметить")
    workspace_file_list: List[str] = Field(default=[], description="файлы и папки кейса, которые копируются в рабочую папку")
    kaggle_slug: Optional[str] = Field(default=None, description="название соревнования в адресе на Kaggle, нужно инструментам kaggle_*")

    unit_file_nm: Optional[str] = Field(default=None, description="csv с результатами валидации по единицам, путь от корня рабочей папки")
    unit_col_nm: Optional[str] = Field(default=None, description="колонка с идентификатором единицы валидации")
    unit_score_col_nm: Optional[str] = Field(default=None, description="колонка со скором одной единицы")
    group_col_nm: Optional[str] = Field(default=None, description="колонка с группой единиц, по группам compare_runs показывает разницу отдельно")
    public_unit_cnt: Optional[int] = Field(default=None, ge=1, description="сколько примерно единиц в публичной части теста")
    lb_decimal_cnt: int = Field(default=3, ge=0, description="до скольких знаков округляется скор на лидерборде")
    team_final_pick_list: List[str] = Field(default=[], description="какие прогоны команда отметила финальными на самом деле, нужно для сверки с приватом")

    def get_required(self, field_nm):
        """
        Значение необязательного поля, без которого инструмент работать не может

        :param field_nm: название поля
        :raises ValueError: если в competition.json этого поля нет
        """
        value = getattr(self, field_nm)
        if value is None:
            field_desc = Competition.model_fields[field_nm].description
            raise ValueError(f"В этом соревновании не задано {field_nm} ({field_desc}), поэтому инструмент здесь не работает")

        return value
