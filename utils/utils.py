# coding:utf-8

import sys
import time
import hashlib
import datetime
import json
import random
from jsmin import jsmin

reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append('..')


class ObjectDict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return None

    def __setattr__(self, name, value):
        self[name] = value


class ReadOnlyObjectDict(ObjectDict):
    """it's readonly object dict"""

    def __setattr__(self, name, value):
        raise Exception("read only object, can't set attr.")


# 从字符串转换成INT
def str_to_int(data):
    if not data:
        return 0
    if data.isdigit():
        return int(data)
    try:
        return int(data)
    except Exception as data:
        print data
    return 0


# 写文件
def write(content, file_name):
    try:
        f = open(file_name, 'w')
        f.write(content)
        f.close()
    except Exception as data:
        print data
    return True


# 写日志文件
def log(obj, file_name):
    try:
        f = open(file_name, 'a')
        f.write(time_mdh() + str(obj) + "\n")
        f.close()
    except Exception as data:
        print data
    return True


# 返回 月日 时分秒 的时间字符串
def time_mdh():
    return time.strftime("%m-%d %X ", time.localtime())


# 返回时间戳int型
def timestamp():
    return int(time.time())


# 返回当天0时的时间戳int型
def timestamp_today():
    any_day = datetime.date(2011, 11, 1)
    date_today = any_day.today()
    date_str = time.strptime(str(date_today), "%Y-%m-%d")
    return int(time.mktime(date_str))


# 返回昨天的0点的时间戳
def timestamp_yesterday():
    return timestamp_today() - 24 * 60 * 60


def md5(data):
    return hashlib.md5(data).hexdigest()


def sha1(data):
    return hashlib.sha1(data).hexdigest()


# 读json文件，并返回对应的对象，适用于小配置文件的读取
def read_json_file(filename):
    with open(filename) as js_file:
        json_data = jsmin(js_file.read())
        js_file.close()
    try:
        obj = json.loads(json_data, strict=False)
        return obj
    except Exception as data:
        print "read json file fail:", filename, data
    return {}


# 解析JSON数据,之所以要把此方法写在这里，请看文件开头的 reload 方法，这样才可以处理utf-8字符
def json_loads(data):
    try:
        py_ret = json.loads(data)
        return py_ret
    except Exception as exp:
        log(str(exp) + ': ' + data, 'jsondecode.log')
        return []


# 从JSON中获取成对象,之所以要把此方法写在这里，请看文件开头的 reload 方法，这样才可以处理utf-8字符
def json_dumps(data):
    return str(json.dumps(data, ensure_ascii=False))


# 获得随机数字，并返回字符串
def make_random_num(length=5):
    a = pow(10, length - 1)
    b = pow(10, length) - 1
    return str(random.randint(a, b))
