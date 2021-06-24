# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2020
@author: cgustave
"""
import logging as log

# create logger
log.basicConfig(
    format='%(asctime)s,%(msecs)3.3d %(levelname)-8s[%(module)-10.10s.\
    %(funcName)-20.20s:%(lineno)5d] %(message)s',
    datefmt='%Y%m%d:%H:%M:%S',
    filename='debug.log',
    level=log.DEBUG)


class Mixin:
    """
    Specific Fortigate agent system functions loaded in FortiGate_agent
    """
    def process_system(self, agent="", conn="1", type="", command="", line=""):
        log.info("Enter with agent={} conn={} type={} command={} line={} ".format(agent, conn, type, command, line))
        if command == 'status':
            result = self.cmd_status(line=line, type=type)
        else:
            log.error("Syntax error: command {} unknown".format(command))
            raise SystemExit
        return result

    def cmd_status(self, type='', line=""):
        """
        get system status
        Records version and license in report
        check: returns True/False as per requirements
        get: returns True but add entries in report
        """
        log.info("Enter having _vdom={} dryrun={} with type={} line={}".format(self._vdom, self.dryrun, type, line))
        result = {}
        if not self.dryrun:
            self._connect_if_needed(stop_on_error=False)
            if self._vdom != '':
                self._cmd_enter_vdom(line=line)
            result = self._ssh.get_status()
            log.debug("result={}".format(result))
            self.add_report_entry(get='version', result=result['version'])
            self.add_report_entry(get='license', result=result['license'])
            if self._vdom != '':
                 self._cmd_leave_vdom(line=line)
            else:
                log.debug("no vdom")
        else:
            log.debug("dry-run")
        if type == 'get':
            return True
        if result:
            found_flag = True    # Without any further requirements, result is pass
        feedback = found_flag
        reqlist = self.get_requirements(line=line)
        for r in reqlist:
            log.debug("requirement: {}".format(r))
            rfdb = self.check_requirement(name=r['name'], value=r['value'], result=result)
            feedback = feedback and rfdb
            self.add_report_entry(check=r['name'], result=feedback)
        return feedback
