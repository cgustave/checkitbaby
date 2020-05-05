Help on module checkitbaby:

NAME
    checkitbaby

DESCRIPTION
    Created on Feb 12, 2019
    @author: cgustave
    
    This package provides main class Checkitbaby
    
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
        Checkitbaby
    
    class Checkitbaby(builtins.object)
     |  Checkitbaby(path='/fortipoc/playbooks', debug=False)
     |  
     |  Main application. This is the interface with the user.
     |  Defines the global settings
     |  Provides a playbook name to run
     |  Registers the playbook testcases (load the testcases from the given
     |  playbook). Allows to enable/disable some of the testcases.
     |  Runs a playbook
     |  Provide feedback
     |  
     |  Contains :
     |      - a single playbook object (containing the testcases, agents...)
     |      - a run id 
     |  
     |  It is called with:
     |      - a base path for the playbook
     |      - a debug level  
     |  
     |  Directory structure:
     |      - /PLAYBOOK_BASE_PATH : The base name of the playbook location
     |        ex : /fortipoc/playbooks
     |  
     |  Methods defined here:
     |  
     |  __init__(self, path='/fortipoc/playbooks', debug=False)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |  
     |  get_playbook(self)
     |      Requirements : previous call to load_playbook
     |      Returns : playbook in json format
     |  
     |  load_playbook(self, name='', dryrun=False)
     |      Loads a playbook as a first element of list self.playbook
     |  
     |  run_all_testcases(self, run=None)
     |      Runs the full playbook testcases on the given run id
     |  
     |  run_playlist(self, run, id)
     |      Runs a playlist specified by its id
     |      Playlist should be defined in conf/playlists.conf 
     |      and should reference existing testcases
     |  
     |  run_report(self, run='1')
     |      Requirement : a minimum of a testcase should have been run on the given run id
     |      Provide a report from the last testcases that ran in run 1
     |      Return: Report in json format
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
    /home/cgustave/github/python/packages/checkitbaby/checkitbaby/checkitbaby.py


