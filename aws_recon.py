import boto3
import json

class AwsSession:
	def __init__(self, profile, region):
		self.profile = profile
		self.region = region
		self.session = self._setup_session()
		self.client = self._setup_client()
		self.elbclient = self._setup_elb_client()
		self.albclient = self._setup_alb_client()
		self.resource = self._setup_resource()
		self.servers = {}
		self.securitygroups = {}
		self.networkinterfaces = {}
		self.classiclbs = {}
		self.applicationlbs = {}


	def _setup_session(self):
		_session = boto3.session.Session(region_name=self.region, profile_name=self.profile)
		return _session

	def _setup_client(self):
		_client = self.session.client("ec2")
		return _client

	def _setup_elb_client(self):  # "Elastic" load balancers have been renamed to "Classic",
		_elbclient = self.session.client("elb")  # but the SDK reflects the old name.
		return _elbclient

	def _setup_alb_client(self):  # Application load balancers have a different client than ELBs
		_albclient = self.session.client("elbv2")
		return _albclient

	def _setup_resource(self):
		_resource = self.session.resource("ec2")
		return _resource


	def enumerate_servers(self):

		""" Queries all EC2 instances in the session.
		Returns all associated tags, private + public IPs, and current state:
		(running / stopped / terminated / etc).
		"""

		for _server in self.resource.instances.all():
			_tags = { "Tags": {}}
			_secondaries = []

			try:  # Grab all tags, add them to the dictionary. Passes if there are none.
				for _tag in _server.tags:
					_tags["Tags"][_tag["Key"]] = _tag["Value"]
			except TypeError:
				pass

			try:  # Grab all secondary IP addresses, and pass if there are none.
				for _address in _server.network_interfaces_attribute[0]["PrivateIpAddresses"]:
					_secondaries.append(_address["PrivateIpAddress"])
			except IndexError:
				pass

			self.servers[_server.instance_id] = (
				{"Current Private IP": _server.private_ip_address},
				{"Public IP": _server.public_ip_address}, 
				{"State": _server.state["Name"]},
				{"AMI": _server.image_id},
				{"Instance Type": _server.instance_type},
				{"Key Name": _server.key_name},
				{"Role Profile": _server.iam_instance_profile},
				{"Available Private IPs": _secondaries},
				_tags
			)

		self.servers = json.dumps(self.servers, indent=2)

	def enumerate_securitygroups(self):

		""" Queries all security groups in the session.
		Returns ID, name, description, and associated VPC.
		"""

		for _group in self.resource.security_groups.all():
			_tags = { "Tags": {}}

			try:  # Grab all tags, add them to the dictionary. Passes if there are none.
				for _tag in _group.tags:
					_tags["Tags"][_tag["Key"]] = _tag["Value"]
			except TypeError:
				pass

			self.securitygroups[_group.group_id] = (
				{"Name": _group.group_name},
				{"Description": _group.description},
				{"VPC": _group.vpc_id},
				_tags
			)

		self.securitygroups = json.dumps(self.securitygroups, indent=2)

	def enumerate_networkinterfaces(self):

		""" Queries all network interfaces in the session.
		Returns ID, public addresses, private addresses, and tags.
		"""

		for _interface in self.resource.network_interfaces.all():
			_tags = { "Tags": {}}
			_secondaries = []

			try:  # Grab all tags, add them to the dictionary. Passes if there are none.
				for _tag in _interface.tag_set:
					_tags["Tags"][_tag["Key"]] = _tag["Value"]
			except KeyError:
				pass

			try:  # Grab all secondary IP addresses, and pass if there are none.
				for _address in _interface.private_ip_addresses:
					_secondaries.append(_address["PrivateIpAddress"])
			except IndexError:
				pass

			try:  # Grab public DNS name, or set to empty and pass if one isn't found.
				_publicdns = _interface.private_ip_addresses[0]["Association"]["PublicDnsName"]
			except KeyError:
				_publicdns = ""
				pass

			try:  # Grab public IP address, or set to empty and pass if one isn't found.
				_publicip = _interface.private_ip_addresses[0]["Association"]["PublicIp"]
			except KeyError:
				_publicip = ""
				pass

			self.networkinterfaces[_interface.network_interface_id] = (
				{"Public IP Address": _publicip},
				{"Public DNS Name": _publicdns},
				{"Current Private IP": _interface.private_ip_address},
				{"Available Private IPs": _secondaries},
				_tags
			)

		self.networkinterfaces = json.dumps(self.networkinterfaces, indent=2)

	def enumerate_classiclbs(self):

		""" Queries all Classic load balancers.
		Returns DNS name, scheme, security groups,
		attached servers, and listening ports.
		"""

		_response = self.elbclient.describe_load_balancers()

		for _lb in _response["LoadBalancerDescriptions"]:
			_listeners = {"Listeners": {}}
			_attachments = []
			_securitygroups = []

			for _listener in _lb["ListenerDescriptions"]:  # Grab the listening ports and protocols, add to dict.
				_listeners["Listeners"][_listener["Listener"]["LoadBalancerPort"]] = _listener["Listener"]["Protocol"]

			for _instance in _lb["Instances"]:
				_attachments.append(_instance["InstanceId"])

			try:  # Get attached security groups, and pass if there aren't any.
				for _group in _lb["SecurityGroups"]:
					_securitygroups.append(_group)
			except KeyError:
				pass

			self.classiclbs[_lb["LoadBalancerName"]] = (
				{"Type": "classic"},
				{"Scheme": _lb["Scheme"]},
				{"DNS Name": _lb["DNSName"]},
				{"Security Groups": _securitygroups},
				{"Attached Servers": _attachments},
				_listeners
			)

		self.classiclbs = json.dumps(self.classiclbs, indent=2)

	def enumerate_applicationlbs(self):

		""" Queries all Application & Network load balancers.
		Returns DNS name, scheme, security groups, and listening ports.
		"""

		_response = self.albclient.describe_load_balancers()

		for _lb in _response["LoadBalancers"]:
			_securitygroups = []

			try:  # Get attached security groups, and pass if there aren't any.
				for _group in _lb["SecurityGroups"]:
					_securitygroups.append(_group)
			except KeyError:
				pass

			self.applicationlbs[_lb["LoadBalancerName"]] = (
				{"Type": _lb["Type"]},
				{"Scheme": _lb["Scheme"]},
				{"DNS Name": _lb["DNSName"]},
				{"Security Groups": _securitygroups}
			)

		self.applicationlbs = json.dumps(self.applicationlbs, indent=2)