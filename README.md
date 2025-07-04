
# 3 Tier Architecture
This CDK stack deploys a complete 3 tiered architecture following best practices, it includes the following:
- VPC
- ECS Fargate as compute.
- Load balancing for traffic to the containers on Fargate.
- RDS PostgreSQL instance as the database.
- CI/CD pipeline with blue/green deployment for ECS.

## Deployment commands

Create a ".env" file (see sample.env) and populate the keys with values relevant to your AWS environment.

Activate virtual environment:
```
$ source .venv/bin/activate
```

Install required dependencies:
```
$ pip install -r requirements.txt
```

CDK deployment related commands:
```
# Emit the synthesized CloudFormation template
$ cdk synth --context stack=STACK_NAME

# Deploy the stack
$ cdk deploy --context stack=STACK_NAME

# Compare deployed stack with current state
$ cdk diff --context stack=STACK_NAME`
```