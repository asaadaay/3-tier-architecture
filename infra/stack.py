from aws_cdk import (
    Stack,
)
from constructs import Construct

from infra.vpc import VPC
from infra.database import Database
from infra.ecs import ECS
from infra.load_balancer import LoadBalancing
from infra.pipeline import Pipeline

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

        load_balancing_construct = LoadBalancing(
            self,
            "load-balancer-construct",
            stack_name,
            vpc=vpc_construct.vpc,
            ecs_service_target=ecs_construct.ecs_service_target,
            alb_sg=ecs_construct.alb_sg
        )

        Pipeline(
            self,
            "pipeline-construct",
            stack_name,
            vpc=vpc_construct.vpc,
            account_id=self.account,
            blue_target_group=load_balancing_construct.blue_target_group,
            green_target_group=load_balancing_construct.green_target_group,
            alb_listener_80=load_balancing_construct.alb_listener_80,
            ecs_service=ecs_construct.ecs_service
        )


