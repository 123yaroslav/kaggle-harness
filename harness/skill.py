import os


class Skill(object):
    """
    Класс скилла - методики, которую harness подмешивает субагенту в системный промпт
    """
    def __init__(self, skill_nm, skill_desc, skill_text):
        """
        :param skill_nm: название скилла
        :param skill_desc: описание: про что методика и когда ее подключать. Это все, что видит диспетчер
        :param skill_text: текст методики. Его видит только субагент, которому скилл подключили
        """
        self.skill_nm = skill_nm
        self.skill_desc = skill_desc
        self.skill_text = skill_text


class SkillStorage(object):
    """
    Класс каталога скиллов. Один скилл - один .md файл: шапка между строками --- с полями name и description, ниже текст
    """
    def __init__(self, skill_dir):
        self.skill_dir = skill_dir
        self.skill_list = []

        self._load()

    def _load(self):
        for file_nm in sorted(os.listdir(self.skill_dir)):
            if not file_nm.endswith('.md'):
                continue

            # utf-8-sig: файл, сохраненный в блокноте с BOM, иначе не проходит проверку шапки
            with open(os.path.join(self.skill_dir, file_nm), encoding='utf-8-sig') as f:
                line_list = f.read().strip().split('\n')

            # шапку разбираем руками, ради двух полей тянуть yaml не хочется. Границы ищем по строкам из одних ---,
            # а не через split('---'): тире внутри описания шапку рвать не должно
            border_idx_list = [idx for idx, line in enumerate(line_list) if line.strip() == '---']
            if len(border_idx_list) < 2 or border_idx_list[0] != 0:
                raise ValueError(f"Скилл {file_nm}: нет шапки. Файл должен начинаться с блока --- name / description ---")

            header_dict = {}
            for line in line_list[1:border_idx_list[1]]:
                if ':' not in line:
                    continue
                key, value = line.split(':', 1)
                header_dict[key.strip()] = value.strip()

            for key in ['name', 'description']:
                if key not in header_dict or len(header_dict[key]) == 0:
                    raise ValueError(f"Скилл {file_nm}: в шапке нет поля {key}")

            self.skill_list.append(Skill(skill_nm=header_dict['name'],
                                         skill_desc=header_dict['description'],
                                         skill_text='\n'.join(line_list[border_idx_list[1] + 1:]).strip()))

        skill_nm_list = self.get_skill_nm_list()
        if len(set(skill_nm_list)) != len(skill_nm_list):
            raise ValueError(f"В {self.skill_dir} есть скиллы с одинаковым name: {skill_nm_list}")

    def get(self, skill_nm):
        """
        Получение скилла по названию

        :param skill_nm: название скилла
        :return: объект Skill
        :raises KeyError: если скилла с таким названием нет
        """
        for skill in self.skill_list:
            if skill.skill_nm == skill_nm:
                return skill

        raise KeyError(f"Скилл '{skill_nm}' не найден. Доступные: {self.get_skill_nm_list()}")

    def get_skill_nm_list(self):
        return [skill.skill_nm for skill in self.skill_list]

    def get_catalog_str(self):
        line_list = []
        for skill in self.skill_list:
            line_list.append(f"- {skill.skill_nm}: {skill.skill_desc}")

        return '\n'.join(line_list)
