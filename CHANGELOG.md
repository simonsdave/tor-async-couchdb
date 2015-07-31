# Change Log
All notable changes to this project will be documented in this file.
Format of this file follows [these](http://keepachangelog.com/) guidelines.
This project adheres to [Semantic Versioning](http://semver.org/).

## [0.11.0] - [2015-06-17]

### Changed
- aync_model_actions.AsyncModelsRetriever enable querying via start/end keys
- installer skip pre-existing databases and design document

## [0.10.0] - [2015-05-26]
### Added
- async_model_actions.AsyncDeleter enables async deletion

### Changed
- installer loads *.json files from regular directory (instead of *.py from
  python package)
- AsyncPersister now requires dictionaries returned by as_doc_for_store()
  in derived classes of Model always return a type property of the form
  ^[^\s]+_v\d+\.\d+$ - this change is key to enabling automated conflict
  resolution
- Update dependencies

## [0.9.2] - [2015-03-01]
- not really the initial release but intro'ed CHANGELOG.md late
