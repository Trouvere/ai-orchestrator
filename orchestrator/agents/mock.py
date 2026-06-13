"""Мок-агенты: проверка всего контура оркестрации без API-ключей и CLI.

Два исполнителя по типу (как и в бою), поведение зависит от роли шага:

* ``MockApiAgent`` (api-режим, имитация Gemini) — на роли ``plan`` пишет
  PLAN.md, на роли ``review`` сперва требует доработку (нет multiply), затем
  ставит approved;
* ``MockClaudeAgent`` (filesystem-режим, имитация Claude Code) — на роли
  ``implement`` создаёт calculator с намеренным багом и тесты, дальше чинит
  баг и по замечаниям ревью добавляет multiply.

Стандартный конвейер на мок-агентах: plan → implement → test → review.
Запуск: ``python -m orchestrator.cli --workspace ./demo --mock``
"""
from __future__ import annotations

from ..protocol import Action, AgentResult, FileChange, Status
from .base import BaseAgent, StepContext, build_prompt

CALCULATOR_BUGGY = '''"""Простой калькулятор (сгенерирован мок-конвейером)."""


def add(a: float, b: float) -> float:
    return a - b  # BUG: намеренная ошибка для демонстрации цикла доработки


def subtract(a: float, b: float) -> float:
    return a - b
'''

CALCULATOR_TESTS = '''import unittest

from calculator import add, subtract


class CalculatorTest(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

    def test_subtract(self):
        self.assertEqual(subtract(5, 3), 2)


if __name__ == "__main__":
    unittest.main()
'''

MULTIPLY_SNIPPET = '''

def multiply(a: float, b: float) -> float:
    return a * b
'''

MULTIPLY_TEST = '''

class MultiplyTest(unittest.TestCase):
    def test_multiply(self):
        from calculator import multiply
        self.assertEqual(multiply(3, 4), 12)
'''


def _read_or_none(workspace, rel: str) -> str | None:
    try:
        return workspace.read(rel)
    except FileNotFoundError:
        return None


class MockApiAgent(BaseAgent):
    """Имитация api-исполнителя (Gemini). Поведение зависит от роли шага.

    * ``plan``   — пишет PLAN.md (status=ok);
    * ``review`` — сперва требует доработку (нет multiply), затем approved;
    * иначе      — генерирует первичный calculator (легаси-режим generate).
    """

    name = "mock_api"
    mode = "api"

    def run(self, ctx: StepContext, workspace) -> AgentResult:
        prompt = build_prompt(ctx, include_files=True)

        if ctx.role == "plan":
            plan = (
                "# План\n\n"
                "1. calculator.py — функции add, subtract, multiply.\n"
                "2. test_calculator.py — unit-тесты на каждую функцию.\n"
                "3. README.md — краткое описание.\n"
            )
            return AgentResult(
                agent=self.name, status=Status.OK,
                summary="Составлен план реализации калькулятора (PLAN.md).",
                changes=[FileChange("PLAN.md", Action.CREATE, plan)],
                prompt=prompt, raw="(mock plan)",
            )

        if ctx.role == "review":
            source = _read_or_none(workspace, "calculator.py") or ""
            if "def multiply" not in source:
                return AgentResult(
                    agent=self.name, status=Status.CHANGES_REQUESTED,
                    summary="Базовая функциональность есть, но задача закрыта не полностью.",
                    notes="Добавьте функцию multiply(a, b) и тест на неё.",
                    prompt=prompt, raw="(mock review)",
                )
            return AgentResult(
                agent=self.name, status=Status.APPROVED,
                summary="Все требования выполнены, тесты на месте. Одобрено.",
                prompt=prompt, raw="(mock review)",
            )

        # Легаси generate-режим (если конвейер использует роль generate).
        return AgentResult(
            agent=self.name, status=Status.OK,
            summary="Сгенерирован модуль calculator.py с тестами и README.",
            changes=[
                FileChange("calculator.py", Action.CREATE, CALCULATOR_BUGGY),
                FileChange("test_calculator.py", Action.CREATE, CALCULATOR_TESTS),
                FileChange("README.md", Action.CREATE, "# Demo calculator\n\nСгенерировано мок-конвейером.\n"),
            ],
            prompt=prompt, raw="(mock manifest)",
        )


class MockClaudeAgent(BaseAgent):
    """Имитация claude-исполнителя (Claude Code): правит реальные файлы на диске.

    Первый прогон (файла ещё нет) — создаёт calculator с намеренным багом и
    тесты. Дальше — чинит баг и по замечаниям ревью добавляет multiply.
    """

    name = "mock_claude"
    mode = "filesystem"

    def run(self, ctx: StepContext, workspace) -> AgentResult:
        prompt = build_prompt(ctx, include_files=False)
        actions: list[str] = []
        source = _read_or_none(workspace, "calculator.py")

        if source is None:
            workspace.write("calculator.py", CALCULATOR_BUGGY)
            workspace.write("test_calculator.py", CALCULATOR_TESTS)
            return AgentResult(
                agent=self.name, status=Status.OK,
                summary="Создан calculator.py (с намеренным багом в add) и тесты.",
                prompt=prompt, raw="(mock filesystem edit)",
            )

        if "a - b  # BUG" in source:
            source = source.replace(
                "return a - b  # BUG: намеренная ошибка для демонстрации цикла доработки",
                "return a + b",
            )
            actions.append("исправлен баг в add()")

        notes = ctx.extra.get("review_notes", "")
        if "multiply" in notes and "def multiply" not in source:
            source += MULTIPLY_SNIPPET
            tests = workspace.read("test_calculator.py")
            workspace.write("test_calculator.py", tests + MULTIPLY_TEST)
            actions.append("по замечаниям ревью добавлена multiply() с тестом")

        workspace.write("calculator.py", source)
        return AgentResult(
            agent=self.name, status=Status.OK,
            summary="; ".join(actions) or "изменения не потребовались",
            prompt=prompt, raw="(mock filesystem edit)",
        )


__all__ = ["MockApiAgent", "MockClaudeAgent"]
