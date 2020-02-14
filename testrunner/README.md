Help on module testrunner:

NAME
    testrunner

DESCRIPTION
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

CLASSES
    builtins.object
        Testrunner
    
    class Testrunner(builtins.object)
     |  Testrunner(path='/fortipoc/playbooks', debug=False)
     |  
     |  Main application. 
     |  
     |  #### A testrunner contains :
     |      - mutliple test agents with their definitions
     |      - a single playbook containing the testcases
     |      - a report structure filled from the testcases when run
     |  
     |  It is called with:
     |      - a base path for the playbook
     |      - a debug level  
     |  
     |  #### Directory structure:
     |      - /PLAYBOOK_BASE_PATH : The base name of the playbook location
     |      ex : /fortipoc/playbooks
     |  
     |     * /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME
     |     ex : /fortipoc/playbooks/advpn
     |  
     |     * /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/conf : configuration directory
     |  
     |          - /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/conf/agents.json  : files with agents definitions in json format
     |          ex : /fortipoc/playbooks/advpn/conf/agents.json
     |  
     |          - /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/conf/variables.json : file defining all variables in json format 
     |  
     |     * /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/testcases    : directory containing testcases
     |     ex : /fortipoc/playbooks/advpn/testcases
     |  
     |          - /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/testcases/NNN_TESTCASE_NAME : one testcase file
     |          with NNN : a number starting from 0 (used as testcase index)
     |          TESTCASE_NAME : any name for the testcase
     |  
     |           ex : /fortipoc/playbooks/advpn/testcases/1_environment.txt
     |           ex : /fortipoc/playbooks/advpn/testcases/2_connectivity.txt
     |           ex : /fortipoc/playbooks/advpn/testcases/3_ipsec_tunnels.txt
     |           ex : /fortipoc/playbooks/advpn/testcases/4_routing.txt
     |  
     |     * /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/runs   : directory for all runs
     |     ex : /fortipoc/playbooks/advpn/runs
     |  
     |          - /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/runs/1 : directory for run number 1 
     |          ex : /fortipoc/playbooks/advpn/runs/1
     |  
     |          - /PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/runs/1/report.json : report from run 1
     |  
     |  #### Internal attributs schemes
     |  
     |     * self.playbook
     |  
     |  Methods defined here:
     |  
     |  __init__(self, path='/fortipoc/playbooks', debug=False)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |  
     |  get_agents(self)
     |      Requirements : previous call to load_agents
     |      Returns : agents json format
     |  
     |  get_playbook(self)
     |      Requirements : previous call to load_playbook
     |      Returns : playbook in json format
     |  
     |  get_variables(self)
     |      Requirements : previous call to load_variables
     |      Returns : testcase variables in json format
     |  
     |  load_agents(self)
     |      Load all agents with their details from json file
     |  
     |  load_playbook(self, name='')
     |      Loads a playbook as a first element of list self.playbook
     |  
     |  load_variables(self)
     |      Load all variables used in the testcase taken from json file format
     |      variables.json
     |  
     |  report(self, run='1')
     |      Requirement : a minimum of a testcase should have been run on the given run id
     |      Provide a report from the last testcases that ran in run 1
     |      Return: Report in json format
     |  
     |  run_all(self)
     |      Runs the full playbook testcases
     |  
     |  run_testcase(self, run, id)
     |      Runs a single testcase specified by its id
     |      Returns True in no exception is caught
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)

FILE
    /home/cgustave/github/python/testrunner/testrunner/testrunner.py


