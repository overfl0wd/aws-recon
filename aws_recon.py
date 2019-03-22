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
		""" Queries all EC2 instances in the account.
		Returns all associated tags, private + public IPs, and current state:
		(running / stopped / terminated / etc).
		"""
		for _server in self.resource.instances.all():
			_tags = { "Tags": {}}
			_secondaries = []

			try:  # Grab all tags, add them to the dictionary. Passes if there are none.
				for tags in _server.tags:
					_tags["Tags"][tags["Key"]] = tags["Value"]
			except TypeError:
				pass

			try:  # Grab all secondary IP addresses, and pass if there are none.
				for item in _server.network_interfaces_attribute[0]["PrivateIpAddresses"]:
					_secondaries.append(item["PrivateIpAddress"])
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
		Returns group name, description, VPC, and ID.
		"""
		_response = self.client.describe_security_groups()

		for _group in _response["SecurityGroups"]:
			self.securitygroups[_group["GroupId"]] = (
				{"Name": _group["GroupName"]},
				{"Description": _group["Description"]},
				{"VPC": _group["VpcId"]}
			)