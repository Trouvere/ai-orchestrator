# AI-оркестратор: совместная разработка несколькими LLM

Многомодельный оркестратор для автоматизированной разработки: координирует Gemini и Claude Code через общее рабочее пространство с git-версионированием.

**Зависимостей нет** — только Python ≥ 3.10 и `git`.

## 📋 Оглавление

- [Быстрый старт](#быстрый-старт)
- [Требования](#требования)
- [Установка](#установка)
- [Первый запуск](#первый-запуск)
- [Ограничения и безопасность](#ограничения-и-безопасность)
- [Подробно](#подробно)

## 🚀 Быстрый старт

### 1. Проверь окружение
```bash
python --version          # Python 3.10+
git --version            # Git установлен
claude --version         # Claude Code CLI (установи: npm install -g @anthropic-ai/claude-code)
```

### 2. Запусти мок (без API ключей)
```bash
python -m orchestrator.cli \
    --workspace ./demo-mock \
    --mock \
    --verbose
```

**Результат:** полная git-история всех шагов в `./demo-mock/` — значит всё работает ✓

### 3. Готово!
```bash
# Твой первый реальный проект
python -m orchestrator.cli \
    --workspace ./my-project \
    --objective "Создай REST API для TODO на FastAPI" \
    --test-command "python -m pytest -q" \
    --max-iterations 4
```

---

## 📋 Требования

- **Python** ≥ 3.10
- **Git** (установлен в PATH)
- **Claude Code CLI**: `npm install -g @anthropic-ai/claude-code` + авторизация
- **Gemini API ключ** (для шагов с Gemini):
  ```bash
  export GEMINI_API_KEY="..."   # или в .env файл
  ```

---

## 📦 Установка

```bash
# Склонируй репо
git clone <repo-url>
cd ai-orchestrator

# Опционально: установи для удобства
pip install -e .

# Или запускай напрямую
python -m orchestrator.cli --help
```

Никаких других зависимостей — только стандартная Python библиотека.

---

## 🔧 Первый запуск

### Этап 1️⃣: Проверка окружения (2 мин)

```bash
# Python и Git
python --version
git --version

# Claude Code
claude --version

# Gemini API ключ (если планируешь использовать Gemini)
python -m scripts.check_gemini_key
```

Если всё зелёно — переходи к этапу 2.

### Этап 2️⃣: Офлайн-тест контура (мок, без ключей, 3 мин)

```bash
python -m orchestrator.cli \
    --workspace ./test-mock \
    --mock \
    --verbose
```

**Что должно произойти:**
- ✓ Мок создаст файлы проекта
- ✓ Мок улучшит код
- ✓ Тесты запустятся
- ✓ Мок ревьюер проверит, может вернуть замечания
- ✓ Возможны 1-2 итерации до `approved`

**Результат:** в `./test-mock` полная git-история. Если успешно — весь контур работает.

### Этап 3️⃣: Проверка Gemini API (если планируешь)

```bash
python -m scripts.check_gemini_key

# или конкретная модель
python -m scripts.check_gemini_key --model gemini-2.5-pro
```

**Успех:** `[OK] Ключ рабочий. Ответ модели: 'Pong'`

**Ошибки:**
- `Ключ не найден` → установи `GEMINI_API_KEY` в окружение или `.env`
- `API_KEY_INVALID` → неправильный ключ
- `HTTP 403` → включи Generative Language API в Google Cloud
- `HTTP 429` → квота исчерпана

### Этап 4️⃣: Первый реальный проект

```bash
python -m orchestrator.cli \
    --workspace ./my-project \
    --objective "REST API списка задач на FastAPI с тестами" \
    --test-command "python -m pytest -q" \
    --max-iterations 4 \
    --verbose
```

**Опции:**
- `--gemini-model` (default: `gemini-2.5-pro`)
- `--claude-model` (выбирается автоматически)
- `--claude-permission-mode` (default: `acceptEdits`)
- `--pipeline` (свой конвейер вместо стандартного)
- `--objective-file` (если цель в файле)

---

## ⚠️ Ограничения и безопасность

- **Workspace как песочница:** Claude Code и команда тестов исполняют код в каталоге. Для недоверенных задач используй контейнер/VM.
- **Валидация путей:** абсолютные пути, `..`, запись в `.git` и `.orchestrator` запрещены.
- **Контроль качества:** основная линия — ревью-шаг и тесты (не блокируй их).
- **Версии CLI:** флаги Claude Code могут меняться — смотри `claude --help`.
- **Лимиты контекста:** большие файлы усекаются; используй `files` для ограничения контекста.

---

## 📖 Подробно

- **[ARCHITECTURE.md](ARCHITECTURE.md)**
  - Архитектура и диаграммы системы
  - Протокол обмена (Gemini API vs Claude Code filesystem)
  - Версионирование через git-коммиты
  - Цикл выполнения конвейера и логика завершения
  - **Свой конвейер** — создание JSON-конвейера
  - **Расширение** — интеграция новой AI-модели
  - Ограничения безопасности
  
- **[EXAMPLES.md](EXAMPLES.md)**
  - Примеры команд: FastAPI TODO, Fibonacci, Click CLI
  - Офлайн-демо (без API ключей и CLI)
  - Варианты для Bash и PowerShell
