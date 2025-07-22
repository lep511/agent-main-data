
## Strands Agents Tools

### Quick Start
First, ensure that you have python 3.12 or later is installed.

We'll create a virtual environment to install the Strands Agents SDK and its dependencies in to.

```bash
uv init --python 3.12.9
```

### Setup MCP

Install MCP (Multi-Container Platform) to manage the agents:

```bash
uv add "mcp[cli]"
```

### Install Strands Agents SDK

Next we'll install the strands-agents SDK package:

```bash
uv add "strands-agents"
```

Let's install those development packages too:

```bash
# pip install strands-agents-tools strands-agents-builder
uv add "strands-agents-tools[strands-agents-builder]"
```

### Running the Example Agent

Now we can run the example agent:

```bash
uv run mcp dev main.py
```

### Configuring Credentials
Strands supports many different model providers. By default, agents use the Amazon Bedrock model provider with the Claude 3.7 model.

To use the examples in this guide, you'll need to configure your environment with AWS credentials that have permissions to invoke the Claude 3.7 model. You can set up your credentials in several ways:

1. **Environment variables**: Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and optionally AWS_SESSION_TOKEN
2. **AWS credentials file**: Configure credentials using aws configure CLI command
3. **IAM roles**: If running on AWS services like EC2, ECS, or Lambda, use IAM roles

Make sure your AWS credentials have the necessary permissions to access Amazon Bedrock and invoke the Claude 3.7 model. You'll need to enable model access in the Amazon Bedrock console following the AWS documentation.