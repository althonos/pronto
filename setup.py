#!/usr/bin/env python
# released under the GNU General Public License version 3.0 (GPLv3)

from setuptools import setup, find_packages
import pronto

## SETUPTOOLS VERSION
setup(
    name='pronto',
    version=pronto.__version__,
    
    packages=find_packages(),
    
    py_modules=['pronto'],
    
    author= pronto.__author__,
    author_email= 'martin.larralde@ens-cachan.fr',

    description="Python for Rife ONTOlogies - an unified frontend for different ontology formats.",
    long_description=open('README.md').read(),
    
    install_requires=['lxml'],

    include_package_data=True,

    url='http://github.com/althonos/pronto',

    classifiers=[
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Topic :: Scientific/Engineering :: Bio-Informatics",
    "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Text Processing :: Markup",
    "Topic :: Utilities",
    "Operating System :: OS Independent",
    ],

    #entry_points = {
    #    'console_scripts': [
    #        'pronto = pronto.__main__.run()',
    #    ],
    #},
    license="GPLv3",

    keywords = ['Bio-Informatics', 'Ontology', 'OBO', 'Owl', 'convert', 'parse'],

)

