.PHONY: format
format:
	poetry run ruff format
	poetry run ruff check

.PHONY: lint
lint:
	poetry run ruff check --exit-non-zero-on-fix --diff
	poetry run ruff format --check --diff
	poetry run flake8 .
	poetry run mypy app
	poetry run lint-imports

.PHONY: secretkey
secretkey:
		@poetry run python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
