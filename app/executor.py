from fastapi import HTTPException
from app.schemas import CommandRequest
import pyautogui
from time import sleep
pyautogui.PAUSE = 0.00000001


def allowcommand(action: str, parameter: str|None):
    allow = {"press": lambda: pyautogui.press(parameter), "type":  lambda: pyautogui.write(parameter,interval=0.02),"up": lambda: pyautogui.keyUp(parameter),"down": lambda: pyautogui.keyDown(parameter)}
    if action not in allow:
        raise ValueError("Unsupported action")
    if action in ("press", "up", "down") and (not parameter or parameter not in pyautogui.KEY_NAMES):
        raise ValueError(f"Unsupported key: {parameter}")
    if action == "type" and not parameter:
        raise ValueError("param cannot be empty")
    allow[action]()
    return {"status": "success", "message": f"Key {parameter} pressed"}


