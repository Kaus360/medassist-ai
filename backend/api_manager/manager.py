import time
from typing import List, Optional

from backend.config import settings
from backend.api_manager.models import APIState

class APIManager:
    """Core manager allocating API requests via health tracking and priority."""

    def __init__(self):
        cooldown = settings.cooldown_seconds
        
        # Maintain internal dictionary of strictly typed APIState configurations
        self.apis = {
            "gemini": APIState(name="gemini", priority=1, cooldown_seconds=cooldown),
            "groq": APIState(name="groq", priority=2, cooldown_seconds=cooldown),
            "openrouter": APIState(name="openrouter", priority=3, cooldown_seconds=cooldown),
        }

    def get_available_apis(self) -> List[APIState]:
        """Returns fundamentally active APIs sorted purely by priority."""
        active = [api for api in self.apis.values() if api.is_active]
        return sorted(active, key=lambda a: a.priority)

    def mark_failure(self, api_name: str) -> None:
        """Marks the specified API as failed and immediately kicks off its cooldown."""
        if api_name in self.apis:
            self.apis[api_name].mark_failure()

    def mark_success(self, api_name: str) -> None:
        """Marks the specified API as fully successful and instantly restores activity."""
        if api_name in self.apis:
            self.apis[api_name].mark_success()

    def get_next_api(self) -> Optional[APIState]:
        """
        Returns the highest priority API that is active OR completely eligible for retry.
        """
        current_time = time.time()
        
        # .can_retry() evaluates True for purely active APIs AND elapsed inactive APIs.
        eligible_apis = [
            api for api in self.apis.values() 
            if api.can_retry(current_time)
        ]
        
        if not eligible_apis:
            return None
            
        # Sort by hierarchical priority ascending (1 = highest urgency)
        eligible_apis.sort(key=lambda a: a.priority)
        
        return eligible_apis[0]

    def recover_apis(self) -> None:
        """
        Scans inactive APIs and reactivates those whose cooldown period has passed.
        Currently invoked manually without threading, ensuring safe, explicit state updates.
        """
        current_time = time.time()
        for api in self.apis.values():
            # Check specifically for inactive APIs where the timeout has expired
            if not api.is_active and api.can_retry(current_time):
                api.is_active = True

    def _execute_api_call(self, api_name: str, prompt: str) -> str:
        """
        Internal modular method to execute the actual external API call.
        Structured this way so real async logic can be seamlessly plugged in later.
        """
        # Simulating external API logic returning the mock response
        return f"Response from {api_name}"

    def execute_with_failover(self, prompt: str) -> str:
        """
        Executes the prompt against configured APIs, dynamically navigating failures.
        """
        current_time = time.time()
        
        # Loop through APIs sorted exactly by priority
        # we strictly filter down to `active` and eligible API states to loop through
        eligible_apis = [
            api for api in self.apis.values() 
            if api.can_retry(current_time)
        ]
        eligible_apis.sort(key=lambda a: a.priority)

        for api in eligible_apis:
            try:
                # Pluggable modular API execution block 
                response = self._execute_api_call(api.name, prompt)
                
                # Upon completion, mark success and return
                self.mark_success(api.name)
                return response
                
            except Exception as e:
                # On simulated execution failure, neatly flag state and proceed to next priority item
                self.mark_failure(api.name)
                continue
                
        # If the complete cascade is thoroughly exhausted
        return "Fallback: All properly configured API models failed or are on cooldown."
