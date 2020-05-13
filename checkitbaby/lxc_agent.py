# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2020
@author: cgustave
"""
import logging as log
from agent import Agent
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
        else:
            self.debug = False
            log.basicConfig(level='ERROR')

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
        self.report = None       # Testcase report (provided from Workbook)

        # Private attributs
        self._connected = False    # ssh connection state with the agent 
        self._ssh = None

    def __del__(self):
        """
        Desctructor to close opened connection to agent when exiting
        """
        if self._ssh:
            self._ssh.close()


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
        elif command == 'ping':
            self.cmd_ping(line)
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
            self.connect(type='lxc')

        # Open connection on agent
        cmd = "nc -l"
        if proto=="udp":
            cmd = cmd+" -u"

        cmd = cmd+" "+port+"\n"
        log.debug("sending cmd={}".format(cmd))
        if not self.dryrun:
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
            self.connect(type='lxc')

        # Connection to server
        cmd = "nc "
        if proto=="udp":
            cmd = cmd+" -u"
      
        cmd = cmd+" "+ip+" "+port+"\n" 
        log.debug("sending cmd={}".format(cmd))
        if not self.dryrun:
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
            if not self.dryrun:
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

            # read from agent (and write to tracefile)
            read_data = self._ssh.channel_read()
            log.debug("CHECK RECV={}".format(read_data))

            # Check in the tracefile
            sp = self.search_pattern_tracefile(pattern=pattern, mark=mark)
            result = sp['result']

        else :
            log.error("Could not recognize check command syntax in line={}".format(line))
            raise SystemExit

        log.debug("Result={}".format(result))

        # Writing testcase result in the playbook report
        if not self.dryrun:
            self.add_report_entry(check=name, result=result)

        return result

    def cmd_close(self, line):
        """
        Processing for command "close"
        """
        log.info("Enter with line={}".format(line))
        
        if self._ssh:
            self._ssh.close()

    def cmd_ping(self, line):
        """
        Connectivity check
        Reports packet loss and delays
        Results (average delay and loss) are reported in 'ping' report section
        Note : using -A (adaptative by default)
          ex : ping [con_test] 10.0.2.1               (always pass)
        
        Additional test criteria : maxloss and maxdelay:
          ex : ping [con_test] 10.0.2.1 maxloss 50    (pass if loss < 50%)
          ex : ping [con_test] 10.0.2.1 maxdelay 100  (pass if delay < 100)
        Return: true|false depending if pass criteria are matched
        """
        log.info("Enter with line=line")
        count = 5 
        loss = 100
        delay = 9999
        result = True

        match = re.search("ping(\s|\t)+\[(?P<name>.+)\](\s|\t)+(?P<host>[A-Za-z0-9_\.-]+)", line)
        if match:
            name = match.group('name')
            host = match.group('host')
            log.debug("name={} host={}".format(name, host))
        else:
            log.error("Could not recognize ping command syntax in line={}".format(line))
            raise SystemExit

        if not self._connected:
            log.debug("Connection to agent needed agent={} conn={}".format(self.name, self.conn))
            self.connect(type='lxc')
      
        # Random mark for analysis
        reference = self.random_string(length=8)

        if not self.dryrun:
            self._ssh.trace_mark(reference)

        # ping
        data = "ping -n -A -w 2 -c "+str(count)+" -W 2 "
        data = data + host
        data = data + "\n"
        log.debug("data={}".format(data))

        if not self.dryrun:
        # look for the prompt on a slow command (5 seconds)
            maxround = self._ssh.maxround
            self._ssh.maxround = 50
            self._ssh.shell_send([data])
            self._ssh.maxround = maxround
       
            # Get loss % : Process result since mark
            sp = self.search_pattern_tracefile(mark=reference, pattern='packets transmitted')
            loss_line = sp['line']
            log.debug("Found loss_line={}".format(loss_line))

            # 5 packets transmitted, 5 received, 0% packet loss, time 803ms 
            match = re.search("\s(?P<loss>\d+)%\spacket\sloss", loss_line)
            if match:
                loss = match.group('loss')
                log.debug("loss={}".format(loss))

                # Check pass condition if any
                log.debug("line={}".format(line))
                match_maxloss = re.search("maxloss\s+(?P<maxloss>\d+)", line)
                if match_maxloss:
                    maxloss = match_maxloss.group('maxloss')
                    log.debug("maxloss={}".format(maxloss))
                    if int(loss) > int(maxloss):
                        log.debug("Fail maxloss criteria : loss={} maxloss={}".format(loss, maxloss))
                        result = False
                    else:
                        log.debug("Pass maxloss criteria : loss={} maxloss={}".format(loss, maxloss))

            # Get avg rtt
            if int(loss) != 100:
                # rtt min/avg/max/mdev = 27.277/28.111/30.203/1.089 ms, ipg/ewma 200.766/28.137 ms
                sp2 = self.search_pattern_tracefile(mark=reference, pattern='rtt min/avg/max')
                delay_line = sp2['line']
                log.debug("Found delay_line={}".format(delay_line))
                match2 = re.search("\s=\s[0-9\.]+/(?P<delay>[0-9\.]+)/", delay_line)
                if match2:
                    delay = match2.group('delay')
                    log.debug("delay={}".format(delay))

                    # Check maxdelay pass condition if any
                    log.debug("line={}".format(line))
                    match_maxdelay = re.search("maxdelay\s+(?P<maxdelay>\d+)", line)
                    if match_maxdelay:
                        maxdelay = match_maxdelay.group('maxdelay')
                        log.debug("maxdelay={}".format(maxdelay))
                        if float(delay) > float(maxdelay):
                            log.debug("Fail maxdelay criteria : delay={} maxdelay={}".format(delay, maxdelay))
                            result = False
                        else:
                            log.debug("Pass maxdelay criteria : delay={} maxdelay={}".format(delay, maxdelay))

            else:
                log.debug("Failure anytime with 100% loss")
                result = False

            self.add_report_entry(get=name, result={'loss': loss, 'delay': delay})
            self.add_report_entry(check=name, result=result)

        return result
        
    def search_pattern_tracefile(self, pattern="", mark=""):
        """
        Search for a pattern in the tracefile
        Returns a dictionary :
            'result' : true|false
            'line'   : matched line 
        If a mark is provided, first search for the mark, then look from the
        pattern starting from there.
        """
        log.info("Enter with pattern={} mark={}".format(pattern, mark))
        result = False
        line = ""

        fname = self.get_filename(type='trace')
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
        # ex : ### 200222-19:15:43 9E9T6EAN ###
        for line in fh:
            line = line.strip()
            log.debug("line={}".format(line))
            if flag:
                match = re.search("###\s\d+-\d+:\d+:\d+\s"+mark+"\s###", line)
                if match:
                    log.debug("Found mark={}".format(mark))
                    flag = False
            else:
                match2 = re.search(pattern, line)
                if match2:
                    log.debug("Found pattern={}".format(pattern))
                    result = True
                    break

        fh.close()
        log.debug("result={}".format(result))
        return {"result": result, "line": line}

    def close(self):
        log.info("Enter")

if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_checkitbaby.py\n")

     


