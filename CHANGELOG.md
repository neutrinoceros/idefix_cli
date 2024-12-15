# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.0.1] - 2024-12-15

- DEP: require inifix 5.1.0 or newer, fix newly detected type-checking errors
- BUG: fix a crash in `idfx run` where a Python exception would be raised
  instead of an error message
- TYP: improve typechecking with pyright

## [6.0.0] - 2024-12-05

- DEP: drop `[isolated]` extra (external tooling should handle dependency pinning)
- BLD: drop package level `__version__` attribute
- BLD: migrate build backend from `setuptools` to `hatchling`
- RFC: refactor theme-handling internals

## [5.2.1] - 2024-09-20

BUG: fix an issue where cloning to a dir with missing parents might create
orphan empty directories if the atomic copy failed. In such an event,
`idfx clone` now attempts to clean up after itself

## [5.2.0] - 2024-09-20

- DOC: minor tweaks and typos
- ENH: `idfx clone` now includes Python files (`*.py`) by default to improve support
  for setups that use `Pydefix` for initialization
- ENH: `idfx clone` now supports cloning to a nested directory, creating parent
  directories as needed
- ENH: `idfx clone` now accepts an `--exclude` argument
- ENH: `idfx conf` now accepts a `-debug` shorthand for `-DIdefix_DEBUG=ON`

## [5.1.0] - 2024-09-18

- BUG: fix a bug where `idfx run` could request more threads than there are physical CPUs
- ENH: add support for error messages with hints

## [5.0.0] - 2023-10-24

- API: drop positional `directory` parameter to `idfx clean`. Replace it with (optional)
  `--dir` parameter, following other commands.


## [4.0.0] - 2023-10-16

- DEP: migrate prompting from rich to termcolor
- API: remove `idfx stamp` command, drop dependency on GitPython
- DEP: bump minimal and pinned `inifix` from 3.0.0 to 4.2.2
- DEPR: rename print_err to print_error, deprecate old name
- ENH: add short version `-i` for `idfx digest --input ...`
- DEPR: expire running deprecations in prep for 4.0 rel

## [3.2.1] - 2023-09-06

- BUG: fix `baballe digest > file.json`
- BUG: fix a bug where `idfx digest` would choke on files where no line is captured

## [3.2.0] - 2023-09-06

ENH: add support for parsing arbitrary files (`idfx digest`)

## [3.1.1] - 2023-09-02

- BUG: exit program after error (`idfx digest`)
- BUG: fix a bug where `idfx digest` would generate invalid json from logs that end with
  an inlined warning or an error

## [3.1.0] - 2023-08-04

ENH: add `--no-confirm` option to `idfx clean`

## [3.0.1] - 2023-08-03

ENH: strip all trailing whitespace in `idfx digest`

## [3.0.0] - 2023-08-02

- ENH: add `-o/--output` argument to `idfx digest`
- PERF: faster type casting in `idfx digest``
- PERF: avoid unnecessary json serialization in `idfx digest`
- ENH: sort log files by process number in `idfx digest`
- API: only parse the first log by default in `idfx digest`

## [2.4.0] - 2023-07-29

- ENH: add a `idfx digest`` command to pre-process performance logs
- TST: test on Python 3.12

## [2.3.3] - 2023-07-28

BUG: copy all `*.ini` files in `idfx clone`

## [2.3.2] - 2023-07-26

- BLD: drop support for Python 3.8
- BUG: avoid spurious warnings and errors when running idefix with `-nolog` or `-nowrite` flags
- DOC: document how to use ccmake through idfx conf

## [2.3.1] - 2023-07-12

There are no functional changes in this release. Infrastructures dependencies were
updated, and this is the first release using PyPI trusted publishers mechanism.

## [2.3.0] - 2023-06-23

- BLD: migrate to src layout
- ENH: Improvements to `idfx run`:
  - step-by-step mode is now more reliable (`--one --times` is translated
    to`-maxcycles`).
  - output types for step-by-step modecan now be specified with the new `--out` option
    (previously they were only parsed from the `--one` option)
  - the `--times` option is deprecated. It is now recommended to use idefix's `-maxcycles` option directly.

## [2.2.0] - 2023-05-06

ENH: let `--nproc` argument in `idfx run` be implicit if `-dec` is also present.

## [2.1.1] - 2023-05-04

- BUG: fix `idfx run` crashing without `--one-step`
- BUG: fix incorrect logging message when running `idfx run` without `--one-step`


## [2.1.0] - 2023-05-04

- ENH: add `idefix_cli.lib.run_subcommand` helper function
- ENH: add new command (`idfx switch`) for switching git branches in `$IDEFIX_DIR`


## [2.0.0] - 2023-04-26

- BUG: fix a bug where `idfx run --one log` would lead to undefined behaviour
- ENH: add support for running idefix_cli as module script (`python -m idefix_cli`)
- ENH: add actual support for running idefix step by step with `idfx run --one ...`
       In previous versions this was done by fixing the time step value at the initial
       value, and didn't work with `-restart`.
       This version is agnostic of how the time step is set, and will interupt idefix
       in a safe way as soon as the desired number of cycles is completed.
- API: disallow abbreviation in command line arguments
- DEPR: deprecate --duration parameter in idfx run
- BUG: fix a bug in `idfx run` where `--times` argument would be silently
  ignored if passed without `--one-step`
- BUG: fix a bug where `idfx run --times -1` would not stop until `tstop` was reached

## [1.2.0] - 2023-04-14

- RFC: replace 'compile' with 'build' internally and in error messages
- ENH: bail out of idfx conf if setup.cpp does not exist

## [1.1.3] - 2023-04-06

BUG: fix a bug where `idfx clone` would crash when including a non-empty directory

## [1.1.2] - 2023-03-03

BUG: fix a bug where `idfx clone --include ...` crashed when a pattern matched a directory

## [1.1.1] - 2023-02-17

- RFC: use a StrEnum for RecompileMode
- DOC: minor fixes for builtin commands docs

## [1.1.0] - 2023-02-17

ENH: `idfx run` now always calls `make` before running Idefix, unless configured otherwise


## [1.0.1] - 2023-02-10

BUG: fix a used-before-definition error detected by mypy

## [1.0.0] - 2023-01-06

* DOC: bootstrap website
* MNT: drop broken toml formatter
* DEPR: rename extension_dir option to plugins_directory
* DOC: document how to configure plugins directory
* ENH: define idefix_cli.lib.__all__
* DOC: define nav
* DOC: document public api idefix_cli.lib
* ENH: move backports to a separate module
* DEPR: remove long-deprecated functionalities
* ENH: implement alternative command

## [0.27.0] - 2022-12-10

* BLD: update CD workflow
* BLD: add the `[isolated]` optional dep target with the effect of pinning dependencies
* RFC: minimise size of future public api module
* RFC: reduce type uncertainty (strict return types)
* TST: rename test file (test_setup.py -> test_conf.py)
* UX: rework help
* ENH: improve phrasing in compilation prompt
* ENH: rename internal module _commons.py to lib.py to mark that it's now public
* RFC: refactor dynamical command loading to avoid deprecation warning
* BUG: fix idfx conf help message and add defaults to all commands help messages

## [0.26.1] - 2022-12-08

BUG: fix packaging issue which made 0.26.0 unusable

## [0.26.0] - 2022-12-08 (yanked)

ENH: enable configuring a directory for user extensions

## [0.25.2] - 2022-09-26

BUG: fix a bug where `idfx run` would not offer to recompile idefix when some options (like IDEFIX_DEBUG) were reconfigured interactively with ccmake.

## [0.25.1] - 2022-08-23

BUG: fix a critical bug introduced in 0.25.0 where `idfx run --one vtk` would crash on a KeyError due to a typo

## [0.25.0] - 2022-08-20

ENH: add `--dir` argument to `idfx conf`

## [0.24.1] - 2022-08-20

ENH: add support for Windows

## [0.24.0] - 2022-07-24

ENH:  add `--times` argument to `idfx run` to run n-steps simulations in combination with `--one`

## [0.23.0] - 2022-07-24

ENH: idfx clone now shows a file tree of files and directories that were created (not in `--shallow` mode)

## [0.22.0] - 2022-07-21

ENH: idfx clean now shows a file tree of files and directories to be removed

## [0.21.2] - 2022-07-19

BUG: fix an unbound variable error in `idfx run`

## [0.21.1] - 2022-07-18

BUG: correctly pass non-zero return value from `idefix` executable to `idfx run`

## [0.21.0] - 2022-06-30

- DOC: clarify and fix a couple example in the README
- ENH: resolve dir path (improve error message in idfx run)
- DEPR: deprecate `[idefix_cli]` configuration section in favor of command specific ones (like `[idfx conf]`)
- ENH: add support for persistent (configured) arbitrary inclusions in `idfx clone`

## [0.20.1] - 2022-06-23

BUG: fix help message for idfx clone:
  - `--shallow` flag was erroneouly marked as not implemented
  - `dest` still referenced a long-gone `--force` flag

## [0.20.0] - 2022-06-18

- ENH: when compiling idefix, always use CPUs in powers of 2 (up to 8), and
  strictly less than the available number. Previously we used `min(8, count//2)`
- ENH: following upstream development, idfx run will now check log files left by
  idefix to determine its return value

## [0.19.3] - 2022-06-16

BUG: fix pattern matching in idfx run again

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
