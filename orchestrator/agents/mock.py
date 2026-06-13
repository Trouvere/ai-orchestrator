"""Мок-агенты: проверка всего контура оркестрации без API-ключей и CLI.

Сценарий мок-прогона повторяет реальный конвейер:

* ``MockGenerator`` (api-режим, имитация Gemini) — генерирует калькулятор
  с намеренной ошибкой и тестами, возвращая JSON-манифест;
* ``MockRefiner`` (filesystem-режим, имитация Claude Code) — правит реальные
  файлы на диске: чинит баг, а на следующей итерации отрабатывает
  замечания ревью (добавляет multiply);
* ``MockReviewer`` (api-режим, имитация Gemini-ревью) — на первой итерации
  требует доработку, на второй ставит approved.

Запуск: ``python -m orchestrator.cli --workspace ./demo --mock``
"""
from __future__ import annotations

from ..protocol import Action, AgentResult, FileChange, Status
from .base import BaseAgent, StepContext, build_prompt

CALCULATOR_BUGGY = '''"""Простой калькулятор (сгенерирован MockGenerator)."""


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


class MockGenerator(BaseAgent):
    """Имитация Gemini-генератора: возвращает манифест новых файлов."""

    name = "mock_gemini"
    mode = "api"

    def run(self, ctx: StepContext, workspace) -> AgentResult:
        return AgentResult(
            agent=self.name,
            status=Status.OK,
            summary="Сгенерирован модуль calculator.py с тестами и README.",
            changes=[
                FileChange("calculator.py", Action.CREATE, CALCULATOR_BUGGY),
                FileChange("test_calculator.py", Action.CREATE, CALCULATOR_TESTS),
                FileChange("README.md", Action.CREATE, "# Demo calculator\n\nСгенерировано мок-конвейером.\n"),
            ],
            prompt=build_prompt(ctx, include_files=True),
            raw="(mock manifest)",
        )


class MockRefiner(BaseAgent):
    """Имитация Claude Code: правит реальные файлы прямо в workspace."""

    name = "mock_claude_code"
    mode = "filesystem"

    def run(self, ctx: StepContext, workspace) -> AgentResult:
        actions: list[str] = []
        source = workspace.read("calculator.py")

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
            agent=self.name,
            status=Status.OK,
            summary="; ".join(actions) or "изменения не потребовались",
            prompt=build_prompt(ctx, include_files=False),
            raw="(mock filesystem edit)",
        )


class MockReviewer(BaseAgent):
    """Имитация Gemini-ревью: сперва запрашивает правки, затем одобряет."""

    name = "mock_gemini_review"
    mode = "api"

    def run(self, ctx: StepContext, workspace) -> AgentResult:
        prompt = build_prompt(ctx, include_files=True)
        source = workspace.read("calculator.py")
        if "def multiply" not in source:
            return AgentResult(
                agent=self.name,
                status=Status.CHANGES_REQUESTED,
                summary="Базовая функциональность есть, но задача закрыта не полностью.",
                notes="Добавьте функцию multiply(a, b) и тест на неё.",
                prompt=prompt,
                raw="(mock review)",
            )
        return AgentResult(
            agent=self.name,
            status=Status.APPROVED,
            summary="Все требования выполнены, тесты на месте. Одобрено.",
            prompt=prompt,
            raw="(mock review)",
        )


__all__ = ["MockGenerator", "MockRefiner", "MockReviewer"]
