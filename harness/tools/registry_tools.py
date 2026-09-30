import math
import os

import numpy as np
import pandas as pd

# Число выборок и сид бутстрапа такие же, как по умолчанию у score_delta в metric.py кейса biohub, и выборка
# делается тем же вызовом rng.choice. Это подгонка под один кейс, и сделана она ради одного: compare_runs и расчет,
# который субагент делает сам через metric.py, должны давать на одних данных один и тот же интервал
bootstrap_resample_cnt = 2000
bootstrap_seed = 1

# разница меньше порога считается нулем: скоры читаются из csv как float, и точное сравнение с нулем ловит ошибки округления
# Порог взят с запасом: в данных biohub самая маленькая настоящая разница скоров единиц - около 3e-6
zero_delta_threshold = 1e-9


def list_runs(workspace, args):
    return workspace.get_run_table_str(max_desc_len=args.max_desc_len)


def _check_run_nm(workspace, run_nm):
    if run_nm not in workspace.get_run_nm_list():
        raise ValueError(f"Прогон '{run_nm}' не найден в реестре. Названия прогонов дает list_runs")


def _paired_units(workspace, base_nm, cand_nm, lane):
    unit_col_nm = workspace.competition.get_required('unit_col_nm')
    base_df = workspace.get_unit_df(run_nm=base_nm, lane=lane).set_index(unit_col_nm)
    cand_df = workspace.get_unit_df(run_nm=cand_nm, lane=lane).set_index(unit_col_nm)

    unit_list = sorted(set(base_df.index) & set(cand_df.index))
    if len(unit_list) == 0:
        raise ValueError(f"У прогонов {base_nm} и {cand_nm} в дорожке {lane} нет общих единиц")

    return base_df.loc[unit_list].reset_index(), cand_df.loc[unit_list].reset_index()


def _bootstrap_score(workspace, unit_df, sample_unit_cnt):
    rng = np.random.default_rng(bootstrap_seed)
    score_list = []
    for _ in range(bootstrap_resample_cnt):
        idx = rng.choice(len(unit_df), sample_unit_cnt)
        score = workspace.score(unit_df=unit_df, idx=idx)
        if np.isfinite(score):
            score_list.append(score)

    return np.array(score_list)


def _bootstrap_delta(workspace, base_df, cand_df, sample_unit_cnt):
    # единицы у базы и кандидата идут в одном порядке, поэтому одна выборка индексов дает парную разницу
    rng = np.random.default_rng(bootstrap_seed)
    delta_list = []
    for _ in range(bootstrap_resample_cnt):
        idx = rng.choice(len(base_df), sample_unit_cnt)
        delta = workspace.score(unit_df=cand_df, idx=idx) - workspace.score(unit_df=base_df, idx=idx)
        # метрика бывает не определена на выборке, в которую не попало ни одной единицы с посчитанным скором
        if np.isfinite(delta):
            delta_list.append(delta)

    return np.array(delta_list)


def _sign_test_pvalue(win_cnt, lose_cnt):
    total_cnt = win_cnt + lose_cnt
    if total_cnt == 0:
        return 1.0
    tail = sum(math.comb(total_cnt, i) for i in range(min(win_cnt, lose_cnt) + 1)) / 2 ** total_cnt
    return min(1.0, 2 * tail)


def _group_delta_line_list(workspace, base_df, cand_df, group_col_nm):
    group_desc_list = []
    plus_nm_list = []
    minus_nm_list = []
    zero_nm_list = []
    unknown_nm_list = []
    for group_nm in sorted(base_df[group_col_nm].unique()):
        group_flg = (base_df[group_col_nm] == group_nm).values
        group_delta = workspace.score(unit_df=cand_df[group_flg]) - workspace.score(unit_df=base_df[group_flg])

        if not np.isfinite(group_delta):
            group_desc_list.append(f"{group_nm} ({int(group_flg.sum())} ед.): не определена")
            unknown_nm_list.append(str(group_nm))
            continue

        group_desc_list.append(f"{group_nm} ({int(group_flg.sum())} ед.): {group_delta:+.5f}")
        if abs(group_delta) <= zero_delta_threshold:
            zero_nm_list.append(str(group_nm))
        elif group_delta > 0:
            plus_nm_list.append(str(group_nm))
        else:
            minus_nm_list.append(str(group_nm))

    # нулевая разница на группе - это не "знак совпадает": кандидат на этой группе просто ничего не меняет,
    # и плюс целиком держится на остальных
    if len(plus_nm_list) > 0 and len(minus_nm_list) > 0:
        sign_desc = "РАЗНЫЙ"
    elif len(plus_nm_list) + len(minus_nm_list) == 0:
        sign_desc = "разницы нет ни на одной группе"
    elif len(zero_nm_list) > 0:
        sign_desc = f"на части групп разница нулевая ({', '.join(zero_nm_list)}), на остальных знак совпадает"
    else:
        sign_desc = "совпадает"
    if len(unknown_nm_list) > 0:
        sign_desc += f"; на {', '.join(unknown_nm_list)} метрика не определена"

    return [f"по группам ({group_col_nm}): " + '; '.join(group_desc_list),
            f"знак разницы по группам: {sign_desc}"]


def compare_runs(workspace, args):
    """
    Парное сравнение двух прогонов на одних и тех же единицах валидации

    Метрика соревнования считается на всем наборе единиц (она может быть пулом, а не средним), разница -
    кандидат минус база. Дальше: бутстрап по единицам, счет по единицам, разница по группам
    """
    competition = workspace.competition
    unit_col_nm = competition.get_required('unit_col_nm')
    unit_score_col_nm = competition.get_required('unit_score_col_nm')

    base_df, cand_df = _paired_units(workspace=workspace, base_nm=args.base, cand_nm=args.cand, lane=args.lane)

    base_score = workspace.score(unit_df=base_df)
    cand_score = workspace.score(unit_df=cand_df)
    for run_nm, score in [(args.base, base_score), (args.cand, cand_score)]:
        if not np.isfinite(score):
            raise ValueError(f"Метрика прогона {run_nm} на общих единицах в дорожке {args.lane} не определена: "
                             f"нет ни одной единицы с посчитанным скором. Сравнивать нечего")

    line_list = [
        f"{args.cand} против {args.base}, дорожка {args.lane}, общих единиц ({unit_col_nm}): {len(base_df)}",
        f"метрика: база {base_score:.5f}, кандидат {cand_score:.5f}, разница {cand_score - base_score:+.5f}"
    ]

    delta = _bootstrap_delta(workspace=workspace, base_df=base_df, cand_df=cand_df, sample_unit_cnt=len(base_df))
    if len(delta) == 0:
        line_list.append(f"бутстрап по единицам: не посчитан, метрика не определена ни на одной из {bootstrap_resample_cnt} выборок")
    else:
        low, high = np.percentile(delta, [2.5, 97.5])
        resample_desc = f"{bootstrap_resample_cnt} выборок"
        if len(delta) < bootstrap_resample_cnt:
            resample_desc += f", из них {bootstrap_resample_cnt - len(delta)} отброшено: метрика на них не определена"
        line_list.append(f"бутстрап по единицам ({resample_desc}): SD разницы {delta.std():.5f}, 95% интервал [{low:+.5f}, {high:+.5f}], "
                         f"доля выборок с разницей > 0: {(delta > 0).mean():.2f}")

    unit_delta = cand_df[unit_score_col_nm].values - base_df[unit_score_col_nm].values
    win_cnt = int((unit_delta > zero_delta_threshold).sum())
    lose_cnt = int((unit_delta < -zero_delta_threshold).sum())
    unknown_cnt = int(np.isnan(unit_delta).sum())
    unit_desc = (f"по единицам ({unit_score_col_nm}): кандидат лучше на {win_cnt}, хуже на {lose_cnt}, "
                 f"без изменений на {len(base_df) - win_cnt - lose_cnt - unknown_cnt}")
    if unknown_cnt > 0:
        unit_desc += f", скор не посчитан на {unknown_cnt}"
    line_list.append(f"{unit_desc}; sign test p = {_sign_test_pvalue(win_cnt=win_cnt, lose_cnt=lose_cnt):.3f}")

    group_col_nm = competition.group_col_nm
    if group_col_nm is not None and group_col_nm in base_df.columns:
        line_list += _group_delta_line_list(workspace=workspace, base_df=base_df, cand_df=cand_df, group_col_nm=group_col_nm)

    # из чего собрана метрика: у каждого соревнования свои компоненты, поэтому печатаем все, что вернул metric.py
    for run_nm, unit_df in [(args.base, base_df), (args.cand, cand_df)]:
        detail_list = []
        for key, value in workspace.score_detail(unit_df=unit_df).items():
            if key == 'score':
                continue
            if isinstance(value, float):
                detail_list.append(f"{key} {value:.5f}")
            else:
                detail_list.append(f"{key} {value}")
        line_list.append(f"состав метрики {run_nm}: {', '.join(detail_list)}")

    return '\n'.join(line_list)


def _lb_noise_row(workspace, base_nm, cand_nm, lane, public_unit_cnt, public_score_dict):
    base_df, cand_df = _paired_units(workspace=workspace, base_nm=base_nm, cand_nm=cand_nm, lane=lane)
    delta = _bootstrap_delta(workspace=workspace, base_df=base_df, cand_df=cand_df, sample_unit_cnt=public_unit_cnt)
    if len(delta) == 0:
        raise ValueError("метрика не определена ни на одной выборке")

    fact_str = '-'
    ratio_str = '-'
    public_delta = public_score_dict.get(cand_nm, float('nan')) - public_score_dict.get(base_nm, float('nan'))
    if pd.notna(public_delta):
        fact_str = f"{public_delta:+.{workspace.competition.lb_decimal_cnt}f}"
        if delta.std() > 0:
            ratio_str = f"{abs(public_delta) / delta.std():.1f}"

    val_delta = workspace.score(unit_df=cand_df) - workspace.score(unit_df=base_df)

    return ' | '.join([f"{cand_nm} - {base_nm}", f"{delta.std():.5f}", fact_str, ratio_str, f"{val_delta:+.5f}"])


def lb_noise(workspace, args):
    """
    Оценка шума публичного лидерборда: бутстрап выборок размером с паблик по результатам валидации

    Для базы - SD самого скора, для каждого кандидата - SD парной разницы с базой. Рядом - фактическая разница
    на паблике, если оба публичных скора есть в реестре
    """
    competition = workspace.competition
    public_unit_cnt = competition.get_required('public_unit_cnt')

    base_df = workspace.get_unit_df(run_nm=args.base, lane=args.lane)
    base_score = _bootstrap_score(workspace=workspace, unit_df=base_df, sample_unit_cnt=public_unit_cnt)
    if len(base_score) == 0:
        raise ValueError(f"Метрика прогона {args.base} в дорожке {args.lane} не определена ни на одной выборке размером с паблик")

    line_list = [
        f"Шум публичного лидерборда по дорожке {args.lane}. Паблик - около {public_unit_cnt} единиц, "
        f"ниже бутстрап выборок такого размера ({bootstrap_resample_cnt} выборок).",
        f"Табло округляется до {competition.lb_decimal_cnt} знаков.",
        f"SD скора {args.base} на выборке размером с паблик: {base_score.std():.5f}",
        "",
        "кандидат - база | SD Δ на паблике | Δ public факт | модуль Δ public в SD | Δ валидации"
    ]

    public_score_dict = {}
    if workspace.run_df is not None:
        public_score_dict = dict(zip(workspace.run_df['label'], workspace.run_df['public_lb']))

    for cand_nm in args.cand_list:
        # кандидат, по которому посчитать нельзя (нет в дорожке, нет общих единиц), не должен обрывать таблицу по остальным
        try:
            line_list.append(_lb_noise_row(workspace=workspace, base_nm=args.base, cand_nm=cand_nm, lane=args.lane,
                                           public_unit_cnt=public_unit_cnt, public_score_dict=public_score_dict))
        except ValueError as exc:
            line_list.append(f"{cand_nm} - {args.base} | не посчитано: {exc}")

    return '\n'.join(line_list)


def set_verdict(workspace, args):
    # сначала проверяются все названия и только потом пишется вердикт: иначе при одной опечатке его получила бы только часть списка
    for run_nm in args.run_list:
        _check_run_nm(workspace=workspace, run_nm=run_nm)

    workspace.add_event(f"вердикт аудитора '{args.verdict}': {', '.join(args.run_list)}. Причина: {args.reason}")
    for run_nm in args.run_list:
        workspace.set_verdict(run_nm=run_nm, verdict=args.verdict)

    return f"Вердикт '{args.verdict}' записан для {len(args.run_list)} прогонов"


def set_final_picks(workspace, args):
    slot_cnt = workspace.competition.final_slot_cnt
    pick_nm_list = [pick.run for pick in args.pick_list]

    if len(pick_nm_list) > slot_cnt:
        raise ValueError(f"Выбрано прогонов: {len(pick_nm_list)}, а финальных слотов {slot_cnt}")
    if len(set(pick_nm_list)) != len(pick_nm_list):
        raise ValueError(f"В выборе один прогон указан дважды: {pick_nm_list}")

    for run_nm in pick_nm_list:
        _check_run_nm(workspace=workspace, run_nm=run_nm)
        # жесткое правило harness, а не пожелание в промпте: финалить можно только то, что принял аудитор
        if workspace.verdict_dict.get(run_nm) != 'принять':
            raise ValueError(f"Прогон '{run_nm}' нельзя финалить: вердикт аудитора - '{workspace.verdict_dict.get(run_nm, 'не смотрел')}'. "
                             f"Выбери из прогонов с вердиктом 'принять' или скажи в ответе, что нужен аудит")
        # прогон из register_run существует только локально: финальным на Kaggle можно отметить то, что туда отправлено
        if not workspace.is_submitted(run_nm=run_nm):
            raise ValueError(f"Прогон '{run_nm}' нельзя финалить: он посчитан локально и на Kaggle не отправлялся. "
                             f"Выбери из отправленных посылок")

    workspace.register_final_picks(pick_list=[pick.model_dump() for pick in args.pick_list],
                                   hypothesis=args.hypothesis, expected_metric=args.expected_metric, rule=args.rule)
    workspace.add_event(f"финальный выбор принят и записан в notes/final_picks.md вместе с пререгистрацией: {pick_nm_list}")

    return f"Финальный выбор записан: {pick_nm_list}"


def set_line_review(workspace, args):
    """
    Запись разбора решений команды по линиям работы: для каждой пары "изменение - база" - что решила команда
    и было ли это решение обосновано данными или принято по шуму
    """
    for review in args.review_list:
        _check_run_nm(workspace=workspace, run_nm=review.cand)
        _check_run_nm(workspace=workspace, run_nm=review.base)

    workspace.register_line_review(review_list=[review.model_dump() for review in args.review_list])
    noise_cnt = sum(review.verdict == 'по шуму' for review in args.review_list)
    workspace.add_event(f"разбор решений записан в notes/line_review.md: {len(args.review_list)} пар, из них 'по шуму' - {noise_cnt}")

    return f"Разбор записан: {len(args.review_list)} пар"


def register_run(workspace, args):
    """
    Добавление нового прогона в реестр. Сначала все проверки и расчет метрики, и только потом запись:
    после ошибки в реестре не должно остаться половины прогона

    Повторный вызов с тем же названием добавляет прогону еще одну дорожку. Сначала так было нельзя, и на записи
    инженер экспериментов посчитал гибрид в пяти дорожках, а зарегистрировать смог только одну
    """
    unit_col_nm = workspace.competition.get_required('unit_col_nm')

    new_run_flg = args.run not in workspace.get_run_nm_list()
    if not new_run_flg:
        if workspace.is_submitted(run_nm=args.run):
            raise ValueError(f"Прогон '{args.run}' - отправленная посылка, ее результаты дописывать нельзя. Дай новому прогону другое название")
        if args.lane in workspace.get_lane_list(args.run):
            raise ValueError(f"У прогона '{args.run}' уже есть результаты в дорожке '{args.lane}'")
    if len(args.parent) > 0:
        _check_run_nm(workspace=workspace, run_nm=args.parent)

    result_file_nm = workspace.resolve_path(path=args.result_file)
    if not os.path.isfile(result_file_nm):
        raise ValueError(f"Файл {args.result_file} не найден. Список файлов дает list_files")
    try:
        result_df = pd.read_csv(result_file_nm)
    except ValueError as exc:
        # сюда же попадают пустой файл и файл не в utf-8: у pandas это наследники ValueError
        raise ValueError(f"Файл {args.result_file} не читается как csv: {exc}")
    if len(result_df) == 0:
        raise ValueError(f"В файле {args.result_file} нет ни одной строки с результатами")

    # новый прогон обязан лечь в ту же таблицу, что и остальные, иначе его не с чем будет сравнить попарно
    if workspace.unit_df is not None:
        need_col_list = [col for col in workspace.unit_df.columns if col not in ('candidate', 'lane')]
    else:
        need_col_list = [unit_col_nm]
    missing_col_list = [col for col in need_col_list if col not in result_df.columns]
    if len(missing_col_list) > 0:
        raise ValueError(f"В {args.result_file} нет колонок {missing_col_list}. Нужны: {need_col_list}")

    if result_df[unit_col_nm].duplicated().any():
        dup_list = list(result_df.loc[result_df[unit_col_nm].duplicated(), unit_col_nm].unique()[:5])
        raise ValueError(f"В {args.result_file} единицы повторяются ({unit_col_nm}: {dup_list}). Нужна одна строка на единицу")

    # прогон в дорожке, которой ни у кого нет, или на другом наборе единиц, чем у родителя, попарно сравнить не с чем
    if workspace.unit_df is not None:
        lane_list = sorted(workspace.unit_df['lane'].unique())
        if args.lane not in lane_list:
            raise ValueError(f"Дорожки '{args.lane}' нет в результатах валидации. Есть: {lane_list}")
        if len(args.parent) > 0 and args.lane in workspace.get_lane_list(args.parent):
            parent_unit_set = set(workspace.get_unit_df(run_nm=args.parent, lane=args.lane)[unit_col_nm])
            unit_set = set(result_df[unit_col_nm])
            if unit_set != parent_unit_set:
                raise ValueError(f"Набор единиц в {args.result_file} не совпадает с родителем '{args.parent}' в дорожке '{args.lane}': "
                                 f"у родителя {len(parent_unit_set)}, в файле {len(unit_set)}, "
                                 f"лишних {len(unit_set - parent_unit_set)}, не хватает {len(parent_unit_set - unit_set)}")

    score = workspace.score(unit_df=result_df)
    if not np.isfinite(score):
        raise ValueError(f"Метрика по {args.result_file} не определена: нет ни одной единицы с посчитанным скором. Прогон не зарегистрирован")

    workspace.add_run(run_nm=args.run, parent_nm=args.parent, description=args.description, lane=args.lane, result_df=result_df)
    if new_run_flg:
        workspace.add_event(f"прогон {args.run} добавлен в реестр: {len(result_df)} единиц в дорожке {args.lane}, метрика {score:.5f}")
        return f"Прогон {args.run} зарегистрирован: {len(result_df)} единиц в дорожке {args.lane}, метрика {score:.5f}"
    else:
        workspace.add_event(f"прогону {args.run} добавлена дорожка {args.lane}: {len(result_df)} единиц, метрика {score:.5f}")
        return f"Прогону {args.run} добавлена дорожка {args.lane}: {len(result_df)} единиц, метрика {score:.5f}"
