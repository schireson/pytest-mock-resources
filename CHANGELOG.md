# Changelog

## [v2.4.0](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.3.0...v2.4.0) (2022-06-15)

### Features

* Amortize the cost of database setup through the use of database templates. fdd8317
* Support non-session scoped containers. 0d1474a


## [v2.3.0](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.2.6...v2.3.0) (2022-04-05)

### Fixes

* Address sqlalchemy 2 warnings. 98f2c0b


### [v2.2.6](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.2.5...v2.2.6) (2022-03-30)

#### Fixes

* Add missing stub config option to pmr command setup. 8ca0491


### [v2.2.5](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.2.3...v2.2.5) (2022-02-25)

#### Features

* Add missing container types and use pmr internals for cli. 37fb772
* Refactor redshift fixture to be "first class". a4e71ee

#### Fixes

* Bump mypy and safe-parallelize tests. be14cf5
* Add missing example inits, leading to mypy caching problems. 436c8b2
* Add additional "docker" extra. 891938f


### [v2.2.3](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.2.2...v2.2.3) (2022-02-23)

#### Features

* Refactor redshift fixture to be "first class". 1a3076d


### [v2.2.2](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.2.1...v2.2.2) (2022-02-23)


### [v2.2.1](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.2.0...v2.2.1) (2022-02-22)


## [v2.2.0](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.1.12...v2.2.0) (2022-02-14)

### Features

* Perform container cleanup in a multiprocess safe way. 10a9946


### [v2.1.12](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.1.11...v2.1.12) (2022-02-08)

#### Features

* Add the ability to specify custom engine kwargs. a87b234


### [v2.1.11](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.1.10...v2.1.11) (2022-01-11)

#### Fixes

* Add missingn py.typed. b422bec


### [v2.1.10](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.1.9...v2.1.10) (2022-01-07)

#### Features

* Add configurable template option for postgres database creation. 6305307

#### Fixes

* linter errors and linter config which allowed linting errors to pass CI 4a75c9c


### [v2.1.9](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.1.8...v2.1.9) (2021-12-22)

#### Features

* Enable multiprocess (xdist) use of the redis fixture. 103e58b


### [v2.1.8](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.1.7...v2.1.8) (2021-12-03)

#### Fixes

* Broken MySQL container startup. MYSQL_USER for root user can no longer be supplied to container. 2561be4


### [v2.1.7](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.1.6...v2.1.7) (2021-12-01)

#### Fixes

* breaking changes required to support pymongo 4.0. 8e9a079


### [v2.1.6](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.1.5...v2.1.6) (2021-11-22)

#### Fixes

* Preempt socket warnings produced by the client not being closed manually. 4b3d9e0
* readthedocs poetry error. 6369064


### [v2.1.5](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.1.3...v2.1.5) (2021-11-22)

#### Features

* Add ability to change image when running pmr c8679ec
* Use sqlalchemy's event system to apply redshift behavior. 2455620

#### Fixes

* Create pytest markers for all resources 1c7c449
* Avoid mocking all of psycopg2 in the name of redshift. 6f38823


### [v2.1.3](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.1.2...v2.1.3) (2021-09-20)

#### Fixes

* Avoid deprecated sqlalchemy URL constructor. 3fa64d3


### [v2.1.2](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.1.1...v2.1.2) (2021-08-24)

#### Fixes

* support for sqlalchemy 1.3. 7fa4fda
* Use the proper MYSQL_USER env var for the mysql fixture. 648a0b1
* Resolve linting issues related to changing linter versions. 59a983f
* Address poor handling of SQL statement parsing for redshift. d0d7685


### [v2.1.1](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.1.0...v2.1.1) (2021-08-17)

#### Fixes

* Resolve linting issues related to changing linter versions. 7aebc6a
* Address poor handling of SQL statement parsing for redshift. 11c4b97


## [v2.1.0](https://github.com/schireson/schireson-pytest-mock-resources/compare/v2.0.0...v2.1.0) (2021-06-29)

### Features

* Add async support (postgres) f45b078


## [v2.0.0](https://github.com/schireson/schireson-pytest-mock-resources/compare/v1.5.0...v2.0.0) (2021-06-02)


## [v1.5.0](https://github.com/schireson/schireson-pytest-mock-resources/compare/v1.4.1...v1.5.0) (2021-02-17)


### [v1.4.1](https://github.com/schireson/schireson-pytest-mock-resources/compare/v1.4.0...v1.4.1) (2020-10-08)

#### Fixes

* Support breaking changes in pytest 6. d6dba02


## [v1.4.0](https://github.com/schireson/schireson-pytest-mock-resources/compare/v1.3.2...v1.4.0) (2020-08-25)

### Features

* Allow globbing table names to select subsets of tables. 55a8aaf


### [v1.3.2](https://github.com/schireson/schireson-pytest-mock-resources/compare/v1.2.2...v1.3.2) (2020-05-28)

#### Features

* Add mysql support 4a79ca6

#### Fixes

* Change user from 'user' to 'root' in mysql fixture method d1e193b


### [v1.2.2](https://github.com/schireson/schireson-pytest-mock-resources/compare/v1.2.1...v1.2.2) (2020-04-02)


### [v1.2.1](https://github.com/schireson/schireson-pytest-mock-resources/compare/v1.0.0...v1.2.1) (2020-03-26)


## v1.0.0 (2020-01-23)


