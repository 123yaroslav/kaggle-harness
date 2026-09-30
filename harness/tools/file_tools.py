import os

from ..utilities.text_part import text_part
from .args import max_read_len

write_dir_nm_list = ['notes', 'scratch']


def list_files(workspace, args):
    return workspace.get_file_tree_str()


def read_file(workspace, args):
    file_nm = workspace.resolve_path(path=args.path)
    if not os.path.isfile(file_nm):
        raise ValueError(f"Файл {args.path} не найден. Список файлов дает list_files")

    with open(file_nm, encoding='utf-8', errors='replace') as f:
        text = f.read()
    if len(text) == 0:
        return "(файл пуст)"

    # limit больше максимума не ошибка, а просто обрезается: подсказка в конце скажет, с какого offset читать дальше
    return text_part(text=text, offset=args.offset, limit=min(args.limit, max_read_len))


def write_file(workspace, args):
    file_nm = workspace.resolve_path(path=args.path)

    # писать можно только в notes и scratch: материалы соревнования и реестр субагенты не переписывают
    # Смотрим на путь после нормализации: notes/../submissions.csv тоже начинается с notes/
    part_list = os.path.relpath(file_nm, workspace.work_dir).split(os.sep)
    if len(part_list) < 2 or part_list[0] not in write_dir_nm_list:
        raise ValueError(f"Писать можно только в файлы внутри notes/ и scratch/, а не в {args.path}")
    if os.path.isdir(file_nm):
        raise ValueError(f"{args.path} - это папка, нужен путь к файлу")

    os.makedirs(os.path.dirname(file_nm), exist_ok=True)
    with open(file_nm, 'w', encoding='utf-8') as f:
        f.write(args.body)

    rel_nm = '/'.join(part_list)
    workspace.add_event(f"записан файл {rel_nm} ({len(args.body)} символов)")

    return f"Файл {rel_nm} записан"
