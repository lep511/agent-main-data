
## Amazon Bedrock AgentCore sample

#### **[Tutorial - AWS Docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/getting-started-custom.html)**

In just a few years, foundation models (FMs) have evolved from being used directly to create content in response to a user’s prompt, to now powering AI agents, a new class of software applications that use FMs to reason, plan, act, learn, and adapt in pursuit of user-defined goals with limited human oversight. This new wave of agentic AI is enabled by the emergence of standardized protocols such as Model Context Protocol (MCP) and Agent2Agent (A2A) that simplify how agents connect with other tools and systems

**Amazon Bedrock AgentCore** is a comprehensive set of enterprise-grade services that help developers quickly and securely deploy and operate AI agents at scale using any framework and model, hosted on Amazon Bedrock or elsewhere.

### Step 1 – Deploying to the cloud with AgentCore Runtime

AgentCore Runtime is a new service to securely deploy, run, and scale AI agents, providing isolation so that each user session runs in its own protected environment to help prevent data leakage—a critical requirement for applications handling sensitive data.

For this example, we'll use the uv package manager, though you can use any Python utility or package manager. To install uv on macOS:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Create and navigate to your project directory:
```bash
mkdir my-custom-agent && cd my-custom-agent
```

Initialize the project with Python 3.11:
```bash
uv init --python 3.11
```

Add the required dependencies (uv automatically creates a .venv):
```bash
uv add fastapi uvicorn[standard] pydantic httpx strands-agents
```

After implementing these changes, you can test your service locally:
```bash
uv run uvicorn agent:app --host 0.0.0.0 --port 8080
```

Test the /ping endpoint (in another terminal):
```bash
curl http://localhost:8080/ping
```

Test the /invocations endpoint:
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "input": {"prompt": "What is artificial intelligence?"}
  }'
```


### What happens behind the scenes
The agent.py file contains the core logic for the agent, which includes:

* Creates a FastAPI application with the required endpoints
* Initializes a Strands agent for processing user messages
* Implements the /invocations POST endpoint for agent interactions
* Implements the /ping GET endpoint for health checks
* Configures the server to run on host 0.0.0.0 and port 8080

### Build and deploy ARM64 image

To build and deploy the ARM64 image, you can use the following command:

```bash
docker buildx create --use
```

Build for ARM64 and test locally:
```bash
docker buildx build --platform linux/arm64 -t my-agent:arm64 --load .
```

Test locally with credentials (Strands agents need AWS credentials):
```bash
docker run --platform linux/arm64 -p 8080:8080 \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  -e AWS_SESSION_TOKEN="$AWS_SESSION_TOKEN" \
  -e AWS_REGION="$AWS_REGION" \
  my-agent:arm64
```


