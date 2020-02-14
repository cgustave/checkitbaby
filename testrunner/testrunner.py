# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2019
@author: cgustave

This package provides main class Testrunner

An agent based testsuite targeted to run within a FortiPoC LXC in order to run through a set 
of defined testcases in a playbook.

Agents could be lxcs, vyos routers, FortiPoC or FortiGates

Tools used to run as server on client on LXC should be simple and similar to the ones used manually for testing.
Each commands and their outputs should be kept within the test run as traces.
Checks should all generate a result in the test report. They are all based on analysis 
from output command output files (so they can be verified by users)
At the end of the testcase, a generic result fail/pass is reported.
"""

import logging as log
import json
import os
import re
from playbook import Playbook

class Testrunner(object):
    """
    Main application. 

    #### A testrunner contains :
        - mutliple test agents with their definitions
        - a single playbook containing the testcases
        - a report structure filled from the testcases when run

    It is called with:
        - a base path for the playbook
        - a debug level  

    #### Directory structure:
        - /PLAYBOOK_BASE_PATH : The base name of the playbook location
        ex : /fortipoc/playbooks

       * /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME
       ex : /fortipoc/playbooks/advpn

       * /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/conf : configuration directory

            - /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/conf/agents.json  : files with agents definitions in json format
            ex : /fortipoc/playbooks/advpn/conf/agents.json

            - /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/conf/variables.json : file defining all variables in json format 

       * /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/testcases    : directory containing testcases
       ex : /fortipoc/playbooks/advpn/testcases

            - /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/testcases/NNN_TESTCASE_NAME : one testcase file
            with NNN : a number starting from 0 (used as testcase index)
            TESTCASE_NAME : any name for the testcase

             ex : /fortipoc/playbooks/advpn/testcases/1_environment.txt
             ex : /fortipoc/playbooks/advpn/testcases/2_connectivity.txt
             ex : /fortipoc/playbooks/advpn/testcases/3_ipsec_tunnels.txt
             ex : /fortipoc/playbooks/advpn/testcases/4_routing.txt

       * /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/runs   : directory for all runs
       ex : /fortipoc/playbooks/advpn/runs

            - /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/runs/1 : directory for run number 1 
            ex : /fortipoc/playbooks/advpn/runs/1

            - /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/runs/1/report.json : report from run 1
    
    #### Internal attributs schemes

       * self.playbook 

    """

    def __init__(self, path="/fortipoc/playbooks", debug=False):

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

        if not (os.path.exists(path) and os.path.isdir(path)):
            print ("path does not exist or is not a directory\n")
            raise SystemExit

        log.info("Constructor with path={}, debug={}".
                 format(path, debug))

        # Attributs
        self.run = None                              # the run identifier
        self.variables = {}                          # dictionnary of testcases variables
        self.playbook = None    
        self.agents = {}                             # dictionary of agent (keys are agents name)
        self.report = {}                             # dictionary of reports (keys are reports name)
        self.path = path                             # base path of the playbook store 

    def load_variables(self):
        """
        Load all variables used in the testcase taken from json file format
        variables.json
        """
        log.info("Enter")

    def get_variables(self):
        """
        Requirements : previous call to load_variables
        Returns : testcase variables in json format
        """
        log.info("Enter")
        return json.dumps(self.variables, indent=4)

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

    def register_testcases(self, playbook='myPlaybook'):
        """
        Load the playbook testcases references
        Does not load the testcases scenario
        Directory contains all testcases (one file per testcase)
        Returns the number of loaded testcases
        """
        log.info("Enter with playbook={}".format(playbook))
        nb = 0
        for filename in os.listdir(self.path+"/"+playbook+"/testcases"):
            nb=+1
            log.debug("nb={} filename={}".format(nb, filename))
            
            # Extract testcase id and name from filename
            match = re.search("^(?P<id>\d+)(?:_)(?P<name>\S+)(?:.txt)",filename)
            if match:
                log.debug("id={} name={}".format(match.group('id'),match.group('name')))
                
            else:
                log.debug("no match")


        return nb

    def get_playbook(self):
        """
        Requirements : previous call to load_playbook
        Returns : playbook in json format
        """
        log.info("Enter")
        return json.dump(self.playbook, indent=4)

    def run_all(self):
        """
        Runs the full playbook testcases
        """
        log.info("Enter")

    def run_testcase(self, run, id):
        """
        Runs a single testcase specified by its id
        Returns True in no exception is caught
        """
        log.info("Enter with run={} id={}".format(run, id))

    def report(self, run='1'):
        """
        Requirement : a minimum of a testcase should have been run on the given run id
        Provide a report from the last testcases that ran in run 1
        Return: Report in json format
        """
        log.info("Enter with run={}".format(run))
        return json.dump(self.report, indent=4)



if __name__ == '__main__': #pragma: no cover

    # Instanciate testrunner using playbook directory ./playbook
    trun = Testrunner(path='./playbooks', debug=True)

    # Load a playbook
    trun.playbook(Playbook(debug=True))

    # Load test agents details
    trun.load_agents()

    # Load variables (if any)
    trun.load_variables()

    # Load playbook with all testcases
    nb_testcases = trun.register_testcases(playbook="myPlaybook")
    print("Loaded {} testcases\n".format(nb_testcases))

    # Run testcase 1 in run 1
    if (trun.run_testcase(id='1', run='1')):
        print("Succesfull testcase run\n")
    else:
        print("Failed testcase run\n")

    # Dump the report from run 1
    #print (trun.report(run='1'))

