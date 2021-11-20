import json
import os
import sys
import unittest
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE, ENCODING
from common.utils import get_message, send_message

sys.path.append(os.path.join(os.getcwd(), '..'))


class TestSocket:

    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_message = None
        self.received_message = None

    def send(self, message_to_send):
        json_test_message = json.dumps(self.test_dict)
        self.encoded_message = json_test_message.encode(ENCODING)  # кодирует сообщение
        self.received_message = message_to_send  # сохраняем что должно было отправлено в сокет

    def recv(self, max_len):
        json_test_message = json.dumps(self.test_dict)
        return json_test_message.encode(ENCODING)


class Tests(unittest.TestCase):
    test_dict_send = {
        ACTION: PRESENCE,
        TIME: 111111.111111,
        USER: {
            ACCOUNT_NAME: 'test_test'
        }
    }
    test_dict_recv_ok = {RESPONSE: 200}
    test_dict_recv_err = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }

    def test_send_message(self):
        test_socket = TestSocket(self.test_dict_send)  # экземпляр тестового словаря, хранит собственно тестовый словарь
        send_message(test_socket, self.test_dict_send)  # вызов тестируемой функции, результаты будут сохранены в
        # тестовом сокете
        self.assertEqual(test_socket.encoded_message,  # сравниваем результат доверенного
                         test_socket.received_message)  # кодирования и результат от тестируемой функции
        with self.assertRaises(Exception):  # дополнительно, проверим генерацию исключения, при не словаре на входе.
            send_message(test_socket, test_socket)

    def test_get_message(self):
        test_sock_ok = TestSocket(self.test_dict_recv_ok)
        test_sock_err = TestSocket(self.test_dict_recv_err)
        self.assertEqual(get_message(test_sock_ok), self.test_dict_recv_ok)  # тест корректной расшифровки корректного
        # словаря
        self.assertEqual(get_message(test_sock_err), self.test_dict_recv_err)  # тест корректной расшифровки ошибочного
        # словаря


if __name__ == '__main__':
    unittest.main()
