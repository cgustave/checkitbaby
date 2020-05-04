# Checkitbaby 

## Definition

Checkitbaby is a tool to allow automatic tests validations in a lab.
It uses 'agents' to interact with the setup for instance to play simple client/server role, to change the setup topology or even to query the DUT. Agent are connected using ssh. It is recommended to use ssh keys.  

*Playbooks* are defined as a collection of *Testcases*, each testcase is a simple text file where each lines defines an action applied to an *Agent*.
Each line of the testcase can either trigger an action and/or get some information and see if some requirements are met (checks).  
Test scenario syntax is simple and evolutive, commands are defined keywords and depend on the type of agents targeted.  
Multiple simultaneous connections to agents are supported. 
*Variables* are allowed  in testcase. A variable is just a keyword starting with a dollar sign '$' and defined in a variable file. 
During testcases execution, all *Run* information such as agent ouputs are collected in log files. The test verification would always be done from log file parsing like a human would do. With this, it is possible to easily double-check the test result post-run.  *Marks* can be used as a delimeter for check verification within the agent log file.  

When all the testcases from a Playbook has run, a *Report* in a json format is delivered. The report is organized by testcases and include all checks results from the testcase.
A general Pass/Fail covering all testcases is also included.  

Checkitbaby can be simply run as a script to run all or some testcases against the setup. It is possible to run the testcase in *Dry-Run* mode to only validate the scenario file syntax for staging.  

Checkitbaby focus is to run against FortiPoc setup, either from withing the PoC (from a testing lxc) or externaly to PoC (from user PC)  


## Installation

Will be deliver as python package (to be done)
* Requirements : netcontrol python library: `pip install -I netcontrol`


## Usage

##### Command line:

* Running all testcases from a playbook :  
  ex : 	`python3 run_playbook.py myPlaybook`

* Running a specific testcase from a playbook
	`python3 run_playbook.py myPlaybook 003`

##### Web integration:

Planned.
The idea is to load, select and run the defined testcases and provide a formated report.


## Organization

#### File tree structure

The following directory tree structure is used to organize the tests :

- Directory structure:
~~~
/PLAYBOOK_BASE_PATH : The base name of the playbook location
	  ex : /fortipoc/playbooks

/PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME
	  ex : /fortipoc/playbooks/advpn

/PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/agents.conf  : files with agents definitions
	  ex : /fortipoc/playbooks/advpn/agents.conf

/PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/variables.conf :  files with variables definitions
	  ex : /fortipoc/playbooks/advpn/variables.conf

/PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/testcases    : directory containing testcases
	  ex : /fortipoc/playbooks/advpn/testcases

/PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/testcases/NNN_TESTCASE_NAME : one testcase file
	                                   with NNN : a number starting from 000 (to order testcases)
									        TESTCASE_NAME : any name for the testcase

      ex : /fortipoc/playbooks/advpn/testcases/001_spoke_to_hub_connectivity.txt
      ex : /fortipoc/playbooks/advpn/testcases/002_spoke_ipsec_tunnel.txt
      ex : /fortipoc/playbooks/advpn/testcases/003_spoke_routing.txt
~~~

* Creating a new playbook:

Use program create_new_playbook.sh to create a new playbook file tree:
`Usage : ./create_new_playbook.sh <playbook_name>`



## Agents

Currently supported agents are : Debian LXC, Vyos routers, FortiGate devices, FortiPoC.  
A few agent-less functions are defined (for instance to wait or append some comments or *standard marks* in the logs)

The generic syntax of each line of a testcase is as follow :  
`__AGENT_NAME__:__AGENT_CONNECTION_ID__  __COMMAND__ __COMMAND_SPECIFIC_DATA__ `

Each test/validation uses command 'check' followed by the test reference between square bracket [__TEST_NAME__].  
The _TEST_NAME_ should be uniq in the testcase file.  
A check may include a single or a list of *Requirements*. Requirements follow keyword 'has', they are provided as key=value pairs separated by spaces.
A test pass if all provided requirements are met. If not requirement are provided, test would be succefull if an occurence was found.  

Each line starting with comment sign '#' are ignored.  
Lines are run sequentially.   

SSH connections to agents are automatically opened and closed at the end of the testcase.  

The following chapter defines each agent command syntax and support.  


#### Generic commands

Following commands are not agent specific and can be used with all agents

~~~

# Append a message on the user output when running the testcase
# This message is not append on the agent log file.
message "set Branch 1 connections delays and losses"

# Appends a mark on the agent log file (but not on user output)
# This should be used to delimit checks parsing start (see check command 'since')
HOSTS-B2:1 mark "receive_ready"

# Skip all following lines from the testcase
skip all

# Wait a number of seconds
wait 30
~~~


#### Debian LXC

Simple ping test.  
Connection (UDP or TCP) one way or two-way test.  
Open, connect, close connections and send data. It is recommended to use 'marks' to limit the check parsing area.
~~~
# Ping test, pass if at least one packet is not lost
# Delay and loss are added in the report
LXC1-1:1 ping [con_test] 10.0.2.1

# Ping test, pass if maximum packet loss under 50 %
LXC1-1:1 ping [con_test] 10.0.2.1 maxloss 50

# Open a tcp server on port 8000  on agent LXC-1 from its connection 1
LXC-1:1 open tcp 8000

# Append a mark in LXC-1:1 log file
LXC-1:1 mark "server ready"

# Connect to a tcp server at ip 10.0.2.1 on port 8000
LXC-2:1 connect tcp 10.0.2.1 8000

# Send data string 'alice' on tcp connection from client side
LXC-2:1 data send "alice"

# Check data 'alice' is received server. Test is called '1_traffic_origin_direction'
# Parsing on server log file starts at mark "server ready"
LXC-1:1 check [1_traffic_origin_direction] data receive "alice" since "server ready"
												
# Append a mark "client ready" on client log file
LXC-2:1 mark "client ready"

# Send data string 'bob' on tcp connection from server side:
LXC-1:1 data send "bob"

# Check data 'bob' is received on client. Test is called '2_traffic_reply_direction'
# Search scope on client log file start at mark "client ready"
LXC-2:1 check [2_traffic_reply_direction] data receive "bob" since "client ready"

# Close tcp socket from client side:
LXC-1:1 close tcp

~~~


#### Vyos

Interact with vyos router. Does not generate tests results in reports.

~~~
# Change vyos device R1-B1 traffic-policy named 'WAN' settings 
R1-B1:1 traffic-policy WAN delay 10 loss 0
~~~

#### FortiGate
Interact with FortiGate device, generates test results and retrieve information added to the report.

###### Status

~~~
# Check that FGT-B1 VM license is Valid
FGT-B1-1:1 check [FGT-B1_license] status has license=True

# Get FortiGate firmware version and VM license status
# Added in the reports as respectively 'version' and 'license'
FGT-B1-1:1 get status
~~~


###### Sessions

Checks on FortiGate session table.
This command has a first 'filter' section to select the sessions. An implicit 'diag sys session filter clear' is done before the command. Allowed keywords are :  
['vd','sintf','dintf','src','nsrc','dst','proto','sport','nport','dport','policy','expire','duration','proto-state','session-state1','session-state2','ext-src','ext-dst','ext-src-negate','ext-dst-negate','negate']. Multiple selectors can be used if separated with space.  

Supported requirements : 'state', 'src','dest','sport','dport','proto','proto_state','duration','expire','timeout','dev','gwy','total' (number of sessions)
~~~
# Checks that a least a session with destination port 9000 exists
FGT-B1-1:1 check [session_tcp9000] session filter dport=9000

# Checks that a least a session with dport 22 and dest ip 192.168.0.1 exists
FGT-B1-1 check [ssh_session_exist] session filter dport=22 dest=192.168.0.1

# Checks that session with destination port 5000 has dirty flag set
FGT-B1-1 check [session_is_dirty] session filter dport=5000 has flag=dirty
~~~

###### IPsec tunnel

- Generic checks on IPsec based on `diagnose vpn ike status`
- flush all ike gateway 

~~~
# Flush all ike gateways ('diagnose vpn ike gateway flush') 
FGT-B1-1:1 flush ike gateway

# Check number of established ike tunnels
FGT-B1-1:1 check [B1_tunnels] ike status has ike_established=3

# Check number of established IPsec tunnels (created and established)
FGT-B1-1:1 check [B1_tunnels] ike status has ipsec_created=3 ipsec_established=3
~~~


###### BGP routes

Checks on routing table BGP from `get router info routing-table bgp`

~~~
# number of bgp routes is 4 :
FGT-B1-1 check [bgp_4_routes] bgp has total=4

# bgp route for subnet 10.0.0.0/24 exist :
FGT-B1-1 check [bgp_subnet_10.0.0.0] bgp has subnet=10.0.0.0/24

# bgp nexthop 10.255.1.253 exist
FGT-B1-1 check [bgp_nexthop_10.255.1.253] bgp has nexthop=10.255.1.253

# bgp has route toward interface vpn_mpls
FGT-B1-1 check [bgp_subnet_10.0.0.0] bgp has interface=vpn_mpls

# multiple requirements can be combined
FGT-B1-1 check [multi] bgp has nexthop=10.255.1.253 nexthop=10.255.2.253 subnet=10.0.0.0/24
FGT-A:1 check [route_ok] routing table bgp 10.0.0.0/24 next-hop 1.1.1.1 interface port1
~~~

###### SD-WAN

Various checks from `diagnose sys virtual-wan-link service __SERVICE__`

~~~
# check alive members :
FGT-B1-1 check [sdwan_1_member1_alive] sdwan service 1 member 1 has state=alive

# check sla value for a particular member (only available for sla type rule)
FGT-B1-1 check [sdwan_1_member1_sla] sdwan service 1 member 1 has sla=0x1

# check that member seq 1 is the preferred member on service 1 (aka rule 1)
FGT-B1-1 check [sdwan_1_preferred] sdwan service 1 member 1 has preferred=1
~~~


#### FortiPoC

Interact with FortiPoC to bring ports up or down
Using fpoc link up/down __device__ __port__

~~~
# Bring up link for FGT-B1-port1 switch side
fpoc:1 link up FGT-B1-1 port1

# Bring down link for FGT-B1-port1 switch side
fpoc:1 link down FGT-B1-1 port1
~~~


## Debug
When running, all debugs are stored in file debug.log
Usefull message (for instance to track syntax error in testcases definition) should be with level WARNING or ERROR.
Program is aborted for level ERROR.

sample :
~~~
20200317:17:25:30,198 DEBUG   [playbook  .    get_agent_type      :  319] name=HOSTS-B2 type=lxc
20200317:17:25:30,198 DEBUG   [playbook  .    _get_agent_from_tc_l:  347] Found corresponding type=lxc
20200317:17:25:30,198 DEBUG   [playbook  .    run_testcase        :  199] agent_name=HOSTS-B2 agent_type=lxc agent_conn=1
20200317:17:25:30,198 INFO    [playbook  .    _create_agent_conn  :  273] Enter with name=HOSTS-B2 type=lxc conn=1
20200317:17:25:30,198 DEBUG   [playbook  .    _create_agent_conn  :  283] agent=HOSTS-B2 is already in our list
20200317:17:25:30,198 DEBUG   [playbook  .    _create_agent_conn  :  303] Connection to HOSTS-B2:1 already exists
20200317:17:25:30,198 DEBUG   [playbook  .    run_testcase        :  219] Agent already existing
~~~