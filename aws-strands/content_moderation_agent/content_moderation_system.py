import os
import logging
from strands import Agent, tool
from utils import create_bedrock_model, safe_structured_output
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@tool
def profanity_scanner(query: str) -> str:
    """Scans text files for profanity and inappropriate content.
    Only access allowed directories.
    
    Args:
        query: The file path to scan for profanity
        
    Returns:
        str: Analysis results or error message
    """
    # Least Privilege: Verify path is in allowed directories
    allowed_dirs = ["/tmp/safe_files_1", "/tmp/safe_files_2"]
    real_path = os.path.realpath(os.path.abspath(query.strip()))
    if not any(real_path.startswith(d) for d in allowed_dirs):
        logging.warning(f"Security violation: {query}")  # Audit Logging
        return "Error: Access denied. Path not in allowed directories."

    try:
        # Error Handling: Read file securely
        if not os.path.exists(query):
            return f"Error: File '{query}' does not exist."
        
        with open(query, 'r', encoding='utf-8') as f:
            file_content = f.read()

        # Create a content analysis agent for profanity detection
        content_analyzer = Agent(
            system_prompt="""You are a content moderator. Analyze the provided text
            and identify any profanity, offensive language, or inappropriate content.
            Report the severity level (mild, moderate, severe) and suggest appropriate
            alternatives where applicable. Be thorough but avoid repeating the offensive
            content in your analysis.
            
            Provide your response in this format:
            - Content Status: [Clean/Contains Issues]
            - Severity: [None/Mild/Moderate/Severe]
            - Issues Found: [Brief description without repeating offensive content]
            - Recommendations: [Suggested actions or alternatives]"""
        )

        # Analyze the content
        scan_prompt = f"Scan this text for profanity and inappropriate content:\n\n{file_content}"
        result = content_analyzer(scan_prompt)
        return result

    except UnicodeDecodeError:
        logging.error(f"Error reading file {query}: Invalid encoding")
        return f"Error: Unable to read file '{query}' - invalid encoding. Please ensure file is UTF-8 encoded."
    except Exception as e:
        logging.error(f"Error scanning file: {str(e)}")  # Audit Logging
        return f"Error scanning file: {str(e)}"


class ProfanityModeratorAgent:
    """A content moderation agent that scans files for inappropriate content using Strands Agents."""
    
    def __init__(self, model=None):
        """Initialize the profanity moderator agent.
        
        Args:
            model: Optional model to use. If None, uses default model.
        """
        # Create the main agent with the profanity scanner tool
        agent_config = {
            "system_prompt": """You are a professional content moderation assistant. You help users scan files 
            for inappropriate content using the profanity_scanner tool. You can:
            
            1. Scan text files for profanity and inappropriate content
            2. Provide summaries of moderation results
            3. Suggest content alternatives when appropriate
            4. Handle batch processing of multiple files
            
            Always use the profanity_scanner tool when asked to analyze files.
            Be helpful, professional, and thorough in your responses.
            
            When providing results, summarize the findings clearly and offer actionable recommendations.""",
            "tools": [profanity_scanner]
        }
        
        # Add model if provided
        if model:
            agent_config["model"] = model
            
        self.agent = Agent(**agent_config)
    
    def scan_file(self, file_path: str) -> str:
        """Scan a specific file for profanity and inappropriate content.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            str: Moderation results
        """
        try:
            prompt = f"Please scan the file at '{file_path}' for profanity and inappropriate content using the profanity_scanner tool."
            result = self.agent(prompt)
            return result
        except Exception as e:
            logging.error(f"Error in scan_file: {str(e)}")
            return f"Error: {str(e)}"
    
    def moderate_content(self, user_request: str) -> str:
        """Handle general moderation requests.
        
        Args:
            user_request: User's content moderation request
            
        Returns:
            str: Response to the moderation request
        """
        try:
            result = self.agent(user_request)
            return result
        except Exception as e:
            logging.error(f"Error in moderate_content: {str(e)}")
            return f"Error: {str(e)}"
    
    def batch_scan(self, file_paths: list) -> dict:
        """Scan multiple files for inappropriate content.
        
        Args:
            file_paths: List of file paths to scan
            
        Returns:
            dict: Results for each file
        """
        results = {}
        for file_path in file_paths:
            try:
                result = self.scan_file(file_path)
                results[file_path] = result
            except Exception as e:
                results[file_path] = f"Error: {str(e)}"
                
        return results


def create_moderator_agent(model=None):
    """Factory function to create a profanity moderator agent.
    
    Args:
        model: Optional model instance (BedrockModel, etc.)
        
    Returns:
        ProfanityModeratorAgent: Configured moderator agent
    """
    return ProfanityModeratorAgent(model=model)


def run_comprehensive_demo():
    """Example of how to use the ProfanityModeratorAgent."""
    
    # Create a Bedrock model instance
    bedrock_model = create_bedrock_model()
    
    # Create the moderation agent
    moderator = create_moderator_agent(bedrock_model)

    # Example 1: Direct file scanning
    print("=== Direct File Scan ===")
    result1 = moderator.scan_file("/tmp/safe_files_1/sample.txt")
    print(result1)
    
    # Example 2: Interactive moderation
    print("\n=== Interactive Moderation ===")
    result2 = moderator.moderate_content(
        "I need to check if the file /tmp/safe_files_2/user_comments.txt contains any inappropriate language."
    )
    print(result2)
    
    # Example 3: Batch processing
    print("\n=== Batch Processing ===")
    files_to_scan = [
        "/tmp/safe_files_1/document1.txt",
        "/tmp/safe_files_1/document2.txt",
        "/tmp/safe_files_2/reviews.txt"
    ]
    
    batch_results = moderator.batch_scan(files_to_scan)
    for file_path, result in batch_results.items():
        print(f"\nScanning: {file_path}")
        print(f"Result: {result}")

