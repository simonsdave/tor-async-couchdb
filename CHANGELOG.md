# Change Log
All notable changes to this project will be documented in this file.
Format of this file follows [these](http://keepachangelog.com/) guidelines.
This project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - [unreleased]
### Added
- async_model_actions.AsyncDeleter enables async deletion

### Changed
- installer loads *.json files from regular directory (instead of *.py from
  python package)
- AsyncPersister now requires dictionaries returned by as_doc_for_store()
  in derived classes of Model always return a type property of the form
  ^[^\s]+_v\d+\.\d+$ - this change is key to enabling automated conflict
  resolution

## [0.9.2] - [2015-03-01]
- not really the initial release but intro'ed CHANGELOG.md late
