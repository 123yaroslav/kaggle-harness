class LiteLLMClient(object):
    """
    Клиент к модели через LiteLLM. Провайдер выбирается префиксом в названии модели,
    ключ берется из переменной окружения этого провайдера (ANTHROPIC_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY, ...)
    """
    def __init__(self, model_nm, max_tokens=16000, max_try_cnt=2):
        try:
            import litellm
        except ImportError:
            raise ImportError("Для режима live нужен litellm: pip install litellm. Режим replay работает без него и без ключа")

        self.litellm = litellm
        self.model_nm = model_nm
        self.max_tokens = max_tokens
        self.max_try_cnt = max_try_cnt
        self.call_cnt = 0

    def complete(self, system_prompt, user_prompt):
        for try_num in range(1, self.max_try_cnt + 1):
            # temperature не передаем: часть новых моделей отвечает на нее ошибкой 400
            response = self.litellm.completion(
                model=self.model_nm,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens
            )
            answer_text = response.choices[0].message.content
            if answer_text is not None and len(answer_text.strip()) > 0:
                break
        self.call_cnt += 1

        if answer_text is None or len(answer_text.strip()) == 0:
            raise RuntimeError(f"Модель {self.model_nm} вернула пустой ответ {self.max_try_cnt} раза подряд, "
                               f"finish_reason: {response.choices[0].finish_reason}")

        # обрезанный по max_tokens ответ все равно отдаем: оборванный блок <tool> субагент вернет модели как ошибку формата
        return answer_text
