def text_part(text, offset, limit):
    """
    Кусок длинного текста для инструментов, которые отдают его частями (read_file, kaggle_pages, kaggle_kernel_source)

    :param text: текст целиком
    :param offset: с какого символа начинать
    :param limit: сколько символов отдать
    :return: кусок текста; если после него что-то осталось - с подсказкой, с какого offset читать дальше
    :raises ValueError: если offset за концом текста
    """
    if offset >= len(text) and len(text) > 0:
        raise ValueError(f"offset {offset} за концом текста: в нем всего {len(text)} символов")

    part = text[offset:offset + limit]
    if offset + limit < len(text):
        part += f"\n... (показаны символы {offset}-{offset + limit} из {len(text)}, дальше - offset={offset + limit})"

    return part
