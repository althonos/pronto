"""
Test doctest contained tests in every file of the module.
"""

import os
import sys
import shutil
import doctest


if os.getcwd().endswith('pronto'):
    os.chdir('tests')

elif not os.getcwd().endswith('tests'):
    sys.exit('Run the tests from either the lib directory or the tests directory!')

pronto_dir = '../pronto'
sys.path.insert(0, os.path.abspath('..'))
os.mkdir('run')

for filename in os.listdir(pronto_dir):

    filepath = os.path.realpath(os.path.join(pronto_dir, filename))

    if filename.endswith('.py'):
        print("Testing:  {}".format(filepath))
        testresults = doctest.testfile(filepath, module_relative=False)
        if testresults.failed:
            print('↳ Test failed !')
            sys.exit(1)

print('All tests succeeded !')
print('Cleaning...')
shutil.rmtree('run')

