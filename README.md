
# 3 Tier Architecture
Standard 3 Tier Architecture.

Activate virtual environment.
```
$ source .venv/bin/activate
```

Install required dependencies
```
$ pip install -r requirements.txt
```

## Useful commands
 * `cdk synth --context stack=STACK_NAME`       emits the synthesized CloudFormation template
 * `cdk deploy --context stack=STACK_NAME`      deploy this stack to your default AWS account/region
 * `cdk diff --context stack=STACK_NAME`        compare deployed stack with current state