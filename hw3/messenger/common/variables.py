import logging

LOGGING_LEVEL = logging.DEBUG

DEFAULT_PORT = 7777  # Порт по умолчанию для сетевого взаимодействия
DEFAULT_IP_ADDRESS = '127.0.0.1'  # IP адрес по умолчанию для подключения клиента
MAX_CONNECTIONS = 5  # Максимальный размер очереди подключений
MAX_PACKAGE_LENGTH = 1024  # Максимальная длинна сообщения в байтах (буфер)
ENCODING = 'utf-8'  # Кодировка проекта

# Протокол JIM основные ключи:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'from'
DESTINATION = 'to'

# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'
EXIT = 'exit'

# пути, относительно корневой папки + имя файла для логирования
PATH_SERV_LOG = 'logs\server\server.log'
PATH_CLIENTS_LOG = 'logs\clients\client.log'
PATH_DECO_LOG = 'logs\deco\decorator.log'

# Словари - ответы:
RESPONSE_200 = {RESPONSE: 200}

RESPONSE_400 = {RESPONSE: 400, ERROR: None}

DATABASE_PATH = 'sqlite:///db.sqlite3'
