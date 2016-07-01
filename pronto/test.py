import os
import doctest
pronto_dir = os.path.dirname(os.path.abspath(__file__))

for filename in os.listdir(pronto_dir):
    if filename.endswith('.py') and not filename.startswith('_'):
        doctest.testfile(filename)

