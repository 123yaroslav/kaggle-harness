def validation_error_text(exc):
    """
    Короткий русский текст из pydantic.ValidationError: какое поле и что с ним не так

    Текст читает модель (ошибка в аргументах инструмента) или человек, который правит competition.json,
    поэтому без типов pydantic и без ссылок на документацию

    :param exc: pydantic.ValidationError
    :return: строка вида "поле: что не так; поле: что не так"
    """
    part_list = []
    for error in exc.errors():
        field_nm = '.'.join(str(loc) for loc in error['loc'])
        # у проверок на уровне всей модели поля нет
        if len(field_nm) > 0:
            part_list.append(f"{field_nm}: {_error_desc(error)}")
        else:
            part_list.append(_error_desc(error))

    return '; '.join(part_list)


def _error_desc(error):
    error_type = error['type']
    ctx = error.get('ctx') or {}
    input_str = repr(error['input'])
    if len(input_str) > 60:
        input_str = input_str[:60] + '...'

    if error_type == 'missing':
        return "обязательный аргумент не передан"
    elif error_type == 'extra_forbidden':
        return "такого аргумента нет"
    elif error_type == 'value_error':
        # сюда попадают ValueError из своих валидаторов, текст у них уже написан для читателя
        return str(ctx['error'])
    elif error_type == 'literal_error':
        return f"допустимые значения: {ctx.get('expected')}, получено {input_str}"
    elif error_type == 'string_type':
        return f"нужна строка, получено {input_str}"
    elif error_type in ('int_type', 'int_parsing', 'int_from_float'):
        return f"нужно целое число, получено {input_str}"
    elif error_type == 'list_type':
        return f"нужен список, получено {input_str}"
    elif error_type in ('model_type', 'model_attributes_type', 'dict_type'):
        return f"нужен объект с полями, получено {input_str}"
    elif error_type == 'too_short':
        return f"элементов должно быть не меньше {ctx['min_length']}, получено {ctx['actual_length']}"
    elif error_type == 'string_too_short':
        return "пустая строка"
    elif error_type == 'greater_than_equal':
        return f"должно быть не меньше {ctx['ge']}, получено {input_str}"
    elif error_type == 'less_than_equal':
        return f"должно быть не больше {ctx['le']}, получено {input_str}"
    else:
        # остальные виды ошибок у нас не встречались, перевода для них нет - отдаем английский текст pydantic как есть
        return error['msg']
