import http.client
import json
from urllib.parse import urlparse
from typing import Optional

def tool_get_exchange_rate(base: str, target: str) -> Optional[dict]:
    """
    Fetches the current exchange rate between two currencies.

    Args:
            base: The base currency (e.g., "SGD").
            target: The target currency (e.g., "JPY").

    Returns:
            The exchange rate information as ExchangeRateResponse object,
            or None if the rate could not be fetched.
    """
    try:        
        base_url = "https://hexarate.paikama.co/api/rates/latest"
        api_url = f"{base_url}/{base}?target={target}"
        
        # Parse the URL
        parsed_url = urlparse(api_url)
        
        # Create HTTPS connection
        conn = http.client.HTTPSConnection(parsed_url.netloc)
        
        try:
            # Make the GET request
            conn.request("GET", parsed_url.path + "?" + parsed_url.query)
            
            # Get the response
            response = conn.getresponse()
            
            if response.status == 200:
                # Read and decode the response data
                data = response.read().decode('utf-8')
                json_data = json.loads(data)

                return json_data
            else:
                return None
                
        except Exception as e:
            print(f"HTTP request error: {e}")
            return None
        finally:
            # Always close the connection
            conn.close()
            
    except Exception as e:
        print(f"Input validation error: {e}")
        return None

# Example usage:
if __name__ == "__main__":
    # Get exchange rate test
    result = get_exchange_rate("SGD", "JPY")
    if result:
        data_exchange = result.get("data", {})
        print(data_exchange)
    else:
        print("Failed to fetch exchange rate")