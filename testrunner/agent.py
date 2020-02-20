# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2019
@author: cgustave
"""
import logging as log
import re
from datetime import datetime
from netcontrol.ssh.ssh import Ssh

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
        NOTE : This method works but may generate a concurrent write to the
        tracefile (here we open the file from writing separately.
        Instead, we will use the Ssh module marking command to have a unique
        writer in the trace file
        Process command 'mark' generic to all agents
        Writes a standardized mark on the agent log file
        """
        log.info("Enter with line={}".format(line))

        # Extract the message
        match = re.search("(\s|\t)*(?:mark)(\s|\t)+(?:\")(?P<message>.+)(?:\")",line)
        if match:
            message = match.group('message')
            log.debug("message={}".format(message))
     
            filename = self.get_trace_filename()

            if not self.dryrun:
                log.debug("marking message={} to filename={}".format(message, filename))

                # The method below would work but it may generate a concurrent
                #write to the tracefile. Instead, we will use the Ssh module
                #marking command to have a unique writer in the tracefile
                # localtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
                # mark = "\n### "+localtime+" - "+message+" ###\n"
                #f = open(filename, "a")
                #f.write(mark)
                #f.close()

                self._ssh.trace_mark(message)

            else:
                log.debug("dry-run - fake marking : {}".format(message))

        else:
           log.debug("could not extract mark message")


    def process(self, line=""):
        """
        Generic line processing for agents
        This method should be overwritten in the specific agent
        """
        log.info("Enter (catch all) with line={}".format(line))


    def get_trace_filename(self):
        """
        Returns the trace file name made of path, playbook name, run id, agent name and connection id
        Ex : run=1 testcase=2 agent_name='lxc-1' connection_id='3'
             filename should be './playbooks/myPlaybook/runs/1/testcases/2/lxc-1_3.log
        """
        log.info("Enter")
            
        file_path = self.path+"/"+self.playbook+"/runs/"+str(self.run)+"/testcases/"
        file_name = str(self.name)+"_"+str(self.conn)+".log"
        testcase = self.testcase
        filename = file_path+testcase+"/"+file_name
        log.debug("tracefile name={}".format(filename))
        return(filename)


    def connect(self):
        """
        Connect to agent without sending any command
        This opens the ssh channel for  data exchange
        """
        log.info("Enter")
        ip = self.agent['ip']
        port = self.agent['port']
        login = self.agent['login']
        password = self.agent['password']
        ssh_key_file = self.agent['ssh_key_file']
        log.debug("ip={} port={} login={} password={} ssh_key_file={}".format(ip, port, login, password, ssh_key_file))

        self._ssh = Ssh(ip=ip, port=port, user=login, password=password, private_key_file=ssh_key_file, debug=self.debug)
        tracefile_name = self.get_trace_filename()
        self._ssh.trace_open(filename=tracefile_name)

        try:
           self._ssh.connect()
        except:
            log.error("Connection to agent {} failed".format(self.name))


if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_testrunner.py\n")

     


