# -*- coding: utf-8 -*-
'''
Created on June 22, 2021
@author: cgustave

Fortgate Agent unittest to be run agains test FortiPoC "checkitbaby_tests"
~/github/python/packages/checkitbaby (master *)$ source venv/bin/activate
(venv) ~/github/python/packages/checkitbaby (master *)$ cd checkitbaby/
(venv) ~/github/python/packages/checkitbaby/checkitbaby (master *)$ python tests/test_lxc.py
'''
import logging as log
import unittest
from lxc_agent import Lxc_agent

# create logger
log.basicConfig(
    format='%(asctime)s,%(msecs)3.3d %(levelname)-8s[%(module)-10.10s.\
    %(funcName)-20.20s:%(lineno)5d] %(message)s',
    datefmt='%Y%m%d:%H:%M:%S',
    filename='debug.log',
    level=log.DEBUG)
log.debug("Start unittest")

class Lxc_agentTestCase(unittest.TestCase):


    def setup_lxc11(self):
        self.lxc11 = Lxc_agent(debug=True)
        # Connection details
        self.lxc11.agent['ip'] = '192.168.122.178'
        self.lxc11.agent['port'] = '10101'
        self.lxc11.agent['login'] = 'root'
        self.lxc11.agent['password'] = 'fortinet'
        self.lxc11.agent['ssh_key_file'] = ''
        self.lxc11.path='/home/cgustave/github/python/packages/checkitbaby/checkitbaby/tests/playbooks'
        self.lxc11.playbook='test'
        self.lxc11.run='1'
        self.lxc11.testcase=''
        self.lxc11.name='lxc11'
        self.lxc11.conn='1'
        self.lxc11.connect(type='lxc')

    def setup_lxc12(self):
        self.lxc12 = Lxc_agent(debug=True)
        self.lxc12.agent['ip'] = '192.168.122.178'
        self.lxc12.agent['port'] = '10102'
        self.lxc12.agent['login'] = 'root'
        self.lxc12.agent['password'] = 'fortinet'
        self.lxc12.agent['ssh_key_file'] = ''
        self.lxc12.path='/home/cgustave/github/python/packages/checkitbaby/checkitbaby/tests/playbooks'
        self.lxc12.playbook='test'
        self.lxc12.run='1'
        self.lxc12.testcase=''
        self.lxc12.name='lx12'
        self.lxc12.conn='1'
        self.lxc12.connect(type='lxc')

    def setup_lxc21(self):
        self.lxc21 = Lxc_agent(debug=True)
        self.lxc21.agent['ip'] = '192.168.122.178'
        self.lxc21.agent['port'] = '10103'
        self.lxc21.agent['login'] = 'root'
        self.lxc21.agent['password'] = 'fortinet'
        self.lxc21.agent['ssh_key_file'] = ''
        self.lxc21.path='/home/cgustave/github/python/packages/checkitbaby/checkitbaby/tests/playbooks'
        self.lxc21.playbook='test'
        self.lxc21.run='1'
        self.lxc21.testcase=''
        self.lxc21.name='lxc21'
        self.lxc21.conn='1'
        self.lxc21.connect(type='lxc')

    def setup_lxc22(self):
        self.lxc22 = Lxc_agent(debug=True)
        self.lxc22.agent['ip'] = '192.168.122.178'
        self.lxc22.agent['port'] = '10104'
        self.lxc22.agent['login'] = 'root'
        self.lxc22.agent['password'] = 'fortinet'
        self.lxc22.agent['ssh_key_file'] = ''
        self.lxc22.path='/home/cgustave/github/python/packages/checkitbaby/checkitbaby/tests/playbooks'
        self.lxc22.playbook='test'
        self.lxc22.run='1'
        self.lxc22.testcase=''
        self.lxc22.name='lxc22'
        self.lxc22.conn='1'
        self.lxc22.connect(type='lxc')


    # --- status ---
    #@unittest.skip
    def test_ping_self(self):
        self.setup_lxc11()
        result = self.lxc11.process(line="lxc11:1 ping [ping_test] 127.0.0.1\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_lx11_pings_lxc21(self):
        self.setup_lxc11()
        result = self.lxc11.process(line="lxc11:1 ping [ping_test] 10.0.2.21\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_lxc11_tcp_lxc21(self):
        self.setup_lxc11()
        self.setup_lxc21()
        result = self.lxc21.process(line="lxc21:1 open tcp 8000\n")
        self.assertTrue(result)
        result = self.lxc11.process(line="lxc11:1 connect tcp 10.0.2.21 8000\n")
        self.assertTrue(result)
        result = self.lxc11.process(line="lxc11:1 send \"alice\"\n")
        self.assertTrue(result)
        result = self.lxc21.process(line="lxc21:1 check [received] \"alice\"\n")
        self.assertTrue(result)
        result = self.lxc11.process(line="lxc11:1 close\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_multicast_join(self):
        self.setup_lxc22()
        result = self.lxc22.process(line="lxc22:1 join multicast eth1 226.94.1.1\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_multicast_leave(self):
        self.setup_lxc22()
        result = self.lxc22.process(line="lxc22:1 leave multicast eth1 226.94.1.1\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_multicast_listen(self):
        self.setup_lxc22()
        result = self.lxc22.process(line="lxc22:1 listen multicast 239.1.1.1 port 1000\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_multicast_send(self):
        self.setup_lxc12()
        result = self.lxc12.process(line="lxc12:1 send multicast 239.1.1.1 sport 1000 dport 11000 \"hello\"\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_multicast_full(self):
        self.setup_lxc12()
        self.setup_lxc22()
        self.lxc22.process(line="lxc22:1 join multicast eth1 239.1.1.1\n")
        self.lxc22.process(line="lxc22:1 listen multicast 239.1.1.1 port 5000\n")
        self.lxc12.process(line="lxc12:1 send multicast 239.1.1.1 sport 10000 dport 5000 \"hihihi\"\n")
        result = self.lxc22.process(line="lxc22:1 check [mctest] \"hihihi\"\n")
        self.assertTrue(result)
        self.lxc22.process(line="lxc22:1 leave multicast eth1 239.1.1.1\n")

if __name__ == '__main__':
    unittest.main()
