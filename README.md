# Checkitbaby

## Definition

Checkitbaby is a tool to allow automatic test validations in a lab.
It uses some **Agents** to interact with the setup, for instance to play a simple client/server role, to change the setup topology or even to query the DUT. Agents are connected using ssh. It is recommended to use ssh keys.  

**Playbooks** are defined as a collection of **Testcases**, each testcase is a simple text file where each line defines an action applied to an **Agent**.
Each line of the testcase can either trigger an action and/or get some information and see if some requirements are met (checks).  
Test scenario syntax is simple and evolutive, commands are defined keywords and depend on the type of agents targeted.  
Multiple simultaneous connections to agents are supported.
**Variables** are allowed  in testcases. A variable is just a keyword encompassed with dollar signs '$' and defined in a variable file.
During testcases execution, each **Run** information such as agent terminal ouputs are collected in log files. Test verifications are always done from log file parsing, like a human would do. With this, it is possible to easily double-check the test result post-run.  **Marks** can be used as a delimeter for check verification within the agent log file.  

Checkitbaby can be simply run as a script to run all or some testcases against the setup. It is possible to run the testcase in **Dry-Run** mode to only validate the scenarios file syntax for staging purpose.  

Checkitbaby focus is to run against a FortiPoc setup, either from withing the PoC (from a testing lxc) or externaly to PoC (from user PC). It can however be used in other contexts.  


There are multiple ways to run a playbook:

- Run the **entire playbook** :  
  `python3 run_playbook --playbook <playbook_name> [--feedback <feedback_file> --run <run_id> --debug]`

- Run a **single testcase** from the playbook by its id :  
  `python3 run_playbook --playbook <playbook_name> --testcase <test_case_id> [--feedback <feedback_file> ]`

- Run a **playlist** of testcases from the playbook, defined in `conf/playlists.yml`:  
  `python3 run_playbook --playbook <playbook_name> --playlist <playlist_id> [--feedback <feedback_file> --run <run_id> --debug]`

For each possibility, it is possible to set options:

  `--feedback <feedback>` : Feedback file expected from taskwatcher  
  `--run`    : Designate the run directory where results will be stored  
  `--dryrun` : Only performs a dry-run to validate scenario syntax (no connections to agents)  
  `--debug`  : Turns debugging on (debug output in file debug.log)  

When all the testcases from a Playbook have run, a **Report** in a json format is created. The report is organized by testcases and includes all checks results from the testcase.
A general Pass/Fail covering all testcases is also included.  

## Author
Cedric GUSTAVE


## Installation

- Requirements : netcontrol python library: `pip3 install -I netcontrol`
- Package is hosted on pypi, it should be installed using pip: `pip3 install -I checkitbaby`


## Usage

##### Command line:

~~~
Usage: python3 run_playbook.py -playbook <playbookName>

Optional settings:

    --playlist <playlist_id>
    --testcase <tescase_id>
    --run <run_id>
    --dryrun
    --debug
~~~

##### Examples

  * Running all testcases from a playbook :  
    ex : `python3 run_playbook.py --playbook myPlaybook --path PlayBookPath`

  * Running a specific testcase from a playbook :  
	ex : `python3 run_playbook.py --playbook myPlaybook --testcase 003 --path PlayBookPath`

  * Running a specific playlist from a playbook :
    ex : `python3 run_playbook.py --playbook myPlaybook --playlist PL01 --path PlayBookPath`


##### Web integration:

There is currently no web integration, this is however in the pipe.  
A web GUI would be provided to : load, select and run the defined testcases and provide a formated report.


## Organization

#### File tree structure

The following directory tree structure is used to organize the tests :

- Directory structure:
~~~
/PLAYBOOK_BASE_PATH : The base name of the playbook location
	  ex : /fortipoc/playbooks

/PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME
	  ex : /fortipoc/playbooks/advpn

/PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/conf/agents.yml: files with agents definitions
	  ex : /fortipoc/playbooks/advpn/conf/agents.yml

/PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/conf/variables.yml : files with variables definitions
	  ex : /fortipoc/playbooks/advpn/conf/variables.yml

/PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/conf/macros.txt : files with macro definitions
	  ex : /fortipoc/playbooks/advpn/conf/macros.txt

/PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/testcases : directory containing testcases
	  ex : /fortipoc/playbooks/advpn/testcases

/PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/testcases/NNN_TESTCASE_NAME : one testcase file  
     with NNN : a number starting from 000 (to order testcases)
	 TESTCASE_NAME : any name for the testcase

      ex : /fortipoc/playbooks/advpn/testcases/001_spoke_to_hub_connectivity.txt
      ex : /fortipoc/playbooks/advpn/testcases/002_spoke_ipsec_tunnel.txt
      ex : /fortipoc/playbooks/advpn/testcases/003_spoke_routing.txt
~~~

* Creating a new playbook:

Use `create_new_playbook.sh` to create a new playbook file tree:  
`Usage : ./create_new_playbook.sh <playbook_name>`



## Agents

Currently supported agents are :
  - Debian LXC (aka Linux host)
  - Vyos routers
  - FortiGate devices
  - FortiPoC VMs
  - Fortiswitches

A few agent-less functions are defined (for instance to wait or append some comments or *standard marks* in the logs)

The generic syntax of each line of a testcase is as follow :  
`<AGENT_NAME>:<AGENT_CONNECTION_ID>  <COMMAND> <COMMAND_SPECIFIC_DATA> `

Each test/validation uses command 'check' followed by the test reference between square bracket [TEST_NAME].  
The _TEST_NAME_ should be unique in the testcase file.  
A check may include a single or a list of *Requirements*. Requirements follow keyword 'has', they are provided as key=value pairs separated by spaces.
A test pass if all provided requirements are met. If no requirements are provided, the test check would be succefull if an occurence was found.  

Each line starting with comment sign '#' are ignored.  
Lines are ran sequentially.   

SSH connections to agents are automatically opened and closed at the end of the testcase.  

The following chapter defines each agent command syntax and support.  


#### Generic commands

Following commands are not agent specific and can be used with all agents

##### message "my message"
~~~
# Append a message on the user output when running the testcase
# This message is not append on the agent log file.
message "set Branch 1 connections delays and losses"
~~~

##### mark "mark_id"
~~~
# Appends a mark on the agent log file (but not on user output)
# This should be used to delimit checks parsing start (see check command 'since')
HOSTS-B2:1 mark "receive_ready"
~~~

##### skip all
~~~
# Skip all following lines from the testcase
skip all
~~~

##### wait (in seconds)
~~~
# Wait a number of seconds
wait 30
~~~


#### Debian LXC

###### Requirements

Install the following package :
`apt-get install hping3 iperf iptraf smcroute`


###### ping test
optional maxloss and maxdelay requirements

~~~
# Ping test, pass if at least one packet is not lost
# Delay and loss are added in the report
LXC1-1:1 ping [con_test] 10.0.2.1

# Ping test, pass if maximum packet loss under 50 %
LXC1-1:1 ping [con_test] 10.0.2.1 maxloss 50

# Ping test, pass if delay is < 10 ms
# Uses variables $google_dns$ defined in conf/variables.yml

clt-1:2 ping [fail_delay_conntest] $google_dns$ maxdelay 10
~~~

###### connection test

Connection (UDP or TCP) one way or two-way test.  
Open, connect, close connections and send data. It is recommended to use 'marks' to limit the check parsing area.
Connectivity test is using netcat-openbsd package *which has a different syntax than netcat-traditional to specify listening port*.  
Make sure netcat-openbsd is installed otherwise server would listen on a random port (netcat-traditional is expecting -l -p PORT whild bsd wants -l PORT

~~~
# Open a tcp server on port 8000  on agent LXC-1 from its connection 1
LXC-1:1 open tcp 8000

# Append a mark in LXC-1:1 log file
LXC-1:1 mark "server ready"

# Connect to a tcp server at ip 10.0.2.1 on port 8000
LXC-2:1 connect tcp 10.0.2.1 8000

# Send data string 'alice' on tcp connection from client side
LXC-2:1 send "alice"

# Check data 'alice' is received server. Test is called '1_traffic_origin_direction'
# Parsing on server log file starts at mark "server ready"
LXC-1:1 check [1_traffic_origin_direction] data receive "alice" since "server ready"

# Append a mark "client ready" on client log file
LXC-2:1 mark "client ready"

# Send data string 'bob' on tcp connection from server side:
LXC-1:1 send "bob"

# Check data 'bob' is received on client. Test is called '2_traffic_reply_direction'
# Search scope on client log file start at mark "client ready"
LXC-2:1 check [2_traffic_reply_direction] data receive "bob" since "client ready"

# Close tcp socket from client side:
LXC-1:1 close tcp
~~~

###### Multicast tests

Mutlicast test tools.  
Requires packages : hping3, smcroute, netcat-openbsd  
Agent can join or leave a multicast group, listen, send some message and check message has been received on receiver.  

~~~
# Join multicast group 239.1.1.1 from interface eth1
lxc22:1 join multicast eth1 239.1.1.1

# Listen multicast group 239.1.1.1 on port 5000
lxc22:1 listen multicast 239.1.1.1 port 5000

# Send a udp mutlicast message "hihihi" to group 239.1.1.1 from source port 10000 to destination port 5000
lxc12:1 send multicast 239.1.1.1 sport 10000 dport 5000 "hihihi"

# Check message hihihi has been seen on the receiver
lxc22:1 check [mctest] "hihihi

# Leave multicast group 239.1.1.1 from interface eth1
lxc22:1 leave multicast eth1 239.1.1.1
~~~


#### Vyos

Interact with Vyos routers. Does not generate tests results in reports.

###### traffic-policy
Changes the defined traffic-policy values
~~~
# Change vyos device R1-B1 traffic-policy named 'WAN' settings
R1-B1:1 traffic-policy WAN delay 10 loss 0
~~~

#### FortiGate
Interact with FortiGate device, generates test results and retrieve information added to the report.  
Vdoms are supported, add keyword vdom=_vdom_name_ in the command line, examples :
- to check vdom 'customer' has 12 bgp routes with 8 of them recursive routes:  
  `F1B2:1 check [bgp_routes] route bgp vdom=customer has total=12 recursive=8`

- to check ssh session exist in vdom customer:  
  `F1B2:1 check [ssh_session_exists] session vdom=customer filter dport=22`

- to check SDWAN member is alive in SDWAN Rule 1 on vdom 'customer':  
  `check [sdwan_service] sdwan vdom=customer service 1 member 1 has status=alive`

Commands are organized in groups: (system, execute, session, ipsec, route, sdwan...)
described below with their associated command syntax.  


##### System
Commands related to FortiGate system:

###### status:
~~~
# Check FGT-B1 VM license is Valid
FGT-B1-1:1 check [FGT-B1_license] system status has license=True

# Get FortiGate firmware version and VM license status
# Added in the reports as respectively 'version' and 'license'
FGT-B1-1:1 get system status
~~~

##### Execute
Commands and checks related to Fortigate cli 'execute' commands

###### Ping
Ping check from the the fortigate itself. Send 5 adaptive pings, test pass if no pings are dropped.  
Possible options: vdom=_vdom_name_ source=_source_ip_  
Packets transmited, received and dropped are added in the report.  
Examples:  
- no vdom, no options:  
	`FGT-B1-1:1 check [ping_test] ping 192.168.0.254`

- specific vdom:  
	`FGT-B1-1:1 check [ping_test] ping vdom=root 192.168.0.254`

- using a specific source-ip address:  
	`FGT-B1-1:1 check [ping_test] ping vdom=root source=192.168.0.1 192.168.0.254`


##### Session

Checks on FortiGate session table.
This command has a first **'filter'** section to select the sessions. An implicit 'diag sys session filter clear' is done before the command. Allowed keywords are :  
['vd','sintf','dintf','src','nsrc','dst','proto','sport','nport','dport','policy','expire','duration','proto-state','session-state1','session-state2','ext-src','ext-dst','ext-src-negate','ext-dst-negate','negate']. Multiple selectors can be used if separated with space.  

Supported requirements : 'state', 'src','dest','sport','dport','proto','proto_state','duration','expire','timeout','dev','gwy','total' (number of sessions)
~~~
# Checks that a least a session with destination port 9000 exists
FGT-B1-1:1 check [session_tcp9000] session filter dport=9000

# Checks that a least a session with dport 22 and dest ip 192.168.0.1 exists
FGT-B1-1 check [ssh_session_exist] session filter dport=22 dst=192.168.0.1

# Checks that session with destination port 5000 has dirty flag set
FGT-B1-1 check [session_is_dirty] session filter dport=5000 has state=dirty
~~~

##### IPsec

- Generic checks on IPsec `diagnose vpn ike status`
- flush all ike gateway

###### IKE
Ike related commands based on `diagnose vpn ike status` and `diagnose vpn ike gateway flush`
~~~
# Flush all ike gateways ('diagnose vpn ike gateway flush')
FGT-B1-1:1 flush ipsec ike gateway

# Check number of established ike tunnels
FGT-B1-1:1 check [B1_tunnels] ipsec ike status has ike_established=3

# Check number of established IPsec tunnels (created and established)
FGT-B1-1:1 check [B1_tunnels] ipsec ike status has ipsec_created=3 ipsec_established=3
~~~


##### route
Commands related to fortigate routing table.

###### BGP:
Checks on routing table BGP from `get router info routing-table bgp`.  
Examples:
~~~
# number of bgp routes in vdom root is 4:
FGT-B1-1 check [bgp_4_routes] route bgp vdom=root has total=4

# at least 1 bgp route for subnet 10.0.0.0/24 exists:
FGT-B1-1 check [bgp_subnet_10.0.0.0] route bgp has subnet=10.0.0.0/24

# at least 1 bgp route with nexthop 10.255.1.253 exists:
FGT-B1-1 check [bgp_nexthop_10.255.1.253] route bgp has nexthop=10.255.1.253

# at least 1 bgp route toward interface vpn_mpls exists:
FGT-B1-1 check [bgp_subnet_10.0.0.0] route bgp has interface=vpn_mpls

# multiple requirements may be combined:
FGT-B1-1 check [multi] route bgp has nexthop=10.255.1.253 nexthop=10.255.2.253 subnet=10.0.0.0/24
FGT-A1:1 check [mutli] route bgp has subnet=10.0.0.0/24 next-hop=1.1.1.1 interface=port1
~~~

##### SD-WAN

Various checks from `diagnose sys sdwan service <SERVICE>`  
For v6.2 version, make sure to add version=6.2 at the end of the line or before the requirements (has)
This would make use of old diag command 'diag sys virtual-wan-link'.

~~~
# check alive members :
FGT-B1-1 check [sdwan_1_member1_alive] sdwan service 1 member 1 has status=alive

# check sla value for a particular member (only available for sla type rule)
FGT-B1-1 check [sdwan_1_member1_sla] sdwan service 1 member 1 has sla=0x1

# check that member seq 1 is the preferred member on service 1 (aka rule 1)
FGT-B1-1 check [sdwan_1_preferred] sdwan service 1 member 1 has preferred=1

# Check on a v6.2 version
FGT-B1-1:1 check [sdwan] sdwan vdom=root service 1 member 1 version=6.2 has sla=0x1
~~~

##### Multicast

Checks on multicast for IGMP groups and mroutes from:
 `get router info multicast igmp groups`
 `diag ip multicast mroute`

~~~
# get multicast groups without requirements on vdom named 'multicast'
FGT-B1-1 check [igmp_groups] multicast igmp groups

# check group 239.0.0.1 is known from igmp
FGT-B1-1 check [igmp_groups] multicast igmp groups has group=239.0.0.1

# check at least 1 multicast route exists on vdom
FGT-B1-1 check [mroute] multicast vdom=multicast mroute

# check a specific multicast mroute 239.1.1.1 exists on the vdom
FGT-B1-1 check [mroute] multicast vdom=multicast mroute has group=239.1.1.1

# check a specific multicast mroute 239.1.1.1 exists on the vdom from source 10.1.1.12
FGT-B1-1 check [mroute] multicast vdom=multicast mroute has group=239.1.1.1 source=10.1.1.12
~~~


##### BFD

Checks on BFD for neighbors states
 `get router info bfd neighbor`

~~~
# get bfd neighbor without requirements on vdom named 'bfd'
# returns True if the given neighbor is found (in whichever state)
FGT-B1-1:1 check [bfd_neighbors] bfd vdom=bfd neighbor 172.18.1.9

# check neighbor 172.17.18.9 exists and is in state UP
FGT-B1-1:1 check [bfd_neighbor_up] bfd vdom=bfd neighbor 172.18.1.9 has state=up
~~~

##### HA

Checks on HA status: `get system ha status` (in global)
  - checks ha report unit healthy (HA Health Status: OK)
  - checks if unit with the given hostname is master or slave  ()
  - checks how many units are seen in the cluster
  - Checks if a given serial number is know in the cluster
  - checks if all members have their configuration synchronized (configuration status -> in-sync)

~~~
# check HA status reports health is OK
FGT-B1-1:1 check [ha_health] ha status has health=ok

# check if unit with name FGT-B1-1 is master
FGT-B1-1:1 check [ha_is_master] ha status has master=FGT-B1-1

# check if unit with name FGT-B1-2 is slave
FGT-B1-2:1 check [ha_is_slave] ha status has slave=FGT-B1-2

# check number of devices reported is 2 devices  
FGT-B1-1:1 check [ha_nb] ha status has nb=2

# check ha device with given serial is seen in cluster
FGT-B1-1:1 check [ha_nb] ha status has serial=FGVM08TM20005010 serial=FGVM08TM20005011

# check all devices reported have their config in-sync
FGT-B1-1:1 check [ha_sync] ha status has config=synchronized

# Example of check with combined requirements (all need to pass)
FGT-B1-1:1 check [ha_nb] ha status has master=FGT-B1-1 slave=FGT-B1-2 nb=2 config=synchronized serial=FGVM08TM20005010 serial=FGVM08TM20005011 health=ok
~~~

HA related actions: `diagnose sys ha reset-uptime`
  - reset ha uptime
~~~
# Reset unit ha uptime
FGT-B1-1:1 ha reset-uptime
~~~  


#### FortiPoC

Interact with FortiPoC to bring ports up or down
Using fpoc link up/down __device__ __port__

##### link up / link down
~~~
# Bring up link for FGT-B1-port1 switch side
fpoc:1 link up FGT-B1-1 port1

# Bring down link for FGT-B1-port1 switch side
fpoc:1 link down FGT-B1-1 port1
~~~


#### Fortiswitch

Interact with FortiSwitch (hardware or VM) to bring ports admin up or down
Check status of a port1 and eventually expect a certain state

##### link up / link down
~~~
# Bring port admin up
fsw:1 port up port10

# Bring port admin down
fsw:1 port down port10
~~~

##### check port link status
~~~
# Check to get port status for record only purpose
fsw:1 check [status_port10] port status port10

# Check port status and expect status to be up
fsw:1 check [status_port10] port status port10 has state=up
~~~


## Debug

All debugs are stored in file 'debug.log'  
Usefull messages (for instance to track syntax error in testcases definition) should be with level WARNING or ERROR.
Program is aborted for level ERROR.

Log level is 'INFO' by default but it can be adjusted to DEBUG using optional `--debug`

### sample
~~~
20200317:17:25:30,198 DEBUG   [playbook  .    get_agent_type      :  319] name=HOSTS-B2 type=lxc
20200317:17:25:30,198 DEBUG   [playbook  .    _get_agent_from_tc_l:  347] Found corresponding type=lxc
20200317:17:25:30,198 DEBUG   [playbook  .    run_testcase        :  199] agent_name=HOSTS-B2 agent_type=lxc agent_conn=1
20200317:17:25:30,198 INFO    [playbook  .    _create_agent_conn  :  273] Enter with name=HOSTS-B2 type=lxc conn=1
20200317:17:25:30,198 DEBUG   [playbook  .    _create_agent_conn  :  283] agent=HOSTS-B2 is already in our list
20200317:17:25:30,198 DEBUG   [playbook  .    _create_agent_conn  :  303] Connection to HOSTS-B2:1 already exists
20200317:17:25:30,198 DEBUG   [playbook  .    run_testcase        :  219] Agent already existing
~~~


### Feedback file values

Setting a feedback file is optinal. When enabled, a live flow of information from the running test will be sent to a 'feedback' file.
Information are formatted to be interpretted by a program, for instance to update a progress bar on web intergration.
The primary goal is to allow a web integration to checkitbaby.
Feedback files are not required when running checkitbaby as a script from command line.

Lists of possible feedback values implemented :
~~~
[playbook_path]     : Path to playbook top directory
[playbook]          : playbook name
[run]               : run id
[testcase_id]	    : id of testcase
[testcase_name]     : name of testcase
[testcase_progress] : percentage of progress for the testcase
[playlist_id]       : name of the playlist
[progress]			: Overall progress for playbook, playlist or individual testcase
[start_time]        : starting time in unix time
[end_time]          : ending time in unix time
~~~


### Files samples

### conf/macros.txt

This is a sample macro file, in `playbooks/PLAYBOOK_NAME/conf/macros.txt`  
Note that a variable 'server' is used in the macro, it is emcompassed with double-dollars '$$'.  
This is made sso $$server$$ is translated to $server$ in the scenario during macro expansion, then variable 'server' (in conf/variables.xml) will be used to replace $server$ in the scenario.  
###### Example of a macro call

Use & to reference a macro.
`&tcp_connection_check(H1B1,1,H1B2,1,9000)`  

###### Definition:
Macros are defined in conf/macros.txt

~~~
# Macro for connectivity check, one-way
macro tcp_connection_check(client,client_conn,server,server_conn,port):

# create a random message
set server_ready = random_string(8)
set message = random_string(8)
set test_id = random_string(4)

# Open server on the given port
$server$:$server_conn$ open tcp $port$
$server$:$server_conn$ mark "$server_ready$"

# Client connects
$client$:$client_conn$ connect tcp $$server$$ $port$

# Client send data on forward direction
$client$:$client_conn$ send "$message$"

# Server checks message is received
$server$:$server_conn$ check [tcp_forward_$test_id$] "$message$" since "$server_ready$"

# Closing
$client$:$client_conn$ close
$server$:$server_conn$ close
end

# ---

# Macro for connectivity check, two-way
# uses a double-translation for client and server that need to be defined

macro tcp_connection_twoway_check(client,client_conn,server,server_conn,port):

# create a random message
set server_ready = random_string(8)
set client_ready = random_string(8)
set message1 = random_string(8)
set message2 = random_string(8)
set test_id = random_string(4)

# Open server on the given port
$server$:$server_conn$ open tcp $port$
$server$:$server_conn$ mark "$server_ready$"

# Client connects
$client$:$client_conn$ connect tcp $$server$$ $port$

# Client send data on forward direction
$client$:$client_conn$ send "$message1$"
$client$:$client_conn$ mark "$client_ready$"

# Server checks message1 is received
$server$:$server_conn$ check [tcp_forward_$test_id$] "$message1$" since "$server_ready$"

# Server send data on reply direction
$server$:$server_conn$ send "$message2$"

# Client checks message2 is received
$client$:$client_conn$ check [tcp_reply_$test_id$] "$message2$" since "$client_ready$"


# Closing
$client$:$client_conn$ close
$server$:$server_conn$ close
end
~~~

### conf/variables.yml

```yamel
---
# checkitbaby variables definition file

srv-1: 127.0.0.1
cli-1: 127.0.0.1
localhost: 127.0.0.1
google_dns: 8.8.8.8
unreachable_host: 169.254.33.111
```


### conf/agents.yml

```yamel
---
# checkitbaby agents definition file

# LXC

clt-1:
  type: lxc
  ip: 127.0.0.1
  port: 22
  login: cgustave
  password: ''
  ssh_key_file: "/home/cgustave/.ssh/id_rsa"

srv-1:
  type: lxc
  ip: 127.0.0.1
  port: 22
  login: cgustave
  password: ''
  ssh_key_file: "/home/cgustave/.ssh/id_rsa"

# Vyos

R1-B1:
  type: vyos
  ip: 192.168.122.178
  port: '10111'
  login: vyos
  password: vyos
  ssh_key_file: "/home/cgustave/github/python/checkitbaby/checkitbaby/playbooks/test/conf/id_rsa"

R2-B1:
  type: vyos
  ip: 192.168.122.178
  port: '10113'
  login: vyos
  password: vyos
  ssh_key_file: "/home/cgustave/github/python/checkitbaby/checkitbaby/playbooks/test/conf/id_rsa"

# FortiPoC

fpoc:
  type: fortipoc
  ip: 192.168.122.178
  port: '22'
  login: admin
  password: ''
  ssh_key_file: ''

# FortiGate

FGT-B1-1:
  type: fortigate
  ip: 192.168.122.178
  port: '10101'
  login: admin
  password: ''
  ssh_key_file: ''

FGT-B2-9:
  type: fortigate
  ip: 192.168.122.178
  port: '10102'
  login: admin
  password: ''
  ssh_key_file: ''
```

### conf/playlists.yml

This is a sample of a playlist file

```yamel
---
# checkitbaby playlist definition file

PL01:
  comment: All LXC tests
  list:
  - '010'
  - '011'
```



### run/1/report.json

This is a sample of a report after a run with --run 1

```json
{
    "result": true,
    "testcases": {
	    "010": {
            "result": true,
            "check": {
			    "origin": true,
                "reply": true
            },
		    "get": {}
        },
        "011": {
		    "result": true,
            "check": {
                "tcp_forward_T69I": true,
				"tcp_reply_T69I": true
            },
            "get": {}
		}
    }
}
```
