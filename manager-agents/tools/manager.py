from typing import Dict, Callable, List, Optional
from tools.finance import tool_get_exchange_rate
from tools.search import (
    tool_serper_search_google,
    tool_scrape_search,
    tool_get_weather_forecast
)
from tools.datetime import (
    tool_get_current_datetime,
    tool_get_current_datetime_utc,
    tool_get_current_datetime_iso
)
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_tool_registry() -> Dict[str, Callable]:
    """
    Register all available tools.
    Map string names to actual functions.   
    """
    
    # ---------------------  Get exchange rate -------------------------------
    def get_exchange_rate(base: str, target: str) -> Optional[dict]:
        """
        Get the exchange rate between two currencies.
        """
        result = tool_get_exchange_rate(base, target)
        logger.debug(f"Exchange rate from {base} to {target}: {result}")
        return result

    # --------------------- Serper search google ------------------------------
    def serper_search_google(query: str, **kwargs) -> Optional[dict]:
        """
        Search Google using the Serper API.
        
        Args:
            query (str): The search query
        
        Returns:
            dict: JSON response from the API, or None if an error occurred
        """
        result = tool_serper_search_google(query, **kwargs)
        logger.debug(f"Serper search result for query '{query}': {result}")
        return result

    # --------------------- Get current datetime ------------------------------
    def get_current_datetime() -> str:
        """
        Get the current date and time as a formatted string.

        Returns:
            str: Current datetime in ISO format (YYYY-MM-DD HH:MM:SS)
        """
        result = tool_get_current_datetime()
        logger.debug(f"Current datetime: {result}")
        return result

    # --------------------- Get current datetime utc ---------------------------
    def get_current_datetime_utc() -> str:
        """
        Get the current UTC date and time.

        Returns:
            str: Current UTC datetime in ISO format
        """
        result = tool_get_current_datetime_utc()
        logger.debug(f"Current UTC datetime: {result}")
        return result
    
    # --------------------- Get current datetime iso ---------------------------
    def get_current_datetime_iso() -> str:
        """
        Get the current date and time in ISO format with timezone.

        Returns:
            str: Current datetime in ISO format with timezone info
        """
        result = tool_get_current_datetime_iso()
        logger.debug(f"Current datetime in ISO format: {result}")
        return result

    # --------------------------- Scrape search ---------------------------------
    def scrape_search(url: str) -> Optional[dict]:
        """
        Scrape a website using the Serper API.

        Args:
            url (str): The URL to scrape

        Returns:
            dict: JSON response from the API, or None if an error occurred
        """
        result = tool_scrape_search(url)
        logger.debug(f"Scraped URL: {url}")
        return result

    def get_weather(location: str) -> Optional[dict]:
        """
        Get the current weather for a specified location.

        Args:
            location (str): The location to get the weather for

        Returns:
            dict: JSON response containing weather information, or None if an error occurred
        """
        result = tool_get_weather_forecast(location)
        logger.debug(f"Weather for {location}: {result}")
        return result
    # ------------------------------ END -----------------------------------------

    return {
        "get_exchange_rate": get_exchange_rate,
        "serper_search_google": serper_search_google,
        "get_current_datetime": get_current_datetime,
        "get_current_datetime_utc": get_current_datetime_utc,
        "get_current_datetime_iso": get_current_datetime_iso,
        "scrape_search": scrape_search,
        "get_weather": get_weather
    }


def resolve_tools_from_names(tool_names: List[str]) -> List[Callable]:
    """
    Convert a list of tool names to the actual functions.
    """
    tool_registry = get_tool_registry()
    resolved_tools = []
    
    for tool_name in tool_names:
        if tool_name in tool_registry:
            resolved_tools.append(tool_registry[tool_name])
            logger.info(f"✓ Loaded tools: {tool_name}")
        else:
            logger.error(f"✗ Tool '{tool_name}' not found in registry")
    
    return resolved_tools