# coding:utf-8
import random
from copy import deepcopy

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

EQUAL = 1  # 相等
MORE = 2  # 大于
LESS = 3  # 小于

COMPARE_EQUAL = 3  # 值比较相等
COMPARE_MORE_THAN_ONE = 2  # 值比较刚好大1
COMPARE_MORE_THAN_MANY = 1  # 值比较大于1


# 返回所有的有效扑克牌
def get_all_cards():
    cards = []
    for _value in range(2, 15):
        for _suit in range(1, 5):
            cards.append(make(_suit, _value))
    return cards


# 制造一张扑克牌，去掉大小王
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


def cards_power_single(card_list):
    """
    一张牌的大小比较顺序
    高牌，高牌的值
    """
    return value(card_list[0])


def cards_power_pair(card_list):
    """
    二张牌的大小比较顺序
    对子：对子的值
    高牌：高牌的值
    """
    [c1, c2] = card_list
    if value(c1) == value(c2):
        return ONE_PAIR, value(c1)
    return (HIGH_CARD, value(c1)) if value(c1) > value(c2) else (HIGH_CARD, value(c2))


def card_sort_cmp(c1, c2):
    """sort方法的自定义比较函数，用于比较两张扑克牌的大小"""
    if value(c1) > value(c2):
        return 1
    elif value(c1) < value(c2):
        return -1
    if suit(c1) > suit(c2):
        return 1
    elif suit(c1) < suit(c2):
        return -1
    return 0


def cards_power_three(card_list):
    """
    注意：sort后调用函数的card_list的值确实被改变了
    三张牌的大小比较：
    三条：三条的值
    对子：对子的值，大单张的值
    高牌：高牌的值，高牌的花色
    """
    card_list.sort(card_sort_cmp, reverse=True)
    [c1, c2, c3] = card_list
    if value(c1) == value(c2) and value(c2) == value(c3):
        return THREE_OF_A_KIND, value(c1)
    if value(c1) == value(c2):
        return ONE_PAIR, value(c1), value(c3)
    if value(c2) == value(c3):
        return ONE_PAIR, value(c2), value(c1)
    return HIGH_CARD, value(c1)


def cards_power_four(card_list):
    """
    四张牌的大小比较 ：
    四条：四条的值
    三条：三条的值
    对子：对子的值，大单张的值
    高牌：高牌的值
    """
    card_list.sort(card_sort_cmp, reverse=True)
    [c1, c2, c3, c4] = card_list
    if value(c1) == value(c2) and value(c2) == value(c3) and value(c3) == value(c4):
        return FOUR_OF_A_KIND, value(c1)
    # 排序后要么前三张成三条，要么后三张成三条
    if value(c1) == value(c2) and value(c2) == value(c3):  # 第一种情况的三条
        return THREE_OF_A_KIND, value(c1)
    if value(c2) == value(c3) and value(c3) == value(c4):  # 第二种情况的三条
        return THREE_OF_A_KIND, value(c2)
    if value(c1) == value(c2):  # 1,2成对子
        return ONE_PAIR, value(c1), value(c3)
    elif value(c2) == value(c3):  # 2,3成对子
        return ONE_PAIR, value(c2), value(c1)
    elif value(c3) == value(c4):  # 3,4成对子
        return ONE_PAIR, value(c3), value(c1)
    return HIGH_CARD, value(c1)


def calc_neighboring_compare_relationship(card_list):
    """计算相临牌之间的大小比较关系，调用前要对card_list排序"""
    ret = []  # 保存牌之间的大小比较关系
    for i in range(0, len(card_list) - 1):
        if value(card_list[i]) == value(card_list[i + 1]):
            ret.append(COMPARE_EQUAL)  # 相等
        elif value(card_list[i]) == value(card_list[i + 1]) + 1:
            ret.append(COMPARE_MORE_THAN_ONE)  # 大于1
        else:
            ret.append(COMPARE_MORE_THAN_MANY)  # 大于多
    return ret


def find_biggest_by_three_equal(card_list):
    """有3个及以上相等的条件，则可能的牌型只有四条，葫芦，三对中的一种"""
    value_dict = {}
    for item in card_list:
        if not value_dict.get(value(item)):
            value_dict[value(item)] = []
        value_dict[value(item)].append(item)
    fh_value1 = 0
    fh_value2 = 0
    pairs = []
    max_card = None  # 最大单牌
    for cvalue, cardlist in value_dict.items():
        len_of_equal = len(cardlist)
        if len_of_equal == 4:  # 成四条
            biggest_card = card_list[4] if value(
                cardlist[0]) == value(card_list[0]) else card_list[0]
            rlist = cardlist + [biggest_card]
            rtype = (FOUR_OF_A_KIND, value(rlist[0]))
            return rtype, rlist
        elif len_of_equal == 3:  # 成葫芦了,注意这里可能成两个三条
            if not fh_value1:
                fh_value1 = cvalue
            elif not fh_value2:
                fh_value2 = cvalue
        elif len_of_equal == 2:  # 成对子了
            pairs.append(cvalue)
        elif len_of_equal == 1 and not max_card:
            max_card = cardlist[0]

    pairs.sort(reverse=True)
    if fh_value1:  # 成葫芦了
        rlist = value_dict[fh_value1]
        if fh_value2:  # 两个三条选一个
            rlist = value_dict[max(fh_value1, fh_value2)]
            rlist += value_dict[min(fh_value1, fh_value2)][0:2]
        else:  # 标准葫芦
            rlist += value_dict[pairs[0]]
        rtype = (FULL_HOUSE, value(rlist[0]))
        return rtype, rlist
    if value(value_dict[pairs[2]][0]) > value(max_card):
        max_card = value_dict[pairs[2]][0]
    rlist = value_dict[pairs[0]] + \
        value_dict[pairs[1]] + [max_card]  # 成两对，要从中选择两对出来
    rtype = (TWO_PAIRS, value(rlist[0]), value(
        rlist[2]), value(rlist[4]), suit(rlist[4]))
    return rtype, rlist


def find_biggest_by_flush(card_list):
    """成同花的情况下返回牌型"""
    flush_count = [0, 0, 0, 0]  # 花色统计
    for c in card_list:
        flush_count[suit(c) - 1] += 1
    for i in range(0, len(flush_count)):
        if flush_count[i] >= 5:  # 成同花了
            suit_list = []
            for item in card_list:
                if suit(item) == i + 1:
                    suit_list.append(item)
            # 在同花列表里面寻找同花顺与皇家同花顺
            suit_compare = calc_neighboring_compare_relationship(suit_list)
            ret_straight = find_biggest_by_straight(suit_list, suit_compare)
            if ret_straight:  # 成同花顺和皇家同花顺
                rtype, rlist = ret_straight
                rtype = (STRAIGHT_FLUSH, value(rlist[0]), suit(rlist[0]))
                if value(rlist[0]) == 14:
                    rtype = (ROYAL_FLUSH, suit(rlist[0]))
                return rtype, rlist
            ret_special = find_biggest_by_special_straight(suit_list)
            if ret_special:  # A2345小同花顺
                rtype, rlist = ret_special
                rtype = (STRAIGHT_FLUSH, value(rlist[1]), suit(rlist[1]))
                return rtype, rlist
            rlist = suit_list[0:5]  # 普通同花
            rtype = (FLUSH, value(rlist[0]), suit(rlist[0]))
            return rtype, rlist
    return False


def find_biggest_by_straight(card_list, compare):
    """寻找顺子"""
    rlist = []
    for i in range(0, len(compare)):
        if not rlist:
            rlist.append(card_list[i])
        if compare[i] == COMPARE_MORE_THAN_ONE:
            rlist.append(card_list[i + 1])
        elif compare[i] == COMPARE_EQUAL:
            continue
        else:
            rlist = []
        if len(rlist) >= 5:
            break
    if len(rlist) >= 5:  # 成顺子了
        rlist = rlist[0:5]
        rtype = (STRAIGHT, value(rlist[0]), suit(rlist[0]))
        return rtype, rlist
    return False


_special_straight = [14, 5, 4, 3, 2]  # A2345小顺子


def find_biggest_by_special_straight(card_list):
    """寻找特殊顺子"""
    rlist = []
    rvalue = []
    for item in card_list:
        if value(item) in _special_straight:
            if value(item) not in rvalue:
                rlist.append(item)
                rvalue.append(value(item))
    if rvalue == _special_straight:
        rtype = (STRAIGHT, value(rlist[1]), suit(rlist[1]))
        return rtype, rlist
    return False


def find_biggest_by_two_equal(card_list, compare):
    """寻找两对或三条"""
    first_index = compare.index(COMPARE_EQUAL)
    if first_index <= 4 and compare[first_index] == compare[first_index + 1]:
        rlist = card_list[first_index:(first_index + 3)]  # 成三条
        if first_index > 1:
            rlist += [card_list[0], card_list[1]]
        elif first_index == 0:
            rlist += [card_list[3], card_list[4]]
        elif first_index == 1:
            rlist += [card_list[0], card_list[4]]
        rtype = (THREE_OF_A_KIND, value(card_list[first_index]))
        return rtype, rlist
    max_card = None  # 成两对了
    rlist = []
    for i in range(0, len(compare)):
        if compare[i] == COMPARE_EQUAL:
            rlist.append(card_list[i])
            rlist.append(card_list[i + 1])
            continue
    for i in range(0, len(compare)):
        if not card_list[i] in rlist:
            max_card = card_list[i]
            break
    rlist += [max_card]
    rtype = (TWO_PAIRS, value(rlist[0]), value(
        rlist[2]), value(rlist[4]), suit(rlist[4]))
    return rtype, rlist


def find_biggest_by_one_equal(card_list, compare):
    """寻找对子"""
    rlist = []
    first_index = compare.index(COMPARE_EQUAL)
    rlist.append(card_list[first_index])
    rlist.append(card_list[first_index + 1])
    if first_index > 2:
        rlist += card_list[0:3]
    elif first_index == 0:
        rlist += card_list[2:5]
    elif first_index == 1:
        rlist += [card_list[0]]
        rlist += card_list[3:5]
    elif first_index == 2:
        rlist += card_list[0:2]
        rlist += [card_list[4]]
    rtype = (ONE_PAIR, value(rlist[0]), value(rlist[2]), suit(rlist[2]))
    return rtype, rlist


def find_biggest_high_card(card_list):
    """寻找高牌"""
    ctype = HIGH_CARD  # 成高牌
    rtype = (ctype, value(card_list[0]), suit(card_list[0]))
    return rtype, card_list[0:5]


def search_biggest_cards(card_list):
    """
    7选5的搜索算法
    五张牌的大小比较：不同牌型按以下顺序确定大小，同牌型时按顺序比较后面的特征值
    皇家同花顺，最大牌的花色
    同花顺，最大牌的值，最大牌的花色
    四条，四条的牌的值
    葫芦，三条的牌的值
    同花，第一大牌的值，第一大牌的花色
    顺子，第一大牌的值，第一大牌的花色
    三条，三条的牌的值
    两对，第一大对的值，第二大对的值，最大单牌的值，最大单牌的花色
    一对，对子的值，最大单牌的值，最大单牌的花色
    高牌，高牌的值，高牌的花色
    杂牌，杂牌的值，杂牌的花色
    """
    if len(card_list) != 7 or 0 in card_list:
        return False
    card_list = deepcopy(card_list)
    card_list.sort(card_sort_cmp, reverse=True)
    compare = calc_neighboring_compare_relationship(card_list)  # 保存牌之间的大小比较关系
    equal_num = compare.count(COMPARE_EQUAL)
    # 如果有3个及以上相等的条件，则可能的牌型只有四条、葫芦、两对中的一种
    if equal_num >= 3:
        return find_biggest_by_three_equal(card_list)

    ret_flush = find_biggest_by_flush(card_list)
    if ret_flush:
        return ret_flush  # 成同花的判断
    than_one_num = compare.count(COMPARE_MORE_THAN_ONE)
    if than_one_num >= 4:  # 是否成顺判断
        ret_straight = find_biggest_by_straight(card_list, compare)
        if ret_straight:
            return ret_straight

    if than_one_num >= 3:  # 检查是否成特殊顺A2345
        ret_special = find_biggest_by_special_straight(card_list)
        if ret_special:
            return ret_special

    if equal_num == 2:  # 连续的两个相等则成三条,两个相等则成两对
        return find_biggest_by_two_equal(card_list, compare)

    if equal_num == 1:  # 成对子了
        return find_biggest_by_one_equal(card_list, compare)
    return find_biggest_high_card(card_list)  # 高牌与杂牌


def get_poker_type(card_list):
    """判断牌型及其用来比较大小的关键数值"""
    clen = len(card_list)
    if 4 == clen:
        return cards_power_four(card_list)
    if 3 == clen:
        return cards_power_three(card_list)
    if 2 == clen:
        return cards_power_pair(card_list)
    if 1 == clen:
        return cards_power_single(card_list)
    raise ValueError


def compare_card_list(card_list1, card_list2):
    """皇家同花顺>同花顺>四条>葫芦>同花>顺>三条>两对>一对>高牌"""
    type1 = get_poker_type(card_list1)
    type2 = get_poker_type(card_list2)
    return compare_by_cards_type(type1, type2)


def compare_by_cards_type(type1, type2):
    """比较已选出的牌型"""
    for i in range(0, len(type1)):
        if type1[i] > type2[i]:
            return MORE
        elif type1[i] < type2[i]:
            return LESS
    return EQUAL


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
