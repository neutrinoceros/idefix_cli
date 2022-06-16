# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.19.2] - 2022-06-16

BUG: fix a bug where source files directly at the top of src/ would be ignored
in compilation check by idfx run

## [0.19.1] - 2022-06-15

BUG: fix an error message in idfx run

## [0.19.0] - 2022-06-15

ENH: make logs stand out more with colors and markup

## [0.18.0] - 2022-06-15

ENH: add support to pass arbitrary arguments to idefix via idfx run

This is a breaking change because `idfx run` previously had one optional
positional argument `directory`, which is now a named argument `--dir` (but
still defaults to the current dir).

## [0.17.1] - 2022-06-14

BUG: fix a bug where idfx run would crash instead of compiling idefix


## [0.17.0] - 2022-06-10

ENH: replace custom solution with stdlib's contextlib.chdir in Python 3.11, vendor it for older versions

Several enhancements to idfx run
- ENH: don't create a temporary inputfile if no edits are required
- ENH: prioritize checking for executable (or Markefile) over inifile in error message for idfx run
- ENH: add support for mpirun in idfx run


## [0.16.0] - 2022-05-24

ENH: use inifix's binary mode to maximize portability, bump minimal supported version to 3.0.0


## [0.15.1] - 2022-05-23

- BUG: fix error messages in idfx clone
- BUG: fix a bug where os.path.setp-terminated target dir would cause a crash in idfx clone

## [0.15.0] - 2022-04-22

ENH: idfx run --one now accepts optional and arbitrary output format identifiers.
For instance

```
$ idfx run --one dmp vtk
```
will run the curdir setup for one time step and output both a dmp file and a vtk file.

## [0.14.2] - 2022-03-16

BUG: fix a bug where the list of files checked for edit time by idfx run was not inclusive enough.


## [0.14.1] - 2022-03-16

BUG: fix a bug where the list of files checked for edit time by idfx run was too inclusive.

## [0.14.0] - 2022-03-15

ENH: idfx run now detects changes in idefix source files since last compilation

## [0.13.3] - 2022-03-14

BUG: same fix as 0.13.2, this time done more carefully.

## [0.13.2] - 2022-03-14 (yanked)

BUG: fix a bug where `-gpu` flag wasn't implied by using a known GPU target architecture in idfx conf

## [0.13.1] - 2022-03-04

BUG: make version parsing more robust to accomodate for loose upstream standards


## [0.13.0] - 2022-02-23

ENH: check for updated source in idfx run and offer to recompile on the fly


## [0.12.1] - 2022-02-23

BUG: fix a broken error message


## [0.12.0] - 2022-02-23

ENH: idfx clone now copies *all* C and C++ source files (`*.h`, `*.c`, `*.hpp`,
`*.cpp`) from the target directory, instead of just `definitions.hpp` and
`setup.cpp`.


## [0.11.3] - 2022-02-22

BUG: fix a bug in idfx clone where symlinks would be generated to missing files https://github.com/neutrinoceros/idefix_cli/pull/101


## [0.11.2] - 2021-12-25

- ENH: fix help message
https://github.com/neutrinoceros/idefix_cli/pull/96
- ENH: improve plugin system validation (check for missing docstrings)
https://github.com/neutrinoceros/idefix_cli/pull/97

## [0.11.1] - 2021-12-25
ENH: improve command plugin validation and increase main module test coverage
https://github.com/neutrinoceros/idefix_cli/pull/95


## [0.11.0] - 2021-12-24

- ENH: improvements to `idfx clean`
  * make idfx clean interactive: no file is removed without an informed
    confirmation, --dry is repurposed to skip prompt
  * improve info messages in idfx clean
  * improve cmake support (detect build/ dir)
https://github.com/neutrinoceros/idefix_cli/pull/94

- ENH: add support for -arch, -gpu, -cxx options with CMake, and support their
  equivalent options from .config/idefix.cfg
https://github.com/neutrinoceros/idefix_cli/pull/93


## [0.10.0] - 2021-12-05
ENH: add `-i/--interactive` flag to `idfx conf` to invoke `ccmake` instead of `cmake`.
https://github.com/neutrinoceros/idefix_cli/pull/92


## [0.9.0] - 2021-12-04

ENH: improve idfx conf for versions of Idefix that don't have configure.py
https://github.com/neutrinoceros/idefix_cli/pull/89


## [0.8.0] - 2021-10-11

MNT: add explicit support for Python 3.10
https://github.com/neutrinoceros/idefix_cli/pull/86

## [0.7.0] - 2021-09-23

ENH: add provisional support for CMake configuration (Idefix 0.9)
https://github.com/neutrinoceros/idefix_cli/pull/70

## [0.6.1] - 2021-09-23

BUG: fix a breaking with idfx conf
https://github.com/neutrinoceros/idefix_cli/pull/84

## [0.6.0] - 2021-09-23

- MNT: rename modules, idfx setup is now idfx conf
  https://github.com/neutrinoceros/idefix_cli/pull/82

- MNT: add support for Python 3.8
  https://github.com/neutrinoceros/idefix_cli/pull/83

## [0.5.0] - 2021-09-23

ENH: implement a plugin architecture for commands
https://github.com/neutrinoceros/idefix_cli/pull/81


## [0.4.5] - 2021-08-31

ENH: programatically guarantee that git-indexed files cannot be removed by `idfx
clean` https://github.com/neutrinoceros/idefix_cli/pull/77

## [0.4.4] - 2021-08-30

- ENH: add preliminary support for cmake via additional globals and functions in
  idefix_cli._commons module https://github.com/neutrinoceros/idefix_cli/pull/75

- BUG: fix version parsing for Idefix in idfx stamp
  https://github.com/neutrinoceros/idefix_cli/pull/76

## [0.4.3] - 2021-08-26

MNT: bump dependencies versions

## [0.4.2] - 2021-08-17

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
