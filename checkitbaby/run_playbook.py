# -*- coding: utf-8 -*-
'''
Created on Feb 14, 2020

@author: cgustave
'''
import logging as log
import sys, getopt
from checkitbaby import Checkitbaby

def main(argv):

    # Default values
    playbook = None
    playlist = ''
    testcase = ''
    run = 1
    dryrun = False 
    debug = False

    try:
        opts, args = getopt.getopt(argv,"hp:trd", ["playbook=","playlist=","testcase=", "run=", "dryrun", "debug"])
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)
    
    for opt,arg in opts:
        if opt in ("-h", "--help"):
            print_usage()
            sys.exit()
        elif opt in ("-p", "--playbook"):
            playbook = arg
        elif opt in ("-t", "--testcase"):
            testcase = arg
        elif opt in ("--playlist"):
            playlist = arg
        elif opt in ("-r", "--run"):
            run = arg
        elif opt == '--dryrun':
            dryrun=True
        elif opt == '--debug':
            debug=True

    # create logger
    if debug:
        log_level = log.DEBUG
    else:
        log_level = log.INFO
        
    log.basicConfig(
        format='%(asctime)s,%(msecs)3.3d %(levelname)-8s[%(module)-10.10s.\
        %(funcName)-20.20s:%(lineno)5d] %(message)s',
        datefmt='%Y%m%d:%H:%M:%S',
        filename='debug.log',
        level=log_level)

    log.info("Starting run_playbook.py with playbook={} playlist={} testcase={} run={}".format(playbook,playlist,testcase,run))
    
    cib = Checkitbaby(path='./playbooks', debug=debug)
    cib.load_playbook(name=playbook, dryrun=dryrun)

    if testcase:
        print ("Running playbook {}, testcase {} only on run {}".format(playbook, testcase, run))
        cib.run_testcase(run=run, id=testcase)
    elif playlist:
        print ("Running playbook {}, playlist {} on run {}".format(playbook, playlist, run))
        cib.run_playlist(run=run, id=playlist)
    else:
        print ("Running all playbook {} on run {}".format(playbook, run))
        cib.run_all_testcases(run=run)

    # Print report
    print("report={}".format(cib.run_report()))


def print_usage():

    print("Usage: python3 run_playbook.py -playbook <playbookName>\n")
    print("Optional settings:\n")
    print("    --playlist <playlist_id>")
    print("    --testcase <tescase_id>")
    print("    --run <run_id>")
    print("    --dryrun")
    print("    --debug")


if __name__ == "__main__":
       main(sys.argv[1:])
