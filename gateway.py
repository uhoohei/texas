#coding:utf-8

import gevent
from gevent.server import StreamServer
from gevent.pool import Pool
import signal

from utils import utils
from controllers.service_base import ServiceBase
from controllers.player import Player
from config import *


__all__ = ["Gateway"]


class Gateway(utils.Singleton):

    def __init__(self):
        self.__services = {}
        self.__players = {}
        self.__ports = []
        self.__game_id = 0

    def insert_service(self, service):
        if not isinstance(service, ServiceBase):
            raise Exception("Service type Error")

        if self.__services.get(service.service_type) is not None:
            raise Exception("service type %d has exists!" % (service.service_type, ))

        self.__services[service.service_type] = service

    def set_ports(self, ports):
        self.__ports = ports

    def set_game_id(self, game_id):
        self.__game_id = game_id

    # 玩家断线
    def on_connection_end(self, p):
        p.set_online(False)
        if p.zid <= 0 and p.tid <= 0:
            self.del_player(p)

    def on_line_received(self, p, line):
        if not line or len(line) < 2:
            p.send('data empty')
            p.close()
            return

        ret = utils.json_loads(line)
        if not ret or len(ret) < 2:
            utils.log('receive data error: ' + line, 'receive_error.log')
            p.send('decode fail')
            p.close()
            return

        if not self.is_legal_command(ret):
            print 'command is illegal', line
            p.send('cmd illegal')
            p.close()
            return

        result = self.distribute(p, ret)
        if result:
            p.send(result)

    @staticmethod
    def connection_handler(sock, address):
        """连接管理器"""
        Player(sock, address).start()

    @staticmethod
    def check_params(data):
        service = data[0]
        cmd = data[1]
        if not COMMANDS_FORMAT.get(service):
            print "CMD NOT SET IN FIREWALL: ", service, cmd
            return True

        api_format = COMMANDS_FORMAT[service].get(cmd)
        if api_format == "" and not data:  # 参数为空
            return True

        if len(api_format) != len(data):  # 参数长度不正确
            return False

        for i in xrange(0, len(api_format)):
            if not (api_format[i] == "i" and (isinstance(data[i], int) or isinstance(data[i], long))) \
                    and not (api_format[i] == "s" and isinstance(data[i], basestring)) \
                    and not (api_format[i] == "f" and isinstance(data[i], float)) \
                    and not (api_format[i] == "b" and isinstance(data[i], bool)):
                return False

        return True

    def is_legal_command(self, data):
        """检查命令是否合法"""
        if not data:
            print 'not data'
            return False

        if not isinstance(data, list):
            print 'data type error'
            return False

        if len(data) < 2:
            print 'data error: ', data
            return False

        if not isinstance(data[0], int):
            print 'data 0 error', data[0]
            return False

        if not isinstance(data[1], int):
            print 'data 1 error', data[1]
            return False

        if not isinstance(COMMANDS_FORMAT.get(data[0]), dict):
            print 'command format fail'
            return False

        if COMMANDS_FORMAT[data[0]].get(data[1]) is None:
            print 'command detail format fail'
            return False

        # 命令类型的检查以及参数个数检查
        return self.check_params(data)

    def distribute(self, p, ret):
        """分发命令给各个服务"""
        service_type = ret[0]
        if not self.__services.get(service_type):
            print 'service not exist: ', service_type
            return

        return self.__services[service_type].exec_cmd(p, ret)

    def broadcast(self, message):
        """整个游戏的消息广播"""
        pool = Pool(50)
        pool.map_async(
            lambda p: p.send(message),
            self.__players).start()

    # 查找玩家
    def get_player(self, uid):
        return self.__players.get(uid)

    # 保存玩家
    def save_player(self, p):
        self.__players[p.uid] = p

    # 删除玩家
    def del_player(self, p):
        print 'del_player', p.uid
        try:
            del self.__players[p.uid]
        except Exception as data:
            print data
            pass

    # 发送数据至玩家
    def send_to_player(self, uid, data):
        p = self.get_player(uid)
        if not p:
            return
        p.send(data)

    def start_service(self):
        assert (len(self.__ports) > 0)
        gevent.signal(signal.SIGQUIT, gevent.killall)
        pool = Pool(10000)

        # 监听网关的端口
        for i in xrange(0, len(self.__ports) - 1):
            server = StreamServer(("0.0.0.0", self.__ports[i]), self.connection_handler, spawn=pool)
            server.start()
        last_port = self.__ports[len(self.__ports) - 1]
        server = StreamServer(("0.0.0.0", last_port), self.connection_handler, spawn=pool)
        for k, service in self.__services.items():  # 启动所有的服务
            service.start()
        server.serve_forever()