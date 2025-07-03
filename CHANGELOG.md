# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite with 100% code coverage
- Multi-layered logging system with custom folder paths
- YAML/TOML configuration file support
- Backward compatibility with existing `setup_logging()` code
- File rotation with configurable sizes and backup counts
- Console and file output destinations
- Professional project structure with demos and examples
- GitHub Actions CI/CD workflow
- Comprehensive documentation (README, QUICK_START, TUTORIAL)

### Changed
- Extracted from original project as standalone package
- Reorganized project structure for better user experience
- Improved error handling and fallback mechanisms

### Fixed
- Pydantic V2 validator migration issues
- TOML file loading compatibility
- Logging level handling edge cases

## [0.1.0] - 2025-01-XX

### Added
- Initial release of Hydra-Logger
- Core logging functionality with multi-layer support
- Configuration management system
- Backward compatibility layer
- Basic examples and documentation

---

## Version History

### Version 0.1.0 (Initial Release)
- **Date**: 2025-01-XX
- **Status**: Development Complete
- **Features**: 
  - Multi-layered logging system
  - Custom folder path support
  - YAML/TOML configuration
  - Backward compatibility
  - File rotation
  - 100% test coverage
  - Professional documentation

---

## Contributing

When contributing to this project, please update this changelog by adding a new entry under the [Unreleased] section. Follow the format above and include:

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** in case of vulnerabilities

## Release Process

1. Update version in `pyproject.toml` and `hydra_logger/__init__.py`
2. Update this CHANGELOG.md with release date
3. Create a git tag for the version
4. Build and publish to PyPI
5. Create GitHub release with changelog 