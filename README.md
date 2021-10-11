[![PyPI](https://img.shields.io/pypi/v/idefix_cli)](https://pypi.org/project/idefix-cli/)
![PyPI](https://img.shields.io/pypi/pyversions/idefix_cli/0.8.0?logo=python&logoColor=white&label=Python)
[![codecov](https://codecov.io/gh/neutrinoceros/idefix_cli/branch/main/graph/badge.svg)](https://codecov.io/gh/neutrinoceros/idefix_cli)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/neutrinoceros/idefix_cli/main.svg)](https://results.pre-commit.ci/badge/github/neutrinoceros/idefix_cli/main.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# `idefix_cli:idfx`

This is a CLI helper tool for Idefix, named `idfx`. `idfx` gathers and automates
boring and repetetive tasks such as configuration and cleanup in a single tool.

> Warning: Idefix itself is not publicly available yet.

<!-- toc -->

- [Installation](#installation)
  * [stable](#stable)
  * [bleeding-edge](#bleeding-edge)
- [Internal documentation](#internal-documentation)
- [Commands](#commands)
  * [`idfx clone`](#idfx-clone)
  * [`idfx conf`](#idfx-conf)
  * [`idfx run`](#idfx-run)
    + [minimal example: run a test sequentially](#minimal-example-run-a-test-sequentially)
    + [running a shorter version of a problem](#running-a-shorter-version-of-a-problem)
  * [IO operations for inifiles](#io-operations-for-inifiles)
    + [`idfx read`](#idfx-read)
    + [`idfx write`](#idfx-write)
    + [arbitrary patching](#arbitrary-patching)
  * [`idfx clean`](#idfx-clean)
  * [`idfx stamp`](#idfx-stamp)
- [Contribution guidelines](#contribution-guidelines)
- [Testing](#testing)

<!-- tocstop -->

# Installation

It is recommended to install this tool in isolation with [`pipx`](https://pipxproject.github.io/pipx/) as
```shell
$ pipx install idefix_cli
```

Otherwise, the way to install the latest stable version is
```shell
$ python3 -m pip install -u idefix_cli
```

Note that most `idfx` commands explicitly require that the env variable `$IDEFIX_DIR` be
set.

# Internal documentation

The following contains usage examples. Get a complete description of available options with
```shell
$ idfx --help
```
Likewise, get help for each command therein as, for instance
```shell
$ idfx run --help
```

# Commands

## `idfx clone`

Clone an idefix problem directory by copying the main source files
(`definitions.hpp`, `setup.cpp`, `idefix.ini`).

```shell
$ idfx clone $IDEFIX_DIR/test/HD/KHI/ /tmp/myKHI
```

<details>
<summary>More</summary>
Instead of making hard copies, files can be symbolically linked to instead of
copied, with `--shallow`.

Additional files may be included in the clone using the `--extra` argument. They
can be specified either by name or POSIX pattern, e.g.
```shell
$ idfx clone $IDEFIX_DIR/test/HD/KHI/ /tmp/myKHI --extra *.log
```

</details>

## `idfx conf`

`idfx conf` creates a valid `Makefile` at the specified location and with the speficied
parameters (HD/MHD ? ... see `idfx conf --help`).

> `idfx conf` is a unified wrapper for `$IDEFIX_DIR/configure.py` and `cmake`.
> All arguments and flags are passed down to the prefered system
> Some arguments like `-mhd`, `-mpi` and `-openmp`, originally implemented in
> `$IDEFIX_DIR/configure.py`, are automatically translated for cmake.

A system preference can be configured globally in
`$HOME/.config/idefix.cfg`, as
```ini
[idefix_cli]
conf_system = python
# or
conf_system = cmake
```
Otherwise `idfx conf` will attempt to guess what system should be used base on
availability. Cmake is prefered over Python when available.

## `idfx run`

`idfx run` performs a simulation. It is mostly useful
run tests problems sequentially for very short periods.

Note that this command will fail if neither `idefix` or `Makefile` are found in the
specified directory. In case only the `Makefile` is present, this command will compile the
program first.

> `idfx run` is not a complete wrapper around the `idefix` executable. This means that
> if you need to pass additional arguments to `idefix` other than `-i`, you should run it directly.

### minimal example: run a test sequentially

```shell
$ idfx run $IDEFIX_DIR/test/HD/KHI
```
The default behaviour is to use `idefix.ini` contained in the specified directory. If you
want to run a different one, use `-i/--inifile`
```shell
$ idfx run . -i myconf.ini
```

Note that `idfx run` looks for the inifile relative to the cwd, and _then_ relative to
the specified directory.

### running a shorter version of a problem
Use the `--duration` and `--time-step` arguments to run a modified version of a base
inifile.

```shell
$ idfx run . --duration 1e-4
```

> The patched copy will be save to a `.ini_` file with a unique identifier (UUID).
> Those files are cleaned with other with `idfx clean --all`

Note that `--time-step` maps to Idefix's inifile `TimeIntegrator.first_dt`.

Use `--one-step/--one` to run a single time step (total simulation time equates to the
first time step).
The length of the time step can be adjusted in combination with `--time-step`, however,
`--one-step` is incompatible with `--duration`.

```shell
$ idfx run . --one
```
is a shortcut for
```shell
$ idfx run . --duration x --time-step x
```
where `x`, is the existing value found in the inifile.


## `idfx clean`

Removes generated files.
```shell
$ idfx clean .
```
By default only intermediate C++ (`*.o`, `*.host` and `*.cuda`) files are cleaned.

To also remove `Makefile`, `idefix` executables and `*.ini_` files generated by `idfx`,
run
```shell
$ idfx clean . --all
```

Use the `--dry-run/--dry` flag to print a list of what files _would_ be deleted
without actually deleting anything.


## `idfx stamp`

Prints key data for reproduction and development to stdout.

```shell
$ idfx stamp
v0.5
daff799bb64b0993f058f50779873d594376d5bf
lesurg
f-dahu
Sat Jan 16 16:15:28 2021
```
<details>
<summary>More</summary>

This command is roughly equivalent (and slightly more portable) to
```shell
$ cd $IDEFIX_DIR \
  && git describe --tags \
  && cd - > /dev/null \
  && date \
  && hostname \
  && echo $USER
```
Additionnally, one can get the underlying data in json-serializable format
```shell
$ idfx stamp --json
{
  "tag": "v0.5",
  "sha": "daff799bb64b0993f058f50779873d594376d5bf",
  "user": "glesur",
  "host": "f-dahu",
  "date": "Sat Jan 16 16:15:54 2021"
}
```

This is helpful to quickly store important metadata next to one's datafiles. The git tag
may be of critical value for reproductability, especially when bugs in Idefix are found
after simulations are run, like so

```shell
$ idfx stamp --json > metadata.json
```
</details>

# IO operations for inifiles
## `idfx read`

Read an Idefix inifile and print the resulting dictionnary to stdout in a json parsable
format. This is useful to inspect inifiles programatically in combination with tools like
[jq](https://stedolan.github.io/jq/)
```shell
$ idfx read $IDEFIX_DIR/test/HD/KHI/idefix.ini | jq '.Output.vtk' --compact-output
[0.01,-1,"single_file"]
```

By default, the ouptut of `idfx read` is flat. Optionnaly, you can use `--indent <N>` to
improve human-readability.

## `idfx write`

Conversely, `idfx write` converts from json formatted strings to Idefix inifile format

```shell
$ idfx write save.ini $(cat save.json)
```

### arbitrary patching
`idfx read` and `idfx write` methods can be combined with `jq` to arbitrarily patch an inifile
```shell
$ idfx read test/HD/KHI/idefix.ini | jq .TimeIntegrator.CFL=1e6 | idfx write idefix_patched.ini
```





# Contribution guidelines

We use the [pre-commit](https://pre-commit.com) framework to automatically lint for code
style and common pitfals.

Before you commit to your local copy of the repo, please run this from the top level
```shell
$ python3 -m pip install -u -e .[dev]
$ pre-commit install
```

# Testing

We use the [pytest](https://docs.pytest.org/en/latest/) framework to test `idfx`'s
internal components. The test suite can be run from the top level with a simple `pytest`
invocation.
```shell
$ pytest
```
