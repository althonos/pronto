Examples
========


Explore an ontology via relationships
-------------------------------------

Pronto can be used to explore an ontology and find children of a specific term.
This example was taken from mzml2isa_, a program that parses .mzML files (a
format of Mass Spectrometry data).

.. code:: python

    self.obo = Ontology('http://purl.obolibrary.org/obo/ms.obo')
    # ... extract metadata and get elements ... #
    for e in elements:
        for ie in e.iterfind('s:cvParam', self.ns):
            if ie.attrib['accession'] in self.obo['MS:1000031'].rchildren().id:
                ### ... get instrument info ... ###
                parents = self.obo[ie.attrib['accession']].rparents()
                manufacturer = next(parent for parent in parents \
                                    if parent in self.obo['MS:1000031'].children)
                ### ... get manufacturer info ... ###


.. _mzml2isa: https://pypi.python.org/pypi/mzml2isa


Merge ontologies and export the merge to the Obo Format
-------------------------------------------------------

It is really easy to merge two ontologies: for instance, if we want to merge
the `Amphibian gross anatomy`_ ontology with the `Xenopus anatomy and development`_
ontology:

    First, we import the ontologies:
        .. code:: python

            >>> from pronto import Ontology
            >>> aao = Ontology('http://aber-owl.net/onts/AAO_60.ont')
            >>> xao = Ontology('http://purl.obolibrary.org/obo/xao.owl')
            >>> print(len(aao), len(xao))
            1603 1521

    Then, either we merge the ontologies in a new ontology:
        .. code:: python

            >>> merged = Ontology()
            >>> merged.merge(aao)
            >>> merged.merge(xao)
            >>> print(len(merged))
            3124

    Or we can also merge the XAO in the AAO to keep the AAO metadata intact:
        .. code:: python

            >>> aao.merge(xao)
            >>> print(len(aao))
            3124

    Then we do the following to export the merged ontology:
        .. code:: python

            >> with open('merged.obo', 'w') as f:
                f.write(aao.obo)  #or f.write(merged.obo)





.. _Amphibian gross anatomy: http://aber-owl.net/ontology/AAO
.. _Xenopus anatomy and development: http://www.obofoundry.org/ontology/xao.html
