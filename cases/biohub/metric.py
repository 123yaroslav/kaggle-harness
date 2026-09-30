import numpy as np

# Метрика соревнования по строкам validation/film_results.csv одного кандидата.
# Формула взята из порта официальной метрики (metric/metric.py, summarise) и из honest_oof/agg2.py, в обоих местах она одна:
#   по фильму:  J = TP / (TP + FP + FN) по ребрам,  adj = max(0, J * (1 - 0.1 * (n_pred - n_est) / n_est))
#   adj_edge  = sum(w * adj) / sum(w),  w = TP + FP + FN по ребрам фильма
#   div_jaccard = sum(TP) / sum(TP + FP + FN) по делениям, суммы по всем фильмам сразу
#   score     = adj_edge + 0.1 * div_jaccard
# Если ни в одном фильме нет ни одного события по делениям, второе слагаемое не добавляется

node_penalty_alpha = 0.1
division_weight = 0.1


def film_adj(edge_tp, edge_fp, edge_fn, n_pred, n_est):
    """
    Adjusted edge Jaccard одного фильма. В film_results.csv он уже лежит в колонке adj,
    функция нужна, чтобы пересчитать его при другом числе узлов или проверить колонку

    :param n_pred: число узлов в предсказании
    :param n_est: оценка числа клеток в фильме из разметки (estimated_number_of_nodes)
    """
    edge_cnt = edge_tp + edge_fp + edge_fn
    if edge_cnt == 0:
        return float('nan')

    edge_jaccard = edge_tp / edge_cnt
    node_multiplier = 1 - node_penalty_alpha * (n_pred - n_est) / n_est

    return max(0.0, edge_jaccard * node_multiplier)


def _adj_edge(weight, adj):
    # фильм без единого ребра в знаменателе не участвует в среднем, у официального кода так же
    # Туда же фильмы с adj = nan. Если считать не по чему, метрика не определена
    scored_flg = (weight > 0) & ~np.isnan(adj)
    if scored_flg.sum() == 0:
        return float('nan')

    return (weight[scored_flg] * adj[scored_flg]).sum() / weight[scored_flg].sum()


def competition_score(film_df):
    """
    Итоговая метрика по набору фильмов

    :param film_df: строки film_results.csv одной дорожки и одного кандидата, по строке на фильм
    :return: словарь: score, adj_edge, div_jaccard, счетчики делений и число фильмов
    """
    if film_df['film'].duplicated().any():
        raise ValueError("В film_df есть повторы фильмов. Передай строки одной дорожки и одного кандидата")

    weight = (film_df['edge_tp'] + film_df['edge_fp'] + film_df['edge_fn']).to_numpy(dtype=float)
    adj = film_df['adj'].to_numpy(dtype=float)
    adj_edge = _adj_edge(weight=weight, adj=adj)

    division_tp = int(film_df['division_tp'].sum())
    division_fp = int(film_df['division_fp'].sum())
    division_fn = int(film_df['division_fn'].sum())
    division_cnt = division_tp + division_fp + division_fn

    if division_cnt > 0:
        div_jaccard = division_tp / division_cnt
        score = adj_edge + division_weight * div_jaccard
    else:
        div_jaccard = float('nan')
        score = adj_edge

    res = {
        'score': float(score),
        'adj_edge': float(adj_edge),
        'div_jaccard': div_jaccard,
        'division_tp': division_tp,
        'division_fp': division_fp,
        'division_fn': division_fn,
        'film_cnt': len(film_df)
    }

    return res


def score_delta(candidate_df, base_df, boot_cnt=2000, seed=1):
    """
    Разница метрики кандидата и базы на общих фильмах и парный бутстрап этой разницы по фильмам.
    Сид и число повторов по умолчанию те же, что в honest_oof/leak.py, поэтому интервалы из leak_table воспроизводятся

    :param candidate_df: строки кандидата (одна дорожка)
    :param base_df: строки базы из той же дорожки
    :return: словарь: delta, ci_low, ci_high (95%), p_positive (доля повторов с delta > 0), film_cnt
    """
    film_list = sorted(set(candidate_df['film']) & set(base_df['film']))
    if len(film_list) == 0:
        raise ValueError("У кандидата и базы нет общих фильмов")

    candidate_df = candidate_df.set_index('film').loc[film_list].reset_index()
    base_df = base_df.set_index('film').loc[film_list].reset_index()

    delta = competition_score(candidate_df)['score'] - competition_score(base_df)['score']

    rng = np.random.default_rng(seed)
    boot_delta_list = []
    for _ in range(boot_cnt):
        idx = rng.choice(len(film_list), len(film_list))
        # после выборки с возвращением фильмы повторяются, поэтому считаем на массивах, а не через competition_score
        boot_delta_list.append(score_by_idx(candidate_df, idx) - score_by_idx(base_df, idx))
    boot_delta = np.array(boot_delta_list)

    res = {
        'delta': float(delta),
        'ci_low': float(np.percentile(boot_delta, 2.5)),
        'ci_high': float(np.percentile(boot_delta, 97.5)),
        'p_positive': float(np.mean(boot_delta > 0)),
        'film_cnt': len(film_list)
    }

    return res


def score_by_idx(film_df, idx):
    """
    Та же метрика, что в competition_score, на выборке фильмов с повторами

    :param idx: индексы строк film_df
    """
    weight = (film_df['edge_tp'] + film_df['edge_fp'] + film_df['edge_fn']).to_numpy(dtype=float)[idx]
    adj = film_df['adj'].to_numpy(dtype=float)[idx]
    adj_edge = _adj_edge(weight=weight, adj=adj)

    division_tp = film_df['division_tp'].to_numpy(dtype=float)[idx].sum()
    division_cnt = division_tp + film_df['division_fp'].to_numpy(dtype=float)[idx].sum() + film_df['division_fn'].to_numpy(dtype=float)[idx].sum()

    if division_cnt > 0:
        return adj_edge + division_weight * division_tp / division_cnt
    else:
        return adj_edge


# Пример:
# import pandas as pd
# film_df = pd.read_csv('validation/film_results.csv')
# lane_df = film_df[film_df['lane'] == 'honest_oofm']
# v12_df = lane_df[lane_df['candidate'] == 'V12']
# fa_df = lane_df[lane_df['candidate'] == 'FA']
# competition_score(v12_df)['score']        -> 0.94624
# score_delta(fa_df, v12_df)['delta']       -> +0.00162
