import functools
import time

import traceback
from logging import Logger


def custom_logging_decorator(logger_object: Logger):
    """
    Логировать вызовов функции (до и после запуска) с указанием времени выполнения.
    Если в процессе работы функции получена ошибка, то записать её в логи.

    :param logger_object: логгер текущего расположения
    """

    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            t_start = time.perf_counter()
            logger_object.warning(f"вызов функции {function.__name__}()")

            try:
                original_result = function(*args, **kwargs)
                all_time = round(time.perf_counter() - t_start, 2)
                logger_object.warning(f"функция {function.__name__}() выполнилась успешно: {all_time} сек.")
                return original_result
            except Exception:
                logger_object.exception(f"ошибка функции {function.__name__}(): {traceback.format_exc()}")
                raise  # перевызвать полученное исключение

        return wrapper

    return decorator
