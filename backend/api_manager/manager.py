import time
from typing import List, Optional

from backend.config import settings
from backend.api_manager.models import APIState
from backend.api_manager.clients.gemini_client import GeminiClient
from backend.api_manager.clients.groq_client import GroqClient
from backend.safety.prompts import SAFETY_SYSTEM_PROMPT

class APIManager:
    """Core manager allocating API requests via health tracking and priority."""

    def __init__(self):
        cooldown = settings.cooldown_seconds
        
        # Maintain internal dictionary of strictly typed APIState configurations
        self.apis = {
            "gemini": APIState(name="gemini", priority=1, is_active=True, cooldown_seconds=60),
            "groq": APIState(name="groq", priority=2, is_active=True, cooldown_seconds=60),
            "openrouter": APIState(name="openrouter", priority=3, is_active=True, cooldown_seconds=60)
        }
        self.gemini_client = GeminiClient()
        self.groq_client = GroqClient()

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
        if api_name == "gemini":
            response = self.gemini_client.generate_response(prompt)
            if response == "Sorry, I am unable to process your request right now.":
                raise Exception("Gemini API failure detected during execution")
            return response
            
        # Simulating external API logic returning the mock response
        return f"Response from {api_name}"

    def execute_with_failover(self, prompt: str) -> str:
        """
        Executes the prompt against configured APIs, dynamically navigating failures.
        """
        eligible_apis = sorted(self.apis.values(), key=lambda x: x.priority)

        for api in eligible_apis:
            try:
                print(f"Trying API: {api.name}")
                
                if api.name == "gemini":
                    response = self.gemini_client.generate_response(prompt, system_prompt=SAFETY_SYSTEM_PROMPT)
                    if "unable to process" in response.lower():
                        raise Exception("Gemini returned fallback response")
                elif api.name == "groq":
                    response = self.groq_client.generate_response(prompt, system_prompt=SAFETY_SYSTEM_PROMPT)
                    if "failed" in response.lower():
                        raise Exception("Groq failed")
                elif api.name == "openrouter":
                    response = "Response from openrouter"
                else:
                    raise Exception(f"Unknown API: {api.name}")
                
                print(f"Success from: {api.name}")
                # Upon completion, mark success and return
                self.mark_success(api.name)
                return response
                
            except Exception as e:
                print(f"Failed: {api.name} → {e}")
                # On simulated execution failure, neatly flag state and proceed to next priority item
                self.mark_failure(api.name)
                continue
                
        # If the complete cascade is thoroughly exhausted
        return "Fallback: All properly configured API models failed or are on cooldown."
# -*- coding: utf-8 -*-

import time
from typing import List

from backend.config import settings
from backend.api_manager.models import APIState
from backend.api_manager.clients.gemini_client import GeminiClient
from backend.api_manager.clients.groq_client import GroqClient
from backend.safety.prompts import SAFETY_SYSTEM_PROMPT


class APIManager:
    """
    Production-grade API Manager with:
    - Failover
    - Cooldown handling
    - Auto recovery
    - Priority rebalancing
    """

    def __init__(self):
        cooldown = settings.cooldown_seconds

        self.apis = {
            "gemini": APIState("gemini", priority=1, is_active=True, cooldown_seconds=cooldown),
            "groq": APIState("groq", priority=2, is_active=True, cooldown_seconds=cooldown),
            "openrouter": APIState("openrouter", priority=3, is_active=True, cooldown_seconds=cooldown),
        }

        self.gemini_client = GeminiClient()
        self.groq_client = GroqClient()

    # =========================
    # STATE MANAGEMENT
    # =========================

    def mark_failure(self, api_name: str):
        if api_name in self.apis:
            print(f"[API STATE] {api_name} FAILED -> cooldown started")
            self.apis[api_name].mark_failure()

    def mark_success(self, api_name: str):
        if api_name in self.apis:
            print(f"[API STATE] {api_name} SUCCESS -> active")
            self.apis[api_name].mark_success()

    def recover_apis(self):
        """
        Reactivates APIs whose cooldown has expired.
        This enables automatic priority restoration.
        """
        current_time = time.time()

        for api in self.apis.values():
            if not api.is_active and api.can_retry(current_time):
                print(f"[API RECOVERY] {api.name} reactivated (quota likely restored)")
                api.is_active = True

    def get_available_apis(self) -> List[APIState]:
        """
        Returns ONLY active APIs sorted by priority.
        Ensures highest priority is always chosen.
        """
        active_apis = [
            api for api in self.apis.values()
            if api.is_active
        ]

        return sorted(active_apis, key=lambda a: a.priority)

    # =========================
    # API CALL LAYER
    # =========================

    def _call_api(self, api_name: str, prompt: str) -> str:
        if api_name == "gemini":
            return self.gemini_client.generate_response(
                prompt,
                system_prompt=SAFETY_SYSTEM_PROMPT
            )

        elif api_name == "groq":
            return self.groq_client.generate_response(
                prompt,
                system_prompt=SAFETY_SYSTEM_PROMPT
            )

        elif api_name == "openrouter":
            # Placeholder (implement later if needed)
            return "Response from openrouter"

        else:
            raise Exception(f"Unknown API: {api_name}")

    # =========================
    # FAILOVER ENGINE
    # =========================

    def execute_with_failover(self, prompt: str) -> str:
        """
        Executes request with:
        - strict priority
        - failover
        - auto recovery
        """

        # Step 1: Recover APIs (VERY IMPORTANT)
        self.recover_apis()

        # Step 2: Get active APIs ONLY
        available_apis = self.get_available_apis()

        if not available_apis:
            print("[FATAL] No APIs available")
            return self._fallback_response()

        # Step 3: Try APIs in strict priority order
        for api in available_apis:
            try:
                print(f"[API TRY] {api.name}")

                response = self._call_api(api.name, prompt)

                # Validate response
                if not response or len(response.strip()) == 0:
                    raise Exception("Empty response")

                if "unable to process" in response.lower():
                    raise Exception("Model returned fallback response")

                print(f"[API SUCCESS] {api.name}")
                self.mark_success(api.name)

                return response

            except Exception as e:
                error_msg = str(e)

                print(f"[API FAIL] {api.name}: {error_msg}")

                # Special handling for quota exhaustion
                if "429" in error_msg or "quota" in error_msg.lower():
                    print(f"[QUOTA] {api.name} quota exhausted")

                self.mark_failure(api.name)
                continue

        # Step 4: If ALL APIs fail
        print("[FAILOVER] All APIs failed")

        return self._fallback_response()

    # =========================
    # FALLBACK RESPONSE
    # =========================

    def _fallback_response(self) -> str:
        return """Summary:
I'm currently unable to generate detailed clinical guidance.

Possible Causes:
- Temporary system limitation
- API service unavailable

What You Can Do:
- Try again after some time
- Monitor your symptoms

Red Flags:
- Severe or worsening symptoms
- Difficulty breathing or chest pain

Next Step:
Please consult a healthcare professional for proper evaluation.

This system is not a substitute for professional medical advice."""