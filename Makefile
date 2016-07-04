SPHINX_INSTALLED=$(shell pip list | grep "Sphinx" -c)
RTD_INSTALLED=$(shell pip list | grep "sphinx-rtd-theme" -c)

all:
	@echo SPHINX IS  ${SPHINX_INSTALLED}

.PHONY: test
test:
	python tests/doctests.py

.PHONY: install
install:
	pip install -r requirements.txt
	pip install .

.PHONY: doc
doc:
	@if [ ! ${SPHINX_INSTALLED} -eq 1 ]; then pip install Sphinx; fi
	@if [ ! ${RTD_INSTALLED} -eq 1 ]; then pip install sphinx-rtd-theme; fi
	cd docs && make html
	${BROWSER} docs/build/html/index.html

.PHONY: clean
.SILENT: clean
clean:
	if [ -d build ]; then rm -rd build; fi
	if [ -d dist ]; then rm -rd dist; fi
	rm -rf docs/build/*
	if [ -d pronto.egg-info ]; then rm -rf pronto.egg-info/; fi
	echo "Done cleaning."
