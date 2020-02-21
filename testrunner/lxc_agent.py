# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2019
@author: cgustave
"""
import logging as log
from agent import Agent
from netcontrol.ssh.ssh import Ssh 
import re

class Lxc_agent(Agent):
    """
    LXC agent
    """
    
    def __init__(self, name='', conn=0, dryrun=False, debug=False):
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

        log.info("Constructor with name={} conn={} dryrun={} debug={}".format(name, conn, dryrun, debug))

        # Attributs set in init
        self.name = name 
        self.conn = conn
        self.dryrun = dryrun 

        # Attributs to be set before processing 
        self.path = None
        self.playbook = None
        self.run = None
        self.agent = None        # name, id ... and all info for the agent itself
        self.testcase = None     # For which testcase id the agent was created

        # Private attributs
        self._connected = False    # ssh connection state with the agent 
        self._ssh = None
       
    def process(self, line=""):
        """
        LXC specific line processing
        List of allowed commands : open, connect, send, check
        Command line example
        srv-1:1 open tcp 80
        clt-1:1 connect tcp 1.1.1.1 80
        clt-1:1 send "alice"
        srv-1:1 check [srv recv] data receive "alice" since "server ready"
        """
        log.info("Enter with line={}".format(line))

        match = re.search("(?:(\s|\t)*[A-Za-z0-9\-_]+:\d+(\s|\t)+)(?P<command>[A-Za-z]+)",line)

        if match:
            command = match.group('command')
            log.debug("Matched with command={}".format(command))
        else:
            log.debug("No command has matched")

        if command == 'open':
            self.cmd_open(line)
        elif command == 'connect':
            self.cmd_connect(line)
        elif command == 'send':
            self.cmd_send(line)
        elif command == 'check':
           self.cmd_check(line) 
        elif command == 'close':
           self.cmd_close(line)
        else:
            log.warning("command {} is unknown".format(command))

 
    def cmd_open(self, line):
        """
        Processing for command "open"
        Opens a server udp or tcp connection 
        ex : srv-1:1 open tcp 9123
        """
        log.info("Enter with line={}".format(line))

        match = re.search("(?:open(\s|\t)+)(?P<proto>tcp|udp)(?:(\s|\t)+)(?P<port>\d+)",line) 
        if match:
            proto = match.group('proto')
            port = match.group('port')
            log.debug("proto={} port={}".format(proto, port))
        else:
            log.error("Could not extract proto and port from open command on line={}".format(line))
            raise SystemExit

        # Connect to agent if not already connected
        if not self._connected:
            log.debug("Connection to agent needed agent={} conn={}".format(self.name, self.conn))
            self.connect()

        # Open connection on agent
        cmd = "nc -l"
        if proto=="udp":
            cmd = cmd+" -u"

        cmd = cmd+" "+port+"\n"
        log.debug("sending cmd={}".format(cmd))
        self._ssh.channel_send(cmd)
        self._ssh.channel_read()
       
            

    def cmd_connect(self, line):
        """
        Processing for command "connect"
        Connect as a client to a remote udp or tcp server
        Requirement : server should be listing (call cmd_open)
        ex : clt-1:1 connect tcp 127.0.0.1 9123
        """
        log.info("Enter with line={}".format(line))

        match = re.search("(?:connect(\s|\t)+)(?P<proto>tcp|udp)(?:(\s|\t)+)(?P<ip>\S+)(?:(\s|\t)+)(?P<port>\d+)",line) 
        if match:
            proto = match.group('proto')
            ip = match.group('ip')
            port = match.group('port')
            log.debug("proto={} ip={} port={}".format(proto, ip, port))
        else:
            log.error("Could not extract proto, ip and port from connect command on line={}".format(line))
            raise SystemExit

        # Connect to agent if not already connected
        if not self._connected:
            log.debug("Connection to agent needed agent={} conn={}".format(self.name, self.conn))
            self.connect()

        # Connection to server
        cmd = "nc "
        if proto=="udp":
            cmd = cmd+" -u"
      
        cmd = cmd+" "+ip+" "+port+"\n" 
        log.debug("sending cmd={}".format(cmd))
        self._ssh.channel_send(cmd)
        self._ssh.channel_read()


    def cmd_send(self, line):
        """
        Processing for command "send"
        Sending data through an opened connection (udp or tcp)
        Requirement : ssh channel should have been opened
        Note : if nc is used, a \n is required to send data
        """
        log.info("Enter with line={}".format(line))

        match = re.search("(?:send(\s|\t)+\")(?P<data>.+)(?:\")", line)
        if match:
            data = match.group('data')
            log.debug("data={}".format(data))
            data = data+"\n"
            self._ssh.channel_send(data)
            self._ssh.channel_read()
        else:
            log.error("Could not recognize send command syntax in line={}".format(line))
            raise SystemExit

    def cmd_check(self, line):
        """
        Processing for command "check"
        Ex : clt-1:1 check [check_name] "keyword" 
        Ex : clt-1:1 check [check_name] "keyword" since "server ready"
        Process local tracefile looking for a pattern
        Optionaly if 'since "mark"' is added, restrict the search in the
        tracefile after the mark
        Return True if keyword is found otherwise False
        """
        log.info("Enter with line={}".format(line))
        result = False
        mark = ""
        
        match = re.search("check(\s|\t)+\[(?P<name>.+)\](\s|\t)+\"(?P<pattern>[A-Za-z0-9_\s-]+)\"", line)
        if match:
            name = match.group('name')
            pattern = match.group('pattern')
            log.debug("name={} pattern={}".format(name, pattern))

            match2 = re.search("\s+since\s+\"(?P<mark>.+)\"",line)
            if match2:
                mark = match2.group('mark')
                log.debug("since mark={}".format(mark))
            result = self._search_pattern_tracefile(pattern=pattern, mark=mark)

        else :
            log.error("Could not recognize check command syntax in line={}".format(line))
            raise SystemExit

        log.debug("Result={}".format(result))

        return result

    def _search_pattern_tracefile(self, pattern="", mark=""):
        """
        Search for a pattern in the tracefile
        Return True if found otherwise False
        If a mark is provided, first search for the mark, then look from the
        pattern starting from there.
        """
        log.info("Enter with pattern={} mark={}-".format(pattern, mark))
        result = False

        fname = self.get_trace_filename()
        log.debug("tracefile={}".format(fname))

        try :
            fh = open(fname)
        except:
            log.error("Tracefile {} can't be opened".format(fname))
            raise SystemExit

        if mark != "":
            log.debug("Need to search mark={}".format(mark))
            flag = True 
        else:
            flag = False

        # Need to first look for the mark
        # ex : ### 200221-19:13:13 server ready ###
        for line in fh:
            line = line.strip()
            print("mark - line={}".format(line))
            if flag:
                match = re.search("###\s\d+-\d+:\d+:\d+\s"+mark, line)
                if match:
                    log.debug("Found mark={}".format(mark))
                    flag = False
            else:
                match2 = re.search(pattern, line)
                if match2:
                    log.debug("Found pattern={}".format(pattern))
                    result = True
                    break

            print("pattern - line={}".format(line))

        fh.close()
        log.debug("result={}".format(result))
        return result







    def cmd_close(self, line):
        """
        Processing for command "close"
        """
        log.info("Enter with line={}".format(line))
        
        if self._ssh:
            self._ssh.close()



if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_testrunner.py\n")

     


