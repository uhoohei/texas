# coding:utf-8
import random


# 各种牌型
ROYAL_FLUSH = 10  # 皇家同花顺
STRAIGHT_FLUSH = 9  # 同花顺
FOUR_OF_A_KIND = 8  # 四条
FULL_HOUSE = 7  # 葫芦
FLUSH = 6  # 同花
STRAIGHT = 5  # 顺子
THREE_OF_A_KIND = 4  # 三条
TWO_PAIRS = 3  # 两对
ONE_PAIR = 2  # 一对
HIGH_CARD = 1  # 高牌


# 方块(0) 梅花(1) 红桃(2) 黑桃(3)
SUIT_STR = ("D", "C", "H", "S")
VALUE_STR = ("J", "Q", "K", "A")

EQUAL = 1  # 相等
MORE = 2  # 大于
LESS = 3  # 小于


# 返回所有的有效扑克牌
def get_all_cards():
    cards = []
    for _value in range(2, 15):
        for _suit in range(1, 5):
            cards.append(make(_suit, _value))
    return cards


# 制造一张扑克牌，炸金花没有大小王，这里也去掉了2-6的小牌
def make(_suit, _value):
    if _suit < 1 or _suit > 4:
        raise ValueError
    if 2 > _value or 14 < _value:
        raise ValueError
    return _suit * 100 + _value


# 获得一张牌的花色
def suit(c):
    return c / 100


# 获得一张牌值的大小
def value(c):
    return c % 100


# 测试是否是扑克牌
def is_card(c):
    s = suit(c)
    v = value(c)
    if 1 <= s <= 4 and 2 <= v <= 14:
        return True
    return False


# 判断所给牌是不是顺子,注意这里不判断是不是顺金,只判断是不是顺.
def is_shun_zi(c1, c2, c3):
    if not is_card(c1) or not is_card(c2) or not is_card(c3):
        return False
    tmp = [value(c1), value(c2), value(c3)]
    tmp.sort()
    if tmp[0] + 1 == tmp[1] and tmp[1] == tmp[2] - 1:
        return True
    return False


# 返回值是一个tuple, (牌型，最大一张牌的值，第二大的牌的值，第三大的牌的值)
def get_type(c1, c2, c3):
    """【牌型说明】
    豹子：三张同样大小的牌。
    顺金：花色相同的相连三张牌。
    金花：三张花色相同的牌。
    顺子：三张花色不全相同的相连三张牌。
    对子：三张牌中有两张点数同样大小的牌。(对子是不可能组合成金花的,因为只有一副牌)
    特殊：花色不同的235牌 。
    单张：除以上牌型的牌。
    检查传过来的三张牌,并返回牌型,返回牌型的大小"""
    if not is_card(c1) or not is_card(c2) or not is_card(c3):
        raise ValueError
    values = [value(c1), value(c2), value(c3)]
    values.sort()
    values.reverse()
    card_type = DANZHANG
    is_shun = is_shun_zi(c1, c2, c3)
    if suit(c1) == suit(c2) and suit(c2) == suit(c3):  # 金花与顺金
        if is_shun:
            card_type = SHUNJIN
        else:
            card_type = JINHUA
    elif is_shun:  # 顺子
        card_type = SHUNZI
    elif values[0] == values[1] and values[1] == values[2]:  # 豹子
        card_type = BAOZI
    elif values[0] == values[1] or values[1] == values[2]:  # 对子
        card_type = DUIZI
        if values[1] == values[2]:
            values = [values[1], values[1], values[0]]
    return tuple([card_type] + values)


# 豹子>顺金>金花>顺子>对子>散牌。
# 比牌，所属牌型和每张牌的大小来判断两手牌的大小
def compare(c1, c2, c3, d1, d2, d3):
    type1 = get_type(c1, c2, c3)
    type2 = get_type(d1, d2, d3)
    i = 0
    ret = EQUAL
    for item in type1:
        if item > type2[i]:
            ret = MORE
            break
        elif item < type2[i]:
            ret = LESS
            break
        i += 1
    return ret


# 当且仅当第一手牌大于第二手牌的时候返回True
def is_bigger(c1, c2, c3, d1, d2, d3):
    return True if compare(c1, c2, c3, d1, d2, d3) == MORE else False


# 扑克类，一幅扑克，不含大小王，不含2-6，总共48张牌
class Poker:

    def __init__(self):
        self.__cards = []  # 扑克所含的所有牌
        self.__cursor = 0  # 当前所发到的牌的位置

    def init(self):
        if len(self.__cards) != 32:
            self.__cards = get_all_cards()
        self.__cursor = 0  # 已发牌清0
        random.shuffle(self.__cards)

    def pop(self):
        if self.__cursor >= len(self.__cards):
            return 0
        c = self.__cards[self.__cursor]
        self.__cursor += 1
        return c
