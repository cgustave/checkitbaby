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


    def process(self, line=""):
        """
        LXC specific line processing

        """
        log.info("Enter with line={}".format(line))

        # Sanity checks
        if self.path == None:
            log.error("Undefined path")
            raise SystemExit





if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_testrunner.py\n")

     


