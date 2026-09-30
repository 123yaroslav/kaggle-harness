def extract_summary(answer_text, max_len=2500):
    """
    Выжимка для диспетчера: все, что идет после последней строки "ИТОГ:"

    :param answer_text: ответ субагента
    :param max_len: до скольких символов обрезается выжимка. 2500 взято на глаз: 3-7 строк, которые просит промпт,
        укладываются с запасом, а ответ целиком в промпт диспетчера все равно не попадает
    """
    marker = 'ИТОГ:'
    idx = answer_text.rfind(marker)

    if idx == -1:
        # исполнитель не выдержал формат, но диспетчеру все равно нужно что-то показать - берем хвост ответа
        summary_text = answer_text.strip()
        if len(summary_text) > max_len:
            return f"(строки ИТОГ: в ответе нет, показан хвост ответа: {max_len} из {len(summary_text)} символов)\n{summary_text[-max_len:]}"
        else:
            return summary_text

    summary_text = answer_text[idx + len(marker):].strip()
    if len(summary_text) > max_len:
        return f"{summary_text[:max_len]}\n... (выжимка обрезана: показаны первые {max_len} из {len(summary_text)} символов)"
    else:
        return summary_text
