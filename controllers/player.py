# coding:utf-8
import sys

import utils

sys.path.append('..')

from models import user_model
from line_receiver import PlayerSession

# 玩家状态标志
IN_VIEW = 0  # 旁观
IN_WAITING = 1  # 等待中(新玩家加入后等待中),
IN_PLAYING = 2  # 游戏中,
IN_FOLD = 3  # 已弃牌
IN_DIEOUT = 4  # 已淘汰
'''IN_CHECKOUT = 6 #6已结算(已发钱已扣钱的状态)
IN_QUIT = 7 #已退出房间,用户信息待游戏结束后删除
IN_ACTION = 8 #动作中'''

HEART_BEAT_SECONDS = 51  # 玩家端的心跳超时时间


class Player(PlayerSession):
    """玩家对象"""

    # 玩家与机器人通用的初始化
    def __init__(self, sock, address):
        super(Player, self).__init__(sock, address)
        self.__uid = 0
        self.__uemail = ''
        self.__uname = ''
        self.__unick = ''
        self.__ukey = ''
        self.__uface = 0
        self.__usex = 0
        self.__uguest = 0
        self.__tid = 0
        self.__zid = 0
        self.__straight_win = 0

        self.__cards = []
        self.__is_online = False
        self.__round_seconds = 0
        self.__timeout_times = 0
        self.__seatid = -1
        self.__game_status = 0
        self.__curr_bet = 0
        self.__total_bet = 0
        self.__is_dark = False
        self.__is_quit = False
        self.__need_change_table = False
        self.__uinfo = []
        self.__user = []
        self.__uguest = 0
        self.__uchip = 0
        self.__uexp = 0
        self.__umedal = 0
        self.__ustatus = 0

    # 设置玩家的基本信息
    def set_uinfo(self, uinfo):
        self.__uinfo = uinfo
        self.__uid = uinfo.uid
        self.__uname = uinfo.uname
        self.__unick = uinfo.unick
        self.__uface = uinfo.uface
        self.__usex = uinfo.usex
        self.__uguest = uinfo.uguest

    #设置玩家的游戏信息
    def set_ugame(self, user):
        self.__user = user
        self.__uchip = user.uchip
        self.__uexp = user.uexp
        self.__umedal = user.umedal
        # self.__roundcount = user.roundcount
        # self.__wincount = user.wincount
        # self.__winstreak = user.winstreak

    # 玩家数据初始化
    def init(self, uinfo, user, session):
        self.set_uinfo(uinfo)
        self.__user = user
        self.__uchip = user.uchip
        self.__uexp = user.uexp
        return True

    @property
    def need_change_table(self):
        return self.__need_change_table

    # 设置换桌标志
    def set_need_change_table(self, flag):
        self.__need_change_table = flag

    @property
    def uid(self):
        return self.__uid

    @property
    def uchip(self):
        return self.__uchip

    @property
    def uname(self):
        return self.__uname

    @property
    def unick(self):
        return self.__unick

    @property
    def uface(self):
        return self.__uface

    @property
    def usex(self):
        return self.__usex

    @property
    def uexp(self):
        return self.__uexp

    @property
    def ukey(self):
        return self.__ukey

    @property
    def uguest(self):
        return self.__uguest

    @property
    def ushell(self):
        return 0

    @property
    def umedal(self):
        return 0

    @property
    def round_count(self):
        return 0

    @property
    def win_count(self):
        return 0

    @property
    def win_streak(self):
        return 0

    @property
    def is_robot(self):
        return False

    # 递增经验值
    def incr_exp(self, exp):
        if user_model.incr_exp(self.__uid, exp) > 0:
            self.__uexp += exp

    # 加载玩家的游戏数据
    def load_game_data(self):
        u = user_model.get(self.__uid)
        if u:
            self.__uchip, self.__uexp, self.__ustatus = (u.uchip, u.uexp, u.ustatus)
            return True
        return False

    @property
    def tid(self):  # 获得玩家当前所处的桌子ID
        return self.__tid

    # 设置玩家的桌子ID
    def set_tid(self, tid):
        self.__tid = tid

    @property
    def status(self):  # 获得玩家当前所处的状态
        return self.__game_status

    # 设置玩家的游戏状态
    def set_status(self, status):
        self.__game_status = status

    @property
    def zid(self):  # 获得玩家当前所处的区域ID
        return self.__zid

    # 设置玩家的区域ID
    def set_zid(self, zid):
        self.__zid = zid

    @property
    def seatid(self):  # 获得玩家当前的坐位ID
        return self.__seatid

    # 设置玩家的坐位ID
    def set_seatid(self, seatid):
        self.__seatid = seatid

    # 设置玩家是否在线的标志
    def set_online(self, flag):
        self.__is_online = flag

    # 返回是否在线标志
    @property
    def online(self):
        return self.__is_online

    # 获得玩家的特定的出牌时间
    @property
    def round_seconds(self):
        return self.__round_seconds

    # 设置玩家的单局时间
    def set_round_seconds(self, seconds):
        self.__round_seconds = seconds

    # 获得玩家超时次数
    @property
    def time_out_times(self):
        return self.__timeout_times

    @property
    def play_time(self):  # 机器人需要此方法来判断不要在一个房间里打太长时间
        return 0

    # 重置玩家超时次数
    def reset_time_out_times(self):
        self.__timeout_times = 0
        return 0

    # 递增玩家超时次数
    def incr_time_out_times(self):
        self.__timeout_times += 1
        return self.__timeout_times

    # 获得连胜次数
    def get_straight_win(self):
        return self.__straight_win

    # 接收扑克牌
    def receive_card(self, card):
        self.__cards.append(card)

    # 清除所有手牌
    def clear_cards(self):
        self.__cards = []

    # 获取玩家的扑克牌
    @property
    def cards(self):
        return self.__cards

    # 移除手上的牌
    def remove_cards(self, cards):
        for card in cards:
            if card in self.__cards:
                self.__cards.remove(card)

    # 玩家赢钱
    def win_chip(self, chip):
        flag = self.set_chip_with_database(chip, True)
        if 0 >= flag:
            str_to_log = "winchip error @tid: %d, uid: %d, seatid: %d, addchip: %d"
            str_to_log = str_to_log % (
                self.__tid, self.__uid, self.__seatid, chip)
            utils.log(str_to_log, 'table_win_chip.log')
        return flag

    # 玩家输掉一局，扣数据库的钱
    def lose_chip(self):
        flag = user_model.set_chip(self.__uid, self.__total_bet, 1)
        if 0 >= flag:
            str_to_log = "losechip error @tid: %d, uid: %d, seatid: %d, subchip: %d"
            str_to_log = str_to_log % (
                self.__tid, self.__uid, self.__seatid, self.__total_bet)
            utils.log(str_to_log, 'table_sub_chip.log')
        return flag

    # 设置玩家的数据库里面的钱，同时也修改内存中的钱
    def set_chip_with_database(self, chip, is_add):
        if not self.set_chip(chip, is_add):
            return 0
        add_flag = 0 if is_add else 1
        return user_model.set_chip(self.__uid, chip, add_flag)

    # 设置玩家筹码，只修改内存中的数据，不改数据库
    def set_chip(self, chip, is_add):
        if 0 >= chip or 100000000 <= chip:
            return False
        if chip > self.__uchip and not is_add:
            return False
        if is_add:
            self.__uchip += chip
        else:
            self.__uchip -= chip
        return True

    # 玩家下注
    def bet(self, chip):
        if not self.set_chip(chip, False):
            return False
        self.__curr_bet = chip
        self.__total_bet += chip
        return True

    # 玩家的累积下注总额
    @property
    def total_bet(self):
        return self.__total_bet

    # 玩家的当前下注额
    @property
    def curr_bet(self):
        return self.__curr_bet

    # 设置当前的明暗牌状态
    def set_quit(self, flag):
        self.__is_quit = flag

    # 记录当前是否为暗牌
    @property
    def is_quit(self):
        return self.__is_quit

    # 设置当前的明暗牌状态
    def set_dark(self, flag):
        self.__is_dark = flag

    # 记录当前是否为暗牌
    @property
    def is_dark(self):
        return self.__is_dark

    # 当换桌时被调用
    def on_change_table(self):
        self.set_tid(0)
        self.set_status(IN_WAITING)
        self.clear_cards()
        self.set_quit(False)
        self.set_online(True)

    # 玩家坐下响应
    def on_sit_down(self, tid, seatid):
        self.set_tid(tid)
        if self.status != IN_PLAYING:
            self.clear_cards()
            self.set_status(IN_WAITING)
        self.set_quit(False)
        self.set_online(True)
        self.set_round_seconds(0)
        self.set_seatid(seatid)
        self.set_need_change_table(False)

    # 一局游戏开始前的清理
    def on_round_start(self):
        self.set_quit(False)
        self.set_online(True)
        self.set_dark(True)
        self.clear_cards()
        self.set_status(IN_PLAYING)
        self.__total_bet = 0
        self.__curr_bet = 0

    # 玩家一局结算, 加减金币，计算经验值
    def on_round_over(self, referee, is_win, chip, exp, by_flow):
        from services import ServiceGame
        if self.status == IN_PLAYING:  # 游戏中则结算
            if is_win:
                self.win_chip(chip - self.__total_bet)
                self.__straight_win += 1
            else:
                self.lose_chip()
                self.__straight_win = 0
            self.incr_exp(exp)
            self.__total_bet = 0
            self.set_status(by_flow)

        if self.need_change_table:  # 玩家换桌
            seconds = 8 if is_win else 2
            ServiceGame.share().on_user_change_table(self, referee, seconds)

    # 轮到自己时被调用
    def on_turn_to(self, referee):
        pass