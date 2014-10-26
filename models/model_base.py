# coding:utf-8

import sys
import MySQLdb
import time
import redis
sys.path.append('..')

from config import *
from torndb import Row


def escape(data):
    return MySQLdb.escape_string(data)


def dict_to_row(dict_obj):
    return Row(dict_obj)


def try_convert_to_number(data):
    """将字符串往数字方向转，如果是INT则转INT，是FLOAT则转FLOAT，否转原样返回"""
    if data.isdigit():
        return int(data)
    try:
        ret = float(data)
        return ret
    except ValueError:
        pass
    return data


def try_convert_dict_item_to_number(data):
    if not isinstance(data, dict):
        return
    for k, v in data.items():
        data[k] = try_convert_to_number(v)


#========================= REDIS的连接与ping ===============================
__redis_pool = False


# 连接redis
def redis_connect():
    global __redis_pool
    if __redis_pool is False:
        __redis_pool = redis.ConnectionPool(**CONFIG.redis_game)
    try:
        return redis.Redis(connection_pool=__redis_pool)
    except Exception as data:
        print data


# 中心redis连接对象
_redis_center = False


# 保持Redis在线的方法，需要定时调用一下
# 如果Redis无法ping通，则尝试重新连接
def keep_redis_connect():
    global _redis_center
    if _redis_center is False:
        _redis_center = redis_connect()

    if not _redis_center:
        return

    try:
        _redis_center.ping()
    except Exception as data:
        print data
        redis_connect()


def share_redis():
    global _redis_center
    return _redis_center
#=========================== REDIS结束 ==============================


if __name__ == '__main__':
    time.sleep(1)
    keep_redis_connect()
