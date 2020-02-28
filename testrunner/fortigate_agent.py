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
        log.info("Enter")
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
            success = self.connect(type='fortigate')
        
            if not success:
                log.error("Could not connect to FortiGate. Won't get information, continue scenario.")
                return False

        # get version
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
        Check commands distribution to specific handling
        """
        log.info("Enter with line={}".format(line))
 
        match_command = re.search("check(\s|\t)+\[(?P<name>.+)\](\s|\t)+(?P<command>\w+)",line)
        if match_command:
          name =  match_command.group('name')
          command = match_command.group('command')
          if command == 'session':
              self._cmd_check_session(name=name, line=line)
          elif command == 'bgp':
              self._cmd_check_bgp(name=name, line=line)
          else:
              log.error("Unknown check command '{}' for test named {}".format(command, name))
              raise SystemExit
        else:
           log.error("Could not understand check command syntax")
           raise SystemExit

    def _cmd_check_bgp(self, name="", line=""):
        """
        Checks on bgp routing table (from get router info routing-table bgp)
        - number of bgp routes is 4 :
          ex : FGT-B1-1 check [bgp_4_routes] bgp has total=4
        - bgp route for subnet 10.0.0.0/24 exist :
          ex : FGT-B1-1 check [bgp_subnet_10.0.0.0] bgp has subnet=10.0.0.0/24
        - bgp nexthop 10.255.1.253 exist
          ex : FGT-B1-1 check [bgp_nexthop_10.255.1.253] bgp has nexthop=10.255.1.253
        - bgp has route toward interface vpn_mpls
          ex : FGT-B1-1 check [bgp_subnet_10.0.0.0] bgp has interface=vpn_mpls
        - multiple requirements can be combined 
          ex ... has nexthop=10.255.1.253 nexthop=10.255.2.253 subnet=10.0.0.0/24
        """
        log.info("Enter with name={} line={}".format(name, line))
        
        found_flag = False

        # Connect to agent if not already connected
        if not self._connected:
            log.debug("Connection to agent needed agent={} conn={}".format(self.name, self.conn))
            success = self.connect(type='fortigate')
            log.debug("connection success={}".format(success))

            if not success:
                log.error("Could not connect to FortiGate {} to extract session. Abort scenario.".format(self.name))
                raise SystemExit
        
        # Query for bgp routes    
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
                    log.debug("Checking requirement {}={}".format(rname, rvalue))
                    rfdb = self._check_bgp_requirement(rname=rname, rvalue=rvalue, result=result)
                    feedback = feedback and rfdb
         
        self.add_report_entry(check=name, result=feedback)

        return found_flag



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
        if not self._connected:
            log.debug("Connection to agent needed agent={} conn={}".format(self.name, self.conn))
            success = self.connect(type='fortigate')
            log.debug("connection success={}".format(success))

            if not success:
                log.error("Could not connect to FortiGate {} to extract session. Abort scenario.".format(self.name))
                raise SystemExit
        
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
                    log.debug("Checking requirement {}={}".format(rname, rvalue))
                    rfdb = self._check_session_requirement(rname=rname, rvalue=rvalue, result=result)
                    feedback = feedback and rfdb
         
        self.add_report_entry(check=name, result=feedback)
        return feedback

    def _check_session_requirement(self, result={}, rname='', rvalue=''):
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
        log.info("Enter with rname={} rvalue={} result={}".format(rname, rvalue, result))
        
        fb = True  # by default, requirement is met

        # Dealing with state
        log.debug("result={}".format(result))

        if not 'state' in result:
            result['state'] = []
        
        if rname == 'state' :
            log.debug("Checking state '{}' is set on the session".format(rvalue))
            if result['state'].count(rvalue) > 0:
                log.debug("state {} is set".format(rname))
            else :
                log.debug("state {} is not set, requirement is not met".format(rvalue))
                fb = False

        elif rname in ('src','dest','sport','dport','proto','proto_state','duration','expire','timeout','dev','gwy','total'):
            log.debug("Accepted requirement rname={}".format(rname))
            if rname in result:
                if result[rname] == rvalue:
                    log.debug("rname={} found : requirement is met".format(rname))
                    fb = True
                else :
                    log.debug("rname={} found : requirement is not met".format(rname))
                    fb = False
        else:
            log.error("unknown session requirement {}={}".format(rname, rvalue))
            raise SystemExit
       
        log.debug("requirements verdict : {}".format(fb))
        return fb

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

        if rname == 'total' :
            log.debug("Checking exact number of subnets : asked={} got={}".format(rvalue, result['total']))
            if str(result['total']) == str(rvalue):
                log.debug("Total number of bgp routes is matching requirement")
            else:
                log.debug("Total number of bgp routes does not match requirement")
                fb = False
                  
        elif rname in ('subnet','nexthop','interface'):
            log.debug("requirement {}={} is known".format(rname, rvalue))
            if result[rname].count(rvalue) > 0:
                log.debug("rname={} found : requirement is met".format(rname))
                fb = True
            else :
                log.debug("rname={} found : requirement is not met".format(rname))
                fb = False
            
        else:
            log.debug("unknown bgp requirement {}={} is unknown".format(rname, rvalue))
            raise SystemExit

        log.debug("requirements verdict : {}".format(fb))
        return fb
 
if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_testrunner.py\n")

     


