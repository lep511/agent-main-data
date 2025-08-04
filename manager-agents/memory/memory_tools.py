import os
from dotenv import load_dotenv
from typing import Optional
import logging
import vertexai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

GOOGLE_AGENT_MEMORY = os.getenv("GOOGLE_AGENT_MEMORY")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")

def tool_load_memory(user_id: str) -> Optional[str]:
    """
    Load the user's memory facts from the Google Agent Memory.

    Args:
        user_id (str): The ID of the user whose memory to load

    Returns:
        Optional[str]: A string containing the user's memory facts, or None if retrieval failed
    """
    # Initialize Vertex AI client
    client = vertexai.Client(
        project=PROJECT_ID,
        location=LOCATION,
    )
    lines = []

    try:
        agent_engine = client.agent_engines.get(name=GOOGLE_AGENT_MEMORY)
        memories = client.agent_engines.retrieve_memories(
            name=agent_engine.api_resource.name,
            scope={"user_id": user_id},
        )
        if not memories:
            return None
    except Exception as e:
        logger.error(f"Failed to retrieve memories for user {user_id}: {e}")
        return None

    logger.info(f"Retrieved {len(memories)} memories for user {user_id}:")

    for memory in memories:
        if hasattr(memory, 'memory') and hasattr(memory.memory, 'fact'):
            lines.append(f"- {memory.memory.fact}")

    return "\n".join(lines) if lines else None

def tool_save_memory(user_id: str, fact: str) -> Optional[str]:
    """
    Save a fact to the user's memory.

    Args:
        user_id (str): The ID of the user to save memory for
        fact (str): The fact to save in memory

    Returns:
        Optional[str]: The name of the created memory bank, or None if creation failed
    """
    # Initialize Vertex AI client
    client = vertexai.Client(
        project=PROJECT_ID,
        location=LOCATION,
    )

    try:
        agent_engine = client.agent_engines.get(name=GOOGLE_AGENT_MEMORY)

        user_memory = client.agent_engines.create_memory(
            name=agent_engine.api_resource.name,
            fact=fact,
            scope={"user_id": user_id},
        )
        if not user_memory:
            logger.error(f"Failed to create memory for user {user_id}")
            return None
    except Exception as e:
        logger.error(f"Failed to create memory for user {user_id}: {e}")
        return None
    
    memory_name = user_memory.response.name
    logger.info(f"Created memory for user {user_id}: {memory_name}")
    return memory_name