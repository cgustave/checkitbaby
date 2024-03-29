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
from lxc_agent import Lxc_agent

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
        self.fgt.agent['port'] = '10106'
        self.fgt.agent['login'] = 'admin'
        self.fgt.agent['password'] = ''
        self.fgt.agent['ssh_key_file'] = ''
        # Feed agent with information it needs for its job
        self.fgt.path='/home/cgustave/github/python/packages/checkitbaby/checkitbaby/tests/playbooks'
        self.fgt.playbook='test'
        self.fgt.run='1'
        self.fgt.testcase=''
        self.fgt.name='fgt1'
        self.fgt.conn='0'
        self.fgt.connect(type='fortigate')


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
        self.lxc12.name='lxc12'
        self.lxc12.conn='1'
        self.lxc12.connect(type='lxc')


    # --- status ---

    #@unittest.skip
    def test_get_status(self):
        result = self.fgt.process(line="FGT-B1-1:1 get system status\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_check_status_no_requirement(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [fgt_status] system status\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_check_status_has_license(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [fgt_status] system status has license=True\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_check_status_has_version(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [fgt_status] system status has version=v6.4.6,build1879,210520\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_check_status_has_license_and_version(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [fgt_status] system status has version=v6.4.6,build1879,210520 license=True\n")
        self.assertTrue(result)

    # --- sessions ---

    #@unittest.skip
    def test_session_dport_22(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [session_ssh] session vdom=root filter dport=22\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_session_dport_dst(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [session_ssh] session vdom=root filter dport=22 dst=192.168.0.1\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_session_dport_has_state_local(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [session_ssh] session vdom=root filter dport=22 has state=local\n")
        self.assertTrue(result)

    # --- ping ---

    #@unittest.skip
    def test_ping_ok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [ping_test] execute ping vdom=root 192.168.0.254\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_ping_source_ok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [ping_test] execute ping vdom=root source=192.2.0.1 192.2.0.2\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_ping_nok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [ping_test] execute ping vdom=root 169.255.1.2\n")
        self.assertFalse(result)

    # --- IPsec ----

    #@unittest.skip
    def test_ike_status(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [ipsec] ipsec ike status vdom=root\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_ike_status_with_requirements(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [ipsec] ipsec ike status vdom=root has ipsec_created=3 ipsec_established=1\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_ike_gateway_flush(self):
        result = self.fgt.process(line="FGT-B1-1:1 flush vdom=root ipsec ike gateway\n")
        self.assertTrue(result)

    # --- BGP routes ---

    #@unittest.skip
    def test_route_bgp(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [route_bgp] route bgp vdom=root\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_route_bpg_has_total_2_ok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [route_bgp] route bgp vdom=root has total=4\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_route_bpg_has_total_3_nok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [route_bgp] route bgp vdom=root has total=3\n")
        self.assertFalse(result)

    #@unittest.skip
    def test_route_bgp_has_subnet_ok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [route_bgp] route bgp vdom=root has subnet=10.0.0.0/24\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_route_bgp_has_subnet_nok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [route_bgp] route bgp vdom=root has subnet=11.2.3.0/24\n")
        self.assertFalse(result)

    #@unittest.skip
    def test_route_bgp_has_nexthop_ok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [route_bgp] route bgp vdom=root has nexthop=10.255.1.253\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_route_bgp_has_nexthop_nok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [route_bgp] route bgp vdom=root has nexthop=10.10.40.22\n")
        self.assertFalse(result)

    #@unittest.skip
    def test_route_bgp_has_interface_ok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [route_bgp] route bgp vdom=root has interface=vpn_isp1\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_route_bgp_has_interface_nok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [route_bgp] route bgp vdom=root has interface=vpn_isp9\n")
        self.assertFalse(result)

    #@unittest.skip
    def test_multi_statement_ok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [route_bgp] route bgp vdom=root has subnet=10.0.0.0/24 nexthop=10.255.1.253 interface=vpn_isp1\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_multi_statement_nok(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [route_bgp] route bgp vdom=root has subnet=14.3.2.0/24 nexthop=10.255.1.253 interface=vpn_isp1\n")
        self.assertFalse(result)

    # --- SD-Wan ---

    #@unittest.skip
    def test_sdwan_service(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [sdwan] sdwan vdom=root service 1 member 1\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_sdwan_service_requirement_preferred(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [sdwan] sdwan vdom=root service 1 member 1 has preferred=1\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_sdwan_service_requirement_status(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [sdwan] sdwan vdom=root service 1 member 1 has status=alive\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_sdwan_service_requirement_sla(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [sdwan] sdwan vdom=root service 1 member 1 has sla=0x1\n")
        self.assertTrue(result)

    #@unittest.skip
    def test_sdwan_service_v62(self):
        # 6.2 should use "diag sys virtual-wan-link and cause an error on 6.4"
        result = self.fgt.process(line="FGT-B1-1:1 check [sdwan] sdwan vdom=root service 1 member 1 version=6.2 has sla=0x1\n")
        self.assertFalse(result)

    # --- Multicast ---

    #@unittest.skip
    def test_multicast_igmp_group_join_ok(self):
        # The following test requires LXC12 up and running
        self.setup_lxc12()
        self.lxc12.cmd_multicast_group(action='join', group='239.0.0.1', dev='eth1')
        result = self.fgt.process(line="FGT-B1-1:1 check [igmp_join] multicast vdom=multicast groups\n")
        self.lxc12.cmd_multicast_group(action='leave', group='239.0.0.1', dev='eth1')
        self.assertTrue(result)

    #@unittest.skip
    def test_multicast_igmp_group_join_requirements_ok(self):
        """Requires LXC12 up and running"""
        self.setup_lxc12()
        self.lxc12.cmd_multicast_group(action='join', group='239.0.0.1', dev='eth1')
        result = self.fgt.process(line="FGT-B1-1:1 check [igmp_join] multicast vdom=multicast groups has group=239.0.0.1\n")
        self.assertTrue(result)
        result = self.fgt.process(line="FGT-B1-1:1 check [igmp_join] multicast vdom=multicast groups has group=242.0.0.1\n")
        self.assertFalse(result)
        self.lxc12.cmd_multicast_group(action='leave', group='239.0.0.1', dev='eth1')

    #@unittest.skip
    def test_multicast_igmp_group_no_group_fails(self):
        result = self.fgt.process(line="FGT-B1-1:1 check [igmp_join] multicast vdom=multicast groups\n")
        self.assertFalse(result)

    #@unittest.skip
    def test_multicast_mroute_ok(self):
        """
        Checking on FHR, no need join, just push multicast traffic
        Requires lxc12 up and running
        """
        self.setup_lxc12()
        self.lxc12.cmd_multicast_send(group='239.1.1.1', sport=10000, dport=5000, message='hello')
        result = self.fgt.process(line="FGT-B1-1:1 check [mroute] multicast vdom=multicast mroute\n")
        self.assertFalse(result)

    # --- BFD ---

    #@unittest.skip
    def test_bfd_neighbor_ok(self):
        result = self.fgt.process(line='FGT-B1-1:1 check [bfd_neighbors] bfd vdom=bfd neighbor 172.18.1.9\n')
        self.assertTrue(result)

    #@unittest.skip
    def test_bfd_neighbor_state_ok(self):
        result = self.fgt.process(line='FGT-B1-1:1 check [bfd_neighbors] bfd vdom=bfd neighbor 172.18.1.9 has state=up\n')
        self.assertTrue(result)

    # --- HA ---

    #@unittest.skip
    def test_ha_status_no_requirement(self):
        result = self.fgt.process(line='FGT-B1-1:1 check [ha_health] ha status\n')
        self.assertTrue(result)

    #@unittest.skip
    def test_ha_status_requirement_health_ok(self):
        result = self.fgt.process(line='FGT-B1-1:1 check [ha_health] ha status has health=ok\n')
        self.assertTrue(result)

    #@unittest.skip
    def test_ha_status_requirement_master_ok(self):
        result = self.fgt.process(line='FGT-B1-1:1 check [ha_is_master] ha status has master=FGT-B1-1\n')
        self.assertTrue(result)

    #@unittest.skip
    def test_ha_status_requirement_slave_ok(self):
        result = self.fgt.process(line='FGT-B1-1:1 check [ha_is_slave] ha status has slave=FGT-B1-2\n')
        self.assertTrue(result)

    #@unittest.skip
    def test_ha_status_requirement_nb_ok(self):
        result = self.fgt.process(line='FGT-B1-1:1 check [ha_nb] ha status has nb=2\n')
        self.assertTrue(result)

    #@unittest.skip
    def test_ha_status_requirement_confsync_ok(self):
        result = self.fgt.process(line='FGT-B1-1:1 check [ha_nb] ha status has config=synchronized\n')
        self.assertTrue(result)

    #@unittest.skip
    def test_ha_status_requirement_serial_ok(self):
        result = self.fgt.process(line='FGT-B1-1:1 check [ha_nb] ha status has serial=FGVM08TM20005010 serial=FGVM08TM20005011\n')
        self.assertTrue(result)

    #@unittest.skip
    def test_ha_status_multi_requirement_ok(self):
        result = self.fgt.process(line='FGT-B1-1:1 check [ha_nb] ha status has master=FGT-B1-1 slave=FGT-B1-2 nb=2 config=synchronized serial=FGVM08TM20005010 serial=FGVM08TM20005011 health=ok\n')
        self.assertTrue(result)

    #@unittest.skip
    def test_ha_reset_uptime(self):
        result = self.fgt.process(line='FGT-B1-1:1 ha reset-uptime\n')
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
