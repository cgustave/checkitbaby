# -*- coding: utf-8 -*-
'''
Created on June 22, 2021
@author: cgustave

Fortgate Agent unittest to be run agains test FortiPoC "checkitbaby_tests"
~/github/python/packages/checkitbaby (master *)$ source venv/bin/activate
(venv) ~/github/python/packages/checkitbaby (master *)$ cd checkitbaby/
(venv) ~/github/python/packages/checkitbaby/checkitbaby (master *)$ python tests/test_fortigate.py
'''
import logging as log
import unittest
from fortigate_agent import Fortigate_agent

# create logger
log.basicConfig(
    format='%(asctime)s,%(msecs)3.3d %(levelname)-8s[%(module)-10.10s.\
    %(funcName)-20.20s:%(lineno)5d] %(message)s',
    datefmt='%Y%m%d:%H:%M:%S',
    filename='debug.log',
    level=log.DEBUG)
log.debug("Start unittest")

class Fortigate_agentTestCase(unittest.TestCase):

    # Always run before any test
    def setUp(self):
        # Create specific agent and provide connection details
        self.fgt = Fortigate_agent(debug=True)
        # Connection details
        self.fgt.agent['ip'] = '192.168.122.178'
        self.fgt.agent['port'] = '10101'
        self.fgt.agent['login'] = 'admin'
        self.fgt.agent['password'] = ''
        self.fgt.agent['ssh_key_file'] = ''
        # Feed agent with information it needs for its job
        self.fgt.path='/home/cgustave/github/python/packages/checkitbaby/checkitbaby/tests/playbooks'
        self.fgt.playbook='test'
        self.fgt.run='1'
        self.fgt.testcase=''
        self.fgt.name='unitest'
        self.fgt.conn='0'
        self.fgt.connect(type='fortigate')

    @unittest.skip
    def test_get_status(self):
        result = self.fgt.process(line="FGT-B1-1:1 get status\n")
        self.assertEqual(result['version'],'v6.2.3,build1066,191219')
        self.assertTrue(result['license'])

    @unittest.skip
    def test_check_status_no_requirement(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [fgt_status] status\n")
        self.assertTrue(result)

    @unittest.skip
    def test_check_status_has_license(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [fgt_status] status has license=True\n")
        self.assertTrue(result)

    @unittest.skip
    def test_check_status_has_version(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [fgt_status] status has version=v6.2.3,build1066,191219\n")
        self.assertTrue(result)

    @unittest.skip
    def test_check_status_has_license_and_version(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [fgt_status] status has version=v6.2.3,build1066,191219 license=True\n")
        self.assertTrue(result)

    @unittest.skip
    def test_session_dport_22(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [session_ssh] session filter dport=22\n")
        self.assertTrue(result)

    @unittest.skip
    def test_session_dport_dst(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [session_ssh] session filter dport=22 dst=192.168.0.1\n")
        self.assertTrue(result)

    @unittest.skip
    def test_session_dport_has_state_local(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [session_ssh] session filter dport=22 has state=local\n")
        self.assertTrue(result)

    @unittest.skip
    def test_ping_ok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [ping_test] ping 192.168.0.254\n")
        self.assertTrue(result)

    @unittest.skip
    def test_ping_source_ok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [ping_test] ping vdom=root source=192.168.0.1 192.168.0.254\n")
        self.assertTrue(result)

    @unittest.skip
    def test_ping_nok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [ping_test] ping vdom=root 169.255.1.2\n")
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
