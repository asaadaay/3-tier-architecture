from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    Duration,
    aws_logs as logs
)
from constructs import Construct

from infra.config import rds_config


class Database(Construct):
    def __init__(self, scope: Construct, construct_id: str, stack_name, vpc, rds_sg, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        rds.DatabaseInstance(
            self,
            f"{stack_name}-rds-instance",
            credentials=rds.Credentials.from_generated_secret(
                username="admin", 
                exclude_characters=r"@!$%^&*()_+=[]{}:;\"'\\|,.<>/?`~#",
                secret_name=f"{stack_name}-db-secret"
            ),
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_17_4
            ),
            allocated_storage=rds_config["allocated-storage"],
            database_name="main-db",
            instance_type=ec2.InstanceType(rds_config["instance-type"]),
            vpc=vpc,
            backup_retention=Duration.days(7),
            cloudwatch_logs_exports=["postgresql","upgrade"],
            cloudwatch_logs_retention=logs.RetentionDays.ONE_YEAR,
            delete_automated_backups=rds_config["delete-automated-backups"],
            instance_identifier=f"{stack_name}-rds-instance",
            security_groups=[rds_sg],
            subnet_group=rds.SubnetGroup(
                self,
                f"{stack_name}-rds-subnet-group",
                description=f"RDS subnet group for {stack_name}-rds-instance",
                vpc=vpc,
                subnet_group_name=f"{stack_name}-rds-subnet-group",
                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
            )
        )





