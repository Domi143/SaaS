run:
\tuvicorn app.main:app --reload

lint:
\t@echo "No linter configured yet."

test:
\tpytest

db-up:
\tdocker-compose up -d db

db-down:
\tdocker-compose stop db

migrate:
\talembic upgrade head

revision:
\talembic revision -m "manual revision"

