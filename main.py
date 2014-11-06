# coding:utf-8
import sys
import os
import daemonized
from gateway import Gateway
from models import model_base
from config import *
from controllers.services import *
import utils


log_file = os.path.join(CONFIG.log_path, CONFIG.log_file_name)


# 启动服务
def main():
    utils.log('started with pid %d' % (os.getpid()), log_file)
    model_base.keep_redis_connect()

    gw = Gateway.share()
    gw.set_ports(CONFIG.ports)  # 设置端口
    gw.set_game_id(CONFIG.game_id)  # 服务类型
    gw.insert_service(ServiceGame.share())  # 插入游戏服务
    gw.insert_service(ServiceLogin.share())  # 插入登陆相关的服务
    gw.insert_service(ServiceSystem.share())  # 插入系统相关的服务
    gw.insert_service(ServiceControl.share())  # 插入控制服务
    gw.start_service()  # 启动服务


pid_file = os.path.join(CONFIG.log_path, CONFIG.pid_file_name)


@daemonized.Daemonize(pidfile=pid_file, stdin=None, stdout=log_file, stderr=log_file)
def daemon_server():
    main()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        daemon_server()
    else:
        main()