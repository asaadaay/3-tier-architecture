from dotenv import load_dotenv
import os

load_dotenv()

git_pat_secret_arn = os.getenv("GIT_PAT_SECRET_ARN")
git_repo_owner = os.getenv("GIT_REPO_OWNER")
git_repo = os.getenv("GIT_REPO")
git_branch = os.getenv("GIT_BRANCH")
ecr_image_uri = os.getenv("ECR_IMAGE_URI")
certificate_arn = os.getenv("CERTIFICATE_ARN")
ecr_repo_uri = os.getenv("ECR_REPO_URI")

vpc_config = {
    "cidr": "10.0.0.0/20"
}

subnets_config = [
    {"name": "public", "type": "PUBLIC"},
    {"name": "app-private", "type": "PRIVATE_WITH_NAT"},
    {"name": "data-private", "type": "PRIVATE_ISOLATED"},
]

rds_config = {
    "allocated-storage": 100,
    "instance-type": "t4g.micro",
    "delete-automated-backups": True
}

alb_config = {
    "certificate-arn": certificate_arn
}

ecs_task_def_config = {
    "cpu": 256,
    "memory_limit_mib": 512,
    "container-port": 3000,
    "ecr-repo-uri": ecr_repo_uri
}

pipeline_config = {
    "repo-owner": git_repo_owner,
    "git-pat-secret-arn": git_pat_secret_arn,
    "repo": git_repo,
    "branch": git_branch,
    "ecr-image-uri": ecr_image_uri
}


