#
#	win32.mak WorkBench
#
all: run build_app

APPNAME=wb
# run_w for production image
# run_w_d for debug meinc image
APPTYPE=run_w

PYTHONPATH=$(PYSVN_PYTHONPATH)

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
	wb_platform_win32_specific.py \
	wb_preferences.py \
	wb_shell_commands.py \
	wb_shell_win32_commands.py \
	wb_source_control_providers.py \
	wb_subversion_utils.py \
	wb_subversion_provider.py \
	wb_subversion_project_info.py \
	wb_subversion_tree_handler.py \
	wb_subversion_list_handler.py \
	wb_subversion_info_dialog.py \
	wb_subversion_properties_dialog.py \
	wb_tree_panel.py \
	wb_version.py \
	I18N\pysvn_workbench.current.pot

wb.rc: wb.rc.template ..\Builder\version.info
	$(PYTHON) -u ..\Builder\brand_version.py ..\Builder\version.info wb.rc.template

wb_version.py: wb_version.py.template ..\Builder\version.info
	$(PYTHON) -u ..\Builder\brand_version.py ..\Builder\version.info wb_version.py.template

I18N\pysvn_workbench.current.pot:
	make-pot-file.cmd
	make-po-file.cmd en
	make-mo-files.cmd locale

IMAGES = \
	toolbar_images/add.png \
	toolbar_images/checkin.png \
	toolbar_images/delete.png \
	toolbar_images/diff.png \
	toolbar_images/edit.png \
	toolbar_images/editcopy.png \
	toolbar_images/editcut.png \
	toolbar_images/editpaste.png \
	toolbar_images/exclude.png \
	toolbar_images/file_browser.png \
	toolbar_images/history.png \
	toolbar_images/include.png \
	toolbar_images/info.png \
	toolbar_images/lock.png \
	toolbar_images/open.png \
	toolbar_images/property.png \
	toolbar_images/revert.png \
	toolbar_images/terminal.png \
	toolbar_images/unlock.png \
	toolbar_images/update.png \
	wb.png


wb_images.py: make_wb_images.py $(IMAGES)
	$(PYTHON) -u make_wb_images.py wb_images.py $(IMAGES) 

#
#	Make the run script
#
run: run_$(APPNAME).cmd

SCRIPT_NAME=run_$(APPNAME).cmd
$(SCRIPT_NAME): win32.mak
	echo setlocal > $(SCRIPT_NAME)
	echo set PYTHONPATH=$(PYTHONPATH) >> $(SCRIPT_NAME)
	echo python %CD%\$(APPNAME)_main.py %* >> $(SCRIPT_NAME)
	echo endlocal >> $(SCRIPT_NAME)

clean::
	if exist *.pyc del *.pyc
	if exist bin rmdir bin /s /q
	if exist wb_version.py del wb_version.py
	if exist wb_images.py del wb_images.py
	if exist locale rmdir /s /q locale
	if exist I18N\pysvn_workbench.current.pot del I18N\pysvn_workbench.current.pot

!include <meinc_installer.mak>
