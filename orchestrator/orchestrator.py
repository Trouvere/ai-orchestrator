"""Ядро оркестратора.

Оркестратор — единственный посредник между моделями. Он:

* ведёт конвейер шагов (кто ходит следующим и с какой инструкцией);
* собирает контекст шага: задача, история, структура и содержимое файлов,
  замечания ревью, вывод тестов;
* применяет манифесты API-моделей к workspace и снимает фактические
  изменения filesystem-агентов;
* фиксирует каждый шаг git-коммитом (версии, diff, откат, аудит);
* запускает тесты (опционально) и решает, достигнут ли результат.

Критерий завершения: ревьюер вернул ``status=approved`` (и тесты прошли,
если задана команда тестов) — либо исчерпан лимит итераций.
"""
from __future__ import annotations

import json
import logging
import subprocess
import time
import traceback
from dataclasses import asdict, dataclass, field

from .agents.base import BaseAgent, StepContext
from .protocol import AgentResult, Status
from .workspace import Workspace

log = logging.getLogger("orchestrator")


@dataclass
class Step:
    """Один шаг конвейера.

    ``kind="agent"`` — работу выполняет исполнитель (``executor``) по инструкции.
    ``kind="test"``  — оркестратор сам запускает ``--test-command``, без модели;
    результат тестов попадает в контекст последующих шагов.

    ``role`` — только ярлык/селектор инструкции (plan | implement | review | …),
    поведения он больше не задаёт: это делают ``kind`` и ``gate``.
    """

    kind: str = "agent"                 # "agent" | "test"
    executor: str = ""                  # "api" | "claude" — ключ в реестре исполнителей (для kind="agent")
    role: str = "step"                  # ярлык этапа: plan | implement | review | произвольный
    instruction: str = ""
    only_first_iteration: bool = False  # например, планирование — один раз
    gate: bool = False                  # шаг-гейт: status=approved (+ зелёные тесты) завершает прогон
    include_file_contents: bool = True  # передавать ли содержимое файлов api-исполнителю
    files: list[str] | None = None      # ограничить контекст конкретными файлами


@dataclass
class StepRecord:
    """Запись журнала об одном выполненном шаге."""

    iteration: int
    step_index: int
    agent: str
    role: str
    status: str
    summary: str
    notes: str
    commit: str | None
    changed_files: list[str]
    duration_s: float


@dataclass
class RunReport:
    """Итог прогона конвейера."""

    success: bool
    message: str
    objective: str
    iterations_used: int
    head_commit: str
    workspace: str
    records: list[StepRecord] = field(default_factory=list)


class _StopRun(Exception):
    """Внутренний сигнал аварийного завершения прогона."""


class Orchestrator:
    def __init__(
        self,
        workspace: Workspace,
        agents: dict[str, BaseAgent],
        pipeline: list[Step],
        max_iterations: int = 3,
        test_command: str | None = None,
        test_timeout: int = 600,
        history_window: int = 10,
    ) -> None:
        unknown = sorted({s.executor for s in pipeline if s.kind == "agent" and s.executor not in agents})
        if unknown:
            raise ValueError(
                f"в конвейере указаны неизвестные исполнители: {unknown}; "
                f"доступны: {sorted(agents)}"
            )
        self.workspace = workspace
        self.agents = agents
        self.pipeline = pipeline
        self.max_iterations = max_iterations
        self.test_command = test_command
        self.test_timeout = test_timeout
        self.history_window = history_window

        self._raw_dir = workspace.log_dir / "raw"
        self._raw_dir.mkdir(exist_ok=True)
        self._jsonl_path = workspace.log_dir / f"run-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"

    # ------------------------------------------------------------- сервисы

    def _log_record(self, record: StepRecord) -> None:
        with self._jsonl_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    def _save_io(self, record: StepRecord, prompt: str, response: str) -> None:
        """Сохранить запрос и ответ шага в raw/ (каждый — отдельным файлом)."""
        base = f"iter{record.iteration}-step{record.step_index}-{record.agent}"
        if prompt:
            (self._raw_dir / f"{base}.request.txt").write_text(prompt, encoding="utf-8")
        if response:
            (self._raw_dir / f"{base}.response.txt").write_text(response, encoding="utf-8")

    def _run_tests(self) -> tuple[bool, str]:
        assert self.test_command

        # Убедиться, что зависимости установлены (важно для первого запуска)
        req_file = self.workspace.root / "requirements.txt"
        if req_file.is_file():
            log.info("   установка зависимостей...")
            install_proc = subprocess.run(
                "pip install -q -r requirements.txt",
                shell=True,
                cwd=self.workspace.root,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if install_proc.returncode != 0:
                log.warning("   ошибка при установке зависимостей: %s", install_proc.stderr[:200])

        log.info("   запускаю тесты: %s", self.test_command)
        try:
            proc = subprocess.run(
                self.test_command,
                shell=True,
                cwd=self.workspace.root,
                capture_output=True,
                text=True,
                timeout=self.test_timeout,
            )
        except subprocess.TimeoutExpired:
            return False, f"тесты не уложились в таймаут {self.test_timeout} с"
        output = ((proc.stdout or "") + (proc.stderr or "")).strip()
        tail = output[-4000:] if output else "(нет вывода)"
        passed = proc.returncode == 0
        log.info("   тесты: %s", "ПРОЙДЕНЫ" if passed else f"ПРОВАЛЕНЫ (код {proc.returncode})")
        return passed, f"exit_code={proc.returncode}\n{tail}"

    def _execute_test_step(
        self, index: int, iteration: int
    ) -> tuple[StepRecord, bool | None, str]:
        """Шаг ``kind="test"``: прогнать тесты и оформить запись журнала.

        Падение тестов — НЕ ошибка прогона (статус ``changes_requested``), а вход
        для следующего шага доработки. Если ``--test-command`` не задана — шаг
        пропускается без ошибки.
        """
        started = time.time()
        if not self.test_command:
            log.info("→ шаг %d: тесты пропущены (нет --test-command)", index)
            record = StepRecord(
                iteration=iteration, step_index=index, agent="test", role="test",
                status=Status.OK.value, summary="тест-команда не задана — шаг пропущен",
                notes="", commit=None, changed_files=[],
                duration_s=round(time.time() - started, 2),
            )
            return record, None, ""

        log.info("→ шаг %d: запуск тестов", index)
        print("  TEST: запускаю тесты...", flush=True)
        passed, output = self._run_tests()
        print(f"  TEST: {'пройдены' if passed else 'провалены'}", flush=True)
        record = StepRecord(
            iteration=iteration, step_index=index, agent="test", role="test",
            status=Status.OK.value if passed else Status.CHANGES_REQUESTED.value,
            summary="тесты пройдены" if passed else "тесты провалены",
            notes=output, commit=None, changed_files=[],
            duration_s=round(time.time() - started, 2),
        )
        return record, passed, output

    # --------------------------------------------------------- основной цикл

    def run(self, objective: str) -> RunReport:
        log.info("Старт прогона. Workspace: %s", self.workspace.root)
        log.info("Задача: %s", objective)

        records: list[StepRecord] = []
        history: list[dict] = []
        review_notes = ""
        test_output = ""
        tests_passed: bool | None = None
        success = False
        message = ""
        iterations_used = 0

        try:
            for iteration in range(1, self.max_iterations + 1):
                iterations_used = iteration
                log.info("=== Итерация %d/%d ===", iteration, self.max_iterations)

                for index, step in enumerate(self.pipeline, start=1):
                    if step.only_first_iteration and iteration > 1:
                        continue

                    # Шаг тестов: оркестратор сам гоняет команду, без модели.
                    if step.kind == "test":
                        record, tests_passed, test_output = self._execute_test_step(index, iteration)
                        records.append(record)
                        self._log_record(record)
                        continue

                    agent = self.agents[step.executor]
                    record = self._execute_step(
                        step, index, iteration, agent, objective,
                        history, review_notes, test_output, records,
                    )

                    if record.status == Status.ERROR.value:
                        raise _StopRun(
                            f"шаг {record.agent} ({record.role}) завершился ошибкой: {record.summary}"
                        )

                    # Шаг-гейт решает, можно ли завершить прогон.
                    if step.gate:
                        review_notes = (record.notes or record.summary).strip()
                        if record.status == Status.APPROVED.value:
                            if self.test_command and tests_passed is False:
                                review_notes += "\nРевью одобрено, но тесты падают — почини их."
                                log.warning("   approved при падающих тестах — продолжаю цикл")
                            else:
                                success = True

                    if success:
                        break
                if success:
                    message = f"задача одобрена ревьюером на итерации {iteration}"
                    break
            if not success and not message:
                message = f"лимит итераций ({self.max_iterations}) исчерпан без статуса approved"
        except _StopRun as exc:
            message = str(exc)
        except KeyboardInterrupt:
            message = "прогон прерван пользователем"

        report = RunReport(
            success=success,
            message=message,
            objective=objective,
            iterations_used=iterations_used,
            head_commit=self.workspace.head(),
            workspace=str(self.workspace.root),
            records=records,
        )
        report_path = self.workspace.log_dir / "report.json"
        report_path.write_text(
            json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        log.info("Итог: %s — %s", "УСПЕХ" if success else "НЕ ЗАВЕРШЕНО", message)
        log.info("Журнал: %s, отчёт: %s", self._jsonl_path, report_path)
        return report

    # ------------------------------------------------------------- один шаг

    def _execute_step(
        self,
        step: Step,
        index: int,
        iteration: int,
        agent: BaseAgent,
        objective: str,
        history: list[dict],
        review_notes: str,
        test_output: str,
        records: list[StepRecord],
    ) -> StepRecord:
        extra: dict[str, str] = {}
        if review_notes:
            extra["review_notes"] = review_notes
        if test_output:
            extra["test_output"] = test_output

        files: dict[str, str] = {}
        if agent.mode == "api" and step.include_file_contents:
            files = self.workspace.export_files(step.files)

        ctx = StepContext(
            objective=objective,
            instruction=step.instruction,
            iteration=iteration,
            step_index=index,
            role=step.role,
            file_tree=self.workspace.tree(),
            files=files,
            history=history[-self.history_window:],
            extra=extra,
        )

        log.info("→ шаг %d: %s (%s, режим %s)", index, agent.name, step.role, agent.mode)
        started = time.time()
        print(f"  >> {agent.name.upper()} работает...", flush=True)
        try:
            result = agent.run(ctx, self.workspace)
        except Exception as exc:  # noqa: BLE001 — сбой агента не должен терять журнал
            result = AgentResult(
                agent=agent.name,
                status=Status.ERROR,
                summary=f"необработанное исключение агента: {exc}",
                raw=traceback.format_exc(),
            )

        print(f"  OK {agent.name.upper()} завершил работу", flush=True)

        # Передача файлов через оркестратор.
        if agent.mode == "api" and result.status is not Status.ERROR:
            print("    -> применяю файлы к диску...", flush=True)
            self.workspace.apply_changes(result.changes)        # манифест -> диск
        elif agent.mode == "filesystem":
            print("    -> снимаю изменения с диска...", flush=True)
            result.changes = self.workspace.pending_changes()   # диск -> история

        commit = self.workspace.snapshot(
            f"[iter {iteration}/{step.role}/{agent.name}] {result.summary[:72]}"
        )
        result.commit = commit

        record = StepRecord(
            iteration=iteration,
            step_index=index,
            agent=agent.name,
            role=step.role,
            status=result.status.value,
            summary=result.summary,
            notes=result.notes,
            commit=commit,
            changed_files=[c.path for c in result.changes],
            duration_s=round(time.time() - started, 2),
        )
        records.append(record)
        history.append(
            {
                "iteration": iteration,
                "agent": agent.name,
                "role": step.role,
                "status": record.status,
                "summary": record.summary[:300],
            }
        )
        self._save_io(record, result.prompt, result.raw)
        self._log_record(record)
        log.info(
            "   статус=%s | файлов изменено: %d | commit=%s | %.1f с — %s",
            record.status, len(record.changed_files), commit, record.duration_s,
            record.summary[:120],
        )
        return record


__all__ = ["Orchestrator", "Step", "StepRecord", "RunReport"]
