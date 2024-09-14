API Reference
==============

.. currentmodule:: pronto

.. automodule:: pronto


Ontology
--------

An abstraction over a :math:`\mathcal{SHOIN}^\mathcal{(D)}` ontology.

.. autosummary::
   :nosignatures:
   :template: summary.rst
   :toctree: 
   :caption: Ontology

   pronto.Ontology


View Layer
----------

The following classes are part of the view layer, and store references to the
ontology/entity they were declared in for verification purposes. For instance,
this let ``pronto`` check that a `Synonym` type can only be changed for a type
declared in the `Ontology` header.

Because of this reason, none of these classes should be created manually, but
obtained from methods of existing `Ontology` or `Entity` instances, such as
`Ontology.get_term` to get a new `Term`.

.. autosummary::
   :nosignatures:
   :template: summary.rst
   :toctree: 
   :caption: View Layer

   pronto.Entity
   pronto.Relationship
   pronto.Synonym
   pronto.Term
   pronto.TermSet


View Collections
----------------

The following classes are dedicated collections that are implemented to view
a specific field of entities, such as relationships. These types cannot be
instantiated directly, but are reachable through the right property on `Entity`
instances.

.. autosummary::
   :nosignatures:
   :template: summary.rst
   :toctree: 
   :caption: View Collections

   pronto.entity.attributes.Relationships


Model Layer
-----------

The following classes are technically part of the data layer, but because they
can be lightweight enough to be instantiated directly, they can also be passed
to certain functions or properties of the view layer. *Basically, these classes
are not worth to implement following the view-model pattern so they can be
accessed and mutated directly.*

.. autosummary::
   :nosignatures:
   :template: summary.rst
   :toctree: 
   :caption: Model Layer

   pronto.Metadata
   pronto.Definition
   pronto.Subset
   pronto.SynonymType
   pronto.LiteralPropertyValue
   pronto.ResourcePropertyValue
   pronto.Xref


Data Layer
----------

The following classes are from the data layer, and store the data extracted from
ontology files. There is probably no point in using them directly, with the
exception of custom parser implementations.

.. autosummary::
   :nosignatures:
   :template: summary.rst
   :toctree: 
   :caption: Data Layer

   pronto.RelationshipData
   pronto.SynonymData
   pronto.TermData


Warnings
--------

.. toctree::
   :hidden:
   :caption: Warnings

   warnings <warnings>

.. autosummary::
   :nosignatures:

   pronto.warnings.ProntoWarning
   pronto.warnings.NotImplementedWarning
   pronto.warnings.SyntaxWarning
   pronto.warnings.UnstableWarning
