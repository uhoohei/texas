# coding:utf-8
import sys
sys.path.append('..')
import utils
import socket
from config import *
from models import online_model
from gevent import monkey
monkey.patch_socket()
import unittest


class SocketTest(unittest.TestCase):

    __connected = False
    __socket = socket.socket()

    def send(self, data):
        if not self.__connected:
            self.__connected = True
            ports = CONFIG.ports
            self.__socket.connect(('localhost', ports[0]))
        self.__socket.send(utils.json_dumps(data) + "\r\n")

    def test_login(self):
        uid = 1
        online_model.delete(uid)
        session_key = online_model.add(uid)

        data = [SERVICE_LOGIN, CMD_LOGIN, "1", VERSION_SUB, CONFIG.game_id, 0, session_key]
        self.send(data)
        stream = self.__socket.recv(1024)
        result = utils.json_loads(stream)
        self.assertTrue(not result)

        data = [SERVICE_LOGIN, CMD_LOGIN, VERSION_MAIN, VERSION_SUB, CONFIG.game_id, 0, session_key]
        self.send(data)
        stream = self.__socket.recv(1024)
        result = utils.json_loads(stream)
        self.assertTrue(len(result) > 0)
        self.assertTrue(result[2] == OK)


if __name__ == '__main__':
    unittest.main()