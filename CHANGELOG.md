# Changelog

## [v2.12.0](https://github.com/schireson/pytest-mock-resources/compare/v2.11.0...v2.12.0) (2024-06-19)

### Features

* handle CONVERT_TIMEZONE function for Redshift (#214)
([fc21dca](https://github.com/schireson/pytest-mock-resources/commit/fc21dca2616ef56654876e4f103960ef263b686f)),
closes [#214](https://github.com/schireson/pytest-mock-resources/issues/214)
* handle LEN function for Redshift (#212)
([67886e0](https://github.com/schireson/pytest-mock-resources/commit/67886e0d88c6f405c2526d2b0b66bb80af2e1827)),
closes [#212](https://github.com/schireson/pytest-mock-resources/issues/212)
* Improve default postgres driver selection heuristics. (#206)
([f013626](https://github.com/schireson/pytest-mock-resources/commit/f013626c1e0e6b6776d866788542dd2e0a0ed591)),
closes [#206](https://github.com/schireson/pytest-mock-resources/issues/206)

### Fixes

* also allow psycopg2-binary as a valid driver (#208)
([d3f87de](https://github.com/schireson/pytest-mock-resources/commit/d3f87de1928d10399f1a5a9bd4fa02828c22ec8b)),
closes [#208](https://github.com/schireson/pytest-mock-resources/issues/208)

## [v2.11.0](https://github.com/schireson/pytest-mock-resources/compare/v2.10.4...v2.11.0) (2024-03-07)

### Features

* Add flag to clean up postgres databases.
([eeef1ec](https://github.com/schireson/pytest-mock-resources/commit/eeef1ec05748f3c6de9b903cea257ce263df1598))

### [v2.10.4](https://github.com/schireson/pytest-mock-resources/compare/v2.10.3...v2.10.4) (2024-06-10)

#### Features

* handle LEN function for Redshift (#212)
([67886e0](https://github.com/schireson/pytest-mock-resources/commit/67886e0d88c6f405c2526d2b0b66bb80af2e1827)),
closes [#212](https://github.com/schireson/pytest-mock-resources/issues/212)

### [v2.10.3](https://github.com/schireson/pytest-mock-resources/compare/v2.10.2...v2.10.3) (2024-04-15)

#### Fixes

* also allow psycopg2-binary as a valid driver (#208)
([d3f87de](https://github.com/schireson/pytest-mock-resources/commit/d3f87de1928d10399f1a5a9bd4fa02828c22ec8b)),
closes [#208](https://github.com/schireson/pytest-mock-resources/issues/208)

### [v2.10.2](https://github.com/schireson/pytest-mock-resources/compare/v2.10.1...v2.10.2) (2024-04-11)

#### Features

* Improve default postgres driver selection heuristics. (#206)
([f013626](https://github.com/schireson/pytest-mock-resources/commit/f013626c1e0e6b6776d866788542dd2e0a0ed591)),
closes [#206](https://github.com/schireson/pytest-mock-resources/issues/206)

### [v2.10.1](https://github.com/schireson/pytest-mock-resources/compare/v2.10.0...v2.10.1) (2024-03-06)

#### Fixes

* cli loading mechanism. (#203)
([978190f](https://github.com/schireson/pytest-mock-resources/commit/978190f878f0a4c1613e32604bc29d1e1438b2a0)),
closes [#203](https://github.com/schireson/pytest-mock-resources/issues/203)

## [v2.10.0](https://github.com/schireson/pytest-mock-resources/compare/v2.9.2...v2.10.0) (2024-02-01)

### Features

* Add way for 3rd party resources to register into the PMR cli. (#199)
([23e40ad](https://github.com/schireson/pytest-mock-resources/commit/23e40adad366f4bf941228aa70f311462f417d38)),
closes [#199](https://github.com/schireson/pytest-mock-resources/issues/199)
* Implement support for "client_call" in python on whales, with a… (#198)
([4d08df2](https://github.com/schireson/pytest-mock-resources/commit/4d08df2c49ec18878233d510f66d8643a19499c7)),
closes [#198](https://github.com/schireson/pytest-mock-resources/issues/198)

### [v2.9.2](https://github.com/schireson/pytest-mock-resources/compare/v2.9.1...v2.9.2) (2023-09-25)

#### Fixes

* Ensure base model compatibility with DeclarativeBase subclasses. (#197)
([670295c](https://github.com/schireson/pytest-mock-resources/commit/670295c48ef989879834c7dae3359a2c92211a23)),
closes [#197](https://github.com/schireson/pytest-mock-resources/issues/197)
* Yield config rather than the container. (#196)
([eafaf36](https://github.com/schireson/pytest-mock-resources/commit/eafaf3613b118d8c6d4b2642af560b5e2cd606fc)),
closes [#196](https://github.com/schireson/pytest-mock-resources/issues/196)

### [v2.9.1](https://github.com/schireson/pytest-mock-resources/compare/v2.9.0...v2.9.1) (2023-07-24)

#### Fixes

* Set the region when creating the client to assume roles. (#194)
([2236bbe](https://github.com/schireson/pytest-mock-resources/commit/2236bbe3232bb9f4ba946e2db9c1f55cb27060c9)),
closes [#194](https://github.com/schireson/pytest-mock-resources/issues/194)

## [v2.9.0](https://github.com/schireson/pytest-mock-resources/compare/v2.7.0...v2.9.0) (2023-07-12)

### Features

* Implement moto "ordered actions" for declaring a specific bucket state.
(#191)
([14c09b8](https://github.com/schireson/pytest-mock-resources/commit/14c09b8f942ca911c81e42f9dd8d81f3095fbd0c)),
closes [#191](https://github.com/schireson/pytest-mock-resources/issues/191)

### Fixes

* Adjust moto fixtures to work correctly with scopes and to propag… (#193)
([ef68ba9](https://github.com/schireson/pytest-mock-resources/commit/ef68ba9fb88b3f0ddac08391a312ac080782db14)),
closes [#193](https://github.com/schireson/pytest-mock-resources/issues/193)

## [v2.7.0](https://github.com/schireson/pytest-mock-resources/compare/v2.6.13...v2.7.0) (2023-06-06)

### Features

* Implement moto "ordered actions" for declaring a specific bucket state.
([5d6665e](https://github.com/schireson/pytest-mock-resources/commit/5d6665e340a48c7f3ce7cda4a09793986fd4c318))

### [v2.6.13](https://github.com/schireson/pytest-mock-resources/compare/v2.6.12...v2.6.13) (2023-05-23)

#### Fixes

* Increase time to wait for mysql to spin up. (#190)
([5d94aea](https://github.com/schireson/pytest-mock-resources/commit/5d94aeaf93576d2009f0da3568e0a84e0183f7bc)),
closes [#190](https://github.com/schireson/pytest-mock-resources/issues/190)

### [v2.6.12](https://github.com/schireson/pytest-mock-resources/compare/v2.6.11...v2.6.12) (2023-05-03)

#### Features

* Ensure all fixture types are automatically included in the CLI. (#189)
([df55dde](https://github.com/schireson/pytest-mock-resources/commit/df55dde5281d544bd114ccbaab939932a185a173)),
closes [#189](https://github.com/schireson/pytest-mock-resources/issues/189)

### [v2.6.11](https://github.com/schireson/pytest-mock-resources/compare/v2.6.10...v2.6.11) (2023-03-03)

#### Fixes

* Deal with port as given by an env var, which might be a string. (#186)
([b4ae4e7](https://github.com/schireson/pytest-mock-resources/commit/b4ae4e71c6f8ba7cfa0016f0f17292a879a3a470)),
closes [#186](https://github.com/schireson/pytest-mock-resources/issues/186)

### [v2.6.10](https://github.com/schireson/pytest-mock-resources/compare/v2.6.9...v2.6.10) (2023-02-24)

#### Fixes

* Only set AUTOCOMMIT isolation level during internal fixture setup which
requires it.
([fd8d313](https://github.com/schireson/pytest-mock-resources/commit/fd8d313f82aa92fd3d34135e25fc3b74603c9ea5))

### [v2.6.9](https://github.com/schireson/pytest-mock-resources/compare/v2.6.8...v2.6.9) (2023-02-24)

#### Fixes

* Ensure connection gets closed and is compatible with asyncpg. (#184)
([4cc1847](https://github.com/schireson/pytest-mock-resources/commit/4cc184748ed585533694145bf5fabc9ba1b8ce97)),
closes [#184](https://github.com/schireson/pytest-mock-resources/issues/184)

### [v2.6.8](https://github.com/schireson/pytest-mock-resources/compare/v2.6.7...v2.6.8) (2023-02-23)

#### Fixes

* Avoid psycopg2 dependency during the execution of create_postgre… (#183)
([ed488f5](https://github.com/schireson/pytest-mock-resources/commit/ed488f5272e4a1452b1616b89e7c89bba3e6175c)),
closes [#183](https://github.com/schireson/pytest-mock-resources/issues/183)

### [v2.6.7](https://github.com/schireson/pytest-mock-resources/compare/v2.6.6...v2.6.7) (2023-01-19)

#### Fixes

* Remove reliance on undeclared attrs dependency. (#180)
([ac96d42](https://github.com/schireson/pytest-mock-resources/commit/ac96d422cebf78dd511e99e9c45f84298ab4fe95)),
closes [#180](https://github.com/schireson/pytest-mock-resources/issues/180)

### [v2.6.6](https://github.com/schireson/pytest-mock-resources/compare/v2.6.5...v2.6.6) (2023-01-13)

#### Features

* Add engine_kwargs argument to mysql fixture. (#178)
([d522be8](https://github.com/schireson/pytest-mock-resources/commit/d522be82cd3a08b886fb504429b315f30d7280eb)),
closes [#178](https://github.com/schireson/pytest-mock-resources/issues/178)

### [v2.6.5](https://github.com/schireson/pytest-mock-resources/compare/v2.6.4...v2.6.5) (2022-12-27)

#### Fixes

* Address compatibilities with sqlalchemy 2. (#176)
([0415c78](https://github.com/schireson/pytest-mock-resources/commit/0415c7841e439d4120685f7ac995b346e2ab94b9)),
closes [#176](https://github.com/schireson/pytest-mock-resources/issues/176)

### [v2.6.4](https://github.com/schireson/pytest-mock-resources/compare/v2.6.3...v2.6.4) (2022-12-21)

#### Fixes

* Move port selection into the filelock. (#174)
([76c7ed3](https://github.com/schireson/pytest-mock-resources/commit/76c7ed37cb2c6c63e979b881eac6f820ee07eaf5)),
closes [#174](https://github.com/schireson/pytest-mock-resources/issues/174)

### [v2.6.3](https://github.com/schireson/pytest-mock-resources/compare/v2.6.1...v2.6.3) (2022-10-27)

#### Fixes

* Decide on behavior support for multiple redshift statements. (#172)
([e9d5f0f](https://github.com/schireson/pytest-mock-resources/commit/e9d5f0f9d63cb27052bea2ea2d75186623c55f39)),
closes [#172](https://github.com/schireson/pytest-mock-resources/issues/172)

### [v2.6.1](https://github.com/schireson/pytest-mock-resources/compare/v2.6.0...v2.6.1) (2022-10-20)

#### Fixes

* Fix redshift event listener interaction with the session keyword. (#171)
([088b180](https://github.com/schireson/pytest-mock-resources/commit/088b1800948d131a44236c57154e062dfb9cc7b2)),
closes [#171](https://github.com/schireson/pytest-mock-resources/issues/171)

## [v2.6.0](https://github.com/schireson/pytest-mock-resources/compare/v2.5.1...v2.6.0) (2022-10-07)

### Features

* Add support for moto as a fixture. (#169)
([d405c7d](https://github.com/schireson/pytest-mock-resources/commit/d405c7d4739d4d1fc4ed5fe6d41f53472deee214)),
closes [#169](https://github.com/schireson/pytest-mock-resources/issues/169)

### Fixes

* Docs build. (#168)
([ee6ea37](https://github.com/schireson/pytest-mock-resources/commit/ee6ea371619ae3ab6b2279495cf421f72d39bdd9)),
closes [#168](https://github.com/schireson/pytest-mock-resources/issues/168)

### [v2.5.1](https://github.com/schireson/pytest-mock-resources/compare/v2.5.0...v2.5.1) (2022-09-16)

#### Fixes

* async engine bug related to engine reuse in a different async loop. (#166)
([3254bd8](https://github.com/schireson/pytest-mock-resources/commit/3254bd8f30fd9bd4c435f27c0995a747cc8d5691)),
closes [#166](https://github.com/schireson/pytest-mock-resources/issues/166)

## [v2.5.0](https://github.com/schireson/pytest-mock-resources/compare/v2.4.5...v2.5.0) (2022-08-24)

### Fixes

* Address incompatibility with strict mode for pytest-asyncio in 0.17.0 and
beyond.
([ead7243](https://github.com/schireson/pytest-mock-resources/commit/ead724376c398cd25c46acb2578d3b05b53aba16))

### [v2.4.5](https://github.com/schireson/pytest-mock-resources/compare/v2.4.4...v2.4.5) (2022-09-15)

#### Fixes

* async engine bug related to engine reuse in a different async loop.
([15cab91](https://github.com/schireson/pytest-mock-resources/commit/15cab91003f76b6dd3109489b338ea0d46851ed1))

### [v2.4.4](https://github.com/schireson/pytest-mock-resources/compare/v2.4.3...v2.4.4) (2022-08-12)

### [v2.4.3](https://github.com/schireson/pytest-mock-resources/compare/v2.4.2...v2.4.3) (2022-07-20)

### [v2.4.2](https://github.com/schireson/pytest-mock-resources/compare/v2.4.1...v2.4.2) (2022-07-14)

#### Fixes

* Incompatilities with sqlalchemy 1.3.
([dbdca54](https://github.com/schireson/pytest-mock-resources/commit/dbdca546fa64142f01aab193f3c48c66e995973f))

### [v2.4.1](https://github.com/schireson/pytest-mock-resources/compare/v2.4.0...v2.4.1) (2022-06-28)

#### Fixes

* Address bug which fails to create schemas for MetaData beyond the first, in
a series of ordered actions.
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
