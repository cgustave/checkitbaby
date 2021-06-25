# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2020
@author: cgustave
"""
import logging as log
from agent import Agent
import re
import fortigate_agent_ipsec
import fortigate_agent_execute
import fortigate_agent_route
import fortigate_agent_sdwan
import fortigate_agent_session
import fortigate_agent_system

# Note: Mixin is a class with only methods.
# it is used to split the class in multiple sub modules with methods only
class Fortigate_agent(Agent, fortigate_agent_ipsec.Mixin, fortigate_agent_execute.Mixin, fortigate_agent_route.Mixin,
                      fortigate_agent_sdwan.Mixin, fortigate_agent_session.Mixin, fortigate_agent_system.Mixin):
    """
    Fortigate specific agent
    To avoid ssh connection issues because of key change, it is recommended to use a ssh key to connect to FortiGate
    1st called method (entry point) is process()
    Specific agent is implemented from Agent.py during normal usage. Direct implementation is only for unittest.
    See tests/test_fortigate.py unittests for samples of user commands.
    Agent syntax documented in README.md
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
        self.path = ""
        self.playbook = ""
        self.run = ""
        self.agent = {}          # name, id ... and all info for the agent itself
        self.testcase = ""     # For which testcase id the agent was created
        self.report = {}         # Testcase report (provided from Workbook)

        # Private attributs
        self._connected = False  # ssh connection state with the agent
        self._vdom = ''          # Keep track of config vdom

    def __del__(self):
        """
        Desctructor to close opened connection to agent when exiting
        """
        pass
        #if self._ssh:
        #    self._ssh.close()

    def process(self, line=""):
        """
        FortiGate specific processing.
        Agent entry point.
        list of commands :
        """
        log.info("Enter with line={}".format(line))
        result = {}
        line = self._vdom_processing(line=line)
        if self._vdom != '':
            self.cmd_enter_vdom()
        else:
            self.cmd_enter_global()
        data = self.parse_line(line=line)
        if data['group'] == 'system':
            result = self.process_system(line=line, agent=data['agent'], conn=data['conn'], type=data['type'], check=data['check'], command=data['command'])
        elif data['group'] == 'execute':
            result = self.process_execute(line=line, agent=data['agent'], conn=data['conn'], type=data['type'], check=data['check'], command=data['command'])
        elif data['group'] == 'session':
            result = self.process_session(line=line, agent=data['agent'], conn=data['conn'], type=data['type'], check=data['check'], command=data['command'])
        elif data['group'] == 'ipsec':
            result = self.process_ipsec(line=line, agent=data['agent'], conn=data['conn'], type=data['type'], check=data['check'], command=data['command'])
        elif data['group'] == 'route':
            result = self.process_route(line)
        elif data['group'] == 'sdwan':
            result = self.process_sdwan(line)
        else:
            log.error("Syntax error: unknown command group {}".format(data['command']))
            raise SystemExit
        self.cmd_leave_vdom()   # leave_vdom or leave_global are the same (send 'end\n')
        return result


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
                self.connect_if_needed()
                self._ssh.cli(commands=['diagnose vpn ike gateway flush'])
            else:
                log.error("unknown combination of command={} subcommand={}".format(command, subcommand))
                raise SystemExit
        else:
            log.debug("No command has matched")

    def _cmd_check_route(self, line=''):
        """
        Check command route distribution
        """
        log.info("Enter with line={}".format(line))
        match_command = re.search("check(\s|\t)+\[(?P<name>.+)\](\s|\t)+(?:route)\s+(?P<command>\w+)",line)
        if match_command:
            name =  match_command.group('name')
            command = match_command.group('command')
            if command == 'bgp':
                result = self._cmd_check_route_bgp(name=name, line=line)
            else:
                log.error("Unknown check route command")
                raise SystemExit
        return result

    def _vdom_processing(self, line):
        """
        Do what is needed if query is specific for a vdom or global section
        We are looking for pattern \svdom=VDOM\s to enter vdom
        We are looking for \svdom=global\s to enter global section
        the line is then returned without its vdom=XXXX keyword for further processing
        record vdom in self.vdom
        self._vdom is set vdom name if vdom=<vdom> was specified in the line
        """
        log.info("Enter with line={}".format(line))
        # Match global
        match_global = re.search("(\svdom=global\s)|(\sglobal\s)", line)
        match_vdom =  re.search("\svdom=(?P<vd>\S+)\s", line)
        found = False
        if match_global:
            self._vdom=''
            found = True
        elif match_vdom:
            vd = match_vdom.group('vd')
            self._vdom=vd
            found = True
        # remove vdom= from line is needed for further processing
        if found:
            line = re.sub("vdom=\S+\s", '', line)
            line = re.sub("\sglobal", '' , line)
            log.debug("stripped line={}".format(line))
        return line

    def cmd_enter_vdom(self):
        """
        Enters vdom specified in self.vdom
        """
        log.info("Enter having vdom={}".format(self._vdom))

        self.connect_if_needed()
        result = self._ssh.enter_vdom(vdom=self._vdom)

        if not result:
            log.error("Could not enter vdom {}".format(vdom))
            raise SystemExit

    def cmd_enter_global(self):
        """
        Enters in global section
        """
        log.info("Enter")

        self.connect_if_needed()
        result = self._ssh.enter_global()

        if not result:
            log.error("Could not enter global section")
            raise SystemExit

    def cmd_leave_vdom(self):
        """
        Leaves vdom
        """
        log.info("Enter")

        self.connect_if_needed()
        #result = self._ssh.leave_vdom()
        result = self._ssh.ssh.shell_send(["end\n"])
        if not result:
            log.error("Could not leave vdom {}".format(vdom))
            raise SystemExit


    def _cmd_check_route_bgp(self, name="", line=""):
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
        """
        log.info("Enter with name={} line={}".format(name, line))
        line = self._vdom_processing(line=line)
        found_flag = False
        self.connect_if_needed()
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
        return feedback


    def connect_if_needed(self, stop_on_error=True):
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
        found_flag = False
        # vdom processing if needed
        line = self._vdom_processing(line=line)
        version = '6.4'
        if re.search('version=6.2', line):
            line = re.sub("version=6.2\s", '', line)
            version = '6.2'
        # remove requirements from line (after 'has ...')
        line_no_requirement = line
        line_no_requirement = line.split('has')[0]
        log.debug("line_no_requirement={}".format(line_no_requirement))
        match_command = re.search("sdwan\s+service\s(?P<rule>\d+)\s+member\s+(?P<seq>\d+)", line_no_requirement)
        if match_command:
            rule = match_command.group('rule')
            seq = match_command.group('seq')
            log.debug("matched sdwan service rule={} member seq={}".format(rule, seq))
            self.connect_if_needed()
            # Query SDWAN service

            result = self._ssh.get_sdwan_service(service=rule, version=version)
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
        # if command failed, no members could be found => fail
        if result['members'] == {}:
            log.warning("could not retrieve sdwan members, return Fail")
            return False
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
            fb = self.check_requirement(result=result['members'][seq], name=rname, value=rvalue)
        else:
            log.error("unknown requirement")
            raise SystemExit
        log.debug("requirements verdict : {}".format(fb))
        return fb


if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_checkitbaby.py\n")
