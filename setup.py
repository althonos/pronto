#!/usr/bin/env python
# released under the GNU General Public License version 3.0 (GPLv3)

from setuptools import setup, find_packages
import warnings
import platform

warnings.simplefilter("ignore")
import pronto


def format_for_setup(requirement_file):
    requirements = []
    with open(requirement_file) as rq:

        for line in rq:
            line = line.strip()
            if line.startswith('-r'):
                requirements.extend(format_for_setup(line.split(' ', 1)[-1]))
            elif line:
                    requirements.append(line)
    return requirements

## SETUPTOOLS VERSION
setup(
    name='pronto',
    version=pronto.__version__,

    packages=find_packages(),

    py_modules=['pronto'],

    author= pronto.__author__,
    author_email= pronto.__author_email__,

    description="Python frontend to ontologies - a library to parse, create, browse and export ontologies.",
    long_description=open('README.rst').read(),

    run_requires= format_for_setup('requirements.txt'),
    test_requires = format_for_setup('requirements-test.txt'),

    extras_require = { extra:format_for_setup('requirements-{}.txt'.format(extra))
                        for extra in ['doc'] },

    include_package_data=True,

    url='http://github.com/althonos/pronto',

    test_suite="tests",

    classifiers=[
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.2",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Topic :: Scientific/Engineering :: Bio-Informatics",
    "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Operating System :: OS Independent",
    ],

    license="GPLv3",

    keywords = ['Bio-Informatics', 'Ontology', 'OBO', 'Owl', 'convert', 'parse'],

)

