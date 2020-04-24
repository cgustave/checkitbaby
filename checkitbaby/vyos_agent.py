# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2019
@author: cgustave
"""
import logging as log
from agent import Agent
import re

class Vyos_agent(Agent):
    """
    Vyos agent
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

    def process(self, line=""):
        """
        Vyos specific processing
        list of commands :
            traffic-policy NAME [delay DELAY loss LOSS]
        """
        log.info("Enter with line={}".format(line))

        match = re.search("(?:(\s|\t)*[A-Za-z0-9\-_]+:\d+(\s|\t)+)(?P<command>[A-Za-z-]+)",line)

        if match:
            command = match.group('command')
            log.debug("Matched with command={}".format(command))
        else:
            log.debug("No command has matched")

        if command == 'traffic-policy':
            self.cmd_traffic_policy(line)
        else:
            log.warning("command {} is unknown".format(command))


    def cmd_traffic_policy(self, line=""):
        """
        Set traffic policy settings (delay and loss)
        """
        log.info("Enter with line={}".format(line))

        delay = None
        loss = None

        match = re.search("traffic-policy\s+(?P<name>\w+)\s+", line)
        if match:
            name = match.group('name')
            log.debug("name={}".format(name))
        else:
            log.error("Could not understand traffic-policy command syntax")
            raise SystemExit

        # Set delay
        match_delay = re.search("\sdelay\s+(?P<delay>\d+)", line)
        match_loss  = re.search("\sloss\s+(?P<loss>\d+)", line)
        has_matched = False
        if match_delay:
            has_matched = True
            delay = match_delay.group('delay')
            log.debug("found delay={}".format(delay))

        if match_loss:
            has_matched = True
            loss = match_loss.group('loss')
            log.debug("found loss={}".format(loss))

        if not has_matched:
            log.error("Could not understand traffic-policy syntax")
            raise SystemExit

        # Connect to agent if not already connected
        if not self._connected:
            log.debug("Connection to agent needed agent={} conn={}".format(self.name, self.conn))
            success = self.connect(type='vyos')

            if not success:
                log.error("Could not connect to Vyos. Aborting scenario.")
                raise SystemExit
   
        if has_matched:
            log.debug("traffic-policy {} : set loss {} and set delay {}".format(name, loss, delay))
            if not self.dryrun:
                self._ssh.traffic_policy = name
                self._ssh.set_traffic_policy(packet_loss=loss, network_delay=delay)
        else:
            log.error("unexpected traffic policy request")
            raise SystemExit

if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_checkitbaby.py\n")

     


