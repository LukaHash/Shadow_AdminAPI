from pydantic import BaseModel
from typing import Literal

class CommandRequest(BaseModel):
    action: str
    parameter: str|float|None= None
    x: float |None= None
    y: float | None = None
    button: Literal["right","left","middle"] | None = "left"




class CommandResponse(BaseModel):
    status: str
    message: str
