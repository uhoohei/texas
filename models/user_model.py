# coding:utf-8
import sys
sys.path.append('..')

import key
from model_base import share_redis
from model_base import try_convert_dict_item_to_number
from model_base import try_convert_to_number


# 根据用户ID来获得用户信息
def get(uid):
    ret = share_redis().hgetall(key.user(uid))
    return try_convert_dict_item_to_number(ret)


# 设置某用户的钱数
def set_chip(uid, chip, is_add=True):
    if 0 >= chip or 100000000 <= chip:
        return 0  # 负数不更新钱数
    incr_chip = chip
    if not is_add:
        incr_chip = chip * -1
    return share_redis().hincrby(key.user(uid), "chip", incr_chip)


# 给用户加经验值
def incr_exp(uid, exp):
    if 0 >= exp:
        return 0
    return share_redis().hincrby(key.user(uid), "exp", exp)


# 查询玩家金币数量
def get_chip(uid):
    return share_redis().hget(key.user(uid), "chip")


# 清除玩家上线时间
def clear_login_time(uid):
    return share_redis().hset(key.user(uid), "login_time", 0)


# 带检查的更新玩家的上线时间
def update_login_time(uid):
    t = try_convert_to_number(share_redis().hget(key.user(uid), "login_time"))
    r = share_redis()
    print t, r