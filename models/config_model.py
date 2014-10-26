# coding:utf-8

import sys
sys.path.append('..')

import key
from model_base import share_redis
from model_base import try_convert_to_number


# 获得某个配置的值
def get(k):
    ret = share_redis().hget(key.SETTINGS, k)
    return try_convert_to_number(ret)