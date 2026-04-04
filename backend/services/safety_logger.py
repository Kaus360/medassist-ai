import json
import os
from datetime import datetime

class SafetyLogger:
    """
    Module for auditing safety behavior by logging LLM inputs, raw outputs,
    safety flags, and final sanitized responses.
    """
    
    LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "safety_logs.json")

    @staticmethod
    def log_event(data: dict):
        """
        Logs a safety event. Wraps in silent try/except to ensure primary flow
        is never interrupted.
        """
        try:
            # Ensure the logs directory exists
            os.makedirs(os.path.dirname(SafetyLogger.LOG_FILE), exist_ok=True)
            
            # Prepare the log entry with a timestamp
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                **data
            }
            
            # Read existing logs or start new array
            logs = []
            if os.path.exists(SafetyLogger.LOG_FILE):
                try:
                    with open(SafetyLogger.LOG_FILE, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            logs = json.loads(content)
                except (json.JSONDecodeError, IOError):
                    # If file is corrupt or unreadable, start fresh
                    logs = []
            
            # Append and write back
            logs.append(log_entry)
            
            with open(SafetyLogger.LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2)
                
        except Exception:
            # Silent fail to prevent breaking the system as per requirements
            pass
