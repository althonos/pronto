Updating from earlier versions
==============================

From ``v1.*``
-------------

Update from `v1.*` to `v2.*` should be straightforward; the only reason the
major version was updated was because the ``cache`` argument was removed from
the `~pronto.Ontology` constructor.


From ``v0.*``
-------------

Render to OBO
^^^^^^^^^^^^^

Exporting an ontology to the OBO (or other supported formats) is now done with
the `~pronto.Ontology.dump` and `~pronto.Ontology.dumps` methods:

.. code:: python

    # before
    print(ontology.obo)
    open("out.obo", "w").write(ontology.obo)

    # after
    print(ontology.dumps(format="obo"))
    ontoloy.dump(open("out.obo", "w"), format="obo")


Subclasses and superclasses
^^^^^^^^^^^^^^^^^^^^^^^^^^^

``pronto`` is not opinionated about the *direction* of a relationship. Subclassing
relationships are now handled as a special case, following the semantics of the
``rdfs:subClassOf`` property in the `RDF schema <https://www.w3.org/TR/rdf-schema/>`_.

Therefore, the code to access subclasses and superclasses of a `~pronto.Term`
has been updated:

.. code:: python

    # before
    children: pronto.TermList = term.rchildren()
    parents: pronto.TermList = term.rparents()

    # after
    children_iter: Iterable[Term] = term.subclasses()
    parents_iter: Iterable[Term] = term.superclasses()


Because we follow the RDF semantics, any class is also its own subclass and
superclass; therefore, both of these iterators will yield the term itself as the
first member of the iteration. This behaviour can be annoying, so you can disable it
by giving ``with_self=False`` as an argument to only get *true* subclasses or
superclasses:

.. code:: python

    children_iter: Iterable[Term] = term.subclasses(with_self=False)
    parents_iter: Iterable[Term] = term.superclasses(with_self=False)


To only get the direct subclasses or superclasses (i.e., what `Term.children`
and `Term.parents` used to do), pass ``distance=1`` as an argument as well:

.. code:: python

    children: Iterable[Term] = term.subclasses(with_self=False, distance=1)
    parents: Iterable[Term] = term.superclasses(with_self=False, distance=1)


Since querying of subclasses and superclasses now gives you an iterator, but your
previous code was expecting a `TermList`, you can use the `~SubclassesIterator.to_set`
method to obtain a `~pronto.TermSet` which hopefully will prevent the rest of
your code to require more update.

.. code:: python

    # you can use `to_set` to get a `TermSet` from the iterator
    children: pronto.TermSet = term.subclasses().to_set()
    parents: pronto.TermSet = term.superclasses().to_set()
