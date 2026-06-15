#!/bin/bash
# Pre-commit hook - run lint, typecheck, and tests before committing

set -e

echo "Running pre-commit checks..."

echo "=== Linting Python backend ==="
cd backend && ruff check . && echo "PASS" || { echo "FAIL: ruff check failed"; exit 1; }

echo "=== Checking Python format ==="
cd backend && ruff format --check . && echo "PASS" || { echo "FAIL: ruff format check failed"; exit 1; }

echo "=== Type checking Python backend ==="
cd backend && mypy app/ --config-file pyproject.toml && echo "PASS" || { echo "FAIL: mypy failed"; exit 1; }

cd ..

echo "=== Linting frontend ==="
cd frontend && npm run lint && echo "PASS" || { echo "FAIL: ESLint failed"; exit 1; }

echo "=== Type checking frontend ==="
cd frontend && npx tsc -b && echo "PASS" || { echo "FAIL: TypeScript check failed"; exit 1; }

echo "=== Running frontend tests ==="
cd frontend && npm run test -- --run && echo "PASS" || { echo "FAIL: Tests failed"; exit 1; }

echo ""
echo "All pre-commit checks passed!"