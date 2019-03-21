from aws_recon import AwsSession


test_class = AwsSession("sys", "us-east-1")

""" Initialize the AWS Session class above.
Pass a profile name from your configs (~/.aws/),
as well as a region to use.
"""

test_class.enumerate_servers()

print(test_class.servers)