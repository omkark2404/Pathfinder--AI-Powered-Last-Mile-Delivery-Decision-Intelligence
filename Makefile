.PHONY: help test eval eval-full

help:
	@echo "Available targets:"
	@echo "  test       - Run the backend test suite"
	@echo "  eval       - Cross-validate both models on the data in data/ (writes docs/eval_results.json)"
	@echo "  eval-full  - Instructions for evaluating on the full public datasets"

test:
	cd backend && DATABASE_URL="" pytest -q

eval:
	cd backend && DATABASE_URL="" python scripts/train_eval.py

eval-full:
	@echo "1. Download the full Amazon Last Mile dataset (CC BY-NC 4.0) from"
	@echo "   https://registry.opendata.aws/amazon-last-mile-challenges/ and save the route data as data/amazon_last_mile.json"
	@echo "2. Download the Mendeley planned-vs-actual dataset (DOI 10.17632/kkwgfvmtxn.1)"
	@echo "   and save it as data/mendeley_planned_vs_actual.csv (check the adapter's column mapping first)"
	@echo "3. Run: make eval"
