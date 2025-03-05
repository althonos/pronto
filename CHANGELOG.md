# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
[Unreleased]: https://github.com/althonos/pronto/compare/v2.7.0...HEAD

## [v2.7.0] - 2025-03-05
[v2.7.0]: https://github.com/althonos/pronto/compare/v2.6.0...v2.7.0
### Added
- `encoding` argument to `Ontology` constructor to skip auto-detection if needed ([#221](https://github.com/althonos/pronto/issues/221), [#241](https://github.com/althonos/pronto/issues/241)).
### Fixed
- Broken implementation of `EncodedFile.readinto` causing issues with some encodings ([#109](https://github.com/althonos/pronto/issues/109)).
- `tests` module being included in site-install ([#237](https://github.com/althonos/pronto/issues/237)).
- Ignore Unicode BOM in `BaseParser.can_parse` if any.

## [v2.6.0] - 2025-02-14
[v2.6.0]: https://github.com/althonos/pronto/compare/v2.5.8...v2.6.0
### Added
- Explicit support for Python 3.13.
- OWL/XML and RDF/XML format support for `Ontology.dump` ([#232](https://github.com/althonos/pronto/issues/232), [#149](https://github.com/althonos/pronto/issues/149)).
### Changed
- Bump `fastobo` to `v0.13.0`.
- Use `pyproject.toml` to store project metadata instead of `setup.cfg`.
### Fixed
- RDF/XML parser not supporting `owl:annotatedTarget` given as attributes.
- Warn when failing to parse a xref in RDF/XML class parser.
- Allow undeclared synonym types in RDF/XML parser ([#229](https://github.com/althonos/pronto/issues/229)).

## [v2.5.8] - 2024-09-14
[v2.5.8]: https://github.com/althonos/pronto/compare/v2.5.7...v2.5.8
### Fixed
- Extraction of implicit string annotation in RDF/XML files ([#231](https://github.com/althonos/pronto/issues/231)).
- RDF/XML parser crash on `oboInOwl:SynonymTypeProperty` when missing a scope ([#230](https://github.com/althonos/pronto/issues/230)).
### Changed
- Migrate documentation to PyData theme.

## [v2.5.7] - 2024-04-24
[v2.5.7]: https://github.com/althonos/pronto/compare/v2.5.6...v2.5.7
### Fixed
- Handling of RDF datatypes in RDF/XML parser ([#223](https://github.com/althonos/pronto/pull/223), by [@chrishmorris](https://github.com/chrishmorris)).

## [v2.5.6] - 2024-02-21
[v2.5.6]: https://github.com/althonos/pronto/compare/v2.5.5...v2.5.6
### Added
- Explicit support for Python 3.12.
### Fixed
- Synonym types not being properly extracted by RDF/XML parser ([#218](https://github.com/althonos/pronto/issues/218)).

## [v2.5.5] - 2023-08-17
[v2.5.5]: https://github.com/althonos/pronto/compare/v2.5.4...v2.5.5
### Fixed
- `replaced_by` and `consider` attributes not being extracted from RDF/XML documents on missing RDF datatype ([#209](https://github.com/althonos/pronto/issues/209)).
- Hard requirement on `multiprocessing.pool` preventing the package to work single-threaded on more restrictive environments ([#208](https://github.com/althonos/pronto/pull/208)).

## [v2.5.4] - 2023-04-10
[v2.5.4]: https://github.com/althonos/pronto/compare/v2.5.3...v2.5.4
### Fixed
- `Entity.synonyms` setter not accepting `frozenset` arguments as expected (#207).
### Changed
- Bump supported `networkx` version to `v3.0` (#206).

## [v2.5.3] - 2023-01-11
[v2.5.3]: https://github.com/althonos/pronto/compare/v2.5.2...v2.5.3
### Fixed
- Crash in `LineageIterator.to_set` when starting from an empty set of entities.

## [v2.5.2] - 2022-12-07
[v2.5.2]: https://github.com/althonos/pronto/compare/v2.5.1...v2.5.2
### Added
- Explicit support for Python 3.11.
### Changed
- Bumped `fastobo` dependency to `v0.12.2`.
- Bumped `chardet` dependency to `v5.0`.

## [v2.5.1] - 2022-10-12
[v2.5.1]: https://github.com/althonos/pronto/compare/v2.5.0...v2.5.1
### Fixed
- `EntitySet.ids` iterating on its elements instead of copying the internal identifiers.
- RDF/XML parser failing on unknown datatypes ([#187](https://github.com/althonos/pronto/issues/187)).
### Changed
- Disable typechecking when collecting entities in `to_set` methods.

## [v2.5.0] - 2022-07-12
[v2.5.0]: https://github.com/althonos/pronto/compare/v2.4.7...v2.5.0
### Changed
- Bumped `fastobo` dependecy to `v0.12.1`
### Removed
- Support for Python 3.6.

## [v2.4.7] - 2022-06-28
[v2.4.7]: https://github.com/althonos/pronto/compare/v2.4.6...v2.4.7
### Fixed
- Serialization of `is_class_level` properties with `fastobo`-based serializers ([#178](https://github.com/althonos/pronto/issues/178)).
- Parsing of `SynonymTypeProperty` elements in RDF/XML without a label attribute ([#176](https://github.com/althonos/pronto/issues/176)).

## [v2.4.6] - 2022-06-18
[v2.4.6]: https://github.com/althonos/pronto/compare/v2.4.5...v2.4.6
### Added
- Setters for the `holds_over_chain` and `equivalent_to_chain` properties of `Relationship` objects.
### Fixed
- Serialization of `holds_over_chain` properties with `fastobo`-based serializers ([#175](https://github.com/althonos/pronto/issues/175)).

## [v2.4.5] - 2022-04-21
[v2.4.5]: https://github.com/althonos/pronto/compare/v2.4.4...v2.4.5
### Fixed
- Serialization of *metadata tag* relationships by `fastobo` ([#164](https://github.com/althonos/pronto/issues/164)).

## [v2.4.4] - 2022-01-24
[v2.4.4]: https://github.com/althonos/pronto/compare/v2.4.3...v2.4.4
### Added
- `OwlFunctionalSerializer` to dump an `Ontology` to OWL Functional-style syntax.
### Changed
- Bumped `fastobo` dependency to `v0.11.1`.
- Make `FastoboParser` raise a `SyntaxWarning` when encoutering creation dates that are not `datetime.datetime`.

## [v2.4.3] - 2021-08-02
[v2.4.3]: https://github.com/althonos/pronto/compare/v2.4.2...v2.4.3
### Added
- Missing documentation for the `pronto.Entity.relationships` property.
### Fixed
- RDX/XML parser crashing on files containing a relationship and a term with the same ID ([#138](https://github.com/althonos/pronto/pull/138)).

## [v2.4.2] - 2021-05-26
[v2.4.2]: https://github.com/althonos/pronto/compare/v2.4.1...v2.4.2
### Added
- Support for `chardet` version `4.0` (in addition to older `3.0`).
### Fixed
- Serialization of `Ontology` failing with non-empty `idspaces`.
- Typo in OWL2 URL in `README.md` ([#130](https://github.com/althonos/pronto/issues/130)).

## [v2.4.1] - 2021-02-19
[v2.4.1]: https://github.com/althonos/pronto/compare/v2.4.0...v2.4.1
### Changed
- `pronto.pv.PropertyValue` is now an abstract class.
- `pronto.parsers.RdfXmlParser` now ignores synonym Xrefs not in 
  the right format.
### Fixed
- `pronto.Entity.definition` documentation now lists return type as
  `pronto.definition.Definition` as expected.
- CURIE compaction in RDF/XML not being handled consistently, causing
  some crashes on ontologies using aliased relationships.
- `pronto.utils.typechecked.disabled` is now reentrant and should
  not be disabled in multithreaded contexts anymore.
### Removed
- Implicit injection of `lxml` instead of `xml.etree`, which caused
  issues with `RdfXmlParser`.

## [v2.4.0] - 2021-02-18
[v2.4.0]: https://github.com/althonos/pronto/compare/v2.3.2...v2.4.0
### Added
- Deprecation warnings for the retrieval of relationships via
  indexing, to be deprecated in `v3`.
### Changed
- Replaced Travis-CI with GitHub Actions to handle continuous integration.
- Bumped `fastobo` dependency to `v0.10.0`.
### Removed
- Retrieval of terms via their alternate IDs (introduced in `v2.3.0`,
  caused multiple issues ([#120](https://github.com/althonos/pronto/issues/120),
  [#126](https://github.com/althonos/pronto/issues/126)).

## [v2.3.2] - 2020-12-17
[v2.3.2]: https://github.com/althonos/pronto/compare/v2.3.1...v2.3.2
### Added
- Support for path-like objects when creating an `Ontology`
  ([#108](https://github.com/althonos/pronto/pull/108)).
### Fixed
- Avoid decoding file-like objects if they are already **UTF-8**
  encoded when creating an `Ontology`
  ([#110](https://github.com/althonos/pronto/pull/110)).

## [v2.3.1] - 2020-09-21
[v2.3.1]: https://github.com/althonos/pronto/compare/v2.3.0...v2.3.1
### Fixed
- `pronto.entity` package not being included in source distribution.

## [v2.3.0] - 2020-09-21 - **YANKED**
[v2.3.0]: https://github.com/althonos/pronto/compare/v2.2.4...v2.3.0
### Added
- Retrieval of entities via their alternate IDs on the source `Ontology`.
- Direct edition of entity relationships via the `Relationships` view.
- `__all__` attribute to all modules of the data model.
- `RelationshipSet` container like `TermSet` with shortcut attributes and
  proxying of actual `Relationship` instances.
- `Relationship.subproperties` and `Relationship.superproperties` methods
  to add, remove, clear and iterate over the subproperties and superproperties
  of a `Relationship` instance.
- `Ontology.synonym_types` method to count (via `SizedIterator`) and iterate
  over the synonym types of an ontology and all of its imports.
- `Ontology.get_synonym_type` method to retrieve a single synonym type by ID
  from an ontology or one of its imports.
### Changed
- Management of sub-properties / super-properties is now consistent with
  the management of subclasses / superclasses.
- `consider`, `disjoint_from`, `disjoint_over`, `equivalent_to`, `replaced_by`
  `transitive_over` and `union_of` properties of `Relationship` now return
  a `RelationshipSet`.
### Fixed
- Outdated documentation in `Term.subclasses` describing the performances of
  the previous algorithm.
- Possible `AttributeError` with the setter of the `Entity.synonyms` property.
- Issue with synonym types declared in imported ontologies not being usable
  with synonyms of the actual ontology.
- Various type annotations not updated since version [v2.2.2].

## [v2.2.4] - 2020-09-11
[v2.2.4]: https://github.com/althonos/pronto/compare/v2.2.3...v2.2.4
### Changed
- Make `Entity.annotations` return a mutable set and add a setter.
### Fixed
- `Term.relationship` erroneously updating the `Ontology._lineage` cache.
- Unneeded code in `pronto.serializers._fastobo` handling `is_a` clauses.

## [v2.2.3] - 2020-07-31
[v2.2.3]: https://github.com/althonos/pronto/compare/v2.2.2...v2.2.3
### Changed
- Replaced `frozendict` with `immutabledict` ([#90](https://github.com/althonos/pronto/pull/90)).
- Bumped `fastobo` dependency to `v0.9.0` to support inline comments.
- Parsers will now process their imports in parallel using a thread pool.
### Fixed
- Argument type checking in view layer is now disabled during the parsing
  phase to reduce overhead.

## [v2.2.2] - 2020-07-18
[v2.2.2]: https://github.com/althonos/pronto/compare/v2.2.1...v2.2.2
### Added
- Extraction of basic relationships from RDF/XML documents.
### Fixed
- Erroneous type annotations on `Term.subclasses` and `Term.superclasses`.
- Bug with `Term.equivalent_to` setter crashing with a `NameError`.
- Bug with `Entity.synonyms` setter not extracting synonym data.

## [v2.2.1] - 2020-06-17
[v2.2.1]: https://github.com/althonos/pronto/compare/v2.2.0...v2.2.1
### Fixed
- Extraction of subclasses/superclasses hierarchy from nested imports.
- Serialization of OBO frames not being done in order.
- Parsing issue with `anti_symmetric` clauses in OBO typedefs.
- Xrefs not being extracted when declared as axioms in RDF/XML documents.
- `ResourceWarning` when creating `Ontology` from file-handles not mapping
  to a filesystem location.

## [v2.2.0] - 2020-06-17
[v2.2.0]: https://github.com/althonos/pronto/compare/v2.1.0...v2.2.0
### Added
- `threads` parameter to `Ontology` constructor to control the number of
  threads used by parsers supporting multithreading (OBO and OBO JSON at
  the moment).
- Deprecation warnings for suspected uses of the `is_a` pseudo-relationship
  since subclasses/superclasses is now to be handled by the owner `Ontology`.
- Support for subclass/superclass edition directly from the objects returned
  by `Term.subclasses()` and `Term.superclasses()`. ([#84](https://github.com/althonos/pronto/issues/84))
### Changed
- Updated `fastobo` to `v0.8`, which reduce memory footprint of identifiers,
  and improves the parser speed.
- Improved OBO parser performance using threading plus zero-copy validation
  of identifiers on `Xref` instantiation.
- Improved performance in debug mode by having the typechecker only extract
  the wrapped function signature once.
### Fixed
- OBO parser crashing on files containing `idspace` clauses in their headers.
- Reference management issue with binary operations of `TermSet`.
### Removed
- `nanoset` depency, which was not useful anymore in Python 3.8 and caused
  issues with multithreading when processing OBO frames in parallel.

## [v2.1.0] - 2020-03-23
[v2.1.0]: https://github.com/althonos/pronto/compare/v2.0.1...v2.1.0
### Added
- `Synonym.xrefs` now has a setter. ([#70](https://github.com/althonos/pronto/issues/70))
- `pickle` support for `Ontology`. ([#66](https://github.com/althonos/pronto/issues/66))
- `RdfXmlParser` support for `owl:inverseOf` and `rdfs:subPropertyOf`.
### Changed
- `Synonym.xrefs` now returns a mutable set that can be used to add
  `Xref` to the synonym directly.
### Fixed
- `SynonymType.type` setter does not consider all synonym types as
  undeclared anymore. ([#71](https://github.com/althonos/pronto/issues/71))
- `RdfXmlParser` crashing on synonym types definition without a label
  like in Uberon. ([#67](https://github.com/althonos/pronto/issues/67))
- `FastoboSerializer` crashing when encountering a relationship with
  at least one `replaced_by` clause.

## [v2.0.1] - 2020-02-19
[v2.0.1]: https://github.com/althonos/pronto/compare/v2.0.0...v2.0.1
### Fixed
- Internal handling of ontology data forcing an `Ontology` to outlive all
  of the `Term`s created from it.
- `Term.id` property missing a return type annotation.
- `Term.equivalent_to` not returning a `TermSet` but a set of strings.
### Changed
- Refactored implementation of `SubclassesIterator` and  
  `SuperclassesIterator` to make both use the interal subclassing cache.
- Make `Term.is_leaf` use internal subclassing cache to make it run in
  constant time.

## [v2.0.0] - 2020-02-14
[v2.0.0]:https://github.com/althonos/pronto/compare/v1.2.0...v2.0.0
### Added
- `TermSet.subclasses` and `TermSet.superclasses` methods to query all    
  the subclasses / superclasses of all `Term`.
- `TermSet` class to the top-level `pronto` module.
- Dynamic management of subclassing cache for the `Ontology` class.
- Setters for `Term.consider`, `Term.union_of` and `Term.intersection_of`.
### Removed
- `cache` keyword argument for the `Ontology`.
### Fixed
- `SuperclassesIterator.to_set` being named `to_self` because of a typo.
- Several bugs affecting the `fastobo`-backed serializer.

## [v1.2.0] - 2020-02-10
[v1.2.0]: https://github.com/althonos/pronto/compare/v1.1.5...v1.2.0
### Added
- Parameter `with_self` to disable reflexivity of `Term.subclasses` and
  `Term.superclasses` iterators.
- `TermSet` class which stores a set of terms efficiently while providing
  some useful shortcuts to access the underlying data.
### Changed
- Moved code of `Term.subclasses` and `Term.superclasses` to a dedicated
  iterator class in the `pronto.logic` submodule.
- Dropped `contexter` requirement.
### Fixed
- Fix a typo in `Synonym.type` setter leading to a potential bug when
  the given `type` is `None`.
- Fix miscellaneous bugs found with `mypy`.
- `fastobo` serializer crashing on namespace clauses because of a type
  issue.
- `fastobo` parsers using data version clauses as format version clauses.

## [v1.1.5] - 2020-01-25
[v1.1.5]: https://github.com/althonos/pronto/compare/v1.1.4...v1.1.5
### Changed
- Bumped `fastobo` to `v0.7.0`, switching parser implementation to use
  multi-threading in order to speedup the parser process.

## [v1.1.4] - 2020-01-21
[v1.1.4]: https://github.com/althonos/pronto/compare/v1.1.3...v1.1.4
### Added
- Explicit support for Python 3.8.
- Support for Windows-style line endings
  ([#53](https://github.com/althonos/pronto/issues/53))

## [v1.1.3] - 2019-11-10
[v1.1.3]: https://github.com/althonos/pronto/compare/v1.1.2...v1.1.3
### Fixed
- Handling of some clauses in `FastoboParser`.
- `OboSerializer` occasionaly missing lines between term and typedef frames.
### Added
- Missing docstrings to some `Entity` properties.

## [v1.1.2] - 2019-10-30
[v1.1.2]: https://github.com/althonos/pronto/compare/v1.1.1...v1.1.2
### Fixed
- `RdfXMLParser` crashing on entities with `rdf:label` elements
  without literal content.

## [v1.1.1] - 2019-10-29
[v1.1.1]: https://github.com/althonos/pronto/compare/v1.1.0...v1.1.1
### Fixed
- `pronto.serializers` module not being embedded in Wheel distribution.

## [v1.1.0] - 2019-10-24
[v1.1.0]: https://github.com/althonos/pronto/compare/v1.0.0...v1.1.0
### Added
- `Entity.add_synonym` method to create a new synonym and add it to an entity.
- `@roundrepr` now adds a minimal docstring to the generated `__repr__` method.
- `Ontology` caches subclassing relationships to greatly improve performance of
  `Term.subclasses`.
### Changed
- `Entity` subclasses now store their `id` directly to improve performance.
- `Term.subclasses` and `Term.superclasses` use `collections.deque` instead of
  `queue.Queue` as a LIFO structure since thread-safety is not needed.
- `chardet` result is now used even when prediction confidence is under 100%
  to detect encoding of the handle passed to `Ontology`.
### Fixed
- `SynonymType` comparison implementation.
- `Synonym.type` getter crashing on `type` not being `None`.
- `RdfXMLParser` crashing on synonymtypedefs without scope specifiers.

## [v1.0.0] - 2019-10-11
[v1.0.0]: https://github.com/althonos/pronto/compare/v1.0.0-alpha.3...v1.0.0
### Fixed
- Issues with typedef serialization in `FastoboSerializer`.
- `Ontology.create_term` and `Ontology.create_relationship` not raising `ValueError`
  when given an identifier already in the knowledge graph.
- Signature of `BaseSerializer.dump` to remove `encoding` argument.
- Missing `__slots__` in `Entity` in non-typechecking runtime.
### Changed
- Bumped `fastobo` requirement to `v0.6.0`.

## [v1.0.0-alpha.3] - 2019-10-10
[v1.0.0-alpha.3]: https://github.com/althonos/pronto/compare/v1.0.0-alpha.2...v1.0.0-alpha.3
### Added
- Extraction of `oboInOwl:consider` annotation in `RdfXMLParser`.
- Extraction of `oboInOwl:savedBy` annotation in `RdfXMLParser`.
- Extraction of `subsetdef` and `synonymtypedef` as annotation properties in
  `RdfXMLParser`.
- Support for `doap:Version` instead of `owl:VersionIri` for specification
  of ontology data version.
- Proper comparison of `PropertyValue` classes, based on the lexicographic order
  of their serialization.
- `Ontology.dump` and `Ontology.dumps` methods to serialize an ontology in
  **obo** or **obojson** format.
### Fixed
- `Metadata` not storing optional description of ID spaces if any.
- Wrong type hints in `RelationshipData.equivalent_to_chain`.
### Changed
- Added type checking to some more property setters.
- Avoid using `networkx` in `Term.subclasses`.
- `fastobo`-derived parsers will not create a new entity if one exists in the
  graph of dependencies already.
- Exposed `pronto.warnings` and the complete warnings hierarchy.

## [v1.0.0-alpha.2] - 2019-10-03
[v1.0.0-alpha.2]: https://github.com/althonos/pronto/compare/v1.0.0-alpha.1...v1.0.0-alpha.2
### Added
- Support for extraction of relationships from OWL/XML files to `OwlXMLParser`.
### Fixed
- Type hints of `RelationshipData.synonyms` attribute.

## [v1.0.0-alpha.1] - 2019-10-02
[v1.0.0-alpha.1]: https://github.com/althonos/pronto/compare/v0.12.2...v1.0.0-alpha.1
### Changed
- Dropped support for Python earlier than `3.6`.
- Brand new data model that follow the OBO 1.4 object model.
- Partial OWL XML parser implementation using the OBO 1.4 semantics.
- New OBO parser implementation based on `fastobo`.
- Imports are properly separated from the top-level ontology.
- `Ontology.__getitem__` can also access entities from imports.
- `Term`, `Relationship`, `Xref`, `SynonymType` compare only based on their ID.
- `Subset`, `Definition` compare only based on their textual value.
### Added
- Support for OBO JSON parser based on `fastobo`.
- Provisional `mypy` type hints.
- Type checking for most properties in `__debug__` mode.
- Proper `repr` implementation that should roundtrip most of the time.
- Detection of file format and encoding based on buffer content.
### Removed
- OBO and JSON serialization support (for now).
- `Term.rchildren` and `Term.rparents` and stop making direction assumptions on relationships.
