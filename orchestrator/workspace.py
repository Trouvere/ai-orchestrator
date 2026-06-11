"""Рабочее пространство проекта.

Единый каталог, через который обмениваются файлами все агенты:

* API-модели (Gemini) получают сериализованное содержимое файлов в промпте
  и возвращают манифест — оркестратор материализует его сюда;
* filesystem-агенты (Claude Code) запускаются прямо в этом каталоге
  и редактируют файлы напрямую.

Каждый шаг конвейера фиксируется git-коммитом: это даёт версии, diff между
ходами агентов, откат и полный аудит того, кто что изменил.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from .protocol import Action, FileChange, PROTECTED_DIRS, safe_rel_path

#: Каталоги, исключаемые из обзора проекта и экспорта в контекст моделей.
EXCLUDED_DIRS = {
    ".git",
    ".orchestrator",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "node_modules",
}

GITIGNORE_BODY = """\
.orchestrator/
__pycache__/
*.pyc
.venv/
node_modules/
"""


class WorkspaceError(RuntimeError):
    pass


class Workspace:
    """Файлы проекта + git-версионирование."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.log_dir = self.root / ".orchestrator"
        self.log_dir.mkdir(exist_ok=True)
        self._ensure_git()

    # ------------------------------------------------------------------ git

    def _git(self, *args: str, check: bool = True) -> str:
        res = subprocess.run(
            ["git", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        if check and res.returncode != 0:
            raise WorkspaceError(
                f"git {' '.join(args)} завершился с кодом {res.returncode}: "
                f"{res.stderr.strip() or res.stdout.strip()}"
            )
        return res.stdout.rstrip("\n")

    def _ensure_git(self) -> None:
        if not (self.root / ".git").exists():
            self._git("init", "-q")
        # Локальная идентичность для коммитов оркестратора (идемпотентно).
        self._git("config", "user.email", "orchestrator@local")
        self._git("config", "user.name", "AI Orchestrator")
        gitignore = self.root / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text(GITIGNORE_BODY, encoding="utf-8")
        # Гарантируем существование HEAD.
        if subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=self.root, capture_output=True,
        ).returncode != 0:
            self._git("add", "-A")
            self._git("commit", "-q", "--allow-empty", "-m", "[orchestrator] init workspace")

    def head(self) -> str:
        return self._git("rev-parse", "--short", "HEAD")

    def snapshot(self, message: str) -> str:
        """Зафиксировать текущее состояние workspace; вернуть sha HEAD."""
        self._git("add", "-A")
        if self._git("status", "--porcelain"):
            self._git("commit", "-q", "-m", message)
        return self.head()

    def diff_stat(self, ref_a: str, ref_b: str = "HEAD") -> str:
        return self._git("diff", "--stat", ref_a, ref_b, check=False)

    def pending_changes(self) -> list[FileChange]:
        """Незакоммиченные изменения (после работы filesystem-агента)."""
        changes: list[FileChange] = []
        for line in self._git("status", "--porcelain").splitlines():
            if len(line) < 4:
                continue
            code, path = line[:2], line[3:].strip().strip('"')
            if " -> " in path:  # переименование: старый путь считаем удалённым
                old, path = path.split(" -> ", 1)
                changes.append(FileChange(path=old, action=Action.DELETE))
            if "D" in code:
                action = Action.DELETE
            elif code == "??" or "A" in code:
                action = Action.CREATE
            else:
                action = Action.UPDATE
            content = None
            if action is not Action.DELETE:
                fp = self.root / path
                if fp.is_file():
                    try:
                        content = fp.read_text(encoding="utf-8")
                    except (UnicodeDecodeError, OSError):
                        content = None  # бинарный файл — фиксируем без содержимого
            changes.append(FileChange(path=path, action=action, content=content))
        return changes

    # ---------------------------------------------------------------- файлы

    def _resolve(self, rel_path: str) -> Path:
        rel = safe_rel_path(rel_path)
        target = (self.root / rel).resolve()
        if not target.is_relative_to(self.root):
            raise WorkspaceError(f"путь выходит за пределы workspace: {rel_path!r}")
        return target

    def read(self, rel_path: str) -> str:
        return self._resolve(rel_path).read_text(encoding="utf-8")

    def write(self, rel_path: str, content: str) -> None:
        target = self._resolve(rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def delete(self, rel_path: str) -> None:
        target = self._resolve(rel_path)
        if target.is_file():
            target.unlink()

    def apply_changes(self, changes: list[FileChange]) -> list[str]:
        """Материализовать манифест API-модели в реальные файлы.

        Возвращает список применённых путей.
        """
        applied: list[str] = []
        for change in changes:
            if change.action is Action.DELETE:
                self.delete(change.path)
            else:
                if change.content is None:
                    continue
                self.write(change.path, change.content)
            applied.append(change.path)
        return applied

    def list_files(self) -> list[str]:
        """Все файлы проекта (без служебных каталогов), отсортированно."""
        files: list[str] = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(self.root)
            if any(part in EXCLUDED_DIRS for part in rel.parts):
                continue
            if rel.suffix == ".pyc":
                continue
            files.append(rel.as_posix())
        return files

    def tree(self, limit: int = 400) -> str:
        """Текстовый обзор структуры проекта для контекста моделей."""
        lines = []
        for rel in self.list_files()[:limit]:
            size = (self.root / rel).stat().st_size
            lines.append(f"{rel} ({size} байт)")
        return "\n".join(lines)

    def export_files(
        self,
        paths: list[str] | None = None,
        max_file_chars: int = 48_000,
        max_total_chars: int = 360_000,
    ) -> dict[str, str]:
        """Сериализовать содержимое файлов для передачи API-модели.

        Бинарные файлы пропускаются, слишком большие — усекаются,
        суммарный объём ограничивается, чтобы не переполнить контекст.
        """
        selected = paths if paths is not None else self.list_files()
        result: dict[str, str] = {}
        total = 0
        for rel in selected:
            fp = self.root / safe_rel_path(rel)
            if not fp.is_file():
                continue
            try:
                text = fp.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if len(text) > max_file_chars:
                text = text[:max_file_chars] + "\n…[обрезано оркестратором: файл слишком большой]"
            if total + len(text) > max_total_chars:
                result[rel] = "…[содержимое не передано: исчерпан лимит контекста]"
                continue
            result[rel] = text
            total += len(text)
        return result


__all__ = ["Workspace", "WorkspaceError", "EXCLUDED_DIRS", "PROTECTED_DIRS"]
