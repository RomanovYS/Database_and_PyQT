import os
import inspect

from datetime import datetime
from common.variables import PATH_DECO_LOG


def log(func):
    name_module = inspect.stack()[1][1].split('\\')[-1]  # выясняем какой модуль эту функцию вызвал
    out_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', PATH_DECO_LOG))  # файл для отчёта

    def c_f(*args, **kwargs):
        with open(out_file, 'a+', encoding='utf-8') as file:  # открываем для добавления
            file.write(f'Время: {datetime.now()}\n')
            file.write(f'В модуле: {name_module}, произошел вызов функции: {func.__name__}, из {func.__module__}\n')
            file.write(f'с параметрами: {args}, {kwargs}\n')
            result = func(*args, **kwargs)
            file.write(f'Функция вернула: {result}\n')
            file.write('************\n')
        return result

    return c_f
