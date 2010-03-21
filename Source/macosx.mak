#
#	Mac OS X makefile for WorkBench
#
all: wb_version.py wb_images.py locale/en/LC_MESSAGES/pysvn_workbench.mo

locale/en/LC_MESSAGES/pysvn_workbench.mo:
	./make-pot-file.sh
	./make-po-file.sh en
	./make-mo-files.sh locale

clean::	
	rm -rf locale/*

include wb_common.mak
