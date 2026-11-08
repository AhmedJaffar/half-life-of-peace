.PHONY: all setup data analysis paper figures clean check

PY := .venv/bin/python

## One-command reproduction from a clean clone
all: setup data analysis paper check

setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

## Download and build all datasets (idempotent, resumable)
data:
	$(PY) scripts/run_all.py --stage data

## All statistics, robustness checks, tables
analysis:
	$(PY) scripts/run_all.py --stage analysis

## All figures
figures:
	$(PY) scripts/run_all.py --stage figures

## Build the manuscript PDF
paper:
	$(PY) scripts/run_all.py --stage paper

## Verify every claim in the paper traces to analysis/results.json
check:
	$(PY) scripts/verify_claims.py

clean:
	rm -rf data/raw data/processed analysis/tables figures/*.png figures/*.pdf
