#coding:utf-8
import sys
sys.path.append('..')
import random
from config import *
import utils
from models import online_model
from models import user_model
from collections import OrderedDict
from utils import DelayCall, LoopingCall
from referee import Referee
import player


__all__ = ["ServiceBase", "ServiceBank", "ServiceControl", "ServiceMall",
           "ServiceMall", "ServiceLogin", "ServiceGame", "ServiceSystem"]


class ServiceBase(object):

    @property
    def service_type(self):
        raise Exception("property service_type must be override!")

    @property
    def is_running(self):
        raise Exception("Property is_running must be override!")

    def exec_cmd(self, session, data):
        raise Exception("Method exec_cmd must be override!")

    def start(self):
        raise Exception("Method start must be override!")

    def stop(self):
        raise Exception("Method stop must be override!")

    def request_fail(self, cmd, error):
        return [self.service_type, cmd, error]

    def request_ok(self, cmd, data=None):
        return [self.service_type, cmd, OK, data]


class ServiceBank(utils.Singleton, ServiceBase):

    def __init__(self):
        self.__is_running = False  # 是否运行中

    @property
    def is_running(self):
        return self.__is_running

    def start(self):
        if self.is_running:
            return
        self.__is_running = True

    def stop(self):
        if not self.is_running:
            return
        self.__is_running = False

    @property
    def service_type(self):
        return SERVICE_BANK


class ServiceMall(utils.Singleton, ServiceBase):

    def __init__(self):
        self.__is_running = False  # 是否运行中

    @property
    def is_running(self):
        return self.__is_running

    def start(self):
        if self.is_running:
            return
        self.__is_running = True

    def stop(self):
        if not self.is_running:
            return
        self.__is_running = False

    @property
    def service_type(self):
        return SERVICE_MALL


class ServiceSystem(utils.Singleton, ServiceBase):

    def __init__(self):
        self.__is_running = False  # 是否运行中

    @property
    def is_running(self):
        return self.__is_running

    def start(self):
        if self.is_running:
            return
        self.__is_running = True

    def stop(self):
        if not self.is_running:
            return
        self.__is_running = False

    @property
    def service_type(self):
        return SERVICE_SYSTEM

    # 执行系统命令的入口
    def exec_cmd(self, session, data):
        print 'exec system cmd: ', data


class ServiceControl(utils.Singleton, ServiceBase):

    def __init__(self):
        self.__is_running = False  # 是否运行中

    @property
    def is_running(self):
        return self.__is_running

    def start(self):
        if self.is_running:
            return
        self.__is_running = True

    def stop(self):
        if not self.is_running:
            return
        self.__is_running = False

    @property
    def service_type(self):
        return SERVICE_CONTROL

    # 执行控制命令的入口
    def exec_cmd(self, session, data):
        print 'exec control cmd: ', data


class ServiceLogin(utils.Singleton, ServiceBase):

    def __init__(self):
        self.__is_running = False  # 是否运行中
        self.__cmd_func = {}

    @property
    def is_running(self):
        return self.__is_running

    def start(self):
        if self.is_running:
            return

        self.__cmd_func[CMD_LOGIN] = self.on_login
        self.__cmd_func[CMD_LOGIN_BONUS] = self.on_login_bonus
        self.__is_running = True

    def stop(self):
        if not self.is_running:
            return
        self.__is_running = False

    @property
    def service_type(self):
        return SERVICE_LOGIN

    def on_login(self, p, data):
        [_, cmd, ver1, ver2, game_id, channel_id, session_key] = data
        if not game_id or not session_key:
            return self.request_fail(cmd, ERR_DATA_BROKEN)
        if ver1 != VERSION_MAIN:
            return self.request_fail(cmd, ERR_VERSION_ERR)
        if game_id != CONFIG.game_id:
            return self.request_fail(cmd, ERR_SYSTEM_ERR)

        info = online_model.get_by_key(session_key)
        if not info or not info.session_key:
            return self.request_fail(cmd, ERR_DATA_BROKEN)

        ugame = user_model.get(info.uid)
        if not ugame:
            return self.request_fail(cmd, ERR_SYSTEM_ERR)

        from gateway import Gateway
        gw = Gateway.share()
        old_player = gw.get_player(info.uid)
        if old_player:  # 玩家已在线，直接将旧的socket清掉，并更新游戏数据，注意此时不返回任何数据，直接通过socket发送
            p.stop()
            old_player.send([SERVICE_LOGIN, CMD_LOGIN, ERR_RE_LOGIN])
            old_player.close()
            old_player.stop()
            old_player.set_socket(p.sock, p.address)
            old_player.start()
            old_player.set_ugame(ugame)
            old_player.send(self.request_ok(cmd, self.make_user_structure(old_player)))
        else:
            p.set_ugame(ugame)
            gw.save_player(p)
            return self.request_ok(cmd, self.make_user_structure(p))

    def xxx(self, p):
        bonus_flag = 0

        return [SERVICE_LOGIN, CMD_LOGIN, OK, self.make_user_structure(p), p.tid, bonus_flag]

    @staticmethod
    def make_user_structure(p):
        ret = [p.uid, p.unick, p.usex, p.uface, "", "", p.uchip, p.uexp]
        return ret

    def on_login_bonus(self, p, data):
        pass

    # 执行登陆命令的入口
    def exec_cmd(self, p, data):
        print 'exec login service cmd: ', data
        cmd = data[1]
        func = self.__cmd_func[cmd]
        if not func or not callable(func):
            return self.request_fail(cmd, ERR_CMD_ERR)
        return func(p, data)


class ServiceGame(utils.Singleton, ServiceBase):

    def __init__(self):
        self.__zone = {}  # 区域列表, 第0项是每个桌子里面当前所拥有的人数
        self.__player_sets = {}  # 区域所对应的等待中的玩家
        self.__judges = {}  # 桌子对象列表
        self.__cmd_func = {}  # 命令处理函数字典
        self.__tables = {}  # 每个游戏区所对应的桌子列表数据
        self.__zone_table_players = {}  # 游戏区间所对应的桌子里的玩家数量，只计数，不存玩家
        self.__level_robots = {}  # 按等级分好的机器人列表
        self.__ignored_relationship = {}  # 玩家忽略的房间列表
        self.__assign_table_task = None  # 分桌任务
        self.__assign_robots_task = None  # 分机器人任务
        self.__clear_relationship_task = None  # 清理换桌关系任务
        self.__is_running = False  # 是否运行中

    @property
    def is_running(self):
        return self.__is_running

    def start(self):
        if self.is_running:
            return
        self.init()
        self.__is_running = True

    def stop(self):
        if not self.is_running:
            return
        self.__is_running = False

    @property
    def service_type(self):
        return SERVICE_GAME

    # 执行游戏命令的入口
    def exec_cmd(self, p, data):
        cmd = data[1]
        if cmd in PLAY_ACTIONS:  # 执行玩家游戏命令
            judge = self.__judges.get(p.tid)
            if not judge:
                utils.log("judge: " + str(p.tid) + " not exist", "no_table.log")
                return False
            judge.deal_user_action(p, data)
            return True

        func = self.__cmd_func[cmd]
        if not func or not callable(func):
            utils.log("cmd " + str(cmd) + " not bind", 'command_unknow.log')
            return self.request_fail(cmd, ERR_CMD_ERR)

        return func(p, data)

    # 注册命令的处理函数, 只需要注册响应客户端的命令
    def setup_command_function(self):
        self.__cmd_func[CMD_ENTER_ZONE] = self.on_enter_zone
        self.__cmd_func[CMD_USER_QUIT] = self.on_user_quit
        self.__cmd_func[CMD_RE_CONNECT] = self.on_re_connect
        self.__cmd_func[CMD_CHANGE_TABLE] = self.on_change_table

    def init(self):
        self.setup_command_function()
        self.init_zone()

        self.__assign_table_task = LoopingCall(0.1, self.do_assign_table)  # 启动分桌检查
        self.__assign_table_task.start()

        self.__assign_robots_task = LoopingCall(1.0, self.do_assign_robot)  # 启动分配机器人检查
        self.__assign_robots_task.start()

        # 清理换桌关系数据
        self.__clear_relationship_task = LoopingCall(1 * 60, self.clear_ignored_relationship)
        self.__clear_relationship_task.start()

    def init_zone(self):
        pass

    # 初始化一个区的所有桌子
    def init_zone_tables(self, zid):
        pass

    # 初始化一个桌子和裁判
    def init_judge(self, zid, row):
        if not row:
            return
        judge = Referee(row)
        self.__judges[row.tid] = judge
        self.__tables[zid].append(row.tid)
        self.__zone_table_players[zid][row.tid] = 0

    # 接收机器人数据，并初始化机器人
    def on_push_robots(self, ret):
        pass

    # 更新manager里面的桌子玩家数量
    def update_table_player_num(self, zid, tid, num):
        self.__zone_table_players[zid][tid] = num

    # 获得某区域的消耗值
    def zone_consume_chip(self, zid):
        return self.__get_zone_info(zid, 2)

    # 获得某区域的底注
    def zone_base_chip(self, zid):
        return self.__get_zone_info(zid, 3)

    # 获得某区域的限制筹码值，小于此值则一局结束后被踢出
    def zone_limit_chip(self, zid):
        return self.__get_zone_info(zid, 4)

    # 获得某区域的玩家最高下注倍数，大于此值则封顶
    def zone_total_hands(self, zid):
        return self.__get_zone_info(zid, 5)

    def __get_zone_info(self, zid, offset):
        zone = self.__zone.get(zid)
        if zone:
            return zone[offset]
        return 0

    # 玩家退出房间时清理
    def clear_player(self, p):
        p.set_tid(0)  # 清除桌子数据
        uid = p.uid
        if p.zid > 0:
            uset = self.__player_sets.get(p.zid)
            if uset:
                try:
                    uset.remove(uid)
                except Exception as data:
                    print data
                    pass
        p.set_zid(0)  # 清除所在区域ID

        if not p.online:
            pass
            #self.del_player(p)

    # 玩家退出当前桌
    def on_user_quit(self, p, ret):
        judge = self.__judges.get(p.tid)
        self.do_user_quit(p, judge, 0)

    # 处理manager里面的玩家离线
    def do_user_quit(self, p, judge, quit_reason=0):
        if p and judge and p.tid != judge.tid:
            return

        if judge:
            judge.user_quit(p, quit_reason)
        else:
            send_data = [CONFIG.game_id, CMD_USER_QUIT,
                         OK, p.uid, p.seatid, quit_reason]
            p.send(send_data)

        self.clear_player(p)

    # 处理机器人退出某房间的命令
    def deal_robot_quit(self, judge, robot):
        judge.user_quit(robot)
        data = [CONFIG.game_id, CMD_USER_QUIT,
                OK, robot.uid, robot.seatid, 0]
        if judge:
            judge.broad_cast(data)
        self.back_robot(judge.zid, robot)

    # 根据tid来获得judge
    def get_judge(self, tid):
        return self.__judges.get(tid)

    # 搜索游戏中并且有空位的桌子
    def search_playing_table(self, zid, ignored_tables):
        player_count = self.__zone_table_players.get(zid)
        if not player_count:
            return None
        data = OrderedDict(
            sorted(player_count.items(), key=lambda t: t[1], reverse=True))
        for tid, num in data.items():
            judge = self.__judges.get(tid)
            if not judge:
                continue
            if 0 >= judge.play_num:
                continue
            if 5 <= judge.play_num:
                continue
            if tid in ignored_tables:  # 不进入已忽略的桌子列表
                continue
            return judge
        return None

    # 搜索可用的桌子
    def search_empty_table(self, zid):
        if self.__tables.get(zid) is None:
            return None
        for tid in self.__tables.get(zid):
            judge = self.__judges.get(tid)
            if not judge:
                continue
            if judge.status == judge.TREADY and judge.play_num == 0:
                return judge

        #tid = table_model.add(zid)
        #self.init_judge(zid, table_model.get(tid))
        return self.search_empty_table(zid)

    # 处理玩家进入游戏区
    def on_enter_zone(self, p, ret):
        if p.tid > 0:  # 玩家已经在某个房间中了
            return self.request_fail(CMD_ENTER_ZONE, ERR_RE_ENTER_SAME_ZONE)

        zid = ret[2]
        if not zid or 0 >= zid:  # 玩家没有待处理的进入操作
            return self.request_fail(CMD_ENTER_ZONE, ERR_DATA_BROKEN)

        zone = self.__zone.get(zid)

        return self.on_enter_zone_success(zone, p)

    # 进入游戏区成功
    def on_enter_zone_success(self, zone, p):
        if not zone:  # zone not exist
            return self.request_fail(CMD_ENTER_ZONE, ERR_ZONE_NOT_EXIST)
        if not p.load_game_data():  # 重加载玩家数据
            return self.request_fail(CMD_ENTER_ZONE, ERR_USER_NOT_EXIST)
        if p.uchip < zone[3] or p.uchip < zone[4]:  # chip not enough
            return self.request_fail(CMD_ENTER_ZONE, ERR_CHIP_NOT_ENOUGH)

        zid = zone[1]
        p.set_zid(zid)
        self.add_to_zone_waiting_list(zid, p.uid)  # 添加玩家ID至等待列表

        # 发送成功结果至客户端
        data = [SERVICE_GAME, CMD_ENTER_ZONE, OK, zid, p.uchip]
        return data

    # 将玩家退回到等待列表
    def back_player(self, zid, uid):
        #-----------未能开始，将玩家ID重新放回等待区------------#
        if uid and uid > 0:
            self.__player_sets[zid].add(uid)
        #-----------end------------------------------------#

    # 从指定区域中弹出一位玩家
    def pop_player(self, zid):
        try:
            uid = self.__player_sets[zid].pop()
        except Exception as data:
            utils.log("assign table error: " + str(zid) + str(data), "ddd.log")
            return None
        #return self.__players.get(uid)

    # 分配桌子
    def do_assign_table(self):
        for zid, zone in self.__zone.items():
            waiting_num = len(self.__player_sets.get(zid))
            if waiting_num <= 0:
                continue

            p = self.pop_player(zid)
            if not p:  # 玩家数据异常
                continue

            judge = self.search_playing_table(
                zid, self.get_ignored_tables(p.uid))  # 搜索游戏中的有空位的桌子
            if not judge:
                judge = self.search_empty_table(zid)  # 没有空闲桌子，开新桌
                if not judge:  # 空桌也没有，直接退回等待列表
                    self.back_player(zid, p.uid)
                    continue

            if judge.sit_down(p) == OK:
                judge.broad_cast(self.get_user_arrive_data(zid, judge.tid, p), p.uid)
                judge.check_start()  # 检查是否开始游戏

    # 搜索等待开局中并且有空位的桌子
    def search_waiting_table(self, zid):
        player_count = self.__zone_table_players.get(zid)
        if not player_count:
            return None
        for tid, num in player_count.items():
            if 0 >= num or 3 <= num:
                continue
            judge = self.__judges.get(tid)
            if not judge:
                continue
            seconds = random.randint(4, 8)  # 4-8秒内未分配机器人的，则添加
            if judge.game_wait_seconds >= seconds:
                return judge
        return None

    # 将机器人退回到等待列表
    def back_robot(self, zid, robot):
        #-----------未能开始，将玩家ID重新放回等待区------------#
        if robot:
            self.__level_robots[zid].add(robot)

    # 从指定区域中弹出一位机器人
    def pop_robot(self, zid):
        try:
            robot = self.__level_robots[zid].pop()
        except Exception as data:
            utils.log("pop robot error: " + str(zid) + str(data), "ddd.log")
            return None
        return robot

    def debug(self, zid, tid):
        print 'debug: ', zid, tid
        player_count = self.__zone_table_players.get(zid)
        judge = self.__judges.get(tid)
        print player_count, judge
        if player_count:
            print 'num: ', player_count.get(tid)
        if judge:
            print "wait seconds: ", judge.GameWaitSeconds

        print self.__level_robots.get(zid)

    # 分配机器人
    def do_assign_robot(self):
        for zid, zone in self.__zone.items():
            if not self.__level_robots.get(zid) or len(self.__level_robots.get(zid)) <= 0:
                continue

            judge = self.search_waiting_table(zid)  # 搜索等待中的桌子
            if not judge:
                continue

            p = self.pop_robot(zid)
            if not p:  # 没有机器人可以陪玩
                continue
            if p.uchip < zone[3] or p.uchip < zone[4]:  # chip not enough
                p.robotAddChips(zone[4] * 10)  # 10倍最小进入加筹码
                if p.uchip < zone[3] or p.uchip < zone[4]:
                    continue

            if judge.sit_down(p) == OK:
                judge.broad_cast(self.get_user_arrive_data(zid, judge.tid, p), p.uid)
                judge.check_start()  # 检查是否开始游戏

    # 断线重连请求
    def on_re_connect(self, p, ret):
        if p.tid <= 0:
            if p.zid > 0:  # 走正常进区间的流程
                return self.on_enter_zone_success(self.__zone.get(p.zid), p)
            else:  # 错误返回，不在此游戏区内
                return self.request_fail(CMD_RE_CONNECT, ERR_ZONE_NOT_EXIST)
        judge = self.__judges.get(p.tid)
        if not judge:  # table not exist
            return self.request_fail(CMD_RE_CONNECT, ERR_TABLE_FULL)

        judge.sit_down(p)

    # 执行玩家请求换桌
    def on_user_change_table(self, p, judge, seconds=2):
        DelayCall(seconds, self.do_user_change_table, p, judge)

    def do_user_change_table(self, p, judge):
        judge.user_quit(p, 4)
        p.on_change_table()
        DelayCall(1, self.add_to_zone_waiting_list, p.zid, p.uid)

    # 处理玩家请求换桌的请求
    def on_change_table(self, p, ret):
        if not ret or len(ret) != 3:
            return self.request_fail(CMD_CHANGE_TABLE, ERR_DATA_BROKEN)
        if p.tid <= 0 or p.zid <= 0:
            return self.request_fail(CMD_CHANGE_TABLE, ERR_TABLE_FULL)
        judge = self.__judges.get(p.tid)
        if not judge:  # table not exist
            return self.request_fail(CMD_CHANGE_TABLE, ERR_TABLE_FULL)

        flag = (ret[2] == 1)
        if flag == p.need_change_table:  # 无需改变当前换桌状态
            return

        p.set_need_change_table(flag)
        self.save_ignored_relationship(p.uid, judge.tid)
        data = [CONFIG.game_id, CMD_CHANGE_TABLE, OK, ret[2]]
        p.send(data)

        if p.status != player.IN_PLAYING and flag:
            self.on_user_change_table(p, judge)

    def get_ignored_tables(self, uid):
        if self.__ignored_relationship.get(uid):
            return self.__ignored_relationship[uid][1]
        return []

    def save_ignored_relationship(self, uid, tid):
        if not self.__ignored_relationship.get(uid):
            self.__ignored_relationship[uid] = [utils.timestamp(), [tid]]
        else:
            self.__ignored_relationship[uid][0] = utils.timestamp()
            self.__ignored_relationship[uid][1].append(tid)
            self.__ignored_relationship[uid][1] = self.__ignored_relationship[uid][1][-2:]

    def clear_ignored_relationship(self):
        for uid, relation in self.__ignored_relationship.items():
            if utils.timestamp() - relation[0] >= 5 * 60:
                del self.__ignored_relationship[uid]

    # 生成玩家抵达的数据包
    @staticmethod
    def get_user_arrive_data(zid, tid, p):
        if not p:
            return None
        data = [CONFIG.game_id, CMD_USER_ARRIVE, zid, tid, p.uid,
                p.uchip, p.seatid, p.uface, p.usex, p.unick, p.status]
        return data

    # 添加至游戏的等待集合
    def add_to_zone_waiting_list(self, zid, uid):
        if not self.__zone.get(zid):
            return False
        self.__player_sets[zid].add(uid)
        return True