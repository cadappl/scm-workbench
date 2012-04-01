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
SUFFIX=${BASENAME#python*}
DIRNAME=$( dirname ${PYTHON} )

if [ "${DIRNAME}" != "" ]
then
    DIRNAME=${DIRNAME}/
fi
PYTHONW=${DIRNAME}pythonw${SUFFIX}

if [ -e /System/Library/CoreServices/SystemVersion.plist ]
then
    ARCH_CMD="arch -i386"
fi

if [ -e ${PYTHONW} ]
then
    ${ARCH_CMD} ${PYTHONW} wb_main.py $*
else
    ${ARCH_CMD} ${PYTHON} wb_main.py $*
fi
