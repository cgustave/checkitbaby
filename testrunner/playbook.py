# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2019
@author: cgustave
"""

import logging as log
import os 
import re
import json
from testcase import Testcase

class Playbook(object):
    """
    A Playbook is an ordered collection of Testcases.
    Each Testcase is identified from a number (id)
    """

    def __init__(self, name='', path='', debug=False):

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

        log.info("Constructor with name={} path={} debug={}".format(name, path, debug))

        # Attributs
        self.name = name
        self.path = path

        self.testcases = []           # List of testcase objects
        self.testcases_agents = []    # List of agents used in the testcases
        self.nb_testcases = 0  

        self.agents = {}              # Dictionnary of agents loaded from json file conf/agents.json

    def register(self):
        """
        Load the playbook testcases references
        Does not load the testcases scenario
        Directory contains all testcases (one file per testcase)
        Arguments:
            - path : path the playbook store (directory)
            - playbook : name of the playbook to run (a subdirectory)
        """
        log.info("Enter")
        nb = 0
        for filename in os.listdir(self.path+"/"+self.name+"/testcases"):
            nb=nb+1
            log.debug("nb={} filename={}".format(nb, filename))
            
            # Extract testcase id and name from filename
            match = re.search("^(?P<id>\d+)(?:_)(?P<name>\S+)(?:.txt)",filename)
            if match:
                id = match.group('id')
                name = match.group('name')
                log.debug("id={} name={}".format(id,name))
                self._register_testcase(id=id, name=name, filename=filename)
                
            else:
                log.debug("no match")

        self.nb_testcases = nb
        log.debug("Number of registered testcases={}".format(self.nb_testcases))
        self._register_used_agents()

    def _register_testcase(self, id, name, filename):
        """
        Register one testcase from id and name
        """
        log.info("Enter with id={} name={} filename={}".format(id,name,filename))

        tc = Testcase(id=id, name=name, playbook=self.name, path=self.path, filename=filename)
        self.testcases.append(tc)

    def _register_used_agents(self):
        """
        Requirements : _register_testcase()
        Go through all registered testcases, extract the agents and compile the
        list in self.agents
        """
        log.info("Enter")

        for tc in self.testcases:
            log.debug("id={} name={} agents={}".format(tc.id, tc.name, str(tc.agents)))
            for agent in tc.agents:
                if agent not in self.testcases_agents:
                    log.debug("Playbook new agent={}".format(agent))
                    self.testcases_agents.append(agent)

    def load_agents(self):
        """
        Load all agents with their details from json file
        """
        log.info("Enter")


    def get_agents(self):
        """
        Requirements : previous call to load_agents
        Returns : agents json format
        """
        return json.dumps(self.agents, indent=4)


if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_testrunner.py\n")
