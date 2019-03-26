import boto3

class AwsSession:
	def __init__(self, profile, region):
		self.profile = profile
		self.region = region
		self.session = self._setup_session()
		self.client = self._setup_client()
		self.resource = self._setup_resource()
		self.servers = {}
		self.securitygroups = {}
		self.networkinterfaces = {}


	def _setup_session(self):
		_session = boto3.session.Session(region_name=self.region, profile_name=self.profile)
		return _session

	def _setup_client(self):
		_client = self.session.client("ec2")
		return _client

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

	def enumerate_securitygroups(self):

		""" Queries all security groups in the session.
		Returns ID, name, description, and associated VPC.
		"""

		for _group in self.resource.security_groups.all():
			self.securitygroups[_group.group_id] = (
				{"Name": _group.group_name},
				{"Description": _group.description},
				{"VPC": _group.vpc_id}
			)

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

			try: # Grab public DNS name, or set to empty and pass if one isn't found.
				_publicdns = _interface.private_ip_addresses[0]["Association"]["PublicDnsName"]
			except KeyError:
				_publicdns = ""
				pass

			try: # Grab public IP address, or set to empty and pass if one isn't found.
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