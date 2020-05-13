# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2020
@author: cgustave
"""

import logging as log
import os 
import glob
import re
import json
import time
import yaml
from pathlib import Path
from testcase import Testcase
from lxc_agent import Lxc_agent
from vyos_agent import Vyos_agent
from fortipoc_agent import Fortipoc_agent
from fortigate_agent import Fortigate_agent
from feedback import Feedback

class Playbook(object):
    """
    A Playbook is an ordered collection of Testcases.
    Playbooks are located in directory provided by path
    Each Testcase is identified from a number (id)

    Testcases :
    Testcases are defined in the playbook dir, inside 'playbooks'
      ex : /fortipoc/playbooks/advpn/testcases

    Agents :
    Agents are defined in the playbook dir, inside 'conf'
      ex : /fortipoc/playbooks/advpn/conf/agents.json

    Variables : 
    List of variables defined in a json format which
    could be used withing testcases scenario (called with $name) :
      ex : { 'var1' : 'port1', 'var2' : 'internal' }}
    Variables can be used in scenario files, between $ like : $myvar$ 

    Variables can also be  assigned within the scenario using statement 'set'.
    In this case, pre-defined functions can be used for assignment :
   
    - random_string(length) : random string generation 
      ex : set message = random_string(4)

    Macros :
    Defines a block of scenario statements which can be
    called with some arguments and referenced in testcase to factories
    statements. Macros are defined in file conf/macro.txt with statement
    'macro' with parameters, ending with statement 'end'. It is possible to
    define variables within macro (statique or dynamique), it is also possible
    to define variables translated into another variables using double
    $$variable$$ (see below). Example of conf/macro.txt :
    Note : in this example H1B2 (server agent) is also defined as variables,
           this allows statement : $$server$$ which triggers a double translation :
              1) $$server$$ -> $H1B2$   (translation from macro parameters)
              2) $H1B2$ -> 10.1.2.1     (translation from variables.json)

        # Macro for connectivity check, one-way
        # Uses a double-translation ($$server$$) so H1B2 need to be declared as a variables

        # example of call : &tcp_connectivity_check(H1B1,1,H1B2,1,9000)

        # Definition :
		macro tcp_connectivity_check(client,client_conn,server,server_conn,port):

		# create a random message
		set server_ready = random_string(8)
		set message = random_string(8)
		set test_id = random_string(4)

		# Open server on the given port
		$server$:$server_conn$ open tcp $port$
		mark "$server_ready$"

		# Client connects
		$client$:$client_conn$ connect tcp $$server$$ 9000

		# Client send data on forward direction
		$client$:$client_conn$  send "$message$"

		# Server checks message is received
		$server$:$server_conn$ check [tcp_forward_$test_id$] "$message$" since "$server_ready$"

        # Closing
        $client$:$client_conn$ close
        $server$:$server_conn$ close
		end

    Runs : 
    A 'run' is a directory containing all traces from the last running playbook
    testcases. To keep track of several 'runs', directory has sub 'run'
    directories numbered 001,002,003,004 so they can be sorted alphatically.
    Before running a playbook, user should tell on which run id it should be run.
      ex : /fortipoc/playbooks/advpn/run/1

    Reports :
       * By testcase :
       When a playbook is processed, a reports in a json format are being generated
       in the run/run_id subdirectory.  One report per testcase name : "<id>_report.json"
       This report contains feedback from all the different checks and gets in
       from the testcases.
         ex : /fortipoc/playbooks/advpn/run/1/001_report.json

       * Summary report :
       When testcases are run, a report file is kept updated.
         ex : /fortipoc/playbooks/advpn/run/1/report.json

    Feedback : if --feedback provided, expects feedback on this file
    """

    def __init__(self, name='', path='', run=1, dryrun=False, feedback=None, debug=False):

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

        log.info("Constructor with name={} path={} run={} dryrun={} feedback={} debug={}".
                 format(name, path, run, dryrun, feedback, debug))

        # Attributs
        self.name = name
        self.path = path
        self.run = run                # Run id
        self.feedback = feedback
        self.macros = {}              
        self.variables = {}           
        self.playlists = {}           # Dictionary of our playlists (from conf/)
        self.testcases = []           # List of testcase objects
        self.testcases_agents = []    # List of agents used in the testcases
        self.testcases_list = []      # List of registered testcase id
        self.nb_testcases = 0  
        self.agents = {}              # Dictionnary of agents loaded from json file conf/agents.json
        self.agents_connections = {}  # SSH connection handle to agents key is agent name
                                      # ex : {'lxc1' : { '1' : <agent_object>, '2' : <agent_object>} }
        self.dryrun = dryrun          # Used for scenario syntax verification only (no connection to agent)
        self.report = {}              # Playbook test report, key is testcase id
        self.report_summary = True    # Overall report summary, to be updated after each testcase

        # Private attributs
        self._FB = None               # Feedback file object, to be instanciated only if feedback path was given
    
    def register(self):
        """
        Load config files and load the playbook testcases references
        Does not load the testcases scenario
        Directory contains all testcases (one file per testcase)
        Arguments:
            - path : path the playbook store (directory)
            - playbook : name of the playbook to run (a subdirectory)
        Load the agents definitions
        """
        log.info("Enter")

        # Load our json files and macro (order variables/macros matters)
        self._load_conf_yaml(name='agents')
        self._load_conf_yaml(name='variables')
        self._load_conf_yaml(name='playlists')
        self._load_macros()

        nb = 0
        for filename in sorted(os.listdir(self.path+"/"+self.name+"/testcases")):
            nb=nb+1
            log.debug("listdir : nb={} filename={}".format(nb, filename))
            
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

    def get_agents(self):
        """
        Requirements : Agent file should have been loaded
        Returns : agents in json format
        """
        log.info("Enter")
        return json.dumps(self.agents, indent=4)

    def get_variables(self):
        """
        Requirements : variables file should have been loaded
        Returns : variables in json format
        """
        log.info("Enter")
        return json.dumps(self.agents, indent=4)

    def get_playlists(self):
        """
        Requirements : playlists file should have been loaded
        Returns : playlists in json format
        """
        log.info("Enter")
        return json.dumps(self.playlists, indent=4)

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

    def prepare_feedback(self):
        """
        Preparation for feedback file to be called before running tests
        Create path if needed
        Delete old file if needed
        Write initial information
        """
        log.info("Enter")

        if self.feedback:

            # Create path if needed
            path = self.path+"/"+self.name+"/runs/"+str(self.run)
            p = Path(path)
            try:
                p.mkdir(parents=True)
            except:
                log.debug("path already created")

            # Delete old feedback file if needed
            if os.path.isfile(self.feedback):
                log.debug("delete old feedback file")
                os.remove(self.feedback)

            # Write initial lines
            log.debug("feedback required on file={}".format(self.feedback))
            self._FB = Feedback(filename=path+"/"+self.feedback, debug=self.debug)
            self._FB.delete()
            self._FB.write(key="playbook_path", value=self.path)
            self._FB.write(key="playbook", value=self.name)
            self._FB.write(key="run", value=self.run)
            self._FB.write(key="start_time", value=(int(time.time())))

        else:
            log.debug("no feedback required")


    def run_testcases(self, id=None):
        """
        Requirements : playbook should have been registered (and ideally verify_agents)
        run attributs should be set
        Optional : testcase id (if none provided, all testcases are run)
        """
        log.info("Enter with id={} (dryrun={})".format(id, self.dryrun))

        if not id:
            self.prepare_feedback()

        index = 0 
        for tc in self.testcases:
            index = index + 1
            if id:
                if tc.id != id:
                    continue

            log.debug("Run scenario index={} id={} name={}".format(index, tc.id, tc.name))

            # Progress
            if self.feedback:
                progress = int((index / self.nb_testcases) * 100)
                self._FB.write(key="progress", value=progress)

            self.run_testcase(testcase=tc)

        # Finish with a 100%
        if self.feedback and not id:
            self._FB.write(key="progress", value=100)
            self._FB.write(key="end_time", value=int(time.time()))


    def run_playlist(self, id=None):
        """
        Requirements : playbook should have been registered
        """
        log.info("Enter with id={} (dryrun={})".format(id, self.dryrun))

        self.prepare_feedback()

        if self.feedback:
            self._FB.write(key="playlist_id", value=id)

        if id not in self.playlists:
            print("Playlist id={} is unknown. Aborting".format(id))
            log.error("Playlist id={} is unknown".format(id))
            raise SystemExit
          
        log.debug("playlist {} = {}".format(id,self.playlists[id]))

        nb_testcases = len(self.playlists[id]['list'])

        index = 0 
        for tc_id in self.playlists[id]['list']:
            index = index + 1
            log.debug("index={} processing tc_id={}".format(index, tc_id))
            if tc_id in self.testcases_list:
                log.debug("Playlist - Run testcase id={}".format(tc_id))
                self.run_testcases(id=tc_id)
                time.sleep(1)
            else:
                log.error("Playlist references an unknown testcase id={}".format(tc_id))
                raise SystemExit

            # Progress
            if self.feedback:
                progress = int((index / nb_testcases) * 100)
                self._FB.write(key="progress", value=progress)

        # Make sure to finish with a 100%
        if self.feedback:
            self._FB.write(key="progress", value=100)
            self._FB.write(key="end_time", value=int(time.time()))


    def run_testcase(self, testcase=None):
        """
        Run one testcase.
        Attribute : a testcase object
        Process each line of the scenario, for each line :
          - extract agent name and connection, create a new agent if first time seen
          - call generic processing (same for all agent), from agent.py
          - call agent specific processing
        """
        log.info("Enter with Testcase id={} name={} (dryrun={})".format(testcase.id, testcase.name, self.dryrun))
        print("* Starting {} - {}".format(testcase.id, testcase.name)) 

        # remove old run logfiles and create run filestructure if needed
        self._create_testcase_run_file_structure(testcase_id=testcase.id)

        if self.feedback:
            self._FB.write(key='testcase_id', value=testcase.id)
            self._FB.write(key='testcase_name', value=testcase.name)

        index = 0
        for line in testcase.lines:
            index = index + 1
            log.debug("index={} testcase line={}".format(index, line))

            # Progress
            if self.feedback:
                progress = int(index  / testcase.nb_lines * 100)
                self._FB.write(key='testcase_progress', value=progress)

            # Get agent name, type and connection_id
            (agent_name, agent_type, agent_conn) = self._get_agent_from_tc_line(id=testcase.id, line=line)
            log.debug("agent_name={} agent_type={} agent_conn={}".format(agent_name, agent_type, agent_conn))

            # Deal with 'message', 'skip all'
            if agent_type == "generic" and agent_name == "continue":
                log.debug("Generic agent, no more processing needed")
                continue

            if  agent_type == "generic" and agent_name == "skipall":
                log.debug("Generic agent, skipall request")
                break

            if agent_type == "generic" and agent_name == "wait":
                log.debug("Generic agent, wait request")
                self._process_wait(line=line)
                continue

            # Create new agent connection if needed
            if self._create_agent_conn(name=agent_name, type=agent_type, conn=agent_conn):
                log.debug("Agent created")
            else:
                log.debug("Agent already existing")

            # Double check
            if agent_name in self.agents_connections:
                log.debug("Agent check OK : agent_name={} Agents keys={}".format(agent_name, self.agents_connections.keys()))

            if agent_conn in self.agents_connections[agent_name]:
                log.debug("Agent connection check ok : agent_name={} dict={}".format(agent_name, self.agents_connections[agent_name].keys()))
            else:
                log.error("ERROR: Agent connection {}:{} does not exists".format(agent_name, agent_conn))
                raise SystemExit 

            # Proceed with Agent specific command line
            # feed agent attributs
            self.agents_connections[agent_name][agent_conn].path = self.path
            self.agents_connections[agent_name][agent_conn].playbook = self.name
            self.agents_connections[agent_name][agent_conn].run = self.run
            self.agents_connections[agent_name][agent_conn].testcase = testcase.id 

            # Tell agent who it is and for which testcase it has been created 
            self.agents_connections[agent_name][agent_conn].agent = self.agents[agent_name]

            # Provide report for update
            self.agents_connections[agent_name][agent_conn].report = self.report 
   
            # Run generic methods (in agent.py) and specific ones
            if not self.dryrun:
                translated_line = self.agents_connections[agent_name][agent_conn].process_generic(line=line)
                self.agents_connections[agent_name][agent_conn].process(line=translated_line)
            else:
                log.debug("dryrun - don't run agent_name={} agent_conn={} line={}".
                          format(agent_name,agent_conn,line))

        # Terminate testcase progress with a 100%
        if self.feedback:
            self._FB.write(key='testcase_progress', value=100)

        # Disconnect all agent (and closed the tracefile)
        self.disconnect_agents()

    def disconnect_agents(self):
        """
        Go through all agent in our connection list,
        disconnect and close the trace file
        """
        log.info("Enter")

        for agent in self.agents_connections:
            for conn in self.agents_connections[agent]:
                if not self.dryrun:
                    self.agents_connections[agent][conn].close()

        # Empty our list for next testcase
        self.agents_connections = {}

    ### PRIVATE METHODS ###

    def _get_agent_type(self, name=""):
        """
        Requirement : Agents should have been loaded
        Returns the type of the agent called 'name'
        """
        log.info("Enter with name={}".format(name))

        if name not in self.agents:
            log.error("Unknown agent name {}".format(name))
            raise SystemExit

        type = self.agents[name]['type']
        log.debug("name={} type={}".format(name, type))
        return type


    def _create_agent_conn(self, name="", type="", conn=None):
        """
        Creates a new agent object in our agent list 
        Returns True if connection creation was required
        Return False if connection was already existing 
        """
        log.info("Enter with name={} type={} conn={}".format(name, type, conn))

        result = False

        # step 1: If agent is not in our dictionary, create it
          
        if not name in self.agents_connections:
            log.debug("Create a new agent={} in our agents_connections dictionnary".format(name))
            self.agents_connections[name] = {}
        else: 
            log.debug("agent={} is already in our list".format(name))

        # step 2 : If agent object is not created for this connection id, create it

        if not conn in self.agents_connections[name]:
            log.debug("Create a new connection {}:{} type={}".format(name, conn, type))
            result = True

            if type == "lxc":
                self.agents_connections[name][conn] = Lxc_agent(name=name, conn=conn, dryrun=self.dryrun, debug=self.debug)
            elif type == "vyos":
                self.agents_connections[name][conn] = Vyos_agent(name=name, conn=conn, dryrun=self.dryrun, debug=self.debug)
            elif type == "fortipoc":
                self.agents_connections[name][conn] = Fortipoc_agent(name=name, conn=conn, dryrun=self.dryrun, debug=self.debug)
            elif type == "fortigate":
                self.agents_connections[name][conn] = Fortigate_agent(name=name, conn=conn, dryrun=self.dryrun, debug=self.debug)
            else:
                print ("Error: undefined type for agent {}".format(type))
                raise SystemExit
        else:
            log.debug("Connection to {}:{} already exists".format(name, conn))

        return result

    def _load_macros(self):
        """
        Load the macros.txt file from conf/
        """
        log.info("Enter")
        filename = self.path+"/"+self.name+"/conf/macros.txt"
        in_macro = False

        try:
            with open(filename) as file_in:
                for line in file_in:
                    line = line.strip()
                    ignore_line = False

                    if line == "":
                        continue
                    if (line[0] == "#"):
                        continue
                    log.debug("read line={}".format(line))
                    
                    match_macro_prototype = re.search("^(?:macro\s+)(?P<name>[A-Za-z0-9\-_]+)(?:\s*)\((?P<params>\S+)\)\:",line)
                    if match_macro_prototype and not in_macro:
                        in_macro = True
                        ignore_line = True
                        name = match_macro_prototype.group('name')
                        params = match_macro_prototype.group('params')
                        log.debug("Matched macro prototype register macro name={} params={}".format(name, params))

                        # register macro
                        self.macros[name] = {}
                        self.macros[name]['lines'] = []

                        # register params, sorted in a list
                        self.macros[name]['params'] = []
                        for p in params.split(','):
                            log.debug("Params={}".format(p))
                            self.macros[name]['params'].append(p)

                    match_macro_end = re.search("^end",line)
                    if match_macro_end and in_macro:
                        in_macro = False
                        ignore_line = True
                        log.debug("Matched end of macro")

                    # Expands macro lines but ignore proto line and end
                    if in_macro and not ignore_line:
                        log.debug("Add line in macro line={}".format(line))
                        self.macros[name]['lines'].append(line)

        except IOError as e:
            log.warning("I/O error filename={} error={}".format(filename,e.strerror))



    def _load_conf_yaml(self, name=''):
        """
        Generic method to load conf yamel files
        """
        log.info("Enter with name={}".format(name))

        # Sanity
        if name not in ['agents', 'variables', 'playlists']:
            log.error("name is not allowed")
            raise SystemExit

        dir = self.path+"/"+self.name+"/conf"
        file = self.path+"/"+self.name+"/conf/"+name+".yml"
        
        # checks conf dir and yml file exists
        if not (os.path.exists(dir) and os.path.isdir(dir)):
            print ("conf dir {} does not exist or is not a directory\n".format(dir))
            raise SystemExit

        if not (os.path.exists(file) and os.path.isfile(file)):
            print ("warning : file {}.yml does not exists ({})\n".format(name,file))
        else :
            log.debug("Loading {}".format(name))
            with open(file, encoding='utf-8') as V:
                if name=="playlists":
                   self.playlists = yaml.safe_load(V.read())
                elif name=="variables":
                    self.variables =yaml.safe_load(V.read())
                elif name=="agents":
                    self.agents =  yaml.safe_load(V.read())
            V.close() 

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
        # Identify the 'message' command
        match_message = re.search("(\s|\t)*(?:message)(\s|\t)+(?:\")(?P<message>.+)(?:\")",line)
        # Identify the 'skip all' command
        match_skip_all = re.search("(\s|\t)*(?:skip all)",line)
        # Identify the 'wait' command
        match_wait = re.search("(\s|\t)*(?:wait)",line)
        # Identify 'set' variable assignment
        match_set = re.search("^set",line)

        if match:
            agent_name = match.group('agent')
            agent_conn =  match.group('conn')
            log.debug("Found id={} agent={} conn={}".format(id, agent_name, agent_conn))

            # Get agent type from agent file
            agent_type = self._get_agent_type(name=agent_name) 
            log.debug("Found corresponding type={}".format(agent_type))

        elif match_message:
            message = match_message.group('message')
            log.debug("message={}".format(message))
            agent_name = "continue"
            agent_type = "generic"
            agent_conn = "0"
            print("  {}".format(message))

        elif match_skip_all:
            log.debug("Requested to skip further lines from the testcase")
            agent_type = "generic"
            agent_name = "skipall"
            agent_conn = "0"

        elif match_wait:
            log.debug("wait request")
            agent_type = "generic"
            agent_name = "wait"
            agent_conn = "0"

        elif match_set:
            log.debug("set command")
            agent_type = "generic"
            agent_name = "continue"
            agent_conn = "0"

        else:
            log.debug("Could not find agent-less command or agent name and connection id={} line={}".format(id, line))
            print("warning: testcase id={} line={} : can't extract agent name and connection id (format NAME:ID)".format(id, line))
        return (agent_name, agent_type, agent_conn)


    def _register_testcase(self, id, name, filename):
        """
        Register one testcase from id and name
        """
        log.info("Enter with id={} name={} filename={}".format(id,name,filename))

        tc = Testcase(id=id, name=name, playbook=self.name, path=self.path,
                      filename=filename, macros=self.macros,
                      variables=self.variables)

        self.testcases_list.append(id)
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

    def _create_testcase_run_file_structure(self, testcase_id=None):
        """
        Delete any old run files and create the required file structure for a run
        ex : playbook_path/PLAYBOOK_NAME/runs/ID
        ex : playbook_path/PLAYBOOK_NAME/runs/ID/testcases 
        ex : playbook_path/PLAYBOOK_NAME/runs/ID/testcases/TESTCASE_ID

        Requirement: run id, playbook name
        """
        log.info("Enter with testcase_id={}".format(testcase_id))

        if not testcase_id:
            log.error("testcase_id is required")
            raise SystemExit

        if not self.path:
            log.error("playbook path is required")
            raise SystemExit

        if not self.name:
            log.error("playbook name is required")
            raise SystemExit

        if not self.run:
            log.error("run id is required")
            raise SystemExit
        
        path = self.path+"/"+self.name+"/runs/"+str(self.run)+"/testcases/"+str(testcase_id)
        log.debug("Create if needed path={}".format(path))
        p = Path(path)
        try:
            p.mkdir(parents=True)
        except:
            log.debug("path already created")

        old_run_logs = path+"/*.log"
        if os.path.exists(path):
            filelist = glob.glob(old_run_logs)
            for f in filelist:
                log.debug("Delete old run {} log file {}".format(self.run, f))
                os.remove(f)


    def _process_wait(self, line=""):
        """
        Wait for the given number of seconds
        """
        log.info("Enter with line={}".format(line))
        match = re.search("(\s|\t)*(?:wait)(\s|\t)+(?P<seconds>\d+)",line)
        if match:
            seconds = match.group('seconds')
            log.debug("seconds={}".format(seconds))
            if not self.dryrun:
                log.debug("Start sleeping for {} seconds...".format(seconds))
                time.sleep(int(seconds))
                log.debug("End sleeping, resuming")
        else:
            log.debug("could not extract seconds to wait")
            raise SystemExit


if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_checkitbaby.py\n")
