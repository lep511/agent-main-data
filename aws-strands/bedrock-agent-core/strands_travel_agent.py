import logging
from strands import Agent, tool
from strands.models import BedrockModel
from typing import Optional
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@tool
def web_search(query: str, count: int = 10, country: str = "US", search_lang: str = "en") -> str:
    """Search the web for current information about travel destinations, attractions, and events using Brave API."""
    try:
        api_key = os.getenv("BRAVE_SEARCH_API_KEY")
        
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key,
            },
            params={
                "q": query,
                "count": min(count, 20),  # Brave API allows max 20 results
                "country": country,
                "search_lang": search_lang,
            },
            timeout=10  # Add timeout for better error handling
        )
        
        # Check if request was successful
        response.raise_for_status()
        data = response.json()
        
        # Extract web results
        web_results = data.get("web", {}).get("results", [])
        
        if not web_results:
            return "No results found."
        
        formatted_results = []
        for i, result in enumerate(web_results[:count], 1):
            title = result.get("title", "No title")
            description = result.get("description", "No description")
            url = result.get("url", "No URL")
            
            formatted_results.append(
                f"{i}. {title}\n"
                f"   {description}\n"
                f"   Source: {url}\n"
            )
        
        return "\n".join(formatted_results)
        
    except requests.exceptions.RequestException as e:
        return f"Network error: {str(e)}"
    except requests.exceptions.HTTPError as e:
        return f"HTTP error: {str(e)}"
    except KeyError as e:
        return f"API response format error: {str(e)}"
    except Exception as e:
        return f"Search error: {str(e)}"

def get_bedrock_model():
    model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
    region = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
    
    try:
        bedrock_model = BedrockModel(
            model_id=model_id,
            region_name=region,
            temperature=0.0,
            max_tokens=512
        )
        logger.info(f"Successfully initialized Bedrock model: {model_id} in region: {region}")
        return bedrock_model
    except Exception as e:
        logger.error(f"Failed to initialize Bedrock model: {str(e)}")
        logger.error("Please ensure you have proper AWS credentials configured and access to the Bedrock model")
        raise

# Initialize the model
bedrock_model = get_bedrock_model()

# Create the travel agent
travel_agent = Agent(
    model=bedrock_model,
    system_prompt="""You are an experienced travel agent specializing in personalized travel recommendations 
    with access to real-time web information. Your role is to find dream destinations matching user preferences 
    using web search for current information. You should provide comprehensive recommendations with current 
    information, brief descriptions, and practical travel details.""",
    tools=[web_search]
)

# Execute the travel research task
query = """Research and recommend suitable travel destinations for someone looking for good food, parks 
and museums in Montevideo, Uruguay. Use web search to find current information about venues, 
events, and attractions."""

result = travel_agent(query)
print("Result:", result)