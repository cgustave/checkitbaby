# -*- coding: utf-8 -*-
"""
Created on May 13, 2020
@author: cgustave
"""
import logging as log
import os
import sys
import datetime

class Feedback(object):
    """
    A class to manage feedback file from checkitbaby testsuite
    """

    def __init__(self, filename='', debug=False):
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
        else:
            self.debug = False
            log.basicConfig(level='ERROR')

        # Sanity
        if not filename:
            log.error("filename is required")
            raise SystemExit


        # Attributs
        self._FILE = None
        self.filename = filename
        self.is_opened = False


    def write(self,key='',value=''):
        """
        Write a key/value paire in feedback file
        Each time, file need to be opened, then closed
        """
        log.info("Enter with key={} value={}".format(key,value))

        self._open()

        if not key:
            log.error("key is required")
            raise SystemExit

        self._open()
        self._FILE.write("[{}]{}\n".format(key,value))
        self._FILE.close()
        self.is_opened = False


    def delete(self):
        """
        Delete an existing feedback file
        """
        log.info("Enter")
        
        if os.path.isfile(self.filename):
            log.debug("confirmed file {} exists, deleting".format(self.filename))
            try:
                os.remove(self.filename)
            except Exception as e:
                log.error("can't delete file - error={}".format(e))
                raise SystemExit


    def _open(self):
        """
        Open an existing file
        """
        log.info("Enter")

        if self.is_opened:
            return

        new = False
        if not os.path.isfile(self.filename):
            new = True
            log.debug("file {} does not exist, will create it".format(self.filename))

        try:
            self._FILE = open(self.filename, "a")
            self.is_opened = True

            # For a creation, add timestamps
            if new:
                date_time = datetime.datetime.now()
                self._FILE.write("# {}\n".format(str(date_time)))

        except Exception as e:
            log.error("can't open file {} for writing, error={}".format(self.filename, e))
            raise SystemExit


if __name__ == '__main__':
    print ("not directly callable")

    




