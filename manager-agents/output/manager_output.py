from typing import Dict, Callable
from venv import logger
from output.invoice import Invoice
from output.shape import ShapeAttributes

def get_output_registry() -> Dict[str, Callable]:
    """
    Returns a dictionary of output types available in the system.
    """
    return {
        "invoice": Invoice,
        "shape_attributes": ShapeAttributes
    }

