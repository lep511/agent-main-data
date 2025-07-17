import boto3
import json
import os

region = os.environ.get('AWS_REGION', 'us-east-1')
agent_name = os.environ.get('BEDROCK_AGENT_NAME')

agent_core_client = boto3.client('bedrock-agentcore', region_name=region)
payload = json.dumps({
    "input": {"prompt": "Explain machine learning in simple terms"}
})

response = agent_core_client.invoke_agent_runtime(
    agentRuntimeArn=f'arn:aws:bedrock-agentcore:{region}:089715336747:runtime/{agent_name}',
    runtimeSessionId='dfmeoagmreaklgmrkleafremoigrmtesogmtrskhmtkrlshmt',  # Must be 33+ chars
    payload=payload,
    qualifier="DEFAULT"
)

response_body = response['response'].read()
response_data = json.loads(response_body)
print("Agent Response:", response_data)
