from pydantic import BaseModel


class CommandRequest(BaseModel):
    action: str
    parameter: str|None = None

class CommandResponse(BaseModel):
    status: str
    message: str
