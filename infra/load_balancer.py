from aws_cdk import(
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    Duration
)

from infra.config import alb_config

from constructs import Construct

class LoadBalancing(Construct):
    def __init__(self, scope: Construct, construct_id: str, stack_name, vpc, ecs_service_target, alb_sg, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        alb = elbv2.ApplicationLoadBalancer(
            self,
            f"{stack_name}-alb",
            security_group=alb_sg,
            vpc=vpc,
            internet_facing=True,
            load_balancer_name=f"{stack_name}-alb",
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT),
        )

        alb_listener_80 = alb.add_listener(
            "listener-80",
            port=80
        )

        alb_listener_80.add_action(
            "redirect-action",
            action=elbv2.ListenerAction.redirect(
                port="443",
                protocol="HTTPS",
                path="/#{path}",
                query="#{query}"
            )
        )

        self.alb_listener_443 = alb.add_listener(
            "listener-443",
            certificates=[elbv2.ListenerCertificate.from_arn(alb_config["certificate-arn"])],
            port=443
        )

        self.blue_target_group = elbv2.ApplicationTargetGroup(
            self,
            f"{stack_name}-tg-1",
            port=3000,
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[ecs_service_target],
            vpc=vpc,
            health_check=elbv2.HealthCheck(
                enabled=True,
                path="/health",
            ),
            deregistration_delay=Duration.seconds(15),
            target_type=elbv2.TargetType.IP,
            target_group_name=f"{stack_name}-tg-1"
        )

        self.green_target_group = elbv2.ApplicationTargetGroup(
            self,
            f"{stack_name}-tg-2",
            port=3000,
            protocol=elbv2.ApplicationProtocol.HTTP,
            vpc=vpc,
            health_check=elbv2.HealthCheck(
                enabled=True,
                path="/health",
            ),
            deregistration_delay=Duration.seconds(15),
            target_type=elbv2.TargetType.IP,
            target_group_name=f"{stack_name}-tg-2"
        )

        self.alb_listener_443.add_action(
            "forward-action",
            action=elbv2.ListenerAction.forward(
                target_groups=[self.blue_target_group]
            )
        )