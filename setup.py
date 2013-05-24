#!/usr/bin/env python
from distutils.core import setup

setup(
    name='pdf-factory',
    description='''Make PDF following a specified json config''',
    long_description=open('README.md').read(),
    version='0.1',
    author='Laurent Mox',
    author_email='laurent@revolunet.com',
    url='http://github.com/revolunet/pdf-factory',
    py_modules=['pdfFactory'],
    scripts=['pdfFactory.py'],
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Web Environment',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Utilities'],
)
