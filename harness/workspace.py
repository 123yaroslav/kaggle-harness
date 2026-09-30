import importlib.util
import os
import shutil

import pandas as pd
from pydantic import ValidationError

from .competition import Competition
from .utilities.now import now
from .utilities.validation_error_text import validation_error_text


class Workspace(object):
    """
    Рабочая папка одного прогона кейса: материалы соревнования, реестр прогонов, результаты валидации по единицам,
    вердикты аудитора и журнал финального выбора. Приватные скоры сюда не копируются

    Реестр прогонов и метрика ищутся в корне рабочей папки по именам submissions.csv и metric.py,
    файл с результатами по единицам у каждого соревнования свой и задается в competition.json (unit_file_nm)
    """
    def __init__(self, case_dir, work_dir):
        """
        :param case_dir: папка кейса: competition.json и файлы, перечисленные в нем в workspace_file_list
        :param work_dir: куда разворачивать рабочую папку. Если она уже есть, будет удалена
        """
        self.case_dir = case_dir
        self.work_dir = os.path.abspath(work_dir)
        self.home_dir = self.work_dir + '_home'

        competition_file_nm = os.path.join(case_dir, 'competition.json')
        with open(competition_file_nm, encoding='utf-8') as f:
            competition_text = f.read()
        try:
            self.competition = Competition.model_validate_json(competition_text)
        except ValidationError as exc:
            raise ValueError(f"Неверный конфиг соревнования {competition_file_nm}: {validation_error_text(exc)}")

        self.verdict_dict = {}
        self.final_pick_list = []
        self.line_review_list = []
        self.event_list = []
        self.script_cnt = 0

        self._prepare()

        self.run_df = None
        run_file_nm = os.path.join(self.work_dir, 'submissions.csv')
        if os.path.isfile(run_file_nm):
            self.run_df = pd.read_csv(run_file_nm, dtype={'ref': str}).fillna({'parent_label': ''})

        self.unit_df = None
        if self.competition.unit_file_nm is not None:
            unit_file_nm = os.path.join(self.work_dir, self.competition.unit_file_nm)
            if not os.path.isfile(unit_file_nm):
                raise ValueError(f"В {competition_file_nm} задан unit_file_nm = {self.competition.unit_file_nm}, но в рабочей папке такого файла нет. "
                                 f"Проверьте workspace_file_list")
            self.unit_df = pd.read_csv(unit_file_nm)

        # метрика у каждого соревнования своя и считается не средним по единицам, поэтому лежит кодом рядом с данными кейса
        self.metric_module = None
        metric_file_nm = os.path.join(self.work_dir, 'metric.py')
        if os.path.isfile(metric_file_nm):
            spec = importlib.util.spec_from_file_location('competition_metric', metric_file_nm)
            self.metric_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.metric_module)

    def _prepare(self):
        shutil.rmtree(self.work_dir, ignore_errors=True)
        shutil.rmtree(self.home_dir, ignore_errors=True)
        os.makedirs(os.path.join(self.work_dir, 'notes'))
        os.makedirs(os.path.join(self.work_dir, 'scratch'))

        for file_nm in self.competition.workspace_file_list:
            src_nm = os.path.join(self.case_dir, file_nm)
            dst_nm = os.path.join(self.work_dir, file_nm)
            if os.path.isdir(src_nm):
                shutil.copytree(src_nm, dst_nm)
            else:
                os.makedirs(os.path.dirname(dst_nm), exist_ok=True)
                shutil.copy(src_nm, dst_nm)

    def resolve_path(self, path):
        full_path = os.path.abspath(os.path.join(self.work_dir, path))
        if full_path != self.work_dir and not full_path.startswith(self.work_dir + os.sep):
            raise ValueError(f"Путь {path} выходит за пределы рабочей папки")
        return full_path

    def get_file_tree_str(self):
        line_list = []
        for root, dir_nm_list, file_nm_list in os.walk(self.work_dir):
            # __pycache__ появляется сам, когда harness импортирует metric.py из рабочей папки
            dir_nm_list[:] = sorted(dir_nm for dir_nm in dir_nm_list if dir_nm != '__pycache__')
            rel_dir = os.path.relpath(root, self.work_dir)
            for file_nm in sorted(file_nm_list):
                rel_nm = file_nm if rel_dir == '.' else os.path.join(rel_dir, file_nm)
                # размер в символах, а не в байтах: offset у read_file считается в символах,
                # а на кириллице байтов почти вдвое больше, чем символов
                with open(os.path.join(root, file_nm), encoding='utf-8', errors='replace') as f:
                    char_cnt = len(f.read())
                line_list.append(f"{rel_nm} ({char_cnt} символов)")

        if len(line_list) == 0:
            return "(пусто)"
        return '\n'.join(line_list)

    def add_event(self, event_text):
        self.event_list.append(event_text)

    def pop_event_list(self):
        event_list = self.event_list
        self.event_list = []
        return event_list

    def get_run_nm_list(self):
        if self.run_df is None:
            return []
        return list(self.run_df['label'])

    def get_lane_list(self, run_nm):
        if self.unit_df is None:
            return []
        return sorted(self.unit_df.loc[self.unit_df['candidate'] == run_nm, 'lane'].unique())

    def get_unit_df(self, run_nm, lane):
        """
        Результаты валидации одного прогона по единицам (фильмам) в одной дорожке

        :param run_nm: название прогона
        :param lane: дорожка валидации
        :return: pd.DataFrame, одна строка на единицу
        """
        if self.unit_df is None:
            raise ValueError("В рабочей папке нет результатов валидации по единицам")

        unit_df = self.unit_df[(self.unit_df['candidate'] == run_nm) & (self.unit_df['lane'] == lane)]
        if len(unit_df) == 0:
            lane_list = self.get_lane_list(run_nm)
            if len(lane_list) == 0:
                raise ValueError(f"Для прогона '{run_nm}' нет результатов валидации по единицам ни в одной дорожке")
            else:
                raise ValueError(f"Для прогона '{run_nm}' нет результатов в дорожке '{lane}'. Дорожки этого прогона: {lane_list}")

        return unit_df.reset_index(drop=True)

    def _check_metric(self):
        if self.metric_module is None:
            raise ValueError("Для этого соревнования не подключена метрика (нет metric.py в рабочей папке)")

    def score_detail(self, unit_df):
        """
        Метрика соревнования на наборе единиц вместе с тем, из чего она собрана

        :param unit_df: строки одного прогона в одной дорожке, по строке на единицу
        :return: словарь, в нем обязательно есть ключ score
        """
        self._check_metric()
        return self.metric_module.competition_score(unit_df)

    def score(self, unit_df, idx=None):
        """
        Метрика соревнования одним числом

        :param unit_df: строки одного прогона в одной дорожке
        :param idx: индексы строк для бутстрапа (с повторами). Если None, метрика считается по всем строкам
        """
        if idx is None:
            return float(self.score_detail(unit_df)['score'])

        self._check_metric()
        return float(self.metric_module.score_by_idx(unit_df, idx))

    def get_run_table_str(self, max_desc_len=110):
        """
        Реестр прогонов таблицей: по строке на прогон

        :param max_desc_len: до скольких символов обрезать описание прогона. 110 взято на глаз:
            таблица целиком идет в каждый промпт диспетчера
        """
        if self.run_df is None or len(self.run_df) == 0:
            return "(реестр прогонов пуст)"

        # колонки разделены " | ", а не выровнены по ширине: список дорожек бывает любой длины,
        # и при фиксированной ширине он склеивался с описанием
        line_list = ["прогон | дата | родитель | public | вердикт | валидация по единицам | описание"]
        for _, row in self.run_df.iterrows():
            lane_str = ', '.join(self.get_lane_list(row['label'])) or '-'
            if pd.isna(row['public_lb']):
                public_str = '-'
            else:
                public_str = f"{row['public_lb']:.{self.competition.lb_decimal_cnt}f}"
            desc_str = str(row['description'])
            if len(desc_str) > max_desc_len:
                desc_str = desc_str[:max_desc_len] + '...'

            date_str = str(row['submitted_at'])[5:16] or 'локально'
            line_list.append(' | '.join([str(row['label']), date_str, str(row['parent_label'] or '-'), public_str,
                                         self.verdict_dict.get(row['label'], 'не смотрел'), lane_str, desc_str]))

        return '\n'.join(line_list)

    def set_verdict(self, run_nm, verdict):
        self.verdict_dict[run_nm] = verdict

        # финалить можно только принятое. set_final_picks это проверяет, но вердикт могут сменить и после выбора,
        # поэтому вторая половина правила живет здесь
        if verdict != 'принять' and run_nm in self.final_pick_list:
            self.final_pick_list.remove(run_nm)
            event_text = (f"прогон {run_nm} убран из финального выбора: вердикт аудитора сменился на '{verdict}'. "
                          f"В выборе остались: {self.final_pick_list}")
            self.add_event(event_text)
            with open(os.path.join(self.work_dir, 'notes', 'final_picks.md'), 'a', encoding='utf-8') as f:
                f.write(f"## {now()}: {event_text}\n\n")

    def is_submitted(self, run_nm):
        # у посылки есть номер на Kaggle, у прогона, который зарегистрировал инженер экспериментов, его нет
        ref = self.run_df.loc[self.run_df['label'] == run_nm, 'ref'].iloc[0]
        return isinstance(ref, str) and len(ref.strip()) > 0

    def add_run(self, run_nm, parent_nm, description, lane, result_df):
        """
        Добавление в реестр нового прогона с результатами валидации по единицам или еще одной дорожки прогону,
        который уже добавлен. Ничего не проверяет: все проверки делает register_run до вызова

        :param run_nm: название прогона
        :param parent_nm: название прогона-родителя или пустая строка
        :param description: что это за прогон и чем отличается от родителя
        :param lane: дорожка валидации, в которой получены результаты
        :param result_df: pd.DataFrame с теми же колонками по единицам, что у остальных прогонов
        """
        result_df = result_df.copy()
        result_df['candidate'] = run_nm
        result_df['lane'] = lane

        # времени у локального прогона нет нарочно: реестр идет в промпты, и с часами запись прогона
        # на replay не совпадала бы сама с собой
        run_row = {'ref': '', 'label': run_nm, 'submitted_at': '', 'description': description,
                   'public_lb': float('nan'), 'parent_label': parent_nm}

        if self.unit_df is None:
            self.unit_df = result_df
        else:
            self.unit_df = pd.concat([self.unit_df, result_df[self.unit_df.columns]], ignore_index=True)
        if self.run_df is None:
            self.run_df = pd.DataFrame([run_row])
        elif run_nm not in self.get_run_nm_list():
            self.run_df.loc[len(self.run_df)] = [run_row[col] for col in self.run_df.columns]

    def register_line_review(self, review_list):
        """
        Запись разбора решений команды

        :param review_list: список словарей с ключами cand, base, team_decision, verdict, reason
        """
        # повторный вызов заменяет разбор целиком: так субагент может исправиться
        self.line_review_list = review_list

        line_list = [f"## {now()}: разбор решений по линиям", ""]
        for review in review_list:
            line_list.append(f"- {review['cand']} против {review['base']}: команда - {review['team_decision']}, "
                             f"разбор - {review['verdict']}. {review['reason']}")
        with open(os.path.join(self.work_dir, 'notes', 'line_review.md'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(line_list) + '\n')

    def register_final_picks(self, pick_list, hypothesis, expected_metric, rule):
        """
        Запись финального выбора и пререгистрации в журнал. Сам выбор заменяется, журнал дописывается:
        по нему видно, как выбор менялся

        :param pick_list: список словарей с ключами run и reason
        :param hypothesis: гипотеза, на которой стоит выбор
        :param expected_metric: какой метрики ждем
        :param rule: правило, по которому выбор мог бы измениться
        """
        self.final_pick_list = [pick['run'] for pick in pick_list]

        line_list = [f"## {now()}: финальные сабмиты", ""]
        for pick in pick_list:
            line_list.append(f"- {pick['run']}: {pick['reason']}")
        line_list += [
            "",
            f"Гипотеза: {hypothesis}",
            f"Ожидаемая метрика по валидации: {expected_metric}",
            f"Правило: {rule}",
            ""
        ]
        with open(os.path.join(self.work_dir, 'notes', 'final_picks.md'), 'a', encoding='utf-8') as f:
            f.write('\n'.join(line_list) + '\n')
