# 2. Реализовать метакласс ServerVerifier, выполняющий базовую проверку класса «Сервер»:
# отсутствие вызовов connect для сокетов;
# использование сокетов для работы по TCP.
# 3. Реализовать дескриптор для класса серверного сокета, а в нем — проверку номера порта. Это должно быть целое число
# (>=0). Значение порта по умолчанию равняется 7777. Дескриптор надо создать в отдельном классе. Его экземпляр добавить
# в пределах класса серверного сокета. Номер порта передается в экземпляр дескриптора при запуске сервера.

import dis
import sys
import time
import socket
import argparse
import logging
import select
import conf.config_server_log
from common.variables import DEFAULT_PORT, MAX_CONNECTIONS, ACTION, TIME, \
    USER, ACCOUNT_NAME, SENDER, PRESENCE, ERROR, MESSAGE, \
    MESSAGE_TEXT, RESPONSE_400, DESTINATION, RESPONSE_200, EXIT
from common.utils import get_message, send_message
from common.decolog import log

# Инициализация логирования сервера.
LOGGER = logging.getLogger('server')


# 3-е задание не успеваю сделать
# class TypedProperty:
#     def __get__(self, addr, port):
#         return getattr(self.addr, self.port)

class ServSoc:
    def __init__(self, l_address, l_port):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.bind((l_address, l_port))
        self.transport.settimeout(0.5)
        self.transport.listen(MAX_CONNECTIONS)  # Слушаем порт
        if not 1023 < listen_port < 65536:  # проверка получения корректного номера порта для работы сервера.
            LOGGER.critical(
                f'Попытка запуска сервера с указанием неподходящего порта {l_port}. '
                f'Допустимы адреса с 1024 до 65535.')
            sys.exit(1)


class ServerVerifier(type):
    def __init__(self, clsname, bases, clsdict):
        search_param = ['connect', 'sock_stream']  # параметры для поиска
        for dict_items in clsdict.items():  # по словарю класса
            if type(dict_items[1]).__name__ == 'function':  # если это функция - будем изучать
                disasm = dis.Bytecode(
                    clsdict[dict_items[0]]).dis().lower()  # дизассемблируем и переводим в нижний регистр
                for _ in search_param:  # ищем ключевые слова
                    if _ in disasm:  # если нашли - генерируем исключение
                        raise Exception(f'В функции {dict_items[0]} класса {clsname} присутствуют недопустимые '
                                        f'параметры - {_}')
        type.__init__(self, clsname, bases, clsdict)  # если всё без исключений - переписываем init


class Server(metaclass=ServerVerifier):

    # для проверки
    # def __init__(self):
    #     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @log
    def process_client_message(self, message, messages_list, client, clients, names):
        """
        Обработчик сообщений от клиентов, принимает словарь - сообщение от клиента,
        проверяет корректность, отправляет словарь-ответ в случае необходимости.
        :param message:
        :param messages_list:
        :param client:
        :param clients:
        :param names:
        :return:
        """
        LOGGER.debug(f'Разбор сообщения от клиента : {message}')

        # Если это сообщение о присутствии, принимаем и отвечаем
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in names.keys():  # Если такой пользователь ещё не зарегистрирован
                names[message[USER][ACCOUNT_NAME]] = client  # регистрируем
                send_message(client, RESPONSE_200)
            else:  # иначе отправляем ответ и завершаем соединение.
                response = RESPONSE_400
                response[ERROR] = 'Имя пользователя уже занято.'
                send_message(client, response)
                clients.remove(client)
                client.close()
            return

        elif ACTION in message and message[ACTION] == MESSAGE and \
                DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:  # Если это сообщение
            messages_list.append(message)  # то добавляем его в очередь сообщений.
            return

        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:  # Если клиент выходит
            clients.remove(names[message[ACCOUNT_NAME]])  # подчищаем его следы
            names[message[ACCOUNT_NAME]].close()
            del names[message[ACCOUNT_NAME]]
            return

        else:  # Иначе отдаём Bad request
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            send_message(client, response)
            return

    @log
    def process_message(self, message, names, listen_socks):  # client
        """
        Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение,
        список зарегистрированных пользователей и слушающие сокеты. Ничего не возвращает.
        :param message:
        :param names:
        :param listen_socks:
        :return:
        """

        if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
            send_message(names[message[DESTINATION]], message)
            LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                        f'от пользователя {message[SENDER]}.')
        elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_socks:
            LOGGER.error(f'Ошибка!!! {message[DESTINATION]} +++ {names[message[DESTINATION]]}')
            raise ConnectionError

        else:
            LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, отправка сообщения невозможна.')
            message[MESSAGE_TEXT] = f'Пользователь {message[DESTINATION]} не подключен.'  # готовим уведомление
            message[DESTINATION] = message[SENDER]  # меняем отправителя на получателя
            message[SENDER] = '*Server*'  # указываем источник сообщения
            message[TIME] = time.time()  # текущее время
            send_message(names[message[DESTINATION]], message)  # отправляем


if __name__ == '__main__':
    server_ex = Server()  # создаём экземпляр сервера

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    soc = ServSoc(listen_address, listen_port)  # Создаём объект сокета
    clients = []  # список клиентов
    messages = []  # очередь сообщений
    names = dict()  # Словарь, содержащий имена пользователей и соответствующие им сокеты.

    LOGGER.info(
        f'Запущен сервер, порт для подключений: {listen_port}, '
        f'адрес с которого принимаются подключения: {listen_address}. '
        f'Если адрес не указан, принимаются соединения с любых адресов.')

    while True:  # Основной цикл программы сервера

        try:  # Ждём подключения, если таймаут вышел, ловим исключение.
            client, client_address = soc.transport.accept()
        except OSError:
            pass
        else:
            LOGGER.info(f'Установлено соединение с ПК {client_address}')
            clients.append(client)

        recv_data_lst = []
        send_data_lst = []
        err_lst = []
        # Проверяем на наличие ждущих клиентов
        try:
            if clients:
                recv_data_lst, send_data_lst, err_lst = select.select(clients, clients, [], 0)
        except OSError:
            pass

        # принимаем сообщения и если ошибка, исключаем клиента.
        if recv_data_lst:
            for client_with_message in recv_data_lst:
                try:
                    server_ex.process_client_message(get_message(client_with_message),
                                                     messages, client_with_message, clients, names)
                except Exception:
                    LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                f'отключился от сервера.')
                    clients.remove(client_with_message)

        # Если есть сообщения, обрабатываем каждое.
        for i in messages:
            try:
                server_ex.process_message(i, names, send_data_lst)
            except Exception:
                LOGGER.info(f'Связь с клиентом с именем {i[DESTINATION]} была потеряна')
                clients.remove(names[i[DESTINATION]])
                del names[i[DESTINATION]]
        messages.clear()
