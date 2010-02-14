"""
flatland
~~~~~~~~

Flatland manages the mapping between structured Python application
data and the flat key/value namespace of forms.  Features include:

  - Declarative form specification, independent of front-end
    representation

  - Conversion to and from native Python types and Unicode

  - Structured data: lists, dicts, lists of dicts, etc.

  - JavaScript-safe name flattening by default

  - Schema-driven, directed expansion of incoming key/value pairs-
    only expected request data is examined and parsed

  - Compound fields

  - Validation

  - Strong value defaulting, pre-populating, re-populating and
    round-tripping

  - Namespacing: easily manage multiple forms in a single page or
    submission

  - Works on form and JSON data

Flatland data is not anonymous. Values retain knowledge of their
location in the form hierarchy and their validation status.  Flatland
tries to provide both pythonic data access in application code and
also simple and foolproof data access in Web templates.

The hg `flatland tip`_ can be installed via ``easy_install
flatland==dev``.

.. _flatland tip: http://bitbucket.org/jek/flatland/get/tip.zip#egg=flatland-dev

"""
import os
import sys

# Restrict to Python 2.5, for now.  Provide compatibilty for 2.4 later.
if sys.version_info < (2, 5):
    print "Python 2.5 or higher is required."
    sys.exit(1)

try:
    from setuptools import setup, find_packages
    extra_setup = dict(
        zip_safe = True,
        tests_require=['nose'],
        # for tests, prefer just 'nosetests tests'
        test_suite='nose.collector',
        )
except ImportError:
    from distutils.core import setup
    extra_setup = {}
    def find_packages(exclude=()):
        return [w[0].replace('/', '.')
                for w in os.walk('flatland')
                if '__init__.py' in w[2]]

setup(name="flatland",
      version="dev",
      packages=find_packages(exclude=['tests.*', 'tests']),
      author='Jason Kirtland',
      author_email='jek@discorporate.us',
      description='HTML form management and validation',
      keywords='wsgi web http webapps form forms validation roundtrip',
      long_description=__doc__,
      license='MIT License',
      url='http://discorporate.us/jek/projects/flatland/',
      classifiers=['Development Status :: 3 - Alpha',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2.5',
                   'Programming Language :: Python :: 2.6',
                   'Topic :: Internet :: WWW/HTTP :: WSGI',
                   'Topic :: Software Development :: Libraries'],
      **extra_setup
)
