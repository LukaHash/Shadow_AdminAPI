from app.schemas import CommandRequest
import pydirectinput
pydirectinput.PAUSE = 0.00001
import pyautogui

pressedkeys = set()
pressedmouse = set()

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

    if param.action in ("scroll",) and (not isinstance(param.parameter, int)):
        raise ValueError(f"parameter must be integer")
    if param.x and param.y and (param.x < 0 or param.y < 0):
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
    if param.action == "hotkey":
        keys = str(param.parameter).split("+")
        for k in keys:
            if k not in pydirectinput.KEYBOARD_MAPPING.keys():
                raise ValueError(f"Unsupported key in hotkey: {k}")
    allow[param.action]()
    if param.action == "down":
        pressedkeys.add(param.parameter)
    if param.action == "up":
        pressedkeys.discard(param.parameter)
    if param.action == "mouse_down":
        pressedmouse.add(param.button)
    if param.action == "mouse_up":
        pressedmouse.discard(param.button)
    return {f"Action: {param.action} completed"}


def release_all_input():
    if pressedmouse:
        for i in pressedmouse:
            pydirectinput.mouseUp(button=i)
    if pressedkeys:
        for i in pressedkeys:
            pydirectinput.keyUp(i)

