from aws_cdk import(
    aws_ecs as ecs,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    RemovalPolicy
)
from constructs import Construct

from infra.config import ecs_task_def_config


class ECS(Construct):
    def __init__(self, scope: Construct, construct_id: str, stack_name, vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.ecr_repo = ecr.Repository(
            self,
            f"{stack_name}-repository",
            empty_on_delete=True,
            removal_policy=RemovalPolicy.DESTROY,
            repository_name=f"{stack_name}-repository"
        )

        ecs_cluster = ecs.Cluster(
            self,
            f"{stack_name}-cluster",
            cluster_name=f"{stack_name}-cluster",
            enable_fargate_capacity_providers=True,
            vpc=vpc
        )

        ecs_execution_role = iam.Role(
            self,
            f"{stack_name}-ecs-exec-role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ],
            role_name=f"{stack_name}-ecs-exec-role"
        )

        ecs_task_role = iam.Role(
            self,
            f"{stack_name}-ecs-task-role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            role_name=f"{stack_name}-ecs-task-role"
        )

        ecs_task_definition = ecs.FargateTaskDefinition(
            self,
            f"{stack_name}-td",
            cpu=ecs_task_def_config["cpu"],
            memory_limit_mib=ecs_task_def_config["memory_limit_mib"],
            execution_role=ecs_execution_role,
            family=f"{stack_name}-td",
            task_role=ecs_task_role
        )

        ecs_container = ecs_task_definition.add_container(
            f"{stack_name}-container",
            image=ecs.ContainerImage.from_registry(ecs_task_def_config["ecr-repo-uri"]),
            container_name=f"{stack_name}-container",
            port_mappings=[ecs.PortMapping(container_port=ecs_task_def_config["container-port"])]
        )

        self.alb_sg = ec2.SecurityGroup(
            self,
            f"{stack_name}-alb-sg",
            vpc=vpc,
            security_group_name=f"{stack_name}-alb-sg"
        )

        self.alb_sg.add_ingress_rule(
            ec2.Peer.ipv4("0.0.0.0/0"),
            ec2.Port.tcp(80)
        )

        self.alb_sg.add_ingress_rule(
            ec2.Peer.ipv4("0.0.0.0/0"),
            ec2.Port.tcp(443)
        )

        ecs_service_sg = ec2.SecurityGroup(
            self,
            f"{stack_name}-ecs-service-sg",
            vpc=vpc,
            description=f"{stack_name}-ecs-service-sg",
            security_group_name=f"{stack_name}-ecs-service-sg"
        )

        ecs_service_sg.add_ingress_rule(
            ec2.Peer.security_group_id(self.alb_sg.security_group_id),
            ec2.Port.tcp(3000)
        )

        self.rds_sg = ec2.SecurityGroup(
            self,
            f"{stack_name}-rds-sg",
            vpc=vpc,
            description=f"{stack_name}-rds-sg",
            security_group_name=f"{stack_name}-rds-sg"
        )

        self.rds_sg.add_ingress_rule(
            ec2.Peer.security_group_id(ecs_service_sg.security_group_id),
            ec2.Port.tcp(5432)
        )

        self.ecs_service = ecs.FargateService(
            self,
            f"{stack_name}-service",
            task_definition=ecs_task_definition,
            cluster=ecs_cluster,
            service_name=f"{stack_name}-service",
            desired_count=1,
            security_groups=[ecs_service_sg],
            deployment_controller=ecs.DeploymentController(
                type=ecs.DeploymentControllerType.CODE_DEPLOY
            )
        )

        self.ecs_service_target = self.ecs_service.load_balancer_target(
            container_name=ecs_container.container_name,
            container_port=ecs_container.container_port
        )
