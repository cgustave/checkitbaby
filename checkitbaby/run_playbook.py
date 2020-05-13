#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
Created on Feb 14, 2020

@author: cgustave
'''
import argparse
from checkitbaby import Checkitbaby

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run a test playbook')
    parser.add_argument('--path', metavar="path",help="playbook directory path", required=True)
    parser.add_argument('--playbook', metavar="name",help="playbook to select", required=True)
    parser.add_argument('--playlist', metavar="name", help="playlist to run from the playbook")
    parser.add_argument('--testcase', metavar="id", help="testcase to run from the playbook")
    parser.add_argument('--feedback', metavar="file", help="feedback file name (without path)")
    parser.add_argument('--run', metavar="id", help="run id", default='1')
    parser.add_argument('--dryrun',  help="dryrun mode", action="store_true", default=False)
    parser.add_argument('--debug', '-d', help="turn on debug", action="store_true")
    args = parser.parse_args()

    cib = Checkitbaby(path=args.path, feedback=args.feedback, debug=args.debug)
    cib.load_playbook(name=args.playbook, dryrun=args.dryrun)

    if args.testcase:
        print ("Running playbook {}, testcase {} only on run {}".
               format(args.playbook, args.testcase, args.run))
        cib.run_testcase(run=args.run, id=args.testcase, feedback=args.feedback)

    elif args.playlist:
        print ("Running playbook {}, playlist {} on run {}".
               format(args.playbook, args.playlist, args.run))
        cib.run_playlist(run=args.run, id=args.playlist)
    else:
        print ("Running all playbook {} on run {}".
               format(args.playbook, args.run))
        cib.run_all_testcases(run=args.run)

    # Print report
    print("report={}".format(cib.run_report()))
