import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
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
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")

@dataclass
class AgentConfig:
    """Configuration for an agent loaded from markdown"""
    name: str
    category: str
    prompt: str
    file_path: str
    model: str = DEFAULT_MODEL
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
            print("Warning: PyYAML not installed. Frontmatter will be ignored.")
            return AgentMetadata()
        except Exception as e:
            print(f"Warning: Could not parse frontmatter: {e}")
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

        settings = ModelSettings(
            temperature=config.temperature, 
            max_tokens=config.max_tokens
        )

        if config.provider.lower() == "google":
            if os.getenv("GOOGLE_GENAI_USE_VERTEXAI") is "TRUE":
                model = GeminiModel(
                    name=config.model,
                    provider='google-vertex',
                    settings=settings
                )
            else:
                model = GeminiModel(
                    name=config.model,
                    provider='google-gla',
                    settings=settings
                )
        elif config.provider.lower() == "anthropic":
            model = AnthropicModel(
                config.model,
                settings=settings
            )
        else:
            raise ValueError(f"Unsupported provider: {config.provider}. Supported providers are 'google' and 'anthropic'.")

        # Create PydanticAI agent
        agent = Agent(
            model=model,
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
            print(f"No .md files found in {self.agents_directory}")
            return {}
        
        print(f"Loading {len(md_files)} agent files...")
        
        for file_path in md_files:
            try:
                agent = self.load_agent_from_file(file_path)
                config = self.configs[list(self.configs.keys())[-1]]  # Get last added config
                self.agents[config.name] = agent
                print(f"✓ Loaded agent: {config.name} ({config.category})")
            except Exception as e:
                print(f"✗ Failed to load {file_path}: {e}")
        
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
    
    def print_agent_info(self):
        """Print information about all loaded agents"""
        print(f"\n=== Loaded Agents ({len(self.agents)}) ===")
        
        categories = self.loader.get_categories()
        for category in sorted(categories):
            agents = self.loader.get_agents_by_category(category)
            print(f"\n{category.upper()}:")
            for name in sorted(agents.keys()):
                config = self.loader.configs[name]
                print(f"  • {name} ({config.model})")


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
    
    # Initialize the agent manager
    manager = AgentManager("./agents")
    
    # Print loaded agents
    manager.print_agent_info()
    
    # Run a specific agent
    if "frontend_developer" in manager.agents:
        response = await manager.run_agent(
            "frontend_developer",
            "How do I optimize React component re-renders?"
        )
        print(f"\nFrontend Developer Response:\n{response}")
    
    # Run all engineering agents on the same question
    engineering_responses = await manager.run_category_consensus(
        "engineering",
        "What are the key considerations for building scalable applications?"
    )
    
    print("\n=== Engineering Team Consensus ===")
    for agent_name, response in engineering_responses.items():
        print(f"\n{agent_name}:")
        print(response[:200] + "..." if len(response) > 200 else response)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())