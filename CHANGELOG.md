# Changelog

## [Unreleased](https://github.com/schireson/pytest-mock-resources/compare/v2.5.0...HEAD) (2022-09-15)

### Fixes

* async engine bug related to engine reuse in a different async loop.
  ([5135031](https://github.com/schireson/pytest-mock-resources/commit/5135031b0f8d83957b9c899331a85251d459a0ba))

## [v2.5.0](https://github.com/schireson/pytest-mock-resources/compare/v2.4.4...v2.5.0) (2022-08-24)

### Fixes

* Address incompatibility with strict mode for pytest-asyncio in 0.17.0 and  
beyond.
  ([ead7243](https://github.com/schireson/pytest-mock-resources/commit/ead724376c398cd25c46acb2578d3b05b53aba16))

### [v2.4.4](https://github.com/schireson/pytest-mock-resources/compare/v2.4.3...v2.4.4) (2022-08-12)

### [v2.4.3](https://github.com/schireson/pytest-mock-resources/compare/v2.4.2...v2.4.3) (2022-07-20)

### [v2.4.2](https://github.com/schireson/pytest-mock-resources/compare/v2.4.1...v2.4.2) (2022-07-14)

#### Fixes

* Incompatilities with sqlalchemy 1.3.
  ([dbdca54](https://github.com/schireson/pytest-mock-resources/commit/dbdca546fa64142f01aab193f3c48c66e995973f))

### [v2.4.1](https://github.com/schireson/pytest-mock-resources/compare/v2.4.0...v2.4.1) (2022-06-28)

#### Fixes

* Address bug which fails to create schemas for MetaData beyond the first, in a  
series of ordered actions.
  ([2feca11](https://github.com/schireson/pytest-mock-resources/commit/2feca115002648e2a381b0ed91c945129bf40235))

## [v2.4.0](https://github.com/schireson/pytest-mock-resources/compare/v2.3.0...v2.4.0) (2022-06-15)

### Features

* Amortize the cost of database setup through the use of database templates.
  ([4c3c1f8](https://github.com/schireson/pytest-mock-resources/commit/4c3c1f8fd467b4e78c96e857a4dd5a219748c67a))

## [v2.3.0](https://github.com/schireson/pytest-mock-resources/compare/v2.2.7...v2.3.0) (2022-04-28)

### Features

* Support non-session scoped containers.
  ([0d1474a](https://github.com/schireson/pytest-mock-resources/commit/0d1474ac7415da6791f5b760386bd01d1c87dfee))

### [v2.2.7](https://github.com/schireson/pytest-mock-resources/compare/v2.2.6...v2.2.7) (2022-04-05)

#### Fixes

* Address sqlalchemy 2 warnings.
  ([98f2c0b](https://github.com/schireson/pytest-mock-resources/commit/98f2c0bd13435979e4ad3b7d2df9e1fb20504499))

### [v2.2.6](https://github.com/schireson/pytest-mock-resources/compare/v2.2.5...v2.2.6) (2022-03-30)

#### Fixes

* Add missing stub config option to pmr command setup.
  ([8ca0491](https://github.com/schireson/pytest-mock-resources/commit/8ca049129294321c02bbd41ef052a14f454bb0cf))

### [v2.2.5](https://github.com/schireson/pytest-mock-resources/compare/v2.2.3...v2.2.5) (2022-02-25)

#### Features

* Add missing container types and use pmr internals for cli.
  ([37fb772](https://github.com/schireson/pytest-mock-resources/commit/37fb772f1d97459f87add09a8f4a8357bfc7db31))
* Refactor redshift fixture to be "first class".
  ([a4e71ee](https://github.com/schireson/pytest-mock-resources/commit/a4e71ee38a0b17573d0beeec689fc04a8873ed61))

#### Fixes

* Bump mypy and safe-parallelize tests.
  ([be14cf5](https://github.com/schireson/pytest-mock-resources/commit/be14cf53754888a86567d44cb98e445c02659aa4))
* Add missing example inits, leading to mypy caching problems.
  ([436c8b2](https://github.com/schireson/pytest-mock-resources/commit/436c8b2c66c97931b701b29857d3789c2455f392))
* Add additional "docker" extra.
  ([891938f](https://github.com/schireson/pytest-mock-resources/commit/891938fc3f88e8b3287cffe7e0c221d8bf1868c2))

### [v2.2.3](https://github.com/schireson/pytest-mock-resources/compare/v2.2.2...v2.2.3) (2022-02-23)

#### Features

* Refactor redshift fixture to be "first class".
  ([1a3076d](https://github.com/schireson/pytest-mock-resources/commit/1a3076d4af51306a746908800f09e886e5a56993))

### [v2.2.2](https://github.com/schireson/pytest-mock-resources/compare/v2.2.1...v2.2.2) (2022-02-23)

### [v2.2.1](https://github.com/schireson/pytest-mock-resources/compare/v2.2.0...v2.2.1) (2022-02-22)

## [v2.2.0](https://github.com/schireson/pytest-mock-resources/compare/v2.1.12...v2.2.0) (2022-02-14)

### Features

* Perform container cleanup in a multiprocess safe way.
  ([10a9946](https://github.com/schireson/pytest-mock-resources/commit/10a9946f87a1c24aee97c39b16878d5105e4362b))

### [v2.1.12](https://github.com/schireson/pytest-mock-resources/compare/v2.1.11...v2.1.12) (2022-02-08)

#### Features

* Add the ability to specify custom engine kwargs.
  ([a87b234](https://github.com/schireson/pytest-mock-resources/commit/a87b2344026f5ad9157ce81db1dc5e35a06d50ba))

### [v2.1.11](https://github.com/schireson/pytest-mock-resources/compare/v2.1.10...v2.1.11) (2022-01-11)

#### Fixes

* Add missingn py.typed.
  ([b422bec](https://github.com/schireson/pytest-mock-resources/commit/b422bec2ef0fc8ccc94dd08d799894de295ed9f5))

### [v2.1.10](https://github.com/schireson/pytest-mock-resources/compare/v2.1.9...v2.1.10) (2022-01-07)

#### Features

* Add configurable template option for postgres database creation.
  ([6305307](https://github.com/schireson/pytest-mock-resources/commit/6305307fda52c7e4e16d0ed7772034685430056b))

#### Fixes

* linter errors and linter config which allowed linting errors to pass CI
  ([4a75c9c](https://github.com/schireson/pytest-mock-resources/commit/4a75c9cf1a9267328a1f5bb48a55785289020d83))

### [v2.1.9](https://github.com/schireson/pytest-mock-resources/compare/v2.1.8...v2.1.9) (2021-12-22)

#### Features

* Enable multiprocess (xdist) use of the redis fixture.
  ([103e58b](https://github.com/schireson/pytest-mock-resources/commit/103e58b3a329e7ff6577d8114942fcbd54c4c398))

### [v2.1.8](https://github.com/schireson/pytest-mock-resources/compare/v2.1.7...v2.1.8) (2021-12-03)

#### Fixes

* Broken MySQL container startup. MYSQL_USER for root user can no longer be  
supplied to container.
  ([2561be4](https://github.com/schireson/pytest-mock-resources/commit/2561be475d258f9d5a41acf6d3fd74557a531881))

### [v2.1.7](https://github.com/schireson/pytest-mock-resources/compare/v2.1.6...v2.1.7) (2021-12-01)

#### Fixes

* breaking changes required to support pymongo 4.0.
  ([8e9a079](https://github.com/schireson/pytest-mock-resources/commit/8e9a079b1c3d0abe420622806df7563e9278c8ab))

### [v2.1.6](https://github.com/schireson/pytest-mock-resources/compare/v2.1.5...v2.1.6) (2021-11-22)

#### Fixes

* Preempt socket warnings produced by the client not being closed manually.
  ([4b3d9e0](https://github.com/schireson/pytest-mock-resources/commit/4b3d9e0db304f56ee6ac7cf8cc0be9a6b67c22fa))
* readthedocs poetry error.
  ([6369064](https://github.com/schireson/pytest-mock-resources/commit/636906460936a4f5f632e5b24d5cc696fdf502d3))

### [v2.1.5](https://github.com/schireson/pytest-mock-resources/compare/v2.1.3...v2.1.5) (2021-11-22)

#### Features

* Add ability to change image when running pmr
  ([c8679ec](https://github.com/schireson/pytest-mock-resources/commit/c8679ec535c421db7868209f883c13b38d26d1de))
* Use sqlalchemy's event system to apply redshift behavior.
  ([2455620](https://github.com/schireson/pytest-mock-resources/commit/2455620b7b9dd08b92e0ac33d625eb83cd6eeeaf))

#### Fixes

* Create pytest markers for all resources
  ([1c7c449](https://github.com/schireson/pytest-mock-resources/commit/1c7c4490b520472a233426d6eee49dbe119b402a))
* Avoid mocking all of psycopg2 in the name of redshift.
  ([6f38823](https://github.com/schireson/pytest-mock-resources/commit/6f388237d7ca51b5d5ce5739fb717bf242cfc86c))

### [v2.1.3](https://github.com/schireson/pytest-mock-resources/compare/v2.1.2...v2.1.3) (2021-09-20)

#### Fixes

* Avoid deprecated sqlalchemy URL constructor.
  ([3fa64d3](https://github.com/schireson/pytest-mock-resources/commit/3fa64d34988d6521e1853e17f1817ce3d497c75c))

### [v2.1.2](https://github.com/schireson/pytest-mock-resources/compare/v2.1.1...v2.1.2) (2021-08-24)

#### Fixes

* support for sqlalchemy 1.3.
  ([7fa4fda](https://github.com/schireson/pytest-mock-resources/commit/7fa4fda9fd943aad01a53f7c5355b56fcc3da290))
* Use the proper MYSQL_USER env var for the mysql fixture.
  ([648a0b1](https://github.com/schireson/pytest-mock-resources/commit/648a0b1eaea25d684e1b2f0701bb92ada9f7a6ba))
* Resolve linting issues related to changing linter versions.
  ([59a983f](https://github.com/schireson/pytest-mock-resources/commit/59a983f2f0e812986d3729bb257ef01712831208))
* Address poor handling of SQL statement parsing for redshift.
  ([d0d7685](https://github.com/schireson/pytest-mock-resources/commit/d0d7685b42e21ca2cf23d2cd4e1e5d91a044e87d))

### [v2.1.1](https://github.com/schireson/pytest-mock-resources/compare/v2.1.0...v2.1.1) (2021-08-17)

#### Fixes

* Resolve linting issues related to changing linter versions.
  ([7aebc6a](https://github.com/schireson/pytest-mock-resources/commit/7aebc6a8be458b31e96bc1e15cea1a14a6ab6818))
* Address poor handling of SQL statement parsing for redshift.
  ([11c4b97](https://github.com/schireson/pytest-mock-resources/commit/11c4b97524505ece6dc3779f12109b5f11f2fbc4))

## [v2.1.0](https://github.com/schireson/pytest-mock-resources/compare/v2.0.0...v2.1.0) (2021-06-29)

### Features

* Add async support (postgres)
  ([f45b078](https://github.com/schireson/pytest-mock-resources/commit/f45b0781482f9e4d0bd2d533e9840b5cc5b8ac1d))

## [v2.0.0](https://github.com/schireson/pytest-mock-resources/compare/v1.5.0...v2.0.0) (2021-06-02)

## [v1.5.0](https://github.com/schireson/pytest-mock-resources/compare/v1.4.1...v1.5.0) (2021-02-17)

### [v1.4.1](https://github.com/schireson/pytest-mock-resources/compare/v1.4.0...v1.4.1) (2020-10-08)

#### Fixes

* Support breaking changes in pytest 6.
  ([d6dba02](https://github.com/schireson/pytest-mock-resources/commit/d6dba02b9492550f48520f6ebd91107f3f9d74b6))

## [v1.4.0](https://github.com/schireson/pytest-mock-resources/compare/v1.3.2...v1.4.0) (2020-08-25)

### Features

* Allow globbing table names to select subsets of tables.
  ([55a8aaf](https://github.com/schireson/pytest-mock-resources/commit/55a8aafc7e73d3bc94b969e06125d1056070e06c))

### [v1.3.2](https://github.com/schireson/pytest-mock-resources/compare/v1.2.2...v1.3.2) (2020-05-28)

#### Features

* Add mysql support
  ([4a79ca6](https://github.com/schireson/pytest-mock-resources/commit/4a79ca60d57f6f53c6f71d170c1b6134a1fc0d02))

#### Fixes

* Change user from 'user' to 'root' in mysql fixture method
  ([d1e193b](https://github.com/schireson/pytest-mock-resources/commit/d1e193b6bcbdbd0399725bb76d3ba4ad145388d9))

### [v1.2.2](https://github.com/schireson/pytest-mock-resources/compare/v1.2.1...v1.2.2) (2020-04-02)

### [v1.2.1](https://github.com/schireson/pytest-mock-resources/compare/v1.0.0...v1.2.1) (2020-03-26)

## v1.0.0 (2020-01-23)
