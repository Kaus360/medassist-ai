from google import genai
from backend.config import settings

class GeminiClient:
    """Client for interacting seamlessly with the Gemini 1.5 language model."""
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        print("API KEY:", settings.gemini_api_key)

    def generate_response(self, prompt: str, system_prompt: str | None = None) -> str:
        """
        Securely contacts the API and returns the textual generation.
        Includes a clean fallback upon network or model failure.
        """
        try:
            # Combine if system prompt given, as Gemini generate_content takes 'contents'
            # Alternatively use system_instruction if setting up the model, but prepend is simpler for 'plain prompt' compatibility rule.
            # User specifically said: "If API uses plain prompt → prepend SAFETY_SYSTEM_PROMPT"
            full_contents = prompt
            if system_prompt:
                full_contents = f"System: {system_prompt}\n\nUser: {prompt}"

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_contents
            )
            return response.text
        except Exception as e:
            print(f"Gemini Error: {e}")
            return "Sorry, I am unable to process your request right now."
