"""Готовые конвейеры и загрузка пользовательских из JSON.

Конвейер — список шагов (``Step``). Каждый шаг это либо работа исполнителя
(``kind="agent"``, поле ``executor``: ``"api"`` или ``"claude"``), либо прогон
тестов (``kind="test"``). Исполнитель указывается абстрактно — конкретного
агента под тип подставляет CLI, поэтому один и тот же конвейер работает и на
боевых агентах, и на мок-агентах.

Стандартный сценарий:

  итерация 1: plan (api) → implement (claude) → test → review (api, gate)
  итерации 2+:            implement (claude) → test → review (api, gate)

Планирование выполняется один раз; дальше цикл «доработка → тесты → ревью»
крутится до approved (при зелёных тестах) или исчерпания лимита итераций.
Замечания ревью и вывод тестов автоматически попадают в контекст следующей
доработки.
"""
from __future__ import annotations

import json
from pathlib import Path

from .orchestrator import Step

PLAN_INSTRUCTION = """\
Составь план реализации глобальной задачи. НЕ пиши код — только план.
Разбей работу на последовательные этапы (например: модель данных, бэкенд,
фронтенд, тесты) так, чтобы их можно было выполнять по отдельности.
Запиши план в файл PLAN.md (через манифест files): список этапов, для каждого —
что сделать и какие файлы затронуть. Верни status=ok."""

IMPLEMENT_INSTRUCTION = """\
Реализуй задачу согласно плану из PLAN.md и текущему состоянию проекта.
Создавай и правь любые нужные файлы: исходный код, тесты, README. Если есть
замечания ревью или падающие тесты — отработай их в первую очередь."""

REVIEW_INSTRUCTION = """\
Проведи ревью текущего состояния проекта относительно глобальной задачи и плана.
Если всё реализовано корректно и полностью — верни status=approved и files=[].
Иначе верни status=changes_requested и перечисли в notes КОНКРЕТНЫЕ правки
(файл, что именно изменить). Мелкие правки можешь внести сам через files."""


def default_pipeline() -> list[Step]:
    """plan → implement → test → review (gate). Подходит и для боевых, и для мок-агентов."""
    return [
        Step(kind="agent", executor="api", role="plan",
             instruction=PLAN_INSTRUCTION, only_first_iteration=True),
        Step(kind="agent", executor="claude", role="implement",
             instruction=IMPLEMENT_INSTRUCTION),
        Step(kind="test"),
        Step(kind="agent", executor="api", role="review",
             instruction=REVIEW_INSTRUCTION, gate=True),
    ]


def load_pipeline(path: str | Path) -> list[Step]:
    """Загрузить конвейер из JSON-файла.

    Формат: список шагов. Для ``kind="agent"`` (по умолчанию) обязательны
    ``executor`` (``"api"``/``"claude"``) и ``instruction``. Для ``kind="test"``
    остальные поля не нужны. См. examples/pipeline.example.json.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("файл конвейера должен содержать непустой JSON-список шагов")
    steps: list[Step] = []
    for i, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"шаг #{i}: должен быть объектом")
        kind = str(item.get("kind", "agent"))
        if kind == "test":
            steps.append(Step(kind="test", role=str(item.get("role", "test")),
                              only_first_iteration=bool(item.get("only_first_iteration", False))))
            continue
        if kind != "agent":
            raise ValueError(f"шаг #{i}: неизвестный kind={kind!r} (ожидается 'agent' или 'test')")
        if "executor" not in item or "instruction" not in item:
            raise ValueError(f"шаг #{i}: для kind='agent' обязательны 'executor' и 'instruction'")
        steps.append(
            Step(
                kind="agent",
                executor=str(item["executor"]),
                role=str(item.get("role", "step")),
                instruction=str(item["instruction"]),
                only_first_iteration=bool(item.get("only_first_iteration", False)),
                gate=bool(item.get("gate", False)),
                include_file_contents=bool(item.get("include_file_contents", True)),
                files=item.get("files"),
            )
        )
    return steps


__all__ = ["default_pipeline", "load_pipeline"]
