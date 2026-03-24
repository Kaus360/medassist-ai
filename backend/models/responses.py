from pydantic import BaseModel

class GenericResponse(BaseModel):
    """Placeholder class grouping generic response schemas."""
    success: bool
    data: dict | None = None
    error: str | None = None
