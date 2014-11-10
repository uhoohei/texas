# coding:utf-8
import sys
import random
sys.path.append('..')

from config import *
import utils
from utils import DelayCall

import player
from poker import Poker

MAX_RAISE_RATE = 10  # 单手最高加注倍数上限
RAISE_RATE_LIST = [1, 2, 5, MAX_RAISE_RATE]  # 允许加注的倍数表


TOTAL_SEAT = 9  # 桌子坐位数
MAX_PLAYERS = 30  # 最多允许的人数


# 桌子的状态 0空闲中 1正准备开始 2游戏中 3正在结算
# 注意顺序不可修改，否则影响游戏进程
TABLE_READY = 0
TABLE_START = 1
TABLE_PLAYING = 2
TABLE_CHECK_OUT = 3

CALL_SECONDS = 25  # 等待玩家响应的秒数
FIRST_CALL_SECONDS = 25
CHECKOUT_SECONDS = 10

WIN_EXP = 2  # 胜者所加经验值
ROUND_START_SECONDS = 6  # 开局后直到第一个玩家响应的等待时间秒数


class Referee(object):
    """游戏裁判"""

    def __init__(self, ret):
        from services import ServiceGame
        self.manager = ServiceGame.share()
        self.__flow = ""  # 桌子日志
        self.__tid = ret.tid
        self.__zid = ret.zid
        self.__round_id = ret.roundid
        self.__curr_seat_id = -1
        self.__seats = [None] * TOTAL_SEAT
        self.__round_results = {}
        self.__is_dark = False  # 最后一手下注的明暗状态
        self.__last_bet = 0  # 最后一手下注的数量
        self.__total_bet = 0  # 累积下注
        self.__raise_rate = 0  # 当前的加注倍数
        self.__round_count = 0  # 轮数
        self.__wait_seconds = 0  # 临时等待玩家的时间秒数，用于比牌时播放动画
        self.__game_wait_seconds = 0  # 等待开桌的计时
        self.__button = -1  # 庄家ID
        self.__random_button = True  # 随机庄家
        self.__duel_dict = {0: set(), 1: set(), 2: set(), 3: set(), 4: set()}
        self.__winner = None  # 最后的比牌赢家

        self.__timer = None  # 游戏的定时器
        self.__poker = Poker()  # 初始化扑克信息

        self.__consume = self.manager.zone_consume_chip(self.__zid)  # 消耗金币数
        self.__base_chip = self.manager.zone_base_chip(self.__zid)  # 基数
        self.__limit_chip = self.manager.zone_limit_chip(self.__zid)  # 最低筹码
        self.__total_hands = self.manager.zone_total_hands(self.__zid)  # 最高下注倍数
        self.__status = TABLE_READY

    # 玩家之间的比牌详情
    def duelers_init(self):
        for i in xrange(0, TOTAL_SEAT):
            self.__duel_dict[i].clear()
            self.__duel_dict[i].add(i)

    @property
    def status(self):
        return self.__status

    # 设置桌子状态
    def set_status(self, status):
        self.__status = status
        self.play_log("set status: %d" % (status, ))

    @property
    def zid(self):
        return self.__zid

    @property
    def tid(self):
        return self.__tid

    @property
    def base_chip(self):
        return self.__base_chip

    @property
    def raise_rate(self):  # 当前加注倍率
        return self.__raise_rate

    # 寻找桌子内的空位
    def search_empty_seat(self):
        for seatid in range(0, TOTAL_SEAT):
            if not self.__seats[seatid]:
                return seatid
        return -1

    # 判断玩家是否在桌子内的流程
    def in_table(self, uid):
        if uid <= 0:
            return False
        for seatid in range(0, TOTAL_SEAT):
            if self.__seats[seatid] and self.__seats[seatid].uid == uid:
                return True
        return False

    # 根据玩家uid来获得玩家的坐位ID
    def get_seatid(self, uid):
        for i in range(0, TOTAL_SEAT):
            if self.__seats[i] and self.__seats[i].uid == uid:
                return i
        return -1

    # 扣除玩家税收，返回所扣到的总钱数
    def tax(self, chip):
        if chip <= 0:
            return 0
        tax_chip = 0
        for seatid in range(0, TOTAL_SEAT):
            if not self.__seats[seatid] or self.__seats[seatid].status != player.IN_PLAYING:
                continue
            if 0 < self.__seats[seatid].setChipWithDB(chip, False):
                tax_chip += chip
            self.__seats[seatid].setDark(True)
        return tax_chip

    # 一局开始前下底注
    def base_bet(self, chip):
        if chip <= 0:
            return 0
        base_chip = 0
        for seatid in range(0, TOTAL_SEAT):
            if not self.__seats[seatid] or self.__seats[seatid].status != player.IN_PLAYING:
                continue
            if self.__seats[seatid].bet(chip):
                base_chip += chip
        return base_chip

    # 通知所有的玩家开始游戏
    def notify_game_start(self):
        for i in range(0, TOTAL_SEAT):
            p = self.__seats[i]
            if not p or p.status != player.IN_WAITING:
                continue
            p.onRoundStart()

    # 一位用户进入房间,收集房间信息并返回给客户端
    def sit_down(self, p):
        if self.in_table(p.uid):
            seatid = self.get_seatid(p.uid)
        else:
            seatid = self.search_empty_seat()

        if seatid < 0:
            return ERR_SEAT_FULL
        self.__seats[seatid] = p
        # 玩家响应坐下，保存桌子ID，设置在线，清除手牌，保存坐位ID等操作
        p.on_sit_down(self.__tid, seatid)
        self.manager.update_table_player_num(self.__zid, self.__tid, self.play_num)

        self.on_sit_down_success(p)
        return OK

    # 统计当前在房间的人数
    @property
    def play_num(self):
        count = 0
        for i in range(0, TOTAL_SEAT):
            if self.__seats[i]:
                count += 1
        return count

    # 检查是否已经满足条件可以开始游戏
    def check_start(self):
        if self.status == TABLE_READY and 3 <= self.play_num:  # 可以开局
            self.set_status(TABLE_START)
            DelayCall(1, self.game_start)
        else:
            # print 'CheckStart NOT IN START: ', self.status, self.play_num, self.GameWaitSeconds, self.__seats
            #Manager.debug(self.__zid, self.__tid)
            pass

    # 游戏开局
    def game_start(self):
        self.manager.update_table_player_num(self.__zid, self.__tid, self.play_num)
        self.set_status(TABLE_PLAYING)
        self.clear_duel()
        self.clear_round_result()
        self.__winner = None
        self.__is_dark = True
        self.__last_bet = self.__base_chip
        self.__raise_rate = 0
        self.__curr_seat_id = -1
        self.__round_id += 1
        self.__round_count = 0
        self.__poker.shuffle()  # 洗牌
        self.duelers_init()  # 比牌关系清除
        self.notify_game_start()  # 开局前通知玩家清理
        self.tax(self.__consume)
        self.__total_bet = self.base_bet(self.__base_chip)
        self.__flow = ''  # 清空打牌日志
        self.select_button()  # 选择庄家
        self.play_log('Round %d start, Tax:%d, Button:%d' %
                     (self.__round_id, self.__consume, self.__button))
        self.send_cards()  # 发牌

        for seatid in range(0, TOTAL_SEAT):
            p = self.__seats[seatid]
            if not p or p.status != p.IN_PLAYING:
                continue
            send_data = [CONFIG.game_id, CMD_ROUND_START, self.__zid, self.__tid,
                         self.__consume, self.__base_chip, self.__total_bet, self.__button]
            p.send(send_data)

        DelayCall(ROUND_START_SECONDS, self.turn_to_next, self.__button, True)

    # 选择庄家，第一轮是随机选庄
    def select_button(self):
        if self.__random_button or 0 > self.__button or TOTAL_SEAT <= self.__button:
            self.__random_button = False
            self.__button = 0
            ulist = []  # 集合
            for i in xrange(0, TOTAL_SEAT):
                if self.__seats[i] and self.__seats[i].status == player.IN_PLAYING:
                    ulist.append(i)
            if ulist and len(ulist) > 0:
                random.shuffle(ulist)
                self.__button = ulist[0]
        return self.__button

    # 发牌
    def send_cards(self):
        for i in xrange(0, 3):
            for j in xrange(0, TOTAL_SEAT):
                if not self.__seats[j]:
                    continue
                self.__seats[j].receiveCard(self.__poker.pop())

    # 获得玩家可操作的动作
    def get_play_actions(self, p):
        ret = list()
        ret.append(CMD_USER_LOOK)
        ret.append(CMD_USER_FOLD)
        if not p:
            return ret
        min_chip = self.calc_call_chip(p.is_dark)
        # 跟死自负
        if p.uchip >= min_chip and p.total_bet / self.__base_chip < self.__total_hands:
            ret.append(CMD_USER_CALL)
            if self.__raise_rate < MAX_RAISE_RATE:
                ret.append(CMD_USER_RAISE)
            if self.can_duel:
                ret.append(CMD_USER_DUEL)
        return ret

    # 获得玩家的响应秒数
    def get_user_seconds(self, seatid, is_begginer=False):
        seconds = FIRST_CALL_SECONDS if is_begginer else CALL_SECONDS
        user_seconds = self.__seats[seatid].roundSeconds
        seconds = user_seconds if user_seconds > 0 else seconds
        return seconds

    # 玩家开始接收动作
    def turn_to_player(self, seatid, is_begginer=False):
        self.play_log('Turn to %d.' % (seatid, ))
        if not self.__seats[seatid]:
            self.play_log('user %d gone, turn to next next...' % (seatid, ))
            self.turn_to_next(seatid)
            return
        self.__seats[seatid].onTurnTo(self)
        seconds = self.get_user_seconds(seatid, is_begginer)

        actions = self.get_play_actions(self.__seats[seatid])  # 玩家可操作的动作
        send_data = [CONFIG.game_id, CMD_TURN_TO_PLAYER, self.__zid, self.__tid,
                     seatid, seconds, self.__round_count, actions]
        self.broad_cast(send_data)
        self.__timer = DelayCall(seconds, self.on_user_time_out, seatid)
        self.__curr_seat_id = seatid

    # 处理玩家超时
    def on_user_time_out(self, seatid):
        self.__seats[seatid].incrTimeOutTimes()
        self.user_fold(self.__seats[seatid])
        self.turn_to_next(seatid)

    # 检查是否合法的seatid
    @staticmethod
    def is_seatid(seat_id):
        return TOTAL_SEAT > seat_id >= 0

    # 记录玩家比牌关系
    def save_duel(self, seatid1, seatid2):
        if not self.is_seatid(seatid1) or not self.is_seatid(seatid2):
            return
        self.__duel_dict[seatid1].add(seatid2)
        self.__duel_dict[seatid1].add(seatid1)
        self.__duel_dict[seatid2].add(seatid1)
        self.__duel_dict[seatid2].add(seatid2)

    # 清除比牌关系列表
    def clear_duel(self):
        for i in xrange(0, TOTAL_SEAT):
            self.__duel_dict[i].clear()

    # 随机挑选出一个比牌的玩家
    def pick_enemy_random(self, uid):
        left_player = []
        for i in xrange(0, TOTAL_SEAT):
            if not self.__seats[i]:
                continue
            if self.__seats[i].uid != uid and self.__seats[i].status == player.IN_PLAYING:
                left_player.append(i)
        if not left_player:
            return False
        return random.choice(left_player)

    # 执行玩家的动作
    def do_user_action(self, p, cmd, ret):
        p.reset_time_out_times()  # 玩家请求成功，重置超时次数

        if cmd == CMD_USER_LOOK:  # 看牌不算一个动作，所以返回false以防止转到下一玩家
            self.user_check(p)
            return False
        elif cmd == CMD_USER_CALL:
            return self.user_call(p)
        elif cmd == CMD_USER_RAISE:
            if not ret or len(ret) != 3 or ret[2] < 1:
                self.manager.request_fail(p.uid, cmd, ERR_DATA_BROKEN)
                return False
            rate = ret[2]
            if rate not in RAISE_RATE_LIST:
                self.manager.request_fail(p.uid, cmd, ERR_DATA_BROKEN)
                return False
            if rate <= self.__raise_rate:
                self.manager.request_fail(p.uid, cmd, ERR_DATA_BROKEN)
                return False
            return self.user_raise(p, rate)
        elif cmd == CMD_USER_FOLD:
            return self.user_fold(p)
        elif cmd == CMD_USER_DUEL:
            if not ret or len(ret) != 3:
                self.manager.request_fail(p.uid, cmd, ERR_DATA_BROKEN)
                return False
            seatid = ret[2]
            if seatid < 0 or seatid >= TOTAL_SEAT:
                self.manager.request_fail(p.uid, cmd, ERR_SEAT_NOT_EXIST)
                return False
            p2 = self.__seats[seatid]
            if not p2:
                self.manager.request_fail(p.uid, cmd, ERR_USER_NOT_EXIST)
                return False
            return self.user_duel(p, p2)

        self.manager.request_fail(p.uid, cmd, ERR_ILLEGAL_OPERATION)
        return False

    # 处理玩家的游戏动作,包括看牌，下注/跟注，加注，弃牌，比牌，开牌
    def deal_user_action(self, p, ret):
        cmd = ret[1]
        if self.status != TABLE_PLAYING:  # 非游戏中不响应玩家游戏命令
            return self.manager.request_fail(p.uid, cmd, ERR_NOT_IN_PLAYING)
        if self.__curr_seat_id != p.seatid:  # 未轮到玩家
            return self.manager.request_fail(p.uid, cmd, ERR_NOT_YOUR_TURN)

        if cmd not in self.get_play_actions(p):  # 不允许进行的操作
            return self.manager.request_fail(p.uid, cmd, ERR_ILLEGAL_OPERATION)

        if not self.do_user_action(p, cmd, ret):
            return

        self.turn_to_next(self.__curr_seat_id)  # 下一个玩家继续

    # 处理机器人的游戏动作
    def deal_robot_action(self, robot, cmd, param1):
        if not self.do_user_action(robot, cmd, [CONFIG.game_id, cmd, param1]):
            return
        self.turn_to_next(self.__curr_seat_id)  # 下一个玩家继续

    # 玩家弃牌处理
    def user_fold(self, p):
        if p.seatid == self.__curr_seat_id:  # 只有当前玩家可以清除定时器
            self.cancel()
        chip = p.total_bet  # 玩家总下注
        exp = 0
        self.save_round_result(p.seatid, False, chip, exp)
        p.on_round_over(self, False, chip, exp, player.IN_FOLD)
        if p == self.__winner:
            self.__winner = None

        self.broad_cast([CONFIG.game_id, CMD_USER_FOLD, OK, p.seatid])
        return True

    # 计算跟牌、下注所需要的筹码
    def calc_call_chip(self, is_dark):
        if self.__is_dark == is_dark:
            return self.__last_bet
        if self.__is_dark and not is_dark:
            return self.__last_bet * 2
        return self.__last_bet / 2

    # 玩家下注/跟注
    def user_call(self, p):
        chip = self.calc_call_chip(p.is_dark)
        if not p.bet(chip):
            self.manager.request_fail(p.uid, CMD_USER_CALL, ERR_CHIP_NOT_ENOUGH)
            return False

        self.__total_bet += chip
        self.save_bet(chip, p.is_dark)
        self.cancel()
        send_data = [CONFIG.game_id, CMD_USER_CALL, OK, p.seatid,
                     int(p.is_dark), chip, self.__total_bet]
        self.broad_cast(send_data)
        return True

    # 玩家加注
    def user_raise(self, p, rate):
        minchip = self.calc_call_chip(p.is_dark)
        chip = self.__base_chip * rate

        if not p.is_dark:
            chip *= 2

        if chip < minchip:
            return self.user_call(p)

        if not p.bet(chip):
            self.manager.request_fail(p.uid, CMD_USER_RAISE, ERR_CHIP_NOT_ENOUGH)
            return False

        self.__raise_rate = rate
        self.__total_bet += chip
        self.save_bet(chip, p.is_dark)
        self.cancel()
        send_data = [CONFIG.game_id, CMD_USER_RAISE,
                     OK, p.seatid, int(p.is_dark), chip, rate, self.__total_bet]
        self.broad_cast(send_data)
        return True

    # 返回当前可否进行比牌的操作
    @property
    def can_duel(self):
        return self.__round_count >= 2

    # 玩家比牌
    # 第三轮及之后才可以比牌
    def user_duel(self, p1, p2):
        if not self.can_duel or not p2:
            self.manager.request_fail(
                p1.uid, CMD_USER_DUEL, ERR_ROUND_THREE_NEEDED)
            return False
        return True

    # 玩家看牌动作
    def user_check(self, p):
        p.set_dark(False)
        send_data = [CONFIG.game_id, CMD_USER_LOOK, OK, p.cards]
        p.send(send_data)

        # 广播玩家看牌
        send_data = [CONFIG.game_id, CMD_LOOK_BC, p.seatid]
        self.broad_cast(send_data)
        return True

    # 获得最后剩余的玩家
    def get_last_player(self):
        for i in xrange(0, TOTAL_SEAT):
            if not self.__seats[i]:
                continue
            if self.__seats[i].status == player.IN_PLAYING:
                return self.__seats[i]

    # 获得当局中没有被淘汰的玩家数量
    @property
    def playing_num(self):
        count = 0
        for i in xrange(0, TOTAL_SEAT):
            if self.__seats[i] and self.__seats[i].status == player.IN_PLAYING:
                count += 1
        return count

    # 记录最后一玩家所下注以及是否暗注
    def save_bet(self, chip, is_dark):
        self.__is_dark = is_dark
        self.__last_bet = chip

    # 保存玩家的结算结果，因为有的是弃牌，有的是比牌被K，而这些玩家可能中途就离开
    def save_round_result(self, seatid, is_win, chip, exp):
        self.__round_results[seatid] = [seatid, int(is_win), chip, exp]

    def clear_round_result(self):
        self.__round_results.clear()

    # 获取玩家的手牌
    def get_cards(self, seat_id):
        if not self.__seats[seat_id]:
            return []
        return self.__seats[seat_id].cards

    # 检查是否累加游戏轮数
    def check_round_count(self, seat_id):
        if seat_id == self.__button:
            DelayCall(0.1, self.incr_round_count)

    # 累加游戏轮数
    def incr_round_count(self):
        self.__round_count += 1

    # 获取下家的坐位ID
    def get_next_seatid(self, curr_seatid):

        for i in xrange(curr_seatid + 1, TOTAL_SEAT):
            self.check_round_count(i)
            if not self.__seats[i]:
                continue
            if self.__seats[i] and self.__seats[i].status == player.IN_PLAYING:
                return i

        for i in xrange(0, min(curr_seatid, TOTAL_SEAT)):
            self.check_round_count(i)
            if not self.__seats[i]:
                continue
            if self.__seats[i] and self.__seats[i].status == player.IN_PLAYING:
                return i

        return curr_seatid

    # 通知下一个玩家操作
    def turn_to_next(self, curr_seatid, is_begginer=False):
        if self.status != TABLE_PLAYING:
            return

        if self.__wait_seconds > 0:
            DelayCall(self.__wait_seconds, self.turn_to_next, curr_seatid)
            self.__wait_seconds = 0
            return

        if self.playing_num < 2:  # 玩家数小于2，结算
            self.check_out(self.get_winner())
            return

        self.turn_to_player(self.get_next_seatid(curr_seatid), is_begginer)

    # 获得当前循环用户还剩余的时间,单位为秒
    def left_seconds(self):
        return self.__timer.int_left_seconds

    # 取消定时器的定时操作
    def cancel(self):
        if self.__timer:
            self.__timer.cancel()

    # 获得当前的胜者
    def get_winner(self):
        if not self.__winner:
            return self.get_last_player()
        return self.__winner

    # 游戏结算 输赢加减钱
    def check_out(self, winner):
        if self.status != TABLE_PLAYING:
            self.play_log("checkout error: not in playing. %d" % (self.status, ))
            return
        if not winner:
            self.play_log("checkout error: no winner")
        self.play_log("checkout")

        self.cancel()
        self.__round_count = 0
        self.set_status(TABLE_CHECK_OUT)

        winchip = self.__total_bet
        if winner:
            self.save_round_result(winner.seatid, True, winchip, WIN_EXP)
            winner.on_round_over(
                self, True, winchip, WIN_EXP, player.IN_WAITING)
            self.__button = winner.seatid

        send_data = [CONFIG.game_id, CMD_CHECK_OUT,
                     self.__zid, self.__tid, CHECKOUT_SECONDS]
        for i, data in self.__round_results.items():
            send_data.append(data)

        self.clear_round_result()
        self.broad_cast(send_data)

        for seatid, duelers in self.__duel_dict.items():  # 通知底牌
            if not duelers:
                continue
            p = self.__seats[seatid]
            if not p or p.isQuit or (not p.online):
                continue
            send_data = [
                CONFIG.game_id, CMD_NOTIFY_CARDS, self.__zid, self.__tid]
            for i in duelers:
                ptmp = self.__seats[i]
                if not ptmp:
                    continue
                attr_data = [i]
                attr_data.extend(ptmp.cards)
                send_data.append(attr_data)
            p.send(send_data)

        DelayCall(CHECKOUT_SECONDS, self.check_out_over)

    # 结算结束，修改桌子状态，清理钱不够的玩家，准备开始新一局
    def check_out_over(self):
        if self.status != TABLE_CHECK_OUT:
            return
        self.set_status(TABLE_READY)
        self.quit_robot()  # 退出多余的机器人
        self.__winner = None

        for seat_id in xrange(0, TOTAL_SEAT):  # 清理筹码不够的玩家出房间
            p = self.__seats[seat_id]
            if not p:
                continue
            if p.isQuit:
                self.__seats[seat_id] = None
                continue
            p.setRoundSeconds(0)
            quit_type = 0
            if p.uchip < self.__limit_chip:  # 筹码不足退出
                quit_type = 1
            elif not p.online:  # 离线则退出
                quit_type = 2
            elif p.timeOutTimes >= 2:  # 超时两次则退出
                quit_type = 3
            if quit_type > 0 and seat_id == self.__button:
                self.__random_button = True
            if 0 < quit_type:
                self.manager.do_user_quit(p, self, quit_type)
                self.__seats[seat_id] = None
            else:
                p.setStatus(player.IN_WAITING)

        self.manager.update_table_player_num(self.__zid, self.__tid, self.play_num)
        self.update_game_wait_seconds()
        self.check_start()  # 检查是否再开始游戏

    # 退出房间内多余的机器人，一次只退一个
    def quit_robot(self):
        if self.play_num <= 3:
            return
        for seatid in xrange(0, TOTAL_SEAT):  # 清理多余的机器人出房间
            p = self.__seats[seatid]
            if not p:
                continue
            if not p.isRobot:
                continue

            self.manager.deal_robot_quit(self, p)
            return

    # 发送当前房间内的已进入的玩家至某玩家
    def send_players_in_table(self, to_player):
        for seatid in range(0, TOTAL_SEAT):
            if not self.__seats[seatid]:
                continue
            p = self.__seats[seatid]
            if p.isQuit:
                continue
            if p != to_player:
                data = self.manager.get_user_arrive_data(self.__zid, self.__tid, p)
                to_player.send(data)

    @property
    def game_wait_seconds(self):
        if self.status != TABLE_READY:
            return 0
        return utils.timestamp() - self.__game_wait_seconds

    # 更新游戏桌子等待开始时间
    def update_game_wait_seconds(self):
        self.__game_wait_seconds = utils.timestamp()

    # 玩家进入成功, 收到成功消息并收到其它玩家的数据,
    # 此处并不广播自己成功的消息，广播由manager来做
    def on_sit_down_success(self, p):
        if not p or not self.in_table(p.uid):
            return

        if self.play_num <= 1 and self.status != TABLE_PLAYING:
            self.update_game_wait_seconds()

        send_data = [CONFIG.game_id, CMD_SIT_DOWN,
                     self.__zid, self.__tid, p.uchip, p.seatid, p.status]
        p.send(send_data)
        self.__random_button = True

        self.send_players_in_table(p)

        self.user_re_connect(p)

    # 玩家断线重连
    def user_re_connect(self, p):
        if self.status != TABLE_PLAYING:
            return
        cards = p.cards
        send_data = [CONFIG.game_id, CMD_RE_CONNECT,
                     OK, self.__zid, self.__tid, self.__total_bet]
        actions = self.get_play_actions(self.__seats[self.__curr_seat_id])
        send_data.extend([self.__button, self.__curr_seat_id, actions, self.left_seconds(),
                          self.__base_chip, self.__raise_rate, self.__last_bet, self.__is_dark])
        if p.is_dark:
            send_data.append([])
        else:
            send_data.append(cards)
        for i in xrange(0, TOTAL_SEAT):
            ptmp = self.__seats[i]
            if not ptmp or ptmp.status < player.IN_PLAYING:
                continue
            send_data.append(
                [i, int(ptmp.isDark), ptmp.currBet, ptmp.status, p.total_bet])

        p.send(send_data)
        p.set_online(True)

    # 玩家退出房间
    def user_quit(self, p, reason=0):
        if not p or p.is_quit or not self.in_table(p.uid):
            return False

        self.play_log('user quit %d@%d when %d' %
                     (p.uid, p.seatid, self.status))
        if self.status == TABLE_PLAYING and p.status == player.IN_PLAYING:
            self.user_fold(p)
            if p.seatid == self.__curr_seat_id:
                self.turn_to_next(self.__curr_seat_id)

        self.broad_cast(
            [CONFIG.game_id, CMD_USER_QUIT, OK, p.uid, p.seatid, reason])

        p.set_quit(True)
        self.__seats[p.seatid] = None

        return True

    # 桌子内广播
    def broad_cast(self, data, not_to_uid=0):
        for x in range(0, TOTAL_SEAT):
            if not self.__seats[x]:
                continue
            p = self.__seats[x]
            if p.isQuit:
                continue
            if not p.online:  # 广播时不包括已离线的玩家
                continue
            if p.tid != self.__tid:  # 不包括已进别的房间的玩家
                continue
            if p.uid != not_to_uid:
                p.send(data)

    # 打牌日志
    def play_log(self, log_data):
        self.__flow += log_data + "\n"
        utils.log(log_data, 'table_' + str(self.__tid) + '.log')

    # 返回当前机器人是否大过所有真人
    def is_winner(self, robot):
        flag = True
        if not robot:
            pass
        for i in xrange(0, TOTAL_SEAT):
            p = self.__seats[i]
            if not p or p.status != player.IN_PLAYING or p.isRobot:
                continue

            # [c1, c2, c3] = robot.cards
            # [d1, d2, d3] = p.cards

        return flag
