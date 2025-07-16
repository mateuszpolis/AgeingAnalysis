# [1.6.0](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.5.0...v1.6.0) (2025-07-16)


### Features

* enhance grid visualization service with resource loading ([c9b73c1](https://github.com/mateuszpolis/AgeingAnalysis/commit/c9b73c1f9b56cdb5b3ab8176b8fd8467e66acb58))

# [1.5.0](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.4.0...v1.5.0) (2025-07-15)


### Features

* add total signal data functionality to analysis and results ([f0fd96d](https://github.com/mateuszpolis/AgeingAnalysis/commit/f0fd96d0d67849db750e253ad45351f4abfc70c9))

# [1.4.0](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.3.0...v1.4.0) (2025-07-15)


### Features

* add integrated charge functionality to configuration and analysis ([7ff024f](https://github.com/mateuszpolis/AgeingAnalysis/commit/7ff024f8738d2b75afdd65585c75fced16ee826c))

# [1.3.0](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.2.0...v1.3.0) (2025-07-15)


### Features

* enhance grid visualization functionality ([ecaf92c](https://github.com/mateuszpolis/AgeingAnalysis/commit/ecaf92c8964c491b14cc464b8accb96eee39e23e))

# [1.2.0](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.1.0...v1.2.0) (2025-07-14)


### Features

* add Time Series and Grid Visualization tabs to Ageing Analysis ([3b67c74](https://github.com/mateuszpolis/AgeingAnalysis/commit/3b67c743c7812d791f95f370ede057071cb325ab))

# [1.1.0](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.0.4...v1.1.0) (2025-07-14)


### Features

* add Ageing Visualization Window for enhanced data analysis ([9875927](https://github.com/mateuszpolis/AgeingAnalysis/commit/98759271783a143278cbbb5830705525bcc84f10))

## [1.0.4](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.0.3...v1.0.4) (2025-07-14)


### Bug Fixes

* update output paths for ageing analysis results ([88ab235](https://github.com/mateuszpolis/AgeingAnalysis/commit/88ab235b0b4fc7186c5b969d81dfbab6d7df7219))

## [1.0.3](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.0.2...v1.0.3) (2025-07-14)


### Bug Fixes

* update safety check command in CI workflow ([08f7d5c](https://github.com/mateuszpolis/AgeingAnalysis/commit/08f7d5c3c0bf8f8fd16403c33a8b3b5d3842c52c))

## [1.0.2](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.0.1...v1.0.2) (2025-07-14)


### Bug Fixes

* update deprecated GitHub Actions to latest versions ([176ecfa](https://github.com/mateuszpolis/AgeingAnalysis/commit/176ecfa1875ca0629e6c9f0fb4d57ce543d53039))

## [1.0.1](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.0.0...v1.0.1) (2025-07-14)


### Bug Fixes

* resolve code quality issues for CI/CD pipeline ([8bd9976](https://github.com/mateuszpolis/AgeingAnalysis/commit/8bd9976aea136fca0fbefceb69f8691ad099a4d5))

# 1.0.0 (2025-07-14)


### Bug Fixes

* update repository URL in package.json for semantic-release ([14b1135](https://github.com/mateuszpolis/AgeingAnalysis/commit/14b1135ec5452fe2b9aaae0b96684919edfa6fdc))


### Features

* add configuration file support and enhance command-line interface ([e29f93a](https://github.com/mateuszpolis/AgeingAnalysis/commit/e29f93a3e5a161120a55b2ac3f883d1f1d18c291))
* enhance automatic versioning and release workflow ([bd5cbc2](https://github.com/mateuszpolis/AgeingAnalysis/commit/bd5cbc211648902e70b4db773c328134b8632381))
* enhance configuration management with global base path support ([deab664](https://github.com/mateuszpolis/AgeingAnalysis/commit/deab664f64e08c4f8afac68c846cfc4334af5667))
* enhance data parsing and analysis capabilities ([5def5dd](https://github.com/mateuszpolis/AgeingAnalysis/commit/5def5dd5b5b705ff2e8e9a324edd9cbe9150c9da))
* introduce configuration generator for FIT detector ageing analysis ([b811524](https://github.com/mateuszpolis/AgeingAnalysis/commit/b8115246eeba432c0392165334580bc5a83f9e09))
* set up semantic-release for automated versioning and releases ([479d3e6](https://github.com/mateuszpolis/AgeingAnalysis/commit/479d3e6b68dfafa91fb6bc3407b1fe300327d53e))

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v1.0.0 (2024-01-XX)

### Feat
- Initial release of AgeingAnalysis module (core)
- Basic GUI application for ageing analysis (gui)
- Data processing capabilities (services)
- Visualization tools (plotting)
- Configuration management system (config)
- Module launcher interface (main)

### Build
- Comprehensive development setup with pre-commit hooks
- Automated CI/CD pipeline with GitHub Actions
- Automated release workflow based on conventional commits
- Dependabot configuration for automated dependency updates

### Chore
- Code quality tools (black, isort, flake8, mypy, bandit)
- Security scanning with CodeQL
- Documentation setup with Sphinx
- Comprehensive test suite structure
- Development Makefile for common tasks

### Refactor
- Updated project structure to modern Python standards
- Migrated to pyproject.toml configuration
