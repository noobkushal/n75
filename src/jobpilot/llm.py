from __future__ import annotations

import json
import os
from typing import Any, TypeVar

import requests
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """Raised when the configured LLM cannot provide a valid JSON response."""


class LLMClient:
    """Provider-agnostic LLM adapter for Gemini, Groq, and Ollama."""

    def __init__(
        self,
        *,
        provider: str = "gemini",
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.2,
        timeout: int = 60,
    ) -> None:
        self.provider = (provider or "gemini").lower()
        self.model = model or self._default_model()
        self.api_key = api_key or os.getenv(self._env_var_name(), "")
        self.base_url = base_url
        self.temperature = temperature
        self.timeout = timeout

    def _env_var_name(self) -> str:
        mapping = {
            "gemini": "GEMINI_API_KEY",
            "groq": "GROQ_API_KEY",
            "ollama": "OLLAMA_API_KEY",
        }
        return mapping.get(self.provider, "GEMINI_API_KEY")

    def _default_model(self) -> str:
        defaults = {
            "gemini": "gemini-2.0-flash",
            "groq": "llama-3.3-70b-versatile",
            "ollama": "llama3.2",
        }
        return defaults.get(self.provider, "gemini-2.0-flash")

    @retry(
        retry=retry_if_exception_type((LLMError, requests.RequestException)),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def generate_json(
        self,
        prompt: str,
        response_model: type[T],
        *,
        system_prompt: str | None = None,
    ) -> T:
        """Send a prompt to the selected provider and validate the returned JSON."""

        payload = self._build_request(prompt, system_prompt=system_prompt)
        response = self._request(payload)
        text = self._extract_text(response)
        parsed = self._parse_json_payload(text)
        return response_model.model_validate(parsed)

    def _build_request(self, prompt: str, *, system_prompt: str | None = None) -> dict[str, Any]:
        if self.provider == "gemini":
            full_prompt = prompt if system_prompt is None else f"{system_prompt}\n\n{prompt}"
            return {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {
                    "temperature": self.temperature,
                    "response_mime_type": "application/json",
                },
            }

        if self.provider == "groq":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            return {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "response_format": {"type": "json_object"},
            }

        if self.provider == "ollama":
            return {
                "model": self.model,
                "prompt": prompt if system_prompt is None else f"{system_prompt}\n\n{prompt}",
                "stream": False,
                "format": "json",
            }

        raise LLMError(f"Unsupported LLM provider: {self.provider}")

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.provider == "gemini":
            if not self.api_key:
                raise LLMError("GEMINI_API_KEY is not configured.")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        if self.provider == "groq":
            if not self.api_key:
                raise LLMError("GROQ_API_KEY is not configured.")
            url = "https://api.groq.com/openai/v1/chat/completions"
            response = requests.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        if self.provider == "ollama":
            url = self.base_url or "http://localhost:11434/api/generate"
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        raise LLMError(f"Unsupported LLM provider: {self.provider}")

    def _extract_text(self, response: dict[str, Any]) -> str:
        if self.provider == "gemini":
            try:
                return response["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError, TypeError) as exc:
                raise LLMError("Gemini response did not contain textual content.") from exc

        if self.provider == "groq":
            try:
                return response["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as exc:
                raise LLMError("Groq response did not contain textual content.") from exc

        if self.provider == "ollama":
            try:
                return response["response"]
            except KeyError as exc:
                raise LLMError("Ollama response did not contain textual content.") from exc

        raise LLMError(f"Unsupported LLM provider: {self.provider}")

    def _parse_json_payload(self, raw_text: str) -> dict[str, Any]:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`\n ")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
            raise LLMError("LLM output was valid JSON but not an object.")
        except json.JSONDecodeError as exc:
            raise LLMError(f"LLM response was not valid JSON: {raw_text[:200]}") from exc
