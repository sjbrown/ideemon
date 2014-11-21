#! /usr/bin/env python

import os, sys
import unittest
from unittest import TestCase

class DumbTest(TestCase):
    def test_nothin(self):
        self.assertEquals(2,2.0)

    def test_fail(self):
        self.assertEquals(2,4.0)


if __name__ == '__main__':
    unittest.main()
