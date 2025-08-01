import os
import http.client
import json
from typing import Optional
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def tool_serper_search_google(query: str, **kwargs) -> Optional[dict]:
    """
    Search Google using the Serper API.
    
    Args:
        query (str): The search query
    
    Returns:
        dict: JSON response from the API, or None if an error occurred
    """
    try:
        # Create HTTPS connection
        conn = http.client.HTTPSConnection("google.serper.dev")
        
        # Prepare payload
        payload = json.dumps({
            "q": query
        })
        
        # Set headers
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        # Make the request
        conn.request("POST", "/search", payload, headers)
        
        # Get response
        res = conn.getresponse()
        data = res.read()
        
        # Close connection
        conn.close()
        
        # Parse and return JSON response
        return json.loads(data.decode("utf-8"))
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return None

def tool_scrape_search(url: str) -> dict:
    """
    Scrape a webpage using the Serper API.

    Args:
        url (str): The URL of the webpage to scrape

    Returns:
        dict: JSON response from the API, or custom error
    """
    try:
        # Create HTTPS connection
        conn = http.client.HTTPSConnection("scrape.serper.dev")

        # Prepare payload
        payload = json.dumps({
            "url": url
        })

        # Set headers
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }

        # Make the request
        conn.request("POST", "/", payload, headers)

        # Get response
        res = conn.getresponse()
        data = res.read()

        # Close connection
        conn.close()

        # Parse and return JSON response
        return json.loads(data.decode("utf-8"))

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return {"ERROR": str(e)}

# Example usage:
if __name__ == "__main__":
    # Search for something
    results = serper_search_google("apple inc")
    
    if results:
        print(json.dumps(results, indent=2))
    else:
        print("Search failed")

    url = "https://www.elpais.com.uy/economia-y-mercado/estados-unidos-brasil-y-china-trump-esta-haciendo-algo-que-nadie-quiere"
    results = scrape_search(url)

    if results:
        print(json.dumps(results, indent=2))
    else:
        print("Scrape failed")