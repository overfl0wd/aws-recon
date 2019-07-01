# AWS recon

this is a utility to extract useful information about resources (servers, networking, etc) in an AWS account. 

each function iterates through specific resources for the given account and region

## what's the point?

- this is used internally to programmatically generate a detailed list of assets. the output is piped into Splunk as a lookup to add value to reports and alerts (adding names to resource IDs that show up in Cloudtrail, etc)

- i think this could also be useful in mapping out the attack surface of a pentest, given a set of AWS API keys w/ read permissions are available. 

## requirements

use the package manager [pip](https://pip.pypa.io/en/stable/) to install boto3

```bash
pip install boto3
```

## usage (example_main.py)
#### available methods:
- enumerate_servers()
- enumerate_securitygroups()
- enumerate_networkinterfaces()
- enumerate_classiclbs()
- enumerate_applicationlbs()
- enumerate_elasticips()
```python
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

```

## what's next
add enumeration for more services/resources, flesh out the example usage info
