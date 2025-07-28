# [1.12.0](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.11.0...v1.12.0) (2025-07-28)


### Bug Fixes

* **time_series_tab:** improve integrated charge display and tooltip formatting ([15cfa14](https://github.com/mateuszpolis/AgeingAnalysis/commit/15cfa14a468d16e0397c02b46d046f6f26d28dfa))


### Features

* **ageing_analysis:** add integrated charge functionality to AgeingAnalysisApp ([ed556e0](https://github.com/mateuszpolis/AgeingAnalysis/commit/ed556e06e50e7da6c782d82dbd1bd576b377e775))
* **ageing_analysis:** add integrated charge progress window and update calculation process ([071e93a](https://github.com/mateuszpolis/AgeingAnalysis/commit/071e93adb587da07f2c1c7b80fa1bc5955627565))
* **ageing_analysis:** enhance GUI with logo support and window icon management ([3cfcf53](https://github.com/mateuszpolis/AgeingAnalysis/commit/3cfcf536630eee17ccb98b7f86be5cb452826230))
* **ageing_analysis:** implement integrated charge calculation and configuration saving ([12bf28d](https://github.com/mateuszpolis/AgeingAnalysis/commit/12bf28d2ba1cfa4608479f6d5eff1e8c5d124cfa))
* **cfd_rate_integration_service:** add CFDRateIntegrationService for CFD rate integration ([400a8dc](https://github.com/mateuszpolis/AgeingAnalysis/commit/400a8dc1392102ddbedaf6613f3d9298a9a5cdb2))
* **cfd_rate_integration_service:** add multiply_by_mu parameter for CFD rate calculations ([0d8dfe5](https://github.com/mateuszpolis/AgeingAnalysis/commit/0d8dfe55ef928780629545eefbf755178c86026a))
* **cfd_rate_integration_service:** enhance CFDRateIntegrationService with logging and coverage improvements ([86d3894](https://github.com/mateuszpolis/AgeingAnalysis/commit/86d38942c0bc888e779ac0f4de2c33b8c5f194f8))
* **cfd_rate_integration_service:** enhance date handling and add unit tests ([95eddf0](https://github.com/mateuszpolis/AgeingAnalysis/commit/95eddf0e8acbf0674143576ccd663e574a057783))
* **da_batch_client:** add DA_batch_client integration for file upload and result retrieval ([e81f4e8](https://github.com/mateuszpolis/AgeingAnalysis/commit/e81f4e84c5cb1633538054161ef48f1abd7d533e))
* **darma_api_service:** enhance DA_batch_client integration with error handling ([40dafeb](https://github.com/mateuszpolis/AgeingAnalysis/commit/40dafebaf1ec73cc29eebc07a28f22bae03e43fe))
* **darma_api_service:** implement DA_batch_client integration for data retrieval ([46d3d74](https://github.com/mateuszpolis/AgeingAnalysis/commit/46d3d74ccd54abb1250681b1081686e75817a885))
* **dependencies:** add pyarrow and requests for parquet support and DA_batch_client ([9bc5302](https://github.com/mateuszpolis/AgeingAnalysis/commit/9bc53021523400cd3781dc5cf0986f7020060ed0))

# [1.11.0](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.10.0...v1.11.0) (2025-07-22)


### Features

* **ageing_analysis:** add prompt for saving results after analysis completion ([a8c5246](https://github.com/mateuszpolis/AgeingAnalysis/commit/a8c5246d3f547028770ff3c18c15fb16a88575a1))

# [1.10.0](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.9.0...v1.10.0) (2025-07-22)


### Features

* **grid_visualization:** add custom colormap option for grid visualization ([f01eab4](https://github.com/mateuszpolis/AgeingAnalysis/commit/f01eab4b90f9229cfe7dd018d396c0e2a4c34a62))

# [1.9.0](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.8.8...v1.9.0) (2025-07-22)


### Features

* **data_parser:** improve non-reference channel data processing and refactor peak detection plotting ([f9b364c](https://github.com/mateuszpolis/AgeingAnalysis/commit/f9b364c13e1f307d954fa695c8b5fc5407ec809c))

## [1.8.8](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.8.7...v1.8.8) (2025-07-18)


### Bug Fixes

* improve logging and parameter adjustments in AgeingAnalysisApp and GridVisualizationService ([1cb9727](https://github.com/mateuszpolis/AgeingAnalysis/commit/1cb9727f62839c32f5f4c37b2fc0d4658ee5b0e5))

## [1.8.7](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.8.6...v1.8.7) (2025-07-18)


### Bug Fixes

* **tests:** add local_only marker for selective test execution ([17b173c](https://github.com/mateuszpolis/AgeingAnalysis/commit/17b173c6467e1408cd1a474fe7043429483c53bb))

## [1.8.6](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.8.5...v1.8.6) (2025-07-18)


### Bug Fixes

* enhance fallback mechanism and add mock mappings in GridVisualizationService ([16ca756](https://github.com/mateuszpolis/AgeingAnalysis/commit/16ca7561f824ac140a0badeaa3cae91e924168a5))

## [1.8.5](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.8.4...v1.8.5) (2025-07-18)


### Bug Fixes

* update test for save_results to verify filename pattern ([acd8bb2](https://github.com/mateuszpolis/AgeingAnalysis/commit/acd8bb2599be54a36accc04131ef1e56fd992758))

## [1.8.4](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.8.3...v1.8.4) (2025-07-18)


### Bug Fixes

* enhance fallback mechanism for loading mappings in GridVisualizationService ([911b9d0](https://github.com/mateuszpolis/AgeingAnalysis/commit/911b9d0395b1d8669ae0e53beb6f08e581eb13d8))

## [1.8.3](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.8.2...v1.8.3) (2025-07-18)


### Bug Fixes

* improve error handling and logging in GridVisualizationService ([f9ade8e](https://github.com/mateuszpolis/AgeingAnalysis/commit/f9ade8ea435e4ba5b4f645efa07dc4fa8155ffe2))

## [1.8.2](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.8.1...v1.8.2) (2025-07-18)


### Bug Fixes

* enhance grid visualization with date comparison ([42ef4dd](https://github.com/mateuszpolis/AgeingAnalysis/commit/42ef4dde984d69976d86e670cae2d410e2169f67))

## [1.8.1](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.8.0...v1.8.1) (2025-07-18)


### Bug Fixes

* improve progress updates and tooltip information in analysis ([02d1412](https://github.com/mateuszpolis/AgeingAnalysis/commit/02d1412feceebb6fa05dbc8377b57d5ebf4cface))

# [1.8.0](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.7.0...v1.8.0) (2025-07-17)


### Features

* add ageing factor selection to grid visualization ([1bb2263](https://github.com/mateuszpolis/AgeingAnalysis/commit/1bb2263aebc24db820b173e773312f5d60e988d5))

# [1.7.0](https://github.com/mateuszpolis/AgeingAnalysis/compare/v1.6.0...v1.7.0) (2025-07-17)


### Features

* add new dataset comparison JSON and enhance Gaussian fitting service ([924dc64](https://github.com/mateuszpolis/AgeingAnalysis/commit/924dc64b1e9b3eea3c7beb1ebfc3e92dcf66a8bc))

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
