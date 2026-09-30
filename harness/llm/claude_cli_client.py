import json
import subprocess
import tempfile
import time


class ClaudeCliClient(object):
    """
    Клиент через установленный claude CLI в режиме print. Ключ API не нужен, работает под логином самого CLI.
    Этим клиентом записаны ответы для режима replay
    """
    def __init__(self, model_nm='opus', effort='medium', timeout_sec=900, max_try_cnt=5):
        self.model_nm = model_nm
        self.effort = effort
        self.timeout_sec = timeout_sec
        self.max_try_cnt = max_try_cnt
        self.call_cnt = 0

    def _call_cli(self, command, user_prompt):
        # возвращает (текст ответа, текст ошибки): ровно одно из двух не None
        try:
            # запускаем из пустой временной папки, чтобы CLI не подтянул в контекст файлы проекта
            with tempfile.TemporaryDirectory() as tmp_dir:
                process = subprocess.run(command, input=user_prompt, capture_output=True, text=True,
                                         cwd=tmp_dir, timeout=self.timeout_sec)
        except subprocess.TimeoutExpired:
            return None, f"CLI не ответил за {self.timeout_sec} секунд"

        # при ошибке API (например, 529 Overloaded) CLI выходит с кодом 1, а описание ошибки кладет в stdout тем же JSON
        try:
            response = json.loads(process.stdout)
        except json.JSONDecodeError:
            return None, f"код {process.returncode}, не JSON в ответе: {process.stderr[-300:]} {process.stdout[-300:]}"

        if process.returncode != 0 or response.get('is_error') or 'result' not in response:
            return None, f"код {process.returncode}: {str(response.get('result'))[:300]}"

        # CLI принимает алиас (opus), а полное название модели есть только в ответе. В modelUsage может быть
        # несколько моделей (служебные вызовы самого CLI), основная - та, что выдала больше всего токенов
        model_usage = response.get('modelUsage') or {}
        if len(model_usage) > 0:
            self.model_nm = max(model_usage.keys(), key=lambda model_nm: model_usage[model_nm].get('outputTokens', 0))

        return response['result'], None

    def complete(self, system_prompt, user_prompt):
        # хуки пользователя отключаем: SessionStart-хук подмешивал в контекст модели свой вывод (текущее время,
        # чужие дедлайны), в записи промптов этого текста не было, и replay не воспроизводил настоящий вход модели
        command = ['claude', '-p', '--system-prompt', system_prompt, '--tools', '', '--model', self.model_nm,
                   '--effort', self.effort, '--settings', '{"disableAllHooks": true}', '--no-session-persistence',
                   '--strict-mcp-config', '--disable-slash-commands', '--output-format', 'json']

        # API бывает перегружен минутами, у меня на этом дважды обрывалась длинная запись. Поэтому несколько попыток с паузой
        for try_num in range(1, self.max_try_cnt + 1):
            answer_text, error_text = self._call_cli(command, user_prompt)
            if error_text is None:
                break
            if try_num < self.max_try_cnt:
                time.sleep(60)
        self.call_cnt += 1

        if error_text is not None:
            raise RuntimeError(f"claude CLI не ответил после {self.max_try_cnt} попыток. Последняя ошибка: {error_text}")

        return answer_text
