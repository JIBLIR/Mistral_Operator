"""
pyautogui_executor.py — Real OS-level action execution via pyautogui.

Usage:
    from pyautogui_executor import PyAutoGUIExecutor
    exe = PyAutoGUIExecutor()
    exe.execute(action)          # single action
    # or wire into run_loop:
    planner.run_loop(command, get_detections=..., execute=exe.execute)
"""

import time

import pyautogui

from actions import Action, ActionType

pyautogui.FAILSAFE = True   # move mouse to top-left corner to abort


class PyAutoGUIExecutor:
    """Executes Action objects for real using pyautogui.

    Actions not yet implemented (FOCUS_INPUT, SELECT_TEXT, OPEN_APP, OPEN_URL)
    are silently skipped — the caller (BasicTaskPerformer / run_loop) continues
    processing the remaining actions in the sequence.
    """

    def execute(self, action: Action) -> None:
        t = action.action_type
        p = action.params

        if t == ActionType.MOVE:
            pyautogui.moveTo(p["x"], p["y"])

        elif t == ActionType.CLICK:
            btn = p.get("button", "left")
            pyautogui.click(button=btn)

        elif t == ActionType.DOUBLE_CLICK:
            pyautogui.doubleClick()

        elif t == ActionType.SCROLL:
            amount = p.get("amount", 3)
            clicks = amount if p.get("direction", "down") == "up" else -amount
            pyautogui.scroll(clicks)

        elif t == ActionType.ZOOM:
            key = "+" if p.get("direction") == "in" else "-"
            pyautogui.hotkey("ctrl", key)

        elif t == ActionType.TYPE:
            pyautogui.write(p["text"], interval=0.03)

        elif t == ActionType.PRESS:
            # supports single keys and combos like "ctrl+a"
            keys = p["key"].lower().split("+")
            if len(keys) == 1:
                pyautogui.press(keys[0])
            else:
                pyautogui.hotkey(*keys)

        elif t == ActionType.WAIT:
            time.sleep(p.get("ms", 500) / 1000)

        # FOCUS_INPUT, SELECT_TEXT, OPEN_APP, OPEN_URL — not implemented yet