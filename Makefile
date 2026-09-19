.PHONY: bootstrap build verify test

PYTHON ?= python3

bootstrap:
	$(PYTHON) scripts/manage_db.py bootstrap

build: bootstrap
	$(PYTHON) scripts/manage_db.py build

verify: bootstrap
	$(PYTHON) scripts/validate_json.py
	$(PYTHON) scripts/manage_db.py verify

test:
	$(PYTHON) -m unittest discover -s tests -v
