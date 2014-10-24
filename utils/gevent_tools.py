# coding:utf-8

from gevent import Greenlet
import gevent
import time
import math


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


if __name__ == "__main__":
    def _test(a, b):
        print a, b

    tm = DelayCall(5, _test, 123, 456)
    gevent.sleep(2.3)
    print tm.active, tm.left_seconds
    gevent.sleep(100)