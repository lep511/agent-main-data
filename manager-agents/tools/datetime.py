from datetime import datetime, timezone

def tool_get_current_datetime() -> str:
    """
    Get the current date and time as a formatted string.
    
    Returns:
        str: Current datetime in ISO format (YYYY-MM-DD HH:MM:SS)
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def tool_get_current_datetime_utc() -> str:
    """
    Get the current UTC date and time.
    
    Returns:
        str: Current UTC datetime in ISO format
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

def tool_get_current_datetime_iso() -> str:
    """
    Get the current date and time in ISO format with timezone.
    
    Returns:
        str: Current datetime in ISO format with timezone info
    """
    return datetime.now(timezone.utc).isoformat()