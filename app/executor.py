from fastapi import HTTPException
from app.schemas import CommandRequest
from time import sleep
import pydirectinput
pydirectinput.PAUSE = 0.00001





def allowcommand(action: str, parameter: str|None):
    allow = {"press": lambda: pydirectinput.press(parameter), "type":  lambda: pydirectinput.write(parameter,interval=0.02),"up": lambda: pydirectinput.keyUp(parameter),"down": lambda: pydirectinput.keyDown(parameter)}
    if action not in allow:
        raise ValueError("Unsupported action")
    if action in ("press", "up", "down") and (not parameter or parameter not in pydirectinput.KEYBOARD_MAPPING.keys()):
        raise ValueError(f"Unsupported key: {parameter}")
    if action == "type" and not parameter:
        raise ValueError("param cannot be empty")
    allow[action]()
    return {"status": "success", "message": f"Key {parameter} pressed"}


