# Andy Sayler
# 2015

ECHO = @echo

PYTHON2 = python2
PIP2 = pip2
PYTHON3 = python3
PIP3 = pip3

REQUIRMENTS = requirments.txt

UNITTEST_PATTERN = '*_test.py'

.PHONY: all reqs2 reqs3 test2 test3 clean

all:
	$(ECHO) "This is a python project; nothing to build!"

reqs2:
	$(PIP2) install -r $(REQUIRMENTS) -U

reqs3:
	$(PIP3) install -r $(REQUIRMENTS) -U

test2:
	$(PYTHON2) -m unittest discover -v -p $(UNITTEST_PATTERN)

test3:
	$(PYTHON3) -m unittest discover -v -p $(UNITTEST_PATTERN)

clean:
	$(RM) *.pyc
	$(RM) *~
