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

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
GOOGLE_AGENT_MEMORY = os.getenv("GOOGLE_AGENT_MEMORY")
MODEL_NAME = "gemini-2.5-flash"

# Initialize Vertex AI client
client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION,
)

def create_agent_engine() -> Optional[str]:
    # creating the Agent Engine with Memory Bank
    try:
        agent_engine = client.agent_engines.create()
        logger.info(f"Created Agent Engine: {agent_engine.api_resource.name}")
    except Exception as e:
        logger.error(f"Failed to create Agent Engine: {e}")
        return None
    return agent_engine.api_resource.name

def create_memory_bank(agent_engine_id: str, user_id: str, fact: str) -> Optional[str]:
    """ Create a memory bank for a user with a specific fact.

    Args:
        agent_engine_id (str): The ID of the agent engine.
        user_id (str): The ID of the user for whom the memory bank is created.

    Returns:
        Optional[str]: The name of the created memory bank, or None if creation failed.
    """ 
    try:
        agent_engine = client.agent_engines.get(name=agent_engine_id)
        
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

def get_memory_bank(agent_engine_id: str, user_id: str) -> Optional[str]:
    agent_engine=client.agent_engines.get(name=agent_engine_id)
    lines = []

    try:
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

def semantic_memory_search(agent_engine_id: str, user_id: str, query: str) -> Optional[str]:
    """
    Use semantic search to find relevant memories based on the user's current message

    Args:
        agent_engine_id (str): The ID of the agent engine.
        user_id (str): The ID of the user.
        query (str): The user's current message to search for relevant memories.

    Returns:
        Optional[str]: A formatted string of relevant memories, or None if no results found.
    """
    agent_engine = client.agent_engines.get(name=agent_engine_id)
    
    memories = client.agent_engines.retrieve_memories(
        name=agent_engine.api_resource.name,
        scope={"user_id": user_id},
        similarity_search_params={
                "search_query": query,
                "top_k": 10  # Retrieve top 10 most relevant memories
        }
    )

    if not memories:
        return None

    lines = []

    # extract facts from memory objects
    for memory in memories:
        if hasattr(memory, 'memory') and hasattr(memory.memory, 'fact'):
            lines.append(f"- {memory.memory.fact}")

    return "\n".join(lines) if lines else None