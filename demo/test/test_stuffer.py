#! /usr/bin/env python
# vim: set fileencoding=utf-8 :


import unittest
import stuffer

class TestStuffer(unittest.TestCase):

    def test_stuff(self):
        result = stuffer.stuff(stuffer.DRUMSTICK)
        self.assertEqual('(  ₺ )=3', result)

    def test_double_stuff(self):
        result = stuffer.stuff(stuffer.DRUMSTICK)
        result = stuffer.stuff(result)
        self.assertEqual('(  ₺₺ )=3', result)

if __name__ == '__main__':
    unittest.main()
