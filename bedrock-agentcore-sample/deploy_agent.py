import boto3
import os

role_arn = os.environ.get('BEDROCK_AGENT_ROLE_ARN')
if role_arn:
    print(f"Role ARN: {role_arn}")
else:
    print("ERROR: BEDROCK_AGENT_ROLE_ARN environment variable not set")
    exit(1)

region = os.environ.get('AWS_REGION', 'us-east-1')

account_id = role_arn.split(':')[4]
client = boto3.client('bedrock-agentcore-control', region_name=region)

response = client.create_agent_runtime(
    agentRuntimeName='strands_agent',
    agentRuntimeArtifact={
        'containerConfiguration': {
            'containerUri': account_id + '.dkr.ecr.' + region + '.amazonaws.com/my-strands-agent:latest'
        }
    },
    networkConfiguration={"networkMode": "PUBLIC"},
    roleArn=role_arn
)

print(f"Agent Runtime created successfully!")
print(f"Agent Runtime ARN: {response['agentRuntimeArn']}")
print(f"Status: {response['status']}")
