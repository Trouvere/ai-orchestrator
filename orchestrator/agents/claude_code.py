"""Адаптер Claude Code (filesystem-режим).

Claude Code — агент с реальным доступом к файловой системе, поэтому он
запускается в headless-режиме (``claude -p ...``) прямо в каталоге workspace:

1. Оркестратор передаёт контекст шага в промпте (без содержимого файлов —
   агент читает их с диска сам).
2. Claude Code читает, изменяет и создаёт реальные файлы проекта,
   при необходимости запускает тесты.
3. Оркестратор снимает фактические изменения через ``git status``
   и фиксирует их коммитом — так все правки попадают в общую историю версий.

Флаги CLI вынесены в параметры конструктора: набор опций может отличаться
между версиями Claude Code — актуальный список смотрите в ``claude --help``
и в документации https://docs.claude.com/en/docs/claude-code/overview.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from ..protocol import AgentResult, Status, extract_json
from .base import BaseAgent, StepContext, build_prompt

CLAUDE_CODE_TASK_SUFFIX = """\
КАК РАБОТАТЬ:
- Ты запущен непосредственно в каталоге проекта: читай и изменяй РЕАЛЬНЫЕ файлы
  (создавай новые, правь существующие, удаляй лишние).
- Не трогай служебные каталоги .git и .orchestrator и не делай git-коммиты:
  фиксацией версий занимается оркестратор.
- Если в проекте есть тесты — по возможности запусти их и почини падения.

В САМОМ КОНЦЕ ответа выведи единственный JSON-объект (без Markdown):
{"summary": "что сделано, 1-3 предложения", "status": "ok", "notes": "проблемы/рекомендации или пустая строка"}"""


class ClaudeCodeAgent(BaseAgent):
    mode = "filesystem"

    def __init__(
        self,
        name: str = "claude_code",
        claude_cmd: str = "claude",
        model: str | None = None,
        max_turns: int | None = 40,
        permission_mode: str | None = "acceptEdits",
        allowed_tools: list[str] | None = None,
        dangerously_skip_permissions: bool = False,
        bare: bool = False,
        extra_args: list[str] | None = None,
        timeout: int = 2400,
    ) -> None:
        self.name = name
        self.claude_cmd = claude_cmd
        self.model = model
        self.max_turns = max_turns
        self.permission_mode = permission_mode
        self.allowed_tools = allowed_tools
        self.dangerously_skip_permissions = dangerously_skip_permissions
        self.bare = bare
        self.extra_args = extra_args or []
        self.timeout = timeout

    # ------------------------------------------------------------- команда

    def _build_command(self, prompt_file: str) -> list[str]:
        cmd = [self.claude_cmd, "-p", prompt_file, "--output-format", "json"]
        if self.bare:
            # Изолирует сборку: пропускает авто-подгрузку CLAUDE.md/памяти/hooks/skills/
            # MCP/плагинов из дерева каталогов. ВНИМАНИЕ: на части версий Claude Code
            # (проверено на 2.1.173) --bare сбрасывает и авторизацию → "Not logged in".
            # Поэтому по умолчанию выключено; включай осознанно (см. --claude-bare).
            cmd += ["--bare"]
        if self.model:
            cmd += ["--model", self.model]
        if self.max_turns:
            cmd += ["--max-turns", str(self.max_turns)]
        if self.dangerously_skip_permissions:
            cmd += ["--dangerously-skip-permissions"]
        elif self.permission_mode:
            cmd += ["--permission-mode", self.permission_mode]
        if self.allowed_tools:
            cmd += ["--allowedTools", ",".join(self.allowed_tools)]
        cmd += self.extra_args
        return cmd

    @staticmethod
    def _final_text(stdout: str) -> tuple[str, bool]:
        """Достать финальный текст ответа из JSON-вывода CLI."""
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return stdout, False
        if isinstance(data, dict):
            return str(data.get("result", "") or stdout), bool(data.get("is_error"))
        return stdout, False

    # ----------------------------------------------------------------- шаг

    def run(self, ctx: StepContext, workspace) -> AgentResult:
        claude_path = shutil.which(self.claude_cmd)
        if claude_path is None:
            return AgentResult(
                agent=self.name,
                status=Status.ERROR,
                summary=(
                    f"CLI '{self.claude_cmd}' не найден. Установите Claude Code: "
                    "npm install -g @anthropic-ai/claude-code"
                ),
            )

        prompt = build_prompt(ctx, include_files=False) + "\n\n" + CLAUDE_CODE_TASK_SUFFIX

        # Пишем промпт в файл внутри workspace, чтобы избежать проблем с temp путями на Windows
        prompt_file = str(workspace.root / ".orchestrator" / "current_prompt.txt")
        Path(prompt_file).parent.mkdir(parents=True, exist_ok=True)
        Path(prompt_file).write_text(prompt, encoding="utf-8")

        try:
            cmd = self._build_command(prompt_file)
            # Заменить относительный путь на абсолютный для надёжности на Windows
            cmd[0] = claude_path
            proc = subprocess.run(
                cmd,
                cwd=workspace.root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return AgentResult(
                agent=self.name,
                status=Status.ERROR,
                summary=f"Claude Code не уложился в таймаут {self.timeout} с",
            )

        text, is_error = self._final_text(proc.stdout)
        raw = proc.stdout + ("\n--- stderr ---\n" + proc.stderr if proc.stderr else "")

        if proc.returncode != 0 or is_error:
            return AgentResult(
                agent=self.name,
                status=Status.ERROR,
                summary=f"Claude Code завершился с ошибкой (код {proc.returncode}): {text[:300]}",
                raw=raw,
            )

        # Финальный JSON-статус из ответа агента (необязателен).
        summary, status, notes = text.strip()[:300] or "(без описания)", Status.OK, ""
        try:
            report = extract_json(text)
            summary = str(report.get("summary", summary)) or summary
            notes = str(report.get("notes", "") or "")
            try:
                status = Status(str(report.get("status", "ok")).strip().lower())
            except ValueError:
                status = Status.OK
        except ValueError:
            pass  # агент не вернул структурированный итог — не критично

        # Изменения файлов оркестратор снимет с диска (git status) сам.
        return AgentResult(agent=self.name, status=status, summary=summary, notes=notes, raw=raw)


__all__ = ["ClaudeCodeAgent"]
