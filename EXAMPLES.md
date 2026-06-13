# Примеры запуска AI-Orchestrator

## 1. FastAPI TODO List

### Bash / Linux / macOS / Git Bash

```bash
python -m orchestrator.cli \
    --workspace ./workspaces/todo \
    --objective "Создай FastAPI приложение с REST API для управления TODO-списком. Endpoints: GET /todos, POST /todos, PUT /todos/{id}, DELETE /todos/{id}. Используй Pydantic для моделей. Напиши тесты с pytest." \
    --test-command "python -m pytest -v" \
    --max-iterations 4
```

### PowerShell (Windows)

```powershell
python -m orchestrator.cli `
    --workspace ./workspaces/todo `
    --objective "Создай FastAPI приложение с REST API для управления TODO-списком. Endpoints: GET /todos, POST /todos, PUT /todos/{id}, DELETE /todos/{id}. Используй Pydantic для моделей. Напиши тесты с pytest." `
    --test-command "python -m pytest -v" `
    --max-iterations 4
```

### PowerShell (одна строка)

```powershell
python -m orchestrator.cli --workspace ./workspaces/todo --objective "Создай FastAPI приложение с REST API для управления TODO-списком" --test-command "python -m pytest -v" --max-iterations 4
```

---

## 2. Python Fibonacci модуль

### Bash / Linux / macOS / Git Bash

```bash
python -m orchestrator.cli \
    --workspace ./workspaces/math \
    --objective "Создай Python-модуль с функцией fibonacci(n). Добавь юнит-тесты." \
    --test-command "python -m pytest tests/ -q" \
    --max-iterations 3
```

### PowerShell (Windows)

```powershell
python -m orchestrator.cli `
    --workspace ./workspaces/math `
    --objective "Создай Python-модуль с функцией fibonacci(n). Добавь юнит-тесты." `
    --test-command "python -m pytest tests/ -q" `
    --max-iterations 3
```

---

## 3. Click CLI утилита

### Bash / Linux / macOS / Git Bash

```bash
python -m orchestrator.cli \
    --workspace ./workspaces/cli \
    --objective "Создай CLI-утилиту на Click для конвертации текста: --uppercase, --lowercase, --reverse. Добавь help и тесты." \
    --test-command "python -m pytest -q" \
    --max-iterations 3
```

### PowerShell (Windows)

```powershell
python -m orchestrator.cli `
    --workspace ./workspaces/cli `
    --objective "Создай CLI-утилиту на Click для конвертации текста: --uppercase, --lowercase, --reverse. Добавь help и тесты." `
    --test-command "python -m pytest -q" `
    --max-iterations 3
```

---

## 4. Офлайн демо (без API ключей)

### Bash / Linux / macOS / Git Bash

```bash
python -m orchestrator.cli \
    --workspace ./workspaces/mock \
    --objective "Создай простой REST API" \
    --mock \
    --verbose
```

### PowerShell (Windows)

```powershell
python -m orchestrator.cli `
    --workspace ./workspaces/mock `
    --objective "Создай простой REST API" `
    --mock `
    --verbose
```

---

## 5. Проверка Gemini ключа

### Bash / Linux / macOS / Git Bash

```bash
python -m scripts.check_gemini_key
python -m scripts.check_gemini_key --model gemini-2.5-pro
```

### PowerShell (Windows)

```powershell
python -m scripts.check_gemini_key
python -m scripts.check_gemini_key --model gemini-2.5-pro
```

---

## Справка: символы переноса строк по оболочкам

| Оболочка | Символ | Пример |
|----------|--------|--------|
| **Bash** | `\` (обратный слеш) | `command \` |
| **PowerShell** | `` ` `` (бэккик) | ``command ` `` |
| **Cmd** (Windows) | `^` (каретка) | `command ^` |

**Правило:**
- На **Linux/macOS** → используй `\`
- На **Windows в PowerShell** → используй `` ` ``
- На **Windows в Cmd** → используй `^`
- В **Git Bash на Windows** → используй `\` (Bash!)
