# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2020
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
"""

import logging as log
import json
import os
from playbook import Playbook

class Checkitbaby(object):
    """
    Main application. This is the interface with the user.
    Defines the global settings
    Provides a playbook name to run
    Registers the playbook testcases (load the testcases from the given
    playbook). Allows to enable/disable some of the testcases.
    Runs a playbook
    Provide feedback

    Contains :
        - a single playbook object (containing the testcases, agents...)
        - a run id 

    It is called with:
        - a base path for the playbook
        - a debug level  

    Directory structure:
        - /PLAYBOOK_BASE_PATH : The base name of the playbook location
          ex : /fortipoc/playbooks

    """

    def __init__(self, path="/fortipoc/playbooks", feedback=None, debug=False):

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

        if not (os.path.exists(path) and os.path.isdir(path)):
            print ("path does not exist or is not a directory\n")
            raise SystemExit

        log.info("Constructor with path={}, debug={}".
                 format(path, debug))

        # Attributs
        self.run = None                              # the run id identifier
        self.playbook = None                         # Playbook object instance 
        self.path = path                             # base path of the playbook store 
        self.dryrun = False                          # Dryrun won't connect to any device
        self.feedback = feedback                     # Feedback file

    def load_playbook(self, name='', dryrun=False):
        """
        Loads a playbook as a first element of list self.playbook 
        """
        log.info("Enter with name={} dryrun={}".format(name, dryrun))
        self.dryrun = dryrun
        self.playbook = Playbook(name=name, path=self.path, feedback=self.feedback, dryrun=dryrun, debug=self.debug)
        self.playbook.register()

    def get_playbook(self):
        """
        Requirements : previous call to load_playbook
        Returns : playbook in json format
        """
        log.info("Enter")
        return json.dump(self.playbook, indent=4)

    def run_all_testcases(self, run=None):
        """
        Runs the full playbook testcases on the given run id
        """
        log.info("Enter with run={} (dry-run={})".format(run, self.dryrun))
        self.playbook.run = run
        self.playbook.run_testcases()

    def run_testcase(self, run, id, feedback=None):
        """
        Runs a single testcase specified by its id
        Returns True in no exception is caught
        """
        log.info("Enter with run={} id={}".format(run, id))
        self.playbook.run = run
        self.playbook.run_testcases(id=id)
  
    def run_playlist(self, run, id):
        """
        Runs a playlist specified by its id
        Playlist should be defined in conf/playlists.conf 
        and should reference existing testcases
        """
        log.info("Enter with run={} id={}".format(run, id))
        self.playbook.run = run
        self.playbook.run_playlist(id=id)

    def run_report(self, run='1'):
        """
        Requirement : a minimum of a testcase should have been run on the given run id
        Provide a report from the last testcases that ran in run 1
        Return: Report in json format
        """
        log.info("Enter with run={}".format(run))
        return json.dumps(self.playbook.report, indent=4)


if __name__ == '__main__': #pragma: no cover

    # Instanciate Checkitbaby using playbook directory ./playbook
    trun = Checkitbaby(path='./playbooks', debug=True)

    # Load a playbook
    trun.playbook(Playbook(debug=True))

    # Load test agents details
    trun.load_agents()

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

