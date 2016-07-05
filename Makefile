#coverage run tests/doctests.py --source pronto
#coverage xml --include 'pronto/*'

TOKEN=`cat ./.codacy.token`
PROFILE_FUNC="import pstats as p; f=open('profile.txt', 'w'); p.Stats('p.tmp',stream=f).print_stats()"

.PHONY: test
test:
	python tests/doctests.py -v

.PHONY: profile
.SILENT: profile
profile:
	python -m cProfile -o '../p.tmp' -s 'cumulative' tests/doctests.py
	echo "Converting profile..."
	python -c ${PROFILE_FUNC}
	echo "Cleaning..."
	rm ./p.tmp


.PHONY: cover
.SILENT: cover
ifndef CODACY_PROJECT_TOKEN
cover:
	coverage run tests/doctests.py --source pronto
	coverage xml --include 'pronto/*'
	export CODACY_PROJECT_TOKEN=${TOKEN} && python-codacy-coverage -r coverage.xml
else
cover:
	coverage run tests/doctests.py --source pronto
	coverage xml --include 'pronto/*'
	python-codacy-coverage -r coverage.xml
endif


.PHONY: install
install:
	pip install -r requirements.txt
	pip install .

.PHONY: doc
.SILENT: doc
doc:
	pip install -r requirements-doc.txt -q
	echo $$TARGET
	cd docs && make $(filter-out $@,$(MAKECMDGOALS))
	
.PHONY: clean
.SILENT: clean
clean:
	if [ -d build ]; then rm -rd build; fi
	if [ -d dist ]; then rm -rd dist; fi
	rm -rf docs/build/*
	rm -rf tests/run
	if [ -d pronto.egg-info ]; then rm -rf pronto.egg-info/; fi
	rm -f ./*.whl
	if [ -f coverage.xml ]; then rm coverage.xml; fi
	if [ -f profile.txt ]; then rm profile.txt; fi
	echo "Done cleaning."

.PHONY: upload
upload:
	@python setup.py sdist upload
	@python setup.py bdist_wheel upload

# targets of Sphinx makefile
.PHONY: html xml pdf dirhtml singlehtml pickle json htmlhelp
.PHONY: qthelp applehelp devhelp epub epub3 latex latexpdf
.PHONY: latexpdfja text man texinfo info gettext changes
.PHONY: pseudoxml linkcheck doctest coverage dummy

# open browser after html generation
html:
	${BROWSER} docs/build/html/index.html

ifdef EDITOR
coverage:
	${EDITOR} docs/build/coverage/python.txt
endif
