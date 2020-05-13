# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2020
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
        else:
            self.debug = False
            log.basicConfig(level='ERROR')

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
        #if self._ssh:
        #    self._ssh.close()

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
        elif command == 'flush':
            self.cmd_flush(line)
        else:
            log.warning("command {} is unknown".format(command))

    def cmd_flush(self, line=""):
        """
        Process flush command:
          - flush ike gateway
        """
        log.info("Enter with line={}".format(line))
        match_command = re.search("flush\s+(?P<command>\w+)\s+(?P<subcommand>\w+)", line)
        if match_command:
            command = match_command.group('command')
            subcommand = match_command.group('subcommand')
            log.debug("Matched with command={} subcommand={}".format(command,subcommand))
            if command == 'ike' and subcommand == 'gateway':
                log.debug("vpn ike gateway flush requested")
                self._connect_if_needed()
                self._ssh.cli(commands=['diagnose vpn ike gateway flush'])
            else:
                log.error("unknown combination of command={} subcommand={}".format(command, subcommand))
                raise SystemExit
        else:
            log.debug("No command has matched")
         


    def cmd_get(self, line=""):
        """
        Process get commands
        """
        log.info("Enter with line={}".format(line))
        self._connect_if_needed(stop_on_error=False)

        # get version
        match_version = re.search("get\sstatus", line)
        if match_version:
             if not self.dryrun:
                 result = self._ssh.get_status()
                 log.debug("==> result={}".format(result))
                 self.add_report_entry(get='version', result=result['version']) 
                 self.add_report_entry(get='license', result=result['license']) 
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
          elif command == 'status':
              self._cmd_check_status(name=name, line=line)
          elif command == 'sdwan':
              self._cmd_check_sdwan(name=name, line=line)
          elif command == 'ike':
              self._cmd_check_ike(name=name, line=line)

          else:
              log.error("Unknown check command '{}' for test named {}".format(command, name))
              raise SystemExit
        else:
           log.error("Could not understand check command syntax")
           raise SystemExit


    def _cmd_enter_vdom(self, vdom=""):
        """
        Enters in specified vdom
        """
        log.info("Enter with vdom={}".format(vdom))

        self._connect_if_needed()
        result = self._ssh.enter_vdom(vdom=vdom)

        if not result:
            log.error("Could not enter vdom {}".format(vdom))
            raise SystemExit


    def _cmd_enter_global(self):
        """
        Enters in global section
        """
        log.info("Enter")

        self._connect_if_needed()
        result = self._ssh.enter_global()

        if not result:
            log.error("Could not enter global section")
            raise SystemExit

    def _vdom_processing(self, line):
        """
        Do what is needed if query is specific for a vdom or global section
        We are looking for pattern \svdom=VDOM\s to enter vdom
        We are looking for \svdom=global\s to enter global section
        the line is then returned without its vdom=XXXX keyword for further
        processing
        """
        log.info("Enter with line={}".format(line))

        # Match global
        match_global = re.search("\svdom=global\s", line)
        match_vdom =  re.search("\svdom=(?P<vd>\S+)\s", line)

        found = False
        if match_global:
            self._cmd_enter_global()
            found = True

        elif match_vdom:
            vd = match_vdom.group('vd')
            self._cmd_enter_vdom(vdom=vd)
            found = True

        # remove vdom= from line id needed 
        if found:
            line = re.sub("vdom=\S+\s", '', line)
            log.debug("stripped line={}".format(line))

        return line


    def _cmd_check_ike(self, name="", line=""):
        """
        ike status:
        Checks on IPsec ike status (from 'diagnose vpn ike status'), examples:
          FGT-B1-1:1 check [B1_tunnels] ike status has ike_created=3
          FGT-B1-1:1 check [B1_tunnels] ike status has ike_created=3 ike_established=3
          FGT-B1-1:1 check [B1_tunnels] ike status has ipsec_created=3 ipsec_established=3
        """
        log.info("Enter with name={} line={}".format(name, line))

        found_flag = False
        self._connect_if_needed()


        result = self._ssh.get_ike_and_ipsec_sa_number()
        if result:
            found_flag = True

            # Without any further requirements, result is pass
            feedback = found_flag

            # Processing further requirements (has ...)
            match_has = re.search("\s+has\s+(?P<requirements>.+)",line)
            if match_has:
                requirements = match_has.group('requirements')
                log.debug("requirements list: {}".format(requirements))
                rnum = 0
                for r in requirements.split():
                    rnum = rnum + 1
                    log.debug("requirement num={} : {}".format(rnum, r))
                    match_req = re.search("^(?P<rname>.+)=(?P<rvalue>.+)", r)
                    if match_req:
                        rname = match_req.group('rname')
                        rvalue = match_req.group('rvalue')
                        log.debug("Checking requirement {}={}".format(rname, rvalue))
                        if rname == 'ike_created':
                            rfdb = self.check_generic_requirement(rname='created', rvalue=rvalue, result=result['ike'])
                        elif rname == 'ike_established':
                            rfdb = self.check_generic_requirement(rname='established', rvalue=rvalue, result=result['ike'])
                        elif rname == 'ipsec_create':
                            rfdb = self.check_generic_requirement(rname='created', rvalue=rvalue, result=result['ipsec'])
                        elif rname == 'ipsec_established':
                            rfdb = self.check_generic_requirement(rname='established', rvalue=rvalue, result=result['ike'])
                        else:
                            log.error("unrecognized requirement")
                            raise SystemExit

                        feedback = feedback and rfdb
            self.add_report_entry(check=name, result=feedback)
            return found_flag

    def _cmd_check_bgp(self, name="", line=""):
        """
        Checks on bgp routing table (from get router info routing-table bgp)
        - number of bgp routes is 4 :
            ex : FGT-B1-1:1 check [bgp_4_routes] bgp has total=4
        - bgp route for subnet 10.0.0.0/24 exist :
            ex : FGT-B1-1:1 check [bgp_subnet_10.0.0.0] bgp has subnet=10.0.0.0/24
        - bgp nexthop 10.255.1.253 exist
            ex : FGT-B1-1:1 check [bgp_nexthop_10.255.1.253] bgp has nexthop=10.255.1.253
        - bgp has route toward interface vpn_mpls
            ex : FGT-B1-1:1 check [bgp_subnet_10.0.0.0] bgp has interface=vpn_mpls
        - multiple requirements can be combined 
            ... has nexthop=10.255.1.253 nexthop=10.255.2.253 subnet=10.0.0.0/24
        - allows vdom= statement, should be positioned after bgp keyword
            ex :  

        """
        log.info("Enter with name={} line={}".format(name, line))
        
        found_flag = False
        self._connect_if_needed()
       
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
        match_has = re.search("\s+has\s+(?P<requirements>.+)",line)
        if match_has:
            requirements = match_has.group('requirements')
            log.debug("requirements list: {}".format(requirements))
            rnum = 0 
            for r in requirements.split():
                rnum = rnum + 1
                log.debug("requirement No={} : {}".format(rnum, r))
                match_req = re.search("^(?P<rname>.+)=(?P<rvalue>.+)", r)
                if match_req:
                    rname = match_req.group('rname')
                    rvalue = match_req.group('rvalue')
                    log.debug("Checking requirement {}={}".format(rname, rvalue))
                    rfdb = self._check_bgp_requirement(rname=rname, rvalue=rvalue, result=result)
                    feedback = feedback and rfdb
         
        self.add_report_entry(check=name, result=feedback)

        return found_flag

    def _connect_if_needed(self, stop_on_error=True):
        """
        Connects to fortigate if not already connected
        if stop_on_error is True, exit if connection could not be established
        """
        # Connect to agent if not already connected
        if not self._connected:
            log.debug("Connection to agent needed agent={} conn={}".format(self.name, self.conn))
            success = self.connect(type='fortigate')
            log.debug("connection success={}".format(success))

            if not success:
                if stop_on_error: 
                   log.error("Could not connect to FortiGate {} aborting scenario ".format(self.name))
                   raise SystemExit
                else:
                   log.error("Could not connect to FortiGate {} but continue scenario ".format(self.name))


    def _cmd_check_status(self, name="", line=""):
        """
        Check on fortigate get system status command
        - license is valid
        """
        log.info("Enter with name={} line={}".format(name, line))
        found_flag = False
        self._connect_if_needed(stop_on_error=True)
        if not self.dryrun:
            result = self._ssh.get_status()
            license = result['license']
            version = result['version']
            # Use this opportunity to record firmware as 'get' value
            self.add_report_entry(get='version', result=result['version']) 
            log.debug("found license={} version={}".format(license, version))
        else:
            log.debug("dry-run")

        if result:
            found_flag = True

        # Without any further requirements, result is pass
        feedback = found_flag

        # Processing further requirements (has ...)
        match_has = re.search("\s+has\s+(?P<requirements>.+)",line)
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
                    rfdb = self._check_status_requirement(rname=rname, rvalue=rvalue, result=result)
                    feedback = feedback and rfdb
         
        self.add_report_entry(check=name, result=feedback)
        return found_flag

    def _cmd_check_session(self, name="", line=""):
        """
        Checks on fortigate session :
        - session exist
          ex : FGT-B1-1:1 check [ssh_session_exist] session filter dport=22 dest=192.168.0.1
        - session has flag 'dirty'
          ex : FGT-B1-1:1 check [session_is_dirty] session filter dport=5000 has flag=dirty

        - allows vdom selection (should be positioned after keyword session
          ex : F1B2:1 check [ssh_session] session vdom=customer filter dport=22
        """
        log.info("Enter with name={} line={}".format(name, line))
      
        found_flag = False
 
        # Prepare session filter
        session_filter = {} 

        # vdom processing if needed
        line = self._vdom_processing(line=line)

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
        self._connect_if_needed()
        
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
        match_has = re.search("\s+has\s+(?P<requirements>.+)",line)
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
            fb = self.check_generic_requirement(result=result, rname=rname, rvalue=rvalue)
        else:
            log.error("unknown session requirement {}={}".format(rname, rvalue))
            raise SystemExit
       
        log.debug("requirements verdict : {}".format(fb))
        return fb

    def _check_status_requirement(self, result={}, rname='', rvalue=''):
        """
        Validates status requirement
        has license=True (be careful with case, true is not True)
        """
        log.info("Enter with rname={} rvalue={} result={}".format(rname, rvalue, result))
        fb = True  # by default, requirement is met
        
        if not 'license' in result:
            result['license'] = {}
       
        if rname=='license':
            log.debug("Checking license")
            if str(result['license']) == str(rvalue):
                log.debug("License requirement is met")
            else:
                log.debug("License requirement is not met")
                fb = False
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

        if rname in ('total', 'recursive', 'subnet','nexthop','interface'):

            log.debug("requirement {}={} is known".format(rname, rvalue))

            if rname == 'total' :
                log.debug("Checking exact number of subnets : asked={} got={}".format(rvalue, result['total']))
                if str(result['total']) == str(rvalue):
                    log.debug("Total number of bgp routes is matching requirement")
                else:
                    log.debug("Total number of bgp routes does not match requirement")
                    fb = False

            elif rname == 'recursive' :
                log.debug("Checking exact number of recursive routes specifically : asked={} got={}".format(rvalue, result['recursive']))
                if str(result['recursive']) == str(rvalue):
                    log.debug("Total number of bgp recursive routes is matching requirement")
                else:
                    log.debug("Total number of bgp recursive routes does not match requirement")
                    fb = False

            elif result[rname].count(rvalue) > 0:
                log.debug("rname={} found : requirement is met".format(rname))
                fb = True
            else :
                log.debug("rname={} found : requirement is not met".format(rname))
                fb = False
            
        else:
           log.error("unknown bgp requirement {}={} is unknown".format(rname, rvalue))
           raise SystemExit

        log.debug("requirements verdict : {}".format(fb))
        return fb

    def _cmd_check_sdwan(self, name="", line=""):
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

        log.info("Enter with name={} line={}".format(name, line))

        # vdom processing if needed
        line = self._vdom_processing(line=line)

        # remove requirements from line (after 'has ...')
        line_no_requirement = line
        line_no_requirement = line.split('has')[0]
        log.debug("line_no_requirement={}".format(line_no_requirement))

        match_command = re.search("sdwan\s+service\s(?P<rule>\d+)\s+member\s+(?P<seq>\d+)", line_no_requirement)
        if match_command:
            rule = match_command.group('rule') 
            seq = match_command.group('seq') 
            log.debug("matched sdwan service rule={} member seq={}".format(rule, seq))
            self._connect_if_needed()

            # Query SDWAN service
            result = self._ssh.get_sdwan_service(service=rule)
            if result:
                if len(result['members']) >= 1:
                    log.debug("At least 1 member was found")
                    found_flag = True

            # Without any further requirements, result is pass
            feedback = found_flag

            # Processing further requirements (has ...)
            match_has = re.search("\s+has\s+(?P<requirements>.+)",line)
            if match_has:
                requirements = match_has.group('requirements')
                log.debug("requirements list: {}".format(requirements))
                rnum = 0
                for r in requirements.split():
                    rnum = rnum + 1
                    log.debug("requirement num={} : {}".format(rnum, r))
                    match_req = re.search("^(?P<rname>.+)=(?P<rvalue>.+)", r)
                    if match_req:
                        rname = match_req.group('rname')
                        rvalue = match_req.group('rvalue')
                        log.debug("Checking requirement {}={}".format(rname, rvalue))
                        rfdb = self._check_sdwan_service_requirement(seq=seq, rname=rname, rvalue=rvalue, result=result)
                        feedback = feedback and rfdb
            self.add_report_entry(check=name, result=feedback)
            return found_flag


    def _check_sdwan_service_requirement(self, seq='', result={}, rname='', rvalue=''):
        """
        Validates all requirements for sdwan service
        """
        log.info("Enter with seq={} rname={} rvalue={} result={}".format(seq, rname, rvalue, result))
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
            fb = self.check_generic_requirement(result=result['members'][seq], rname=rname, rvalue=rvalue)
        else:
            log.error("unknown requirement")
            raise SystemExit

        log.debug("requirements verdict : {}".format(fb))
        return fb

    def check_generic_requirement(self, result={}, rname="", rvalue=""):
        """
        Generic requirement check
        Returns True or False
        """
        log.info("Enter with rname={} rvalue={}".format(rname,rvalue))
        if rname in result:
            if result[rname] == rvalue:
                 log.debug("rname={} found : requirement is met".format(rname))
                 fb = True
            else :
                 log.debug("rname={} found : requirement is not met".format(rname))
                 fb = False
        else:
            log.error("requirement {} is not in result={}".format(rname, result))
            fb = False
        return fb
 

if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_checkitbaby.py\n")

     


