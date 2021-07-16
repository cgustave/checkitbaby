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
        self.path = ""
        self.playbook = ""
        self.run = ""
        self.agent = {}        # name, id ... and all info for the agent itself
        self.testcase = ""     # For which testcase id the agent was created
        self.report = {}       # Testcase report (provided from Workbook)
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
        srv-1:1 iperf -s -u -B 226.94.1.1 -i 1
        """
        log.info("Enter with line={}".format(line))
        result = False
        match = re.search("(?:(\s|\t)*[A-Za-z0-9\-_]+:\d+(\s|\t)+)(?P<command>[A-Za-z]+)",line)
        if match:
            command = match.group('command')
            log.debug("Matched with command={}".format(command))
        else:
            log.debug("No command has matched")
        if command == 'open':
            result = self.cmd_open(line=line)
        elif command == 'connect':
            result = self.cmd_connect(line=line)
        elif command == 'send':
            match = re.search("(\s|\t)+multicast(\s|\t)+", line)
            if match:
                result = self.cmd_multicast(line=line)
            else:
                result = self.cmd_send(line=line)
        elif command == 'check':
            result = self.cmd_check(line=line)
        elif command == 'close':
            result = self.cmd_close(line=line)
        elif command == 'ping':
            result = self.cmd_ping(line=line)
        elif command == 'join':
            result = self.cmd_multicast(line=line)
        elif command == 'leave':
            result = self.cmd_multicast(line=line)
        elif command == 'listen':
            result = self.cmd_multicast(line=line)
        else:
            log.error("command {} is unknown".format(command))
            raise SystemExit
        return result

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
        return True

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
        cmd = "\nnc "
        if proto=="udp":
            cmd = cmd+" -u"
        cmd = cmd+" "+ip+" "+port+"\n"
        log.debug("sending cmd={}".format(cmd))
        if not self.dryrun:
            self._ssh.channel_send(cmd)
            self._ssh.channel_read()
        return True

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
        return True

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
            return True

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
        data = "\nping -n -A -w 2 -c "+str(count)+" -W 2 "
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
            self.add_report_entry(check=name, result=result)
            self.add_report_entry(data=name, result={'loss': loss, 'delay': delay})
        return result

    def cmd_multicast(self, line=''):
        """
        Commands:
        linux1:1 join multicast eth1 226.94.1.1
        linux1:1 listen multicast 226.94.1.1 port 5001
        linux2:1 send multicast 226.94.1.1 sport 10000 dport 5001 "keyword"
        linux1:1 check [check_name] "keyword"
        linux1:1 leave multicast eth1 226.91.1.1
        Requirements:
        Need the following packages installed : smcroute, hping3
        Note: for multiple send command,
        """
        log.info("Enter with line={}".format(line))
        result = False
        match1 = re.search("(?P<type>(join|leave))(\s|\t)+multicast(\s|\t)+(?P<dev>\S+)(\s|\t)+(?P<group>[0-9\.]+)", line)
        match2 = re.search("listen(\s|\t)+multicast(\s|\t)+(?P<group>[0-9\.]+)(\s|\t)+port(\s|\t)+(?P<port>\d+)", line)
        match3 = re.search("send(\s|\t)+multicast(\s|\t)+(?P<group>[0-9\.]+)(\s|\t)+sport(\s|\t)+(?P<sport>\d+)(\s|\t)+dport(\s|\t)+(?P<dport>\d+)(\s|\t)+\"(?P<message>.*?)\"", line)
        if match1:
            type = match1.group('type')
            dev = match1.group('dev')
            group = match1.group('group')
            log.debug("type={} dev={} group={}".format(type, dev, group))
            if type == 'join':
                result = self.cmd_multicast_group(action='join', dev=dev, group=group)
            elif type == 'leave':
                result = self.cmd_multicast_group(action='leave', dev=dev, group=group)
        elif match2:
             group = match2.group('group')
             port = match2.group('port')
             result = self.cmd_multicast_listen(group=group, port=port)
        elif match3:
            group = match3.group('group')
            sport = match3.group('sport')
            dport = match3.group('dport')
            message = match3.group('message')
            result = self.cmd_multicast_send(group=group, sport=sport, dport=dport, message=message)
        else:
            log.error("Could not recognize multicast command syntax in line={}".format(line))
            raise SystemExit
        return result

    def cmd_multicast_group(self, action='', group='', dev=''):
        """
        Join or leave a mutlicast group
        uses smcroute on the client, ex:
          smcroute -j eth1 239.1.1.1
          smcroute -l eth1 239.1.1.1
        """
        log.info("Enter with action={} group={} dev={}".format(action, group, dev))
        result = False
        option = 'h'
        if action == 'join':
            option = 'j'
        elif action == 'leave':
            option = 'l'
        else:
            log.error("syntax error")
            raise SystemExit
        if not self._connected:
            log.debug("Connection to agent needed agent={} conn={}".format(self.name, self.conn))
            self.connect(type='lxc')
        cmd =  "\nsmcroute -"+option+" "+dev+" "+group+"\n"
        log.debug("sending cmd={}".format(cmd))
        if not self.dryrun:
            self._ssh.channel_send(cmd)
            self._ssh.channel_read()
        return True
        return result

    def cmd_multicast_listen(self, group="", port=""):
        """
        List a mutlicast address/port.
        Uses netcat
        nc -l -u 239.1.1.1 1000
        """
        log.info("Enter with group={} port={}".format(group, port))
        if not self._connected:
            log.debug("Connection to agent needed agent={} conn={}".format(self.name, self.conn))
            self.connect(type='lxc')
        cmd = "\nnc -l -u "+group+" "+port+"\n"
        log.debug("sending cmd={}".format(cmd))
        if not self.dryrun:
            self._ssh.channel_send(cmd)
            self._ssh.channel_read()
        return True
        return result

    def cmd_multicast_send(self, group='', sport='', dport='', message=''):
        """
        Sends a message in udp multicast
        Uses hping3
        echo "message" | hping3 --udp 239.1.1.1 -t 32 -s 10000 -p 5000 -k -d 10 -c 1 -E /dev/stdin --faster
        """
        log.info("Enter with group={} sport={} dport={} message={}".format(group, sport, dport, message))
        message = message + "\n"
        result = False
        len_message = len(message)
        log.debug("message length={}".format(len_message))
        cmd = "\necho \"{}\" | hping3 --udp {} -t 32 -s {} -p {} -k -d {} -c 1 -E /dev/stdin --faster\n".format(message, group, sport, dport, str(len_message))
        log.debug("sending cmd={}".format(cmd))
        if not self._connected:
            log.debug("Connection to agent needed agent={} conn={}".format(self.name, self.conn))
            self.connect(type='lxc')
        if not self.dryrun:
            self._ssh.channel_send(cmd)
            self._ssh.channel_read()
        return True

    def close(self):
        log.info("Enter")

if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_checkitbaby.py\n")
