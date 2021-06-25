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
    Specific Fortigate agent session functions loaded in FortiGate_agent
    """
    def process_session(self, agent="", conn="1", type="", check="", command="", line=""):
        log.info("Enter with agent={} conn={} type={} check={} command={} line={} ".format(agent, conn, type, check, command, line))
        if command == 'filter' and type == 'check':
            result = self._cmd_check_session(check=check ,line=line)
        else:
            log.error("Syntax error: command {} unknown".format(command))
            raise SystemExit
        return result

    def _cmd_check_session(self, check="", line=""):
        """
        Checks on fortigate session :
        - session exist
          ex : FGT-B1-1:1 check [ssh_session_exist] session filter dport=22 dest=192.168.0.1
        - session has flag 'dirty'
          ex : FGT-B1-1:1 check [session_is_dirty] session filter dport=5000 has flag=dirty

        - allows vdom selection (should be positioned after keyword session
          ex : F1B2:1 check [ssh_session] session vdom=customer filter dport=22
        """
        log.info("Enter with check={} line={}".format(check, line))
        found_flag = False
        # Prepare session filter
        session_filter = {}
        # remove requirements from line (after 'has ...')
        line_no_requirement = line
        line_no_requirement = line.split('has')[0]
        log.debug("line_no_requirement={}".format(line_no_requirement))
        match_command = re.search("session\s+filter\s+(?P<filters>.*)(?:\s+has\s+)?",line_no_requirement)
        if match_command:
            filters = match_command.group('filters')
            log.debug("filters={}".format(filters))
            for f in filters.split():
                log.debug("filter: {}".format(f))
                match_filter = re.search("^(?P<fname>.+)=(?P<fvalue>.+)", f)
                if match_filter:
                    fname = match_filter.group('fname')
                    fvalue = match_filter.group('fvalue')
                    log.debug("Adding filter : fname={} fvalue={}".format(fname, fvalue))
                    session_filter[fname]=fvalue
        log.debug("Prepared session_filter={}".format(session_filter))
        # Connect to agent if not already connected
        self.connect_if_needed()
        # Query for session
        result = self._ssh.get_session(filter=session_filter)
        log.debug("Found result={}".format(result))
        # See if at least one session was found
        if result:
            if result['total'] == '1':
                log.debug("1 session was found")
                found_flag = True
            if result['total'] == '0':
                log.warning("no session foud")
                found_flag = False
            else:
                log.warning("Multiple sessions found num={}".format(result['total']))
                found_flag = True
        # Without any further requirements, result is pass
        feedback = found_flag
        # Processing further requirements (has ...)
        reqlist = self.get_requirements(line=line)
        for r in reqlist:
            log.debug("requirement: {}".format(r))
            rfdb = self._check_session_requirement(name=r['name'], value=r['value'], result=result)
            feedback = feedback and rfdb
        self.add_report_entry(check=check, result=feedback)
        self.add_report_entry(data=check, result=result)
        return feedback

    def _check_session_requirement(self, result={}, name='', value=''):
        """
        Validates session requirements, that is verifying if the 'has ...' part
        of the scenario line has all its requirements set.
        A list of requirement are described as key=value pairs seperated by
        spaces all after keyworl 'has ...'
        Handling may be different based on the requirement type :
        - session state : search in the 'state' list of result dict
        - Other requirement keys should have the same key as the session result key
        Prerequisite : one session should have been selected so result dict
        contains all its details

        state : should be search in session 'state' dict
        Returns : True if requirements are met, false otherwise
        """
        log.info("Enter with name={} value={} result={}".format(name, value, result))
        fb = True  # by default, requirement is met
        # Dealing with state
        log.debug("result={}".format(result))
        if not 'state' in result:
            result['state'] = []
        if name == 'state' :
            log.debug("Checking state '{}' is set on the session".format(value))
            if result['state'].count(value) > 0:
                log.debug("state {} is set".format(name))
            else :
                log.debug("state {} is not set, requirement is not met".format(value))
                fb = False
        elif name in ('src','dst','sport','dport','proto','proto_state','duration','expire','timeout','dev','gwy','total'):
            log.debug("Accepted requirement rname={}".format(name))
            fb = self.check_requirement(result=result, name=name, value=value)
        else:
            log.error("unknown session requirement {}={}".format(name, value))
            raise SystemExit
        log.debug("requirements verdict : {}".format(fb))
        return fb
