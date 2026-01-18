from setuptools import setup, find_packages

with open('README') as f:
    long_desc = f.read()

setup(name="flatland",
      packages=find_packages(exclude=['tests.*', 'tests']),
      author='Jason Kirtland',
      author_email='jek@discorporate.us',
      description='HTML form management and validation',
      keywords='schema validation data web form forms roundtrip',
      long_description=long_desc,
      license='MIT License',
      url='https://github.com/discorporate/flatland/',
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.9',
                   'Programming Language :: Python :: 3.10',
                   'Programming Language :: Python :: 3.11',
                   'Programming Language :: Python :: 3.12',
                   'Programming Language :: Python :: 3.13',
                   'Programming Language :: Python :: 3.14',
                   'Topic :: Internet :: WWW/HTTP :: WSGI',
                   'Topic :: Software Development :: Libraries'],
      use_scm_version={
          'write_to': 'flatland/_version.py',
      },
      setup_requires=[
          'setuptools_scm',
      ],
      install_requires=[
          'blinker',
      ],
      python_requires='>=3.9',
      include_package_data=True,
      zip_safe=True,
)
