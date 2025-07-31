from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import Counter
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import KnownModelName
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.settings import ModelSettings
from dotenv import load_dotenv
import logging
import os
import re

# Optional import for YAML frontmatter parsing
try:
    import yaml
except ImportError:
    yaml = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentCategory(BaseModel):
    name: str = Field(..., description="The human-friendly category title")
    specializations: List[str] = Field(
        ..., description="List of agent specialization slugs"
    )


class AgentsOverview(BaseModel):
    categories: List[AgentCategory]

class Orchestrator:
    """Orchestrator for managing multiple agents"""
    
    def __init__(
            self,
            agents: Dict[str, Agent],
            orchestrator_directory: str = "./orchestrator"
    ):
        self.agents = agents
        self.orchestrator_directory = Path(orchestrator_directory)
        if not self.orchestrator_directory.exists():
            raise FileNotFoundError(
                f"Orchestrator directory not found: {orchestrator_directory}"
            )
        
        # Load orchestration workflows from directory
        self.workflows = self._load_workflows()
        
    def _load_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Load orchestration workflows from markdown files"""
        workflows = {}
        workflow_files = list(self.orchestrator_directory.rglob("*.md"))
        
        for file_path in workflow_files:
            try:
                workflow = self._parse_workflow_file(file_path)
                workflows[workflow['name']] = workflow
                logger.info(f"✓ Loaded workflow: {workflow['name']}")
            except Exception as e:
                logger.error(f"✗ Failed to load workflow {file_path}: {e}")
        
        return workflows
    
    def _parse_workflow_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a workflow markdown file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract frontmatter
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        workflow_config = {
            'name': file_path.stem,
            'system_prompt': '',
            'description': '',
            'model': '',
            'provider': '',
            'temperature': 0.7,
            'max_tokens': 2000,
            'parallel': False
        }
        
        if match:
            try:
                import yaml
                yaml_content = match.group(1)
                metadata = yaml.safe_load(yaml_content)
                workflow_config.update(metadata)
            except (ImportError, Exception) as e:
                logger.warning(f"Could not parse workflow frontmatter: {e}")
        
        # Extract workflow content
        content = re.sub(frontmatter_pattern, '', content, flags=re.DOTALL).strip()
        workflow_config['system_prompt'] = content

        return workflow_config

    def get_routing_agent(self, available_agents: str, query_type: str) -> Agent:
        """Get the routing agent for query routing"""
        workflow_name = "routing"

        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")

        routing_workflow = self.workflows[workflow_name]
        
        context = {
            'workflow_name': "routing",
            'workflow': routing_workflow,
            'agents': self.agents,
            'placeholders': {
                'available_agents': available_agents,
                'query_type': query_type
            }
        }

        # Run the routing workflow
        result = self._get_workflow_step("routing", context)
        return result["agent"]

    def get_orchestrator_agent(self) -> Agent:
        """Main entry point to get main workflow"""
        workflow_name = "orchestrator_main"
        
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        main_workflow = self.workflows[workflow_name]

        context = {
            'workflow_name': workflow_name,
            'workflow': main_workflow,
            'agents': self.agents,
            'placeholders': []
        }

        # Run the workflow
        result = self._get_workflow_step(workflow_name, context)
        return result["agent"]

            

    def _get_workflow_step(self, step: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step in the workflow"""
        logger.info(f"Executing workflow step: {step}")
        workflow = context['workflow']

        # Define model settings
        settings = ModelSettings(
            temperature=workflow.get('temperature', 0.7), 
            max_tokens=workflow.get('max_tokens', 2000)
        )

        model = workflow.get('model', 'gemini-2.5-flash-lite')
        provider = workflow.get('provider', 'google')

        system_prompt = workflow.get('system_prompt', '')

        if not system_prompt:
            raise ValueError("System prompt is required for workflow execution")

        # Check if context have placeholders
        if 'placeholders' in context:
            for key, value in context['placeholders'].items():
                system_prompt = system_prompt.replace(f"{{{{{key}}}}}", str(value))
        
        logger.info(f"System prompt: {system_prompt}")

        # Determine model and provider
        if provider.lower() == "google":
            if os.getenv("GOOGLE_GENAI_USE_VERTEXAI") == "TRUE":
                model_pydantic = GeminiModel(
                    model,
                    provider='google-vertex',
                    settings=settings
                )
            else:
                model_pydantic = GeminiModel(
                    model,
                    provider='google-gla',
                    settings=settings
                )
        elif provider.lower() == "anthropic":
            model_pydantic = AnthropicModel(
                model,
                settings=settings
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}. Supported providers are 'google' and 'anthropic'.")

        # Create PydanticAI agent
        agent = Agent(
            model=model_pydantic,
            system_prompt=system_prompt,
        )

        return {
            'step': step,
            'agent': agent,
            'execution_type': 'sequential'
        }

    async def parallel_execution(self, agent_configs: List[Dict[str, Any]], message: str) -> Dict[str, Any]:
        """Execute multiple agents in parallel"""
        import asyncio
        
        tasks = []
        agent_names = []
        
        for config in agent_configs:
            agent_name = config['agent']
            if agent_name not in self.agents:
                logger.warning(f"Agent '{agent_name}' not found, skipping")
                continue
            
            agent = self.agents[agent_name]
            task_message = config.get('message', message)
            tasks.append(agent.run(task_message))
            agent_names.append(agent_name)
        
        if not tasks:
            return {'error': 'No valid agents found for parallel execution'}
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            parallel_results = {
                'execution_type': 'parallel',
                'agent_count': len(agent_names),
                'results': {},
                'errors': {}
            }
            
            for i, result in enumerate(results):
                agent_name = agent_names[i]
                if isinstance(result, Exception):
                    parallel_results['errors'][agent_name] = str(result)
                else:
                    parallel_results['results'][agent_name] = result.output
            
            return parallel_results
            
        except Exception as e:
            return {'error': f'Parallel execution failed: {e}'}
    
    def list_workflows(self) -> List[str]:
        """List all available workflows"""
        return list(self.workflows.keys())
    
    def get_workflow_info(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific workflow"""
        return self.workflows.get(workflow_name)
    
    def add_agent(self, name: str, agent: Agent) -> None:
        """Add an agent to the orchestrator"""
        self.agents[name] = agent
        logger.info(f"Added agent: {name}")
    
    def remove_agent(self, name: str) -> bool:
        """Remove an agent from the orchestrator"""
        if name in self.agents:
            del self.agents[name]
            logger.info(f"Removed agent: {name}")
            return True
        return False
    
    def get_agent_list(self) -> List[str]:
        """Get list of all available agents"""
        return list(self.agents.keys())