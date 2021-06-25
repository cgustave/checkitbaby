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
    Specific Fortigate agent sdwan functions loaded in FortiGate_agent
    """
    def process_sdwan(self, agent="", conn="1", type="", check="", command="", line=""):
        log.info("Enter with agent={} conn={} type={} check={} command={} line={} ".format(agent, conn, type, check, command, line))
        version = '6.4'
        if re.search('version=6.2', line):
            line = re.sub("version=6.2\s", '', line)
            version = '6.2'
        result = False
        if command == 'service' and type == 'check':
            result = self.cmd_check_sdwan(check=check, version=version, line=line)
        else:
            log.error("Syntax error: command {} unknown".format(command))
            raise SystemExit
        return result

    def cmd_check_sdwan(self, check="", version="", line=""):
        """
        Checks on sdwan feature
        - member selected from sdwan rule :

            FGT-B1-1 # diagnose sys virtual-wan-link service 1
			Service(1): Address Mode(IPV4) flags=0x0
			  Gen(1), TOS(0x0/0x0), Protocol(0: 1->65535), Mode(sla)
			  Service role: standalone
			  Member sub interface:
			  Members:
				1: Seq_num(1 vpn_isp1), alive, sla(0x1), cfg_order(0), cost(0), selected
				2: Seq_num(2 vpn_isp2), alive, sla(0x1), cfg_order(1), cost(0), selected
				3: Seq_num(3 vpn_mpls), alive, sla(0x1), cfg_order(2), cost(0), selected
			  Src address:
					10.0.1.0-10.0.1.255

			  Dst address:
					10.0.2.0-10.0.2.255

			FGT-B1-1 #

            - check alive members :
                ex : FGT-B1-1:1 check [sdwan_1_member1_alive] sdwan service 1 member 1 has status=alive
            - check sla value for a particular member
                ex : FGT-B1-1:1 check [sdwan_1_member1_sla] sdwan service 1 member 1 has sla=0x1
            - check preferred member
                ex : FGT-B1-1:1 check [sdwan_1_preferred] sdwan service 1 member 1 has preferred=1
            - vdom supported :
                ex : F1B2:1 check [sdwan_1_member1_alive] sdwan vdom=customer service 1 member 1 has status=alive
	    """
        log.info("Enter with check={} version={} line={}".format(check, version, line))
        found_flag = False

        line_no_requirement = line
        line_no_requirement = line.split('has')[0]
        log.debug("line_no_requirement={}".format(line_no_requirement))
        match_command = re.search("sdwan\s+service\s(?P<rule>\d+)\s+member\s+(?P<seq>\d+)", line_no_requirement)
        if match_command:
            rule = match_command.group('rule')
            seq = match_command.group('seq')
            log.debug("matched sdwan service rule={} member seq={}".format(rule, seq))
            self.connect_if_needed()
            result = self._ssh.get_sdwan_service(service=rule, version=version)
            if result:
                if len(result['members']) >= 1:
                    log.debug("At least 1 member was found")
                    found_flag = True
            feedback = found_flag
            reqlist = self.get_requirements(line=line)
            for r in reqlist:
                log.debug("requirement : {}".format(r))
                rfdb = self._check_sdwan_service_requirement(seq=seq, rname=r['name'], rvalue=r['value'], result=result)
                feedback = feedback and rfdb
        self.add_report_entry(check=check, result=feedback)
        self.add_report_entry(data=check, result=result)
        return feedback

    def _check_sdwan_service_requirement(self, seq='', result={}, rname='', rvalue=''):
        """
        Validates all requirements for sdwan service
        """
        log.info("Enter with seq={} rname={} rvalue={} result={}".format(seq, rname, rvalue, result))
        # if command failed, no members could be found => fail
        if result['members'] == {}:
            log.warning("could not retrieve sdwan members, return Fail")
            return False
        fb = True  # by default, requirement is met
        # Checking member is preferred
        # Extract seq from 1st member and see if its our
        if rname == 'preferred':
            if '1' in result['members']:
                pref_member_seq = result['members']['1']['seq_num']
                log.debug("Preferred member seq_num={}".format(pref_member_seq))
                if pref_member_seq == seq:
                    log.debug("requirement is fullfilled".format(rvalue))
                    fb = True
                else:
                    log.debug("requirement is not fullfilled")
                    fb = False
            else:
                log.error("No members found in 1st position")
                fb = False
        elif rname in ('status','sla'):
            log.debug("Accepted requirement rname={} checking member={} detail={}".format(rname, seq, result['members'][seq]))
            fb = self.check_requirement(result=result['members'][seq], name=rname, value=rvalue)
        else:
            log.error("unknown requirement")
            raise SystemExit
        log.debug("requirements verdict : {}".format(fb))
        return fb
