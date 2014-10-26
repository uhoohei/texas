# coding:utf-8
import sys
sys.path.append('..')
import random
from player import Player
from models import user_model
import utils
from utils import DelayCall
from config import *


# 平衡范围，在输-5手到正10手范围内算盈亏平衡
BALANCE_RANGE = [-5, 10]

# 平衡间隔时间，在达到某时间段后进行强制平衡，等级越高的AI平衡时间越长
BALANCE_TIME = [300, 600, 1200, 2400]

# AI的性格
OBTRUSION_AI = 1  # 莽撞型，常闷牌
CAUTIOUS_AI = 2  # 谨慎型，不敢玩大的
CLEVER_AI = 3  # 聪明全能型
BRAVE_AI = 4  # 勇敢爱炸型
CHARACTER = [OBTRUSION_AI, CAUTIOUS_AI, CLEVER_AI, BRAVE_AI]

# AI的等级
LEVEL_NORMAL = 0  # 普通等级
LEVEL_MIDDLE = 1  # 中等等级
LEVEL_HIGH = 2  # 高级AI
LEVEL_PRO = 3  # 专业级AI

# 赢利指标，按不同等级往上走，越高级的AI赢利指数就越高, 赢利指百分比
WIN_TARGET = [0, 5, 10, 15]

# 止损点，单局输至某点后强制比牌或者弃牌
LOSE_RATE_MAX = [-25, -50, -150, -200]

# 止赢点，单局最高赢钱点
WIN_RATE_MAX = [50, 100, 200, 300]

# 机器人在一房间内的最长玩牌时间
ROBOT_PLAY_TIME = 10 * 60


# 爱蒙的人的打法
# 跟注2轮，再加注2倍跟2轮，三人以上则比一次，接着跟2轮，再比一次，结算
# 加注已达10倍时，则30%的概率看牌，如果赢定，则6成跟，其它比或弃，如果输定，则6成弃，4成跟或者比
OBTRUSION_FLOW = [
    [CMD_USER_CALL, 1, 3],  # 动作，轮数小值，轮数大值
    [CMD_USER_RAISE, [2, 5]],  # 加注，小倍数，大倍数
    [CMD_USER_CALL, 1, 3],  # 跟注，1～3轮
    [CMD_USER_DUEL, 3],  # 大于3人则比牌一次
    [CMD_USER_CALL, 1, 3],  # 跟注，1~3轮
    [CMD_USER_DUEL, 0],  # 比牌，无人数条件限制，一直比牌直到结算
]


# 从start到end随机添加action
def append_by_action(ret, action, start, end):
    num = random.randint(start, end)
    for i in xrange(0, num):
        ret.append(action)


# 计算爱蒙的人的路径，每局都重橷计算，模板是一样的
def calc_obtrusion_flow():
    ret = []

    append_by_action(
        ret, OBTRUSION_FLOW[0][0], OBTRUSION_FLOW[0][1], OBTRUSION_FLOW[0][2])

    rate = random.choice(OBTRUSION_FLOW[1][1])
    ret.append([OBTRUSION_FLOW[1][0], rate])

    append_by_action(
        ret, OBTRUSION_FLOW[2][0], OBTRUSION_FLOW[2][1], OBTRUSION_FLOW[2][2])

    ret.append(OBTRUSION_FLOW[3])

    append_by_action(
        ret, OBTRUSION_FLOW[4][0], OBTRUSION_FLOW[4][1], OBTRUSION_FLOW[4][2])

    ret.append(OBTRUSION_FLOW[5])
    ret.append(OBTRUSION_FLOW[5])
    ret.append(OBTRUSION_FLOW[5])
    ret.append(OBTRUSION_FLOW[5])

    return ret


# 爱蒙的人的特殊流程
OBTRUSION_SPECIAL = [
    # 加注已达10倍时，30%的概率决策路径,20=>60%概率，40=》90%概率
    [CMD_USER_LOOK, [10, 40], [20, 60], [40, 90]],
    [[60, CMD_USER_CALL], [70, CMD_USER_FOLD],
     [100, CMD_USER_DUEL]],  # 若赢，则70%概率跟,10%弃，20%比
    [[70, CMD_USER_FOLD], [80, CMD_USER_CALL],
     [100, CMD_USER_DUEL]],  # 若输, 70%弃，10%跟，20%比
]


# 根据当前下注倍数来计算是否要走特殊流程
def calc_need_look(curr_rate):
    action = 0
    for i in xrange(1, 3):
        [rate, percent] = OBTRUSION_SPECIAL[0][i]
        if curr_rate >= rate:
            action = 0
            num = random.randint(0, 100)
            if num < percent:
                action = OBTRUSION_SPECIAL[0][0]

    return action


# 根据概率选择特殊看牌之后的动作
def calc_action_after_look(is_win):
    data = OBTRUSION_SPECIAL[1] if is_win else OBTRUSION_SPECIAL[2]
    num = random.randint(0, 99)
    for item in data:
        [percent, tmp_action] = item
        if num < percent:
            return tmp_action


# 计算是否需要修改当前出牌流程
def calc_obtrusion_special_flow(judge, robot):
    chip = judge.calc_call_chip(robot.is_dark)
    curr_rate = chip / judge.base_chip
    action = calc_need_look(curr_rate)
    if not action:
        return 0

    ret = []
    if robot.is_dark:
        ret.append(OBTRUSION_SPECIAL[0][0])
    cmd = calc_action_after_look(judge.is_winner(robot))
    if not cmd:
        return 0
    ret.append(cmd)
    ret.append(0)
    return ret


# 计算机器人的当局的打牌动作列表
def calc_flow(robot):
    ret = calc_obtrusion_flow()
    return ret


# 判断当前的动作是否符合规则
def is_action_allow(judge, robot, action):
    actions = judge.get_play_actions(robot)
    param = 0
    if isinstance(action, int):
        cmd = action

    elif isinstance(action, list):

        if len(action) == 3:
            cmd = action[1]
            param = action[2]
        else:
            cmd = action[0]
            param = action[1]

    else:
        return False

    if cmd not in actions:
        return False

    if cmd == CMD_USER_RAISE:  # 判断加注的倍率是否已经加过了
        if param <= judge.raise_rate:
            return False

    if cmd == CMD_USER_DUEL:  # 比牌则需要判断是否有人数限制
        if judge.playing_num < param:  # 此动作不能执行，因为人数不对
            return False

    return True


# 根据性格，当前局势来决定机器人的动作及相关的数值
# 总下注大于止损点，且输给真人，则弃
# 总下注大于止赢点，且赢了真人，则比
def decide_action(judge, robot):
    if not judge or not robot:
        return

    special_action = calc_obtrusion_special_flow(judge, robot)
    if special_action and is_action_allow(judge, robot, special_action):
        return special_action

    action = 0
    # 判断下一个动作是否可以执行，可否加对应倍数的注，可否比牌
    for i in xrange(1, 5):
        action = robot.enter_next_step()  # 顺序执行下一个动作
        if is_action_allow(judge, robot, action):
            break
    if not action:
        action = CMD_USER_FOLD

    return action


# 获得前一动作的延时
def get_prev_action_seconds(robot, cmd):
    return random.randint(2, 5)


def get_straight_action_seconds(robot, cmd, param):
    return random.randint(6, 10)


# 模拟玩家延时
def get_action_seconds(robot, cmd, param):
    if cmd == CMD_USER_LOOK:
        return random.randint(2, 7)
    return random.randint(2, 7)


# 机器人思考，决定下一步的动作并行动
def thinking(judge, robot):
    if not judge or not robot:
        return

    action = decide_action(judge, robot)
    if not action:
        print 'action empty: ', judge, robot
        return

    cmd = 0  # 要执行的命令
    prev_cmd = 0  # 要预先执行的命令，一般是看牌
    param = 0
    if isinstance(action, int):
        cmd = action
    elif isinstance(action, list):
        if len(action) == 3:
            [prev_cmd, cmd, param] = action
        else:
            [cmd, param] = action

    if cmd == CMD_USER_DUEL:  # 比牌则随机挑选对象
        param = judge.pick_enemy_random(robot.uid)

    if prev_cmd:  # 带前缀动作的执行，主要注意执行时间不能有颠倒
        seconds = get_prev_action_seconds(robot, prev_cmd)
        DelayCall(seconds, judge.deal_robot_action, robot, prev_cmd, 0)
        seconds = get_straight_action_seconds(robot, cmd, param)
        DelayCall(seconds, judge.deal_robot_action, robot, cmd, param)
    else:  # 无前缀动作直接执行
        seconds = get_action_seconds(robot, cmd, param)
        DelayCall(seconds, judge.deal_robot_action, robot, cmd, param)


# 检查机器人是否需要退出当前房间
def should_quit(judge, robot, is_win):
    from services import ServiceGame

    if not robot or not judge:
        return
    time1 = int(ROBOT_PLAY_TIME - ROBOT_PLAY_TIME / 4)
    time2 = int(ROBOT_PLAY_TIME + ROBOT_PLAY_TIME / 4)
    max_time = random.randint(time1, time2)
    if robot.play_time >= max_time:  # 达到时间后退出
        seconds = judge.CHECKOUT_SECONDS - random.randint(0, 3)
        DelayCall(seconds, ServiceGame.share().deal_robot_quit, judge, robot)


def make_uinfo_data(u):
    return [u.uid, u.uemail, u.uname, u.unick, u.ukey, u.uface, u.usex, u.uguest]


class Robot(Player):

    def __init__(self):
        super(Player, self).__init__(None, None)
        self.__steps = []
        self.__curr_step = 0
        self.__play_time = 0

    # 机器人的初始化
    def init(self, uinfo, user, session=None):
        player_uinfo = make_uinfo_data(uinfo)
        Player.init(self, player_uinfo, user, None)
        self.init_robot()

    def init_robot(self):
        self.__steps = []
        self.__curr_step = 0
        self.__play_time = 0

    @property
    def is_robot(self):  # 覆盖你类的方法
        return True

    @property
    def play_time(self):
        return utils.timestamp() - self.__play_time

    # 机器人加游戏币
    def robot_add_chips(self, chips):
        user_model.set_chip(self.uid, chips, 0)
        self.load_game_data()

    # 机器人坐下响应
    def on_sit_down(self, tid, seatid):
        Player.on_sit_down(self, tid, seatid)
        self.__play_time = utils.timestamp()

    # 一局游戏开始前的清理，覆盖了父类的方法
    def on_round_start(self):
        Player.on_round_start(self)  # 调用父类的方法
        self.__steps = calc_flow(self)  # 重新计算自己的出牌步骤
        self.__curr_step = 0

    # 玩家一局结算, 加减金币，计算经验值，覆盖了父类的方法
    def on_round_over(self, referee, is_win, chip, exp, flow):
        Player.on_round_over(self, referee, is_win, chip, exp, flow)
        self.__steps = []
        should_quit(referee, self, is_win)

    # 执行进行下一步骤的操作
    def enter_next_step(self):
        if self.__curr_step >= len(self.__steps) - 1:
            return 0
        curr = self.__steps[self.__curr_step]
        self.__curr_step += 1
        return curr

    # 轮到自己的时候被调用
    def on_turn_to(self, referee):
        Player.on_turn_to(self, referee)
        thinking(referee, self)

    # 设置机器人的步骤, 中途改变固有的步骤
    def set_steps(self, steps):
        self.__steps = steps
        self.__curr_step = 0

    # 发送数据给玩家
    def send(self, obj):
        pass