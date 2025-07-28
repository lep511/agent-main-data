import asyncio
import logging
import os
import sys
import traceback

import sqlalchemy
import sqlalchemy.ext.asyncio
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import DatabaseTaskStore, InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent import root_agent as calendar_agent
from agent_executor import ADKAgentExecutor
from dotenv import load_dotenv
from google.cloud.alloydbconnector import AsyncConnector
from starlette.applications import Starlette


# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


async def create_sqlalchemy_engine(
    inst_uri: str,
    user: str,
    password: str,
    db: str,
    refresh_strategy: str = 'lazy',  # Use lazy for Cloud Run
) -> tuple[sqlalchemy.ext.asyncio.engine.AsyncEngine, AsyncConnector]:
    """Creates a connection pool for an AlloyDB instance."""
    try:
        logger.info("Creating AlloyDB connection...")
        connector = AsyncConnector(refresh_strategy=refresh_strategy)

        # create SQLAlchemy connection pool
        engine = sqlalchemy.ext.asyncio.create_async_engine(
            'postgresql+asyncpg://',
            async_creator=lambda: connector.connect(
                inst_uri,
                'asyncpg',
                user=user,
                password=password,
                db=db,
                ip_type='PUBLIC',
            ),
            execution_options={'isolation_level': 'AUTOCOMMIT'},
        )
        logger.info("AlloyDB connection created successfully")
        return engine, connector
    except Exception as e:
        logger.error(f"Failed to create AlloyDB connection: {e}")
        raise


async def create_app():
    """Create and configure the Starlette application."""
    try:
        logger.info("Creating agent card...")
        agent_card = AgentCard(
            name=calendar_agent.name,
            description=calendar_agent.description,
            version='1.0.0',
            url=os.environ.get('APP_URL', 'http://localhost:8080'),  # Provide default
            default_input_modes=['text', 'text/plain'],
            default_output_modes=['text', 'text/plain'],
            capabilities=AgentCapabilities(streaming=True),
            skills=[
                AgentSkill(
                    id='add_calendar_event',
                    name='Add Calendar Event',
                    description='Creates a new calendar event.',
                    tags=['calendar', 'event', 'create'],
                    examples=[
                        'Add a calendar event for my meeting tomorrow at 10 AM.',
                    ],
                )
            ],
        )
        logger.info("Agent card created successfully")

        # Initialize task store
        use_alloy_db_str = os.getenv('USE_ALLOY_DB', 'False')
        logger.info(f"USE_ALLOY_DB: {use_alloy_db_str}")
        
        if use_alloy_db_str.lower() == 'true':
            logger.info("Setting up AlloyDB task store...")
            # Check required environment variables
            required_vars = ['DB_INSTANCE', 'DB_NAME', 'DB_USER', 'DB_PASS']
            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            if missing_vars:
                raise ValueError(f"Missing required environment variables: {missing_vars}")
            
            DB_INSTANCE = os.environ['DB_INSTANCE']
            DB_NAME = os.environ['DB_NAME']
            DB_USER = os.environ['DB_USER']
            DB_PASS = os.environ['DB_PASS']

            engine, connector = await create_sqlalchemy_engine(
                DB_INSTANCE,
                DB_USER,
                DB_PASS,
                DB_NAME,
                refresh_strategy='lazy'
            )
            task_store = DatabaseTaskStore(engine)
            logger.info("AlloyDB task store created successfully")
        else:
            logger.info("Using in-memory task store")
            task_store = InMemoryTaskStore()

        logger.info("Creating request handler...")
        request_handler = DefaultRequestHandler(
            agent_executor=ADKAgentExecutor(
                agent=calendar_agent,
            ),
            task_store=task_store,
        )

        logger.info("Creating A2A application...")
        a2a_app = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )
        from starlette.routing import Route
        from starlette.responses import JSONResponse
        
        # Add health check endpoint
        async def health_check(request):
            return JSONResponse({"status": "healthy", "service": "sample-a2a-agent"})
        
        routes = a2a_app.routes()
        # Add health check route
        routes.append(Route("/health", health_check, methods=["GET"]))
        
        app = Starlette(
            routes=routes,
            middleware=[],
        )
        logger.info("Application created successfully")
        return app

    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        logger.error(traceback.format_exc())
        raise


async def main():
    """Main application entry point."""
    try:
        # Get configuration from environment
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', 8080))
        
        logger.info(f"Starting application on {host}:{port}")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Environment variables: PORT={os.environ.get('PORT')}, HOST={os.environ.get('HOST')}")
        
        # Create the application
        app = await create_app()
        
        # Configure uvicorn
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level='info',
            access_log=True,
            # Add timeout configurations
            timeout_keep_alive=65,
            timeout_graceful_shutdown=30,
        )
        
        logger.info("Starting uvicorn server...")
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)