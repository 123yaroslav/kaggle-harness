import pandas as pd
import numpy as np

import io
import os
import re
import sys
import json
import glob
import subprocess
import importlib.util
from datetime import datetime, timezone

from metric import competition_score, score_delta, film_adj

# Сборка данных кейса biohub: реестр посылок, приватные скоры и по-фильмовая валидация.
# Скрипт читает исходники вне репозитория (рабочая папка соревнования на внешнем диске и ~/farm_local) и зовет kaggle CLI,
# результат лежит в репозитории, перезапускать нужно только если меняется состав дорожек.
# Запуск из любой папки: python cases/biohub/build_case.py
#
# На диск с исходниками ничего не пишется. Приватные скоры попадают только в private/private_scores.csv

case_dir = os.path.dirname(os.path.abspath(__file__))
biohub_dir = '/Volumes/T7/biohub'
# полные результаты фермы лежат не на внешнем диске, а в домашней папке (диск в тот день отваливался)
farm_result_dir = os.path.expanduser('~/farm_local/results/final')
competition_nm = 'biohub-cell-tracking-during-development'

lane_src_dict = {'in_sample': 'full', 'honest_oof': 'oof', 'honest_oofm': 'oofm'}

# Конфигурации шага форков вокруг V12: смещение кропа divclf, порог добавления форка, порог удаления, макс. расстояние между сестрами.
# Колонки: кандидат, имя строки в honest_oof/leak.py (если она там есть), offset, add, prune, sister, метка посылки, совпадение, примечание
fork_config_list = [
    ('V12', 'V12', 'DEF', 0.8, None, 18, 'V12', 'exact', ''),
    ('FA', 'FA', 'HALF', 0.8, None, 18, 'FA', 'exact', ''),
    ('FAS', None, 'HALF', 0.85, None, 13, 'FAS', 'exact', ''),
    ('PR07', None, 'DEF', 0.8, 0.7, 18, 'PR07', 'exact', ''),
    ('TAP', 'TAP (TA+sis13)', '0', 0.85, 0.9, 13, 'TAP', 'exact', ''),
    ('TP2', 'TP2fork (T+sis14)', '0', 0.8, 0.9, 14, 'TP2', 'approx',
     "только шаг форков: в replay subvox alpha 0.5, у посылки 0.3"),
    ('T', 'T', '0', 0.8, 0.9, 18, '', 'not_submitted', "V12 + offset 0 + prune 0.9, не посылалась"),
    ('TA', 'TA', '0', 0.85, 0.9, 18, '', 'not_submitted', "T + add 0.85, не посылалась"),
    ('TP', 'TP (T+sis13)', '0', 0.8, 0.9, 13, '', 'not_submitted', "T + max sister 13, не посылалась"),
    # остальные строки leak.py - точки сетки вокруг кандидатов, ни одна не посылалась
    ('V12thr@zero', 'V12thr@zero', '0', 0.8, None, 18, '', 'not_submitted', "точка сетки из leak.py"),
    ('TA+sis14', 'TA+sis14', '0', 0.85, 0.9, 14, '', 'not_submitted', "точка сетки из leak.py"),
    ('T add.9', 'T add.9', '0', 0.9, None, 18, '', 'not_submitted', "точка сетки из leak.py"),
    ('T prune.95', 'T prune.95', '0', 0.8, 0.95, 18, '', 'not_submitted', "точка сетки из leak.py"),
    ('add.9/prune.95', 'add.9/prune.95', '0', 0.9, 0.95, 18, '', 'not_submitted', "точка сетки из leak.py"),
    ('add.85/prune.95', 'add.85/prune.95', '0', 0.85, 0.95, 18, '', 'not_submitted', "точка сетки из leak.py"),
    ('add.85/prune.95/sis13', 'add.85/prune.95/sis13', '0', 0.85, 0.95, 13, '', 'not_submitted', "точка сетки из leak.py"),
    ('def .8/.9', 'def .8/.9', 'DEF', 0.8, 0.9, 18, '', 'not_submitted', "точка сетки из leak.py"),
    ('def .85/.9', 'def .85/.9', 'DEF', 0.85, 0.9, 18, '', 'not_submitted', "точка сетки из leak.py"),
    ('def .8/.9/sis13', 'def .8/.9/sis13', 'DEF', 0.8, 0.9, 13, '', 'not_submitted', "точка сетки из leak.py"),
    ('half .8/.9', 'half .8/.9', 'HALF', 0.8, 0.9, 18, '', 'not_submitted', "точка сетки из leak.py"),
    ('half .85/.9', 'half .85/.9', 'HALF', 0.85, 0.9, 18, '', 'not_submitted', "точка сетки из leak.py"),
    ('half .8/.9/sis13', 'half .8/.9/sis13', 'HALF', 0.8, 0.9, 13, '', 'not_submitted', "точка сетки из leak.py"),
    ('half .85/.9/sis13', 'half .85/.9/sis13', 'HALF', 0.85, 0.9, 13, '', 'not_submitted', "точка сетки из leak.py"),
    ('half .9/.95', 'half .9/.95', 'HALF', 0.9, 0.95, 18, '', 'not_submitted', "точка сетки из leak.py, в groups.py она же FA-t9")
]

fork_replay_file_list = [
    'honest_oof/rep_zero.jsonl',
    'honest_oof/rep_pod.jsonl',
    'honest_oof/rep_oofm.jsonl',
    # точный replay PR07 сделали отдельно, в день дедлайна
    'research/final_picks_work/rep_p7.jsonl'
]

b44_lkb_nm = 's.DEEPCENTER_GAP_THRESHOLD=0.2+s.OUTPUT_MIN_TRACK_LEN=6+s.SAFE_DIV_FRAME_FRAC_CAP=0.0028' \
             '+s.LEAF_PRUNE_MIN_EDGE_PROB=0.0+s.GAP2_MAX_TOTAL_UM=9.0+p.0.15'

own_head_note = "своя голова координат в fold-варианте: обучена без этих фильмов, у посылки - на 100 фильмах"
k1_note = "без subvox"
f1_trunc_note = "float-координаты усечены до целых, как их читает грейдер"
f1_float_note = "float-координаты как есть, если бы грейдер их не усекал"
subvox_note = "настройки subvox как у посылки, но граф IF + форки V2@0.8, а у посылки D08"

# Все остальные дорожки. Колонки: дорожка, кандидат, метка посылки, совпадение, чем читать, файл, ключ внутри файла, примечание.
# Совпадение - про конфигурацию кандидата внутри дорожки. Чем сама дорожка отличается от посылки (веса, predict, набор фильмов),
# написано в lane_desc_dict
source_list = [
    # пост-процессинг продакшена на кэше предсказаний, 114 фильмов, база - ноутбук T
    ('ppprod', 'V12', 'V12', 'exact', 'jsonl', 'ppprod/scores/sweep1.jsonl', 'pp::v12prod', ''),
    ('ppprod', 'T', '', 'not_submitted', 'jsonl', 'ppprod/scores/sweep1.jsonl', 'pp::tune', "V12 + offset 0 + prune 0.9, не посылалась"),
    ('ppprod', 'TP', '', 'not_submitted', 'jsonl', 'ppprod/scores/sweep1.jsonl', 'pp::MODEL_FORKS_MAX_SISTER_UM=13.0', "T + max sister 13, не посылалась"),
    ('ppprod', 'TP2', 'TP2', 'exact', 'jsonl', 'ppprod/scores/sweep1.jsonl', 'pp::COMBO_S14_A03', ''),

    # ноутбуки посылок целиком на арендованном GPU
    ('evalpod', 'V12', 'V12', 'exact', 'jsonl', 'evalpod/results/scores_main.jsonl,evalpod/results/scores_B.jsonl,evalpod/results/scores_C.jsonl', 'pmin0.1::prod', ''),
    ('evalpod', 'LNK', 'LNK', 'exact', 'jsonl', 'evalpod/results/scores_NA.jsonl,evalpod/results/scores_NB.jsonl', 'pmin0.1::prod', "только партии A и B, 85 фильмов"),

    ('farm', 'V12', 'V12', 'exact', 'farm', farm_result_dir, 'V12', ''),
    ('farm', 'FA', 'FA', 'exact', 'farm', farm_result_dir, 'FA', ''),
    ('farm', 'FAS', 'FAS', 'exact', 'farm', farm_result_dir, 'FAS', ''),
    ('farm', 'TAP', 'TAP', 'exact', 'farm', farm_result_dir, 'TAP', ''),
    ('farm', 'TP2', 'TP2', 'exact', 'farm', farm_result_dir, 'TP2', ''),
    ('farm', 'T', '', 'not_submitted', 'farm', farm_result_dir, 'T', "ноутбук получен из TAP возвратом max sister 18 и add 0.8, не посылалась"),
    ('farm', 'TA', '', 'not_submitted', 'farm', farm_result_dir, 'TA', "ноутбук получен из TAP возвратом max sister 18, не посылалась"),

    # прогоны ноутбуков на Kaggle по train-фильмам. Скрипты команды по ним только печатали таблицу, строк по фильмам на диске нет
    # (кроме двух прогонов audit44), поэтому пересчитываю тем же портом метрики из сохраненных submission.csv
    ('visible4', 'E1', 'E1', 'approx', 'kernel', 'kern/out/bh-ifdiag-off/submission.csv', '', "ноутбук IF с выключенным flow-relink"),
    ('visible4', 'IF', 'IF', 'exact', 'kernel', 'kern/out/bh-ifdiag-on/submission.csv', '', ''),
    ('visible4', 'LNK', 'LNK', 'exact', 'kernel', 'coordhead/audit/lnk/submission.csv', '', ''),
    ('visible4', 'V12', 'V12', 'exact', 'kernel', 'coordhead/audit/v12/submission.csv', '', "публичная голова координат могла видеть эти фильмы при обучении"),
    ('visible4', 'V12O', 'V12O', 'approx', 'kernel', 'coordhead/audit/v12own_prelim/submission.csv', '', "предварительная своя голова (52 фильма), у посылки финальная на 100 фильмах"),

    ('audit8', 'LNK', 'LNK', 'exact', 'kernel', 'coordhead/audit8/lnk/submission.csv', '', ''),
    ('audit8', 'V12', 'V12', 'exact', 'kernel', 'coordhead/audit8/v12/submission.csv', '', ''),
    ('audit8', 'V12O', 'V12O', 'approx', 'kernel', 'coordhead/audit8/own/submission.csv', '', own_head_note),

    ('audit44', 'V12', 'V12', 'exact', 'kernel', 'coordhead/audit44/v12/submission.csv', '', ''),
    ('audit44', 'V12O', 'V12O', 'approx', 'kernel', 'coordhead/audit44/ownp/submission.csv', '', own_head_note),
    ('audit44', 'FA', 'FA', 'exact', 'kernel', 'lastaudit/out/bh-a44-fa/submission.csv', '', ''),

    ('audit_d8', 'V12', 'V12', 'exact', 'kernel', 'lastaudit/out/bh-ad8-v12/submission.csv', '', ''),
    ('audit_d8', 'FA', 'FA', 'exact', 'kernel', 'lastaudit/out/bh-ad8-fa/submission.csv', '', ''),

    # ранние дорожки: replay пост-процессинга на кэше предсказаний публичных весов (46 фильмов)
    ('cache46', 'E1', 'E1', 'exact', 'report', 'cache/replay/prod/report.json', '', ''),
    ('cache46', 'E3', 'E3', 'exact', 'report', 'calib/in_e3/report.json', '', ''),
    ('cache46', 'E4', 'E4', 'exact', 'report', 'calib/in_e4/report.json', '', ''),
    ('cache46', 'IF', 'IF', 'exact', 'rows', 'edgefix/results/main/IF.json', '', ''),
    ('cache46', 'D08', 'D08', 'exact', 'rows', 'coords/results/d08.json', 'round', ''),
    ('cache46', 'F1', 'F1', 'exact', 'rows', 'coords/results/d08.json', 'f1_trunc', f1_trunc_note),
    ('cache46', 'F1_float', 'F1', 'approx', 'rows', 'coords/results/d08.json', 'float', f1_float_note),
    ('cache46', 'SV', 'SV', 'exact', 'rows', 'coords/results/d08sv.json', 'round', ''),
    ('cache46', 'LB3', 'LB3', 'approx', 'fork', 'ppsweep/work/res/S_MOTION_RELINK_LEARNED_BONUS=3.0.json', '', "на базе D08 без subvox, посылка на базе SV"),
    ('cache46', 'LNK', 'LNK', 'exact', 'rows', 'coords/results/lnksv.json', 'round', ''),

    # honest A: 49 фильмов 6bba, которых модель не видела
    ('honest_a', 'E1', 'E1', 'exact', 'report', 'honest/honest_foldA/replay_local_prod/report.json', '', ''),
    ('honest_a', 'E3', 'E3', 'exact', 'report', 'calib/h_e3/report.json', '', ''),
    ('honest_a', 'E4', 'E4', 'exact', 'report', 'calib/h_e4/report.json', '', ''),
    ('honest_a', 'IF', 'IF', 'exact', 'rows', 'edgefix/results/honestA/IF.json', '', ''),
    ('honest_a', 'D08', 'D08', 'exact', 'rows', 'coords/results/d08_hA.json', 'round', ''),
    ('honest_a', 'F1', 'F1', 'exact', 'rows', 'coords/results/d08_hA.json', 'f1_trunc', f1_trunc_note),
    ('honest_a', 'F1_float', 'F1', 'approx', 'rows', 'coords/results/d08_hA.json', 'float', f1_float_note),
    ('honest_a', 'SV', 'SV', 'exact', 'rows', 'coords/results/d08_hAsv.json', 'round', ''),
    ('honest_a', 'LNK', 'LNK', 'approx', 'rows', 'lnk/results/honestA/bl_l0_p0.1@h44.json', '', "гейт LNK поверх E1, без форков D08 и subvox; гейт обучен только на 44b6"),

    # honest B: 20 фильмов 44b6
    ('honest_b', 'E1', 'E1', 'exact', 'per_film', 'honest/honest_foldB/score.json', '', ''),
    ('honest_b', 'D08', 'D08', 'exact', 'rows', 'coords/results/d08_hB.json', 'round', ''),
    ('honest_b', 'F1', 'F1', 'exact', 'rows', 'coords/results/d08_hB.json', 'f1_trunc', f1_trunc_note),
    ('honest_b', 'F1_float', 'F1', 'approx', 'rows', 'coords/results/d08_hB.json', 'float', f1_float_note),

    # свип b44 на базе LNK + k1: те же три набора фильмов, но своя обвязка, с остальными дорожками числа не сравнивать
    ('cache46_b44', 'LK1', 'LK1', 'approx', 'fork', 'b44/res_final3/main/base.json', '', k1_note),
    ('cache46_b44', 'LKB', 'LKB', 'approx', 'fork', f'b44/res_final3/main/{b44_lkb_nm}.json', '', k1_note),
    ('honest_a_b44', 'LK1', 'LK1', 'approx', 'fork', 'b44/res_final3/honestA/base.json', '', k1_note),
    ('honest_a_b44', 'LKB', 'LKB', 'approx', 'fork', f'b44/res_final3/honestA/{b44_lkb_nm}.json', '', k1_note),
    ('honest_b_b44', 'LK1', 'LK1', 'approx', 'fork', 'b44/res_final3/honestB/base.json', '', k1_note),
    ('honest_b_b44', 'LKB', 'LKB', 'approx', 'fork', f'b44/res_final3/honestB/{b44_lkb_nm}.json', '', k1_note),

    # варианты subvox считали не на D08, а на графе IF + форки V2@0.8 (ребра фиксированы, двигаются только координаты)
    ('cache46_ifmf', 'IFMF', '', 'not_submitted', 'rows', 'edgefix/results/main/subvox_main.json', 'base', "IF + форки V2@0.8 без subvox, база этой дорожки"),
    ('cache46_ifmf', 'SV', 'SV', 'approx', 'rows', 'edgefix/results/main/subvox_main.json', 'c14_2_p20|after|capNone|a0.5', subvox_note),
    ('cache46_ifmf', 'SVA', 'SVA', 'approx', 'rows', 'edgefix/results/main/subvox_main.json', 'c14_2_p20|after|cap2.0|a1.0', subvox_note),
    ('cache46_ifmf', 'SVB', 'SVB', 'approx', 'rows', 'edgefix/results/main/subvox_main.json', 'c14_2_p20|before|cap2.0|a1.0', subvox_note),
    ('honest_a_ifmf', 'IFMF', '', 'not_submitted', 'rows', 'edgefix/results/honestA/subvox_honestA.json', 'base', "IF + форки V2@0.8 без subvox, база этой дорожки"),
    ('honest_a_ifmf', 'SV', 'SV', 'approx', 'rows', 'edgefix/results/honestA/subvox_honestA.json', 'c14_2_p20|after|capNone|a0.5', subvox_note),
    ('honest_a_ifmf', 'SVA', 'SVA', 'approx', 'rows', 'edgefix/results/honestA/subvox_honestA.json', 'c14_2_p20|after|cap2.0|a1.0', subvox_note),
    ('honest_a_ifmf', 'SVB', 'SVB', 'approx', 'rows', 'edgefix/results/honestA/subvox_honestA.json', 'c14_2_p20|before|cap2.0|a1.0', subvox_note),

    # дообучение основного детектора: проверка весов на двух train-фильмах сразу после обучения
    ('ft_sanity', 'SV', 'SV', 'exact', 'sanity', 'ftpack/ft2/pack/sanity.json', 'orig_primary', "исходные веса основного детектора, как в SV"),
    ('ft_sanity', 'FTPR', 'FTPR', 'exact', 'sanity', 'ftpack/ft2/pack/sanity.json', 'P-R', "дообученные веса основного детектора")
]

# что за пайплайн в дорожке и что в ней честно. Число фильмов считается по данным
lane_desc_dict = {
    'in_sample': ("replay шага форков на выходе продакшен-ноутбука, логиты divclf от ансамбля продакшена (5 CNN TTA2 + 5 GBM)",
                  "ничего: детектор, линкер и divclf видели эти фильмы"),
    'honest_oof': ("тот же replay, логиты divclf от моделей фолда, в обучение которого фильм не попал (2 сида CNN, TTA8, GBM)",
                   "только divclf; детектор и линкер обучены на всех 199 фильмах train"),
    'honest_oofm': ("тот же replay, логиты divclf от одного члена продакшен-ансамбля, не видевшего фильм (сид 0, TTA2, GBM)",
                    "только divclf; детектор и линкер обучены на всех 199 фильмах train"),
    'ppprod': ("пост-процессинг продакшена на кэше предсказаний, свип ручек вокруг ноутбука T",
               "ничего, divclf от ансамбля продакшена"),
    'evalpod': ("ноутбук посылки целиком (predict и пост-процессинг) на арендованном GPU",
                "гейт LNK и LR форков обучались на других фильмах (кроме 3 фильмов из audit8); детектор, линкер и divclf in-sample"),
    'farm': ("пост-процессинг ноутбуков посылок на арендованных GPU, predict один на всех - от ноутбука V12",
             "ничего"),
    'visible4': ("ноутбук посылки на Kaggle, 4 видимых фильма теста (они же есть в train)",
                 "ничего; своя голова координат обучалась без этих фильмов"),
    'audit8': ("ноутбук посылки на Kaggle GPU, 8 train-фильмов",
               "своя голова координат обучалась без этих фильмов, остальное in-sample"),
    'audit44': ("ноутбук посылки на Kaggle GPU, 8 train-фильмов эмбриона 44b6",
                "своя голова координат обучалась без этих фильмов, остальное in-sample"),
    'audit_d8': ("ноутбук посылки на Kaggle GPU, 8 фильмов 6bba с большим числом делений",
                 "ничего"),
    'cache46': ("replay пост-процессинга на кэше предсказаний публичных весов, predict без TTA детекции",
                "детектор и линкер видели эти фильмы; ранкер форков и гейт LNK применялись out-of-fold по фильмам"),
    'honest_a': ("тот же replay на предсказаниях модели, обученной с нуля на 71 фильме 44b6 (один сид)",
                 "детектор, линкер и DeepCenter не видели эмбрион 6bba"),
    'honest_b': ("тот же replay на предсказаниях модели, обученной с нуля на 128 фильмах 6bba (один сид)",
                 "детектор и линкер не видели эмбрион 44b6, DeepCenter in-sample"),
    'cache46_b44': ("свип b44 вокруг LNK + k1 на том же кэше, что cache46; логиты divclf берутся из кэша с допуском 0.5 um по координатам",
                    "как в cache46"),
    'cache46_ifmf': ("тот же кэш, что cache46; граф IF + форки V2@0.8, сравниваются варианты уточнения координат (subvox)",
                     "как в cache46"),
    'honest_a_ifmf': ("то же на предсказаниях honest A", "как в honest_a"),
    'honest_a_b44': ("свип b44 на предсказаниях honest A", "как в honest_a"),
    'honest_b_b44': ("свип b44 на предсказаниях honest B", "как в honest_b"),
    'ft_sanity': ("проверка весов детектора на поде сразу после дообучения: сырой predict и линковка без пост-процессинга посылки",
                  "ничего, оба фильма были в обучении")
}

# все, что посчитано позже этого момента, в кейс попасть не должно
cutoff_dttm = datetime(2026, 9, 29, 23, 30, tzinfo=timezone.utc)

count_col_list = ['edge_tp', 'edge_fp', 'edge_fn', 'division_tp', 'division_fp', 'division_fn']
result_col_list = ['lane', 'candidate', 'note', 'film', 'embryo', 'group'] + count_col_list + ['n_pred', 'n_est', 'adj']


def read_jsonl(file_nm):
    row_list = []
    with open(file_nm) as f:
        for line in f:
            row_list.append(json.loads(line))

    return row_list


def source_path(file_nm):
    if os.path.isabs(file_nm):
        full_file_nm = file_nm
    else:
        full_file_nm = os.path.join(biohub_dir, file_nm)

    modified_dttm = datetime.fromtimestamp(os.path.getmtime(full_file_nm), tz=timezone.utc)
    if modified_dttm > cutoff_dttm:
        raise ValueError(f"Файл {full_file_nm} изменен {modified_dttm:%Y-%m-%d %H:%M} UTC, это позже состояния кейса")

    return full_file_nm


def normalize_row(raw_row):
    # в исходниках два набора имен: у replay-скриптов film / n_pred / adj, у порта метрики name / num_pred_nodes / adj_edge_jaccard
    if 'film' in raw_row:
        film = raw_row['film']
    else:
        film = raw_row['name']

    if 'n_pred' in raw_row:
        n_pred = raw_row['n_pred']
        adj = raw_row['adj']
    else:
        n_pred = raw_row['num_pred_nodes']
        adj = raw_row['adj_edge_jaccard']

    row = {'film': film}
    for col in count_col_list:
        row[col] = int(raw_row[col])
    row['n_pred'] = int(n_pred)
    row['n_est'] = int(raw_row['n_est'])
    row['adj'] = float(adj)

    if row['n_est'] != raw_row['n_est']:
        raise ValueError(f"Нецелое n_est у фильма {film}: {raw_row['n_est']}")

    return row


def load_fork_replay():
    """
    Строки replay шага форков: словарь config -> film -> строка и словарь config -> файл, из которого строка взята
    """
    config_row_dict = {}
    config_file_dict = {}
    for file_nm in fork_replay_file_list:
        for raw_row in read_jsonl(source_path(file_nm)):
            config = raw_row['config']
            if config not in config_row_dict:
                config_row_dict[config] = {}
                config_file_dict[config] = file_nm
            # одна и та же конфигурация V12 есть и в rep_pod, и в rep_p7, берем из того файла, где встретили первой
            if config_file_dict[config] == file_nm:
                config_row_dict[config][raw_row['film']] = raw_row

    return config_row_dict, config_file_dict


def fork_key(src, offset, add, prune, sister):
    # так же, как key() в leak.py: нулевое смещение в дорожке oofm записано как ZERO
    if src == 'oofm' and offset == '0':
        offset = 'ZERO'

    return f"{src}{offset}|{add}|{prune}|{sister}"


def load_metric_port():
    """
    Порт официальной метрики из рабочей папки соревнования (metric/metric.py) и разметка train.
    Этим же портом команда считала прогоны ноутбуков на train-фильмах в audit_score8.py и summ.py
    """
    # иначе python положит .pyc рядом с metric.py, а на диск с исходниками писать нельзя
    sys.dont_write_bytecode = True

    # обычный import не годится: модуль с именем metric уже занят файлом кейса
    spec = importlib.util.spec_from_file_location('biohub_metric_port', source_path('metric/metric.py'))
    metric_port = importlib.util.module_from_spec(spec)
    sys.modules['biohub_metric_port'] = metric_port
    spec.loader.exec_module(metric_port)

    with open(source_path('metric/n_est_train.json')) as f:
        n_est_dict = json.load(f)
    gt_dict = metric_port.load_gt_bundle(source_path('data/labels_bundle/labels.npz'), n_est_dict)

    return metric_port, gt_dict


def score_kernel_output(file_nm, metric_port, gt_dict):
    # по-фильмовые строки метрики для submission.csv, который ноутбук выдал на train-фильмах
    submission_df = pd.read_csv(file_nm)
    film_list = sorted(submission_df['dataset'].unique())

    _, row_list = metric_port.score_submission(submission_df, {film: gt_dict[film] for film in film_list})

    return row_list


def read_source(reader, file_nm, key, metric_port, gt_dict):
    if reader == 'jsonl':
        run_nm, config_nm = key.split('::')
        film_row_dict = {}
        for part_file_nm in file_nm.split(','):
            for raw_row in read_jsonl(source_path(part_file_nm)):
                if raw_row['run'] == run_nm and raw_row['config'] == config_nm:
                    # в sweep1.jsonl несколько фильмов посчитаны дважды, берем последнюю строку, как analyze.py
                    film_row_dict[raw_row['film']] = raw_row
        raw_row_list = list(film_row_dict.values())

    elif reader == 'farm':
        film_row_dict = {}
        for part_file_nm in sorted(glob.glob(os.path.join(file_nm, '*', f'{key}_*.jsonl'))):
            for raw_row in read_jsonl(source_path(part_file_nm)):
                if raw_row['arm'] != key:
                    raise ValueError(f"В файле {part_file_nm} строка чужого прогона: {raw_row['arm']}")
                film_row_dict[raw_row['film']] = raw_row
        raw_row_list = list(film_row_dict.values())

    elif reader == 'kernel':
        raw_row_list = score_kernel_output(source_path(file_nm), metric_port, gt_dict)

    else:
        with open(source_path(file_nm)) as f:
            data = json.load(f)

        if reader == 'report':
            raw_row_list = data['score']['per_film']
        elif reader == 'per_film':
            raw_row_list = data['per_film']
        elif reader == 'rows':
            if key == '':
                raw_row_list = data
            else:
                raw_row_list = data[key]
        elif reader == 'fork':
            raw_row_list = []
            for film_res in data:
                raw_row = dict(film_res['fork'])
                raw_row['film'] = film_res['film']
                raw_row_list.append(raw_row)
        elif reader == 'sanity':
            raw_row_list = data[key]['rows']
        else:
            raise ValueError(f"Неизвестный способ чтения: {reader}")

    row_list = []
    for raw_row in raw_row_list:
        row_list.append(normalize_row(raw_row))

    return row_list


def make_submissions():
    """
    Реестр посылок из kaggle CLI. Публичная часть идет в submissions.csv, приватные скоры - отдельным файлом в private/
    """
    cli_res = subprocess.run(['kaggle', 'competitions', 'submissions', competition_nm, '--csv'], capture_output=True, text=True)
    if cli_res.returncode != 0:
        raise ValueError(f"kaggle CLI вернул ошибку: {cli_res.stderr.strip()}. Проверьте, что CLI установлен и авторизован")

    raw_df = pd.read_csv(io.StringIO(cli_res.stdout))
    raw_df = raw_df.sort_values('date').reset_index(drop=True)

    label_list = []
    for i, description in enumerate(raw_df['description']):
        if i == 0:
            # у первой посылки в описании просто "baseline: ..."
            label_list.append('BASE')
        else:
            label_list.append(description.split(':')[0].strip())

    if len(set(label_list)) != len(label_list):
        raise ValueError(f"Метки посылок повторяются: {label_list}")

    # родитель - метка, с которой начинается описание ("FA: V12 + ..." -> V12), если такая посылка есть
    parent_label_list = []
    for label, description in zip(label_list, raw_df['description']):
        match = re.match(r'^[^:]+:\s*([A-Za-z0-9]+)\s*(\+|with )', description)
        if match and match.group(1) in label_list and match.group(1) != label:
            parent_label_list.append(match.group(1))
        else:
            parent_label_list.append('')

    # то, что видно не из начала описания, а из журнала kern/SUBMISSIONS.md
    parent_override_dict = {
        'E1': 'BASE',   # тот же ноутбук amanatar, конфиг зафиксирован и валидатор выключен
        'LKA': 'LK1',   # "LNK + k1 + ..." - это LK1 с еще одной правкой
        'LT8': 'LK1',
        'LKB': 'LK1'
    }
    for i, label in enumerate(label_list):
        if label in parent_override_dict:
            parent_label_list[i] = parent_override_dict[label]

    submission_df = pd.DataFrame({
        'ref': raw_df['ref'],
        'label': label_list,
        'submitted_at': pd.to_datetime(raw_df['date']).dt.strftime('%Y-%m-%d %H:%M:%S'),
        'description': raw_df['description'],
        'public_lb': raw_df['publicScore'],
        'parent_label': parent_label_list
    })
    submission_df.to_csv(os.path.join(case_dir, 'submissions.csv'), index=False, float_format='%.3f')

    private_df = pd.DataFrame({'ref': raw_df['ref'], 'label': label_list, 'private_lb': raw_df['privateScore']})
    os.makedirs(os.path.join(case_dir, 'private'), exist_ok=True)
    private_df.to_csv(os.path.join(case_dir, 'private', 'private_scores.csv'), index=False, float_format='%.3f')

    print(f"Посылок в реестре: {len(submission_df)}, с {submission_df['submitted_at'].min()} по {submission_df['submitted_at'].max()} UTC")

    return submission_df


def make_validation(submission_df):
    with open(source_path('evalpod/film_groups.json')) as f:
        film_group_dict = json.load(f)

    # группы - три партии фильмов, которые по очереди считали на evalpod
    group_dict = {}
    subgroup_dict = {}
    for subgroup, group in [('held28', 'A36'), ('audit8', 'A36'), ('batchB', 'B49'), ('batchC', 'C29')]:
        for film in film_group_dict[subgroup]:
            group_dict[film] = group
            subgroup_dict[film] = subgroup

    result_list = []
    candidate_list = []

    def add_candidate(lane, candidate, submission_label, match_type, file_nm, key, note, row_list):
        if submission_label != '' and submission_label not in set(submission_df['label']):
            raise ValueError(f"Кандидат {candidate} ссылается на посылку {submission_label}, которой нет в реестре")
        if len(row_list) == 0:
            raise ValueError(f"Для кандидата {candidate} в дорожке {lane} не нашлось ни одной строки: {file_nm} {key}")

        for row in row_list:
            row = dict(row)
            row['lane'] = lane
            row['candidate'] = candidate
            row['note'] = note
            row['embryo'] = row['film'].split('_')[0]
            row['group'] = group_dict.get(row['film'], '')
            result_list.append(row)

        candidate_list.append({
            'lane': lane,
            'candidate': candidate,
            'submission_label': submission_label,
            'match_type': match_type,
            'film_cnt': len(row_list),
            'source_file': file_nm.replace(os.path.expanduser('~'), '~'),
            'source_key': key,
            'note': note
        })

    config_row_dict, config_file_dict = load_fork_replay()
    for lane, src in lane_src_dict.items():
        for candidate, leak_nm, offset, add, prune, sister, submission_label, match_type, note in fork_config_list:
            key = fork_key(src, offset, add, prune, sister)
            row_list = []
            for raw_row in config_row_dict[key].values():
                row_list.append(normalize_row(raw_row))
            add_candidate(lane, candidate, submission_label, match_type, config_file_dict[key], key, note, row_list)
    print(f"Дорожки replay форков собраны: {len(candidate_list)} пар дорожка-кандидат")

    metric_port, gt_dict = load_metric_port()
    for lane, candidate, submission_label, match_type, reader, file_nm, key, note in source_list:
        row_list = read_source(reader, file_nm, key, metric_port, gt_dict)
        add_candidate(lane, candidate, submission_label, match_type, file_nm, key, note, row_list)

    film_df = pd.DataFrame(result_list)[result_col_list]
    film_df = film_df.sort_values(['lane', 'candidate', 'film'], kind='stable').reset_index(drop=True)

    # колонку adj исходные скрипты считали сами, проверяем, что она сходится с формулой
    bad_adj_cnt = 0
    for row in film_df.itertuples():
        expected_adj = film_adj(row.edge_tp, row.edge_fp, row.edge_fn, row.n_pred, row.n_est)
        if np.isnan(expected_adj) and np.isnan(row.adj):
            continue
        if not abs(expected_adj - row.adj) < 1e-9:
            bad_adj_cnt += 1
    if bad_adj_cnt > 0:
        raise ValueError(f"adj не сходится с формулой в {bad_adj_cnt} строках")

    if film_df.duplicated(['lane', 'candidate', 'film']).any():
        raise ValueError("В film_results есть повторы по lane, candidate, film")

    validation_dir = os.path.join(case_dir, 'validation')
    os.makedirs(validation_dir, exist_ok=True)
    film_df.to_csv(os.path.join(validation_dir, 'film_results.csv'), index=False)

    candidate_df = pd.DataFrame(candidate_list)
    candidate_df.to_csv(os.path.join(validation_dir, 'candidates.csv'), index=False)

    lane_list = []
    for lane in candidate_df['lane'].unique():
        lane_film_df = film_df[film_df['lane'] == lane].drop_duplicates('film')
        lane_list.append({
            'lane': lane,
            'film_cnt': len(lane_film_df),
            'film_6bba_cnt': int((lane_film_df['embryo'] == '6bba').sum()),
            'film_44b6_cnt': int((lane_film_df['embryo'] == '44b6').sum()),
            'candidate_cnt': int((candidate_df['lane'] == lane).sum()),
            'pipeline_desc': lane_desc_dict[lane][0],
            'honest_desc': lane_desc_dict[lane][1]
        })
    lane_df = pd.DataFrame(lane_list)
    lane_df.to_csv(os.path.join(validation_dir, 'lanes.csv'), index=False)

    film_list = []
    for film in sorted(film_df['film'].unique()):
        film_list.append({
            'film': film,
            'embryo': film.split('_')[0],
            'group': group_dict.get(film, ''),
            'subgroup': subgroup_dict.get(film, ''),
            'visible_flg': int(film in film_group_dict['visible4']),
            'lane_list': ' '.join(sorted(film_df.loc[film_df['film'] == film, 'lane'].unique()))
        })
    pd.DataFrame(film_list).to_csv(os.path.join(validation_dir, 'films.csv'), index=False)

    print(f"film_results.csv: {len(film_df)} строк, дорожек {len(lane_df)}, фильмов {len(film_list)}")

    return film_df, candidate_df


def parse_leak_table(file_nm):
    """
    Разбор таблицы, которую печатает honest_oof/leak.py: шапка с абсолютным скором V12 и по строке на конфигурацию
    """
    with open(file_nm) as f:
        line_list = f.read().splitlines()

    head = re.match(r'V12 in-sample ([\d.]+) div \((\d+), (\d+), (\d+)\) \| V12 honest ([\d.]+) div \((\d+), (\d+), (\d+)\)', line_list[0])
    base = {
        'in_sample_score': float(head.group(1)),
        'in_sample_div': tuple(int(head.group(i)) for i in (2, 3, 4)),
        'honest_score': float(head.group(5)),
        'honest_div': tuple(int(head.group(i)) for i in (6, 7, 8))
    }

    row_dict = {}
    for line in line_list[2:]:
        if line.strip() == '':
            continue
        part_list = line.split('|')
        in_sample_part = part_list[0][24:]
        honest_part = part_list[1]
        ci = re.search(r'\[([+-][\d.]+),([+-][\d.]+)\]\s+([\d.]+)', honest_part)
        row_dict[line[:24].strip()] = {
            'in_sample_delta': float(in_sample_part.split()[0]),
            'in_sample_div': tuple(int(v) for v in re.search(r'\((\d+), (\d+), (\d+)\)', in_sample_part).groups()),
            'honest_delta': float(honest_part.split()[0]),
            'honest_ci': (float(ci.group(1)), float(ci.group(2))),
            'honest_p': float(ci.group(3)),
            'honest_div': tuple(int(v) for v in re.search(r'\((\d+), (\d+), (\d+)\)', honest_part).groups()),
            'group_delta_list': [float(v) for v in part_list[3].strip().split('/')]
        }

    return base, row_dict


def check_leak_table(film_df, table_file_nm, honest_lane):
    """
    Сверка metric.py с таблицей leak.py: абсолютный скор V12, дельты к V12, счетчики делений, интервалы бутстрапа и дельты по группам.
    Таблица напечатана с 5 знаками (группы и интервалы - с 4), сверяем с точностью до округления
    """
    base, table_row_dict = parse_leak_table(source_path(table_file_nm))

    def lane_candidate_df(lane, candidate):
        return film_df[(film_df['lane'] == lane) & (film_df['candidate'] == candidate)]

    def division_tuple(score):
        return (score['division_tp'], score['division_fp'], score['division_fn'])

    in_sample_base_df = lane_candidate_df('in_sample', 'V12')
    honest_base_df = lane_candidate_df(honest_lane, 'V12')
    in_sample_base = competition_score(in_sample_base_df)
    honest_base = competition_score(honest_base_df)

    print(f"\nСверка с {table_file_nm} (дорожка {honest_lane}), фильмов {honest_base['film_cnt']}")
    print(f"{'строка':<24} {'ожидали':>10} {'получили':>10} {'расхождение':>12}")
    print(f"{'V12 in-sample':<24} {base['in_sample_score']:>10.5f} {in_sample_base['score']:>10.5f} {in_sample_base['score'] - base['in_sample_score']:>+12.1e}")
    print(f"{'V12 honest':<24} {base['honest_score']:>10.5f} {honest_base['score']:>10.5f} {honest_base['score'] - base['honest_score']:>+12.1e}")

    max_diff = max(abs(in_sample_base['score'] - base['in_sample_score']), abs(honest_base['score'] - base['honest_score']))
    bad_cnt = 0
    if division_tuple(in_sample_base) != base['in_sample_div'] or division_tuple(honest_base) != base['honest_div']:
        bad_cnt += 1

    group_mask_list = [
        lambda df: df['embryo'] == '6bba',
        lambda df: df['embryo'] == '44b6',
        lambda df: df['group'] == 'A36',
        lambda df: df['group'] == 'B49',
        lambda df: df['group'] == 'C29'
    ]

    for candidate, leak_nm, _, _, _, _, _, _, _ in fork_config_list:
        if leak_nm is None:
            continue
        expected = table_row_dict[leak_nm]

        in_sample_df = lane_candidate_df('in_sample', candidate)
        honest_df = lane_candidate_df(honest_lane, candidate)
        in_sample_score = competition_score(in_sample_df)
        honest_score = competition_score(honest_df)
        in_sample_delta = in_sample_score['score'] - in_sample_base['score']
        boot = score_delta(honest_df, honest_base_df)

        diff_list = [in_sample_delta - expected['in_sample_delta'], boot['delta'] - expected['honest_delta']]
        # интервалы и доля напечатаны с 4 и 2 знаками
        ci_diff_list = [boot['ci_low'] - expected['honest_ci'][0], boot['ci_high'] - expected['honest_ci'][1]]

        group_diff_list = []
        for group_mask, expected_group_delta in zip(group_mask_list, expected['group_delta_list']):
            group_delta = competition_score(honest_df[group_mask(honest_df)])['score'] \
                          - competition_score(honest_base_df[group_mask(honest_base_df)])['score']
            group_diff_list.append(group_delta - expected_group_delta)

        ok_flg = max(abs(d) for d in diff_list) <= 5.01e-6 \
                 and max(abs(d) for d in ci_diff_list + group_diff_list) <= 5.01e-5 \
                 and abs(boot['p_positive'] - expected['honest_p']) <= 5.01e-3 \
                 and division_tuple(in_sample_score) == expected['in_sample_div'] \
                 and division_tuple(honest_score) == expected['honest_div']
        if not ok_flg:
            bad_cnt += 1
        max_diff = max(max_diff, max(abs(d) for d in diff_list))

        print(f"{leak_nm + ' in-sample d':<36} {expected['in_sample_delta']:>+9.5f} {in_sample_delta:>+9.5f} {diff_list[0]:>+9.1e}   "
              f"honest d {expected['honest_delta']:>+9.5f} {boot['delta']:>+9.5f} {diff_list[1]:>+9.1e}   "
              f"CI [{boot['ci_low']:+.4f},{boot['ci_high']:+.4f}] P>0 {boot['p_positive']:.2f}   {'ok' if ok_flg else 'НЕ СХОДИТСЯ'}")

    print(f"Строк с расхождением: {bad_cnt}, максимальное расхождение по скору и дельтам: {max_diff:.1e}")

    return bad_cnt


def check_recorded_scores(film_df):
    """
    Сверка остальных дорожек с числами, которые команда записала в своих таблицах и заметках
    """
    # дорожка, кандидат, число из заметок, откуда оно
    recorded_list = [
        ('ppprod', 'T', 0.95022, 'ppprod/scores/final_all_114.txt'),
        ('ppprod', 'V12', 0.95022 - 0.00349, 'ppprod/scores/final_all_114.txt'),
        ('ppprod', 'TP2', 0.95022 + 0.00191, 'ppprod/scores/final_all_114.txt'),
        ('ppprod', 'TP', 0.95022 + 0.00177, 'ppprod/scores/final_all_114.txt'),
        ('evalpod', 'V12', 0.94673, 'evalpod/results/table_ABC.txt'),
        ('visible4', 'E1', 0.8974, 'research/calibration.md'),
        ('visible4', 'IF', 0.9285, 'research/calibration.md'),
        ('visible4', 'LNK', 0.95495, 'coordhead/PROGRESS.md'),
        ('visible4', 'V12', 0.96625, 'coordhead/PROGRESS.md'),
        ('visible4', 'V12O', 0.95489, 'coordhead/PROGRESS.md'),
        ('audit8', 'LNK', 0.90557, 'coordhead/PROGRESS.md'),
        ('audit8', 'V12', 0.90285, 'coordhead/PROGRESS.md'),
        ('audit8', 'V12O', 0.91782, 'coordhead/PROGRESS.md'),
        ('audit44', 'V12', 0.95065, 'coordhead/PROGRESS.md'),
        ('audit44', 'V12O', 0.91938, 'coordhead/PROGRESS.md'),
        ('cache46', 'E1', 0.9158, 'research/calibration.md'),
        ('cache46', 'E3', 0.9022, 'research/calibration.md'),
        ('cache46', 'E4', 0.9129, 'research/calibration.md'),
        ('cache46', 'IF', 0.9158 + 0.0199, 'research/edgefix.md'),
        ('cache46', 'D08', 0.9361, 'coords/lanes.md'),
        ('cache46', 'SV', 0.9373, 'coords/lanes.md'),
        ('cache46', 'LNK', 0.9538, 'coords/lanes.md'),
        ('honest_a', 'E1', 0.7726, 'research/honest_lane.md'),
        ('honest_a', 'E3', 0.7596, 'research/calibration.md'),
        ('honest_a', 'E4', 0.7708, 'research/calibration.md'),
        ('honest_a', 'IF', 0.7805, 'research/honest_lane.md'),
        ('honest_a', 'LNK', 0.77645, 'lnk/results/summary.json'),
        ('honest_a', 'D08', 0.7768, 'coords/lanes.md'),
        ('honest_a', 'SV', 0.7787, 'coords/lanes.md'),
        ('honest_b', 'E1', 0.8266, 'research/honest_lane.md'),
        ('honest_b', 'D08', 0.8309, 'coords/lanes.md'),
        ('cache46_ifmf', 'IFMF', 0.96119, 'research/edgefix.md'),
        ('cache46_ifmf', 'SV', 0.96119 + 0.0016, 'research/edgefix.md'),
        ('cache46_ifmf', 'SVB', 0.96119 + 0.0020, 'research/edgefix.md'),
        ('honest_a_b44', 'LK1', 0.78311, 'b44/final3_table.txt'),
        ('honest_b_b44', 'LK1', 0.82926, 'b44/final3_table.txt'),
        ('ft_sanity', 'SV', 0.8727, 'ftpack/ft2/pack/sanity.log'),
        ('ft_sanity', 'FTPR', 0.8890, 'ftpack/ft2/pack/sanity.log')
    ]

    print(f"\nСверка остальных дорожек с записанными числами")
    print(f"{'дорожка':<14} {'кандидат':<9} {'записано':>9} {'получили':>9} {'расхождение':>12}  источник")
    bad_cnt = 0
    for lane, candidate, recorded_score, source_nm in recorded_list:
        score = competition_score(film_df[(film_df['lane'] == lane) & (film_df['candidate'] == candidate)])['score']
        # записанные числа округлены до 4-5 знаков, некоторые получены сложением двух округленных
        if abs(score - recorded_score) > 1.01e-4:
            bad_cnt += 1
        print(f"{lane:<14} {candidate:<9} {recorded_score:>9.5f} {score:>9.5f} {score - recorded_score:>+12.1e}  {source_nm}")
    print(f"Строк с расхождением больше 1e-4: {bad_cnt}")

    return bad_cnt


def check_kernel_rescore(film_df):
    """
    Для двух прогонов audit44 строки по фильмам на диске все-таки есть (farm/results/kaggle), сверяем с ними пересчет
    """
    print(f"\nСверка пересчета прогонов Kaggle с сохраненными строками")
    bad_cnt = 0
    for candidate, file_nm in [('V12', 'farm/results/kaggle/KV12.jsonl'), ('FA', 'farm/results/kaggle/KFA.jsonl')]:
        stored_row_dict = {}
        for raw_row in read_jsonl(source_path(file_nm)):
            stored_row_dict[raw_row['film']] = normalize_row(raw_row)

        rescored_df = film_df[(film_df['lane'] == 'audit44') & (film_df['candidate'] == candidate)]
        diff_cnt = 0
        for row in rescored_df.itertuples():
            stored_row = stored_row_dict[row.film]
            for col in count_col_list + ['n_pred', 'n_est']:
                if getattr(row, col) != stored_row[col]:
                    diff_cnt += 1
            if abs(row.adj - stored_row['adj']) > 1e-12:
                diff_cnt += 1

        if diff_cnt > 0 or len(rescored_df) != len(stored_row_dict):
            bad_cnt += 1
        print(f"audit44 {candidate}: фильмов {len(rescored_df)}, отличающихся значений {diff_cnt} ({file_nm})")

    return bad_cnt


if __name__ == "__main__":
    submission_df = make_submissions()
    film_df, candidate_df = make_validation(submission_df)

    bad_cnt = check_leak_table(film_df, 'honest_oof/leak_table_oofm.txt', 'honest_oofm')
    # leak_table.txt - та же таблица для дорожки oof
    bad_cnt += check_leak_table(film_df, 'honest_oof/leak_table.txt', 'honest_oof')
    bad_cnt += check_recorded_scores(film_df)
    bad_cnt += check_kernel_rescore(film_df)

    if bad_cnt > 0:
        raise ValueError(f"Сверка не прошла: расхождений {bad_cnt}")
