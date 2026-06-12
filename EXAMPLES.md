# Примеры запуска AI-Orchestrator

## 1. FastAPI TODO List

```bash
python -m orchestrator.cli \
    --workspace ./demo-todo \
    --objective "Создай FastAPI приложение с REST API для управления TODO-списком. Endpoints: GET /todos, POST /todos, PUT /todos/{id}, DELETE /todos/{id}. Используй Pydantic для моделей. Напиши тесты с pytest." \
    --test-command "python -m pytest -v" \
    --max-iterations 4
```

## 2. Python Fibonacci модуль

```bash
python -m orchestrator.cli \
    --workspace ./demo-math \
    --objective "Создай Python-модуль с функцией fibonacci(n). Добавь юнит-тесты." \
    --test-command "python -m pytest tests/ -q" \
    --max-iterations 3
```

## 3. Click CLI утилита

```bash
python -m orchestrator.cli \
    --workspace ./demo-cli \
    --objective "Создай CLI-утилиту на Click для конвертации текста: --uppercase, --lowercase, --reverse. Добавь help и тесты." \
    --test-command "python -m pytest -q" \
    --max-iterations 3
```

## 4. Офлайн демо (без API ключей)

```bash
python -m orchestrator.cli \
    --workspace ./demo-mock \
    --objective "Создай простой REST API" \
    --mock \
    --verbose
```

## 5. Проверка Gemini ключа

```bash
python -m scripts.check_gemini_key
python -m scripts.check_gemini_key --model gemini-2.5-pro
```

## PowerShell на Windows

**Важно:** используй бэккик `` ` `` для переноса строк (не `\`):

```powershell
python -m orchestrator.cli `
    --workspace ./demo-todo `
    --objective "Создай FastAPI приложение с REST API для управления TODO-списком. Endpoints: GET /todos, POST /todos, PUT /todos/{id}, DELETE /todos/{id}. Используй Pydantic для моделей. Напиши тесты с pytest." `
    --test-command "python -m pytest -v" `
    --max-iterations 4
```

Или как одну строку:

```powershell
python -m orchestrator.cli --workspace ./demo-todo --objective "Создай FastAPI приложение с REST API для управления TODO-списком" --test-command "python -m pytest -v" --max-iterations 4
```