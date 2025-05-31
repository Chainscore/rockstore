# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-XX

### Added
- Initial release of RockStore
- Basic RocksDB operations: put, get, delete
- String convenience methods: put_string, get_string, delete_string
- Context manager support with open_database
- Read-only mode support
- Configurable compression types (snappy, lz4, zstd, etc.)
- Customizable write buffer size and max open files
- Per-operation sync and fill_cache options
- Cross-platform support (macOS, Linux, Windows)
- Comprehensive test suite

### Notes
- Package renamed from "pyrocks" to "rockstore" due to PyPI name availability
- Main class renamed from "PyRocks" to "RockStore" for consistency 