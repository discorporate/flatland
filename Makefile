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
	scripts/sdist

# release is now done by invoking scripts/sign-upload-pypi 1.2.3 [test] after creating the sdist.
