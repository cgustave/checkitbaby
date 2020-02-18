# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2019
@author: cgustave
"""
import logging as log
import re
from datetime import datetime

class Agent(object):
    """
    Generic Agent class inherited by all specific agents
    """

    def __init__(self):
        """
        Constructor
        """
        pass
        # no call to __init__ from sons (no super calls)
        # we are only interested in the methods
        # attributes are the sons ones
        
        # create logger
        #log.basicConfig(
        #      format='%(asctime)s,%(msecs)3.3d %(levelname)-8s[%(module)-\
        #      10.10s.%(funcName)-20.20s:%(lineno)5d] %(message)s',
        #      datefmt='%Y%m%d:%H:%M:%S',
        #      filename='debug.log',
        #      level=log.NOTSET)
        # Set debug level first

        #if debug:
        #    self.debug = True
        #    log.basicConfig(level='DEBUG')

        #log.info("Constructor with name={} conn={} dryrun={} debug={}".format(name, conn, dryrun, debug))
        #
        #self.name = name
        #self.conn = conn
        #self.dryrun = dryrun


    def process_generic(self, line=""):
        """
        Generic processing done for any kind of agents
        This method is not overwritten and called systematically for all agents
        """
        log.info("Enter with line={}".format(line))

        # Sanity checks
        if self.path == None:
            log.error("Undefined path")
            raise SystemExit

        if self.playbook == None:
            log.error("Undefined playbook")
            raise SystemExit

        if self.run == None:
            log.error("Undefined run")
            raise SystemExit
        log.debug("Our attributs : path={} playbook={} run={}".format(self.path, self.playbook, self.run))

        # Get command
        match = re.search("(?:(\s|\t)*[A-Za-z0-9\-_]+:\d+(\s|\t)+)(?P<command>[A-Za-z]+)",line)

        if match:
            command = match.group('command')
            log.debug("Matched with command={}".format(command))
        else:
            log.debug("No command has matched")

        if command == "mark":
            self.process_mark(line=line)


    def process_mark(self, line=""):
        """
        Process command 'mark' generic to all agents
        Writes a standardized mark on the agent log file
        """
        log.info("Enter with line={}".format(line))

        # Extract the message
        match = re.search("(\s|\t)*(?:mark)(\s|\t)+(?:\")(?P<message>.+)(?:\")",line)
        if match:
            message = match.group('message')
            log.debug("message={}".format(message))
            localtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
            mark = "\n### "+localtime+" - "+message+" ###\n"
     
            filename = self.get_trace_filename()

            if not self.dryrun:
                log.debug("marking mark={} filename={}".format(mark, filename))
                f = open(filename, "a")
                f.write(mark)
                f.close()

            else:
                log.debug("dry-run - fake marking : {}".format(mark))

        else:
           log.debug("could not extract mark message")

    def process(self, line=""):
        """
        Generic line processing for agents
        This method could be overwritten in the specific agent
        """
        log.info("Enter with line={}".format(line))


    def get_trace_filename(self):
        """
        Returns the trace file name made of path, playbook name, run id, agent name and connection id
        Ex : run=1 agent_name='lxc-1' connection_id='1'
             filename should be './playbooks/myPlaybook/runs/1/lxc-1_1.log
        """
        log.info("Enter")
            
        file_path = self.path+"/"+self.playbook+"/runs/"+str(self.run)+"/"
        file_name = str(self.name)+"_"+str(self.conn)+".log"
        filename = file_path+file_name
        log.debug("filename={}".format(filename))
        return(filename)

if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_testrunner.py\n")

     


