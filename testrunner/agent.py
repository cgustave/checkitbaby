# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2019
@author: cgustave
"""
import logging as log

class Agent(object):
    """
    Generic Agent class inherited by all specific agents
    """

    def __init__(self, name='', debug=False):
        """
        Constructor
        """
        
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

        log.info("Constructor with name={} debug={}".format(name, debug))

        self.name = None


    def process(self, line=""):
        """
        Generic line processing for agents
        This method could be overwritten in the specific agent
        """
        log.info("Enter with line={}".format(line))


if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_testrunner.py\n")

     


