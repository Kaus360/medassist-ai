"""
backend/agents/triage_agent.py

Symptom triage agent for MedAssist AI.

Responsibilities:
- Maintain a slot-filling dialogue to collect required clinical data
- Emit ASK responses when more information is needed
- Emit PROCEED responses (+ structured metadata) when triage is complete

Enforcement:
- Strictly follows required slots for specific symptoms.
- No auto-filling or assuming values.
"""

from __future__ import annotations

import re
from typing import Any

from backend.agents.base import BaseAgent


# ---------------------------------------------------------------------------
# Slot Definitions & Symptom-Specific Requirements
# ---------------------------------------------------------------------------

REQUIRED_SLOTS_BY_SYMPTOM = {
    "HEADACHE": ["duration", "severity", "type", "associated_symptoms"],
    "CHEST PAIN": ["type", "duration", "severity", "associated_symptoms"],
}

DEFAULT_REQUIRED_SLOTS = ["duration", "severity", "description"]

SLOT_DEFINITIONS = {
    "symptom": {
        "key": "symptom",
        "question": "What is your primary symptom?",
        "pattern": None,
    },
    "duration": {
        "key": "duration",
        "question": "How long have you been experiencing this? (e.g. '2 hours', '3 days')",
        "pattern": r"\d+\s*(?:hour|day|week|month)s?",
    },
    "severity": {
        "key": "severity",
        "question": "On a scale of 1–10 (or mild/moderate/severe), how severe is your discomfort?",
        "pattern": r"\b([1-9]|10|mild|moderate|severe)\b",
    },
    "type": {
        "key": "type",
        "question": "Can you describe the type of pain? (e.g. throbbing, sharp, dull, pressure)",
        "pattern": None,
    },
    "associated_symptoms": {
        "key": "associated_symptoms",
        "question": "Are you experiencing any other symptoms? (e.g. nausea, dizziness, shortness of breath)",
        "pattern": None,
    },
    "description": {
        "key": "description",
        "question": "Can you provide more details about this symptom?",
        "pattern": None,
    }
}


class TriageAgent(BaseAgent):
    """
    Slot-filling triage agent that strictly enforces data collection before clinical guidance.
    """

    def __init__(self) -> None:
        super().__init__()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_initial_state(self) -> dict[str, Any]:
        """Initialize a fresh triage session state."""
        return {
            "stage": "ASK",
            "last_question": SLOT_DEFINITIONS["symptom"]["question"],
            "expected_slot": "symptom",
            "slots": {},
            "secondary_symptoms": []
        }

    def generate_next_step(
        self,
        user_input: str,
        history: list[dict[str, str]],
    ) -> dict[str, Any]:
        """
        Process the FIRST user message to start triage.
        """
        # 1. Identify symptom
        extracted = {}
        symptom_val = self._extract_value(user_input, SLOT_DEFINITIONS["symptom"]["pattern"])
        if symptom_val:
            extracted["symptom"] = symptom_val
            
            # 2. Once symptom is known, try to fill other slots from same input (only if patterns match)
            # This is NOT auto-fill; it's proactive extraction from the first message.
            # Step 5: "DO NOT assume values" - so we only take it if it matches the pattern.
            req_slots = self._get_required_slots(symptom_val)
            for slot_key in req_slots:
                if slot_key == "symptom":
                    continue
                pattern = SLOT_DEFINITIONS[slot_key].get("pattern")
                # For slots with no pattern (free text), we DON'T take it from the symptom line
                # unless it's clearly distinct, but to be safe and "strict", we'll only take
                # pattern-matched values in the first pass.
                if pattern:
                    val = self._extract_value(user_input, pattern)
                    if val and val.lower() != symptom_val.lower():
                        extracted[slot_key] = val

        missing = self._find_missing_slots(extracted)

        # DEBUG LOGS (Step 6)
        print(f"[Triage] Slots: {extracted}")
        print(f"[Triage] Missing: {missing}")
        print(f"[Triage] Stage: {'ASK' if missing else 'PROCEED'}")

        if missing:
            next_slot = missing[0]
            question = SLOT_DEFINITIONS[next_slot]["question"]
            return self._build_ask(question, extracted, next_slot)

        return self._build_proceed(extracted)

    def handle_followup(self, user_input: str, state: dict[str, Any]) -> dict[str, Any]:
        """
        Interpret user input as an answer to the last-asked question.
        (Step 3: Enforce ASK)
        """
        slot = state.get("expected_slot")
        if not slot:
            return self.generate_next_step(user_input, [])

        # 1. Fill the expected slot (Strict extraction)
        # For free-text slots (pattern is None), we take the whole input.
        # For pattern slots, we only take it if it matches.
        pattern = SLOT_DEFINITIONS[slot].get("pattern")
        value = self._extract_value(user_input, pattern)

        if value:
            # Step 5: Remove any default/guess logic. Just take the value.
            state["slots"][slot] = value
        
        # 2. Evaluate completeness
        missing = self._find_missing_slots(state["slots"])
        
        # DEBUG LOGS (Step 6)
        print(f"[Triage] Slots: {state['slots']}")
        print(f"[Triage] Missing: {missing}")

        if missing:
            next_slot = missing[0]
            question = SLOT_DEFINITIONS[next_slot]["question"]
            state["expected_slot"] = next_slot
            state["last_question"] = question
            print(f"[Triage] Stage: ASK")
            return self._build_ask(question, state["slots"], next_slot)

        # 3. All slots filled
        state["stage"] = "PROCEED"
        print(f"[Triage] Stage: PROCEED")
        return self._build_proceed(state["slots"])

    # ------------------------------------------------------------------
    # Internal Logic
    # ------------------------------------------------------------------

    def _get_required_slots(self, symptom: str) -> list[str]:
        """Determine which slots are required based on the patient's symptom."""
        if not symptom:
            return ["symptom"]
            
        symptom_upper = symptom.upper()
        # Step 1: Definition of symptoms
        for key, slots in REQUIRED_SLOTS_BY_SYMPTOM.items():
            if key in symptom_upper:
                return ["symptom"] + slots
        
        return ["symptom"] + DEFAULT_REQUIRED_SLOTS

    def _find_missing_slots(self, slots: dict[str, Any]) -> list[str]:
        """Step 2: Add Slot Validation."""
        symptom = slots.get("symptom")
        required = self._get_required_slots(symptom)
        
        missing_slots = []
        for slot in required:
            val = slots.get(slot)
            # Check if missing or empty
            if not val or (isinstance(val, str) and not val.strip()):
                missing_slots.append(slot)
        return missing_slots

    @staticmethod
    def _extract_value(text: str, pattern: str | None) -> str:
        """Helper to extract value from text based on pattern."""
        text = text.strip()
        if not text:
            return ""
        if pattern is None:
            return text
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0) if match else ""

    # ------------------------------------------------------------------
    # Response Builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_ask(question: str, extracted: dict[str, str], next_slot: str) -> dict[str, Any]:
        """Step 3: Enforce ASK."""
        return {
            "status": "ASK",
            "message": question,
            "meta": {
                "filled_slots": list(extracted.keys()),
                "expected_slot": next_slot,
            },
            "extracted_data": dict(extracted),
        }

    @staticmethod
    def _build_proceed(extracted: dict[str, str]) -> dict[str, Any]:
        """Step 4: ONLY THEN PROCEED."""
        return {
            "status": "PROCEED",
            "message": (
                "Thank you for providing those details. "
                "I am now analyzing your situation to provide clinical guidance."
            ),
            "meta": {
                **extracted,
                "filled_slots": list(extracted.keys()),
            },
            "extracted_data": dict(extracted),
        }
