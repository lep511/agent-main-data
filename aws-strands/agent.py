from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import calculator, current_time, python_repl
from botocore.config import Config as BotocoreConfig
import boto3
import logging

MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"
REGION = "us-east-1"

# Define a custom tool as a Python function using the @tool decorator
@tool
def letter_counter(word: str, letter: str) -> int:
    """
    Count occurrences of a specific letter in a word.

    Args:
        word (str): The input word to search in
        letter (str): The specific letter to count

    Returns:
        int: The number of occurrences of the letter in the word
    """
    if not isinstance(word, str) or not isinstance(letter, str):
        return 0

    if len(letter) != 1:
        raise ValueError("The 'letter' parameter must be a single character")

    return word.lower().count(letter.lower())

def handle_agent_error(e):
    # Placeholder for error handling logic
    logger.error(f"Handling agent error: {str(e)}")
    # You can add more sophisticated error handling here

logger = logging.getLogger("my_agent")

# Create a boto client config with custom settings
boto_config = BotocoreConfig(
    retries={"max_attempts": 3, "mode": "standard"},
    connect_timeout=5,
    read_timeout=60
)

# Create a configured Bedrock model
bedrock_model = BedrockModel(
    model_id=MODEL_ID,
    region_name=REGION,
    temperature=0.3,
    top_p=0.8,
    stop_sequences=["###", "END"],
    boto_client_config=boto_config,
)

# Create an agent with a specific model and with tools from the strands-tools 
# example tools package as well as our custom letter_counter tool
agent = Agent(
    model=bedrock_model,
    tools=[calculator, current_time, python_repl, letter_counter]
)

# Ask the agent a question that uses the available tools
message = """
I have 4 requests:

1. What is the time right now?
2. Calculate 3111696 / 74088
3. Tell me how many letter R's are in the word "strawberry" 🍓
4. Output a script that does what we just spoke about!
   Use your python tools to confirm that the script works before outputting it
"""

try:
    response = agent(message)
except Exception as e:
    # Implement appropriate fallback
    handle_agent_error(e)
