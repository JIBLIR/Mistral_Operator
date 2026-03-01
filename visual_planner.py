# visual_planner.py — Vision-guided closed-loop action planner.
#
# Vision-guided action loop:
#   1. YOLO detects screen elements → list of detections.
#   2. VisualPlanner.plan(command, yolo_detections) sends detections +
#      the natural-language command to a Mistral chat model.
#   3. The model responds with a JSON object containing:
#        - "actions"  → ordered list of low-level Actions
#        - "status"   → "in_progress" | "done" | "error"
#        - "message"  → human-readable summary or error detail
#   4. run_loop() executes actions, re-scans, and repeats until
#      status is "done" / "error" or max_steps is reached.
#
# This module is intentionally standalone. It is NOT wired into
# BasicTaskPerformer yet; integration comes in a later iteration.

import json
import os
import re
from dataclasses import dataclass, field
from typing import Callable

from dotenv import load_dotenv
from mistralai import Mistral

from actions import Action, ActionType

load_dotenv()


_SYSTEM_PROMPT = """You are agent 4's visual planner in a multi-agent desktop automation system.

Your job: given a natural-language command and a list of YOLO screen detections,
produce a minimal, ordered list of low-level actions that will accomplish the next
step of the command, then report whether the overall task is complete.

## Available action types (with compact param examples)
  MOVE         params: {"x":160, "y":355}
  CLICK        params: {"button":"left"}    or   {"button":"right"}
  DOUBLE_CLICK params: {}
  SCROLL       params: {"direction":"up"|"down", "amount":3}
  ZOOM         params: {"direction":"in"|"out", "amount":1}
  SELECT_TEXT  params: {"start":0,"end":10}
  FOCUS_INPUT  params: {}
  TYPE         params: {"text":"Hello world"}
  PRESS        params: {"key":"enter"}      or   {"key":"ctrl+a"}
  WAIT         params: {"ms":500}
  OPEN_APP     target: "Gmail"
  OPEN_URL     target: "https://..."

## YOLO detection schema (input)
Each detection looks like:
{
  "label": "button",
  "confidence": 0.92,
  "bbox": {"x": 120, "y": 340, "width": 80, "height": 30}
}
Use bbox to compute click coords: center_x = x + width/2, center_y = y + height/2.

## Output format — CRITICAL
Respond with a single JSON object and nothing else.
No prose, no markdown fences, no explanation outside the object.

{
  "actions": [
    {
      "action_type":  "<ACTION_TYPE>",
      "target":       "<element label or null>",
      "params":       {},
      "description":  "<short note for logging>"
    }
  ],
  "status":  "in_progress" | "done" | "error",
  "message": "<short description of what was done, or what went wrong>"
}

Status semantics:
  "in_progress" — actions have been emitted but the task is not yet complete.
  "done"        — task is fully accomplished; "actions" may be empty.
  "error"       — something prevents completion; "message" must explain why.

## Worked example
Command: "click the Submit button"
Detections: [{"label":"button","confidence":0.95,"bbox":{"x":120,"y":340,"width":80,"height":30}}]

Expected output:
{
  "actions": [
    {"action_type":"MOVE",  "target":"button","params":{"x":160,"y":355},        "description":"Move to Submit button center"},
    {"action_type":"CLICK", "target":"button","params":{"button":"left"},        "description":"Click the Submit button"}
  ],
  "status":  "done",
  "message": "Clicked the Submit button at (160, 355)."
}
"""


@dataclass
class PlanResult:
    """Structured output of a single plan() call."""
    actions: list[Action] = field(default_factory=list)
    status:  str = "in_progress"   # "in_progress" | "done" | "error"
    message: str = ""


class VisualPlanner:
    """Translates a natural-language command + YOLO detections into a PlanResult.

    Uses a Mistral chat completion (not a pre-built agent) so that the system
    prompt — and therefore the output format — are fully under our control.

    Args:
        model: Mistral model ID to use. Defaults to "mistral-medium-latest".
    """

    def __init__(self, model: str = "mistral-small-latest") -> None:
        self._client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
        self._model = model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plan(self, command: str, yolo_detections: list[dict]) -> PlanResult:
        """Return a PlanResult for the current screen state.

        Args:
            command: Natural-language instruction, e.g. "click the Submit button".
            yolo_detections: List of YOLO detection dicts, each with the shape:
                {
                    "label": str,
                    "confidence": float,   # 0.0 – 1.0
                    "bbox": {"x": int, "y": int, "width": int, "height": int}
                }

        Returns:
            A :class:`PlanResult` with validated :class:`actions.Action` objects,
            a status string, and a human-readable message.

        Raises:
            ValueError: If the model response cannot be parsed as a valid JSON object.
        """
        user_message = self._build_user_message(command, yolo_detections)

        response = self._client.chat.complete(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
        )

        raw_text = response.choices[0].message.content
        data = self._extract_object(raw_text)

        actions = [Action(**a) for a in data.get("actions", [])]
        status  = data.get("status",  "in_progress")
        message = data.get("message", "")
        return PlanResult(actions=actions, status=status, message=message)

    def run_loop(
        self,
        command: str,
        get_detections: Callable[[], list[dict]],
        execute: Callable[[Action], None],
        max_steps: int = 20,
    ) -> PlanResult:
        """Drive the observe → plan → act loop until done, error, or max_steps.

        Args:
            command: Natural-language task description.
            get_detections: Zero-argument callable that returns a fresh list of
                YOLO detections (caller owns the screen-capture / YOLO pipeline).
            execute: Callable that accepts a single :class:`Action` and carries
                it out (caller owns the action execution backend).
            max_steps: Hard cap on loop iterations. Defaults to 20.

        Returns:
            The last :class:`PlanResult` returned by :meth:`plan`.
        """
        step = 0
        while step < max_steps:
            detections = get_detections()
            result = self.plan(command, detections)

            for action in result.actions:
                execute(action)

            if result.status in ("done", "error"):
                return result

            step += 1

        return PlanResult(
            actions=[],
            status="error",
            message=f"Max steps ({max_steps}) reached without completion.",
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_user_message(command: str, detections: list[dict]) -> str:
        detections_json = json.dumps(detections, indent=2, ensure_ascii=False)
        return (
            f"Command: {command}\n\n"
            f"Current screen detections:\n{detections_json}"
        )

    @staticmethod
    def _extract_object(raw_text: str) -> dict:
        """Extract the first JSON object from *raw_text*.

        Handles cases where the model wraps output in markdown code fences
        (```json ... ```) or adds surrounding prose.

        Raises:
            ValueError: If no valid JSON object is found.
        """
        # Strip markdown fences if present
        stripped = re.sub(r"```(?:json)?", "", raw_text).strip()

        # Find the outermost {...} block
        match = re.search(r"\{.*\}", stripped, re.DOTALL)
        if not match:
            raise ValueError(
                f"VisualPlanner: model response contains no JSON object.\n"
                f"Raw output:\n{raw_text}"
            )

        try:
            return json.loads(match.group())
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"VisualPlanner: failed to parse JSON from model response.\n"
                f"Parse error: {exc}\n"
                f"Raw output:\n{raw_text}"
            ) from exc