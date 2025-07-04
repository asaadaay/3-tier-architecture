from aws_cdk import (
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codedeploy as codedeploy,
    aws_ecr as ecr,
    aws_codebuild as codebuild,
    aws_s3 as s3,
    aws_iam as iam,
    SecretValue,
    RemovalPolicy
)

from constructs import Construct
from infra.config import pipeline_config


class Pipeline(Construct):
    def __init__(
            self, 
            scope: Construct, 
            construct_id: str, 
            stack_name, 
            vpc,
            account_id, 
            blue_target_group, 
            green_target_group, 
            alb_listener_443, 
            ecs_service,
            ecr_repo,
            **kwargs
        ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        pipeline_artifacts_bucket = s3.Bucket(
            self,
            f"{stack_name}-pipeline-artifacts",
            auto_delete_objects=True,
            bucket_name=f"{stack_name}-pipeline-artifacts",
            removal_policy=RemovalPolicy.DESTROY,
        )

        codepipeline_role = iam.Role(
            self,
            f"{stack_name}-pipeline-role",
            assumed_by=iam.ServicePrincipal("codepipeline.amazonaws.com"),
            role_name=f"{stack_name}-pipeline-role"
        )

        codebuild_role = iam.Role(
            self, 
            f"{stack_name}-codebuild-role",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            role_name=f"{stack_name}-codebuild-role"
        )

        codedeploy_role = iam.Role(
            self,
            f"{stack_name}-codedeploy-role",
            assumed_by=iam.ServicePrincipal("codedeploy.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeDeployRoleForECS")],
            role_name=f"{stack_name}-codedeploy-role"
        )

        codepipeline_role.attach_inline_policy(
            iam.Policy(
                self,
                "codepipeline-policy",
                statements=[
                    iam.PolicyStatement(
                        actions=["sts:AssumeRole"],
                        resources=[codebuild_role.role_arn, codedeploy_role.role_arn]
                    ),
                    iam.PolicyStatement(
                        actions=["secretsmanager:GetSecretValue"],
                        resources=[pipeline_config["git-pat-secret-arn"]]
                    )
                ]
            )
        )

        codebuild_role.assume_role_policy.add_statements(
            iam.PolicyStatement(
                actions=["sts:AssumeRole"],
                principals=[iam.ArnPrincipal(codepipeline_role.role_arn)]
            )
        )

        codebuild_role.attach_inline_policy(
            iam.Policy(
                self,
                "codebuild-policy",
                statements=[
                    iam.PolicyStatement(
                        actions=["ecr:GetAuthorizationToken", "ecs:DescribeTaskDefinition"],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        actions=[
                            "ecr:CompleteLayerUpload",
                            "ecr:UploadLayerPart",
                            "ecr:InitiateLayerUpload",
                            "ecr:BatchCheckLayerAvailability",
                            "ecr:PutImage",
                            "ecr:BatchGetImage"
                        ],
                        resources=[ecr_repo.repository_arn]
                    ),
                ]
            )
        )

        codedeploy_role.assume_role_policy.add_statements(
            iam.PolicyStatement(
                actions=["sts:AssumeRole"],
                principals=[iam.ArnPrincipal(codepipeline_role.role_arn)]
            )
        )

        source_output = codepipeline.Artifact("source-artifacts")
        build_output = codepipeline.Artifact("build-artifacts")

        pipeline = codepipeline.Pipeline(
            self,
            f"{stack_name}-pipeline",
            artifact_bucket=pipeline_artifacts_bucket,
            pipeline_name=f"{stack_name}-pipeline",
            role=codepipeline_role
        )

        pipeline.add_stage(
            stage_name="Source",
            actions=[
                codepipeline_actions.GitHubSourceAction(
                    action_name="Source",
                    owner=pipeline_config["repo-owner"],
                    oauth_token=SecretValue.secrets_manager(pipeline_config["git-pat-secret-arn"]),
                    repo=pipeline_config["repo"],
                    output=source_output,
                    branch=pipeline_config["branch"],
                    trigger=codepipeline_actions.GitHubTrigger.WEBHOOK
                )
            ]
        )

        codebuild_project = codebuild.PipelineProject(
            self,
            f"{stack_name}-build-project",
            build_spec=codebuild.BuildSpec.from_source_filename(".aws/buildspec.yml"),
            description=f"{stack_name}-build-project",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                privileged=True,
            ),
            project_name=f"{stack_name}-build-project",
            role=codebuild_role,
            environment_variables={
                "ECR_REGISTRY_URI": codebuild.BuildEnvironmentVariable(value=pipeline_config["ecr-image-uri"]),
                "ECR_IMAGE_NAME": codebuild.BuildEnvironmentVariable(value=ecr_repo.repository_name)
            }
        )

        pipeline.add_stage(
            stage_name="Build",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="backend",
                    project=codebuild_project,
                    input=source_output,
                    outputs=[build_output],
                    role=codebuild_role,
                    environment_variables={
                        "SAMPLE_VARIABLE": codebuild.BuildEnvironmentVariable(value="SAMPLE_VALUE"),
                    }
                )
            ]
        )

        codedeploy_application = codedeploy.EcsApplication(
            self,
            f"{stack_name}-ecs-application",
            application_name=f"{stack_name}-ecs-application"
        )

        deployment_group = codedeploy.EcsDeploymentGroup(
            self,
            f"{stack_name}-dg",
            blue_green_deployment_config=codedeploy.EcsBlueGreenDeploymentConfig(
                blue_target_group=blue_target_group,
                green_target_group=green_target_group,
                listener=alb_listener_443
            ),
            service=ecs_service,
            application=codedeploy_application,
            deployment_config=codedeploy.EcsDeploymentConfig.ALL_AT_ONCE,
            deployment_group_name=f"{stack_name}-dg"
        )

        pipeline.add_stage(
            stage_name="Deploy",
            actions=[
                codepipeline_actions.CodeDeployEcsDeployAction(
                    deployment_group=deployment_group,
                    app_spec_template_file=build_output.at_path("appspec.yml"),
                    container_image_inputs=[
                        codepipeline_actions.CodeDeployEcsContainerImageInput(
                            input=build_output,
                            task_definition_placeholder="TASK_DEF_IMAGE"
                        )
                    ],
                    task_definition_template_file=build_output.at_path("task_def.json"),
                    role=codedeploy_role,
                    action_name="Deploy"
                )
            ]
        )
