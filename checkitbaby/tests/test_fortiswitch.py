# -*- coding: utf-8 -*-
'''
Created on June 22, 2021
@author: cgustave

FortSwitch Agent unittest to be run agains test FortiPoC "checkitbaby_tests"
~/github/python/packages/checkitbaby (master *)$ source venv/bin/activate
(venv) ~/github/python/packages/checkitbaby (master *)$ cd checkitbaby/
(venv) ~/github/python/packages/checkitbaby/checkitbaby (master *)$ python tests/test_fortiswitch.py
'''
import logging as log
import unittest
from fortiswitch_agent import Fortiswitch_agent

# create logger
log.basicConfig(
    format='%(asctime)s,%(msecs)3.3d %(levelname)-8s[%(module)-10.10s.\
    %(funcName)-20.20s:%(lineno)5d] %(message)s',
    datefmt='%Y%m%d:%H:%M:%S',
    filename='debug.log',
    level=log.DEBUG)
log.debug("Start unittest")

class Fortiswitch_agentTestCase(unittest.TestCase):


    def setUp(self):
        # Create specific agent and provide connection details
        # to be run against Testing FortiPoC
        self.fsw = Fortiswitch_agent(debug=True)
        # Connection details
        self.fsw.agent['ip'] = '192.168.122.178'
        self.fsw.agent['port'] = '10104'
        self.fsw.agent['login'] = 'admin'
        self.fsw.agent['password'] = 'fortinet'
        self.fsw.agent['ssh_key_file'] = ''
        # Feed agent with information it needs for its job
        self.fsw.path='/home/cgustave/github/python/packages/checkitbaby/checkitbaby/tests/playbooks'
        self.fsw.playbook='test'
        self.fsw.run='1'
        self.fsw.testcase=''
        self.fsw.name='unitest'
        self.fsw.conn='0'
        self.fsw.connect(type='fortiswitch')

    def test_process_port_up(self):
        self.fsw.process(line="fsw1:1 port up port1\n")
        result = self.fsw.process(line="fsw1:1 check [port1_status] port status port1 has state=up\n")
        self.assertTrue(result)

    def test_process_port_down(self):
        self.fsw.process(line="fsw1:1 port down port2\n")
        result = self.fsw.process(line="fsw1:1 check [port2_status] port status port2 has state=down\n")
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
