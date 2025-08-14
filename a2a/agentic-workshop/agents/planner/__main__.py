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
from planner.agent import root_agent as planner_agent
from planner.agent_executor import ADKAgentExecutor
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host=os.environ.get("A2A_HOST", "localhost")
port=int(os.environ.get("A2A_PORT",10003))

class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


@click.command()
@click.option("--host", default=host)
@click.option("--port", default=port)
def main(host, port):

    PUBLIC_URL=os.environ.get("PUBLIC_URL", f'http://{host}:{port}')

    # Agent card (metadata)
    agent_card = AgentCard(
        name='Event Planner Agent',
        description=planner_agent.description,
        url=PUBLIC_URL,
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="event_planner",
                name="Event planner",
                description=("This agent generates multiple fun plan suggestions tailored to your specified location, dates, and interests,"
                "all designed for a moderate budget. It delivers detailed itineraries,"
                "including precise venue information (name, latitude, longitude, and description), in a structured JSON format."),
                tags=["instavibe"],
                examples=["What about Bostona MA this weekend?"],
            )
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=ADKAgentExecutor(
            agent=planner_agent,
        ),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()