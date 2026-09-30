import json


def parse_json_answer(answer_text):
    """
    Разбирает текст от модели, в котором должен быть один JSON-объект: ответ диспетчера или аргументы инструмента

    :param answer_text: текст от модели
    :return: словарь
    :raises ValueError: если объекта нет или он не разбирается
    """
    # json просим без обертки, но модели все равно часто заворачивают его в кодовый блок
    # или дописывают фразу до и после, поэтому режем от первой скобки до последней
    start_idx = answer_text.find('{')
    end_idx = answer_text.rfind('}')
    if start_idx == -1 or end_idx == -1:
        raise ValueError(f"В тексте нет JSON-объекта: {answer_text[:200]!r}")

    try:
        return json.loads(answer_text[start_idx:end_idx + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON не разобрался ({exc}): {answer_text[:200]!r}")
