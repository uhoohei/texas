# coding:utf-8

import sys
sys.path.append('..')
import utils
import key
from model_base import share_redis


def get_by_key(session_key):
    if not session_key:
        return 0
    return utils.str_to_int(share_redis().hget(key.ONLINE, session_key))