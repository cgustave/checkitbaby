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
import fortigate_agent_multicast
import fortigate_agent_bfd
import fortigate_agent_ha


# Note: Mixin is a class with only methods.
# it is used to split the class in multiple sub modules with methods only
class Fortigate_agent(Agent, fortigate_agent_ipsec.Mixin, fortigate_agent_execute.Mixin, fortigate_agent_route.Mixin,
                      fortigate_agent_sdwan.Mixin, fortigate_agent_session.Mixin, fortigate_agent_system.Mixin,
                      fortigate_agent_multicast.Mixin, fortigate_agent_bfd.Mixin, fortigate_agent_ha.Mixin):
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
            result = self.process_route(line=line, agent=data['agent'], conn=data['conn'], type=data['type'], check=data['check'], command=data['command'])
        elif data['group'] == 'sdwan':
            result = self.process_sdwan(line=line, agent=data['agent'], conn=data['conn'], type=data['type'], check=data['check'], command=data['command'])
        elif data['group'] == 'multicast':
            result = self.process_multicast(line=line, agent=data['agent'], conn=data['conn'], type=data['type'], check=data['check'], command=data['command'])
        elif data['group'] == 'bfd':
            result = self.process_bfd(line=line, agent=data['agent'], conn=data['conn'], type=data['type'], check=data['check'], command=data['command'])
        elif data['group'] == 'ha':
            result = self.process_ha(line=line, agent=data['agent'], conn=data['conn'], type=data['type'], check=data['check'], command=data['command'])
        else:
            log.error("Syntax error: unknown command group {}".format(data['command']))
            raise SystemExit
        self.cmd_leave_vdom()   # leave_vdom or leave_global are the same (send 'end\n')
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
            log.error("Could not enter vdom {}".format(self._vdom))
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



if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_checkitbaby.py\n")
