# AGENTS.md

Навигация для AI-агента по этому репозиторию. Здесь **нет** пересказа документации — только
куда смотреть, что запускать и какие правила нельзя нарушать. За подробностями — по ссылкам.

## Что это

Многомодельный оркестратор разработки: координирует **Gemini** (режим `api`) и **Claude Code**
(режим `filesystem`) через общее рабочее пространство с git-версионированием на каждый шаг.
Чистый Python ≥ 3.10, **без внешних зависимостей**.

## Куда читать (не дублируй — открой нужное)

| Если ты работаешь с… | Открой |
|---|---|
| общим обзором, установкой, быстрым стартом | [README.md](README.md) |
| архитектурой, протоколом обмена, циклом выполнения, расширением новой моделью | [ARCHITECTURE.md](ARCHITECTURE.md) |
| примерами команд запуска (Bash + PowerShell) | [EXAMPLES.md](EXAMPLES.md) |
| форматом пользовательского конвейера | [examples/pipeline.example.json](examples/pipeline.example.json) |

## Карта кода (где что лежит)

| Меняешь… | Файл |
|---|---|
| CLI, аргументы, точку входа, загрузку `.env` | [orchestrator/cli.py](orchestrator/cli.py) |
| цикл итераций, запуск тестов, критерий завершения, журналы | [orchestrator/orchestrator.py](orchestrator/orchestrator.py) |
| формат `AgentResult`/`FileChange`, парсер манифеста, валидацию путей | [orchestrator/protocol.py](orchestrator/protocol.py) |
| файлы workspace, git-операции, экспорт контекста | [orchestrator/workspace.py](orchestrator/workspace.py) |
| стандартный конвейер (plan→implement→test→review), загрузку JSON-конвейера | [orchestrator/pipelines.py](orchestrator/pipelines.py) |
| базовый интерфейс агента и сборку промпта | [orchestrator/agents/base.py](orchestrator/agents/base.py) |
| адаптер Gemini (REST, JSON-ответ, ретраи) | [orchestrator/agents/gemini.py](orchestrator/agents/gemini.py) |
| адаптер Claude Code (headless CLI) | [orchestrator/agents/claude_code.py](orchestrator/agents/claude_code.py) |
| мок-агенты для офлайн-прогона | [orchestrator/agents/mock.py](orchestrator/agents/mock.py) |
| проверку ключа Gemini | [scripts/check_gemini_key.py](scripts/check_gemini_key.py) |

## Команды

```bash
# Офлайн-прогон контура без ключей и CLI (быстрая проверка, что ничего не сломал)
python -m orchestrator.cli --workspace ./demo-mock --mock --verbose

# Боевой запуск (нужны GEMINI_API_KEY и установленный Claude Code)
python -m orchestrator.cli --workspace ./my-project \
    --objective "..." --test-command "python -m pytest -q" --max-iterations 4

# Проверка ключа Gemini
python -m scripts.check_gemini_key
```

После любого изменения логики — **прогони `--mock`**: это сквозной тест всего контура.
Отдельного набора unit-тестов в репозитории нет.

## Инварианты — не нарушай

1. **Никаких внешних зависимостей.** `dependencies = []` в [pyproject.toml](pyproject.toml).
   Только стандартная библиотека (включая `urllib` вместо `requests`, свой мини-`load_dotenv`).
   Хочешь добавить пакет — сначала переспроси.
2. **Каждый шаг = git-коммит** вида `[iter N/role/agent] summary`. Не обходи `workspace.snapshot()`.
3. **Манифест возвращает полное содержимое файла, а не diff.** См. `MANIFEST_SCHEMA_HINT` в
   [protocol.py](orchestrator/protocol.py).
4. **Валидация путей обязательна.** Все пути из манифестов проходят `safe_rel_path()`: запрещены
   абсолютные пути, `..`, запись в `PROTECTED_DIRS` (`.git`, `.orchestrator`). Не ослабляй.
5. **`workspaces/` и `.orchestrator/` исключены из git** — это сгенерированные артефакты и
   demo-проекты со своими репозиториями. Не коммить их, не правь как исходники.
6. **`approved` при падающих тестах не принимается** — цикл продолжается. Логика завершения в
   `Orchestrator.run()`; не «упрощай» её.
7. **Сбой агента не должен терять журнал** — исключения агента ловятся и пишутся как `Status.ERROR`.

## Конфигурация

- Ключ Gemini: `GEMINI_API_KEY` (или `GOOGLE_API_KEY`), берётся из окружения или `.env`
  (реальное окружение в приоритете). См. [.env.example](.env.example).
- Дефолтная модель Gemini — `gemini-2.5-flash`, согласованно в двух местах: дефолт `--gemini-model`
  ([cli.py](orchestrator/cli.py)) и дефолт параметра `model` у класса `GeminiAgent`
  ([gemini.py](orchestrator/agents/gemini.py)). Меняешь — правь оба, чтобы не разъехались.

## Язык

Код, комментарии, докстринги и документация — **на русском**. Придерживайся стиля окружения.
