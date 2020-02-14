# -*- coding: utf-8 -*-
'''
Created on Feb 14, 2020

@author: cgustave
'''
import logging as log
import json
import unittest
from testrunner import Testrunner
from playbook import Playbook

# create logger
log.basicConfig(
    format='%(asctime)s,%(msecs)3.3d %(levelname)-8s[%(module)-10.10s.\
    %(funcName)-20.20s:%(lineno)5d] %(message)s',
    datefmt='%Y%m%d:%H:%M:%S',
    filename='debug.log',
    level=log.DEBUG)

log.debug("Start unittest")

class TestrunnerTestCase(unittest.TestCase):

    # Always run before any test
    def setUp(self):
        self.tr = Testrunner(path='./playbooks', debug=True)

    def test_loading(self):
        self.tr.load_playbook(name="myPlaybook")
        self.tr.playbook.testcases[0].disable()
        self.tr.playbook.testcases[0].enable()
        #self.assertEqual(self.tr.playbook.nb_testcases,2)


if __name__ == '__main__':
    unittest.main()






