"""Быстрая проверка ключа Gemini.

Подгружает .env, шлёт минимальный запрос к тому же REST-эндпоинту, что и
рабочий агент (``GeminiAgent``), и печатает понятный результат. Без внешних
зависимостей.

Запуск из корня репозитория:

    python -m scripts.check_gemini_key
    python -m scripts.check_gemini_key --model gemini-2.5-pro
"""
from __future__ import annotations

import argparse
import sys

from orchestrator.agents.gemini import GeminiAgent
from orchestrator.cli import load_dotenv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_gemini_key",
        description="Проверка валидности API-ключа Gemini одним запросом.",
    )
    parser.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="модель для проверки (по умолчанию быстрая gemini-2.5-flash)",
    )
    args = parser.parse_args(argv)

    # Windows-консоль часто в cp1252/cp866 и не выводит кириллицу — переключаем на UTF-8.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")

    load_dotenv()  # .env из текущего каталога; реальное окружение в приоритете

    agent = GeminiAgent(model=args.model, retries=0, timeout=30)

    if not agent.api_key:
        print("[FAIL] Ключ не найден: задайте GEMINI_API_KEY (или GOOGLE_API_KEY) "
              "в .env или окружении.", file=sys.stderr)
        return 2

    masked = agent.api_key[:6] + "..." + agent.api_key[-4:]
    print(f"[..] Ключ найден ({masked}), модель {args.model}. Отправляю тестовый запрос...")

    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Ответь одним словом: ping"}]}],
        # запас по токенам: у "думающих" моделей часть уходит на reasoning
        "generationConfig": {"temperature": 0, "maxOutputTokens": 512},
    }

    try:
        data = agent._request(payload)
        text = agent._extract_text(data).strip()
    except RuntimeError as exc:
        msg = str(exc)
        print(f"[FAIL] Запрос не прошёл: {msg}", file=sys.stderr)
        if "HTTP 400" in msg or "API_KEY_INVALID" in msg:
            print("  -> Похоже, ключ недействителен.", file=sys.stderr)
        elif "HTTP 403" in msg:
            print("  -> Ключ есть, но нет доступа к API/модели (проверь включение "
                  "Generative Language API и регион).", file=sys.stderr)
        elif "HTTP 404" in msg:
            print(f"  -> Модель '{args.model}' недоступна для этого ключа.", file=sys.stderr)
        elif "HTTP 429" in msg:
            print("  -> Ключ валиден, но превышена квота (rate limit).", file=sys.stderr)
        return 1

    print(f"[OK] Ключ рабочий. Ответ модели: {text!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
