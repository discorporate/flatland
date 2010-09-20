TIP=$(shell hg tip --template '{rev}')
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
	@echo "Preparing sdist of flatland @ hg.$(TIP)"
	perl -pi -e \
          "s~version = flatland.__version__~version = 'hg.$(TIP)'~" \
          setup.py
	(cd docs/source && make clean)
	(cd docs/source && VERSION=$(TIP) make html)
	(cd docs/source && VERSION=$(TIP) make text)
	python setup.py sdist
	perl -pi -e \
          "s~version = 'hg.$(TIP)'~version = flatland.__version__~" \
          setup.py
