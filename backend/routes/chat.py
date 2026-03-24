from fastapi import APIRouter
from pydantic import BaseModel
from backend.api_manager.manager import APIManager

router = APIRouter()

# Initialize globally for failover routing execution
api_manager = APIManager()

class ChatRequest(BaseModel):
    """Schema enforcing JSON payloads with a required 'message' string."""
    message: str

@router.post("/chat")
def chat_endpoint(request: ChatRequest):
    """Accepts a chat prompt and securely executes it across fallback APIs."""
    # Pass the validated payload directly into failover handling
    result = api_manager.execute_with_failover(request.message)
    return {"response": result}
