
import os
import sys

# Restrict to Python 2.5, for now.  Provide compatibilty for 2.4 later.
if sys.version_info < (2, 5):
    print "Python 2.5 or higher is required."
    sys.exit(1)

try:
    from setuptools import setup, find_packages
    extra_setup = dict(
        zip_safe=True,
        tests_require=['nose', 'Genshi'],
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

import flatland
version = flatland.__version__
long_desc = open('README').read()

setup(name="flatland",
      version=version,
      packages=find_packages(exclude=['tests.*', 'tests']),
      author='Jason Kirtland',
      author_email='jek@discorporate.us',
      description='HTML form management and validation',
      keywords='schmea validation data web form forms roundtrip',
      long_description=long_desc,
      license='MIT License',
      url='http://discorporate.us/jek/projects/flatland/',
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2.5',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Internet :: WWW/HTTP :: WSGI',
                   'Topic :: Software Development :: Libraries'],
      **extra_setup)
