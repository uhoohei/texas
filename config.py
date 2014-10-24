# coding:utf-8

import os as _os
from utils import utils as _utils
from utils.utils import ReadOnlyObjectDict as _ReadOnlyObjectDict


# APP根目录
APP_BASE_PATH = _os.path.dirname(_os.path.realpath(__file__))
_config_file = APP_BASE_PATH + '/config.json'


class ConfigWithJsonFile(_ReadOnlyObjectDict):

    def reload(self):
        """
        重加载配置文件
        """
        content = _utils.read_json_file(_config_file)
        self.update(content)


# json配置文件里面的数据
CONFIG = ConfigWithJsonFile(_utils.read_json_file(_config_file))


VERSION_MAIN = 1  # 主版本号
VERSION_SUB = 1  # 子版本号


# ----------------------- 服务类型集合 ------------------------------------------#
SERVICE_CONTROL = 0  # 服务器的控制命令
SERVICE_LOGIN = 1  # 登陆服务
SERVICE_SYSTEM = 2  # 系统服务
SERVICE_MALL = 3  # 商城服务
SERVICE_BANK = 4  # 银行服务
SERVICE_GAME = 5  # 普通场游戏服务
# ----------------------- 服务类型集合 ------------------------------------------#


# ----------------------- 服务端控制命令集 ------------------------------------------#
CMD_SET_SERVICE_TYPE = 1  # 设置服务类型
CMD_SERVER_HEART_BEAT = 2  # 心跳命令
CMD_REQUEST_CENTER = 3  # 请求返回的响应
CMD_PUSH_ROBOTS = 4  # 推送机器人数据
# ----------------------- 服务端命令结束 ----------------------------------------#


# ----------------------- 登录相关命令集 -----------------------------------------#
# login command
CMD_LOGIN = 1  # login cmd
CMD_LOGIN_BONUS = 2  # 登陆奖励
CMD_EARN_GUEST_UPDATE_CHIP = 6  # 获得升级账号的游戏币
CMD_EDIT_PROFILE = 8  # 修改个人资料
# ----------------------- 登录相关命令集 -----------------------------------------#


# ----------------------- 系统相关命令集 -----------------------------------------#
CMD_USER_HEART_BEAT = 1  # heart beat cmd
CMD_BROAD_CAST = 2  # broad cast cmd
CMD_SYSTEM_ERROR = 3  # 系统错误
CMD_PAUSE_HEART_BEAT = 4  # 暂停心跳命令
CMD_SERVER_IN_PAUSE = 5  # 服务器维护中
CMD_GET_RANK = 6  # 请求排行榜的命令
# ----------------------- 系统相关命令集 -----------------------------------------#


# ---------------------- 银行的相关命令 -----------------------------------------#
CMD_CHIP_IN = 1  # 存款
CMD_CHIP_OUT = 2  # 取款
CMD_CHIP_QUERY = 3  # 查询保险箱中的钱
# ---------------------- 银行的相关命令 -----------------------------------------#


# ---------------------- 游戏的命令列表 -----------------------------------------#
CMD_ENTER_ZONE = 1  # 进入区间
CMD_USER_ARRIVE = 2  # 玩家抵达
CMD_USER_QUIT = 3  # 玩家退出
CMD_SIT_DOWN = 4  # 玩家坐下
CMD_ROUND_START = 5  # 游戏开始
CMD_TURN_TO_PLAYER = 6  # 轮到某人
CMD_USER_CALL = 7  # 玩家下/跟注
CMD_USER_RAISE = 8  # 玩家加注
CMD_USER_FOLD = 9  # 玩家弃牌
CMD_USER_LOOK = 10  # 玩家看牌
CMD_USER_DUEL = 11  # 玩家比牌(决斗)
CMD_LOOK_BC = 12  # 某玩家已经看过牌
CMD_CHECK_OUT = 13  # 结算命令
CMD_RE_CONNECT = 14  # 玩家重连
CMD_LOTTERY_CHIP = 15  # 喜钱命令
CMD_NOTIFY_CARDS = 16  # 通知底牌
CMD_CHANGE_TABLE = 17  # 要求换桌
# ---------------------- 游戏的命令列表 -----------------------------------------#


# 玩家需操作的动作列表
PLAY_ACTIONS = [CMD_USER_CALL, CMD_USER_RAISE,
                CMD_USER_FOLD, CMD_USER_LOOK, CMD_USER_DUEL]


# 命令的格式的定义, 这里只定义客户端请求的数据，这里要做必要的命令过滤
COMMANDS_FORMAT = dict()
COMMANDS_FORMAT[SERVICE_LOGIN] = {
    CMD_LOGIN: "iiiiiis",
    CMD_LOGIN_BONUS: "ii",
}
COMMANDS_FORMAT[SERVICE_SYSTEM] = {

}
COMMANDS_FORMAT[SERVICE_GAME] = {
    CMD_ENTER_ZONE: "iii",
    CMD_USER_QUIT: "ii",
    CMD_USER_CALL: "ii",
    CMD_USER_RAISE: "iii",
    CMD_USER_FOLD: "ii",
    CMD_USER_LOOK: "ii",
    CMD_USER_DUEL: "iii",
    CMD_RE_CONNECT: "ii",
    CMD_CHANGE_TABLE: "iii",
}


# 服务端错误码列表：类型为short
ERR_OK = 1
ERR_CMD_ERR = -2  # 命令错误
ERR_VERSION_ERR = -3  # 版本号错误
ERR_DATA_BROKEN = -6  # 客户端请求数据错误，不符合即定格式
ERR_SYSTEM_ERR = -5  # 系统错误
ERR_RE_LOGIN = -7  # 客户端收到通知，账号已在别处登陆
ERR_ZONE_NOT_EXIST = -8  # 所请求的游戏区不存在
ERR_TABLE_FULL = -9  # 没有可用的桌子
ERR_CHIP_NOT_ENOUGH = -10  # 进入失败，金币不足
ERR_SEAT_FULL = -11  # 没有可用的坐位
ERR_RE_ENTER_SAME_ZONE = -12  # 重复进入同一游戏区域
ERR_CHIP_FAIL = -13  # 进入失败，金币异常
ERR_USER_NOT_EXIST = -14  # 玩家数据不存在
ERR_RULE_BROKEN = -15  # 出牌不符合规则
ERR_NOT_YOUR_TURN = -16  # 当前循问的玩家不是你
ERR_NOT_IN_PLAYING = -17  # 当前并非游戏中状态，请求失败
ERR_CARD_NOT_EXIST = -18  # 所出牌不存在

ERR_SERVICE_UNIQUE_ERROR = -21  # 尝试进入不同的游戏服务
ERR_USER_NOT_FREE = -22  # 玩家并非自由状态，不能进入排队列表

ERR_USER_IS_NOT_GUEST = -23  # 玩家并非游客状态，不能再次升级

ERR_ROUND_THREE_NEEDED = -24  # 至少要到第三轮才可以比牌
ERR_ILLEGAL_OPERATION = -25  # 非法操作
ERR_SEAT_NOT_EXIST = -26  # 不存在的坐位id
ERR_LOCK_SERVICE_FAIL = -27  # 锁定玩家失败


HEART_BEAT_SECONDS = 51  # 玩家的心跳时间


if __name__ == "__main__":
    print APP_BASE_PATH
