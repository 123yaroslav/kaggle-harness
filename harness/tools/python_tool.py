import os
import site
import subprocess
import sys

run_timeout_sec = 180
# сколько символов stdout и stderr возвращается модели. Числа взяты на глаз, подбирать их не пробовал: важно только,
# что вместе они короче max_result_len у ToolStorage. Берется хвост, потому что ошибка и итог печатаются в конце
max_stdout_len = 5000
max_stderr_len = 2500


def _tail(text, max_len, stream_nm):
    if len(text) <= max_len:
        return text

    tail = text[-max_len:]
    # хвост начинаем с целой строки, иначе первая строка приходит модели с середины.
    # Но только если перенос близко: когда весь хвост - одна длинная строка (print(df.to_json())), от него не оставалось ничего
    newline_idx = tail.find('\n')
    if 0 <= newline_idx < max_len // 2:
        tail = tail[newline_idx + 1:]

    return f"(показан хвост {stream_nm}: {len(tail)} из {len(text)} символов)\n{tail}"


def run_python(workspace, args):
    """
    Запускает код субагента отдельным процессом из корня рабочей папки

    Это не настоящая песочница: процесс идет под тем же пользователем и видит файловую систему.
    Ограничены рабочая папка, время, переменные окружения и домашняя папка (учетных данных в ней нет)
    """
    workspace.script_cnt += 1
    script_nm = os.path.join('scratch', f'script_{workspace.script_cnt}.py')
    with open(workspace.resolve_path(path=script_nm), 'w', encoding='utf-8') as f:
        f.write(args.body)

    # Код модели не должен уметь действовать от имени пользователя. Поэтому из окружения убираются ключи и токены,
    # а HOME подменяется пустой папкой: без этого инженер экспериментов на пробном прогоне сам нашел ~/.kaggle
    # и начал качать данные через kaggle CLI. Доступ к Kaggle есть только у инструментов harness, и только на чтение
    env = {}
    for key, value in os.environ.items():
        if 'KEY' not in key.upper() and 'TOKEN' not in key.upper() and 'SECRET' not in key.upper():
            env[key] = value

    # домашняя папка лежит рядом с рабочей, а не внутри: python на macOS писал туда кэш байткода,
    # и сотни .pyc попадали в список файлов, который видят субагенты. Сейчас байткод отключен совсем
    # (без этого после import metric в рабочей папке появляется еще и __pycache__), но папку оставил снаружи:
    # кэши и конфиги в HOME складывает не только python
    os.makedirs(workspace.home_dir, exist_ok=True)
    env['HOME'] = workspace.home_dir
    # вместе с HOME уезжает и user-site: если зависимости стоят через pip install --user, import pandas в скрипте падал бы
    env['PYTHONUSERBASE'] = site.getuserbase()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    # скрипт лежит в scratch/, и в sys.path попадает scratch/, а не корень рабочей папки: без этой строки import metric не работает
    # PYTHONPATH пользователя сюда не переносится: pandas, numpy и scipy берутся из того же окружения, что и сам harness
    env['PYTHONPATH'] = workspace.work_dir

    try:
        process = subprocess.run([sys.executable, script_nm], cwd=workspace.work_dir, env=env,
                                 capture_output=True, text=True, timeout=run_timeout_sec)
    except subprocess.TimeoutExpired:
        return f"Скрипт не уложился в {run_timeout_sec} секунд и был остановлен"

    result_text = _tail(text=process.stdout, max_len=max_stdout_len, stream_nm='stdout')
    if process.returncode != 0:
        result_text += f"\n[код возврата {process.returncode}]\n{_tail(text=process.stderr, max_len=max_stderr_len, stream_nm='stderr')}"
    if len(result_text.strip()) == 0:
        result_text = "(скрипт отработал и ничего не напечатал)"

    # абсолютные пути этой машины из вывода убираем: в трассировках они есть всегда, и запись прогона
    # на другой машине иначе не совпадет с тем, что там получится при replay
    # Домашняя папка идет первой: ее путь начинается с пути рабочей
    path_list = [(workspace.home_dir, '~'), (workspace.work_dir, '.'), (sys.prefix, '<python>'), (sys.base_prefix, '<python>')]
    for path, short_nm in path_list:
        # на macOS процесс видит рабочую папку через настоящий путь (/private/tmp вместо /tmp), поэтому меняем оба варианта
        for path_variant in [os.path.realpath(path), path]:
            result_text = result_text.replace(path_variant, short_nm)

    return result_text
