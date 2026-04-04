"""
backend/conversation/memory.py

Persistent, file-backed memory store for MedAssist AI.
Tracks per-user symptom history across sessions and exposes
utilities for recurrence detection and context enrichment.

Design principles:
- Single responsibility: storage + retrieval only, no clinical logic
- Append-only writes: history is never overwritten
- Thread-safe at the file level via atomic JSON flush
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Default storage path – sits inside the project, outside the package tree
# so it is never accidentally imported or linted.
# ---------------------------------------------------------------------------
_DEFAULT_STORE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "memory_store.json"


class MemoryManager:
    """
    Manages persistent user interaction history and active session states for clinical triage.

    Storage Format (JSON):
    {
        "history": {
            "<user_id>": [
                {
                    "session_id": "...",
                    "symptom": "...",
                    "extracted_data": {...},
                    "timestamp": "ISO-8601"
                },
                ...
            ]
        },
        "active_sessions": {
            "<session_id>": {
                "user_id": "...",
                "stage": "ASK" | "PROCEED",
                "last_question": "...",
                "expected_slot": "...",
                "slots": {...},
                "last_updated": "ISO-8601"
            }
        }
    }
    """

    def __init__(self, store_path: Path | str | None = None) -> None:
        self._store_path = Path(store_path) if store_path else _DEFAULT_STORE_PATH
        self._store: dict[str, Any] = {
            "history": {},
            "active_sessions": {}
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize_storage(self) -> None:
        """
        Ensure the storage file and parent directories exist.
        Loads existing data into memory.  Safe to call multiple times.
        """
        self._store_path.parent.mkdir(parents=True, exist_ok=True)

        if self._store_path.exists():
            try:
                with open(self._store_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    # Support legacy format (where root was the history dict)
                    if "history" not in data:
                        self._store = {"history": data, "active_sessions": {}}
                    else:
                        self._store = data
            except (json.JSONDecodeError, OSError):
                # Corrupt or empty file – start fresh without crashing
                self._store = {"history": {}, "active_sessions": {}}
        else:
            self._store = {"history": {}, "active_sessions": {}}
            self._flush()

    # ------------------------------------------------------------------
    # Active Session Management
    # ------------------------------------------------------------------

    def get_active_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve the state of an active triage session."""
        return self._store.get("active_sessions", {}).get(session_id)

    def save_active_session(self, session_id: str, state: dict[str, Any]) -> None:
        """Update or create an active triage session state."""
        if "active_sessions" not in self._store:
            self._store["active_sessions"] = {}
        
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._store["active_sessions"][session_id] = state
        self._flush()

    def clear_active_session(self, session_id: str) -> None:
        """Remove a session from active storage once triage is completed."""
        if session_id in self._store.get("active_sessions", {}):
            del self._store["active_sessions"][session_id]
            self._flush()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save_interaction(
        self,
        user_id: str,
        session_id: str,
        symptom: str,
        extracted_data: dict[str, Any] | None = None,
    ) -> None:
        """
        Append a completed triage interaction to the user's history.

        Only call this when triage status == "PROCEED".
        Never overwrites existing records – always appends.

        Args:
            user_id:        Stable user identifier (e.g. "default_user").
            session_id:     UUID for the current consultation.
            symptom:        Primary symptom extracted by TriageAgent.
            extracted_data: Slot data collected during triage (optional).
        """
        record: dict[str, Any] = {
            "session_id": session_id,
            "symptom": symptom.strip().lower(),
            "extracted_data": extracted_data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if user_id not in self._store["history"]:
            self._store["history"][user_id] = []

        self._store["history"][user_id].append(record)
        self._flush()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_user_history(self, user_id: str) -> list[dict[str, Any]]:
        """
        Return the full interaction history for a given user.

        Returns an empty list if the user has no recorded interactions.
        """
        return list(self._store.get("history", {}).get(user_id, []))

    # ------------------------------------------------------------------
    # Derived queries
    # ------------------------------------------------------------------

    def detect_recurrence(self, user_id: str, symptom: str) -> bool:
        """
        Return True if the user has previously reported the same symptom.

        Comparison is case-insensitive and strip-normalised.
        """
        normalised = symptom.strip().lower()
        history = self.get_user_history(user_id)
        return any(record.get("symptom") == normalised for record in history)

    def enrich_context(self, user_id: str, symptom: str) -> str:
        """
        Build a plain-English context hint for LLM prompt augmentation.

        Returns an empty string when no relevant history exists so the caller
        can skip injecting any context block.
        """
        if not self.detect_recurrence(user_id, symptom):
            return ""

        history = self.get_user_history(user_id)
        prior = [r for r in history if r.get("symptom") == symptom.strip().lower()]
        count = len(prior)
        last_ts = prior[-1].get("timestamp", "")

        if last_ts:
            try:
                dt = datetime.fromisoformat(last_ts)
                last_seen = dt.strftime("%B %d, %Y")
            except ValueError:
                last_seen = last_ts
        else:
            last_seen = "a previous session"

        noun = "time" if count == 1 else "times"
        return (
            f"[Clinical Context] This user has previously reported '{symptom}' "
            f"{count} {noun} (most recently on {last_seen}). "
            f"Consider possible recurrence or chronic pattern."
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _flush(self) -> None:
        """Write the in-memory store to disk atomically."""
        tmp_path = self._store_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(self._store, fh, indent=2, ensure_ascii=False)
        # Atomic replace – avoids corrupt reads on crash mid-write
        os.replace(tmp_path, self._store_path)
