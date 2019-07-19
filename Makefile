SOURCES=$(shell find flatland -name '*.py')
I18N=flatland/i18n


$(I18N)/flatland.pot: $(SOURCES)
	pybabel extract -o $(I18N)/flatland.pot \
	  -k P_:1,2 --charset=utf-8 \
	  --sort-by-file --add-comments=TRANSLATORS: \
          --msgid-bugs-address=flatland-users@googlegroups.com \
	  flatland

update-messages: $(I18N)/flatland.pot
	pybabel update -i $(I18N)/flatland.pot -d $(I18N) \
	  -D flatland --previous

compile-messages:
	pybabel compile -d $(I18N) -D flatland

tip-sdist: compile-messages
	@echo "Preparing sdist of flatland..."
	(cd docs/source && make clean)
	(cd docs/source && make html)
	(cd docs/source && make text)
	python setup.py sdist

release: tip-sdist
	@echo "before doing 'make release', tag the new version with git,"
	@echo "so setuptools_scm creates the correct version for docs and pkg."
	python setup.py register sdist upload --identity="Thomas Waldmann" --sign
