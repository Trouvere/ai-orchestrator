"""CLI оркестратора.

Примеры:

  # Боевой запуск (нужны GEMINI_API_KEY и установленный Claude Code):
  python -m orchestrator.cli --workspace ./my-project \\
      --objective "Сделай REST API списка задач на FastAPI с тестами" \\
      --test-command "python -m pytest -q" --max-iterations 4

  # Офлайн-проверка контура на мок-агентах (ключи не нужны):
  python -m orchestrator.cli --workspace ./demo --mock
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path


def load_dotenv(path: str | os.PathLike[str] = ".env") -> None:
    """Подгрузить переменные из .env (если файл есть).

    Минимальный аналог python-dotenv на стандартной библиотеке, чтобы не тащить
    зависимость. Уже заданные переменные окружения не перетираются — приоритет
    у реального окружения. Поддерживаются строки ``KEY=VALUE``, комментарии ``#``
    и необязательный префикс ``export``.
    """
    p = Path(path)
    if not p.is_file():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

from .agents.claude_code import ClaudeCodeAgent
from .agents.gemini import GeminiAgent
from .agents.mock import MockGenerator, MockRefiner, MockReviewer
from .orchestrator import Orchestrator
from .pipelines import default_pipeline, load_pipeline, mock_pipeline
from .workspace import Workspace

MOCK_OBJECTIVE = (
    "Реализовать модуль calculator.py с функциями add, subtract, multiply "
    "и unit-тестами к ним."
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ai-orchestrator",
        description="Оркестратор совместной разработки несколькими LLM "
                    "(Gemini + Claude Code) через общее файловое пространство.",
    )
    p.add_argument("--workspace", required=True, help="каталог общего рабочего пространства")
    p.add_argument("--objective", help="текст глобальной задачи")
    p.add_argument("--objective-file", help="файл с текстом задачи (альтернатива --objective)")
    p.add_argument("--max-iterations", type=int, default=3)
    p.add_argument("--test-command", help='команда проверки, напр. "python -m pytest -q"')
    p.add_argument("--pipeline", help="JSON-файл с пользовательским конвейером шагов")

    # p.add_argument("--gemini-model", default="gemini-2.5-pro")
    p.add_argument("--gemini-model", default="gemini-2.5-flash")
    p.add_argument("--claude-model", default=None, help="модель для Claude Code (по умолчанию его собственная)")
    p.add_argument("--claude-cmd", default="claude", help="исполняемый файл Claude Code CLI")
    p.add_argument("--claude-permission-mode", default="acceptEdits",
                   help="режим прав Claude Code (см. claude --help)")
    p.add_argument("--claude-max-turns", type=int, default=40)
    p.add_argument("--claude-no-bare", dest="claude_bare", action="store_false", default=True,
                   help="не передавать --bare: разрешить Claude Code подгружать CLAUDE.md/"
                        "память/hooks/skills/MCP из дерева каталогов (по умолчанию изолировано)")

    p.add_argument("--mock", action="store_true",
                   help="прогон контура на встроенных мок-агентах, без ключей и CLI")
    p.add_argument("--verbose", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    load_dotenv()  # .env из текущего каталога; реальное окружение в приоритете

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )

    objective = args.objective
    if not objective and args.objective_file:
        objective = Path(args.objective_file).read_text(encoding="utf-8").strip()
    if not objective:
        if args.mock:
            objective = MOCK_OBJECTIVE
        else:
            print("Ошибка: задайте --objective или --objective-file", file=sys.stderr)
            return 2

    workspace = Workspace(args.workspace)

    if args.mock:
        agents = {
            "generator": MockGenerator(),
            "refiner": MockRefiner(),
            "reviewer": MockReviewer(),
        }
        pipeline = load_pipeline(args.pipeline) if args.pipeline else mock_pipeline()
    else:
        agents = {
            "gemini": GeminiAgent(model=args.gemini_model),
            "claude_code": ClaudeCodeAgent(
                model=args.claude_model,
                claude_cmd=args.claude_cmd,
                permission_mode=args.claude_permission_mode,
                max_turns=args.claude_max_turns,
                bare=args.claude_bare,
            ),
        }
        pipeline = load_pipeline(args.pipeline) if args.pipeline else default_pipeline()

    orchestrator = Orchestrator(
        workspace=workspace,
        agents=agents,
        pipeline=pipeline,
        max_iterations=args.max_iterations,
        test_command=args.test_command,
    )
    report = orchestrator.run(objective)
    return 0 if report.success else 1


if __name__ == "__main__":
    sys.exit(main())
