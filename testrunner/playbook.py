 # -*- coding: utf-8 -*-
"""
Created on Feb 12, 2019
@author: cgustave

This package provides class Playbook

"""

import logging as log

class Playbook(object):
    """
    A Playbook is an ordered collection of Tescases.
    Each Testcase is identified from a number (id)
    """

    def __init__(self, debug=False):

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


        log.info("Constructor with debug={}".format(debug))


        # Attributs





if __name__ == '__main__': #pragma: no cover

    pb = Playbook(debug=True)


