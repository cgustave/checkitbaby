# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2019
@author: cgustave
"""
import logging as log
from agent import Agent
import re

class Fortigate_agent(Agent):
    """
    Fortigate agent
    To avoid ssh connection issues because of key change, it is recommended
    to use an ssh key to connect to FortiGate
    Commands :
      get version
        ex : FGT-1:1 get version
      check [policy_flag] session filter dport 22 has flag may_dirty
    """

    def __init__(self, name='', conn=0, dryrun=False, debug=False):
        """
        Constructor
        """
        # create logger
        log.basicConfig(
              format='%(asctime)s,%(msecs)3.3d %(levelname)-8s[%(module)-\
              10.10s.%(funcName)-20.20s:%(lineno)5d] %(message)s',
              datefmt='%Y%m%d:%H:%M:%S',
              filename='debug.log',
              level=log.NOTSET)
        # Set debug level first

        if debug:
            self.debug = True
            log.basicConfig(level='DEBUG')

        log.info("Constructor with name={} conn={} dryrun={} debug={}".format(name, conn, dryrun, debug))

        # Attributs set in init
        self.name = name
        self.conn = conn
        self.dryrun = dryrun

        # Attributs to be set before processing
        self.path = None
        self.playbook = None
        self.run = None
        self.agent = None        # name, id ... and all info for the agent itself
        self.testcase = None     # For which testcase id the agent was created
        self.report = None       # Testcase report (provided from Workbook)

        # Private attributs
        self._connected = False  # ssh connection state with the agent
        self._ssh = None         # Will be instanciated with type Vyos

    def __del__(self):
        """
        Desctructor to close opened connection to agent when exiting
        """
        log.info("Enter this")
        if self._ssh:
            self._ssh.close()

    def process(self, line=""):
        """
        FortiGate specific processing
        list of commands :
        """
        log.info("Enter with line={}".format(line))
        match = re.search("(?:(\s|\t)*[A-Za-z0-9\-_]+:\d+(\s|\t)+)(?P<command>[A-Za-z-]+)",line)

        if match:
            command = match.group('command')
            log.debug("Matched with command={}".format(command))
        else:
            log.debug("No command has matched")

        if command == 'get':
            self.cmd_get(line)
        elif command == 'check':
             self.cmd_check(line) 
        else:
            log.warning("command {} is unknown".format(command))

    def cmd_get(self, line=""):
        """
        Process get commands
        """
        log.info("Enter with line={}".format(line))

        # Connect to agent if not already connected
        if not self._connected:
            log.debug("Connection to agent needed agent={} conn={}".format(self.name, self.conn))
            self.connect(type='fortigate')

        match_version = re.search("get\sversion", line)
        if match_version:
             if not self.dryrun:
                 version = self._ssh.get_version()
                 self.add_report_entry(get='version', result=version) 
             else:
                 log.debug("dry-run")
        else:
            log.error("unknown get command")
            raise SystemExit


    def cmd_check(self, line=""):
        """
        Process check commands
        """
        log.info("Enter with line={}".format(line))
 
        match_command = re.search("check(\s|\t)+\[(?P<name>.+)\](\s|\t)+(?P<command>\w+)\s",line)
        if match_command:
          name =  match_command.group('name')
          command = match_command.group('command')
          if command == 'session':
              self._cmd_check_session(name=name, line=line)
          else:
              log.error("Unknown check command {}".format(command))
              raise SystemExit
        else:
           log.error("Could not understand check command syntax")
           raise SystemExit
 

    def _cmd_check_session(self, name="", line=""):
        """
        Checks on fortigate session :
        - session exist
          ex : FGT-B1-1 check [ssh_session_exist] session filter dport=22 dest=192.168.0.
        - session has flag 'dirty'
          ex : FGT-B1-1 check [session_is_dirty] session filter dport=5000 has flag=dirty
        """
        log.info("Enter with name={} line={}".format(name, line))
      
        found_flag = False
 
        # Prepare session filter
        session_filter = {} 
        # TBD : has matches as a session filter - to be fixed
        match_command = re.search("session\s+filter\s+(?P<filters>.*)(?:\s+has\s+)?",line)
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
        if not self._connected:
            log.debug("Connection to agent needed agent={} conn={}".format(self.name, self.conn))
            self.connect(type='fortigate')
        
        # Query for session    
        result = self._ssh.get_session(filter=session_filter)
        log.debug("Found result={}".format(result))

        # See if at least one session was found
        if result:
            if result['total'] == 1:
                log.debug("1 session was found")
                found_flag = True
            else:
                log.warning("number of sessions found {}".format(result['total']))
                found_flag = True

        # Without any further requirements, result is pass
        feedback = found_flag

        # Processing further requirements (has ...)
        match_has = re.search("\s+has\s+(?P<requirements>\S+)",line)
        if match_has:
            requirements = match_has.group('requirements')
            log.debug("requirements list: {}".format(requirements))
            for r in requirements.split():
                log.debug("requirement: {}".format(r))
                match_req = re.search("^(?P<rname>.+)=(?P<rvalue>.+)", r)
                if match_req:
                    rname = match_req.group('rname')
                    rvalue = match_req.group('rvalue')
                    log.debug("Checking requirement {}:{}".format(rname, rvalue))
                    rfdb = self._check_session_requirement(rname=rname, rvalue=rvalue, result=result)
                    feedback = feedback and rfdb
         
        self.add_report_entry(check=name, result=feedback)
        return feedback

    def _check_session_requirement(self, result={}, rname='', rvalue=''):
        """
        Validates session requirements.
        Handling may be different based on the requirement type
        state : should be search in session 'state' dict
        """
        log.info("Enter with rname={} rvalue={} result={}".format(rname, rvalue, result))
        
        fb = True  # by default, requirement is met

        # Dealing with state
        if rname == 'state':
            log.debug("Checking state '{}' is set on the session".format(rvalue))
            if result['state'].count(rvalue) > 0:
                log.debug("state {} is set".format(rname))
            else :
                log.debug("state {} is not set, requirement is not met".format(rvalue))
                fb = False
        else:
            log.error("unknown session requirement {}={}".format(rname, rvalue))
            raise SystemExit
       
        log.debug("requirements verdict : {}".format(fb))
        return fb
        
 
 
if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_testrunner.py\n")

     


