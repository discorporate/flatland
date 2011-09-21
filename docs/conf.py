project = u'flatland'
copyright = u'2008-2011, the flatland authors and contributors'

version = '0.0'
release = '0.0.hg-tip'


master_doc = 'index'
add_module_names = False
default_role = 'py:obj'


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
]


try:
    from sphinxcontrib import spelling
    del spelling
    extensions.append('sphinxcontrib.spelling')
except ImportError:
    pass


autoclass_content = 'both'
autodoc_default_flags = ['members', 'show-inheritance']
autodoc_member_order = 'bysource'


intersphinx_mapping = {
    'http://docs.python.org/': None,
    'http://discorporate.us/projects/Blinker/docs/tip/': None,
}


todo_include_todos = True


spelling_ignore_pypi_package_names = True


html_static_path = ['_static']
html_theme_path = ['_themes']
html_theme = 'flatland'
html_logo = 'flatland.png'
html_show_sourcelink = False
html_sidebars = {
    'index': ['globaltoc.html', 'relations.html', 'sourcelink.html', 'searchbox.html'],
}
