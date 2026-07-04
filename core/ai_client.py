import os
from groq import Groq

from utils.logger import get_logger
logger = get_logger(__name__)


class AIClient:

    def __init__(self):
        api_key = None

        try:
            import streamlit as st
            api_key = st.secrets.get("GROQ_API_KEY")
        except Exception:
            pass

        if not api_key:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY not found in secrets or .env")

        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def ask(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.exception("AIClient request failed")
            raise