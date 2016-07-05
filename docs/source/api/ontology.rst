Ontology
=========

.. testsetup:: *

   import os
   os.chdir(os.path.abspath(os.path.join(os.getcwd(), '../tests')))
   if not os.path.isdir('run'): os.mkdir('run')
   import pronto
   pronto.Ontology._time_limit = 0


.. automodule:: pronto.ontology
   :members:
