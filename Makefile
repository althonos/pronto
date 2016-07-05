TOKEN=`cat ./.codacy.token`

.PHONY: test
test:
	python3 tests/doctests.py -v

.PHONY: cover
.SILENT: cover
cover:
	coverage run tests/doctests.py --source pronto
	coverage xml
	export CODACY_PROJECT_TOKEN=${TOKEN} && python-codacy-coverage -r coverage.xml --source pronto

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
	rm -f ./*.whl
	if [ -f coverage.xml ]; then rm coverage.xml; fi
	echo "Done cleaning."

.PHONY: upload
upload:
	@python3 setup.py sdist upload
	@python3 setup.py bdist_wheel upload
