# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.3] - 2021-26-08

MNT: bump dependencies versions

## [0.4.2] - 2021-17-08

UX: add colored logging and refactor idfx clone to use os.replace for atomicity

## [0.4.1] - 2021-08-05

UX: add a more specific error message when IDEFIX_DIR exists but isn't valid.

## [0.4.0] - 2021-05-30

- refactor: use temporary ini files in `idfx run` to avoid polluting the work
   directory. Remove "temporary" `*.ini_` filename pattern from `idfx clean`'s
   rules (backwards incompat)
- refactor: remove error wrapping in `idfx setup` to allow debugging via breakpoints
- UX: add default values for the `directory` positional argument in `idfx clean` and `idfx run`
- UX: display a clean error message in case idefix itself errors out in `idfx run`

## [0.3.3] - 2021-05-18

- UX: clarify error messages for `idfx run` in case compilation is necessary but
  impossible (either because IDEDIX_DIR isn't configured or the compilation
  itself fails)
- Reduce the maximum number of CPU used for compilation to half the available pool.

## [0.3.2] - 2021-05-10

Fix a bug where idfx would fail to launch when the git executable wasn't available.

## [0.3.1] - 2021-05-04

Fix a bug where idfx clone wouldn't work across multiple devices.

## [0.3.0] - 2021-05-04

- Add the `idfx clone` command
- bump the required version of inifix
