import os
import logging

import click
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from social.agent import root_agent as social_agent
from social.agent_executor import ADKAgentExecutor
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host=os.environ.get("A2A_HOST", "localhost")
port=int(os.environ.get("A2A_PORT",10001))

class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


@click.command()
@click.option("--host", default=host)
@click.option("--port", default=port)
def main(host, port):

    PUBLIC_URL=os.environ.get("PUBLIC_URL", f'http://{host}:{port}')

    # Agent card (metadata)
    agent_card = AgentCard(
        name='Social Profile Agent',
        description=("Using a provided list of names, this agent synthesizes Instavibe social profile information by analyzing posts, friends, and events. "
            "It delivers a comprehensive single-paragraph summary for individuals, and for groups, identifies commonalities in their social activities "
            "and connections based on profile data."),
        url=PUBLIC_URL,
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="social_profile_analysisg",
                name="Analyze Instavibe social profile",
                description=("Using a provided list of names, this agent synthesizes Instavibe social profile information by analyzing posts, friends, and events. "
                    "It delivers a comprehensive single-paragraph summary for individuals, and for groups, identifies commonalities in their social activities "
                    "and connections based on profile data."),
                tags=["instavibe"],
                examples=["Can you tell me about Bob and Alice?"],
            )
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=ADKAgentExecutor(
            agent=social_agent,
        ),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()