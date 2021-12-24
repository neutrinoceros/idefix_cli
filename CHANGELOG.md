# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

- ENH: improvements to `idfx clean`
  * make idfx clean interactive: no file is removed without an informed
    confirmation, --dry is repurposed to skip prompt
  * improve info messages in idfx clean
  * improve cmake support (detect build/ dir)
https://github.com/neutrinoceros/idefix_cli/pull/94

## [0.10.0] - 2021-05-12
ENH: add `-i/--interactive` flag to `idfx conf` to invoke `ccmake` instead of `cmake`.
https://github.com/neutrinoceros/idefix_cli/pull/92


## [0.9.0] - 2021-04-12

ENH: improve idfx conf for versions of Idefix that don't have configure.py
https://github.com/neutrinoceros/idefix_cli/pull/89


## [0.8.0] - 2021-11-10

MNT: add explicit support for Python 3.10
https://github.com/neutrinoceros/idefix_cli/pull/86

## [0.7.0] - 2021-23-09

ENH: add provisional support for CMake configuration (Idefix 0.9)
https://github.com/neutrinoceros/idefix_cli/pull/70

## [0.6.1] - 2021-23-09

BUG: fix a breaking with idfx conf
https://github.com/neutrinoceros/idefix_cli/pull/84

## [0.6.0] - 2021-23-09

- MNT: rename modules, idfx setup is now idfx conf
  https://github.com/neutrinoceros/idefix_cli/pull/82

- MNT: add support for Python 3.8
  https://github.com/neutrinoceros/idefix_cli/pull/83

## [0.5.0] - 2021-23-09

ENH: implement a plugin architecture for commands
https://github.com/neutrinoceros/idefix_cli/pull/81


## [0.4.5] - 2021-31-08

ENH: programatically guarantee that git-indexed files cannot be removed by `idfx
clean` https://github.com/neutrinoceros/idefix_cli/pull/77

## [0.4.4] - 2021-30-08

- ENH: add preliminary support for cmake via additional globals and functions in
  idefix_cli._commons module https://github.com/neutrinoceros/idefix_cli/pull/75

- BUG: fix version parsing for Idefix in idfx stamp
  https://github.com/neutrinoceros/idefix_cli/pull/76

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
- refactor: remove error wrapping in `idfx conf` to allow debugging via breakpoints
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
