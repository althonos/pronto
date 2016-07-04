#SPHINX_INSTALLED=$(shell pip list | grep "Sphinx" -c)
#RTD_INSTALLED=$(shell pip list | grep "sphinx-rtd-theme" -c)
#@while read DEP; do echo if [ ! $( eval $(shell pip list | grep ${DEP} -c)) -eq 1 ]; then pip install ${DEP}; fi; end < requirements-doc.txt

INSTALLED = $(eval pip list | grep $$DEP -c | echo $$DEP)

.PHONY: test
test:
	python tests/doctests.py -v

.PHONY: install
install:
	pip install -r requirements.txt
	pip install .

.PHONY: doc
doc:
	@pip install -r requirements-doc.txt -q
	@cd docs && make html
	${BROWSER} docs/build/html/index.html

.PHONY: clean
.SILENT: clean
clean:
	if [ -d build ]; then rm -rd build; fi
	if [ -d dist ]; then rm -rd dist; fi
	rm -rf docs/build/*
	if [ -d pronto.egg-info ]; then rm -rf pronto.egg-info/; fi
	rm ./*.whl
	echo "Done cleaning."

.PHONY: upload
upload:
	@python3 setup.py sdist upload
	@python3 setup.py bdist_wheel upload