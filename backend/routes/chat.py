from fastapi import APIRouter
from backend.api_manager.manager import APIManager

router = APIRouter()

# Initialize globally for temporary testing purposes
api_manager = APIManager()

@router.post("/chat")
def chat_endpoint():
    """Temporary testing endpoint for APIManager failover logic."""
    response = api_manager.execute_with_failover("test prompt")
    return {"message": response}
