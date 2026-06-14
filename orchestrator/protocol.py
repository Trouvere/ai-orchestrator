"""Протокол обмена между оркестратором и AI-агентами.

Все агенты, независимо от способа интеграции (API-модель или агент с прямым
доступом к файловой системе), возвращают результат в едином формате
``AgentResult`` со списком изменений файлов ``FileChange``.

* Для API-моделей (Gemini) изменения извлекаются из JSON-манифеста,
  который модель обязана вернуть в ответе. Оркестратор материализует
  манифест в реальные файлы рабочего пространства.
* Для filesystem-агентов (Claude Code) изменения вычисляются по фактическому
  состоянию рабочего пространства (``git status``) после работы агента.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import PurePosixPath
from typing import Any

#: Каталоги, в которые агентам запрещено писать.
PROTECTED_DIRS = (".git", ".orchestrator")


class Action(str, Enum):
    """Тип операции над файлом."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class Status(str, Enum):
    """Статус, который агент присваивает своему шагу."""

    OK = "ok"                                # шаг выполнен, работа продолжается
    APPROVED = "approved"                    # ревьюер подтвердил результат
    CHANGES_REQUESTED = "changes_requested"  # ревьюер требует доработок
    ERROR = "error"                          # шаг завершился сбоем


@dataclass
class FileChange:
    """Одно изменение файла в рабочем пространстве."""

    path: str
    action: Action
    content: str | None = None  # None допустим для delete и бинарных файлов

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "action": self.action.value,
            "content_chars": len(self.content) if self.content is not None else None,
        }


@dataclass
class AgentResult:
    """Единый результат шага любого агента."""

    agent: str
    status: Status
    summary: str
    changes: list[FileChange] = field(default_factory=list)
    notes: str = ""           # развёрнутые замечания (например, текст ревью)
    prompt: str = ""          # запрос, отправленный модели — сохраняется в журнал
    raw: str = ""             # сырой ответ модели — сохраняется в журнал
    commit: str | None = None  # sha коммита, зафиксировавшего шаг


#: Контракт манифеста, который вставляется в системный промпт API-моделей.
MANIFEST_SCHEMA_HINT = """\
Отвечай СТРОГО одним JSON-объектом без пояснений вокруг и без Markdown:
{
  "summary": "краткое описание сделанного (1-3 предложения)",
  "status": "ok | approved | changes_requested",
  "notes": "замечания, найденные проблемы, план следующих шагов (можно пустую строку)",
  "files": [
    {"path": "относительный/путь/к/файлу", "action": "create | update | delete",
     "content": "ПОЛНОЕ новое содержимое файла"}
  ]
}
Правила манифеста:
- это должен быть ОДИН валидный JSON: внутри строк экранируй двойные кавычки
  как \\" и переводы строк как \\n; не используй тройные кавычки и Markdown;
- path всегда относительный: без ведущего "/" и без "..";
- content передаётся целиком (полная итоговая версия файла, а не diff);
- для action=delete поле content не указывается;
- если файлы менять не нужно (например, при ревью без правок) — "files": [];
- статус approved может ставить только ревьюер и только когда задача
  действительно решена; иначе используй changes_requested и перечисли
  конкретные правки в notes."""


def extract_json(text: str) -> dict[str, Any]:
    """Извлечь JSON-объект из ответа модели.

    Терпим к типичным отклонениям: Markdown-ограждения ```json ... ```,
    пояснительный текст до/после объекта.
    """
    text = (text or "").strip()
    candidates: list[str] = []

    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        candidates.append(fence.group(1))

    candidates.append(text)

    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start : end + 1])

    for cand in candidates:
        try:
            obj = json.loads(cand)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    raise ValueError("в ответе модели не найден корректный JSON-объект")


def safe_rel_path(path: str) -> str:
    """Нормализовать путь из манифеста и проверить, что он безопасен.

    Запрещены абсолютные пути, выход из workspace через ``..`` и запись
    в служебные каталоги (``.git``, ``.orchestrator``).
    """
    raw = str(path).strip().replace("\\", "/")
    p = PurePosixPath(raw)
    if p.is_absolute():
        raise ValueError(f"абсолютный путь запрещён: {path!r}")
    parts = [part for part in p.parts if part != "."]
    if not parts:
        raise ValueError(f"пустой путь: {path!r}")
    if any(part == ".." for part in parts):
        raise ValueError(f"выход за пределы workspace запрещён: {path!r}")
    if parts[0] in PROTECTED_DIRS:
        raise ValueError(f"запись в служебный каталог запрещена: {path!r}")
    return "/".join(parts)


def parse_manifest(agent: str, text: str) -> AgentResult:
    """Разобрать JSON-манифест API-модели в ``AgentResult``.

    Некорректные записи о файлах не «роняют» весь шаг: они пропускаются,
    а описание проблемы добавляется в notes.
    """
    data = extract_json(text)

    status_raw = str(data.get("status", "ok")).strip().lower()
    try:
        status = Status(status_raw)
    except ValueError:
        status = Status.OK

    notes = str(data.get("notes", "") or "")
    problems: list[str] = []
    changes: list[FileChange] = []

    for item in data.get("files", []) or []:
        if not isinstance(item, dict):
            problems.append(f"пропущена запись манифеста (не объект): {item!r}")
            continue
        try:
            rel = safe_rel_path(item.get("path", ""))
        except ValueError as exc:
            problems.append(f"пропущен файл: {exc}")
            continue

        action_raw = str(item.get("action", "update")).strip().lower()
        try:
            action = Action(action_raw)
        except ValueError:
            action = Action.UPDATE

        content = item.get("content")
        if action is not Action.DELETE and not isinstance(content, str):
            problems.append(f"пропущен файл {rel}: отсутствует строковое поле content")
            continue

        changes.append(
            FileChange(
                path=rel,
                action=action,
                content=None if action is Action.DELETE else content,
            )
        )

    if problems:
        notes = (notes + "\n" if notes else "") + "Проблемы манифеста: " + "; ".join(problems)

    return AgentResult(
        agent=agent,
        status=status,
        summary=str(data.get("summary", "") or "(без описания)"),
        changes=changes,
        notes=notes,
        raw=text,
    )
