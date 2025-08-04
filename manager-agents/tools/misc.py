from typing import Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def tool_create_burger_order(user_id: str, order_details: str) -> Optional[str]:
    """
    Create a burger order for the user.

    Args:
        user_id (str): The ID of the user placing the order
        order_details (str): The details of the burger order

    Returns:
        Optional[str]: Confirmation message or None if creation failed
    """
    logger.info(f"Creating burger order for user {user_id} with details: {order_details}")
    return f"Order for user {user_id} created successfully."
