"""Готовые конвейеры и загрузка пользовательских из JSON.

Стандартный сценарий повторяет ТЗ:

  итерация 1: Gemini (generate) → Claude Code (refine) → Gemini (review)
  итерации 2+:                    Claude Code (refine) → Gemini (review)

Первичная генерация выполняется один раз; дальше цикл «доработка → ревью»
крутится до approved или исчерпания лимита итераций. Замечания ревью
автоматически попадают в контекст следующего шага доработки.
"""
from __future__ import annotations

import json
from pathlib import Path

from .orchestrator import Step

GENERATE_INSTRUCTION = """\
Выполни первичную реализацию глобальной задачи. Создай все необходимые файлы:
исходный код, тесты, при необходимости — спецификацию и README. Структуру
каталогов выбирай сам, исходя из задачи."""

REFINE_INSTRUCTION = """\
Проанализируй текущее состояние файлов проекта. Исправь ошибки, выполни
рефакторинг, допиши недостающую функциональность и тесты. Если есть
замечания ревью или падающие тесты — отработай их в первую очередь."""

REVIEW_INSTRUCTION = """\
Проведи ревью текущего состояния проекта относительно глобальной задачи.
Если всё реализовано корректно и полностью — верни status=approved и files=[].
Иначе верни status=changes_requested и перечисли в notes КОНКРЕТНЫЕ правки
(файл, что именно изменить). Мелкие правки можешь внести сам через files."""


def default_pipeline() -> list[Step]:
    return [
        Step(agent="gemini", role="generate", instruction=GENERATE_INSTRUCTION,
             only_first_iteration=True),
        Step(agent="claude_code", role="refine", instruction=REFINE_INSTRUCTION),
        Step(agent="gemini", role="review", instruction=REVIEW_INSTRUCTION),
    ]


def mock_pipeline() -> list[Step]:
    """Конвейер той же формы на мок-агентах (см. agents/mock.py)."""
    return [
        Step(agent="generator", role="generate", instruction=GENERATE_INSTRUCTION,
             only_first_iteration=True),
        Step(agent="refiner", role="refine", instruction=REFINE_INSTRUCTION),
        Step(agent="reviewer", role="review", instruction=REVIEW_INSTRUCTION),
    ]


def load_pipeline(path: str | Path) -> list[Step]:
    """Загрузить конвейер из JSON-файла.

    Формат: список объектов с полями Step, см. examples/pipeline.example.json.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("файл конвейера должен содержать непустой JSON-список шагов")
    steps: list[Step] = []
    for i, item in enumerate(data, start=1):
        if not isinstance(item, dict) or "agent" not in item or "instruction" not in item:
            raise ValueError(f"шаг #{i}: обязательны поля 'agent' и 'instruction'")
        steps.append(
            Step(
                agent=str(item["agent"]),
                role=str(item.get("role", "step")),
                instruction=str(item["instruction"]),
                only_first_iteration=bool(item.get("only_first_iteration", False)),
                include_file_contents=bool(item.get("include_file_contents", True)),
                files=item.get("files"),
            )
        )
    return steps


__all__ = ["default_pipeline", "mock_pipeline", "load_pipeline"]
