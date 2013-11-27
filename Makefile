ENVDIR = ./env
PEP8 = $(ENVDIR)/bin/pep8
PIP = C_INCLUDE_PATH="/opt/local/include:/usr/local/include" $(ENVDIR)/bin/pip
PIPOPTS=$(patsubst %,-r %,$(wildcard $(HOME)/.requirements.pip requirements.pip))
PYTHON = $(ENVDIR)/bin/python
PYTHON_VERSION = python2.7
VIRTUALENV = virtualenv
VIRTUALENVOPTS = --python=$(PYTHON_VERSION)

help:
	@echo "make help     -- print this help"
	@echo "make generate -- regenerate the json"
	@echo "make update   -- upload the json and index.html to s3"

generate:
	python generate.py

update:
	s3cmd put index.html s3://wheelpackages/index.html  --cf-invalidate \
	--add-header='Cache-Control: max-age=30' \
	--add-header='Date: `date -u +"%a, %d %b %Y %H:%M:%S GMT"`'
	s3cmd put results.json s3://wheelpackages/results.json  --cf-invalidate \
	--add-header='Cache-Control: max-age=30' \
	--add-header='Date: `date -u +"%a, %d %b %Y %H:%M:%S GMT"`'

## Local Setup ##
.PHONY: requirements req virtualenv
requirements:
	@rm -f .req
	$(MAKE) .req

req: .req
.req: $(ENVDIR) requirements.pip
	$(PIP) install $(PIPOPTS)
	@touch .req

virtualenv: $(ENVDIR)
$(ENVDIR):
	$(VIRTUALENV) $(VIRTUALENVOPTS) $(ENVDIR)

## Housekeeping ##
.PHONY: mostlyclean clean distclean maintainer-clean
mostlyclean:
	@echo "Removing intermediate files"
	$(RM) RELEASE-VERSION .nose-stopwatch-times .tests.pylintrc pip-log.txt
	$(RM) -r dist disttest *.egg *.egg-info
	find . -type f -name '*.pyc' -delete

clean: mostlyclean
	@echo "Removing output files"
	$(RM) -r $(REPORTDIR) build
	$(RM) .coverage .req

distclean: clean
	@echo "Removing generated build artifacts"
	$(RM) -r doc/doctrees doc/html

maintainer-clean: distclean
	@echo "Removing all generated and downloaded files"
	$(RM) -r $(ENVDIR)
