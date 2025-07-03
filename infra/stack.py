from aws_cdk import (
    Stack,
)
from constructs import Construct

from infra.vpc import VPC
from infra.database import Database
from infra.ecs import ECS
from infra.load_balancer import LoadBalancing

class ThreeTierStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, stack_name, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc_construct = VPC(
            self,
            "vpc-construct",
            stack_name,
        )

        ecs_construct = ECS(
            self,
            "ecs-construct",
            stack_name,
            vpc=vpc_construct.vpc,
        )

        Database(
            self,
            "database-construct",
            stack_name,
            vpc_construct.vpc,
            rds_sg=ecs_construct.rds_sg

        )

        LoadBalancing(
            self,
            "load-balancer-construct",
            stack_name,
            vpc=vpc_construct.vpc,
            ecs_service_target=ecs_construct.ecs_service_target,
            alb_sg=ecs_construct.alb_sg
        
        )


