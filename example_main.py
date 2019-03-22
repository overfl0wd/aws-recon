from aws_recon import AwsSession


test_class = AwsSession("production", "us-east-1")

""" Initialize the AWS Session class above.
Pass a profile name from your configs (~/.aws/),
as well as a region to use.
"""

test_class.enumerate_servers()
test_class.enumerate_securitygroups()

print("\n### ec2 instances ###\n")
print(test_class.servers)

print("\n### security groups ###\n")
print(test_class.securitygroups)