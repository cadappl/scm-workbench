build: all test kit

all:
	cd ..\Source && $(MAKE) -f win32.mak all

clean:
	cd ..\Source && $(MAKE) -f win32.mak clean
	cd ..\kit\Win32 && $(MAKE) -f win32.mak clean

kit:
	cd ..\kit\Win32 && $(MAKE) -f win32.mak all

install:
	..\kit\Win32\tmp\output\setup.exe

test:
