# coding:utf-8
import sys
import os

import daemonized

from gateway import Gateway
from models import model_base
from config import *
from controllers.service_game import ServiceGame
from controllers.service_login import ServiceLogin
from controllers.service_system import ServiceSystem
from controllers.service_control import ServiceControl
import utils


log_file = os.path.join(CONFIG.log_path, CONFIG.log_file_name)


# 启动服务
def main():
    utils.log('started with pid %d' % (os.getpid()), log_file)
    model_base.keep_redis_connect()

    # manager.init()
    gw = Gateway.share()
    gw.set_ports(CONFIG.ports)  # 设置端口
    gw.set_game_id(CONFIG.game_id)  # 服务类型
    gw.insert_service(ServiceGame.share())  # 插入游戏服务
    gw.insert_service(ServiceLogin.share())  # 插入登陆相关的服务
    gw.insert_service(ServiceSystem.share())  # 插入系统相关的服务
    gw.insert_service(ServiceControl.share())  # 插入控制命令

    # __gw.setGameCmdHandler(manager.exec_game_cmd)  # 设置游戏执行函数
    # __gw.setKeepDBFunc(database.keep_connect)  # 保持数据库在线函数
    # __gw.setKeepRedisFunc(database.keep_redis_connect)  # 保持中心redis在线的函数
    # __gw.setKeepGameRedisFunc(database.keep_game_redis_connect)  # 保持游戏redis在线的函数
    # gw.setLogPath(LOG_PATH)  # 写日志路径
    # gw.setPlayerConnectionLostFunc(manager.on_player_connection_lost)  # 玩家掉线回调
    # gw.setGameLogFile(log_file_name)  # 设置游戏日志文件

    gw.start_service()  # 启动reactor循环,服务开启


pid_file = os.path.join(CONFIG.log_path, CONFIG.pid_file_name)


@daemonized.Daemonize(pidfile=pid_file, stdin=None, stdout=log_file, stderr=log_file)
def daemon_server():
    main()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        daemon_server()
    else:
        main()