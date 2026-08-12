from pydantic import BaseModel


class CommandRequest(BaseModel):
    action: str
    parameter: str|None|float = None
    x: float |None= None
    y: float | None = None
    button: str | None = "left"




class CommandResponse(BaseModel):
    status: str
    message: str
