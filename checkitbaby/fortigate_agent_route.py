# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2020
@author: cgustave
"""
import logging as log
import re
# create logger
log.basicConfig(
    format='%(asctime)s,%(msecs)3.3d %(levelname)-8s[%(module)-10.10s.\
    %(funcName)-20.20s:%(lineno)5d] %(message)s',
    datefmt='%Y%m%d:%H:%M:%S',
    filename='debug.log',
    level=log.DEBUG)


class Mixin:
    """
    Specific Fortigate agent route functions loaded in FortiGate_agent
    """
    def process_route(self, agent="", conn="1", type="", check="", command="", line=""):
        log.info("Enter with agent={} conn={} type={} check={} command={} line={} ".format(agent, conn, type, check, command, line))
        if command == 'bgp':
            result = self.cmd_route(type=type, check=check, command=command, line=line)
        else:
            log.error("Syntax error: unknown command={}".format(command))
            raise SystemExit
        return result

    def cmd_route(self, type='', check='', command='', line=''):
        """
        Check command route distribution
        """
        log.info("Enter with type={} check={} command={} line={}".format(type, check, command, line))
        if command == 'bgp' and check != '':
            result = self.cmd_check_route_bgp(check=check, line=line)
        else:
            log.error("Unknown check route command")
            raise SystemExit
        return result

    def cmd_check_route_bgp(self, check="", line=""):
        """
        Checks on bgp routing table (from get router info routing-table bgp)
        - number of bgp routes is 4 :
            ex : FGT-B1-1:1 check [bgp_4_routes] bgp has total=4
        - bgp route for subnet 10.0.0.0/24 exist :
            ex : FGT-B1-1:1 check [bgp_subnet_10.0.0.0] bgp has subnet=10.0.0.0/24
        - bgp nexthop 10.255.1.253 exist
            ex : FGT-B1-1:1 check [bgp_nexthop_10.255.1.253] bgp has nexthop=10.255.1.253
        - bgp has route toward interface vpn_mpls
            ex : FGT-B1-1:1 check [bgp_subnet_10.0.0.0] bgp has interface=vpn_mpls
        - multiple requirements can be combined
            ... has nexthop=10.255.1.253 nexthop=10.255.2.253 subnet=10.0.0.0/24
        - allows vdom= statement, should be positioned after bgp keyword
        """
        log.info("Enter with check={} line={}".format(check, line))
        found_flag = False
        self.connect_if_needed()
        result = self._ssh.get_bgp_routes()
        log.debug("Found result={}".format(result))
        # See if at least one bgp route was found
        if result:
            if result['total'] >= 1:
                log.debug("At least 1 bgp route was found (total={})".format(result['total']))
                found_flag = True
        # Without any further requirements, result is pass
        feedback = found_flag
        # Processing further requirements (has ...)
        reqlist = self.get_requirements(line=line)
        for r in reqlist:
            log.debug("requirement: {}".format(r))
            rfdb = self._check_bgp_requirement(rname=r['name'], rvalue=r['value'], result=result)
            feedback = feedback and rfdb
        self.add_report_entry(check=check, result=feedback)
        self.add_report_entry(data=check, result=result)
        return feedback

    def _check_bgp_requirement(self, result={}, rname='', rvalue=''):
        """
        Validates bgp routes requirements, that is verifying if the 'has ...' part
        """
        log.info("Enter with rname={} rvalue={} result={}".format(rname, rvalue, result))
        fb = True  # by default, requirement is met
        if not 'subnet' in result:
            result['subnet'] = []
        if not 'nexthop' in result:
            result['nexthop'] = []
        if not 'interface' in result:
            result['interface'] = []
        if rname in ('total', 'recursive', 'subnet','nexthop','interface'):
            log.debug("requirement {}={} is known".format(rname, rvalue))
            if rname == 'total' :
                log.debug("Checking exact number of subnets : asked={} got={}".format(rvalue, result['total']))
                if str(result['total']) == str(rvalue):
                    log.debug("Total number of bgp routes is matching requirement")
                else:
                    log.debug("Total number of bgp routes does not match requirement")
                    fb = False
            elif rname == 'recursive' :
                log.debug("Checking exact number of recursive routes specifically : asked={} got={}".format(rvalue, result['recursive']))
                if str(result['recursive']) == str(rvalue):
                    log.debug("Total number of bgp recursive routes is matching requirement")
                else:
                    log.debug("Total number of bgp recursive routes does not match requirement")
                    fb = False
            elif result[rname].count(rvalue) > 0:
                log.debug("rname={} found : requirement is met".format(rname))
                fb = True
            else :
                log.debug("rname={} found : requirement is not met".format(rname))
                fb = False
        else:
           log.error("unknown bgp requirement {}={} is unknown".format(rname, rvalue))
           raise SystemExit
        log.debug("requirements verdict : {}".format(fb))
        return fb
