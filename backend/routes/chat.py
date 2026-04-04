"""
backend/routes/chat.py

MedAssist AI – primary chat endpoint.

CRITICAL SAFETY ENFORCEMENT
---------------------------
ALL outgoing responses MUST pass through build_safe_response().
This ensures that every message—whether from the LLM, the Triage agent, 
or an error handler—is sanitized and includes the mandatory disclaimer.
DO NOT return raw text directly to the client.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from backend.api_manager.manager import APIManager
from backend.agents.triage_agent import TriageAgent
from backend.conversation.memory import MemoryManager
from backend.services.safety_filter import SafetyFilter

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter()

# Initialize singletons
api_manager = APIManager()
triage_agent = TriageAgent()
memory_manager = MemoryManager()
safety_filter = SafetyFilter()

memory_manager.initialize_storage()

def build_safe_response(raw_text: str, user_input: str = "N/A") -> dict:
    """
    Mandatory safety wrapper for all outgoing text.
    Enforces sanitization, neutralizes authority claims, and appends disclaimer.
    Now returns a dict with 'response' and 'safety' metadata.
    """
    if not isinstance(raw_text, str):
        raw_text = str(raw_text)

    # 1. Apply SafetyFilter pipeline
    result = safety_filter.process(raw_text, user_input=user_input)
    safe_text = result["text"]
    flags = result["flags"]
    safety_action = result["safety_action"]

    # 2. Add safety metadata (risk level logic)
    # if has_dosage or has_prescription -> "high"
    # elif has_medical_claim -> "medium"
    # else -> "low"
    if flags.get("has_dosage") or flags.get("has_prescription"):
        risk_level = "high"
    elif flags.get("has_medical_claim"):
        risk_level = "medium"
    else:
        risk_level = "low"

    # [Fail-safe] Ensure disclaimer is present in every outgoing message
    assert "not a substitute for professional medical advice" in safe_text.lower(), \
        "SAFETY VIOLATION: Mandatory medical disclaimer missing from response."
    
    print(f"[Safety Enforcement] Output sanitized ({safety_action}) and disclaimer verified. Risk: {risk_level}")
    
    return {
        "response": safe_text,
        "safety": {
            "filtered": (safety_action != "none"),
            "action": safety_action,
            "risk_level": risk_level
        }
    }


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


class SafetyMetadata(BaseModel):
    """Metadata regarding safety filtering and risk level."""
    filtered: bool
    action: str
    risk_level: str

class ChatResponse(BaseModel):
    """Typed response returned by the /chat endpoint."""
    response: str
    status: str          # "ASK" | "PROCEED"
    session_id: str
    recurrence: bool = False
    safety: SafetyMetadata


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

    # ── STEP 1: Fetch user history and active state ──────────────────────
    user_id = "default_user"  # Future: derive from authenticated session
    session_id = request.session_id or str(uuid.uuid4())

    active_session = memory_manager.get_active_session(session_id)
    user_history = memory_manager.get_user_history(user_id)

    # ── STEP 2: Unified Triage Logic ────────────────────────────────────
    if active_session and active_session.get("stage") == "ASK":
        # FOLLOW-UP MODE: Bypass classification
        print(f"[Routing] Mode: FOLLOWUP (Expected Slot: {active_session.get('expected_slot')})")
        triage_response = triage_agent.handle_followup(
            user_input=request.message,
            state=active_session
        )
    else:
        # NEW MODE: Perform initial symptom detection
        print(f"[Routing] Mode: NEW")
        triage_response = triage_agent.generate_next_step(
            user_input=request.message,
            history=request.history,
        )
        if triage_response["status"] == "ASK":
            active_session = {
                "user_id": user_id,
                "stage": "ASK",
                "last_question": triage_response["message"],
                "expected_slot": triage_response["meta"].get("expected_slot"),
                "slots": triage_response["extracted_data"],
            }

    # ── STEP 3: TRIAGE GATING (CRITICAL) ────────────────────────────────
    # IF triage is incomplete, return follow-up question IMMEDIATELY (Step 2)
    if triage_response["status"] == "ASK":
        print("[Triage] Status: ASK (Gating LLM call)")
        memory_manager.save_active_session(session_id, active_session)
        safe_package = build_safe_response(triage_response["message"], user_input=request.message)
        return ChatResponse(
            response=safe_package["response"],
            safety=safe_package["safety"],
            status="ASK",
            session_id=session_id,
            recurrence=False,
        )

    # ── STEP 4 (PROCEED): Only reached if triage_status == "PROCEED" ─────
    print("[Triage] Status: PROCEED (Enabling LLM diagnostics)")
    
    # 1. Finalize metadata
    memory_manager.clear_active_session(session_id)
    meta = triage_response.get("meta", {})
    if active_session and "secondary_symptoms" in active_session:
        meta["secondary_symptoms"] = active_session["secondary_symptoms"]

    symptom = meta.get("symptom", request.message)
    extracted_data = triage_response.get("extracted_data", {})

    # 2. Persist history
    memory_manager.save_interaction(
        user_id=user_id,
        session_id=session_id,
        symptom=symptom,
        extracted_data=extracted_data,
    )

    # 3. Detect recurrence
    recurrence = any(
        record.get("symptom") == symptom.strip().lower()
        for record in user_history
    )

    # 4. Enrich and Call LLM
    context_hint = memory_manager.enrich_context(user_id, symptom)
    final_prompt = _build_prompt(
        user_input=request.message,
        triage_meta=meta,
        context_hint=context_hint,
    )

    try:
        llm_response = api_manager.execute_with_failover(final_prompt)
    except Exception as e:
        print(f"[Chat Error] LLM Failure: {e}")
        llm_response = "I encountered an error while formulating clinical guidance. Please try again."

    # ── STEP 5: Final Safety Check & Return ──────────────────────────────
    safe_package = build_safe_response(llm_response, user_input=request.message)
    return ChatResponse(
        response=safe_package["response"],
        safety=safe_package["safety"],
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
    secondary = triage_meta.get("secondary_symptoms", [])

    triage_block = (
        f"Symptom: {symptom}\n"
        f"Duration: {duration}\n"
        f"Severity (1-10): {severity}\n"
        f"Temperature: {temperature}"
    )
    if secondary:
        secondary_str = ", ".join(secondary)
        triage_block += f"\nSecondary Symptoms: {secondary_str}"

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
