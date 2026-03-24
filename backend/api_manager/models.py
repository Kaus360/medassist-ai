import time
from dataclasses import dataclass

@dataclass
class APIState:
    """Model representing the health and routing state of an external API."""
    name: str
    priority: int
    is_active: bool = True
    last_failure_time: float | None = None
    cooldown_seconds: int = 5
    success_count: int = 0
    failure_count: int = 0

    def mark_failure(self) -> None:
        """Marks the API as failed, triggering cooldown."""
        self.is_active = False
        self.last_failure_time = time.time()
        self.failure_count += 1

    def mark_success(self) -> None:
        """Marks the API as successful and sets to active."""
        self.is_active = True
        self.success_count += 1

    def can_retry(self, current_time: float) -> bool:
        """Determines if the cooldown has elapsed to allow retrying the API."""
        if self.is_active:
            return True
            
        if self.last_failure_time is None:
            return True
            
        return (current_time - self.last_failure_time) >= self.cooldown_seconds
