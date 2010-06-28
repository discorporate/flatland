SOURCES=$(shell find flatland -name '*.py')
I18N=flatland/i18n


$(I18N)/flatland.pot: $(SOURCES)
	pybabel extract -o $(I18N)/flatland.pot \
	  -k P_:1,2 --charset=utf-8 \
	  --sort-by-file --width=79 --add-comments=TRANSLATORS: \
          --msgid-bugs-address=flatland-users@googlegroups.com \
	  flatland

update-messages: $(I18N)/flatland.pot
	pybabel update -i $(I18N)/flatland.pot -d $(I18N) \
	  -D flatland --previous
