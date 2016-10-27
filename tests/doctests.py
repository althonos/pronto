# coding: utf-8
"""
Test doctest contained tests in every file of the module.
"""

import os
import sys
import shutil
import doctest

if __name__ == "__main__":

    if os.getcwd().endswith('pronto'):
        os.chdir('tests')

    elif not os.getcwd().endswith('tests'):
        sys.exit('Run the tests from either the lib directory or the tests directory!')

    pronto_dir = '../pronto'
    sys.path.insert(0, os.path.abspath('..'))

    if not os.path.isdir('run'):
        os.mkdir('run')

    for filename in os.listdir(pronto_dir):

        filepath = os.path.realpath(os.path.join(pronto_dir, filename))

        if filename.endswith('.py'):
            print("Testing:  {}".format(filepath))

            try:
                testresults = doctest.testfile(filepath, module_relative=False)
            except KeyboardInterrupt:
                shutil.rmtree('run')
                sys.exit(1)
            if testresults.failed:
                print('↳ Test failed !')
                shutil.rmtree('run')
                sys.exit(1)

    print('All tests succeeded !')
    print('Cleaning...')
    shutil.rmtree('run')

