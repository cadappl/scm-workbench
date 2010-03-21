#
#	makefile WorkBench
#
all: build_bin locale/en/LC_MESSAGES/pysvn_workbench.mo

locale/en/LC_MESSAGES/pysvn_workbench.mo:
	./make-pot-file.sh
	./make-po-file.sh en
	./make-mo-files.sh locale

APPNAME=wb
APPTYPE=run

PYTHONPATH=$(PYSVNLIB)

SOURCES= \
	wb_app.py \
	wb_dialogs.py \
	wb_diff_difflib.py \
	wb_diff_frame.py \
	wb_diff_images.py \
	wb_diff_main.py \
	wb_diff_processor.py \
	wb_exceptions.py \
	wb_frame.py \
	wb_list_panel.py \
	wb_ids.py \
	wb_images.py \
	wb_main.py \
	wb_platform_specific.py \
	wb_platform_unix_specific.py \
	wb_preferences.py \
	wb_shell_commands.py \
	wb_shell_unix_commands.py \
	wb_source_control_providers.py \
	wb_subversion_utils.py \
	wb_subversion_provider.py \
	wb_subversion_project_info.py \
	wb_subversion_tree_handler.py \
	wb_subversion_list_handler.py \
	wb_subversion_info_dialog.py \
	wb_subversion_properties_dialog.py \
	wb_tree_panel.py \
	wb_version.py

include wb_common.mak

PYCHECKER_OPTIONS=--no-shadowbuiltin
INSTALLER_OPTIONS=--force-ld-library-path


build_bin: build_app build_fixup

build_fixup:
	rm -f bin/support/readline.so

#check: checkstop

clean::
	rm -f locale/en/LC_MESSAGES/pysvn_workbench.mo
	rm -f .pycheckrc
	rm -rf bin
	rm -rf *.pyc
	rm -rf wb_version.py

#include $(PYCHECKER_DIR)/pychecker.mak
include $(MEINC_INSTALLER_DIR)/meinc_installer.mak
