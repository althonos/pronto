.PHONY: test
test:
	python tests/doctests.py

.PHONY: install
install:
	pip install -r requirements.txt
	pip install .

.PHONY: doc
doc:
	pip install Sphinx sphinx-rtd-theme
	cd docs && make html
	${BROWSER} docs/build/html/index.html

.PHONY: clean
.SILENT: clean
clean:
	if [ -d build ]; then rm -rd build; fi
	if [ -d dist ]; then rm -rd dist; fi
	rm -rf docs/build/*
	if [ -d pronto.egg.info ]; then rm -rf pronto.egg-info/; fi
	echo "Done cleaning."
