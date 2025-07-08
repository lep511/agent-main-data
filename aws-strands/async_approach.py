import asyncio
from strands import Agent
from strands.models import BedrockModel
from strands_tools import calculator
import os

# Read an environment variable (returns None if not found)
api_key = os.getenv('AWS_BEARER_TOKEN_BEDROCK')

MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"
REGION = "us-east-1"

# Create a configured Bedrock model
bedrock_model = BedrockModel(
    model_id=MODEL_ID,
    region_name=REGION,
)

# Initialize our agent without a callback handler
agent = Agent(
    model=bedrock_model,
    tools=[calculator],
    callback_handler=None  # Disable default callback handler
)

# Async function that iterates over streamed agent events
async def process_streaming_response():
    query = "What is 25 * 48 and explain the calculation"

    # Get an async iterator for the agent's response stream
    agent_stream = agent.stream_async(query)

    # Process events as they arrive
    async for event in agent_stream:
        if "data" in event:
            # Print text chunks as they're generated
            print(event["data"], end="", flush=True)
        elif "current_tool_use" in event and event["current_tool_use"].get("name"):
            # Print tool usage information
            print(f"\n[Tool use delta for: {event['current_tool_use']['name']}]")

# Run the agent with the async event processing
asyncio.run(process_streaming_response())