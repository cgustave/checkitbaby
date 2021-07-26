# -*- coding: utf-8 -*-
"""
Created on July 26, 2021
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
    Specific Fortigate agent ha functions loaded in FortiGate_agent
    """
    def process_ha(self, agent="", conn="1", type="", check="", command="", line=""):
        log.info("Enter with agent={} conn={} type={} check={} command={} line={} ".format(agent, conn, type, check, command, line))
        if command == 'status':
            result = self.cmd_ha_status(type=type, check=check, command=command, line=line)
        elif command == 'reset-uptime':
            result = self.cmd_ha_reset_uptime()
        else:
            log.error("Syntax error: unknown command={}".format(command))
            raise SystemExit
        return result

    def cmd_ha_reset_uptime(self):
        """
        Reset ha-uptime using command "diagnose sys ha reset-uptime"
        """
        log.info("\* Enter")
        feedback = True
        if not self.dryrun:
            cmd = "diagnose sys ha reset-uptime\n"
            self._ssh.ssh.shell_send([cmd])
            for l in self._ssh.ssh.output.splitlines():
                if re.search("Command fail", l):
                    log.warning("Command failed")
                    feedback = False ;
                log.debug("line={}".format(l))
        return feedback

    def cmd_ha_status(self, type='', check='', command='', line=''):
        """
        Check ha commands
        if no requirement, return True  if seeing 'Cluster Uptime line'
        Note : format of the command has changed (6.2: Master/slave, 6.4:Primary/Secondary)
        """
        log.info("Enter with type={} check={} command={} line={}".format(type, check, command, line))
        result = {}
        nbdev = 0
        flag_config = False # Flag to tell if we are in "Configuration Status: section"
        flag_insync = True
        if check != '':
            flag_found = False
            if not self.dryrun:
                cmd = "get system ha status\n"
                self._ssh.ssh.shell_send([cmd])
                for l in self._ssh.ssh.output.splitlines():
                    # Uptime
                    match_uptime = re.search("^Cluster\sUptime:\s(?P<nbdays>\d+)\sdays\s(?P<hms>\S+)", l)
                    if match_uptime:
                        uptime = match_uptime.group('nbdays')+" days "+match_uptime.group('hms')
                        log.debug("Found uptime={}".format(uptime))
                        result['uptime'] = uptime
                        flag_found = True
                    # health
                    match_health = re.search("^HA Health Status: (?P<health>\S+)", l)
                    if match_health:
                        health = match_health.group('health')
                        log.debug("Found health={}".format(health))
                        result['health'] = health
                    # master
                    match_master = re.search("^((Primary\s+:)|(Master:))\s+(?P<master>\S+)", l)
                    if match_master:
                        master = match_master.group('master')
                        nbdev = nbdev + 1
                        log.debug("Found master={}, nbdev={}".format(master, nbdev))
                        result['master'] = master
                    # slave (may have more than one Slave line)
                    match_slave = re.search("^((Secondary\s+:)|(Slave\s+:))\s(?P<slave>\S+)", l)
                    if match_slave:
                        slave = match_slave.group('slave')
                        nbdev = nbdev + 1
                        log.debug("Found slave={}, nbdev={}".format(slave, nbdev))
                        if 'slaves' not in result:
                            result['slaves'] = []
                        result['slaves'].append(slave)
                    # Set flag_config
                    if flag_config and re.search("^System Usage stats:", l):
                        log.debug("End of Configuration Status")
                        flag_config = False
                    if flag_config:
                        if not re.search("\sin-sync", l):
                            log.debug("One device is not in sync in line={}".format(l))
                            flag_insync = False
                        else:
                            log.debug("Found a device in-sync")
                            match_serial = re.search("\s+(?P<serial>[A-Z0-9-_]+)", l)
                            if match_serial:
                                serial = match_serial.group('serial')
                                log.debug("Found device serial={}".format(serial))
                                if 'serials' not in result:
                                    result['serials'] = []
                                result['serials'].append(serial)

                    if re.search("^Configuration Status:", l):
                        log.debug("Start of Configuration Status")
                        flag_config = True

            result['nb'] = nbdev
            result['sync'] = flag_insync
            feedback = flag_found
            reqlist = self.get_requirements(line=line)
            for r in reqlist:
                log.debug("feedback so far={} requirement: {}".format(feedback, r))
                rfdb = self.check_ha_status_requirement(name=r['name'], value=r['value'], result=result, line=line)
                feedback = feedback and rfdb
            self.add_report_entry(check=check, result=feedback)
            self.add_report_entry(data=check, result=result)
        else:
            log.error("Unknown ha command")
            raise SystemExit
        return feedback


    def check_ha_status_requirement(self, name, value, result, line):
        """
        Check ha status requirements
        """
        feedback = False
        log.info("Enter with name={} value={}, result={} line={}".format(name, value, result, line))
        if name == 'health':
             log.debug("Checking health")
             if value.lower() == result['health'].lower():
                 log.debug("health requirement OK")
                 feedback = True
             else:
                 log.debug("health is not ok")
        elif name == 'master':
            log.debug("Checking master")
            if value.lower() == result['master'].lower():
                log.debug("master requirement OK")
                feedback = True
            else:
                log.debug("master is not ok")
        elif name == 'slave':
            log.debug("Checking slave")
            if value in result['slaves']:
                log.debug("slave {} is known".format(value))
                feedback = True
        elif name == 'nb':
            log.debug("Checking nb")
            if str(value) == str(result['nb']):
                log.debug("nb requirement met")
                feedback = True
        elif name == 'config':
            log.debug("Checking config sync")
            if (value != 'synchronized'):
                log.error("Syntax error in line={} : requirement value for config can only be synchronized")
                raise SystemExit
            if result['sync']:
                log.debug("config sync requirement is met")
                feedback = True
        elif name == 'serial':
            log.debug("Checking serial")
            if value in result['serials']:
                log.debug("serial {} is known".format(value))
                feedback = True
        else:
            log.error("Syntax error : Unexpected ha requirement in line={}".format(line))
            raise SystemExit
        return feedback
