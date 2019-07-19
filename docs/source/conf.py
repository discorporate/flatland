project = u'flatland'
copyright = u'2008-2018, the flatland authors and contributors'

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
import sys, os
sys.path.insert(0, os.path.abspath('../..'))

from flatland._version import version
release = version


master_doc = 'index'
add_module_names = False
default_role = 'py:obj'


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
]


rst_epilog = open('abbrevs.txt').read()


autoclass_content = 'both'
autodoc_default_flags = ['members', 'show-inheritance']
autodoc_member_order = 'bysource'


intersphinx_mapping = {
    'http://docs.python.org/': None,
    'http://pythonhosted.org/blinker/': None,
}


todo_include_todos = True


templates_path = ['_templates']


html_static_path = ['_static']
html_theme_path = ['_themes']
html_theme = 'flatland'
html_logo = '_static/flatland.png'
html_show_sourcelink = False
html_sidebars = {
    'index': ['globaltoc.html', 'relations.html', 'links.html', 'sourcelink.html', 'searchbox.html'],
    'genindex': ['links.html', 'sourcelink.html', 'searchbox.html'],
}

# Avoid issues like below when running under python 3.x:
#
# Expected:
#     [u'hello', u'world']
#
# Got:
#     ['hello', 'world']

import re
import sys
import doctest
OrigOutputChecker = doctest.OutputChecker


class Py23OutputChecker(OrigOutputChecker):
    def check_output(self, want, got, optionflags):
        if sys.version_info[0] > 2:
            want = re.sub("u'(.*?)'", "'\\1'", want)
            want = re.sub('u"(.*?)"', '"\\1"', want)
        return OrigOutputChecker.check_output(self, want, got, optionflags)


doctest.OutputChecker = Py23OutputChecker
