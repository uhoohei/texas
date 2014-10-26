# coding:utf-8
import random
import card

# 扑克类，一幅扑克，不含大小王，不含2-6，总共48张牌


class Poker:

    def __init__(self):
        self.__cards = []  # 扑克所含的所有牌
        self.__cursor = 0  # 当前所发到的牌的位置

    def init(self):
        if len(self.__cards) != 32:
            self.__cards = card.get_all_cards()
        self.__cursor = 0  # 已发牌清0
        random.shuffle(self.__cards)

    def pop(self):
        if self.__cursor >= len(self.__cards):
            return 0
        c = self.__cards[self.__cursor]
        self.__cursor += 1
        return c
