import os
import uuid
import logfire
from typing import Optional

from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker

from pydantic_ai import Agent
from pydantic_ai.durable_exec.temporal import AgentPlugin, PydanticAIPlugin, TemporalAgent, LogfirePlugin

# Environment configuration
LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # Default to development
SERVICE_NAME = os.getenv("SERVICE_NAME", "temporal-agent")
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")

def configure_logfire() -> None:
    """Configure logfire with environment variables."""
    if not LOGFIRE_TOKEN:
        logfire.info("LOGFIRE_TOKEN not set, using 'if-token-present' mode", environment=ENVIRONMENT)
        logfire.configure(send_to_logfire='if-token-present')
    else:
        logfire.configure(
            token=LOGFIRE_TOKEN,
            service_name=SERVICE_NAME,
            environment=ENVIRONMENT
        )

# Configure logfire at module level
configure_logfire()

# Create agent with logfire logging
agent = Agent(
    'gpt-5',
    instructions="You're an expert in geography.",
    name='geography',  
)

temporal_agent = TemporalAgent(agent)  

logfire.info("Agent initialized", 
            agent_name=agent.name, 
            environment=ENVIRONMENT,
            service_name=SERVICE_NAME)


@workflow.defn
class GeographyWorkflow:  
    @workflow.run
    async def run(self, prompt: str) -> str:
        # Log workflow execution start
        logfire.info("Starting workflow execution", 
                    prompt=prompt, 
                    environment=ENVIRONMENT,
                    workflow_id=workflow.info().workflow_id)
        
        try:
            result = await temporal_agent.run(prompt)
            
            # Log successful completion
            logfire.info("Workflow completed successfully", 
                        prompt=prompt,
                        result_length=len(result.output),
                        environment=ENVIRONMENT,
                        workflow_id=workflow.info().workflow_id)
            
            return result.output
            
        except Exception as e:
            # Log workflow errors
            configure_logfire()
            logfire.error("Workflow execution failed", 
                         prompt=prompt,
                         error=str(e),
                         error_type=type(e).__name__,
                         environment=ENVIRONMENT,
                         workflow_id=workflow.info().workflow_id)
            raise


async def connect_temporal_client() -> Client:
    """Connect to Temporal server with proper error handling and logging."""
    
    try:
        client = await Client.connect(  
            TEMPORAL_HOST,  
            plugins=[PydanticAIPlugin(), LogfirePlugin()], 
        )
                
        return client
        
    except RuntimeError as e:
        if 'Connection refused' in str(e):
            error_msg = f"Temporal server not running at {TEMPORAL_HOST}. Start it with `temporal server start-dev`"
            configure_logfire()
            logfire.error("Temporal connection refused", 
                         temporal_host=TEMPORAL_HOST,
                         error_message=error_msg,
                         environment=ENVIRONMENT)
            raise RuntimeError(error_msg)
        else:
            configure_logfire()
            logfire.error("Temporal connection error", 
                         temporal_host=TEMPORAL_HOST,
                         error=str(e),
                         error_type=type(e).__name__,
                         environment=ENVIRONMENT)
            raise


async def execute_geography_workflow(client: Client, prompt: str) -> str:
    """Execute the geography workflow with logging."""
    workflow_id = f'geography-{uuid.uuid4()}'
    
    logfire.info("Executing geography workflow", 
                prompt=prompt,
                workflow_id=workflow_id,
                environment=ENVIRONMENT)
    
    try:
        output = await client.execute_workflow(  
            GeographyWorkflow.run,
            args=[prompt],
            id=workflow_id,
            task_queue='geography',
        )
        
        logfire.info("Workflow execution completed", 
                    prompt=prompt,
                    workflow_id=workflow_id,
                    output=output,
                    environment=ENVIRONMENT)
        
        return output
        
    except Exception as e:
        configure_logfire()
        logfire.error("Failed to execute workflow", 
                     prompt=prompt,
                     workflow_id=workflow_id,
                     error=str(e),
                     error_type=type(e).__name__,
                     environment=ENVIRONMENT)
        raise


async def main():
    """Main application entry point."""
    
    try:
        # Connect to Temporal
        client = await connect_temporal_client()
        
        # Start worker and execute workflow
        async with Worker(  
            client,
            task_queue='geography',
            workflows=[GeographyWorkflow],
            plugins=[AgentPlugin(temporal_agent)],  
        ) as worker:
            
            # Execute the workflow
            prompt = 'What is the capital of Mexico?'
            output = await execute_geography_workflow(client, prompt)
            
            print(f"Result: {output}")
            
            logfire.info("Application completed successfully", 
                        final_output=output,
                        environment=ENVIRONMENT)
            
    except Exception as e:
        configure_logfire()
        logfire.error("Application failed", 
                     error=str(e),
                     error_type=type(e).__name__,
                     environment=ENVIRONMENT)
        raise
    

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())