#### Collecting ideas

- Could be called "Check-it-baby"

##### Objectives

- can run in FortiPoc LXC and drive LXC, vyos, fortigate, fpoc
- relies on netcontrol for device communication
- netcontrol now supports :
	- file tracing : devices ssh communication is dumped to a tracefile
	- file tracing writing : writing on the tracefile
	- file tracing marking : Write standardized marks (with timing) on the tracefile
- analysis of command output done from log trace analysis and using markings for delimeter
- test scenario should be recipies close to natural human
- scenario language :
	- support macros (defined or not in the test playbook) with variables (defined syntax by keyword)
	- handles multiple devices connections simultaneously
	- handles multiple connections to the same device
	- devices referenced by their names, definition of devices should be simple file and movable to a Django DB
	- keyword 'check' reserved for test assesment, would generate a test result
    - lines starting with # are comments
	- tabs or space should be allowed (but not mandatory)
	- sections are needed, starting with 'start', ending with 'end'.
		This is needed for playbook, testcase 
	- variables should be allowed in the playbook. They could be defined in the playbook or (futur) inherited from a DB

- Test runner :
	- reads the scenario in the playbook
	- ability to validate the test definition without running (staging)
	- spawn the different connections to the devices and keep them alive until closed when asked ('open')
	- test connection should allow TCP and use simple tools (like netcat)
	- should be possible to send new data further down on the scenario
	- a 'check' statement in the scenario would trigger a connection to the device and inspect the tracefile
	- a command should block until it is done (so the next command is not run too early)
	- Each testcase of a playbook may generated multiple test results
	- open connections are automatically closed at the end of the playbook
	- at the end of the playbook, a result json is provided :
		{ 'playbook' : playbook_name,
		  'date'     : timing information
		  'result'   : pass|fail|unknown
		  'testcases' : {
							TestCase_ID : [
											 CHECK_ID : 'pass',
											 'FGT-A check [reply packet] sniffer receive reply port port3' : pass,
											 'FGT-A check [session] session exist' : pass,
							              [
		               }
		}


##### Questions

- Q: is it possible with netcat in listen mode to send data from server to client ?
  A: yes, netcat -l do this naturally 


#### Syntax definition

##### LXC Connections
Open, connect, close connections and send data
Each action should generate automatically a mark for analysis.

- Open a tcp server :							LXC-1:1 open tcp <port>
												LXC-1:1 mark "server ready"
- Connect to a tcp server :						LXC-2:1 connect tcp <ip> <port>
- Send data on tcp connection from client :		LXC-2:1 data send "alice"
- Check data is received server :				LXC-1:1 check [server receive] data receive "alice" since "server ready"
												LXC-2:1 mark "client ready"
- Send data on tcp connection from server :     LXC-1:1 data send "bob"
- Check data is received on client :			LXC-2:1 check [client receive] data receive "bob" since "client ready"
- Close a tcp socket from client:				LXC-1:1 close tcp


Note : 
 - confirmation : netcat in listen mode (-l) allows to send STDIN chars to client side so both client and serveur can issue traffic
 - use syntax check data receive PATERN since MARK where MARK delimits the search start on the log file from a mark issued by command 'mark'

##### VYOS
Interact with vyos router

* network-emulator

- Set network emulator delay:			R1 network-emulator WAN delay 10
- Set network emulator packet loss:		R1 network-emulator WAN loss 1



##### FortiPoC
Interact with FortiPoC

- Bring port UP				: fpoc link up FGT-1 port1
- Bring port DOWN			: fpoc link down FGT-1 port1


##### FortiGate
Interact with FortiGate device


###### Sessions

- Checks a session exists on the FortiGate:	
	
	FGT-A:1 session filter clear
	FGT-A:1 session dst 8.8.8.8
	FGT-A:1 session dport 80
	FGT-A:1 check [session exist] session exist

- Check session duration is over a minimum :		FGT-A:1 session check duration over 10
- Check session flag :								FGT-A:1 session check flag dirty


###### Sniffer

	FGT-A:1 sniffer start any "host 1.1.1.1"			- append sniffer start mark
	FGT-A:1 sniffer stop                                - append sniffer stop mark
	FGT-A:1 check [sniffer reply port3] sniffer receive reply port port3      - check between start and stop mark (if no stop mark, check till eof)



###### IPsec tunnel

###### Routing table

- Check a route exist

	FGT-A:1 check [route ok] routing table bgp 10.0.0.0/24 next-hop 1.1.1.1 interface port1



##### Marks management
Add marks in the tracefile.
Marks could be used to define the scope of a text analysis in the tracefile (regexp)



##### Variable management:

- set a variable from the playbook :	set <variable> "value"
- use a variable :						#variable# 


##### Analysis
- Check pattern was received on tcp :	DEVICE:INSTANCE check receive <pattern> 
	check receive checks <pattern> exists in the tracefile from the mark of the session opening
	generates a result for the running playbook/testcase : PASS if pattern is received otherwise FAIL


##### Macros definition
Macros can be used by their name in a playbook file to simplify the writing of a testcase
Macros may involve multiple instances (provided as parameter)

Ex : macro start CHECK_TCP_CONNECTION <server_name_and_instance> <server_ip> <server_port> <client_name_and_instance> 


##### Example of testcase from a playbook

# Author: cgustave
# Date : xx/xx/xx
# Purpose : blabla

description : "Check two-way tcp connectivity between client and server"

# Define testcase variables
set CLIENTIP "10.0.0.1"
set SERVERIP "10.0.1.1"
set SERVERPORT "80"

# Start server tcp check
lxc-2:1 open tcp #SERVERPORT"
lxc-2:1 mark "start"

# Client connect to server
lxc-1:1 connect tcp #SERVERIP# #SERVERPORT#  
lxc-1:1 mark "start"

# Client to server check
lxc-1:1 send "ALICE"
lxc-2:1 check [1] receive "ALICE" since "start"

# Server to client check
lxc-2:1 send "BOB"
lxc-1:1 check [2] receive "BOB" since "start"

# Disconnect
lxc-1:1 close

##### objects models

class Testrunner(object)
    """
	Main application
	A testrunner contains :
	   - mutliple test agents with their definitions
	   - a single playbook containing the testcases
	   - a report structure filled from the testcases when run

	Directory structure
	/PLAYBOOK_BASE_PATH : The base name of the playbook location
	  ex : /fortipoc/playbooks

	/PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME
	  ex : /fortipoc/playbooks/advpn

	/PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/agents.conf  : files with agents definitions
	  ex : /fortipoc/playbooks/advpn/agents.conf

	/PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/testcases    : directory containing testcases
	  ex : /fortipoc/playbooks/advpn/testcases

	/PLAYBOOK_BASE_PATH/ANY_PLAYBOOK_NAME/testcases/NNN_TESTCASE_NAME : one testcase file
	                                   with NNN : a number starting from 000 (to order testcases)
									        TESTCASE_NAME : any name for the testcase

      ex : /fortipoc/playbooks/advpn/testcases/001_spoke_to_hub_connectivity.txt
      ex : /fortipoc/playbooks/advpn/testcases/002_spoke_ipsec_tunnel.txt
      ex : /fortipoc/playbooks/advpn/testcases/003_spoke_routing.txt
	
	


	"""

    def __init__(self, playbook_name="playbook"):
        """
		playbook_name : directory name where playbook files are stored (agents and testcases)
		"""
	    self.playbook = Playbook()
	    self.agents = {}      # dictionary of agent (keys are agents name)
		self.report = {}      # dictionary of reports (keys are reports name)

    def load_agents(self):
	    """
		Load all agent with their details
		Agents are stored in a file ? agents.conf
		Could then be stored in django DB table 'Agent'
		"""

	def get_agents(self):
	    """
		Requirements : previous call to load_agents
		Returns : dictionnary of agent (key agent name) to feed playbook
		"""

	def load_playbook(directory=""):
	    """
		Load the playbook represented by the directory
		Directory contains all testcases (one file per testcase)
		"""

	def run(self):
	    """
		Run the playbook
		"""

	def report(self):
	    """
		Provide a report from the run results
		"""


class Playbook(object):
    """
	A playbook is a collection of test cases
	It references agents but don't define them
	"""

	def __init__(self, description='', directory=''):

	    self.description = description  
	    self.directory = directory
	    self.testcases = []  
		self.agents = {}     # dictionnary by agent name

	def add_agent(self, name='', type='', ):
	    """
		Adds an agent to our list of agent
		Agent information should be retrieved as a dictionnary from Testrunner
		"""

	def load(self):
	    """ 
		Loads the testcases from the playbook directory. 
	    Each files from the directory with extension ".test" is a testcase
		Calls Testcase.load for each file
		Adds each testcase to the list testcase list 
		Loads all agents details (from file then later from Django DB)
		"""

		self.testcase_list.append

    def list_testcases(self):
	    """
		Provide the summary of the loaded testcases
		"""


class Testcase(object):
    """
	Defines one testcase.
	Contains a list of test "agent" (anything we can interact with)
	"""

	def __init__(self, description=''):
	    self.description = description   
		self.variables = {}   # dictionary of variables (keys is the variable name)
		self.commands = []    # list of command lines 

	def load(self, file=''):
	    """
		Load the testcase file.
		Extract the variables information and load them in the variables dictionary
		Extract the Agent information and load them in the agents dictionary
		Extracts all command lines and load then in a list
		"""

    def add_variable(self, variable=''):
	    """
		Adds a variable to our variable dictionary
		"""
 
    def add_commands(self, line):
	    """
		Adds command lines to our commands list
		"""

    def dump(self):
	    """
        Returns a json representing the view of the testcase : variables, agents, commands)
		"""

class Agent(object):
    """
	Any device we can interract with is considered a test "agent"
	It could be an LXC, a Vyos router, a FortiGate
	An agent has a type, an ip address and access details
	Multiple connection may exist to the agent so it has a list of connections instances stored in instance_list
    """

	def __init__(self, type='', ip='', user='', password='', ssh_key_file=''):
	    self.type = type
		self.ip = ip
		self.user = user
		self.password = password
		self.ssh_key_file = ssh_key_file
		self.connections = {}   # This is a dictionary where the key is the instance index 0, 1, 2 ...

	def connect(self):
	    """
		Connects a new instance to the agent, add this connection to the connection_list (accessible by index)
		This should be a generic function common to all types of agent which all use ssh
		Make sure no connection instance is already exising (if so, don't connect)
		Returns : True if a new connection was done, false if the connection was already existing
		"""

    def is_connected(self, instance):
	    """
		Returns True if the instance is already connected, otherwise returns False
		"""

	def close(self):
	    """
        Closes the connection instance.
		Returns True if the connection was existing and was closed. False if no connection instance was existing
		"""

    def get_instance(self, command_line=""):
	    """
		Analyse the given command_line format <AGENT>:<INSTANCE> XXXX
		returns : instance
		Exception : die with error message if instance could not be extracted from command line
		"""

    def mark(self):
	    """
		Appends a mark to the agent log file. Generic to all agent.
		Return : Undef
		"""



from Agent import Agent

class Lxc(Agent):
    """
	Specific LXC agent class
	"""

	def __init__(self, ip='', user='', password='', ssh_key_file=''):

	    super(Lxc,self).__init__(type='lxc', ip=self.ip, user=self.user, password=self.password, ssh_key_file=self.ssh_key_file


    def interpreter(self, dryrun=True):
	    """
        Analyse a line of command for a type LXC.
		Determines the instances (call Agent.get_instance)
		Determines the function to call and its parameters, call the action function (include dryrun=True|False) to each action
		Returns True if the function to call could be identified from the command line
		"""

	def open(self, instance=instance, protocol='tcp', port=''):
	    """
		Calls Agent.connect
		Opens a new tcp connection in listen mode on given port using  lxc using nc -l port
		"""

	def connect(self, protocol='tcp', ip='', port=''):
	    """
		Calls Agent.connect
		Opens a new tcp connection as a client to the provided ip and port
		"""

	def send(self, data=''):
	    """
		Pre-requisite : session should have been opened (check with agent.is_connected(instance)
		Sends data to an opened connection for both client side or server side
		"""_

    def check_receive_since(self, data='', since=''):
	    """
        Checks data has been received on the instance looking for pattern 'data' in session trace file, starting from last seen 'since' marks
        Returns True if confirmed received
		"""
