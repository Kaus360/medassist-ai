from google import genai
from backend.config import settings

class GeminiClient:
    """Client for interacting seamlessly with the Gemini 1.5 language model."""
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        print("API KEY:", settings.gemini_api_key)

    def generate_response(self, prompt: str) -> str:
        """
        Securely contacts the API and returns the textual generation.
        Includes a clean fallback upon network or model failure.
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Gemini Error: {e}")
            return "Sorry, I am unable to process your request right now."
