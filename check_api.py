import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from backend.api_manager.manager import APIManager
from dotenv import load_dotenv

load_dotenv()

def test_api_manager():
    manager = APIManager()
    prompt = "Test prompt for clinical guidance regarding chest pain."
    try:
        print("Starting execute_with_failover...")
        response = manager.execute_with_failover(prompt)
        print("Response received:")
        print(response)
    except Exception as e:
        print(f"Exception caught in test script: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_manager()
