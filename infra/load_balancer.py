from aws_cdk import(
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
)

from constructs import Construct

class LoadBalancing(Construct):
    def __init__(self, scope: Construct, construct_id: str, stack_name, vpc, ecs_service_target, alb_sg, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        alb = elbv2.ApplicationLoadBalancer(
            self,
            f"{stack_name}-alb",
            security_group=alb_sg,
            vpc=vpc,
            internet_facing=False,
            load_balancer_name=f"{stack_name}-alb",
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT),
        )

        alb_listener_80 = alb.add_listener(
            "listener-80",
            port=80
        )

        target_group = elbv2.ApplicationTargetGroup(
            self,
            f"{stack_name}-tg",
            port=80,
            targets=[ecs_service_target],
            vpc=vpc
        )

        alb_listener_80.add_action(
            "forward-action",
            action=elbv2.ListenerAction.forward(
                target_groups=[target_group]
            )
        )