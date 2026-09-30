import argparse
import json
import os
import sys

from harness.agents import Scout, ValidationEngineer, ExperimentEngineer, Auditor, Strategist
from harness.dispatcher import Dispatcher
from harness.llm import LiteLLMClient, ClaudeCliClient, ReplayClient, RecordClient
from harness.private_check import private_check
from harness.schema import Case
from harness.skill import SkillStorage
from harness.tools import make_tool_storage
from harness.trace import Trace
from harness.utilities import now
from harness.workspace import Workspace

root_dir = os.path.dirname(os.path.abspath(__file__))
case_nm_list = ['biohub_final_picks', 'biohub_gate_experiment', 'biohub_line_review', 'rsna_day1']
default_model_nm = 'anthropic/claude-opus-5-5'


def get_replay_file_nm(case_nm, skill_flg):
    replay_nm = case_nm if skill_flg else f'{case_nm}_no_skills'
    return os.path.join(root_dir, 'cases', 'replay', f'{replay_nm}.json')


def make_llm_client(llm_mode, replay_file_nm, record_flg):
    if llm_mode == 'replay':
        return ReplayClient(replay_file_nm)

    if llm_mode == 'live':
        llm_client = LiteLLMClient(model_nm=os.environ.get('HARNESS_MODEL', default_model_nm))
    else:
        llm_client = ClaudeCliClient(model_nm=os.environ.get('HARNESS_CLI_MODEL', 'opus'),
                                     effort=os.environ.get('HARNESS_CLI_EFFORT', 'medium'))

    if record_flg:
        return RecordClient(llm_client, replay_file_nm)
    return llm_client


def run_case(case_nm, llm_mode, skill_flg, record_flg, verbose):
    with open(os.path.join(root_dir, 'cases', f'{case_nm}.json'), encoding='utf-8') as f:
        case = Case(**json.load(f))

    replay_file_nm = get_replay_file_nm(case_nm, skill_flg)
    replay_nm = os.path.splitext(os.path.basename(replay_file_nm))[0]
    llm_client = make_llm_client(llm_mode, replay_file_nm, record_flg)

    # внешние инструменты (Kaggle API) в replay не вызываются: их результаты лежат рядом с записью ответов модели
    if llm_mode == 'replay':
        external_mode = 'replay'
    elif record_flg:
        external_mode = 'record'
    else:
        external_mode = 'live'
    tool_storage = make_tool_storage(external_mode=external_mode,
                                     external_file_nm=os.path.join(root_dir, 'cases', 'replay', f'{replay_nm}.tools.json'))

    workspace = Workspace(case_dir=os.path.join(root_dir, 'cases', case.competition_nm),
                          work_dir=os.path.join(root_dir, 'workdir', replay_nm))
    skill_storage = SkillStorage(os.path.join(root_dir, 'skills'))
    # трейс лежит не в рабочей папке: ее дерево попадает в промпты, субагентам свой трейс видеть незачем
    trace_file_nm = os.path.join(root_dir, 'traces', f'{replay_nm}.jsonl')
    trace = Trace(trace_file_nm)

    agent_list = [
        Scout(llm_client, tool_storage),
        ValidationEngineer(llm_client, tool_storage),
        ExperimentEngineer(llm_client, tool_storage),
        Auditor(llm_client, tool_storage),
        Strategist(llm_client, tool_storage)
    ]
    dispatcher = Dispatcher(llm_client=llm_client, agent_list=agent_list, skill_storage=skill_storage, skill_flg=skill_flg)

    separator = "=" * 100
    print(separator)
    print(f"Кейс {case_nm}. Режим {llm_mode}, модель {llm_client.model_nm}, скиллы: {'подключаются' if skill_flg else 'отключены'}")
    print(f"Запрос: {case.request_text}")
    print(separator)
    print(f"{now()}: [harness] скиллов в каталоге: {len(skill_storage.skill_list)}, субагентов: {len(agent_list)}, "
          f"инструментов: {len(tool_storage.tool_list)}, прогонов в реестре: {len(workspace.get_run_nm_list())}")

    trace.add('request', 'harness', case_nm=case_nm, request_text=case.request_text, llm_mode=llm_mode,
              model_nm=llm_client.model_nm, skill_flg=skill_flg)
    res = dispatcher.run(request_text=case.request_text, workspace=workspace, trace=trace, verbose=verbose)

    print(separator)
    print("Ответ диспетчера:")
    print(res['final_answer'])
    print()
    tool_call_cnt = sum(step.tool_call_cnt for step in res['step_list'])
    print(f"Шагов: {len(res['step_list'])}, вызовов инструментов: {tool_call_cnt}, вызовов модели: {llm_client.call_cnt}")
    if llm_mode == 'replay' and llm_client.mismatch_cnt > 0:
        print(f"[replay] пользовательский промпт отличался от записанного в {llm_client.mismatch_cnt} вызовах из {llm_client.call_cnt}")

    check_text = private_check(workspace, trace)
    if check_text is not None:
        trace.add('private_check', 'harness', check_text=check_text)
        print()
        print(check_text)

    trace.save_md()
    print()
    print(f"Трейс: {os.path.relpath(trace.get_md_file_nm(), root_dir)} (читать), {os.path.relpath(trace_file_nm, root_dir)} (все события с промптами)")
    print()


def main():
    parser = argparse.ArgumentParser(description="Harness для ML-соревнований: диспетчер, субагенты, скиллы")
    parser.add_argument('--case', default='all', choices=case_nm_list + ['all'], help="какой кейс прогнать, по умолчанию все")
    parser.add_argument('--llm', default='replay', choices=['replay', 'live', 'cli'],
                        help="replay - записанные ответы (по умолчанию), live - LiteLLM, cli - claude CLI")
    parser.add_argument('--no-skills', action='store_true', help="не подмешивать скиллы субагентам (для сравнения)")
    parser.add_argument('--record', action='store_true', help="записать ответы модели и внешних инструментов в cases/replay")
    parser.add_argument('--verbose', type=int, default=1, choices=[0, 1, 2],
                        help="0 - только результат, 1 - лог делегирования, 2 - плюс промпты и ответы")
    args = parser.parse_args()

    if args.record and args.llm == 'replay':
        parser.error("--record пишет ответы живой модели, с --llm replay он не имеет смысла. Добавьте --llm live или --llm cli")

    # если вывод перенаправлен в файл или tee, без этого лог появляется только в конце прогона
    sys.stdout.reconfigure(line_buffering=True)

    if args.case == 'all':
        run_case_nm_list = case_nm_list
    else:
        run_case_nm_list = [args.case]

    skill_flg = not args.no_skills
    for case_nm in run_case_nm_list:
        # без скиллов записаны не все кейсы: в replay остальные пропускаем, а не падаем на первом
        replay_file_nm = get_replay_file_nm(case_nm, skill_flg)
        if args.llm == 'replay' and not os.path.isfile(replay_file_nm):
            print(f"Кейс {case_nm} пропущен: нет записи {os.path.relpath(replay_file_nm, root_dir)}. "
                  f"Записать ее можно через --llm cli --record или --llm live --record")
            print()
            continue

        run_case(case_nm=case_nm, llm_mode=args.llm, skill_flg=skill_flg, record_flg=args.record, verbose=args.verbose)


if __name__ == "__main__":
    main()
