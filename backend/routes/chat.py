"""
backend/routes/chat.py

MedAssist AI – primary chat endpoint.

Integration flow (per request):
  1. Receive input + optional session_id
  2. Fetch user history from MemoryManager
  3. Run TriageAgent to resolve ASK / PROCEED state
  4. IF ASK  → return immediately (no memory write)
  5. IF PROCEED:
       a. Save interaction to memory (append-only)
       b. Detect symptom recurrence
       c. Enrich LLM prompt with clinical context
       d. Call APIManager.execute_with_failover(final_prompt)
  6. Return structured response to client
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from backend.api_manager.manager import APIManager
from backend.agents.triage_agent import TriageAgent
from backend.conversation.memory import MemoryManager

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter()

# ---------------------------------------------------------------------------
# Module-level singletons – initialised once at import time so that the
# startup event wires up storage exactly once.
# ---------------------------------------------------------------------------
api_manager = APIManager()
triage_agent = TriageAgent()
memory_manager = MemoryManager()

# Initialize persistent storage on module load (idempotent)
memory_manager.initialize_storage()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """
    JSON payload schema for the /chat endpoint.

    Fields:
        message:    The user's current message.
        history:    Accumulated conversation turns (role + content pairs).
                    The frontend is responsible for maintaining and sending this.
        session_id: Optional UUID for the current consultation.
                    A new UUID is generated server-side when absent.
    """
    message: str
    history: list[dict[str, str]] = []
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Typed response returned by the /chat endpoint."""
    response: str
    status: str          # "ASK" | "PROCEED"
    session_id: str
    recurrence: bool = False


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Unified context-aware clinical triage + LLM endpoint.

    Stages:
        BEFORE TRIAGE  → Fetch user memory history
        TRIAGE         → TriageAgent determines ASK / PROCEED
        IF ASK         → Return follow-up question (no memory write)
        IF PROCEED     → Save interaction, detect recurrence,
                         enrich prompt, call LLM
    """

    # ── Stable identifiers ──────────────────────────────────────────────
    user_id = "default_user"  # Future: derive from authenticated session
    session_id = request.session_id or str(uuid.uuid4())

    # ── STEP 1: Fetch user history ───────────────────────────────────────
    user_history = memory_manager.get_user_history(user_id)

    # ── STEP 2: Run triage (stateless) ──────────────────────────────────
    triage_response = triage_agent.generate_next_step(
        user_input=request.message,
        history=request.history,
    )

    triage_status: str = triage_response["status"]

    # ── STEP 3: Return early if more information is needed ───────────────
    if triage_status == "ASK":
        return ChatResponse(
            response=triage_response["message"],
            status="ASK",
            session_id=session_id,
            recurrence=False,
        )

    # ── STEP 4 (PROCEED): Extract metadata ──────────────────────────────
    symptom: str = triage_response["meta"].get("symptom", request.message)
    extracted_data: dict = triage_response.get("extracted_data", {})

    # ── STEP 5: Persist interaction (append-only, never overwrite) ───────
    memory_manager.save_interaction(
        user_id=user_id,
        session_id=session_id,
        symptom=symptom,
        extracted_data=extracted_data,
    )

    # ── STEP 6: Detect recurrence ────────────────────────────────────────
    # Recurrence check runs AFTER saving so the current session is excluded
    # from the detection window (history loaded before save).
    recurrence: bool = any(
        record.get("symptom") == symptom.strip().lower()
        for record in user_history  # loaded before this session's save
    )

    # ── STEP 7: Enrich LLM prompt with clinical context ─────────────────
    context_hint: str = memory_manager.enrich_context(user_id, symptom)

    final_prompt = _build_prompt(
        user_input=request.message,
        triage_meta=triage_response["meta"],
        context_hint=context_hint,
    )

    # ── STEP 8: Call LLM via failover chain ─────────────────────────────
    llm_response: str = api_manager.execute_with_failover(final_prompt)

    return ChatResponse(
        response=llm_response,
        status="PROCEED",
        session_id=session_id,
        recurrence=recurrence,
    )


# ---------------------------------------------------------------------------
# Prompt builder (pure function – easy to unit-test in isolation)
# ---------------------------------------------------------------------------

def _build_prompt(
    user_input: str,
    triage_meta: dict,
    context_hint: str,
) -> str:
    """
    Compose the final LLM prompt from triage metadata and optional context.

    Rules:
    - context_hint is only injected when non-empty (no clutter)
    - Triage metadata is always included for structured clinical reasoning
    """
    symptom = triage_meta.get("symptom", "")
    duration = triage_meta.get("duration", "not specified")
    severity = triage_meta.get("severity", "not specified")
    temperature = triage_meta.get("temperature", "not specified")

    triage_block = (
        f"Symptom: {symptom}\n"
        f"Duration: {duration}\n"
        f"Severity (1-10): {severity}\n"
        f"Temperature: {temperature}"
    )

    parts: list[str] = []

    if context_hint:
        parts.append(context_hint)

    parts.append(
        f"Patient Triage Summary:\n{triage_block}\n\n"
        f"Patient Message:\n{user_input}\n\n"
        f"Provide structured clinical guidance. Include: possible differential diagnoses, "
        f"recommended next steps, red-flag symptoms to watch for, and when to seek "
        f"emergency care. Use plain language suitable for a patient."
    )

    return "\n\n".join(parts)
