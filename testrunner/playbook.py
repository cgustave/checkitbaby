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

    Testcases :
    Testcases are defined in the playbook dir, inside 'playbooks'
      ex : /fortipoc/playbooks/advpn/testcases

    Agents :
    Agents are defined in the playbook dir, inside 'conf'
      ex : /fortipoc/playbooks/advpn/conf/agents.json

    Variables : 
    (future implementation) list of variables defined in a json format which
    could be used withing testcases scenario (called with $name) :
      ex : { 'var1' : 'port1', 'var2' : 'internal' }}

    Flows :
    (future implementation) list of flows defined with protocol, src_ip,
    dst_ip, dest_port. Flows could be referenced in the scenario :
       ex :  { 'flow1' : { 'sip' : '10.0.1.1', 'dip' : '10.0.2.1', 'dport' : '80' }`}

    Macros :
    (future implementation) defines a block of scenario statements which can be
    called with some arguments and referenced in testcase to factories
    statements: to be determined...

    Runs : 
    A 'run' is a directory containing all traces from the last running playbook
    testcases. To keep track of several 'runs', directory has sub 'run'
    directories numbered 1,2,3,4... Before running a playbook, user should tell
    on which run id it should be run.
      ex : /fortipoc/playbooks/advpn/run/1

    Reports :
       * By testcase :
       When a playbook is processed, a reports in a json format are being generated
       in the run/run_id subdirectory.  One report per testcase name : "<id>_report.json"
       This report contains feedback from all the different checks and gets in
       from the testcases.
         ex : /fortipoc/playbooks/advpn/run/1/1_report.json

       * Summary report :
       Once all testcases from the workbook have run, it is possible to
       generate a summary report for all testcases compiling the general
       feedback from each testcase (without getting to the details of all
       checks done in the testcase.
         ex : /fortipoc/playbooks/advpn/run/1/Summary_report.json
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
        self.agents_connections = {}  # SSH connection handle to agents key is agent name
                                      # ex : {'lxc1' : { '1' : SSH1, '2' : SSH2} }

    def register(self):
        """
        Load the playbook testcases references
        Does not load the testcases scenario
        Directory contains all testcases (one file per testcase)
        Arguments:
            - path : path the playbook store (directory)
            - playbook : name of the playbook to run (a subdirectory)
        Load the agents definitions
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
        self._load_agents()

    def get_agents(self):
        """
        Requirements : previous call to load_agents
        Returns : agents json format
        """
        log.info("Enter")
        return json.dumps(self.agents, indent=4)

    def verify_agents(self):
        """
        Requirements : playbooks should be registered
        Verifies the selected testcases have all the required agents loaded to
        run
        """
        log.info("Enter")

        # Forces another call to register the used agent
        # This needs to be done as some testcase may have been disabled since
        # our initial load 
        self._register_used_agents

        result = True 
        for ua in self.testcases_agents:
            if ua not in self.agents:
                log.debug("Agent {} is missing to execute workbook".format(ua))
                result = False

        return result


    def run(self, run=None):
        """
        Requirements : playbook should have been registered (and ideally
        verify_agents)
        """
        log.info("Enter with run={}".format(run))
        for tc in self.testcases:
            log.debug("Run scenario id={} name={}".format(tc.id, tc.name))
            self.process_testcase(testcase=tc)

    def process_testcase(self, testcase=None):
        """
        Processes all statements from a given testcase :
        Process each line of the scenario, for each line :
            Extract the agent name, type and connection
        """
        log.info("Enter")
        log.debug("Testcase id={} name={}".format(testcase.id, testcase.name))

        for line in testcase.lines:
            log.debug("line={}".format(line))

            # Get agent name, type and connection_id
            (agent_name, agent_type, agent_conn) = self._get_agent_from_tc_line(id=testcase.id, line=line)
            log.debug("agent_name={} agent_type={} agent_conn={}".format(agent_name, agent_type, agent_conn))

            # Manage the connection to agent : if connection is not already open,
            # then open it
          
            if not agent_name in self.agents_connections:
               log.debug("create a new agent={} in our agents_connections dictionnary".format(agent_name))
               self.agents_connections[agent_name] = {}

            if not agent_conn in self.agents_connections[agent_name]:
                log.debug("Create a new connection conn={} for agent={}".format(agent_conn,agent_name))
                # TBD 

            else:
                log.debug("Connection conn={} already exists".format(agent_conn))


    ### PRIVATE METHODS ###

    def _get_agent_from_tc_line(self, id=None, line=""):
        """
        Returns a list (agent_name, agent_type, agent_connection) from the testcase line
        """
        log.info("Enter with id={} line={}".format(id, line))
        agent_name = ""  # taken from the line
        agent_conn = ""  # taken from the line
        agent_type = ""  # Extracted from agent file

        # Get agent name and connection id from the line
        match = re.search("(?:\s|\t)*(?P<agent>[A-Za-z0-9\-_]+)(?::)(?P<conn>\d+)",line)
        if match:
            agent_name = match.group('agent')
            agent_conn =  match.group('conn')
            log.debug("Found id={} agent={} conn={}".format(id, agent_name, agent_conn))

            # Get agent type from agent file
            agent_type = self.agents[agent_name]['type']
            log.debug("Found corresponding type={}".format(agent_type))

        else:
            log.debug("Could not find agent name and connection id={} line={}".format(id, line))
            print("warning: testcase id={} line={} : can't extract agent name and connection id (format NAME:ID)".format(id, line))


        return (agent_name, agent_type, agent_conn)






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

    def _load_agents(self):
        """
        Requirements : an agent file should exists
        Load all agents with their details from json file
        """
        log.info("Enter")

        dir = self.path+"/"+self.name+"/conf"
        file = self.path+"/"+self.name+"/conf/agents.json"
        
        # checks agent conf dir and json file exists
        if not (os.path.exists(dir) and os.path.isdir(dir)):
            print ("conf dir {} does not exist or is not a directory\n".format(dir))
            raise SystemExit

        if not (os.path.exists(file) and os.path.isfile(file)):
            print ("file agents.json does not exists ({})\n".format(file))
            raise SystemExit

        with open(file, encoding='utf-8') as F:
            self.agents = json.loads(F.read())

if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_testrunner.py\n")
