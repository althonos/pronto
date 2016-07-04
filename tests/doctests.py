"""
Test doctest contained tests in every file of the module.
"""

import os
import sys
import doctest


if os.getcwd().endswith('tests'):
    pronto_dir = '../pronto'
elif os.getcwd().endswith('pronto'):
    pronto_dir = 'pronto'
else:
    sys.exit('Run the tests from either the lib directory or the tests directory!')



for filename in os.listdir(pronto_dir):

    filepath = os.path.realpath(os.path.join(pronto_dir, filename))

    if filename.endswith('.py'):
        print("Testing:  {}".format(filepath))
        doctest.testfile(filepath, module_relative=False)

