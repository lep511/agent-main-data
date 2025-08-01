import os
import http.client
import json
from typing import Optional
from dotenv import load_dotenv
import logging
import time

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
    Scrape a webpage using the Serper API with retry logic.

    Args:
        url (str): The URL of the webpage to scrape

    Returns:
        dict: JSON response from the API, or custom error
    """
    max_retries = 3     # Maximum number of retry attempts
    base_delay = 1.0    # Base delay between retries in seconds
    
    for attempt in range(max_retries + 1):
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

            # Check for HTTP errors
            if res.status >= 400:
                raise Exception(f"HTTP {res.status}: {res.reason}")

            # Parse and return JSON response
            return json.loads(data.decode("utf-8"))

        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            
            # If this was the last attempt, return error
            if attempt == max_retries:
                logger.error(f"All {max_retries + 1} attempts failed for URL: {url}")
                return {"ERROR": str(e)}
            
            # Calculate delay with exponential backoff
            delay = base_delay * (2 ** attempt)
            logger.info(f"Retrying in {delay:.2f} seconds...")
            time.sleep(delay)

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