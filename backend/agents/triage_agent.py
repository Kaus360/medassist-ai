"""
backend/agents/triage_agent.py

Symptom triage agent for MedAssist AI.

Responsibilities:
- Maintain a slot-filling dialogue to collect required clinical data
- Emit ASK responses when more information is needed
- Emit PROCEED responses (+ structured metadata) when triage is complete

State machine:
    INCOMPLETE  →  status: "ASK"
    COMPLETE    →  status: "PROCEED"

No memory logic lives here – the agent is stateless across requests.
The caller (chat route) is responsible for persistence.
"""

from __future__ import annotations

import re
from typing import Any

from backend.agents.base import BaseAgent


# ---------------------------------------------------------------------------
# Slot schema: each slot has a key, a user-facing question, and an optional
# regex extractor.  Add / remove slots here without touching the engine.
# ---------------------------------------------------------------------------
_SLOTS: list[dict[str, Any]] = [
    {
        "key": "symptom",
        "question": "What is your primary symptom?",
        "pattern": None,  # free text – take the whole input
    },
    {
        "key": "duration",
        "question": "How long have you been experiencing this? (e.g. '2 days', '1 week')",
        "pattern": r"\d+\s*(?:hour|day|week|month)s?",
    },
    {
        "key": "severity",
        "question": "On a scale of 1–10, how severe is your discomfort?",
        "pattern": r"\b([1-9]|10)\b",
    },
    {
        "key": "temperature",
        "question": "Do you have a fever? If yes, what is your temperature? (e.g. '101°F' or 'no')",
        "pattern": None,  # free text
    },
]


class TriageAgent(BaseAgent):
    """
    Slot-filling triage agent that drives a structured symptom intake dialog.

    The agent receives the current user message and the accumulated conversation
    history (list of {role, content} dicts).  It fills slots progressively and
    returns a typed response dict.

    Response schema:
        {
            "status": "ASK" | "PROCEED",
            "message": str,
            "meta": {
                "symptom": str,          # present when status == "PROCEED"
                "filled_slots": list,    # always present
                ...
            },
            "extracted_data": dict       # all filled slot values (always present)
        }
    """

    def __init__(self) -> None:
        super().__init__()
        self._slot_keys = [s["key"] for s in _SLOTS]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_next_step(
        self,
        user_input: str,
        history: list[dict[str, str]],
    ) -> dict[str, Any]:
        """
        Process the latest user message and advance the triage state machine.

        Args:
            user_input: The most recent user message.
            history:    Full conversation history so far (read-only).

        Returns:
            Typed triage response dict (see class docstring).
        """
        extracted = self._extract_slots_from_history(history, user_input)
        missing = self._find_missing_slots(extracted)

        if missing:
            next_slot = missing[0]
            question = self._question_for_slot(next_slot)
            return self._build_ask(question, extracted)

        # All slots filled → emit PROCEED with full metadata
        return self._build_proceed(extracted)

    # ------------------------------------------------------------------
    # Slot extraction
    # ------------------------------------------------------------------

    def _extract_slots_from_history(
        self,
        history: list[dict[str, str]],
        current_input: str,
    ) -> dict[str, str]:
        """
        Scan conversation history + current input for slot values.
        Fills slots in order; stops once all are filled.
        """
        # Combine all user utterances (oldest first) + current message
        user_texts: list[str] = [
            msg["content"]
            for msg in history
            if msg.get("role") == "user"
        ]
        user_texts.append(current_input)

        filled: dict[str, str] = {}

        for slot_def in _SLOTS:
            key = slot_def["key"]
            pattern = slot_def["pattern"]

            for text in user_texts:
                if key in filled:
                    break
                value = self._extract_value(text, pattern)
                if value:
                    filled[key] = value

        return filled

    @staticmethod
    def _extract_value(text: str, pattern: str | None) -> str:
        """Extract a value from text using pattern, or take full text if no pattern."""
        text = text.strip()
        if not text:
            return ""
        if pattern is None:
            return text
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0) if match else ""

    def _find_missing_slots(self, filled: dict[str, str]) -> list[str]:
        """Return list of slot keys that have not yet been filled."""
        return [key for key in self._slot_keys if not filled.get(key)]

    @staticmethod
    def _question_for_slot(slot_key: str) -> str:
        for slot_def in _SLOTS:
            if slot_def["key"] == slot_key:
                return slot_def["question"]
        return "Could you provide more information?"

    # ------------------------------------------------------------------
    # Response builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_ask(question: str, extracted: dict[str, str]) -> dict[str, Any]:
        return {
            "status": "ASK",
            "message": question,
            "meta": {
                "filled_slots": list(extracted.keys()),
            },
            "extracted_data": dict(extracted),
        }

    @staticmethod
    def _build_proceed(extracted: dict[str, str]) -> dict[str, Any]:
        return {
            "status": "PROCEED",
            "message": (
                "Thank you for providing your details. "
                "I'll now prepare clinical guidance for you."
            ),
            "meta": {
                "symptom": extracted.get("symptom", ""),
                "duration": extracted.get("duration", ""),
                "severity": extracted.get("severity", ""),
                "temperature": extracted.get("temperature", ""),
                "filled_slots": list(extracted.keys()),
            },
            "extracted_data": dict(extracted),
        }
