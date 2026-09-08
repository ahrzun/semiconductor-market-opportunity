# Pipeline entry points. Every target is safe to re-run; scripts are idempotent.
PYTHON ?= python3

.PHONY: all data score db excel deck clean

all: data score db excel deck

data:
	$(PYTHON) src/generate_data.py
	$(PYTHON) src/clean.py

score:
	$(PYTHON) src/score.py
	$(PYTHON) src/sensitivity.py

# load_sqlite.py also executes the seven analytical queries and refreshes sql/RESULTS.md,
# so the committed query output can never drift from the committed data.
db:
	$(PYTHON) src/load_sqlite.py

excel:
	$(PYTHON) src/build_excel.py

deck:
	$(PYTHON) src/build_deck.py

clean:
	rm -f data/raw/*.csv data/processed/*.csv db/market.db excel/*.xlsx presentation/*.pptx
	rm -rf src/__pycache__
