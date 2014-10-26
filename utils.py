# coding:utf-8

import sys
import time
import hashlib
import datetime
import json
import random
from jsmin import jsmin
from gevent import Greenlet
import gevent
import math

reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append('..')


class Singleton(object):

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def share(cls):
        if not cls._instance:
            cls()
        return cls._instance


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


class Delay:
    """延迟对象
    """

    def __init__(self, f, *args, **kw):
        self.f = f
        self.args = args
        self.kw = kw

    def call(self):
        return self.f(*self.args, **self.kw)


class DelayCall(Greenlet):
    """以一个微线程的方式实现一个延时调用
    example:
    def p(x):
        print x
    d = DelayCall(5, p, "xx")
    d.start() # 会执行 d._run
    """

    def __init__(self, seconds, f, *args, **kw):
        Greenlet.__init__(self)
        self.seconds = seconds
        self.delay = Delay(f, *args, **kw)
        self.start_seconds = 0
        self.start()

    def cancel(self):
        """取消延时调用
        """
        if self.active:
            self.kill()

    @property
    def active(self):
        return not self.ready() or not self.successful()

    @property
    def left_seconds(self):
        if not self.active:
            return 0
        seconds = time.time() - self.start_seconds
        return max(0, self.seconds - seconds)

    @property
    def int_left_seconds(self):
        return math.floor(self.left_seconds)

    def start(self):
        self.start_seconds = time.time()
        super(DelayCall, self).start()

    def _run(self):
        gevent.sleep(self.seconds)
        return self.delay.call()


class LoopingCall(Greenlet):

    """以一个微线程的方式实现一个定时调用 example:
    def p(x):
        print x
    lc = LoopingCall(5, p, "xx")
    lc.start() # 会执行 d._run
    # some condition
    lc.cancel()
    """

    def __init__(self, seconds, f, *args, **kw):
        Greenlet.__init__(self)
        self.seconds = seconds
        self.delay = Delay(f, *args, **kw)

    def cancel(self):
        """取消定时调用
        """
        self.kill()

    def _run(self):
        while True:
            gevent.sleep(self.seconds)
            self.delay.call()


class Timeout(object):
    """example:
    def p(x):
        print x
    t = Timeout(4, p, "xx")
    # 如果在4s内没有调用t.reset, 则会触发p被调用
    """
    def __init__(self, seconds, cb, *args, **kw):
        """
        """
        self.seconds = seconds
        self.cb = cb
        self.args = args
        self.kw = kw
        self.dc = DelayCall(seconds, cb, *args, **kw)
        self.dc.start()

    def cancel(self):
        self.dc.cancel()

    def reset(self):
        """要在要进行超时设置的函数里调用, 也可以使用其它方式(如继承)
        """
        self.dc.cancel()
        self.dc = DelayCall(self.seconds, self.cb, *self.args, **self.kw)
        self.dc.start()


class TimeoutMixin(object):
    """example:
    class Test(TimeoutMixin):

        def __init__(self):
            self.set_timeout(180)

        def on_timeout(self):
            print "timeout..."
    # 如果在180s内没有调用self.reset,或者self.set_timeout, 则会触发timeout_connection被调用
    """

    def __init__(self):
        self.timeout_timer = None
        self.in_running = False
        self.seconds = 0

    def set_timeout(self, seconds):
        """可以重新设置超时时间"""
        if self.in_running:
            self.cancel()
        self.seconds = seconds
        self.timeout_timer = DelayCall(seconds, self.on_timeout)
        self.timeout_timer.start()
        self.in_running = True

    def on_timeout(self):
        raise NotImplementedError

    def cancel(self):
        self.timeout_timer.cancel()
        self.in_running = False

    def reset(self):
        """重置超时
        """
        assert self.in_running is False
        self.timeout_timer.cancel()
        self.timeout_timer = DelayCall(self.seconds, self.on_timeout)
        self.timeout_timer.start()


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


if __name__ == "__main__":
    def _test(a, b):
        print a, b

    tm = DelayCall(5, _test, 123, 456)
    gevent.sleep(2.3)
    print tm.active, tm.left_seconds
    gevent.sleep(100)