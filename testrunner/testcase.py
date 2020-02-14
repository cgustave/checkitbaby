# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2019
@author: cgustave

"""

import logging as log
import re


class Testcase(object):
    """
    Testcase class
    """

    def __init__(self, id='', name='', playbook='', path='', filename='', debug=False):

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

        log.info("Constructor with id={} name={} playbook={} path={} \
                 filename={} debug={}".format(id, name, playbook, path, filename, debug))

        # Attributs
        self.id = id
        self.name = name
        self.playbook = playbook
        self.path = path
        self.filename = filename

        self.lines = []      
        self.state = True
        self.agents = []    # list of agents used in the scenario

        # Run
        self.load_scenario()

    def load_scenario(self):
        """
        Load the testcase statements
        """
        log.info("Enter")
        filename = self.path+"/"+self.playbook+"/testcases/"+self.filename

        try:
            with open(filename) as file_in:
                for line in file_in:
                    line = line.strip()
                    if line == "":
                        continue
                    if (line[0] == "#"):
                        continue
                    log.debug("read line={}".format(line))
                    self.lines.append(line)

                    # Extract agents and add in our list if needed
                    match = re.search("(?:\s|\t)*(?P<agent>[A-Za-z0-9\-_]+)",line)
                    if match:
                        agent = match.group('agent')
                        if agent not in self.agents:
                            log.debug("Found a new agent={}".format(agent))
                            self.agents.append(agent)

        except IOError as e:
            log.debug("I/O error filename={} error={}".format(filename,e.strerror))


    def disable(self):
        """
        Disable a testcase (won't be selected to run)
        """
        log.info("Enter")
        self.state = False

    def enable(self):
        """
        Enable a testcase (will be selected to run)
        """
        log.info("Enter")
        self.state = True

if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_testrunner.py\n")

