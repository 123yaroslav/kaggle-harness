import hashlib
import json
import os

from ..utilities.now import now


def prompt_hash(prompt_text):
    # в записи лежат не сами промпты, а их хэши: с полными текстами четыре записи весили 19 МБ.
    # Посмотреть, что уходит модели, можно через --verbose 2 - в replay промпты собираются заново
    return hashlib.sha256(prompt_text.encode('utf-8')).hexdigest()[:16]


class ReplayClient(object):
    """
    Отдает записанные ответы модели по порядку вызовов. Нужен, чтобы кейсы прогонялись без ключа и без сети
    """
    def __init__(self, replay_file_nm):
        with open(replay_file_nm, encoding='utf-8') as f:
            replay = json.load(f)

        self.replay_file_nm = replay_file_nm
        self.model_nm = replay['model_nm']
        self.call_list = replay['call_list']
        self.call_cnt = 0
        self.mismatch_cnt = 0

    def complete(self, system_prompt, user_prompt):
        if self.call_cnt >= len(self.call_list):
            raise RuntimeError(
                f"Запись {self.replay_file_nm} закончилась на вызове {self.call_cnt + 1}: либо она оборвана, "
                f"либо прогон пошел не так, как при записи (код субагента отработал иначе). Запустите с --llm live или --llm cli"
            )

        call = self.call_list[self.call_cnt]
        self.call_cnt += 1

        # системный промпт обязан совпасть: если нет, значит вызван другой исполнитель или другой скилл, чем при записи.
        # Пользовательский сверяем мягко - в нем скоры из песочницы, на другой машине они могут отличаться в последних знаках
        if call['system_prompt_hash'] != prompt_hash(system_prompt):
            print(f"{now()}: [replay] ВНИМАНИЕ: системный промпт вызова {self.call_cnt} отличается от записанного, ответ взят из записи по порядку")
        if call['user_prompt_hash'] != prompt_hash(user_prompt):
            self.mismatch_cnt += 1

        return call['answer_text']


class RecordClient(object):
    """
    Обертка над живым клиентом: каждый вызов дописывает в файл записи.
    Если файл записи уже есть, прогон продолжается с того места, где запись оборвалась
    """
    def __init__(self, llm_client, replay_file_nm):
        self.llm_client = llm_client
        self.replay_file_nm = replay_file_nm
        self.model_nm = llm_client.model_nm
        self.call_list = []
        self.call_cnt = 0

        self.old_call_list = []
        if os.path.isfile(replay_file_nm):
            with open(replay_file_nm, encoding='utf-8') as f:
                old_replay = json.load(f)
            self.old_call_list = old_replay['call_list']
            self.model_nm = old_replay['model_nm']

    def complete(self, system_prompt, user_prompt):
        # пока промпты дословно совпадают со старой записью, модель не зовем: это тот же прогон, просто оборванный.
        # Первое же расхождение значит, что изменились промпты или код, и дальше старая запись не годится
        old_call = None
        if len(self.call_list) < len(self.old_call_list):
            old_call = self.old_call_list[len(self.call_list)]

        if old_call is not None and old_call['system_prompt_hash'] == prompt_hash(system_prompt) \
                and old_call['user_prompt_hash'] == prompt_hash(user_prompt):
            answer_text = old_call['answer_text']
        else:
            self.old_call_list = []
            answer_text = self.llm_client.complete(system_prompt=system_prompt, user_prompt=user_prompt)
            self.model_nm = self.llm_client.model_nm
        self.call_cnt += 1

        self.call_list.append({
            'system_prompt_hash': prompt_hash(system_prompt),
            'user_prompt_hash': prompt_hash(user_prompt),
            'answer_text': answer_text
        })
        # сохраняем после каждого вызова: прогон длинный, и если он упадет на середине, записанное не пропадет.
        # Через временный файл, иначе обрыв посреди записи оставит битый json, и возобновление на нем упадет
        tmp_file_nm = self.replay_file_nm + '.tmp'
        with open(tmp_file_nm, 'w', encoding='utf-8') as f:
            json.dump({'model_nm': self.model_nm, 'call_list': self.call_list}, f, ensure_ascii=False, indent=1)
        os.replace(tmp_file_nm, self.replay_file_nm)

        return answer_text
