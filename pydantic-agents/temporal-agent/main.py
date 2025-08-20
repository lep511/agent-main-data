import os
import uuid
import logfire

from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker

from pydantic_ai import Agent
from pydantic_ai.durable_exec.temporal import AgentPlugin, PydanticAIPlugin, TemporalAgent, LogfirePlugin

logfire_token = os.getenv("LOGFIRE_TOKEN")

if not logfire_token:
    # 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
    logfire.configure(send_to_logfire='if-token-present')
else:
    logfire.configure(
        token=logfire_token,
        service_name='temporal-agent',
        environment='test'
    )
                  
agent = Agent(
    'gpt-5',
    instructions="You're an expert in geography.",
    name='geography',  
)

temporal_agent = TemporalAgent(agent)  


@workflow.defn
class GeographyWorkflow:  
    @workflow.run
    async def run(self, prompt: str) -> str:
        result = await temporal_agent.run(prompt)  
        return result.output


async def main():
    client = await Client.connect(  
        'localhost:7233',  
        plugins=[PydanticAIPlugin(), LogfirePlugin()], 
    )

    async with Worker(  
        client,
        task_queue='geography',
        workflows=[GeographyWorkflow],
        plugins=[AgentPlugin(temporal_agent)],  
    ):
        output = await client.execute_workflow(  
            GeographyWorkflow.run,
            args=['What is the capital of Mexico?'],
            id=f'geography-{uuid.uuid4()}',
            task_queue='geography',
        )
        print(output)
        #> Mexico City (Ciudad de México, CDMX)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
