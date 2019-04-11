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
		self.elasticips = {}


	def _setup_session(self):
		_session = boto3.session.Session(region_name=self.region, profile_name=self.profile)
		return _session

	def _setup_client(self):
		_client = self.session.client("ec2")
		return _client

	def _setup_elb_client(self):  # "Elastic" load balancers have been renamed to "Classic",
		_elbclient = self.session.client("elb")  # but the SDK reflects the old name.
		return _elbclient

	def _setup_alb_client(self):  # Application & Network load balancers have a different client than ELBs
		_albclient = self.session.client("elbv2")
		return _albclient

	def _setup_resource(self):
		_resource = self.session.resource("ec2")
		return _resource


	def enumerate_servers(self):

		""" Queries all EC2 instances in the session.
		Each unique object is added as a nested dictionary to self.servers.
		Each nested dict contains associated tags, the current private IP & all available
		secondary IPs, public IP, AMI, instance type, attached IAM role,
		resource ID, private key name, and current state of each server:
		(running / stopped / terminated / etc).
		"""

		for _server in self.resource.instances.all():
			_secondaries = []

			self.servers[_server.instance_id] = {
				"Profile": self.profile,
				"Region": self.region,
				"Service": "EC2",
				"Resource": "Instance",
				"Instance ID": _server.instance_id,
				"Current Private IP": _server.private_ip_address,
				"Public IP": _server.public_ip_address,
				"State": _server.state["Name"],
				"AMI": _server.image_id,
				"Instance Type": _server.instance_type,
				"Key Name": _server.key_name,
			}

			try:  # Get all tags, add them to the dictionary. Passes if there are none.
				for _tag in _server.tags:
					self.servers[_server.instance_id][_tag["Key"]] = _tag["Value"]
			except TypeError:
				pass

			try:  # Get the IAM role attached to the instance.
				self.servers[_server.instance_id]["IAM Role"] = _server.iam_instance_profile["Arn"]
			except TypeError:
				pass

			try:  # Get all secondary IP addresses, and pass if there are none.
				for _address in _server.network_interfaces_attribute[0]["PrivateIpAddresses"]:
					_secondaries.append(_address["PrivateIpAddress"])
			except IndexError:
				pass

			self.servers[_server.instance_id]["Available Private IPs"] = ', '.join(_secondaries)

		self.servers = json.dumps(self.servers, indent=2)

	def enumerate_securitygroups(self):

		""" Queries all security groups in the session.
		Each unique resource is added as a nested dictionary to self.securitygroups.
		Each nested dict contains the name, resource ID, description, VPC, and tags of each group.
		"""

		for _group in self.resource.security_groups.all():

			self.securitygroups[_group.group_id] = {
				"Profile": self.profile,
				"Region": self.region,
				"Service": "EC2",
				"Resource": "Security Group",
				"Name": _group.group_name,
				"Group ID": _group.group_id,
				"Description": _group.description,
				"VPC": _group.vpc_id
			}

			try:  # Get all tags, add them to the dictionary. Passes if there are none.
				for _tag in _group.tags:
					self.securitygroups[_group.group_id][_tag["Key"]] = _tag["Value"]
			except TypeError:
				pass

		self.securitygroups = json.dumps(self.securitygroups, indent=2)

	def enumerate_networkinterfaces(self):

		""" Queries all network interfaces in the session.
		Each unique object is added as a nested dictionary to self.networkinterfaces.
		Each nested dict contains the current private IP & all available
		secondary IPs, public IP, DNS Name, resource ID, and tags of each network interface.
		"""

		for _interface in self.resource.network_interfaces.all():
			_secondaries = []

			self.networkinterfaces[_interface.network_interface_id] = {
				"Profile": self.profile,
				"Region": self.region,
				"Service": "EC2",
				"Resource": "Network Interface",
				"Interface ID": _interface.network_interface_id,
				"Current Private IP": _interface.private_ip_address
			}

			try:  # Get public IP address, or set to empty and pass if one isn't found.
				self.networkinterfaces[_interface.network_interface_id]["Public IP Address"] = _interface.private_ip_addresses[0]["Association"]["PublicIp"]
			except KeyError:
				pass

			try:  # Get public DNS name, or set to empty and pass if one isn't found.
				self.networkinterfaces[_interface.network_interface_id]["Public DNS Name"] = _interface.private_ip_addresses[0]["Association"]["PublicDnsName"]
			except KeyError:
				pass

			try:  # Get all tags, add them to the dictionary. Passes if there are none.
				for _tag in _interface.tag_set:
					self.networkinterfaces[_interface.network_interface_id][_tag["Key"]] = _tag["Value"]
			except KeyError:
				pass

			try:  # Get all secondary IP addresses, and pass if there are none.
				for _address in _interface.private_ip_addresses:
					_secondaries.append(_address["PrivateIpAddress"])
			except IndexError:
				pass

			self.networkinterfaces[_interface.network_interface_id]["Available Private IPs"] = ', '.join(_secondaries)

		self.networkinterfaces = json.dumps(self.networkinterfaces, indent=2)

	def enumerate_classiclbs(self):

		""" Queries all Classic load balancers in the session.
		Each unique object is added as a nested dictionary to self.classiclbs.
		Each nested dict contains the name, scheme (internal / external),
		DNS name, attached security groups, associated EC2 instances,
		and listening ports & protocols of each load balancer.
		"""

		_response = self.elbclient.describe_load_balancers()

		for _lb in _response["LoadBalancerDescriptions"]:
			_listeners = {}
			_attachments = []
			_securitygroups = []

			self.classiclbs[_lb["LoadBalancerName"]] = {
				"Profile": self.profile,
				"Region": self.region,
				"Service": "EC2",
				"Resource": "Load Balancer",
				"Type": "classic",
				"Scheme": _lb["Scheme"],
				"Name": _lb["LoadBalancerName"],
				"DNS Name": _lb["DNSName"]
			}

			for _listener in _lb["ListenerDescriptions"]:  # Get the listening ports and protocols, add to dict.
				_listeners[_listener["Listener"]["LoadBalancerPort"]] = _listener["Listener"]["Protocol"]

			for _instance in _lb["Instances"]:
				_attachments.append(_instance["InstanceId"])

			try:  # Get attached security groups, and pass if there aren't any.
				for _group in _lb["SecurityGroups"]:
					_securitygroups.append(_group)
			except KeyError:
				pass

			self.classiclbs[_lb["LoadBalancerName"]]["Attached Servers"] = ', '.join(_attachments)
			self.classiclbs[_lb["LoadBalancerName"]]["Security Groups"] = ', '.join(_securitygroups)
			self.classiclbs[_lb["LoadBalancerName"]]["Listeners"] = _listeners

		self.classiclbs = json.dumps(self.classiclbs, indent=2)

	def enumerate_applicationlbs(self):

		""" Queries all Application & Network load balancers in the session.
		Each unique object is added as a nested dictionary to self.applicationlbs.
		Each nested dict contains the name, type, scheme (internal / external),
		DNS name, and attached security groups of each load balancer.
		"""

		_response = self.albclient.describe_load_balancers()

		for _lb in _response["LoadBalancers"]:
			_securitygroups = []

			self.applicationlbs[_lb["LoadBalancerName"]] = {
				"Profile": self.profile,
				"Region": self.region,
				"Service": "EC2",
				"Resource": "Load Balancer",
				"Name": _lb["LoadBalancerName"],
				"Type": _lb["Type"],
				"Scheme": _lb["Scheme"],
				"DNS Name": _lb["DNSName"]
			}

			try:  # Get attached security groups, and pass if there aren't any.
				for _group in _lb["SecurityGroups"]:
					_securitygroups.append(_group)
			except KeyError:
				pass

			self.applicationlbs[_lb["LoadBalancerName"]]["Security Groups"] = ', '.join(_securitygroups)

		self.applicationlbs = json.dumps(self.applicationlbs, indent=2)

	def enumerate_elasticips(self):

		""" Queries all Elastic IP Addresses in the session.
		Each unique object is added as a nested dictionary to self.elasticips.
		Each nested dict contains the allocation ID, attached EC2 instance,
		network interface, private IP, public IP, and tags of each Elastic IP.
		"""

		_response = self.resource.vpc_addresses.all()

		for _address in _response:

			self.elasticips[_address.allocation_id] = {
				"Profile": self.profile,
				"Region": self.region,
				"Service": "EC2",
				"Resource": "Elastic IP",
				"Allocation ID": _address.allocation_id,
				"Attached Instance": _address.instance_id,
				"Network Interface":_address.network_interface_id,
				"Private IP": _address.private_ip_address,
				"Public IP": _address.public_ip
			}

			try:  # Get all tags, add them to the dictionary. Passes if there are none.
				for _tag in _address.tags:
					self.elasticips[_address.allocation_id][_tag["Key"]] = _tag["Value"]
			except TypeError:
				pass

		self.elasticips = json.dumps(self.elasticips, indent=2)