# -*- coding: utf-8 -*-
'''
Created on Feb 14, 2020

@author: cgustave
'''
import logging as log
import sys
from testrunner import Testrunner

# create logger
log.basicConfig(
    format='%(asctime)s,%(msecs)3.3d %(levelname)-8s[%(module)-10.10s.\
    %(funcName)-20.20s:%(lineno)5d] %(message)s',
    datefmt='%Y%m%d:%H:%M:%S',
    filename='debug.log',
    level=log.DEBUG)

playbook = sys.argv[1]
if not playbook:
    print("Usage: ./run_playbook.py <playbookName>")
    raise SystemExit

# Default Run id
run=1

log.info("Starting run_playbook.py with playbook={} run={}".format(playbook,run))

#print("Running dry-run for playbook {} on run {}".format(playbook, run))
#dr = Testrunner(path='./playbooks', debug=True)
#dr.load_playbook(name=playbook, dryrun=True)
#dr.run_all_testcases(run=run)

print("Running playbook {} on run {}".format(playbook, run))
tr = Testrunner(path='./playbooks', debug=True)
tr.load_playbook(name=playbook, dryrun=False)
tr.run_all_testcases(run=run)

print("report={}".format(tr.run_report()))

