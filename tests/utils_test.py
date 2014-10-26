# coding:utf-8
import sys
sys.path.append('..')
import utils
import unittest


class DatabaseTest(unittest.TestCase):

    def test_time(self):
        utils.timestamp_today() > 0


if __name__ == '__main__':
    unittest.main()
