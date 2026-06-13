# AI-оркестратор: совместная разработка несколькими LLM

Многомодельный оркестратор для автоматизированной разработки: координирует **Gemini** (режим `api`) и **Claude Code** (режим `filesystem`) через общее рабочее пространство с git-версионированием на каждый шаг.

**Зависимостей нет** — только Python ≥ 3.10 и `git` в `PATH`. Для боевого запуска дополнительно нужны Claude Code CLI и ключ Gemini.

## Установка

```bash
git clone <repo-url>
cd ai-orchestrator
pip install -e .            # опционально; иначе — python -m orchestrator.cli
```

Claude Code CLI (для filesystem-агента): `npm install -g @anthropic-ai/claude-code` + авторизация.
Ключ Gemini (для api-агента): `export GEMINI_API_KEY="..."` или строкой в `.env` (см. [.env.example](.env.example)).

## Быстрый старт

**1. Офлайн-прогон контура** — без ключей и CLI, проверяет, что весь конвейер работает:

```bash
python -m orchestrator.cli --workspace ./demo-mock --mock --verbose
```

Результат: в `./demo-mock/` появится git-история всех шагов (generate → refine → тесты → review). Если она есть — контур исправен.

**2. Проверка ключа Gemini** (если планируете боевой запуск):

```bash
python -m scripts.check_gemini_key            # успех: [OK] Ключ рабочий. Ответ модели: 'Pong'
```

Типичные ошибки: `Ключ не найден` → не задан `GEMINI_API_KEY`; `API_KEY_INVALID` → неверный ключ; `HTTP 403` → не включён Generative Language API; `HTTP 429` → исчерпана квота.

**3. Реальный проект:**

```bash
python -m orchestrator.cli \
    --workspace ./my-project \
    --objective "REST API списка задач на FastAPI с тестами" \
    --test-command "python -m pytest -q" \
    --max-iterations 4 --verbose
```

### Основные опции

| Опция | Назначение | По умолчанию |
|---|---|---|
| `--workspace` | каталог проекта (создаётся, если нет) | — |
| `--objective` / `--objective-file` | задача текстом или из файла | — |
| `--test-command` | команда тестов между итерациями | нет |
| `--max-iterations` | лимит итераций | `3` |
| `--pipeline` | свой JSON-конвейер вместо стандартного | стандартный |
| `--gemini-model` | модель Gemini | `gemini-2.5-flash` |
| `--claude-model` | модель Claude Code | его собственная |
| `--claude-permission-mode` | режим прав Claude Code | `acceptEdits` |
| `--mock` | офлайн-агенты без ключей и CLI | выкл. |

`python -m orchestrator.cli --help` — полный список.

## Ограничения и безопасность

- **Workspace = песочница:** Claude Code и команда тестов исполняют код в каталоге. Для недоверенных задач запускайте в контейнере/VM.
- Пути из манифестов жёстко валидируются (без `..`, абсолютных путей и записи в `.git`/`.orchestrator`); основная линия контроля качества — ревью-шаг и тесты.
- Флаги Claude Code CLI могут меняться между версиями — сверяйтесь с `claude --help`.

Подробнее — в [ARCHITECTURE.md](ARCHITECTURE.md#безопасность).

## Дальше

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — архитектура и диаграммы, протокол обмена, версионирование, цикл выполнения, свой конвейер, добавление новой модели.
- **[EXAMPLES.md](EXAMPLES.md)** — готовые команды (FastAPI TODO, Fibonacci, Click CLI), офлайн-демо, варианты для Bash и PowerShell.
