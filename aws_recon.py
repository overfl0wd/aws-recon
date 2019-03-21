import boto3

class AwsSession:
	def __init__(self, profile, region):
		self.profile = profile
		self.region = region
		self.session = self._setup_session()
		self.client = self._setup_client()
		self.resource = self._setup_resource()
		self.instances = {}


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

			try:
				for tags in _server.tags:
					_tags["Tags"][tags["Key"]] = tags["Value"]
			except TypeError:
				pass

			self.instances[_server.instance_id] = (
				{"Private IP": _server.private_ip_address}, 
				{"Public IP": _server.public_ip_address}, 
				{"State": _server.state["Name"]}, _tags
			)