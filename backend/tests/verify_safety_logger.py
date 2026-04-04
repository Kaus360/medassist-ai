
import sys
import os
import json

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.safety_filter import SafetyFilter

def verify_logging():
    print("Verifying SafetyLogger integration...")
    
    filter = SafetyFilter()
    
    # Simulate a message that should trigger safety flags
    test_user_input = "Suggest aspirin dosage"
    test_llm_output = "You should take 500mg of aspirin every 4 hours."
    
    print(f"Processing test input: {test_user_input}")
    result = filter.process(test_llm_output, user_input=test_user_input)
    safe_output = result["text"]
    safety_action = result["safety_action"]
    
    print(f"\nSafe Output obtained (Action: {safety_action}):")
    print(safe_output)
    
    # Check if log file exists
    log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs", "safety_logs.json"))
    print(f"\nChecking for log file at: {log_path}")
    
    if os.path.exists(log_path):
        print("Log file found!")
        with open(log_path, "r") as f:
            logs = json.load(f)
            print(f"Number of log entries: {len(logs)}")
            if len(logs) > 0:
                last_log = logs[-1]
                print("\nLast log entry:")
                print(json.dumps(last_log, indent=2))
    else:
        print("Log file NOT found. Integration failed.")

if __name__ == "__main__":
    verify_logging()
