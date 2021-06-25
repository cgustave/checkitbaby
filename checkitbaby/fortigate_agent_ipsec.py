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
    Specific Fortigate agent ipsec functions loaded in FortiGate_agent
    """
    def process_ipsec(self, agent="", conn="1", type="", check="", command="", line=""):
        log.info("Enter with agent={} conn={} type={} check={} command={} line={} ".format(agent, conn, type, check, command, line))
        if command == 'ike' and type == 'check':
            result = self.cmd_ike(check=check ,line=line)
        elif command == 'ike' and type == 'flush':
            result = self.cmd_ike_flush(line=line)
        else:
            log.error("Syntax error: command {} unknown".format(command))
            raise SystemExit
        return result

    def cmd_ike(self, check="", line=""):
        """
        Dispatcher for ike commands
        """
        log.info("Enter with check={} line={}".format(check, line))
        match = re.search('ipsec\s+ike\s', line)
        if match:
            result = self.cmd_ike_status(check=check, line=line)
        else:
            log.error("Syntax error: unknown ipsec command from line={}".format(line))
            raise SystemExit
        return result

    def cmd_ike_status(self, check="", line=""):
        """
        ike status:
        Checks on IPsec ike status (from 'diagnose vpn ike status'), examples:
          FGT-B1-1:1 check [B1_tunnels] ike status has ike_created=3
          FGT-B1-1:1 check [B1_tunnels] ike status has ike_created=3 ike_established=3
          FGT-B1-1:1 check [B1_tunnels] ike status has ipsec_created=3 ipsec_established=3
        """
        log.info("Enter with check={} line={}".format(check, line))
        found_flag = False
        self.connect_if_needed(stop_on_error=False)
        result = self._ssh.get_ike_and_ipsec_sa_number()
        if result:
            found_flag = True
            # Without any further requirements, result is pass
            feedback = found_flag
            # Processing further requirements (has ...)
            reqlist = self.get_requirements(line=line)
            for r in reqlist:
                log.debug("Checking requirement {}={}".format(r['name'], r['value']))
                if r['name'] == 'ike_created':
                    rfdb = self.check_requirement(name='created', value=r['value'], result=result['ike'])
                elif r['name'] == 'ike_established':
                    rfdb = self.check_requirement(name='established', value=r['value'], result=result['ike'])
                elif r['name'] == 'ipsec_created':
                    rfdb = self.check_requirement(name='created', value=r['value'], result=result['ipsec'])
                elif r['name'] == 'ipsec_established':
                    rfdb = self.check_requirement(name='established', value=r['value'], result=result['ike'])
                else:
                    log.error("unrecognized requirement")
                    raise SystemExit
                feedback = feedback and rfdb
            self.add_report_entry(check=check, result=feedback)
            self.add_report_entry(data=check, result=result)
            return found_flag

    def cmd_ike_flush(self, line=""):
        """
        Process flush command:
          - flush ike gateway
        """
        log.info("Enter with line={}".format(line))
        self.connect_if_needed()
        result = self._ssh.cli(commands=['diagnose vpn ike gateway flush'])
        return True
