from typing import Union, List
from pydantic import BaseModel

class ShapeAttributes(BaseModel):
    attributes: Union[List[str], List[int]]