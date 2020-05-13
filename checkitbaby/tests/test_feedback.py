# -*- coding: utf-8 -*-
'''
Created on May 13, 2020

@author: cgustave
'''
import logging as log
import unittest
import json
from feedback import Feedback

# create logger
log.basicConfig(
    format='%(asctime)s,%(msecs)3.3d %(levelname)-8s[%(module)-10.10s.\
    %(funcName)-20.20s:%(lineno)5d] %(message)s',
    datefmt='%Y%m%d:%H:%M:%S',
    filename='debug.log',
    level=log.DEBUG)

log.debug("Start unittest")

class FeedbackTestCase(unittest.TestCase):

    # Always run before any test
    def setUp(self):
        self.fdb = Feedback(filename='tests/feedback.log', debug=True)

    def test10_delete1(self):
        self.fdb.delete()

    def test20_delete2(self):
        self.fdb.delete()

    #@unittest.skip  # no reason needed
    def test30_write(self):
        self.fdb.write(key='mykey', value='myvalue')

    def test40_delete2(self):
        self.fdb.delete()

if __name__ == '__main__':
    unittest.main()






