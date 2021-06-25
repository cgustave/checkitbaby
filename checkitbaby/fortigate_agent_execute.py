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
    Specific Fortigate agent execute functions loaded in FortiGate_agent
    """

    def process_execute(self, agent="", conn="1", type="", check="", command="", line=""):
        log.info("Enter with agent={} conn={} type={} check={} command={} line={} ".format(agent, conn, type, check, command, line))
        if command == 'ping':
            result = self.cmd_check_ping(type=type, check=check, line=line)
        else:
            log.error("Syntax error: command {} unknown".format(command))
            raise SystemExit
        return result

    def cmd_check_ping(self, type='', check='', line=''):
        """
        ping check accepted format
        ex : fgt1:1 check [ping_test] ping 192.168.0.254
        ex : fgt1:1 check [ping_test] ping vdom=root 192.168.0.254  (vdom option after ping word)
        ex : fgt1:1 check [ping_test] ping source=192.168.0.1 192.168.0.254 (source option)
        Note : transmited/received/drop packets added in report get={} section
        """
        log.info("Enter with type={} check={} line={}".format(type, check, line))
        result = False
        if not self.dryrun:
            self.connect_if_needed(stop_on_error=False)
        match = re.search('\s+ping\s+(?:source=[A-Za-z0-9_\.-]+)?\s?(?P<host>\S+)', line)
        if match:
            host = match.group('host')
            log.debug("found host={}".format(host))
        else:
            log.error("could not recognize ping command syntax line={}".format(line))
            raise SystemExit
        reference = self.random_string(length=8)
        if not self.dryrun:
            self._ssh.trace_mark(reference)
            maxround = self._ssh.ssh.maxround
            self._ssh.ssh.maxround = 90
            cmd_list = ["execute ping-options reset\n","execute ping-options adaptive-ping enable\n"]
            match_source = re.search ('source=(?P<source>[A-Za-z0-9_\.-]+)', line)
            if match_source:
                source = match_source.group('source')
                log.debug("source={}".format(source))
                cmd_list.append("execute ping-options source {}\n".format(source))
            for data in cmd_list:
                log.debug("data={}".format(data))
                self._ssh.ssh.shell_send([data])
            data = "execute ping "+host+"\n"
            self._ssh.ssh.shell_send([data])
            self._ssh.ssh.maxround = maxround
            sp = self.search_pattern_tracefile(mark=reference, pattern='packets transmitted')
            log.debug("sp={}".format(sp))
            if sp['result'] == True:
                log.debug("Found summary_line={}".format(sp['line']))
                match = re.search('(?P<transmit>\d+)\spackets\stransmitted,\s(?P<receive>\d+)\spackets\sreceived,\s(?P<drop>\d+)', sp['line'])
                if match:
                    transmit = match.group('transmit')
                    receive = match.group('receive')
                    drop = match.group('drop')
                    log.debug("transmit={} receive={} drop={}".format(transmit, receive, drop))
                    self.add_report_entry(data=check, result={'transmit': transmit, 'receive': receive, 'drop': drop})
                    if drop == '0':
                        log.debug("ping test passed (no drop)")
                        result = True
                    else:
                        log.debug("ping test failed with drops={}".format(drop))
                        result = False
                    self.add_report_entry(check=check, result=result)
                else:
                    log.warning("Can't extract ping result")
        return result
