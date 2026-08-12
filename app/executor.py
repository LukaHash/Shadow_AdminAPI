from fastapi import HTTPException
from app.schemas import CommandRequest
from time import sleep
import pydirectinput
pydirectinput.PAUSE = 0.00001
import pyautogui

width, length = pydirectinput.size()

def allowcommand(param: CommandRequest):
    allow = {"press": lambda: pydirectinput.press(param.parameter),
             "type":  lambda: pydirectinput.write(param.parameter,interval=0.02),
             "up": lambda: pydirectinput.keyUp(param.parameter),
             "down": lambda: pydirectinput.keyDown(param.parameter),
             "click": lambda: pydirectinput.click(int(param.x*width),int(param.y*length),button=param.button),
             "move": lambda: pydirectinput.moveTo(int(param.x*width),int(param.y*length)),
             "scroll": lambda: pyautogui.scroll(int(param.parameter)),
            "mouse_up": lambda: pydirectinput.mouseUp(int(param.x*width),int(param.y*length), button=param.button),
            "mouse_down": lambda: pydirectinput.mouseDown(int(param.x*width),int(param.y*length), button=param.button),
             "hotkey": lambda: pyautogui.hotkey(*param.parameter.split("+")),
             }
    if param.action not in allow:
        raise ValueError("Unsupported action")
    if param.action in ("press", "up", "down") and (not param.parameter or param.parameter not in pydirectinput.KEYBOARD_MAPPING.keys()):
        raise ValueError(f"Unsupported key: {param.parameter}")
    if param.action in ("type","scroll") and not param.parameter:
        raise ValueError("param cannot be empty")
    if param.action in ("click","move") and (param.y is None or param.x is None):
        raise ValueError("param cannot be empty")
    if param.action in ("click","mouse_up","mouse_down") and (param.button is None):
        raise ValueError("param cannot be empty")
    allow[param.action]()
    return {"status": "success", "message": f"Key {param} pressed"}


