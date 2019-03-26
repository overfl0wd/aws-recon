from aws_recon import AwsSession

""" Initialize the AWS Session class.
Pass a profile name from your configs (~/.aws/),
as well as a region to use.
"""
prod_east1 = AwsSession("production", "us-east-1")


""" Run the EC2 instance enumeration function,
and print the returned information.
"""
prod_east1.enumerate_servers()
print(prod_east1.servers)