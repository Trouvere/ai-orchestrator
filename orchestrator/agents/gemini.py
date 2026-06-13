"""Адаптер Gemini (API-режим).

Модель не имеет доступа к файловой системе, поэтому обмен организован так:

1. Оркестратор сериализует реальные файлы workspace в промпт.
2. Gemini возвращает JSON-манифест: какие файлы создать/обновить/удалить
   и их полное содержимое (формат принудительно JSON через
   ``responseMimeType: application/json``).
3. Оркестратор материализует манифест обратно в реальные файлы.

Реализация использует REST-эндпоинт ``generateContent`` напрямую через
стандартную библиотеку — без внешних зависимостей. Ключ берётся из
``GEMINI_API_KEY`` (или ``GOOGLE_API_KEY``).
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from ..protocol import AgentResult, Status, parse_manifest
from .base import BaseAgent, StepContext, build_prompt

API_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

GEMINI_SYSTEM_PROMPT = """\
Ты — один из AI-агентов конвейера автоматической разработки. Оркестратор
передаёт тебе реальные файлы проекта в тексте запроса, а возвращённый тобой
манифест материализует обратно в файловую систему. Поэтому:
- работай аккуратно: всё, что ты вернёшь в "files", станет реальными файлами;
- возвращай полное содержимое файлов, а не фрагменты и не diff;
- не выдумывай файлы, которых не требует задача;
- учитывай историю шагов и замечания ревью из контекста.
"""

RETRYABLE_HTTP = {429, 500, 502, 503, 504}


class GeminiAgent(BaseAgent):
    mode = "api"

    def __init__(
        self,
        name: str = "gemini",
        model: str = "gemini-2.5-flash",
        api_key: str | None = None,
        temperature: float = 0.4,
        max_output_tokens: int = 65_536,
        timeout: int = 300,
        retries: int = 2,
        system_prompt: str = GEMINI_SYSTEM_PROMPT,
    ) -> None:
        self.name = name
        self.model = model
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.timeout = timeout
        self.retries = retries
        self.system_prompt = system_prompt

    # ------------------------------------------------------------------ API

    def _request(self, payload: dict) -> dict:
        if not self.api_key:
            raise RuntimeError(
                "не задан API-ключ Gemini: установите переменную окружения GEMINI_API_KEY"
            )
        req = urllib.request.Request(
            API_URL_TEMPLATE.format(model=self.model),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                last_error = RuntimeError(f"Gemini API HTTP {exc.code}: {body[:600]}")
                if exc.code not in RETRYABLE_HTTP or attempt == self.retries:
                    raise last_error from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_error = RuntimeError(f"Gemini API недоступен: {exc}")
                if attempt == self.retries:
                    raise last_error from exc
            time.sleep(3 * (attempt + 1))
        raise last_error or RuntimeError("Gemini API: неизвестная ошибка")

    @staticmethod
    def _extract_text(data: dict) -> str:
        candidates = data.get("candidates") or []
        if not candidates:
            feedback = data.get("promptFeedback")
            raise RuntimeError(f"Gemini не вернул кандидатов ответа: {feedback or data}")
        parts = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts)
        if not text.strip():
            raise RuntimeError(
                f"пустой ответ Gemini (finishReason={candidates[0].get('finishReason')})"
            )
        return text

    # ----------------------------------------------------------------- шаг

    def run(self, ctx: StepContext, workspace) -> AgentResult:
        from ..protocol import MANIFEST_SCHEMA_HINT  # локальный импорт против циклов

        prompt = build_prompt(ctx, include_files=True)
        system_text = self.system_prompt + "\n\n" + MANIFEST_SCHEMA_HINT
        full_request = system_text + "\n\n=== ЗАДАЧА (user) ===\n" + prompt
        payload = {
            "systemInstruction": {"parts": [{"text": system_text}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_output_tokens,
                "responseMimeType": "application/json",
            },
        }
        data = self._request(payload)
        text = self._extract_text(data)
        try:
            result = parse_manifest(self.name, text)
        except ValueError as exc:
            result = AgentResult(
                agent=self.name,
                status=Status.ERROR,
                summary=f"не удалось разобрать манифест Gemini: {exc}",
                raw=text,
            )
        result.prompt = full_request
        return result


__all__ = ["GeminiAgent"]
