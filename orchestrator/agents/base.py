"""Базовый интерфейс AI-агента и сборка контекста шага.

Агент бывает двух режимов:

* ``api`` — модель без доступа к файловой системе (Gemini). Получает
  содержимое файлов в промпте, возвращает JSON-манифест изменений,
  который оркестратор материализует на диск.
* ``filesystem`` — агент работает прямо в каталоге workspace (Claude Code).
  Изменения вычисляются оркестратором по факту (``git status``).
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Literal, TYPE_CHECKING

from ..protocol import AgentResult

if TYPE_CHECKING:  # pragma: no cover
    from ..workspace import Workspace

AgentMode = Literal["api", "filesystem"]


@dataclass
class StepContext:
    """Полный контекст одного шага конвейера, передаваемый агенту."""

    objective: str                 # глобальная задача всего прогона
    instruction: str               # инструкция текущего шага
    iteration: int
    step_index: int
    role: str                      # generate | refine | review | ...
    file_tree: str = ""            # обзор структуры проекта
    files: dict[str, str] = field(default_factory=dict)   # путь -> содержимое
    history: list[dict[str, Any]] = field(default_factory=list)
    extra: dict[str, str] = field(default_factory=dict)   # review_notes, test_output, ...


class BaseAgent(abc.ABC):
    """Единый интерфейс для всех моделей, подключаемых к оркестратору."""

    name: str = "agent"
    mode: AgentMode = "api"

    @abc.abstractmethod
    def run(self, ctx: StepContext, workspace: "Workspace") -> AgentResult:
        """Выполнить шаг и вернуть результат в едином формате."""


def build_prompt(ctx: StepContext, include_files: bool = True) -> str:
    """Собрать текстовый контекст шага.

    Один и тот же формат используется для всех агентов, чтобы модели
    видели проект одинаково. Для filesystem-агентов содержимое файлов
    не вставляется (``include_files=False``) — они читают файлы сами.
    """
    sections: list[str] = [
        f"ГЛОБАЛЬНАЯ ЗАДАЧА ПРОЕКТА:\n{ctx.objective}",
        f"ТВОЯ ИНСТРУКЦИЯ НА ЭТОМ ШАГЕ (итерация {ctx.iteration}, роль: {ctx.role}):\n{ctx.instruction}",
    ]

    if ctx.extra.get("review_notes"):
        sections.append("ЗАМЕЧАНИЯ ПОСЛЕДНЕГО РЕВЬЮ (их нужно отработать):\n" + ctx.extra["review_notes"])
    if ctx.extra.get("test_output"):
        sections.append("РЕЗУЛЬТАТ ПОСЛЕДНЕГО ЗАПУСКА ТЕСТОВ:\n" + ctx.extra["test_output"])

    if ctx.history:
        rows = [
            f"- итерация {h['iteration']}, {h['agent']} ({h['role']}): "
            f"{h['summary']} [status={h['status']}]"
            for h in ctx.history
        ]
        sections.append("ИСТОРИЯ ПРЕДЫДУЩИХ ШАГОВ:\n" + "\n".join(rows))

    sections.append("ТЕКУЩАЯ СТРУКТУРА ПРОЕКТА:\n" + (ctx.file_tree or "(workspace пока пуст)"))

    if include_files and ctx.files:
        blocks = [
            f"=== ФАЙЛ: {path} ===\n{content}\n=== КОНЕЦ ФАЙЛА: {path} ==="
            for path, content in ctx.files.items()
        ]
        sections.append("ТЕКУЩЕЕ СОДЕРЖИМОЕ ФАЙЛОВ ПРОЕКТА:\n\n" + "\n\n".join(blocks))

    return "\n\n".join(sections)


__all__ = ["BaseAgent", "StepContext", "build_prompt", "AgentMode"]
