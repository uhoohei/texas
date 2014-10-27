# coding:utf-8
import sys
sys.path.append("..")
import unittest
from controllers.poker import *
import random
import time


class CardsTest(unittest.TestCase):

    def test_is_card(self):
        """
        make(suit, value), suit(c), value(c)
        测试是否是扑克牌对象
        """
        self.assertRaises(ValueError, make, -1, 2)
        self.assertRaises(ValueError, make, 5, 2)
        self.assertRaises(ValueError, make, 1, 1)
        self.assertRaises(ValueError, make, 5, 1)
        self.assertRaises(ValueError, make, 1, 15)
        self.assertRaises(ValueError, make, -1, 15)
        self.assertTrue(make(1, 2))

    def test_type1(self):
        """测试单张牌的牌型与大小"""
        c = make(2, 14)
        ret = card_type1([c])
        self.assertEqual(ret[0], 14)
        self.assertEqual(ret[1], 2)

    def test_type2(self):
        c1 = make(2, 3)
        c2 = make(1, 3)
        ret = card_type2([c1, c2])
        self.assertEqual(ONE_PAIR, ret[0])  # 测试3的对子
        self.assertEqual(3, ret[1])
        c2 = make(1, 14)
        ret = card_type2([c1, c2])
        self.assertEqual(HIGH_CARD, ret[0])
        self.assertEqual(14, ret[1])

    def test_type3(self):
        """
        测试三张牌时的牌型返回函数
        三张牌的大小比较：
        三条：三条的值
        对子：对子的值，大单张的值，大单张的花色
        高牌：高牌的值，高牌的花色
        """
        c1 = make(3, 9)
        c2 = make(2, 9)
        c3 = make(1, 9)
        ret = card_type3([c1, c2, c3])
        self.assertEqual(ret[0], THREE_OF_A_KIND)
        self.assertEqual(ret[1], 9)
        c3 = make(1, 10)
        ret = card_type3([c1, c2, c3])
        self.assertEqual(ret[0], ONE_PAIR)
        self.assertEqual(ret[1], 9)
        self.assertEqual(ret[2], 10)
        self.assertEqual(ret[3], 1)
        c2 = make(3, 14)
        clist = [c1, c2, c3]
        ret = card_type3(clist)
        self.assertEqual(ret[0], HIGH_CARD)
        self.assertEqual(ret[1], 14)
        self.assertEqual(ret[2], 3)

        self.assertEqual(0, card_sort_cmp(make(2, 5), make(2, 5)))  # 同大小的牌比较
        self.assertEqual(1, card_sort_cmp(make(2, 5), make(1, 5)))  # 花色较大的牌比较

    def test_type4(self):
        """
        四张牌的大小比较 ：
        四条：四条的值
        三条：三条的值
        对子：对子的值，大单张的值，大单张的花色
        高牌：高牌的值，高牌的花色
        """
        c1 = make(4, 5)
        c2 = make(2, 5)
        c3 = make(1, 5)
        c4 = make(3, 5)

        ret = card_type4([c1, c2, c3, c4])
        self.assertEqual(FOUR_OF_A_KIND, ret[0])
        self.assertEqual(5, ret[1])

        c3 = make(1, 10)
        ret = card_type4([c1, c2, c3, c4])
        self.assertEqual(THREE_OF_A_KIND, ret[0])
        self.assertEqual(value(c1), ret[1])
        c3 = make(1, 2)
        ret = card_type4([c1, c2, c3, c4])
        self.assertEqual(THREE_OF_A_KIND, ret[0])
        self.assertEqual(value(c2), ret[1])

        # 对子分析
        c2 = make(1, 9)
        for i in range(0, 5):
            clist = [c1, c2, c3, c4]
            random.shuffle(clist)
            ret = card_type4(clist)
            self.assertTrue(ONE_PAIR == ret[0])
            self.assertTrue(5 == ret[1])
            self.assertTrue(9 == ret[2])
            self.assertTrue(1 == ret[3])

        c1 = make(2, 8)
        c4 = make(2, 7)
        ret = card_type4([c1, c2, c3, c4])
        self.assertEqual(HIGH_CARD, ret[0])
        self.assertEqual(9, ret[1])
        self.assertEqual(1, ret[2])

    def test_int(self):
        # 将扑克牌转化为short的表述方式
        c1 = make(3, 10)
        c2 = make(2, 10)
        c3 = make(1, 3)
        clist = [c1, c2, c3]
        for c in clist:
            self.assertTrue(0 < c)

    def test_find_biggest2(self):
        """
        # 测试七选五的算法2，要挑出最大的牌
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
        """
        tmptime = time.time()
        data = [[1, 3], [2, 4], [3, 5], [4, 6], [1, 7], [2, 8], [4, 8]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        for i in range(0, 100):  # 测试顺子
            rtype, rlist = find_biggest2(clist)
        print "2:", time.time() - tmptime
        self.assertTrue(rtype[0] == STRAIGHT)
        self.assertTrue(rtype[1] == 8)
        self.assertTrue(rtype[2] == 4)
        self.assertTrue(value(rlist[0]) == 8)
        self.assertTrue(suit(rlist[0]) == 4)
        self.assertTrue(value(rlist[1]) == 7)
        self.assertTrue(value(rlist[2]) == 6)
        self.assertTrue(value(rlist[3]) == 5)
        self.assertTrue(value(rlist[4]) == 4)

        tmptime = time.time()
        data = [[1, 3], [2, 4], [3, 5], [4, 2], [1, 14], [2, 8], [4, 8]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        for i in range(0, 100):  # 测试A2345特殊顺子
            rtype, rlist = find_biggest2(clist)
        print "2:", time.time() - tmptime
        self.assertTrue(rtype[0] == STRAIGHT)
        self.assertTrue(rtype[1] == 5)
        self.assertTrue(rtype[2] == 3)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [14, 5, 4, 3, 2])

        tmptime = time.time()
        data = [10, 11, 3, 4, 12, 13, 14]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(1, item))
        for i in range(0, 100):  # 测试皇家同花顺
            rtype, rlist = find_biggest2(clist)
        print "3:", time.time() - tmptime
        self.assertTrue(rtype[0] == ROYAL_FLUSH)
        self.assertTrue(rtype[1] == 1)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [14, 13, 12, 11, 10])

        tmptime = time.time()
        data = [10, 11, 3, 4, 12, 13, 9]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(1, item))
        for i in range(0, 100):  # 测试同花顺
            rtype, rlist = find_biggest2(clist)
        print "4:", time.time() - tmptime
        self.assertTrue(rtype[0] == STRAIGHT_FLUSH)
        self.assertTrue(rtype[1] == 13)
        self.assertTrue(rtype[2] == 1)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [13, 12, 11, 10, 9])

        tmptime = time.time()
        data = [10, 7, 3, 4, 12, 13, 9]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(1, item))
        for i in range(0, 100):  # 测试同花
            rtype, rlist = find_biggest2(clist)
        print "4:", time.time() - tmptime
        self.assertTrue(rtype[0] == FLUSH)
        self.assertTrue(rtype[1] == 13)
        self.assertTrue(rtype[2] == 1)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [13, 12, 10, 9, 7])

        tmptime = time.time()
        data = [14, 11, 3, 4, 5, 2, 9]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(1, item))
        for i in range(0, 100):  # 测试A2345同花顺
            rtype, rlist = find_biggest2(clist)
        print "5:", time.time() - tmptime
        self.assertTrue(rtype[0] == STRAIGHT_FLUSH)
        self.assertTrue(rtype[1] == 5)
        self.assertTrue(rtype[2] == 1)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [14, 5, 4, 3, 2])

        tmptime = time.time()
        data = [[1, 13], [2, 13], [3, 13], [4, 13], [1, 14], [2, 3], [2, 14]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        for i in range(0, 100):  # 测试四条
            rtype, rlist = find_biggest2(clist)
        print "6:", time.time() - tmptime
        self.assertTrue(rtype[0] == FOUR_OF_A_KIND)
        self.assertTrue(rtype[1] == 13)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [13, 13, 13, 13, 14])

        tmptime = time.time()
        data = [[1, 3], [2, 3], [3, 3], [4, 6], [3, 6], [2, 6], [2, 14]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        for i in range(0, 100):  # 测试葫芦1
            rtype, rlist = find_biggest2(clist)
        print "7:", time.time() - tmptime
        self.assertTrue(rtype[0] == FULL_HOUSE)
        self.assertTrue(rtype[1] == 6)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [6, 6, 6, 3, 3])

        tmptime = time.time()
        data = [[1, 3], [2, 3], [3, 3], [4, 6], [3, 6], [1, 14], [2, 14]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        for i in range(0, 100):  # 测试葫芦2
            rtype, rlist = find_biggest2(clist)
        print "8:", time.time() - tmptime
        self.assertTrue(rtype[0] == FULL_HOUSE)
        self.assertTrue(rtype[1] == 3)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [3, 3, 3, 14, 14])

        tmptime = time.time()
        data = [[1, 3], [2, 3], [3, 9], [4, 6], [3, 6], [1, 14], [2, 14]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        for i in range(0, 100):  # 测试三对的情况1
            rtype, rlist = find_biggest2(clist)
        print "8:", time.time() - tmptime
        self.assertTrue(rtype[0] == TWO_PAIRS)
        self.assertTrue(rtype[1] == 14)
        self.assertTrue(rtype[2] == 6)
        self.assertTrue(rtype[3] == 9)
        self.assertTrue(rtype[4] == 3)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [14, 14, 6, 6, 9])

        tmptime = time.time()
        data = [[1, 3], [2, 3], [3, 2], [4, 6], [3, 6], [1, 14], [2, 14]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        for i in range(0, 100):  # 测试三对的情况2
            rtype, rlist = find_biggest2(clist)
        print "9:", time.time() - tmptime
        self.assertTrue(rtype[0] == TWO_PAIRS)
        self.assertTrue(rtype[1] == 14)
        self.assertTrue(rtype[2] == 6)
        self.assertTrue(rtype[3] == 3)
        self.assertTrue(rtype[4] == 2)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [14, 14, 6, 6, 3])

        # 三条，三条的牌的值
        tmptime = time.time()
        data = [[1, 11], [2, 11], [3, 11], [4, 8], [3, 6], [1, 10], [2, 3]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        for i in range(0, 100):  # 测试三对的情况2
            rtype, rlist = find_biggest2(clist)
        print "10:", time.time() - tmptime
        self.assertTrue(rtype[0] == THREE_OF_A_KIND)
        self.assertTrue(rtype[1] == 11)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [11, 11, 11, 10, 8])

        # 两对，第一大对的值，第二大对的值，最大单牌的值，最大单牌的花色
        tmptime = time.time()
        data = [[1, 3], [2, 3], [3, 2], [4, 8], [3, 8], [1, 10], [2, 14]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        for i in range(0, 100):
            rtype, rlist = find_biggest2(clist)
        print "11:", time.time() - tmptime
        self.assertTrue(rtype[0] == TWO_PAIRS)
        self.assertTrue(rtype[1] == 8)
        self.assertTrue(rtype[2] == 3)
        self.assertTrue(rtype[3] == 14)
        self.assertTrue(rtype[4] == 2)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [8, 8, 3, 3, 14])

        # 两对，第一大对的值，第二大对的值，最大单牌的值，最大单牌的花色
        tmptime = time.time()
        data = [[1, 3], [2, 3], [3, 2], [4, 8], [3, 8], [1, 7], [2, 5]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        for i in range(0, 100):
            rtype, rlist = find_biggest2(clist)
        print "11:", time.time() - tmptime
        self.assertTrue(rtype[0] == TWO_PAIRS)
        self.assertTrue(rtype[1] == 8)
        self.assertTrue(rtype[2] == 3)
        self.assertTrue(rtype[3] == 7)
        self.assertTrue(rtype[4] == 1)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [8, 8, 3, 3, 7])

        # 5d 6s 8d Ac 8c 4c As 问题数据测试
        # 两对，第一大对的值，第二大对的值，最大单牌的值，最大单牌的花色
        tmptime = time.time()
        data = [[1, 5], [4, 6], [1, 8], [2, 14], [2, 8], [2, 4], [4, 14]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        for i in range(0, 100):
            rtype, rlist = find_biggest2(clist)
        print "11:", time.time() - tmptime
        # print rtype, cards_to_str(rlist)
        self.assertTrue(rtype[0] == TWO_PAIRS)
        self.assertTrue(rtype[1] == 14)
        self.assertTrue(rtype[2] == 8)
        self.assertTrue(rtype[3] == 6)
        self.assertTrue(rtype[4] == 4)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [14, 14, 8, 8, 6])

        # 一对，第一大对的值，最大单牌的值，最大单牌的花色
        tmptime = time.time()
        data = [[1, 3], [2, 6], [3, 2], [4, 8], [3, 8], [1, 7], [2, 5]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        for i in range(0, 100):
            rtype, rlist = find_biggest2(clist)
        print "11:", time.time() - tmptime
        self.assertTrue(rtype[0] == ONE_PAIR)
        self.assertTrue(rtype[1] == 8)
        self.assertTrue(rtype[2] == 7)
        self.assertTrue(rtype[3] == 1)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [8, 8, 7, 6, 5])

        # 一对，对子的值，最大单牌的值，最大单牌的花色
        tmptime = time.time()
        data = [[1, 10], [2, 10], [3, 2], [4, 8], [3, 12], [1, 11], [2, 14]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        for i in range(0, 100):
            rtype, rlist = find_biggest2(clist)
        print "12:", time.time() - tmptime
        self.assertTrue(rtype[0] == ONE_PAIR)
        self.assertTrue(rtype[1] == 10)
        self.assertTrue(rtype[2] == 14)
        self.assertTrue(rtype[3] == 2)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [10, 10, 14, 12, 11])

        # 高牌，高牌的值，高牌的花色
        tmptime = time.time()
        data = [[1, 5], [2, 10], [3, 2], [4, 8], [3, 12], [1, 11], [2, 14]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        for i in range(0, 100):
            rtype, rlist = find_biggest2(clist)
        print "13:", time.time() - tmptime
        self.assertTrue(rtype[0] == HIGH_CARD)
        self.assertTrue(rtype[1] == 14)
        self.assertTrue(rtype[2] == 2)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [14, 12, 11, 10, 8])

        # 杂牌，杂牌的值，杂牌的花色
        tmptime = time.time()
        data = [[1, 2], [2, 3], [3, 4], [4, 6], [3, 7], [1, 8], [2, 9]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        for i in range(0, 100):
            rtype, rlist = find_biggest2(clist)
        print "14:", time.time() - tmptime
        self.assertTrue(rtype[0] == HIGH_CARD)
        self.assertTrue(rtype[1] == 9)
        self.assertTrue(rtype[2] == 2)
        rvalue = [value(rlist[0]), value(rlist[1]), value(
            rlist[2]), value(rlist[3]), value(rlist[4])]
        self.assertTrue(rvalue == [9, 8, 7, 6, 4])

    def test_pair_compare(self):
        cl1 = [make(1, 3), make(4, 13), make(2, 14), make(
            4, 2), make(3, 11), make(1, 11), make(4, 6)]
        cl2 = [make(4, 11), make(4, 10), make(2, 11), make(
            4, 7), make(3, 4), make(1, 14), make(1, 12)]
        type1, bigfive1 = find_biggest2(cl1)
        type2, bigfive2 = find_biggest2(cl2)
        self.assertTrue(compare_type(type1, type2) == MORE)

    def test_three_equal(self):
        tmptime = time.time()
        # [[1, 5], [2, 5], [1, 8], [2, 8], [3, 10], [4, 10], [4, 14]]
        data = [[1, 5], [2, 9], [3, 11], [2, 5]]
        clist = []
        random.shuffle(data)
        for item in data:
            clist.append(make(item[0], item[1]))
        clist += [0, 0, 0]
        self.assertFalse(find_biggest2(clist))

    # 测试扑克重置,发牌
    def test_init(self):
        poker = Poker()
        for i in range(0, 52):
            c = poker.pop()
            self.assertTrue(is_card(c))


if __name__ == '__main__':
    unittest.main()
