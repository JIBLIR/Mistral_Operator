from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """
    Complete vocabulary of low-level actions agent 4 can emit.
    All actions are abstract / simulated unless executed by PyAutoGUIExecutor.
    """
    MOVE         = "MOVE"          # params: {"x": int, "y": int}
    CLICK        = "CLICK"         # params: {"button": "left"|"right"}, default "left"
    DOUBLE_CLICK = "DOUBLE_CLICK"  # double left-click (e.g. select a word)
    SCROLL       = "SCROLL"        # params: {"direction": "up"|"down", "amount": int}
    SELECT_TEXT  = "SELECT_TEXT"   # highlight a range of text
    FOCUS_INPUT  = "FOCUS_INPUT"   # place keyboard focus on an input field
    TYPE         = "TYPE"          # params: {"text": str}  (may come from agent 5)
    OPEN_APP     = "OPEN_APP"      # target: app name  (e.g. "Gmail")
    OPEN_URL     = "OPEN_URL"      # target: full URL  (e.g. "https://...")
    PRESS        = "PRESS"         # params: {"key": str}  e.g. "enter", "ctrl+a"
    WAIT         = "WAIT"          # params: {"ms": int}
    ZOOM         = "ZOOM"          # params: {"direction": "in"|"out", "amount": int}


class Action(BaseModel):
    """
    One serialisable low-level action in the executor vocabulary.

    Fields are intentionally broad so a future real computer-use backend
    can pass coordinates, selectors, window handles, etc. inside `params`
    without changing the model schema.
    """
    action_type: ActionType
    target: str | None = None
    # ^ identifies *what* to act on:
    #   CLICK / FOCUS_INPUT → UI element id or label  (e.g. "compose_body")
    #   OPEN_APP            → app name               (e.g. "Gmail")
    #   OPEN_URL            → full URL               (e.g. "https://mail.google.com")
    #   TYPE                → destination field id
    #   MOVE                → element id or None (use params for coords)
    params: dict[str, Any] = Field(default_factory=dict)
    # ^ action-specific payload, e.g.:
    #   TYPE   → {"text": "..."}
    #   SCROLL → {"direction": "down", "amount": 3}
    #   MOVE   → {"x": 540, "y": 720}
    #   WAIT   → {"ms": 500}
    #   PRESS  → {"key": "ctrl+a"}
    description: str = ""
    # ^ human-readable note — used for logging and debugging only