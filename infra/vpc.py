from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from infra.config import vpc_config
from infra.config import subnets_config

class VPC(Construct):
    def __init__(self, scope: Construct, construct_id: str, stack_name, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        subnet_configs=[]
        for subnet in subnets_config:
            subnet_configs.append(
                ec2.SubnetConfiguration(
                    name=f"{stack_name}-{subnet["name"]}-subnet",
                    subnet_type=getattr(ec2.SubnetType, subnet["type"]),
                    cidr_mask=24
                )
            )

        self.vpc = ec2.Vpc(
            self, 
            f"{stack_name}-vpc",
            cidr=vpc_config["cidr"], 
            enable_dns_hostnames=True,
            enable_dns_support=True,
            nat_gateways=2,
            max_azs=2,
            subnet_configuration=subnet_configs,
            vpc_name=f"{stack_name}-vpc"
        )