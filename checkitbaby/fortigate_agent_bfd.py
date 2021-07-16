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
    Specific Fortigate agent bfd functions loaded in FortiGate_agent
    """
    def process_bfd(self, agent="", conn="1", type="", check="", command="", line=""):
        log.info("Enter with agent={} conn={} type={} check={} command={} line={} ".format(agent, conn, type, check, command, line))
        if command == 'neighbor':
            result = self.cmd_bfd_neighbor(type=type, check=check, command=command, line=line)
        else:
            log.error("Syntax error: unknown command={}".format(command))
            raise SystemExit
        return result

    def cmd_bfd_neighbor(self, type='', check='', command='', line=''):
        """
        Check bfd commands
        """
        log.info("Enter with type={} check={} command={} line={}".format(type, check, command, line))
        state = 'unknown'
        feedback = False
        neighbor = ''
        match_neighbor = re.search("\sneighbor(\s|\t)+(?P<neighbor>[0-9.]+)", line)
        if match_neighbor:
            neighbor = match_neighbor.group('neighbor')
            log.debug('neighbor={}'. format(neighbor))
        else:
            log.error("Syntax error: could not find a neighbor ip in line={}".format(line))
            raise SystemExit
        if check != '':
            flag_found = False
            if not self.dryrun:
                cmd = "get router info bfd neighbor \n"
                self._ssh.ssh.shell_send([cmd])
                for l in self._ssh.ssh.output.splitlines():
                    match = re.search("^(?P<ourAddress>[0-9.]+)(\s|\t)+(?P<neighAddress>[0-9.]+)(\s|\t)+(?P<state>\S+)(\s|\t)", l)
                    if match:
                        flag_found = True
                        ourAddress = match.group('ourAddress')
                        neighAddress = match.group('neighAddress')
                        state = match.group('state')
                        log.debug("neighbor={} state={}".format(neighAddress, state))
            feedback = flag_found
            reqlist = self.get_requirements(line=line)
            for r in reqlist:
                log.debug("requirement: {}".format(r))
                rfdb = self.check_bfd_neighbor_requirement(name=r['name'], value=r['value'], neighbor=neighbor, state=state)
                feedback = feedback and rfdb
            self.add_report_entry(check=check, result=feedback)
            self.add_report_entry(data=check, result=state)
        else:
            log.error("Unknown bfd neighbor command")
            raise SystemExit
        return feedback


    def check_bfd_neighbor_requirement(self, name, value, neighbor, state):
        """
        Check bfd neighbor requirements
        # returns True if the given neighbor is found (in whichever state)
        FGT-B1-1:1 check [bfd_neighbors] bfd vdom=bfd neighbor 172.18.1.9 has state=UP
        """
        feedback = False
        log.info("Enter with name={} value={}, neighbor={} state={}".format(name, value, neighbor, state))
        if name == 'state':
            log.debug("Checking state for neighbor {}".format(neighbor))
            if value.lower() == state.lower():
                log.debug("state requirement OK")
                feedback = True
            else:
                log.debug("state is different")
        return feedback
