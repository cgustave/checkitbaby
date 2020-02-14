# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2019
@author: cgustave

"""

import logging as log
import os

class Testcase(object):
    """
    Testcase class
    """

    def __init__(self, id='', name='', workbook='', path='', debug=False):

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

        log.info("Constructor with id={} name={} workbook={} path={} debug={}".format(id, name, workbook, path, debug))

        # Attributs
        self.id = id
        self.name = name
        self.workbook = workbook
        self.path = path
        self.lines= []      

        self.load_statements()

    def load_statements(self):
        """
        Load the testcase statements
        """
        log.info("Enter")

if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_testrunner.py\n")

