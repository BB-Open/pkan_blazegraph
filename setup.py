# -*- coding: utf-8 -*-
"""Installer for the pkan.dcatapde package."""

from setuptools import find_packages
from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install

import os
import sys


version = '0.1.dev0'
description = 'PKAN interface to Blazegraph tripelstore'
long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CONTRIBUTORS.rst').read(),
    open('CHANGES.rst').read(),
])

install_requires = [
    'setuptools',
    # -*- Extra requirements: -*-
    'requests',
    'SPARQLWrapper',
    'pylama',
    'python-githooks',
],

test_requires = [
    'responses',
    'pylama',
]

testfixture_requires = [
]

TEMPLATE = """
cd {0}
{1} -m {2} ./src"""

LINTER = 'pylama'

def _post_install():
    BASE_DIR = os.environ["PWD"]
    GITHOOKS_FILE = os.path.join(BASE_DIR, '.git/hooks/pre_commit')
    python = sys.executable

    res = TEMPLATE.format(
        BASE_DIR,
        python,
        LINTER
    )
    f_out = open(GITHOOKS_FILE, 'w')

    f_out.write(res)
    f_out.close()


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self, *args, **kwargs):
        super(PostDevelopCommand, self).run(*args, **kwargs)
        _post_install()

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self, *args, **kwargs):
        super(PostInstallCommand, self).run(*args, **kwargs)
        _post_install()


setup(
    name='pkan.blazegraph',
    version=version,
    description=description,
    long_description=long_description,
    # Get more from https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Plone',
        'Framework :: Plone :: 5.0',
        'Framework :: Plone :: 5.1',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],

    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
    keywords='Python Plone',
    author='Dr. Volker Jaenisch',
    author_email='volker.jaenisch@inqbus.de',
    url='https://github.com/BB-Open/pkan.blazegraph',
    download_url='https://pypi.python.org/pypi/pkan.blazegraph',
    license='GPL version 2',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['pkan'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'test': test_requires,
        'testfixture': testfixture_requires,
    },
    entry_points="""
    """,
)
