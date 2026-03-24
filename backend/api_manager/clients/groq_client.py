from groq import Groq
from backend.config import settings

class GroqClient:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)

    def generate_response(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant"
            )
            print("=== GROQ RESPONSE ===")
            print(response)
            print("====================")
            return response.choices[0].message.content
        except Exception as e:
            print("Groq Error:", e)
            raise Exception("Groq failed")
