#!/bin/echo Usage: . $0
export WORKDIR=$(cd ..;pwd)

# default to highest version we can find if no value in $1 and $2
if [ ! -z "$1" ]
then
    PREF_VER=$1.$2
else
    if [ "$(uname)" = "Darwin" ]
    then
        # default to 2.3 on Mac OS X
        PREF_VER=2.7
    else
        PREF_VER=
    fi
fi
for PY_VER in ${PREF_VER} 2.7 2.6 2.5
do
    # used in pick python to use in Builder driver makefile
    export PYTHON=$( which python${PY_VER} )
    if [ -e "${PYTHON}" ]
    then
        PYSVN_PY_VER=${PY_VER%.*}${PY_VER#*.}
        break
    fi
done
unset PREF_VER

if [ "$WC_SVNVERSION" = "" ]
then
    export WC_SVNVERSION=svnversion
fi

export MEINC_INSTALLER_DIR=${WORKDIR}/Import/MEINC_Installer
for _DIR in ${WORKDIR}/../Extension/Source ${WORKDIR}/../py${PYSVN_PY_VER}_pysvn_python_org//Source
do
    if [ -e "${_DIR}" ]
    then
        export PYTHONPATH=$(cd ${_DIR};pwd)
        export PYSVNLIB=$(cd ${_DIR};pwd)
    fi
done
unset _DIR
${PYTHON} -c "import sys;print 'Info: Python Version %r' % sys.version"
${PYTHON} -c "import pysvn;print 'Info: pysvn Version',pysvn.version"
${PYTHON} -c "import pysvn;print 'Info: svn version',pysvn.svn_version"
