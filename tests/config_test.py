# coding:utf-8
import sys
sys.path.append('..')
import unittest
from config import *


class ConfigTest(unittest.TestCase):

    def test_config(self):
        self.assertTrue(CONFIG.game_id > 0)
        self.assertTrue(len(CONFIG.game_name) > 0)
        self.assertTrue(CONFIG.is_debug is not None)
        self.assertTrue(CONFIG.heart_beat_seconds > 0)

if __name__ == '__main__':
    unittest.main()
