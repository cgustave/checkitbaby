# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2019
@author: cgustave
"""
import logging as log
from agent import Agent
import re

class Lxc_agent(Agent):
    """
    LXC agent
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

        # Private attributs
        self._connected = False    # ssh connection state with the agent 
       
    def process(self, line=""):
        """
        LXC specific line processing
        List of allowed commands : open, connect, send, check
        Command line example
        srv-1:1 open tcp 80
        clt-1:1 connect tcp 1.1.1.1 80
        clt-1:1 send "alice"
        srv-1:1 check [srv recv] data receive "alice" since "server ready"
        """
        log.info("Enter with line={}".format(line))

        match = re.search("(?:(\s|\t)*[A-Za-z0-9\-_]+:\d+(\s|\t)+)(?P<command>[A-Za-z]+)",line)

        if match:
            command = match.group('command')
            log.debug("Matched with command={}".format(command))
        else:
            log.debug("No command has matched")

        if command == 'open':
            self.cmd_open(line)
        elif command == 'connect':
            self.cmd_connect(line)
        elif command == 'send':
            self.cmd_send(line)
        elif command == 'check':
           self.cmd_check(line) 
        elif command == 'close':
           self.cmd_close(line)
        else:
            log.warning("command {} is unknown".format(command))

 
    def cmd_open(self, line):
        """
        Processing for command "open"
        Opens a server udp or tcp connection 
        """
        log.info("Enter with line={}".format(line))

        match = re.search("(?:open(\s|\t)+)(?P<proto>tcp|udp)(?:(\s|\t)+)(?P<port>\d+)",line) 
        if match:
            proto = match.group('proto')
            port = match.group('port')
            log.debug("proto={} port={}".format(proto,port))
        else:
            log.error("Could not extract proto and port from open command on line={}".format(line))
            raise SystemExit

        # Connect to agent if not already connected
        if not self._connected:
            log.debug("Connection to agent needed agent={} conn={}".format(self.name, self.conn))


    def cmd_connect(self, line):
        """
        Processing for command "connect"
        """
        log.info("Enter with line={}".format(line))


    def cmd_send(self, line):
        """
        Processing for command "send"
        """
        log.info("Enter with line={}".format(line))


    def cmd_check(self, line):
        """
        Processing for command "check"
        """
        log.info("Enter with line={}".format(line))


    def cmd_close(self, line):
        """
        Processing for command "close"
        """
        log.info("Enter with line={}".format(line))


if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_testrunner.py\n")

     


