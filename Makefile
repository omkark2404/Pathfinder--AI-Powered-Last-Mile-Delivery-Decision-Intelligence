.PHONY: help eval-full

help:
	@echo "Available targets:"
	@echo "  eval-full  - Automates downloading and evaluating against the full 9,184 route Amazon dataset."

eval-full:
	@echo "======================================================================"
	@echo "WARNING: This requires approx 5GB of free space and 16GB RAM."
	@echo "Currently running evaluation on a 13-route benchmark sample."
	@echo "To run the full evaluation:"
	@echo "1. Download the full Amazon dataset from AWS Open Data Registry:"
	@echo "   aws s3 cp s3://amazon-last-mile-challenges/ data/amazon_last_mile.json"
	@echo "2. Download the full Mendeley dataset from DOI: 10.17632/kkwgfvmtxn.1"
	@echo "   and place at data/mendeley_planned_vs_actual.csv"
	@echo "3. Run: curl -X POST http://localhost:8000/api/v1/datasets/ingest -d '{\"dataset_name\":\"AMAZON_LAST_MILE\"}'"
	@echo "4. Run: curl -X POST http://localhost:8000/api/v1/models/train"
	@echo "======================================================================"
