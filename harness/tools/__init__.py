from ..tool import Tool, ToolStorage

from .args import NoArgs, ReadFileArgs, WriteFileArgs, RunPythonArgs, ListRunsArgs, CompareRunsArgs, LbNoiseArgs, SetVerdictArgs
from .args import SetFinalPicksArgs, SetLineReviewArgs, RegisterRunArgs, KagglePagesArgs, KaggleKernelsArgs, KaggleKernelSourceArgs, KaggleCsvProfileArgs
from .file_tools import list_files, read_file, write_file
from .python_tool import run_python, run_timeout_sec, max_stdout_len, max_stderr_len
from .registry_tools import list_runs, compare_runs, lb_noise, set_verdict, set_final_picks, set_line_review, register_run
from .kaggle_tools import kaggle_pages, kaggle_files, kaggle_leaderboard, kaggle_kernels, kaggle_csv_profile, kaggle_kernel_source, kaggle_part_len


def make_tool_storage(external_mode='live', external_file_nm=None):
    # в описании - только что инструмент делает и какие у него лимиты. Аргументы дописываются сами из модели аргументов
    tool_list = [
        Tool("list_files", "список файлов рабочей папки с размерами в символах", list_files, NoArgs),
        Tool("read_file", "прочитать текстовый файл из рабочей папки. Длинный файл читается частями: в конце результата "
                          "будет подсказка, с какого offset продолжать", read_file, ReadFileArgs),
        Tool("write_file", "записать текстовый файл в notes/ или scratch/, существующий файл перезаписывается", write_file, WriteFileArgs),
        Tool("run_python", "запустить код на Python из корня рабочей папки (pandas, numpy, scipy; metric.py соревнования можно импортировать). "
                           f"Возвращает stdout, при ошибке - еще и stderr. Лимиты: {run_timeout_sec} секунд на запуск, из stdout возвращаются "
                           f"последние {max_stdout_len} символов, из stderr - последние {max_stderr_len}", run_python, RunPythonArgs),
        Tool("list_runs", "реестр прогонов: название, дата, родитель, публичный скор, вердикт аудитора, в каких дорожках "
                          "есть валидация по единицам, описание", list_runs, ListRunsArgs),
        Tool("compare_runs", "парное сравнение двух прогонов по валидации: метрика соревнования на общих единицах, бутстрап по единицам, "
                             "счет по единицам, разница по группам", compare_runs, CompareRunsArgs),
        Tool("lb_noise", "шум публичного лидерборда: SD скора и SD парной разницы на выборке размером с паблик, рядом фактическая "
                         "разница на паблике", lb_noise, LbNoiseArgs),
        Tool("set_verdict", "записать вердикт аудитора по прогонам. Если вердикт финального сабмита меняется на доработать или исключить, "
                            "прогон убирается из финального выбора", set_verdict, SetVerdictArgs),
        Tool("set_final_picks", 'записать финальные сабмиты и пререгистрацию. Примет только прогоны с вердиктом аудитора "принять". '
                                "Повторный вызов заменяет выбор целиком", set_final_picks, SetFinalPicksArgs),
        Tool("set_line_review", "записать разбор решений команды по линиям работы. Повторный вызов заменяет разбор целиком",
             set_line_review, SetLineReviewArgs),
        Tool("register_run", "добавить в реестр новый прогон с результатами валидации по единицам в одной дорожке. "
                             "Если прогон посчитан в нескольких дорожках - по вызову на дорожку с тем же run", register_run, RegisterRunArgs),
        Tool("kaggle_pages", f"страницы соревнования через Kaggle API: список страниц или текст одной страницы, по {kaggle_part_len} символов за вызов",
             kaggle_pages, KagglePagesArgs, external_flg=True),
        Tool("kaggle_files", "сводка по файлам данных соревнования через Kaggle API", kaggle_files, NoArgs, external_flg=True),
        Tool("kaggle_leaderboard", "верх публичного лидерборда через Kaggle API: места и скоры", kaggle_leaderboard, NoArgs, external_flg=True),
        Tool("kaggle_kernels", "публичные ноутбуки соревнования через Kaggle API", kaggle_kernels, KaggleKernelsArgs, external_flg=True),
        Tool("kaggle_kernel_source", f"исходный код публичного ноутбука через Kaggle API, без выходов ячеек, по {kaggle_part_len} символов за вызов",
             kaggle_kernel_source, KaggleKernelSourceArgs, external_flg=True),
        Tool("kaggle_csv_profile", "профиль табличного файла соревнования через Kaggle API: число строк, типы, пропуски, доли значений. "
                                   "Сам файл не сохраняется", kaggle_csv_profile, KaggleCsvProfileArgs, external_flg=True),
    ]

    return ToolStorage(tool_list, external_mode=external_mode, external_file_nm=external_file_nm)
