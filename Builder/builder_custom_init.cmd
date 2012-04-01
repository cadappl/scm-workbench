rem figure out where we are
for %%I in ( %0\..\.. ) do set WORKDIR=%%~fI

set PY_MAJ=2
if not "%1" == "" set PY_MAJ=%1

set PY_MIN=7
if not "%2" == "" set PY_MIN=%2

if not "%3" == "" set SVN_VER_MAJ_MIN=%3
if "%SVN_VER_MAJ_MIN%" == "" set /p SVN_VER_MAJ_MIN="Build against Subversion Version [maj.min]: "
if "%SVN_VER_MAJ_MIN%" == "" goto :eof

rem Save CWD
pushd .

rem in development the version info can be found
rem otherwise the builder will have run it already
set COMPILER=msvc71
if "%PY_MAJ%.%PY_MIN%" == "2.4" set COMPILER=msvc71
if "%PY_MAJ%.%PY_MIN%" == "2.5" set COMPILER=msvc71
if "%PY_MAJ%.%PY_MIN%" == "2.6" set COMPILER=msvc90
if "%PY_MAJ%.%PY_MIN%" == "2.7" set COMPILER=msvc90
if "%PY_MAJ%.%PY_MIN%" == "3.0" set COMPILER=msvc90
if "%PY_MAJ%.%PY_MIN%" == "3.1" set COMPILER=msvc90
if "%PY_MAJ%.%PY_MIN%" == "3.2" set COMPILER=msvc90

if exist ..\..\ReleaseEngineering\win32-%COMPILER%\software-versions-%SVN_VER_MAJ_MIN%.cmd (
    pushd ..\..\ReleaseEngineering\win32-%COMPILER%
    call software-versions-%SVN_VER_MAJ_MIN%.cmd off
    popd
    )

rem see if there is a built pysvn
if not "%TARGET%" == "" set PYSVN_PYTHONPATH=%TARGET%\py%PY_MAJ%%PY_MIN%_pysvn\Source
if not "%TARGET%" == "" set PYTHONPATH=%PYSVN_PYTHONPATH%;%WORKDIR%\Source
if "%TARGET%" == "" set PYTHONPATH=%WORKDIR%\Source

echo PYTHONPATH %PYTHONPATH%

set MEINC_INSTALLER_DIR=%WORKDIR%\Import\MEINC_Installer-%MEINC_INSTALLER_VER%-py%PY_MAJ%%PY_MIN%-win32
set INCLUDE=%MEINC_INSTALLER_DIR%;%INCLUDE%

set PY=c:\python%PY_MAJ%%PY_MIN%.win32
if not exist %PY%\python.exe set PY=c:\python%PY_MAJ%%PY_MIN%

set PYTHON=%PY%\python.exe

rem Need python and SVN on the path
PATH %PY%;%SVN_BIN%;c:\UnxUtils;%PATH%

%PYTHON% -c "import sys;print 'Info: Python Version',sys.version"
%PYTHON% -c "import pysvn;print 'Info: pysvn Version',pysvn.version,'svn version',pysvn.svn_version"
popd
