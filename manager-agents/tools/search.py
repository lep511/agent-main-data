import os
import http.client
import json
from typing import Optional
from typing import Optional, Tuple
from dotenv import load_dotenv
import urllib.parse
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
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

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

def tool_get_weather_forecast(location: str) -> dict:
    """
    Get weather forecast using Google Weather API.

    Args:
        location (str): The location to get the weather forecast

    Returns:
        dict: JSON response from the API, or error message
    """    
    # API endpoint details
    host = "weather.googleapis.com"
    path = "/v1/forecast/days:lookup"

    geo_location = tool_get_coordinates(location)
    logger.info(f"Coordinates for {location}: {geo_location}")
    if not geo_location:
        return {"ERROR": "Failed to get coordinates for the location."}
    
    latitude, longitude = geo_location
    
    # Parameters
    params = {
        "key": GOOGLE_API_KEY,
        "location.latitude": str(latitude),
        "location.longitude": str(longitude),
        "days": "7"
    }
    
    # Build query string
    query_string = urllib.parse.urlencode(params)
    full_path = f"{path}?{query_string}"
    
    # Create HTTPS connection
    conn = http.client.HTTPSConnection(host)
    
    try:
        # Make GET request
        conn.request("GET", full_path)
        
        # Get response
        response = conn.getresponse()
        
        # Read response data
        data = response.read().decode('utf-8')
                
        # Parse JSON if response is successful
        if response.status == 200:
            try:
                json_data = json.loads(data)
                return json_data
            except json.JSONDecodeError:
                logger.warning("Response is not valid JSON")
                return data
        else:
            logger.error(f"Request failed with status {response.status}")
            return {"ERROR": str(response.status)}

    except Exception as e:
        logger.error(f"Error making request: {e}")
        return {"ERROR": str(e)}
        
    finally:
        # Close connection
        conn.close()

def tool_get_coordinates(location: str) -> Optional[Tuple[float, float]]:
    """
    Get latitude and longitude for any location using Google Geocoding API with retry logic.
    
    Args:
        location: The location to geocode (e.g., "Mountain View, CA")
        
    Returns:
        Tuple of (latitude, longitude) or None if failed
    """
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries + 1):
        conn = None
        try:
            # Build request
            params = {"address": location, "key": GOOGLE_API_KEY}
            query_string = urllib.parse.urlencode(params)
            path = f"/maps/api/geocode/json?{query_string}"
            
            # Make request
            conn = http.client.HTTPSConnection("maps.googleapis.com", timeout=10)
            conn.request("GET", path)
            response = conn.getresponse()
            data = response.read().decode('utf-8')
            
            # Check response
            if response.status == 200:
                result = json.loads(data)
                if result.get("status") == "OK" and result.get("results"):
                    location = result["results"][0]["geometry"]["location"]
                    return (location["lat"], location["lng"])
            
            # Retry on failure
            if attempt < max_retries:
                time.sleep(retry_delay)
                retry_delay *= 2
                
        except Exception:
            if attempt < max_retries:
                time.sleep(retry_delay)
                retry_delay *= 2
        finally:
            if conn:
                conn.close()
    
    return None

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