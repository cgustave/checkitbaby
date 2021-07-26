# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2020
@author: cgustave
"""
import logging as log
import re
import json
import string
import random
from netcontrol.ssh.ssh import Ssh
from netcontrol.vyos.vyos import Vyos
from netcontrol.fpoc.fpoc import Fpoc
from netcontrol.fortigate.fortigate import Fortigate
from netcontrol.fortiswitch.fortiswitch import Fortiswitch

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
        result = False
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
        # Generic commands : 'mark'
        match = re.search("(?:(\s|\t)*[A-Za-z0-9\-_]+:\d+(\s|\t)+)(?P<command>[A-Za-z]+)",line)
        if match:
            command = match.group('command')
            log.debug("Matched with command={}".format(command))
        else:
            log.debug("No command has matched")
        if command == "mark":
            result = self.process_mark(line=line)

        # returning translated line
        return result

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
            if not self.dryrun:
                log.debug("marking message={}".format(message))
                self._ssh.trace_mark(message)
            else:
                log.debug("dry-run - fake marking : {}".format(message))
            return True
        else:
           log.debug("could not extract mark message")
           return False

    def process(self, line=""):
        """
        Generic line processing for agents
        This method should be overwritten in the specific agent
        """
        log.info("Enter (catch all) with line={}".format(line))

    def get_filename(self, type='trace'):
        """
        Returns different type of filename based on of path, playbook name, run id, agent name and connection id

        * type='trace' : returns a trace_file name
        Ex : run=1 testcase=2 agent_name='lxc-1' connection_id='3'
             filename should be './playbooks/myPlaybook/runs/1/testcases/2/lxc-1_3.log

        * type='report' : returns path and filename for a report in testcase
        """
        log.info("Enter with type={}".format(type))

        file_path = self.path+"/"+self.playbook+"/runs/"+str(self.run)+"/"

        if type == 'trace':
           testcase = self.testcase
           file_path = file_path+"testcases/"+testcase+"/"
           file_name = str(self.name)+"_"+str(self.conn)+".log"
        elif type == 'report':
           file_name = "report.json"
        else:
           log.error("unknown type={}".format(type))
           raise SystemExit

        filename = file_path+file_name
        log.debug("type={} filename={}".format(type, filename))
        return(filename)

    def parse_line(self, line=''):
        """
        Parses agent line to extract required information common to all agents
        Returns a dictionary of line elements
        Generate ERROR and exit in case of syntax errors
        """
        log.info("Enter with line={}".format(line))
        match = re.search("(\s|\t)*(?P<agent>[A-Za-z0-9\-_]+):(?P<conn>\d+)(\s|\t)+(?P<type>get|check|flush)?(\s|\t)*(?P<check>\[\S+\])?(\s|\t)*(?P<group>[A-Za-z-]+)(\s|\t)*(?P<command>[A-Za-z-]+)",line)
        if match:
            agent = match.group('agent')
            conn = match.group('conn')
            type = match.group('type')
            check = match.group('check')
            # Remove [ ] from check
            if check:
                match_check = re.search('\[(?P<check>\S+)\]', check)
                if match_check:
                    check = match_check.group('check')
            group = match.group('group')
            command = match.group('command')
            log.debug("Matched with agent={} conn={} type={} check={} group={} command={}".format(agent, conn, type, check, group, command))
        else:
            log.error("Syntax error: could not extract agent, connection or command from {}".format(line))
            raise SystemExit
        return { 'agent': agent, 'conn': conn, 'type': type, 'check': check, 'group': group, 'command': command }

    def add_report_entry(self, check="", get="", data="", result=""):
        """
        Adds an entry in the report.
        For a check entry, call with check=check_name, result=pass|fail
        Update the testcase generic result.
        get: from 'get' commands (like get system status)
        check: the subkey is the check name (in brackets in the line), value is True for a Pass and False for a Fail.
        data: same subkey as the check command. Key 'data' is used to store additional information gathere during a check.
        """
        log.info("Enter with check={} get={} data={} result={}".format(check, get, data, result))

        # Create playbook result if needed
        if 'result' not in self.report:
            self.report['result'] = True

        # Create testcase in report if needed
        if 'testcases' not in self.report:
            self.report['testcases'] = {}

        if self.testcase not in self.report['testcases']:
            self.report['testcases'][self.testcase]={}

        # Create testcase generic result if needed
        if 'result' not in self.report['testcases'][self.testcase]:
            self.report['testcases'][self.testcase]['result'] = True

        # Create check group if needed
        if 'check' not in self.report['testcases'][self.testcase]:
            self.report['testcases'][self.testcase]['check'] = {}

        # Create get group if needed
        if 'get' not in self.report['testcases'][self.testcase]:
            self.report['testcases'][self.testcase]['get'] = {}

        # Create 'data' group if needed
        if 'data' not in self.report['testcases'][self.testcase]:
            self.report['testcases'][self.testcase]['data'] = {}

        if check:
            log.debug("Adding check={} result={} in testcase={}".format(check, result, self.testcase))
            self.report['testcases'][self.testcase]['check'][check] = result

            # Update playbook result
            pr = self.report['result'] and result
            self.report['result'] = pr
            log.debug("Playbook result updated with result={}".format(pr))

            # Update testcase result
            tr = self.report['testcases'][self.testcase]['result'] and result
            self.report['testcases'][self.testcase]['result'] = tr
            log.debug("Testcase result updated with result={}".format(tr))

        if data:
            log.debug("Adding data={} result={} in testcase={}".format(data, result, self.testcase))
            self.report['testcases'][self.testcase]['data'][data] = result

        # Add get report entry for the given agent
        if get:
            log.debug("Adding get={} result={} in testcase={}".format(get, result, self.testcase))
            if self.name not in self.report['testcases'][self.testcase]['get']:
               self.report['testcases'][self.testcase]['get'][self.name] = {}
            self.report['testcases'][self.testcase]['get'][self.name][get] = result

        # Write report file
        filename = self.get_filename(type='report')
        log.debug("Writing report filename={}".format(filename))

        f = open (filename, "w")
        f.write(json.dumps(self.report, indent=4))
        f.close()

    def random_string(self, length=8):
        """
        Returns a random string
        """
        log.info("Enter with length={}".format(length))
        s = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))
        return s

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

    def connect(self, type=''):
        """
        Connect to agent without sending any command
        This opens the ssh channel for data exchange and tracefile
        """
        log.info("Enter with type={}".format(type))
        ip = self.agent['ip']
        port = self.agent['port']
        login = self.agent['login']
        password = self.agent['password']
        ssh_key_file = self.agent['ssh_key_file']
        log.debug("ip={} port={} login={} password={} ssh_key_file={}".format(ip, port, login, password, ssh_key_file))
        success = True
        if not self.dryrun:
            if type == 'lxc':
                self._ssh = Ssh(ip=ip, port=port, user=login, password=password, private_key_file=ssh_key_file, debug=self.debug)
            elif type == 'vyos':
                self._ssh = Vyos(ip=ip, port=port, user=login, password=password, private_key_file=ssh_key_file, debug=self.debug)
            elif type == 'fortipoc':
                self._ssh = Fpoc(ip=ip, port=port, user=login, password=password, private_key_file=ssh_key_file, debug=self.debug)
            elif type == 'fortigate':
                self._ssh = Fortigate(ip=ip, port=port, user=login, password=password, private_key_file=ssh_key_file, debug=self.debug)
            elif type == 'fortiswitch':
                self._ssh = Fortiswitch(ip=ip, port=port, user=login, password=password, private_key_file=ssh_key_file, debug=self.debug)
            else:
                log.error("unknown type")
                raise SystemExit
            tracefile_name = self.get_filename(type='trace')
            self._ssh.trace_open(filename=tracefile_name)
            try:
                success = self._ssh.connect()
                self._connected = True
                success = True
            except:
                log.error("Connection to agent {} failed".format(self.name))
                success = False
        else:
            log.debug("dryrun mode")
        return success

    def get_requirements(self, line=""):
        """
        Returns a list of key/value pairs corresponding to the requirement list.
        Requirements are expressed as key=value separated by spaces, after keyword 'has'
        """
        log.info("Enter with line={}".format(line))
        reqlist = []
        match_has = re.search("\s+has\s+(?P<requirements>.+)",line)
        if match_has:
            requirements = match_has.group('requirements')
            log.debug("requirements string {}".format(requirements))
            nb = 0
            for r in requirements.split():
                nb = nb + 1
                log.debug("requirement nb={} string:{}".format(nb, r))
                match_req = re.search("^(?P<rname>.+)=(?P<rvalue>.+)", r)
                if match_req:
                    rname = match_req.group('rname')
                    rvalue = match_req.group('rvalue')
                    reqlist.append({ 'name': rname, 'value': rvalue })
                else:
                    log.error("Syntax error : failed to extract requirement from {}".value(r))
                    raise SystemExit
        else:
            log.debug("no requirements found")
        return reqlist

    def check_requirement(self, result={}, name='', value=''):
        """
        Validates the given requirement.
        Returns true if the name/value pair received exists in result dictionary
        """
        log.info("Enter with name={} value={} result={}".format(name, value, result))
        fb = True  # by default, requirement is met
        if not name in result:
            log.warning("requirement name={} is not in result={}".format(name, result))
            return False
        elif str(result[name]) == str(value):
            log.debug("{}={} requirement is met".format(name, value))
            return True
        else:
            log.debug("{}={} requirement is not met".format(name, value))
            return False

    def close(self):
        """
        Generic close for all agent, may be overwritten
        """
        log.info("Enter")


if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_checkitbaby.py\n")
