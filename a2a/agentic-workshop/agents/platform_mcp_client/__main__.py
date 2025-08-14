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
from platform_mcp_client.agent import root_agent as posting_agent
from platform_mcp_client.agent_executor import ADKAgentExecutor
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host=os.environ.get("A2A_HOST", "localhost")
port=int(os.environ.get("A2A_PORT",10002))

class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


@click.command()
@click.option("--host", default=host)
@click.option("--port", default=port)
def main(host, port):

    PUBLIC_URL=os.environ.get("PUBLIC_URL", f'http://{host}:{port}')

    # Agent card (metadata)
    agent_card = AgentCard(
        name='Instavibe Posting Agent',
        description=("This 'Instavibe' agent helps you create posts (identifying author, text, and sentiment – inferred if unspecified) and register "
            "for events (gathering name, date, attendee). It efficiently collects required information and utilizes dedicated tools "
            "to perform these actions on your behalf, ensuring a smooth sharing experience."),
        url=PUBLIC_URL,
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="instavibe_posting",
                name="Post social post and events on instavibe",
                description=("This 'Instavibe' agent helps you create posts (identifying author, text, and sentiment – inferred if unspecified) and register "
                    "for events (gathering name, date, attendee). It efficiently collects required information and utilizes dedicated tools "
                    "to perform these actions on your behalf, ensuring a smooth sharing experience."),
                tags=["instavibe"],
                examples=["Create a post for me, the post is about my cute cat and make it positive, and I'm Alice"],
            )
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=ADKAgentExecutor(
            agent=posting_agent,
        ),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()