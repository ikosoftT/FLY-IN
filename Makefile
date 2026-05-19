# =========================
# Fly-In Project Makefile
# =========================

PYTHON := python3
PIP := python3 -m pip

MAP ?= maps/easy/01_linear_path.txt



install:
	$(PIP) install -r requirements.txt



run:
	$(PYTHON) main.py $(MAP)


debug:
	$(PYTHON) -m pdb main.py $(MAP)



clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete



lint:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs



lint-strict:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict




help:
	@echo "Available targets:"
	@echo "  install       Install dependencies"
	@echo "  run           Run simulation (MAP=$(MAP))"
	@echo "  debug         Run with pdb"
	@echo "  clean         Remove cache files"
	@echo "  lint          Run flake8 + mypy (safe checks)"
	@echo "  lint-strict   Run full strict mypy checks"
	@echo "  help          Show this help"


.PHONY: install run debug clean lint lint-strict  help