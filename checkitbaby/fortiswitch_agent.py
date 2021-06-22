"""
Created on Jun 21, 2021
@author: cgustave
"""
import logging as log
from agent import Agent
import re

class Fortiswitch_agent(Agent):
    """
    Fortiswitch agent
    To avoid ssh connection issues because of key change, it is recommended
    to use an ssh key to connect to FortiGate
    Commands :
      port up|down <portid>
        ex: FSW1: port up port10
      check [check_id] port status [ has state=up|down]
        ex: FSW1: check [port10_status] port port10 status
        ex: FSW1: check [port10_status_is_up] port status has state=up
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
        self.testcase = ""       # For which testcase id the agent was created
        self.report = {}         # Testcase report (provided from Workbook)

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
        FortiSwitch specific processing
        list of commands :
        """
        log.info("Enter with line={}".format(line))
        result = False
        match = re.search("(?:(\s|\t)*[A-Za-z0-9\-_]+:\d+(\s|\t)+)(?P<command>[A-Za-z-]+)",line)
        if match:
            command = match.group('command')
            log.debug("Matched with command={}".format(command))
            if command == 'port':
                self.cmd_port(line)
            elif command == 'check':
                 result = self.cmd_check(line=line)
            else:
                 log.debug("No command has matched")
        else:
            log.warning("command is unknown")
        return result

    def cmd_port(self, line=""):
        """
        Process port commands
        port up\down <port>
        """
        log.info("Enter with line={}".format(line))
        match = re.search('(?P<status>(up|down))\s+(?P<port>(port\d+))', line)
        if match:
            status = match.group('status')
            port = match.group('port')
            log.debug("status={} port={}".format(status, port))
            self._ssh.set_port_status(port=port, status=status)
        else:
            log.warning("unrecognized port command syntax")

    def cmd_check(self, line=""):
        """
        Process check commands
        Check commands distribution to specific handling
        """
        result = False
        log.info("Enter with line={}".format(line))
        match_command = re.search("check(\s|\t)+\[(?P<name>.+)\](\s|\t)+(?P<command>\w+)",line)
        if match_command:
            name =  match_command.group('name')
            command = match_command.group('command')
            if command == 'port':
                result = self.cmd_check_port(name=name,line=line)
        return result

    def cmd_check_port(self, name="", line=""):
        """
        Process check port command
        check [name] port status <port> has state=<up/down>
        """
        log.info("Enter with name={} line={}".format(name, line))
        result = False
        match_command = re.search('port\s+status\s+(?P<port>(port\d+))', line)
        if match_command:
            port = match_command.group('port')
            result = self._ssh.get_port_status(port=port)
            log.debug("port={} status={}".format(port, result))
            self.add_report_entry(get=name, result={'port': port, 'status': result})
            match_requirement = re.search('has\sstate=(?P<state>(up|down))', line)
            if match_requirement:
                state = match_requirement.group('state')
                if state == result:
                    self.add_report_entry(check=name, result=True)
                    result = True
                    log.debug("port={} status={} is matching requirement".format(port, state))
                else:
                    self.add_report_entry(check=name, result=False)
                    result = False
                    log.debug("port={} status={} is not matching requirement".format(port, state))
            else:
                log.warning('unrecognized requirement')
        return result

if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_checkitbaby.py\n")
