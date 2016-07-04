import json
import pprint

"""
Takes in clean JSON file (see sample.json), and creates session objects with the associated (readable) events.
"""

class OutputParser:
	def __init__(self, filename="cowrie.json.2016_4_22"):
		self.unassigned_events = {}
		self.unassigned_nonsessions = {}
		self.sessions = {}

		with open(filename, "r") as fin:
			for line in fin:
				try:
					d = json.loads(line)
				# if d.get('isError', 0):
				# 	print "Found error" #TODO: handle

					self.parse_dict(d)
				#print("_______________________________")
				#pprint.pprint(d)
				except: 
					pass

		self.assign_events()

		
	def parse_dict(self, d):
		switcher = {'cowrie.session.connect': Session}
		obj = switcher.get(d['eventid'], Event)(d)
		self.unassigned_events[obj.sid] = self.unassigned_events.get(obj.sid, []) + [obj]

	def assign_events(self):
		#assigns events to sessions
		new_unassigned = {}
		for sid in self.unassigned_events:
			for event in self.unassigned_events[sid]:
				if event.TAG == "SESSION":
					self.sessions[sid] = event
				else:
					if sid in self.sessions:
						self.sessions[sid].add_event(event)
					else:
						#print "WAT"
						new_unassigned[sid] = new_unassigned.get(sid, []) + [event]

		self.unassigned_events = new_unassigned


	def __str__(self):
		s = ''
		for v in self.sessions.values():
			s += str(v) + '\n'
		return s

		

class Session:
	TAG = "SESSION"
	def __init__(self, d):
		self.d = d
		
		"""
		Format of d:
			{u'dst_ip': u'127.0.0.1',
			 u'dst_port': 2222,
			 u'eventid': u'cowrie.session.connect',
			 u'format': u'New connection: %(src_ip)s:%(src_port)s (%(dst_ip)s:%(dst_port)s) [session: %(session)s]',
			 u'isError': 0,
			 u'message': [],
			 u'sensor': u'ip-172-31-52-233',
			 u'session': u'1287fb65',
			 u'src_ip': u'127.0.0.1',
			 u'src_port': 37047,
			 u'system': u'cowrie.ssh.transport.HoneyPotSSHFactory',
			 u'timestamp': u'2016-04-04T00:11:31.629291Z'}
		"""

		self.sid = d['session']
		self.timestamp = d['timestamp']
		self.src = (d['src_ip'], d['src_port'])
		self.dest = (d['dst_ip'], d['dst_port'])

		self.events = []

	def add_event(self, event):
		self.events.append(event)

	def __str__(self):
		s = str('SESSION ID: ' + self.sid + '\nTIMESTAMP: ' + self.timestamp + '\n')
		s += 'EVENTS: '
		for e in self.events:
			s+='\n\t' + str(e)
		return s

class SSHVersion:
	"""remote SSH version"""
	TAG = "SSH_VERSION"
	def __init__(self, d):
		self.d = d

		"""
		Examples of fields:
			u'sensor': u'ip-172-31-52-233',
			u'session': u'1287fb65',
			u'src_ip': u'127.0.0.1',
			u'system': u'HoneyPotTransport,0,127.0.0.1',
			u'timestamp': u'2016-04-04T00:11:31.631061Z',
			u'version': u'SSH-2.0-OpenSSH_6.6.1p1 Ubuntu-2ubuntu2.4'
		"""

		self.sid = d['session']
		self.sensor = d['sensor']
		self.src_ip = d['src_ip']
		self.system = d['system']
		self.timestamp = d['timestamp']
		self.version = d['version']

	def __str__(self):
		return "version: " + self.version

class Event:
	TAG = "EVENT"

	def __init__(self, d):
		self.d = d
		self.sid = d['session']
		self.format = d['format']
		self.event_id = d['eventid']
		self.description = self.get_description()

	def get_description(self):
		info = []
		descriptors = self.format.split('%(')
		info.append(descriptors[0])
		descriptors = descriptors[1:]
		descriptors = [elt.split(')')[0] for elt in descriptors]
		info += [(elt, self.d[elt]) for elt in descriptors]
		return info

	def __str__(self):
		return str(self.description)

"""
If you just want see main info for each session; 
to dig in, work in python interactive environment.
"""
def main(fname):
	o = OutputParser(filename=fname)
	#print o

