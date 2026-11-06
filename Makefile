PYTHON ?= .venv/bin/python

.PHONY: install download test analysis notebook

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -e .

download:
	$(PYTHON) scripts/download_hbedb.py

test:
	$(PYTHON) -m pytest

analysis:
	$(PYTHON) scripts/run_analysis.py

notebook:
	$(PYTHON) -m jupyter nbconvert --to notebook --execute --inplace notebooks/vision_surface_postural_sway.ipynb
