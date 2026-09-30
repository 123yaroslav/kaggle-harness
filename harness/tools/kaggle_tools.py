import csv
import glob
import io
import json
import os
import subprocess
import tempfile

import pandas as pd

from ..utilities.text_part import text_part

# сколько символов страницы или исходника ноутбука отдается за один вызов. Взято на глаз:
# вдвое меньше max_result_len у ToolStorage, чтобы подсказка про следующий offset не обрезалась
kaggle_part_len = 6000


def _kaggle(command_list, timeout_sec=120):
    """
    Вызов kaggle CLI

    :return: (текст без служебных строк, токен следующей страницы или None)
    """
    # в текст ошибки идут только первые два слова команды: дальше бывают пути временных папок этой машины
    command_desc = f"kaggle {' '.join(command_list[:2])}"
    try:
        process = subprocess.run(['kaggle'] + command_list, capture_output=True, text=True, timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        raise ValueError(f"{command_desc} не ответил за {timeout_sec} секунд")
    except FileNotFoundError:
        raise ValueError("kaggle CLI не установлен, инструменты kaggle_* на этой машине не работают")
    if process.returncode != 0:
        raise ValueError(f"{command_desc} завершился с ошибкой: {(process.stderr or process.stdout)[-400:]}")

    # CLI печатает токен следующей страницы отдельной строкой перед данными
    page_token = None
    line_list = []
    for line in process.stdout.split('\n'):
        if line.startswith('Next Page Token = '):
            page_token = line[len('Next Page Token = '):].strip()
        else:
            line_list.append(line)

    return '\n'.join(line_list).strip(), page_token


def _slug(workspace):
    return workspace.competition.get_required('kaggle_slug')


def kaggle_pages(workspace, args):
    # "--" перед названием обязателен: без него CLI принимает название соревнования за подкоманду
    command_list = ['competitions', 'pages', 'list', '--format', 'json']
    if args.page is not None:
        command_list += ['--content', '--page-name', args.page]
    raw_text, _ = _kaggle(command_list=command_list + ['--', _slug(workspace=workspace)])

    try:
        page_list = json.loads(raw_text)
    except json.JSONDecodeError:
        raise ValueError(f"kaggle CLI вернул не JSON: {raw_text[:200]}")

    if args.page is None:
        return "Страницы соревнования: " + ', '.join(page['name'] for page in page_list)
    if len(page_list) == 0:
        raise ValueError(f"Страница {args.page} не найдена. Список страниц - kaggle_pages без аргументов")

    return text_part(text=page_list[0].get('content', ''), offset=args.offset, limit=kaggle_part_len)


def kaggle_files(workspace, args, max_page_cnt=15):
    row_list = []
    page_token = None
    for _ in range(max_page_cnt):
        command_list = ['competitions', 'files', _slug(workspace=workspace), '--csv', '--page-size', '200']
        if page_token is not None:
            command_list += ['--page-token', page_token]
        raw_text, page_token = _kaggle(command_list=command_list)
        row_list += list(csv.DictReader(io.StringIO(raw_text)))
        if page_token is None:
            break

    # в соревнованиях с картинками файлов десятки тысяч, поэтому показываем не список, а сводку по верхнему уровню
    dir_dict = {}
    for row in row_list:
        top_nm = row['name'].split('/')[0]
        if top_nm not in dir_dict:
            dir_dict[top_nm] = [0, 0]
        dir_dict[top_nm][0] += 1
        dir_dict[top_nm][1] += int(row['size'] or 0)

    more_str = " (список обрезан, файлов больше)" if page_token is not None else ""
    line_list = [f"Файлов в списке: {len(row_list)}{more_str}. Сводка по верхнему уровню:"]
    for top_nm, (file_cnt, size) in dir_dict.items():
        line_list.append(f"{top_nm}: файлов {file_cnt}, {size / 1e6:.1f} МБ")

    return '\n'.join(line_list)


def kaggle_leaderboard(workspace, args):
    raw_text, _ = _kaggle(command_list=['competitions', 'leaderboard', _slug(workspace=workspace), '--show', '--csv'])
    row_list = list(csv.DictReader(io.StringIO(raw_text)))

    # названия команд не отдаем: для работы нужны только скоры и плотность верха таблицы
    line_list = [f"Верх публичного лидерборда ({len(row_list)} мест):"]
    for place, row in enumerate(row_list, start=1):
        line_list.append(f"{place}: {row['score']} ({row['submissionDate'][:10]})")

    return '\n'.join(line_list)


def kaggle_kernels(workspace, args):
    raw_text, _ = _kaggle(command_list=['kernels', 'list', '--competition', _slug(workspace=workspace), '--sort-by', args.sort_by,
                                        '--csv', '--page-size', str(args.page_size)])
    row_list = list(csv.DictReader(io.StringIO(raw_text)))

    line_list = ["Публичные ноутбуки соревнования (ref | название | голоса | последний запуск):"]
    for row in row_list:
        line_list.append(f"{row['ref']} | {row['title']} | {row['totalVotes']} | {row['lastRunTime'][:10]}")

    return '\n'.join(line_list)


def kaggle_csv_profile(workspace, args, max_size=200e6):
    """
    Профиль одного табличного файла соревнования: файл скачивается во временную папку, профилируется и удаляется.
    Сами данные в рабочую папку и в запись не попадают - только агрегаты
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        _kaggle(command_list=['competitions', 'download', '-c', _slug(workspace=workspace), '-f', args.file, '-p', tmp_dir, '-q'], timeout_sec=600)

        file_list = glob.glob(os.path.join(tmp_dir, '*'))
        if len(file_list) == 0:
            raise ValueError(f"Файл {args.file} не скачался")
        if os.path.getsize(file_list[0]) > max_size:
            raise ValueError(f"Файл {args.file} больше {max_size / 1e6:.0f} МБ, профиль по нему не строится")
        # pandas сам разберет и csv, и csv в zip
        try:
            df = pd.read_csv(file_list[0])
        except ValueError as exc:
            raise ValueError(f"Файл {args.file} не читается как csv: {exc}")

    line_list = [f"{args.file}: строк {len(df)}, колонок {df.shape[1]}",
                 f"{'колонка':<28}{'тип':<10}{'уникальных':<12}{'пропуски':<10}значения"]
    for col in df.columns:
        unique_cnt = df[col].nunique()
        if unique_cnt <= 12:
            value_share = df[col].value_counts(normalize=True, dropna=False).head(12)
            value_str = ', '.join(f"{value}: {share:.3f}" for value, share in value_share.items())
        elif pd.api.types.is_numeric_dtype(df[col]):
            value_str = f"мин {df[col].min():.4g}, медиана {df[col].median():.4g}, макс {df[col].max():.4g}"
        else:
            # текстовые и идентификаторные колонки показываем только длиной: сырые значения в промпты не отдаем.
            # Сюда идет все нечисловое, а не только dtype object: в pandas 3 у строковых колонок тип уже str
            value_str = f"длина строк: медиана {int(df[col].dropna().astype(str).str.len().median())}"

        line_list.append(f"{str(col):<28}{str(df[col].dtype):<10}{unique_cnt:<12}{df[col].isna().mean():<10.3f}{value_str}")

    return '\n'.join(line_list)


def kaggle_kernel_source(workspace, args):
    with tempfile.TemporaryDirectory() as tmp_dir:
        _kaggle(command_list=['kernels', 'pull', args.ref, '-p', tmp_dir], timeout_sec=300)

        file_list = glob.glob(os.path.join(tmp_dir, '*.ipynb')) + glob.glob(os.path.join(tmp_dir, '*.py'))
        if len(file_list) == 0:
            raise ValueError(f"Исходник ноутбука {args.ref} не скачался")

        with open(file_list[0], encoding='utf-8', errors='replace') as f:
            raw_text = f.read()

    if file_list[0].endswith('.ipynb'):
        # выходы ячеек выбрасываем: в них картинки в base64 и логи на мегабайты
        cell_text_list = []
        for cell in json.loads(raw_text).get('cells', []):
            cell_text = ''.join(cell.get('source', []))
            if len(cell_text.strip()) > 0:
                cell_text_list.append(f"# [{cell.get('cell_type')}]\n{cell_text}")
        source_text = '\n\n'.join(cell_text_list)
    else:
        source_text = raw_text

    return text_part(text=source_text, offset=args.offset, limit=kaggle_part_len)
