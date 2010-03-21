#!/bin/sh
export PYSVN_WORKBENCH_STDOUT_LOG=$(tty)
if [ "$PYTHONPATH" = "" ]
then
	export PYTHONPATH=${WORKDIR}/Source
else
	export PYTHONPATH=${WORKDIR}/Source:$PYTHONPATH
fi

PYTHON=${PYTHON:-python}
BASENAME=$( basename ${PYTHON} )
SUFFIX=${X#python*}
DIRNAME=$( dirname ${PYTHON} )

if [ "${DIRNAME}" != "" ]
then
    DIRNAME=${DIRNAME}/
fi
PYTHONW=${DIRNAME}pythonw${SUFFIX}

if [ -e ${PYTHONW} ]
then
    ${PYTHONW} wb_main.py $*
else
    ${PYTHON} wb_main.py $*
fi
