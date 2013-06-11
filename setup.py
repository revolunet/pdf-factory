#!/usr/bin/env python
from distutils.core import setup

setup(
    name='pdfFactory',
    description='''Make PDF following a specified json config''',
    long_description=open('README.md').read(),
    version='0.1',
    author='Laurent Mox',
    author_email='laurent@revolunet.com',
    url='http://github.com/revolunet/pdf-factory',
    py_modules=['pdfFactory'],
    scripts=['pdfFactory.py'],
    dependency_links=['https://github.com/revolunet/pypdftk/archive/33acc90f449933cc9826fc9f4b93e9eb92188b04.tar.gz#egg=pypdftk-0.3'],
    install_requires=['pypdftk>=0.3', 'requests>=1.2.2'],
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Web Environment',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Utilities'],
)
