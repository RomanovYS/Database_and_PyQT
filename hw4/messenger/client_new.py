# 1. Реализовать метакласс ClientVerifier, выполняющий базовую проверку класса «Клиент»
# (для некоторых проверок уместно использовать модуль dis):
# отсутствие вызовов accept и listen для сокетов;
# использование сокетов для работы по TCP;
# отсутствие создания сокетов на уровне классов, то есть отсутствие конструкций такого вида: class Client: s = socket()
import dis
import sys
import json
import socket
import time
import argparse
import logging
import threading
import conf.config_client_log
from common.variables import DEFAULT_PORT, DEFAULT_IP_ADDRESS, ACTION, \
    TIME, USER, ACCOUNT_NAME, SENDER, PRESENCE, RESPONSE, \
    ERROR, MESSAGE, MESSAGE_TEXT, DESTINATION, EXIT, GET_CONTACTS, ALERT, RESPONSE_202, ADD_CONTACTS, DEL_CONTACTS, \
    GET_MY_LIST
from common.utils import get_message, send_message
from errors import IncorrectDataRecivedError, ReqFieldMissingError, ServerError
from common.decolog import log

# Инициализация клиентского логгера
from messenger.db_comm import DataBase

LOGGER = logging.getLogger('client')


class ClientVerifier(type):
    def __init__(self, clsname, bases, clsdict):
        search_param = ['accept', 'listen', 'socket', 'sock_stream']  # параметры для поиска
        for dict_items in clsdict.items():  # по словарю класса
            if type(dict_items[1]).__name__ == 'function':  # если это функция - будем изучать
                disasm = dis.Bytecode(
                    clsdict[dict_items[0]]).dis().lower()  # дизассемблируем и переводим в нижний регистр
                for _ in search_param:  # ищем ключевые слова
                    if _ in disasm:  # если нашли - генерируем исключение
                        raise Exception(f'В функции {dict_items[0]} класса {clsname} присутствуют недопустимые '
                                        f'параметры - {_}')
        type.__init__(self, clsname, bases, clsdict)  # если всё без исключений - переписываем init


class Client(metaclass=ClientVerifier):

    def __init__(self, user_name):
        self.flag = True  # флаг синхронизации вывода сообщений из разных потоков
        self.flag_inp = True  # флаг ожидания ввода текстовых данных для синхронизации
        self.flag_save_mess = False  # флаг и данные для передачи в БД клиента через родительский поток
        self.mess = ''
        self.mess_send = ''
        self.mess_rcv = ''
        self.flag_save_friend = False
        self.friend = ''

    @log
    def create_exit_message(self, account_name):
        """Функция создаёт словарь с сообщением о выходе"""
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: account_name
        }

    @log
    def message_from_server(self, sock, my_username):
        """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
        while True:
            try:
                message = get_message(sock)
                if RESPONSE in message:
                    self.flag = False
                    if message[RESPONSE] == 201:
                        if message[ALERT] == '':
                            cont_list = 'пусто'
                            self.flag_inp = False
                        else:
                            self.flag_inp = True
                            cont_list = message[ALERT]
                        print('В Вашем списке контактов', cont_list)
                        self.flag = True
                    if message[RESPONSE] == 202:
                        # получаем из входной строки список и удаляем ID пользователей
                        user_list = message[ALERT].replace(' ', '').split(',')[1::2]
                        user_list.remove(client_name)  # удаляем из списка своё имя
                        print('На сервере зарегистрированы:', user_list)
                    if message[RESPONSE] == 203:
                        print(message[ALERT])
                    if message[RESPONSE] == 400:
                        print(message[ERROR])

                elif all([  # Если все условия выполняются - тогда действуем  ===================================
                    ACTION in message,
                    message[ACTION] == MESSAGE,
                    SENDER in message,
                    DESTINATION in message,
                    MESSAGE_TEXT in message,
                    message[DESTINATION] == my_username]):  # ===================================================

                    print(f'\nПолучено сообщение от пользователя {message[SENDER]}: {message[MESSAGE_TEXT]}')
                    print('Введите команду: ', end='')
                    LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}: {message[MESSAGE_TEXT]}')
                    self.mess_send = message[SENDER]  # эти костыли, возвращают данные в родительский поток
                    self.mess_rcv = message[DESTINATION]
                    self.mess = message[MESSAGE_TEXT]
                    self.flag_save_mess = True  # признак что, надо бы это сохранить в клиентской БД
                else:
                    LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
            except IncorrectDataRecivedError:
                LOGGER.error(f'Не удалось декодировать полученное сообщение.')
            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, json.JSONDecodeError):
                LOGGER.critical(f'Потеряно соединение с сервером.')
                break
            finally:
                self.flag = True

    @log
    def create_message(self, sock, account_name='Guest'):
        """
        Функция запрашивает кому отправить сообщение и само сообщение,
        и отправляет полученные данные на сервер
        :param sock:
        :param account_name:
        :return:
        """
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        self.flag = True
        try:
            send_message(sock, message_dict)
            LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
        except:
            LOGGER.critical('Потеряно соединение с сервером.')
            sys.exit(1)
        self.mess_send = account_name  # эти костыли, возвращают данные в родительский поток
        self.mess_rcv = to_user
        self.mess = message
        self.flag_save_mess = True  # признак что, надо бы это сохранить в клиентской БД

    @log
    def get_list(self, sock, account_name):
        message_dict = {
            ACTION: GET_CONTACTS,
            SENDER: account_name,
            TIME: time.time(),
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(sock, message_dict)
            LOGGER.info(f'Отправлен запрос списка пользователей ')
        except:
            LOGGER.critical('Потеряно соединение с сервером.')
            sys.exit(1)

    @log
    def add_user(self, sock, account_name):
        to_user = input('Введите имя пользователя для добавления в список контактов: ')
        message_dict = {
            ACTION: ADD_CONTACTS,
            SENDER: account_name,
            TIME: time.time(),
            USER: to_user,
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(sock, message_dict)
            LOGGER.info(f'Отправлен запрос списка пользователей ')
        except:
            LOGGER.critical('Потеряно соединение с сервером.')
            sys.exit(1)
        self.friend = to_user
        self.flag_save_friend = True

    @log
    def del_user(self, sock, account_name):
        message_dict = {
            ACTION: GET_MY_LIST,
            SENDER: account_name,
            TIME: time.time(),
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(sock, message_dict)
            LOGGER.info(f'Отправлен запрос списка пользователей ')
        except:
            LOGGER.critical('Потеряно соединение с сервером.')
            sys.exit(1)
        while not self.flag:  # вводим флаг класса для задержки исполнения программы последовательного вывода строк
            pass  #
        if self.flag_inp:  # Если мой список не пустой, значит есть кого удалять... ждём кого

            to_user = input('Введите имя пользователя для удаления из списка контактов: ')
            self.flag = False
            message_dict = {
                ACTION: DEL_CONTACTS,
                SENDER: account_name,
                TIME: time.time(),
                USER: to_user,
            }
            LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
            try:
                send_message(sock, message_dict)
                LOGGER.info(f'Отправлен запрос списка пользователей ')
            except:
                LOGGER.critical('Потеряно соединение с сервером.')
                sys.exit(1)

    @log
    def user_interactive(self, sock, username):
        """Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения"""
        self.print_help()
        while True:
            while not self.flag:  # вводим классовый флаг задержки исполнения программы для последовательного вывода
                pass  # строк
            command = input('Введите команду: ')
            self.flag = False
            if command == '-m':
                self.create_message(sock, username)
            elif command == '-l':
                self.get_list(sock, username)
            elif command == '-a':
                self.add_user(sock, username)
            elif command == '-d':
                self.del_user(sock, username)
            elif command == '-h':
                self.print_help()
            elif command == '-e':
                send_message(sock, self.create_exit_message(username))
                print('Завершение соединения.')
                LOGGER.info('Завершение работы по команде пользователя.')
                # Задержка необходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробуйте снова. help - вывести поддерживаемые команды.')
                self.flag = True

    @log
    def create_presence(self, account_name):
        """Функция генерирует запрос о присутствии клиента"""
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name
            }
        }
        LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
        return out

    def print_help(self):
        """Функция выводящая справку по использованию"""
        print('Поддерживаемые команды:')
        print('-m - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('-h - вывести подсказки по командам')
        print('-l - запросить список контактов с сервера')
        print('-a - добавить контакт в список контактов')
        print('-d - удалить контакт из списка контактов')
        print('-e - выход из программы')
        self.flag = True

    @log
    def process_response_ans(self, message):
        """
        Функция разбирает ответ сервера на сообщение о присутствии,
        возвращает 200 если все ОК или генерирует исключение при ошибке:param message:
        :return:
        """
        LOGGER.debug(f'Разбор приветственного сообщения от сервера: {message}')
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return '200 : OK'
            elif message[RESPONSE] == 400:
                raise ServerError(f'400 : {message[ERROR]}')
        raise ReqFieldMissingError(RESPONSE)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    # проверим подходящий номер порта
    if not 1023 < server_port < 65536:
        LOGGER.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    # Если имя пользователя не было задано, необходимо запросить пользователя.
    if not client_name:
        client_name = input('Введите имя пользователя: ')

    print(f'Консольный мессенджер. Пользователь: {client_name}')

    LOGGER.info(
        f'Запущен клиент с парамерами: адрес сервера: {server_address}, '
        f'порт: {server_port}, имя пользователя: {client_name}')

    client_ex = Client(client_name)  # создаём экземпляр клиента
    udb = DataBase(client_name)  # объект соединения с БД
    # Инициализация сокета и сообщение серверу о нашем появлении
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_message(transport, client_ex.create_presence(client_name))
        answer = client_ex.process_response_ans(get_message(transport))
        LOGGER.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        LOGGER.error('Не удалось декодировать полученную Json строку.')
        sys.exit(1)
    except ServerError as error:
        LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        sys.exit(1)
    except ReqFieldMissingError as missing_error:
        LOGGER.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        sys.exit(1)
    except (ConnectionRefusedError, ConnectionError):
        LOGGER.critical(
            f'Не удалось подключиться к серверу {server_address}:{server_port}, '
            f'конечный компьютер отверг запрос на подключение.')
        sys.exit(1)
    else:
        # Если соединение с сервером установлено корректно,
        # запускаем клиентский процесс приёма сообщений
        receiver = threading.Thread(target=client_ex.message_from_server, args=(transport, client_name))
        receiver.daemon = True
        receiver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        user_interface = threading.Thread(target=client_ex.user_interactive, args=(transport, client_name))
        user_interface.daemon = True
        user_interface.start()
        LOGGER.debug('Запущены процессы')

    while True:
        time.sleep(0.5)
        if receiver.is_alive() and user_interface.is_alive():
            if client_ex.flag_save_mess:  # сохраняем сообщения в клиентской БД
                client_ex.flag_save_mess = False
                udb.save_mess(client_ex.mess_send, client_ex.mess_rcv, client_ex.mess)
            if client_ex.flag_save_friend:  # сохраняем друзей в клиентской БД
                client_ex.flag_save_friend = False
                udb.save_friend(client_ex.friend)
            continue
        break

    # cli_ex.main()  # запускаем его
