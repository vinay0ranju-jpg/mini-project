"""
LLM Client module.
Provides a unified, resilient interface to Gemini or other LLM providers with
prompt sandboxing and graceful local fallback when API keys are absent.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
try:
    from ..config import Config
except (ImportError, ValueError):
    from config import Config


logger = logging.getLogger(__name__)


class LLMClient:
    """Interacts with external LLM APIs safely."""

    def __init__(self):
        self.provider = Config.LLM_PROVIDER
        self.api_key = Config.LLM_API_KEY
        self.model = Config.LLM_MODEL

    def is_configured(self) -> bool:
        """Checks if an API key has been configured."""
        return bool(self.api_key and self.provider != "none")

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        """
        Sends a completion request to the configured LLM provider.
        Returns text response or None on failure or missing credentials.
        """
        if not self.is_configured():
            return None

        # Sanitize prompt against delimiter injection
        safe_prompt = prompt.replace("```json", "").replace("```", "")

        if self.provider == "gemini":
            return self._call_gemini(safe_prompt, system_instruction)
        elif self.provider == "openai":
            return self._call_openai(safe_prompt, system_instruction)
        else:
            return None

    def _call_gemini(self, prompt: str, system_instruction: Optional[str]) -> Optional[str]:
        """Calls Google Gemini API using google-genai or direct requests."""
        try:
            # Try official google.genai or google.generativeai
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model_instance = genai.GenerativeModel(
                model_name=self.model,
                system_instruction=system_instruction,
            )
            response = model_instance.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except ImportError:
            # Fallback to direct REST API if package is not yet imported
            return self._call_gemini_rest(prompt, system_instruction)
        except Exception as e:
            logger.warning(f"Gemini SDK generation failed: {e}. Falling back to deterministic engine.")
            return None

    def _call_gemini_rest(self, prompt: str, system_instruction: Optional[str]) -> Optional[str]:
        """Direct REST fallback for Gemini API."""
        try:
            import requests
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
            }
            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip()
            else:
                logger.warning(f"Gemini REST returned HTTP {resp.status_code}: {resp.text}")
                return None
        except Exception as e:
            logger.warning(f"Gemini REST call failed: {e}")
            return None

    def _call_openai(self, prompt: str, system_instruction: Optional[str]) -> Optional[str]:
        """Calls OpenAI API using standard requests."""
        try:
            import requests
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model or "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.2,
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            return None
        except Exception as e:
            logger.warning(f"OpenAI call failed: {e}")
            return None
