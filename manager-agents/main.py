import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib import response
from orchestrator.orchestrator_core import (
    Orchestrator, 
    RoutingResult,
    parse_routing_result_raw
)
from tools.manager_tools import resolve_tools_from_names
from output.manager_output import get_output_registry
from memory.memory_tools import tool_load_memory
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.settings import ModelSettings
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Default model and provider settings
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.5-pro")
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "google")

@dataclass
class AgentConfig:
    """Configuration for an agent loaded from markdown"""
    name: str
    description: str
    category: str
    prompt: str
    file_path: str
    user_id: str
    model: Optional[str]
    provider: Optional[str]
    base_url: Optional[str] = None
    api_key_name: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4000
    include: Optional[List[str]] = None
    output_type: Optional[str] = None
    tools: Optional[List[str]] = None

class AgentMetadata(BaseModel):
    """Pydantic model for agent metadata parsing"""
    name: str
    description: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tags: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    include: Optional[List[str]] = None
    output_type: Optional[str] = None
    version: Optional[str] = None

class AgentLoader:
    """Loads and manages PydanticAI agents from markdown files"""
    
    def __init__(self, agents_directory: str, user_id: str):
        self.agents_directory = Path(agents_directory)
        self.agents: Dict[str, Agent] = {}
        self.configs: Dict[str, AgentConfig] = {}
        self.user_id = user_id

    def parse_markdown_file(self, file_path: Path) -> AgentConfig:
        """Parse a markdown file and extract agent configuration"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract frontmatter if present (YAML between --- markers)
        metadata = self._extract_frontmatter(content)
        prompt = self._extract_prompt_content(content)
        
        # Generate agent name from file path
        category = file_path.parent.name
        agent_name = file_path.stem.replace('-', '_')
        
        return AgentConfig(
            name=metadata.name or agent_name,
            description=metadata.description or "No description available",
            category=category,
            prompt=prompt,
            file_path=str(file_path),
            user_id=self.user_id,
            model=metadata.model or DEFAULT_MODEL,
            provider=metadata.provider or DEFAULT_PROVIDER,
            base_url=metadata.base_url,
            api_key_name=metadata.api_key_name or "DEFAULT_API_KEY",
            temperature=metadata.temperature or 0.7,
            max_tokens=metadata.max_tokens or 4000,
            tools=metadata.tools or [],
            include=metadata.include or [],
            output_type=metadata.output_type
        )
    
    def _extract_frontmatter(self, content: str) -> AgentMetadata:
        """Extract YAML frontmatter from markdown content"""
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if not match:
            return AgentMetadata()
        
        try:
            import yaml
            yaml_content = match.group(1)
            data = yaml.safe_load(yaml_content)
            return AgentMetadata(**data)
        except ImportError:
            logger.warning("Warning: PyYAML not installed. Frontmatter will be ignored.")
            return AgentMetadata()
        except Exception as e:
            logger.warning(f"Warning: Could not parse frontmatter: {e}")
            return AgentMetadata()
    
    def _extract_prompt_content(self, content: str) -> str:
        """Extract the main prompt content from markdown"""
        # Remove frontmatter if present
        frontmatter_pattern = r'^---\s*\n.*?\n---\s*\n'
        content = re.sub(frontmatter_pattern, '', content, flags=re.DOTALL)
        
        # Clean up the content
        content = content.strip()
        
        # If content starts with a heading, use everything after it
        if content.startswith('#'):
            lines = content.split('\n')
            # Skip the first heading line and any empty lines
            content_lines = []
            skip_initial_heading = True
            for line in lines:
                if skip_initial_heading and line.startswith('#'):
                    continue
                skip_initial_heading = False
                content_lines.append(line)
            content = '\n'.join(content_lines).strip()
        
        return content
    
    def load_agent_from_file(self, file_path: Path) -> Agent:
        """Load a single agent from a markdown file"""
        config = self.parse_markdown_file(file_path)

        # Define instructions and add extra information
        instructions = config.prompt.strip()

        # Check include
        if config.include:
            for item in config.include:
                if item == "user_id":
                    instructions = instructions.replace("{{user_id}}", self.user_id)
                elif item == "current_time_utc":
                    # Get current UTC datetime
                    utc_now = datetime.now(timezone.utc)
                    utc_now_fmt = utc_now.strftime("%Y-%m-%d %H:%M:%S")
                    instructions = instructions.replace("{{current_time_utc}}", utc_now_fmt)
                elif item == "current_time":
                    # Get current local datetime
                    local_now = datetime.now()
                    local_now_fmt = local_now.strftime("%Y-%m-%d %H:%M:%S")
                    instructions = instructions.replace("{{current_time}}", local_now_fmt)
                elif item == "memory":
                    result = tool_load_memory(self.user_id)
                    if result:
                        instructions = instructions.replace("{{memory}}", result)
                    else:
                        instructions = instructions.replace("{{memory}}", "")
                else:
                    logger.warning(f"Unknown include item: {item}. Skipping.")

        # logger.info(f"Loading agent: {config.name} from {file_path}")
        

        # Define model settings
        model = DEFAULT_MODEL
        settings = ModelSettings(
            temperature=config.temperature, 
            max_tokens=config.max_tokens
        )

        model = config.model
        provider = config.provider

        # Determine model and provider
        # ==== GOOGLE =====
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
        
        # ==== OPENAI =====
        elif provider.lower() == "openai":
            if config.base_url:                
                if not os.getenv(config.api_key_name):
                    logger.error(f"ERROR: {config.api_key_name} environment variable is not set.")
                    api_key = ""
                else:
                    api_key = os.getenv(config.api_key_name)

                model_pydantic = OpenAIModel(
                    model,
                    provider=OpenAIProvider(
                        base_url=config.base_url,
                        api_key=api_key
                    ),
                    settings=settings
                )

            else:
                model_pydantic = OpenAIModel(
                    model,
                    settings=settings
                )
        
        # ==== ANTHROPIC =====
        elif provider.lower() == "anthropic":
            model_pydantic = AnthropicModel(
                model,
                settings=settings
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}. Supported providers are 'openai', 'google' and 'anthropic'.")

        # Create parameters for the agent
        parameters = {
            "model": model_pydantic,
            "instructions": instructions
        }

        # Check tools
        if config.tools:
            tools = resolve_tools_from_names(config.tools)
            if not tools:
                logger.error(f"ERROR: No tools found for names: {config.tools}. Please check your tools configuration.")
            else:
                parameters["tools"] = tools
 
        # Check output type
        if config.output_type:
            outputs = get_output_registry()
            output_type = outputs.get(config.output_type)
            if not output_type:
                logger.error(f"ERROR: Output type '{config.output_type}' not found in output registry.")
            else:
                parameters["output_type"] = output_type

        # Create PydanticAI agent
        agent = Agent(
            **parameters,
        )
        
        # Store configuration for reference
        self.configs[config.name] = config
        
        return agent
    
    def load_all_agents(self) -> Dict[str, Agent]:
        """Load all agents from the agents directory"""
        if not self.agents_directory.exists():
            raise FileNotFoundError(f"Agents directory not found: {self.agents_directory}")
        
        # Find all .md files recursively
        md_files = list(self.agents_directory.rglob("*.md"))
        
        if not md_files:
            logger.warning(f"No .md files found in {self.agents_directory}")
            return {}
        
        logger.info(f"Loading {len(md_files)} agent files...")
        
        for file_path in md_files:
            try:
                agent = self.load_agent_from_file(file_path)
                config = self.configs[list(self.configs.keys())[-1]]  # Get last added config
                self.agents[config.name] = agent
                logger.info(f"✓ Loaded agent: {config.name} ({config.category})")
            except Exception as e:
                logger.error(f"✗ Failed to load {file_path}: {e}")

        return self.agents
    
    def load_selected_agents(self, agent_names: List[str]) -> Dict[str, Agent]:
        """Load specific agents by name"""
        if not self.agents_directory.exists():
            raise FileNotFoundError(f"Agents directory not found: {self.agents_directory}")

        # Find all .md files recursively
        md_files = list(self.agents_directory.rglob("*.md"))
        
        if not md_files:
            logger.warning(f"No .md files found in {self.agents_directory}")
            return {}
        
        logger.info(f"Loading {len(md_files)} agent files...")
        loaded_agents = {}
        for file_path in md_files:
            try:
                config = self.parse_markdown_file(file_path)
                if config.name in agent_names:
                    agent = self.load_agent_from_file(file_path)
                    loaded_agents[config.name] = agent
                    self.agents[config.name] = agent
                    self.configs[config.name] = config
                    logger.info(f"✓ Loaded agent: {config.name} ({config.category})")
            except Exception as e:
                logger.error(f"✗ Failed to load {file_path}: {e}")
        
        return loaded_agents
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get a specific agent by name"""
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """List all loaded agent names"""
        return list(self.agents.keys())
    
    def get_agents_by_category(self, category: str) -> Dict[str, Agent]:
        """Get all agents in a specific category"""
        return {
            name: agent for name, agent in self.agents.items() if self.configs[name].category.lower() == category.lower()
        }
    
    def get_categories(self) -> List[str]:
        """Get all available categories"""
        return list(set(config.category for config in self.configs.values()))


# Example usage and helper functions
class AgentManager:
    """Higher-level manager for working with loaded agents"""

    def __init__(
        self,
        agents_directory: str = "./agents",
        user_id: Optional[str] = None,
        selected_agents: Optional[List[str]] = None
    ) -> None:
        self.user_id = user_id or "current_user"
        self.loader = AgentLoader(agents_directory, self.user_id)
        if selected_agents:
            self.agents = self.loader.load_selected_agents(selected_agents)
        else:
            self.agents = self.loader.load_all_agents()
        if not self.agents:
            logger.error("No agents loaded. Please check your agents directory, agent files or agent selected.")

    def get_categories(self) -> str:
        """Get a formatted string of available agent categories"""
        categories = self.loader.get_categories()
        if not categories:
            return "No agent categories available."
        return "\n".join(f"- {cat}" for cat in categories)
    
    def get_full_categories(self) -> str:
        """Get a formatted string of available agent categories and their specializations"""
        lines = []
        for cat in self.loader.get_categories():
            agents_in_category = self.loader.get_agents_by_category(cat)
            lines.append(f"\n### {cat.upper()}")
            for name, agent in agents_in_category.items():
                config = self.loader.configs[name]
                lines.append(f"- **{name}**: {config.description or 'No description available'}")
        return "\n".join(lines)
    
    async def run_agent(self, agent_name: str, message: str, **kwargs) -> Any:
        """Run a specific agent with a message"""
        agent = self.loader.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")

        result = await agent.run(message, **kwargs)
        return result
    
    async def run_category_consensus(self, category: str, message: str) -> Dict[str, str]:
        """Run all agents in a category and return their responses"""
        category_agents = self.loader.get_agents_by_category(category)
        results = {}
        
        for name, agent in category_agents.items():
            try:
                result = await agent.run(message)
                results[name] = result.output
            except Exception as e:
                results[name] = f"Error: {e}"
        
        return results

async def get_routing(question: str, available_categories: str, orchestrator: Orchestrator) -> Optional[RoutingResult]:
    """
    Get the routing result for a given question.
    
    Args:
        question: The question to route
        available_categories: Available categories for routing
        orchestrator: The orchestrator instance
        
    Returns:
        RoutingResult if successful, None if failed
        
    Raises:
        ValueError: If required parameters are invalid
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")
    
    if not available_categories:
        raise ValueError("Available categories cannot be empty")
    
    routing_agent = orchestrator.get_routing_agent(available_categories)
    
    # First attempt: Try with structured output
    try:
        logger.debug(f"Attempting routing with structured output for question: {question[:100]}...")
        result_routing = await routing_agent.run(
            question,
            output_type=RoutingResult,
        )
        logger.info("Successfully obtained routing result with structured output")
        return result_routing.output
        
    except Exception as e:
        logger.warning(f"Structured output routing failed: {e}")
        
        # Second attempt: Fallback to string parsing
        try:
            logger.debug("Attempting fallback routing with string parsing")
            result = await routing_agent.run(question)
            
            if not hasattr(result, 'output') or not result.output:
                logger.error("Routing agent returned empty or invalid result")
                return None
            
            # Clean the response text
            cleaned_response = _clean_json_response(result.output)
            routing_result = parse_routing_result_raw(cleaned_response)

            logger.info("Successfully obtained routing result with fallback method")
            return routing_result

        except Exception as fallback_error:
            logger.error(f"Fallback routing also failed: {fallback_error}")
            return None

def _clean_json_response(response_text: str) -> str:
    """
    Clean JSON response by removing markdown code blocks and extra whitespace.
    
    Args:
        response_text: Raw response text that may contain JSON
        
    Returns:
        Cleaned JSON string
    """
    if not response_text:
        return ""
    
    # Remove markdown code blocks
    cleaned = re.sub(r'```(?:json)?\s*', '', response_text)
    cleaned = re.sub(r'```\s*', '', cleaned)
    
    # Remove extra whitespace
    return cleaned.strip()

# Usage example
async def main():
    """Example usage of the agent loader"""
    user_id = "user_test_003"

    # load agents using AgentManager
    manager = AgentManager(
        agents_directory="./agents",
        user_id=user_id,
        selected_agents=["instagram_curator"]
    )

    if not manager.agents:
        return

    # create orchestrator with loaded agents
    orchestator = Orchestrator(
        agents=manager.agents,
        orchestrator_directory="./orchestrator"
    )
    
    print(f"\nAvailable workflows: {orchestator.list_workflows()}")

    participants = orchestator.get_agent_list()
    print(f"Participants: {participants}")

    print("\n=== Routing Agent ===")
    available_categories = manager.get_full_categories()

    print(f"\nAvailable categories:\n{available_categories}")
    # print(f"\nAvailable categories formatted: {query_type}")

    question = "How should we approach building a new e-commerce platform and publish in Instagram?"
    # question = "What UX research methods should we use to validate our new feature ideas?"
    # question = "Can you analyze our user feedback and identify the top pain points in our app?"
    # question = "How should we structure our database schema for a real-time chat application?"
    # question = "What is the exchange rate from American dollar to Argentine peso?"
    # question = "My IPhone is making a loud strange noise after the latest update—should I be worried?"
    # question = "What is the weather forecast in Mountain View, CA for the next days?"
    # question = "Resumeme esta noticia: https://www.elpais.com.uy/el-empresario/para-que-usan-inteligencia-artificial-los-ceo-uruguayos-chatgpt-gemini-copilot-y-zapia-entre-las-elegidas"
    # question = "Why was my checking account charged a $35 overdraft fee when I thought I had overdraft protection enabled?"
    # question = "I like the cheeseburger which one do you recommend?"
    # question = "Analyze this invoice: Vendor: Acme Corp, 123 Main St, Springfield, IL 62704 Invoice Number: INV-2025-001 Date: 2025-02-10 Items: - Widget A, 5 units, $10.00 each - Widget B, 2 units, $15.00 each Total: $80.00 USD"
    # question = "Extract: red square, blue circle, green triangle"
    # question = "Extract: square size 10, circle size 20, triangle size 30"
    # question = "Run this sql query: Select the names and countries of all capitals in the table capital_cities"
    print("=" * 120)
    print(f"Question: {question}")
    print("=" * 120)

    result_output = await get_routing(question, available_categories, orchestator)
    print(result_output)
    specialist = result_output['specialists'][0]

    response1 = await manager.run_agent(specialist, question)
    print(f"\n{specialist} Response:\n{response1.output}")

    # approve_order = "Yes, I want to order one Double Cheeseburger."
    # response2 = await manager.run_agent(specialist, approve_order, message_history=response1.new_messages())  
    # print(f"\n{specialist} Response:\n{response2.output}")

    # approve_order = "Yes is correct. Save my preferences."
    # response3 = await manager.run_agent(specialist, approve_order, message_history=response2.new_messages())  
    # print(f"\n{specialist} Response:\n{response3.output}")

    # orchestrator_agent = orchestrator.orchestrator_agent

    # result1 = await orchestrator_agent.run(question)
    # print(result1.output)

    # print("\n=== Orchestrator Agent Clarification ===")

    # print("\n=== Clarification Request ===")
    # result2 = await orchestrator_agent.run(
    #     clarification,
    #     message_history=result1.new_messages()
    # )
    # print(result2.output)

    # # Run a specific agent
    # if "frontend_developer" in manager.agents:
    #     response = await manager.run_agent(
    #         "frontend_developer",
    #         "How do I optimize React component re-renders?"
    #     )
    #     print(f"\nFrontend Developer Response:\n{response}")
    
    # # Run all engineering agents on the same question
    # engineering_responses = await manager.run_category_consensus(
    #     "engineering",
    #     "What are the key considerations for building scalable applications?"
    # )
    
    # print("\n=== Engineering Team Consensus ===")
    # for agent_name, response in engineering_responses.items():
    #     print(f"\n{agent_name}:")
    #     print(response[:200] + "..." if len(response) > 200 else response)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())