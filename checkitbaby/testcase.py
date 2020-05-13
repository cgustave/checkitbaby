# -*- coding: utf-8 -*-
"""
Created on Feb 12, 2019
@author: cgustave
"""

import logging as log
import re
import os
import json
import string
import random

class Testcase(object):
    """
    Testcase class
    Test cases are defined within a playbook directory inside dir 'testcases'
    They are organised in multiple files, one testcase per file.
    Filename format is "ID_NAME.txt", ID should be numbered with 3 digits to
    allow alphabetical sorting 
      ex : /fortipoc/playbooks/advpn/testcases/001_environment.txt
      ex : /fortipoc/playbooks/advpn/testcases/002_connectivity.txt
      ex : /fortipoc/playbooks/advpn/testcases/003_ipsec_tunnels.txt
      ex : /fortipoc/playbooks/advpn/testcases/004_routing.txt

    requires : variables, macros, playbook, path, name, id
    """

    def __init__(self, id='', name='', playbook='', path='', filename='', variables='', macros='',  debug=False):

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

        log.info("Constructor with id={} name={} playbook={} path={} filename={} debug={}".format(id, name, playbook, path, filename, debug))

        # Attributs
        self.id = id
        self.name = name
        self.playbook = playbook
        self.path = path
        self.filename = filename

        self.lines = []      
        self.nb_lines = 0           # Number of lines in the scenario
        self.state = True
        self.agents = []            # list of agents used in the scenario
        self.macros = macros        # macro definitions, dictionnay with macro name as key
        self.variables = variables  # variables defined for the playbook

        # Run
        self.load_scenario()
        self.expand_variables()
        self.build_agents_list()

    def load_scenario(self):
        """
        Load the testcase statements in memory
        Asks for macro expansion if found
        """
        log.info("Enter")
        filename = self.path+"/"+self.playbook+"/testcases/"+self.filename

        try:
            with open(filename) as file_in:
                index = 1 
                for line in file_in:
                    line = line.strip()
                    log.debug("index={} read line={}".format(index, line))

                    # Ignore empty lines and comments
                    if line == "":
                        continue
                    if (line[0] == "#"):
                        continue

                    # Exclude generic commands
                    match_reserved_command = re.search("^(set|message|sleep|mark)",line)
                    if match_reserved_command:
                        log.debug("A generic command is found, skip")
                        continue
 
                    # Expands macro if found
                    # Macro starts with &
                    match_macro = re.search("^(?:&)(?P<macro>[A-Za-z0-9\-_]+)(?:\s*)\((?P<params>\S+)\)",line)

                    if match_macro:
                        macro = match_macro.group('macro')
                        params = match_macro.group('params')
                        log.debug("Found macro={} with params={}".format(macro, params))
                        if not (macro in self.macros.keys()):
                            log.error("macro {} is not defined in conf/macros.txt".format(macro))
                            raise SystemExit
                        else :
                            added_lines = self.expand_macro(name=macro, params=params)
                            index = index + added_lines
                    else:
                         self.lines.append(line)
                         index = index + 1
            
                # Keep track of number of line for progress bar
                self.nb_lines = index

        except IOError as e:
            log.debug("I/O error filename={} error={}".format(filename,e.strerror))

    def build_agents_list(self):
        """
        Go through the loaded scenario and extract the agents
        """
        log.info("Enter")

        for line in self.lines:

            # Ignore empty lines and comments
            if line == "":
                continue
            if (line[0] == "#"):
               continue

            # Exclude generic commands
            match_reserved_command = re.search("^(set|message|sleep|mark)",line)
            if match_reserved_command:
                log.debug("A generic command is found, skip")
                continue
 
            # Extract agents and add in our list if needed
            match = re.search("(?:\s|\t)*(?P<agent>[A-Za-z0-9\-_]+)",line)
            if match:
                agent = match.group('agent')
                if agent not in self.agents:
                    log.debug("Found a new agent={}".format(agent))
                    self.agents.append(agent)

    def expand_macro(self, name, params):
        """
        Expands the macro in testcase lines
        Macro should have been defined and should have been registered
        ex: &tcp_connectivity_check(H1B1,1,H1B2,1,9000)
            where tcp_connectivity_check is a registered macro
                  H1B1,1,H1B2,1,9000 are the sorted parameters of the macro
        we receive : name=tcp_connectivity_check params=H1B1,1,H1B2,1,9000

        While expanding the macro, all params of the macro should be replaced
        with their given values

        Return : number of lines expanded
        """
        log.info("Enter with name={} params={}".format(name, params))

        # Get params values as a sorted list
        params_values = []
        for p in params.split(','):
            log.debug("store params values={}".format(p))
            params_values.append(p)

        # Extract parameters values
        index = 1
        for line in self.macros[name]['lines']:
            log.debug("line={}".format(line))

            # See if macro params are present and need top be replaced
            position = 0
            for key in self.macros[name]['params']:
                log.debug("position={} checking param={} to be replaced by {}".format(position,key,params_values[position] ))
                line=line.replace("$"+key+"$",params_values[position])
                position = position + 1

            log.debug("line after macro expansion = {}".format(line))
            self.lines.append(line)
            index = index + 1

        return index


    def expand_variables(self):
        """
        Variables can be used in scenario.
        This function does 2 things :

        1) translate the variables from scenario in their values
        2) dynamically assign variable from the scenario, using :
           set variable=assignment
           Some build-in functions may be use for assignment
        """
        log.info("Enter")

        line_index = 0
        for line in self.lines:
            
            found = False
            original_line = line
            
            # See if a variable assignment is needed
            match_assignment = re.search("set\s+(?P<var>[A-Za-z0-9\-_]+)(?:\s*)=(?:\s*)(?P<assignment>\S+)",line)
            if match_assignment:
                var = match_assignment.group('var')
                assignment = match_assignment.group('assignment')
                found = True
                log.debug("Variable assignment required : var={} assignment={}".format(var,assignment))

                # Deal with special functions
                match_random_cmd = re.search("^random_string\((?P<length>\d+)\)",assignment)
                if match_random_cmd:
                    length = match_random_cmd.group('length')
                    s = ''.join(random.choice(string.ascii_uppercase+string.digits) for _ in range(int(length)))
                    log.debug("random string generator with length={} : s={}".format(length, s))
                    self.variables[var] = s

                else:
                    log.debug("static assignment {} => {}".format(var, assignment))
                    self.variables[var] = assignment

            # Variables translation
            nb = 0
            for word in line.split():
                match_variable = re.search("\$(?P<variable>\S+)\$", word)
                if match_variable:
                    variable = match_variable.group('variable')
                    log.debug("Found variable={} in world={}, translating".format(variable, word))

                    # check variable is defined
                    if variable in self.variables:
                        found = True
                        log.debug("Variable={} has been found, converting to {}".
                                  format(variable, self.variables[variable]))
                        word_to_replace = "\$"+str(variable)+"\$"
                        translated_line = re.sub(word_to_replace, self.variables[variable], line)
                        line = translated_line
                        nb = nb + 1
                        log.debug("Line translated to line={} (iteration={})".format(line, nb))
                    else:
                        log.error("Variable {} is not defined in line={}. Aborting test".
                                  format(variable, original_line))
                        raise SystemExit

            if found:
                log.debug("Translation done, replacing original line at line_index={}".format(line_index))
                self.lines[line_index] = line
       
            # Increase line index by 1 
            line_index = line_index + 1

 
    def disable(self):
        """
        Disable a testcase (won't be selected to run)
        """
        log.info("Enter")
        self.state = False

    def enable(self):
        """
        Enable a testcase (will be selected to run)
        """
        log.info("Enter")
        self.state = True

if __name__ == '__main__': #pragma: no cover
    print("Please run tests/test_checkitbaby.py\n")
