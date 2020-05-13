# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2020
@author: cgustave
"""
import logging as log
from agent import Agent
import re

class Fortipoc_agent(Agent):
    """
    Fortipoc agent
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
        self.variables = None    # Scenario variables
        self.testcase = None     # For which testcase id the agent was created
        self.report = None       # Testcase report (provided from Workbook)

        # Private attributs
        self._connected = False  # ssh connection state with the agent
        self._ssh = None         # Will be instanciated with type Fpoc

    def __del__(self):
        """
        Desctructor to close opened connection to agent when exiting
        """
        if self._ssh:
            self._ssh.close()

    def process(self, line=""):
        """
        Fpoc specific processing
        list of commands :
          link down|up DEVICE PORT
            ex : fpoc:1 link down FGT-B1-1 Port1
        """
        log.info("Enter with line={}".format(line))

        match = re.search("(?:(\s|\t)*[A-Za-z0-9\-_]+:\d+(\s|\t)+)(?P<command>[A-Za-z-]+)",line)
        if match:
            command = match.group('command')
            log.debug("Matched with command={}".format(command))
        else:
            log.debug("No command has matched")

        if command == 'link':
            self.cmd_link(line)
        else:
            log.warning("command {} is unknown".format(command))

    def cmd_link(self, line):
        """
        Bring FortiPoC link up or down
        """
        log.info("Enter with line={}".format(line))

        match = re.search("link\s+(?P<state>up|down)(\s|\t)+(?P<device>[A-Za-z0-9\-_]+)(\s|\t)+(?P<port>[A-Za-z0-9\-_]+)", line)
        if match:
            state = match.group('state')
            device = match.group('device')
            port = match.group('port')
            log.debug("state={} device={} port={}".format(state, device, port))

        else:
            log.error("Could not understand link syntax")
            raise SystemExit

        # Connect to agent if not already connected
        if not self._connected:
            log.debug("Connection to agent needed agent={} conn={}".format(self.name, self.conn))
            success = self.connect(type='fortipoc')
            
            if not success:
                log.error("Could not connect to FortiPoC. Aborting scenario")
                raise SystemExit

        if not self.dryrun:
            self._ssh.set_poc_link_status(device=device, link=port, status=state)


if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_checkitbaby.py\n")

     


