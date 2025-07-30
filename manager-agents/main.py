import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from orchestrator.orchestrator_core import Orchestrator
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.settings import ModelSettings
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
    category: str
    prompt: str
    file_path: str
    model: str
    provider: str
    temperature: float = 0.7
    max_tokens: int = 4000


class AgentMetadata(BaseModel):
    """Pydantic model for agent metadata parsing"""
    name: Optional[str] = None
    category: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    version: Optional[str] = None

class AgentLoader:
    """Loads and manages PydanticAI agents from markdown files"""
    
    def __init__(self, agents_directory: str = "./agents"):
        self.agents_directory = Path(agents_directory)
        self.agents: Dict[str, Agent] = {}
        self.configs: Dict[str, AgentConfig] = {}
        
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
            category=metadata.category or category,
            prompt=prompt,
            file_path=str(file_path),
            model=metadata.model or DEFAULT_MODEL,
            provider=metadata.provider or DEFAULT_PROVIDER,
            temperature=metadata.temperature or 0.7,
            max_tokens=metadata.max_tokens or 4000
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
        model = DEFAULT_MODEL

        # logger.info(f"Loading agent: {config.name} from {file_path}")

        # Define model settings
        settings = ModelSettings(
            temperature=config.temperature, 
            max_tokens=config.max_tokens
        )

        model = config.model
        provider = config.provider

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
            system_prompt=config.prompt,
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
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get a specific agent by name"""
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """List all loaded agent names"""
        return list(self.agents.keys())
    
    def get_agents_by_category(self, category: str) -> Dict[str, Agent]:
        """Get all agents in a specific category"""
        return {
            name: agent for name, agent in self.agents.items()
            if self.configs[name].category == category
        }
    
    def get_categories(self) -> List[str]:
        """Get all available categories"""
        return list(set(config.category for config in self.configs.values()))


# Example usage and helper functions
class AgentManager:
    """Higher-level manager for working with loaded agents"""

    def __init__(self, agents_directory: str = "./agents"):
        self.loader = AgentLoader(agents_directory)
        self.agents = self.loader.load_all_agents()
    
    async def run_agent(self, agent_name: str, message: str, **kwargs) -> str:
        """Run a specific agent with a message"""
        agent = self.loader.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")
        
        result = await agent.run(message, **kwargs)
        return result.output
    
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
    
# Example markdown file format
EXAMPLE_MARKDOWN = '''---
name: "frontend_developer"
category: "engineering"
model: "claude-sonnet-4-20250514"
temperature: 0.7
max_tokens: 4000
tags: ["react", "typescript", "css"]
description: "Expert frontend developer specializing in modern web technologies"
---

# Frontend Developer Agent

You are an expert frontend developer with deep expertise in modern web technologies. You specialize in React, Vue, Angular, TypeScript, CSS/SASS, responsive design, and performance optimization. 

You write clean, accessible, and maintainable code while staying current with web standards and best practices. When solving problems, you consider user experience, browser compatibility, and performance implications. 

You provide practical solutions with working code examples and explain trade-offs clearly.

## Key Capabilities
- Modern JavaScript/TypeScript development
- React, Vue, Angular frameworks
- Responsive design and CSS architecture
- Performance optimization
- Accessibility best practices
- Testing strategies

## Communication Style
- Provide working code examples
- Explain technical decisions and trade-offs
- Consider performance and user experience
- Stay current with web standards
'''


# Usage example
async def main():
    """Example usage of the agent loader"""
    
    # Step 1: Load agents using AgentManager
    manager = AgentManager("./agents")

    # Step 2: Create orchestrator with loaded agents
    orchestrator = Orchestrator(
        agents=manager.agents,
        orchestrator_directory="./orchestrator"
    )

    print(f"Loaded {len(orchestrator.agents)} agents:")
    for agent_name in orchestrator.get_agent_list():
        print(f"  - {agent_name}")
    
    print(f"\nAvailable workflows: {orchestrator.list_workflows()}")

    # Step 3: Run all agents on a sample question
    question = "How should we approach building a new e-commerce platform?"
    participants = orchestrator.get_agent_list()

    print(f"Participants: {participants}")

    print("\n=== Orchestrator Agent First Step ===")
    orchestrator_agent = orchestrator.orchestrator_agent

    result1 = await orchestrator_agent.run(question)
    print(result1.output)

    print("\n=== Orchestrator Agent Clarification ===")

    clarification = '''
1.  **Budget:** We're aiming for something in the range of **$15,000 to $20,000** for the initial build. We have a bit of flexibility for essential features, but we want to be mindful of costs.

2.  **Timeline:** Ideally, we'd love to launch the basic version of the platform within **3 months**. We understand that more complex features might push that out, but a quick go-to-market is important for us.

3.  **Key Features:** Our absolute must-haves include:
    * A robust **product catalog** with categories and subcategories.
    * **User accounts** with order history and wishlists.
    * Secure **payment gateway integration** (think Stripe and PayPal).
    * Flexible **shipping options** with various rates.
    * Basic **marketing tools** like discount codes and email sign-ups.
    * An easy-to-use **admin panel** for managing products and orders.

4.  **Technical Expertise:** Our internal team has some decent technical skills, but we're definitely **not looking for a fully managed solution** where we have to do everything ourselves. We'd prefer a platform that's fairly intuitive for our marketing and operations team to manage day-to-day. We'd be happy to have our developers handle custom integrations or more advanced maintenance if needed.

5.  **Target Audience:** We're primarily targeting **small to medium-sized businesses (SMBs)**, specifically those in the craft and artisanal goods sector. Our ideal customer values unique, handmade items and appreciates a curated shopping experience.

6.  **Product Type:** We'll be selling **physical goods**, mainly handmade jewelry, custom artwork, and unique home decor items. We might consider digital products down the line, but for now, it's all about physical inventory.
''' 
    print("\n=== Clarification Request ===")
    result2 = await orchestrator_agent.run(
        clarification,
        message_history=result1.new_messages()
    )
    print(result2.output)

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