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

def create_memory_bank(agent_engine_id: str, user_id: str):
    agent_engine = client.agent_engines.get(name=agent_engine_id)
    
    user_memory = client.agent_engines.create_memory(
        name=agent_engine.api_resource.name,
        fact=f"The user's name is {user_id} and they have a passion for learning new things.",
        scope={"user_id": user_id},
    )
    memory = user_memory.response
    logger.info("Created initial memory:")
    logger.info(f"  Fact: {memory.fact}")
    logger.info(f"  User ID: {memory.scope.get('user_id')}")
    logger.info(f"  Created at: {memory.create_time}")


def get_memory_bank(agent_engine_id: str, user_id: str) -> Optional[str]:
    agent_engine=client.agent_engines.get(name=agent_engine_id)
    lines = []

    memories = client.agent_engines.retrieve_memories(
        name=agent_engine.api_resource.name,
        scope={"user_id": user_id},
    )

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

if __name__ == "__main__":
    try:
        # agent_engine_id = create_agent_engine()
        # print(f"\nAgent Engine ID: {agent_engine_id}")

        user_id = "user_3002b2a1-9e05-481c-a6a9-c12326cbc718"
        agent_engine_id = "projects/500889128816/locations/us-central1/reasoningEngines/7362884013448495104"

        # create_memory_bank(agent_engine_id, user_id)
        
        memory = get_memory_bank(agent_engine_id, user_id)
        print(f"\nMemory Bank for {user_id}:\n{memory if memory else 'No memories found.'}")
        
        # query = "What is my city of born?"
        # relevant_memories = semantic_memory_search(agent_engine_id, user_id, query)
        # print(f"\nRelevant Memories for query '{query}':\n{relevant_memories if relevant_memories else 'No relevant memories found.'}")
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
