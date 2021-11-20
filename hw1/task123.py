# 1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
# Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
# В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
# («Узел доступен», «Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().

# 2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона. Меняться должен только последний
# октет каждого адреса. По результатам проверки должно выводиться соответствующее сообщение.

# 3. Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2. Но в данном случае
# результат должен быть итоговым по всем ip-адресам, представленным в табличном формате (использовать модуль tabulate).
# Таблица должна состоять из двух колонок и выглядеть примерно так:
# Reachable     Unreachable
# 10.0.0.1      10.0.0.3
# 10.0.0.2      10.0.0.4


import ipaddress
import subprocess
import chardet
from tabulate import tabulate

proof_message = 'Заданный узел недоступен'  # сообщение ping по которому будем принимать решение о доступности IP
addr_list = ['192.168.1.1', '192.168.1.2', '192.168.1.50']  # тестовый список


def host_ping(adr_list):  # Функция №1
    ping_result = []  # список результатов тестирования
    for adr in adr_list:
        flag = True
        ipv4 = ipaddress.ip_address(adr)
        proc_ans = subprocess.Popen(['ping', '-n', '1', str(ipv4)],  # вызываем пинг один раз (не 4 как по умолчанию)
                                    stdout=subprocess.PIPE,  # берём из процесса выводимый текст
                                    creationflags=subprocess.CREATE_NO_WINDOW)  # вызываем пинг без открытия окна
        for list_str in proc_ans.stdout:  # проходимся по строкам ответа субпроцесса
            decode_str = list_str.decode(chardet.detect(list_str)['encoding'])  # приводим к читабельному виду
            if proof_message in decode_str:  # ищем заданную строку в ответе субпроцесса
                flag = False  # если адрес недоступен - сбрасываем флаг
                break  # покидаем цикл и идём проверять следующий адрес
        print(adr, "- Узел доступен") if flag else print(adr, "- Узел не доступен")  # выводим соответствующее сообщение
        ping_result.append([adr, flag])
    return ping_result


def host_range_ping(net_range):  # Функция №2
    try:
        subnet = ipaddress.ip_network(net_range)  # пробуем преобразовать входную строку в список IP
        return host_ping(list(subnet))
    except ValueError:
        print('Введённое значение не принадлежит сети!')
        return []  # предотвращаем ошибку в случае не распознанного адреса


def host_range_ping_tab():  # Функция №3
    list_a = host_range_ping(net)  # входной список

    d = {'Reachable': [], 'Unreachable': []}  # объявляем словарь списков
    for ip in list_a:  # разделяем входной список на 2 списка в зависимости от значения flag
        if ip[1]:  # проверяем как установлен flag
            d['Reachable'].append(ip[0])
        else:
            d['Unreachable'].append(ip[0])
    print(tabulate(d, headers='keys'))


host_ping(addr_list)  # Задание №1
print('*' * 50)

net = input(  # Задание №2
    'Введите адрес сети (например 192.168.1.0/28) для сканирования диапазона ip-адресов принадлежащих этой сети: ')
# host_range_ping(net)  # чтобы не повторяться - здесь не используем, используется в следующей функции

host_range_ping_tab()  # Задание №3
