import json
import os
import re

import pandas as pd

no_private_desc = "нет приватного скора"
# чем субагент мог бы дотянуться до файлов вне рабочей папки: выход наверх, абсолютный путь из кода, слово private
outside_pattern = re.compile(r"\.\.[/\\]|'\.\.'|\"\.\.\"|pardir|__file__|getcwd|abspath|realpath|private", re.IGNORECASE)


def get_outside_call_list(trace):
    """
    Вызовы инструментов, в которых субагент мог выйти за рабочую папку. run_python - не песочница, и файл
    с приватными скорами лежит на том же диске, поэтому "агенты привата не видели" проверяется по трейсу:
    в аргументах и коде всех вызовов ищутся выход наверх по папкам и слово private

    :param trace: объект Trace прошедшего прогона
    :return: список событий tool_call, которые стоит посмотреть глазами. Пустой, если таких нет
    """
    outside_call_list = []
    for event in trace.event_list:
        if event['event_nm'] != 'tool_call':
            continue
        call_text = json.dumps(event['attr_dict'], ensure_ascii=False) + '\n' + event['body']
        if outside_pattern.search(call_text) is not None:
            outside_call_list.append(event)

    return outside_call_list


def private_check(workspace, trace):
    """
    Сверка финального выбора с приватным лидербордом. Вызывается из main после того, как диспетчер закончил:
    в рабочую папку и в промпты эти числа не попадают

    :param workspace: объект Workspace
    :param trace: объект Trace прошедшего прогона, по нему проверяется, что субагенты не ходили за рабочую папку
    :return: текст с таблицей или None, если у кейса нет приватных скоров
    """
    private_file_nm = os.path.join(workspace.case_dir, 'private', 'private_scores.csv')
    if not os.path.isfile(private_file_nm) or workspace.run_df is None:
        return None

    private_df = pd.read_csv(private_file_nm)
    # у прогонов, которые зарегистрировал сам harness, приватного скора нет: их никто не отправлял
    run_df = workspace.run_df.merge(private_df[['label', 'private_lb']], on='label', how='left')
    score_df = run_df[run_df['private_lb'].notna()]
    slot_cnt = workspace.competition.final_slot_cnt
    decimal_cnt = workspace.competition.lb_decimal_cnt

    line_list = ["Сверка с приватным лидербордом (в рабочую папку и в промпты эти числа не попадали)"]
    tool_call_cnt = sum(event['event_nm'] == 'tool_call' for event in trace.event_list)
    outside_call_list = get_outside_call_list(trace)
    if len(outside_call_list) == 0:
        line_list.append(f"По трейсу: ни в одном из {tool_call_cnt} вызовов инструментов нет выхода из рабочей папки и обращений к private")
    else:
        event_num_list = [event['event_num'] for event in outside_call_list]
        line_list.append(f"ВНИМАНИЕ: в {len(outside_call_list)} из {tool_call_cnt} вызовов инструментов есть выход из рабочей папки или слово private, "
                         f"сверке ниже верить нельзя, пока они не просмотрены. События трейса: {event_num_list}")
    if len(score_df) == 0:
        line_list.append("Ни у одного прогона из реестра нет приватного скора, сверять не с чем")
        return '\n'.join(line_list)

    if len(workspace.final_pick_list) > 0:
        line_list.append(f"Выбор harness: {_pick_desc(run_df=run_df, pick_list=workspace.final_pick_list, decimal_cnt=decimal_cnt)}")
    else:
        line_list.append("Выбор harness: финальные сабмиты не выбраны")

    team_pick_list = workspace.competition.team_final_pick_list
    if len(team_pick_list) > 0:
        team_desc = _pick_desc(run_df=run_df, pick_list=team_pick_list, decimal_cnt=decimal_cnt)
        line_list.append(f"Что выбрала команда в реальности: {team_desc}")

    # для сравнения: что дал бы выбор просто лучших по паблику и какой итог был возможен в принципе
    public_top_df = score_df.sort_values(['public_lb', 'submitted_at'], ascending=False).head(slot_cnt)
    line_list.append(f"{slot_cnt} лучших по public {list(public_top_df['label'])} -> итог {public_top_df['private_lb'].max():.{decimal_cnt}f}")

    best_row = score_df.loc[score_df['private_lb'].idxmax()]
    line_list.append(f"Лучший возможный выбор: {best_row['label']} (public {_score_str(score=best_row['public_lb'], decimal_cnt=decimal_cnt)}, "
                     f"private {best_row['private_lb']:.{decimal_cnt}f})")

    if len(workspace.line_review_list) > 0:
        line_list += ["", _line_review_check(workspace=workspace, run_df=run_df)]

    return '\n'.join(line_list)


def _score_str(score, decimal_cnt):
    if pd.isna(score):
        return '-'
    else:
        return f"{score:.{decimal_cnt}f}"


def _pick_desc(run_df, pick_list, decimal_cnt):
    pick_desc_list = []
    private_score_list = []
    for run_nm in pick_list:
        pick_df = run_df[run_df['label'] == run_nm]
        if len(pick_df) == 0:
            pick_desc_list.append(f"{run_nm} (нет в реестре)")
            continue

        row = pick_df.iloc[0]
        public_str = _score_str(score=row['public_lb'], decimal_cnt=decimal_cnt)
        if pd.isna(row['private_lb']):
            pick_desc_list.append(f"{run_nm} (public {public_str}, {no_private_desc})")
        else:
            pick_desc_list.append(f"{run_nm} (public {public_str}, private {row['private_lb']:.{decimal_cnt}f})")
            private_score_list.append(row['private_lb'])

    # итог выбора - лучший из приватных скоров: на Kaggle засчитывается лучший из отмеченных сабмитов
    if len(private_score_list) == 0:
        return f"{', '.join(pick_desc_list)} -> итог неизвестен"
    else:
        return f"{', '.join(pick_desc_list)} -> итог {max(private_score_list):.{decimal_cnt}f}"


def _line_review_check(workspace, run_df):
    """
    Сверка разбора решений с приватом. Решение команды считается верным, если "принято" и на привате кандидат
    выше базы, либо "закрыто" и кандидат не выше базы. Разбор прав, когда назвал "по шуму" решение,
    которое оказалось неверным, или "обосновано" - решение, которое оказалось верным
    """
    private_dict = dict(zip(run_df['label'], run_df['private_lb']))
    public_dict = dict(zip(run_df['label'], run_df['public_lb']))
    decimal_cnt = workspace.competition.lb_decimal_cnt

    # ширина первой колонки - по самому длинному названию пары: у прогонов инженера экспериментов названия длиннее, чем у посылок
    pair_len = max(len(f"{review['cand']} - {review['base']}") for review in workspace.line_review_list) + 2
    pair_len = max(pair_len, 16)
    line_list = ["Разбор решений команды против привата",
                 f"{'пара':<{pair_len}}{'Δ public':<10}{'команда':<10}{'разбор':<12}{'Δ private':<11}{'команда права':<15}разбор прав"]
    checked_cnt = 0
    team_ok_cnt = 0
    review_ok_cnt = 0
    noise_cnt = 0
    noise_ok_cnt = 0
    for review in workspace.line_review_list:
        pair_nm = f"{review['cand']} - {review['base']}"
        private_delta = private_dict[review['cand']] - private_dict[review['base']]
        public_delta = public_dict[review['cand']] - public_dict[review['base']]
        if pd.isna(public_delta):
            public_str = '-'
        else:
            public_str = f"{public_delta:+.{decimal_cnt}f}"

        # пару, где у одного из прогонов нет приватного скора, сверить нельзя: показываем ее, но в счет она не идет
        if pd.isna(private_delta):
            line_list.append(f"{pair_nm:<{pair_len}}{public_str:<10}{review['team_decision']:<10}{review['verdict']:<12}{no_private_desc}")
            continue
        checked_cnt += 1

        # скоры на табло округлены, равные считаются точно равными. Порог стоит только от ошибок вычитания float
        if review['team_decision'] == 'принято':
            team_ok_flg = private_delta > 1e-9
        else:
            team_ok_flg = private_delta <= 1e-9

        if review['verdict'] == 'по шуму':
            review_ok_flg = not team_ok_flg
            noise_cnt += 1
            noise_ok_cnt += review_ok_flg
        else:
            review_ok_flg = team_ok_flg

        team_ok_cnt += team_ok_flg
        review_ok_cnt += review_ok_flg
        line_list.append(f"{pair_nm:<{pair_len}}{public_str:<10}{review['team_decision']:<10}{review['verdict']:<12}"
                         f"{private_delta:<+11.{decimal_cnt}f}{'да' if team_ok_flg else 'нет':<15}{'да' if review_ok_flg else 'нет'}")

    review_cnt = len(workspace.line_review_list)
    if checked_cnt == 0:
        # так бывает, когда разбирали только локальные прогоны: их никто не отправлял, и приват про них ничего не скажет
        line_list.append(f"Решений разобрано: {review_cnt}, приватного скора нет ни у одной пары - сверять не с чем.")
        return '\n'.join(line_list)
    if checked_cnt < review_cnt:
        line_list.append(f"Решений разобрано: {review_cnt}, из них с приватным скором у обоих прогонов: {checked_cnt}. Дальше - только по ним.")
    else:
        line_list.append(f"Решений разобрано: {review_cnt}.")
    line_list.append(f"Команда оказалась права по привату в {team_ok_cnt}, разбор - в {review_ok_cnt}.")
    line_list.append(f"Разбор назвал 'по шуму' {noise_cnt} решений, из них неверными на привате оказались {noise_ok_cnt}.")

    return '\n'.join(line_list)
