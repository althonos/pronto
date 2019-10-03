# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
[Unreleased]: https://github.com/althonos/pronto/compare/v1.0.0-alpha.2...HEAD

## [1.0.0-alpha.2] - 2019-10-03
[1.0.0-alpha.2]: https://github.com/althonos/pronto/compare/v1.0.0-alpha.1...v1.0.0-alpha.2
### Added
- Support for extraction of relationships from OWL/XML files to `OwlXMLParser`.
### Fixed
- Type hints of `RelationshipData.synonyms` attribute.

## [1.0.0-alpha.1] - 2019-10-02
[1.0.0-alpha.1]: https://github.com/althonos/pronto/compare/v0.12.2...v1.0.0-alpha.1
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
