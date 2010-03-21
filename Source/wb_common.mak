wb_version.py: wb_version.py.template ../Builder/brand_version.py ../Builder/version.info
	$(PYTHON) -u make_wb_version.py

wb_images.py: make_wb_images.py
	$(PYTHON) -u make_wb_images.py

run:
	$(PYTHON) -u wb_main.py

check:
	$(PYTHON) -c "import wb_pychecker;import wb_main;wb_pychecker.report()"

clean::
	rm -f wb_version.py
	rm -f wb_images.py
