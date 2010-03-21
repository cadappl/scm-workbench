#!/bin/sh
set -e
STARTDIR=$(pwd)
cd ../../Source
make -f macosx.mak clean all
cd $STARTDIR

${PYTHON} -u make_pkg.py
