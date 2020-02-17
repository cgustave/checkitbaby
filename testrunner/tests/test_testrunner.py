# -*- coding: utf-8 -*-
'''
Created on Feb 14, 2020

@author: cgustave
'''
import logging as log
import json
import unittest
from testrunner import Testrunner
from playbook import Playbook

# create logger
log.basicConfig(
    format='%(asctime)s,%(msecs)3.3d %(levelname)-8s[%(module)-10.10s.\
    %(funcName)-20.20s:%(lineno)5d] %(message)s',
    datefmt='%Y%m%d:%H:%M:%S',
    filename='debug.log',
    level=log.DEBUG)

log.debug("Start unittest")

class TestrunnerTestCase(unittest.TestCase):

    # Always run before any test
    def setUp(self):
        self.tr = Testrunner(path='./playbooks', debug=True)

    def test_loading(self):

        # Load the given playbook testcases 
        self.tr.load_playbook(name="myPlaybook")

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

        #self.assertEqual(self.tr.playbook.nb_testcases,2)


    def test_run_playbook(self):
        self.tr.load_playbook(name="myPlaybook")
        self.tr.run_all_testcases(run=1)



if __name__ == '__main__':
    unittest.main()






