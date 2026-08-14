from fastapi import HTTPException
from app.schemas import CommandRequest
from time import sleep
import pydirectinput
pydirectinput.PAUSE = 0.00001
import pyautogui



def allowcommand(param: CommandRequest):
    width, height = pydirectinput.size()
    allow = {"press": lambda: pydirectinput.press(param.parameter),
             "type":  lambda: pydirectinput.write(param.parameter,interval=0.02),
             "up": lambda: pydirectinput.keyUp(param.parameter),
             "down": lambda: pydirectinput.keyDown(param.parameter),
             "click": lambda: pydirectinput.click(int(param.x*width),int(param.y*height),button=param.button),
             "move": lambda: pydirectinput.moveTo(int(param.x*width),int(param.y*height)),
             "scroll": lambda: pyautogui.scroll(int(param.parameter)),
            "mouse_up": lambda: pydirectinput.mouseUp(button=param.button),
            "mouse_down": lambda: pydirectinput.mouseDown(button=param.button),
             "hotkey": lambda: pyautogui.hotkey(*param.parameter.split("+")),
             }

    if param.action in ("scroll",) and not isinstance(param.parameter, int):
        raise ValueError(f"parameter must be integer")
    if param.x < 0 or param.y < 0:
        raise ValueError("Coordinates can't be negative")
    if param.action not in allow:
        raise ValueError("Unsupported action")
    if param.action in ("press", "up", "down") and (not param.parameter or param.parameter not in pydirectinput.KEYBOARD_MAPPING.keys()):
        raise ValueError(f"Unsupported key: {param.parameter}")
    if param.action in ("type","scroll","hotkey") and not param.parameter:
        raise ValueError("param cannot be empty")
    if param.action in ("click","move") and (param.y is None or param.x is None):
        raise ValueError("param cannot be empty")
    if param.action in ("click","mouse_up","mouse_down") and (param.button is None):
        raise ValueError("param cannot be empty")
    allow[param.action]()
    return {"status": "success", "message": f"{param} pressed"}




