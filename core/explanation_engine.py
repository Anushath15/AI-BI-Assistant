import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class ClaudeClient:
    """
    Handles communication with Claude API.
    """

    def __init__(self):

        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in .env")

        self.client = Anthropic(api_key=api_key)

    def ask(self, prompt):

        try:

            response = self.client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1024,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return response.content[0].text

        except Exception as e:

            return json.dumps({
                "error": str(e)
            })