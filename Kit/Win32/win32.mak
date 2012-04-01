all: kit

kit: workbench-branded.iss info_before.txt copy_setup.cmd
	copy ..\..\LICENSE.txt tmp\workbench_LICENSE.txt
	copy ..\..\Source\bin\wb.exe tmp\WorkBench.exe
	copy ..\..\Source\bin\wb.exe.manifest tmp\WorkBench.exe.manifest
	"c:\Program Files (x86)\Inno Setup 5\ISCC.exe" tmp\workbench-branded.iss
	tmp\setup_copy.cmd

info_before.txt: workbench-branded.iss

copy_setup.cmd: workbench-branded.iss

workbench-branded.iss: setup_version_handling.py workbench.iss
	if not exist tmp mkdir tmp
	python setup_version_handling.py

debug:
	"c:\Program Files (x86)\Inno Setup 5\Compil32.exe" workbench-branded.iss

clean:
	if exist tmp rmdir /s /q tmp
