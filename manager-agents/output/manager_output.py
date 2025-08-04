from typing import Dict, Any
from venv import logger
from output.invoice import Invoice
from output.shape import ShapeAttributes
from output.sql import run_sql_query
from output.text import split_into_words
from pydantic_ai import TextOutput

def get_output_registry() -> Dict[str, Any]:
    """
    Returns a dictionary of output types available in the system.
    """
    return {
        "invoice": Invoice,
        "shape_attributes": ShapeAttributes,
        "sql_function": run_sql_query,
        "split_into_words": TextOutput(split_into_words),
    }

