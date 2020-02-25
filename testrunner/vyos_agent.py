# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2019
@author: cgustave
"""
import logging as log
from agent import Agent
from netcontrol.vyos.vyos import Vyos
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
        if match_delay:
            delay = match_delay.group('delay')
            log.debug("delay={}".format(delay))
        elif match_loss:
            loss = match_loss.group('loss')
            log.debug("loss={}".format(loss))
        else:
            log.error("Could not understand traffic-policy syntax")
            raise SystemExit

        # Connect to agent if not already connected
        if not self._connected:
            log.debug("Connection to agent needed agent={} conn={}".format(self.name, self.conn))
            self.connect()

        if delay:
            log.debug("traffic-policy {} : set delay {}".format(name, delay)) 
            self._ssh.set_traffic_policy(network_delay=delay)
            
        if loss:
            log.debug("traffic-policy {} : set loss {}".format(name, loss))
            self._ssh.set_traffic_policy(packet_loss=loss)
 
    def connect(self):
        """
        Connect to vyos agent without sending any command
        This opens the ssh channel for data exchange
        """
        log.info("Enter")
        ip = self.agent['ip']
        port = self.agent['port']
        login = self.agent['login']
        password = self.agent['password']
        ssh_key_file = self.agent['ssh_key_file']
        log.debug("ip={} port={} login={} password={} ssh_key_file={}".format(ip, port, login, password, ssh_key_file))

        self._ssh = Vyos(ip=ip, port=port, user=login, password=password, private_key_file=ssh_key_file, debug=self.debug)
        tracefile_name = self.get_filename(type='trace')
        self._ssh.trace_open(filename=tracefile_name)

        try:
           self._ssh.connect()
           self._connected = True
        except:
            log.error("Connection to agent {} failed".format(self.name))



if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_testrunner.py\n")

     


