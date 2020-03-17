# -*- coding: utf-8 -*-
'''
Created on Feb 14, 2020

@author: cgustave
'''
import logging as log
import sys
from checkitbaby import Checkitbaby

# create logger
log.basicConfig(
    format='%(asctime)s,%(msecs)3.3d %(levelname)-8s[%(module)-10.10s.\
    %(funcName)-20.20s:%(lineno)5d] %(message)s',
    datefmt='%Y%m%d:%H:%M:%S',
    filename='debug.log',
    level=log.DEBUG)

playbook = sys.argv[1]
testcase = None

if not playbook:
    print("Usage: ./run_playbook.py <playbookName> [<tescase_id>]")
    raise SystemExit

if (len(sys.argv)>2):
   testcase = sys.argv[2]
   print ("Running testcase {} only".format(testcase))

# Default Run id
run=1

log.info("Starting run_playbook.py with playbook={} run={}".format(playbook,run))

print("Running playbook {} on run {} [testcase {}]".format(playbook, run, testcase))
tr = Checkitbaby(path='./playbooks', debug=True)
tr.load_playbook(name=playbook, dryrun=False)

if testcase:
    tr.run_testcase(run=run, id=testcase)
    print("report={}".format(tr.run_report()))

else:
    tr.run_all_testcases(run=run)
    print("report={}".format(tr.run_report()))
