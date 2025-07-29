## Amazon Bedrock AgentCore Observability

This code demonstrates how to use setup observability for a Strands Agent SDK agent hosted outside of Amazon Bedrock AgentCore Runtime. Once you have completed the setup, you will be able to view the internal decision making process of Strands agent in GenAI Observability dashboard in Amazon CloudWatch.

Install the required dependencies:

```bash
uv add "strands-agents[otel]" strands-agents-tools boto3 botocore duckduckgo-search "aws-opentelemetry-distro==0.10.0" python-dotenv
```

### Environment Configuration
To enable observability for your Strands agent and send telemetry data to Amazon CloudWatch, you'll need to configure the following environment variables. We use a .env file to manage these settings securely, keeping sensitive AWS credentials separate from your code while making it easy to switch between different environments.

Create a .env file with your AWS credentials and configuration. Use Strands/.env.example as a template.

If you are using an existing log group and corresponding log stream, please add that to your environment variable.

Else, you would need to create a log group and log stream in Cloudwatch before you set that as an environment variable, example names are provided.
