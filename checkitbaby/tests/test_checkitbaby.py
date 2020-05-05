# -*- coding: utf-8 -*-
'''
Created on Feb 14, 2020

@author: cgustave
'''
import logging as log
import unittest
import json
from checkitbaby import Checkitbaby

# create logger
log.basicConfig(
    format='%(asctime)s,%(msecs)3.3d %(levelname)-8s[%(module)-10.10s.\
    %(funcName)-20.20s:%(lineno)5d] %(message)s',
    datefmt='%Y%m%d:%H:%M:%S',
    filename='debug.log',
    level=log.DEBUG)

log.debug("Start unittest")

class CheckitbabyTestCase(unittest.TestCase):

    # Always run before any test
    def setUp(self):
        self.tr = Checkitbaby(path='./playbooks', debug=True)

    #@unittest.skip  # no reason needed
    def test_loading(self):

        # Load the given playbook testcases 
        self.tr.load_playbook(name="test")

        # Disable / Enable some of the testcases
        self.tr.playbook.testcases[0].disable()
        self.tr.playbook.testcases[0].enable()

        # verify the playbook : 
        print ("Loaded agents list: \n{}".format(self.tr.playbook.get_agents()))
        # Check if the required agents are defined for the enabled testcases 
        if self.tr.playbook.verify_agents():
            print ("All agents required for selected testcases are defined\n")
        else:
            print ("Missing some agents to run selected testcases\n") 
        self.assertEqual(self.tr.playbook.nb_testcases,5)

    #@unittest.skip  # no reason needed
    def test_dryrun_playbook(self):
        self.tr.load_playbook(name="test", dryrun=True)
        self.tr.run_all_testcases(run=1)

    #@unittest.skip
    # Run lxc test in local using 127.0.0.1 addresses
    def test_run_playbook_no_macro(self):
        self.tr.load_playbook(name="test", dryrun=False)
        self.tr.run_testcase(run=1,id='010')
        report = json.loads(self.tr.run_report())
        expected = {'result':True,'testcases':{'010':{'result':True,'check':{'origin':True,'reply':True},'get':{}}}}
        self.assertDictEqual(expected, report)

    # Run lxc test in local using 127.0.0.1 addresses
    #@unittest.skip
    def test_run_playbook_with_macro(self):
        self.tr.load_playbook(name="test", dryrun=False)
        self.tr.run_testcase(run=1,id='011')
        report = json.loads(self.tr.run_report())
        # Report contains dynamic parts, only test overall result
        result = report['result']
        self.assertTrue(result, True)

   



if __name__ == '__main__':
    unittest.main()






