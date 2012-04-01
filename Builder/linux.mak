build: all kit

all: workbench

workbench: meinc_installer
	cd ../Source && $(MAKE) -f linux.mak build_bin

# build the launcher
# but get ride of the config.dat that is created as it
# prevent correct creation of a usable config.dat
meinc_installer:
	cd ../Import/MEINC_Installer/source/linux && $(PYTHON) Make.py && $(MAKE) && rm -f ../../config.dat

clean:
	find .. -name '*.pyc' -exec rm {} ';'
	cd ../Source && $(MAKE) -f linux.mak clean
	cd ../Kit/Linux && rm -rf tmp
	cd ../Import/MEINC_Installer/source/linux && $(MAKE) clean
	rm -f ../Import/MEINC_Installer/support/run*
	rm -f ../Import/MEINC_Installer/config.dat

kit:
	cd ../Kit/Linux && $(PYTHON) make_rpm.py

install:

test:
