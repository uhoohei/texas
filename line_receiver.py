#coding:utf-8

import gevent
from utils import utils


# 行协议
class BaseLineReceiver(gevent.Greenlet):

    def __init__(self, sock, address):
        self.sock = sock
        self.address = address  # 客户端地址
        self.__read_file = self.sock.makefile('rb')
        self.__write_file = self.sock.makefile('wb')

        gevent.Greenlet.__init__(self)
        #log.debug('{0} new worker'.format(self.address))

    def _run(self):
        recv = gevent.spawn(self.__socket_receive_loop)

        def _clear(glet):
            glet.unlink(_clear)
            gevent.killall([recv])

        recv.link(_clear)
        gevent.joinall([recv])
        self.before_session_end()
        #log.debug('{0} worker died'.format(self.address))

    def __socket_receive_loop(self):
        while True:
            gevent.sleep(0)
            data = self.__sock_recv()

            if not data:
                break
            self.on_line_received(data)

    @property
    def ip(self):
        return self.address[0]

    def on_line_received(self, message):
        raise Exception('on_line_received must be implement.' + message)

    def __sock_recv(self):
        try:
            return self.__read_file.readline()
        except Exception as e:
            print e
            # log.error('LineSocketMixIn, sock_recv error: {0}'.format(str(e)))
            return ''

    def before_session_end(self, *args):
        raise Exception('before_session_end must be implement.' + str(args))

    def send(self, message):
        if not isinstance(message, basestring) or not message:
            return

        if not message.endswith('\r\n'):
            message = '%s\r\n' % message
        try:
            self.__write_file.write(message)
            self.__write_file.flush()
        except Exception as e:
            print e
            # log.error("worker send error: {0}".format(str(e)))
            this = gevent.getcurrent()
            this.kill()

    def close(self):
        self.sock.close()

    def set_socket(self, sock, address):
        self.__init__(sock, address)


class PlayerSession(BaseLineReceiver):

    def __init__(self, sock, address):
        super(PlayerSession, self).__init__(sock, address)

    def on_line_received(self, message):
        print 'line received: ', message
        from gateway import Gateway
        gw = Gateway.share()
        gw.on_line_received(self, message)

    def before_session_end(self, *args):
        from gateway import Gateway
        gw = Gateway.share()
        gw.on_connection_end(self)

    def send(self, message):
        if isinstance(message, basestring):
            return super(PlayerSession, self).send(message)

        if isinstance(message, list) or isinstance(message, dict):
            return super(PlayerSession, self).send(utils.json_dumps(message))

        raise Exception('send data fail, type error')