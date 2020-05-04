#!/bin/bash
NAME=checkitbaby

PYTHONPATH=$PYTHONPATH:/home/cgustave/github/python/packages/checkitbaby/venv/lib/python3.7/site-packages

echo "***" > debug.log
echo "" >> debug.log

echo
echo "======================================================================"
echo "= PYTHON code analysis                                               ="
echo "======================================================================"
pyflakes3 "$NAME".py
echo

echo "======================================================================"
echo "= PEP 8 codestyle check                                              ="
echo "======================================================================"
pycodestyle "$NAME".py --statistics
echo

echo "======================================================================"
echo "= UNIT TESTS                                                         ="
echo "======================================================================"
python3 -m coverage run --rcfile tests/coveragerc  tests/test_"$NAME".py

echo
echo "======================================================================"
echo "= COVERAGE                                                           ="
echo "======================================================================"
python3 -m coverage report --show-missing
echo

echo "======================================================================"
echo "= DOCUMENTATION                                                      ="
echo "======================================================================"
python3 -m pydoc "$NAME"  > README.md

echo "" >> debug.log