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
    Specific Fortigate agent multicast functions loaded in FortiGate_agent
    """
    def process_multicast(self, agent="", conn="1", type="", check="", command="", line=""):
        log.info("Enter with agent={} conn={} type={} check={} command={} line={} ".format(agent, conn, type, check, command, line))
        if command == 'groups' and type == 'check':
            result = self.cmd_check_multicast_igmp(check=check ,line=line)
        elif command == 'mroute' and type == 'check':
            result = self.cmd_check_multicast_mroute(check=check ,line=line)
        else:
            log.error("Syntax error: command {} unknown".format(command))
            raise SystemExit
        return result

    def cmd_check_multicast_igmp(self, check="", line=""):
        """
        Check igmp groups
        - group exists
          ex : FGT-B1-1 check [igmp_group] multicast igmp groups
        """
        log.info("Enter with check={} line={}".format(check, line))
        flag_found = False
        groups = []
        if not self.dryrun:
            cmd = "get router info multicast igmp groups\n"
            self._ssh.ssh.shell_send([cmd])
            for l in self._ssh.ssh.output.splitlines():
                match = re.search("^(?P<group>[0-9.]+)(\s|\t)+(?P<interface>\S+)(\s|\t)+(?P<uptime>\S+)(\s|\t)+(?P<expire>\S+)(\s|\t)+(?P<last_reporter>\S+)", l)
                if match:
                    flag_found = True
                    group = match.group('group')
                    interface = match.group('interface')
                    uptime = match.group('uptime')
                    expire = match.group('expire')
                    last_reporter = match.group('last_reporter')
                    log.debug("group={} interface={} uptime={} expire={} last_reporter={}".format(group, interface, uptime, expire, last_reporter))
                    groups.append({'group': group, 'interface': interface, 'uptime': uptime, 'expire': expire, 'last_reporter': last_reporter})
        # Processing further requirements (has ...)
        feedback = flag_found
        reqlist = self.get_requirements(line=line)
        for r in reqlist:
            log.debug("requirement: {}".format(r))
            rfdb = self.check_igmp_groups_requirement(name=r['name'], value=r['value'], groups=groups)
            feedback = feedback and rfdb
        self.add_report_entry(check=check, result=feedback)
        self.add_report_entry(data=check, result=groups)
        return feedback

    def cmd_check_multicast_mroute(self, check='', line=''):
        """
        Check multicast mroute
        Based on 'diag ip multicast mroute', ex :
        FGT-B2-9 (multicast) # diagnose ip multicast mroute
        grp=239.1.1.1 src=10.1.1.12 intf=8 flags=(0x10000000)[  ] status=resolved
                last_assert=1410655 bytes=76 pkt=2 wrong_if=0 num_ifs=1
                index(ttl)=[9(1),]

        FGT-B2-9 (multicast) #
        """
        log.info("Enter with check={} line={}".format(check, line))
        flag_found = False
        mroutes = []
        if not self.dryrun:
            cmd = "diagnose ip multicast mroute\n"
            self._ssh.ssh.shell_send([cmd])
            for l in self._ssh.ssh.output.splitlines():
                log.debug("l={}".format(l))
                match = re.search("^grp=(?P<grp>[0-9.]+)(\s|\t)+src=(?P<src>[0-9.]+)(\s|\t)+intf=(?P<intf>\d+)",l )
                if match:
                    flag_found = True
                    grp = match.group('grp')
                    src = match.group('src')
                    intf=match.group('intf')
                    log.debug("grp={} src={} intf={}".format(grp, src, intf))
                    mroutes.append({'grp': grp, 'src': src, 'intf': intf})

        # Processing further requirements (has ...)
        self.add_report_entry(data=check, result=mroutes)
        feedback = flag_found
        return feedback



    def check_igmp_groups_requirement(self, name='', value='', groups=[]):
        """
        checks requirements for muticast igmp groups
        has group=239.0.0.1
        """
        feedback = False
        log.info("Enter with name={} value={}, groups={}".format(name, value, groups))
        for g in groups:
            if name == 'group':
                log.debug("Checking group is known")
                if g['group'] == value:
                    log.debug("found group {}".format(value))
                    feedback = True
        return feedback
