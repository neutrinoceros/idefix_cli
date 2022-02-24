[![PyPI](https://img.shields.io/pypi/v/idefix_cli)](https://pypi.org/project/idefix-cli/)
![PyPI](https://img.shields.io/pypi/pyversions/idefix_cli/0.10.0?logo=python&logoColor=white&label=Python)
[![codecov](https://codecov.io/gh/neutrinoceros/idefix_cli/branch/main/graph/badge.svg)](https://codecov.io/gh/neutrinoceros/idefix_cli)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/neutrinoceros/idefix_cli/main.svg)](https://results.pre-commit.ci/badge/github/neutrinoceros/idefix_cli/main.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# `idefix_cli`

This is a CLI helper tool for the hexascale portable MHD code
[Idefix](https://gricad-gitlab.univ-grenoble-alpes.fr/lesurg/idefix-public),
written by Geoffroy Lesur et al.

It provides a family of commands to help with repetitive tasks such as
configuration and cleanup in a single tool.

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
set at runtime.

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

`idfx conf` is a unified wrapper for `cmake` and the historical Python script
`$IDEFIX_DIR/configure.py`. All arguments and flags are passed down to the
relevant configuration system.

Arguments that were originally implemented in
`$IDEFIX_DIR/configure.py` (`-mhd`, `-mpi`, `-openmp`, `-cxx`, `-arch`, `-gpu`)
are converted on the fly for cmake.

For instance
```shell
$ idfx conf -gpu -mpi -openmp -arch Ampere86 -cxx g++
```
is equivalent to
```
$ cmake $IDEFIX_DIR \
  -DKokkos_ENABLE_CUDA=ON \
  -DIdefix_MPI=ON \
  -DKokkos_ENABLE_OPENMP=ON \
  -DKokkos_ARCH_AMPERE86=ON \
  -DCMAKE_CXX_COMPILER=g++
```


### Persistent, sytem wide configuration file

Some configuration options like prefered compiler and target architecture rarely
need to be changed on a single maching. `idfx conf` follows the last version of
`$IDEFIX_DIR/configure.py` and looks for persistent options stored in
`$HOME/.config/idefix.cfg`.

For instance, one can select a persistent build target (say Ampere86) and custom compiler as
```ini
# idefix.cfg

[compilation]
GPU = Ampere86
compiler = g++
```

A prefered conf system can also be stored as
```ini
# idefix.cfg

[idefix_cli]
conf_system = python  # use configure.py
# or
conf_system = cmake
```
though this is mostly useful for testing purposes. In general `idfx conf`
automatically determines which configuration system to use based on
resources available. Cmake is prefered over Python when both are available.

Any option passed on the command line will override its equivalent persistent
configuration.

Lastly, it is possible invoke `ccmake` instead of `cmake` by passing the
`-i/--interactive` flag to `idfx conf`.


## `idfx run`

This command is intended as a simple assistant to continuously check soundness
of your setup as your developing it, and run tests problems sequentially for
very short periods of time.

`idfx run` essenitally invokes the `idefix` binary, but will also (re)compiles
it if necessary. If source files were edited since last compilation, a prompt
will offer to recompile.

Note that this command will fail if neither `idefix` or `Makefile` are found in the
specified directory. Use `idfx conf` to generate the `Makefile`.

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

Removes intermediate compilation files (`*.o`, `*.host`, `*.cuda`) as well as
CMake cache files and directories

```shell
$ idfx clean .
```
This command will print a list of purgable files, and will not remove anything
without confirmation.

To also remove `Makefile`, `idefix` executables, use the `--all` flag
```shell
$ idfx clean . --all
```

Use the `--dry-run/--dry` flag to skip the prompt and only display the list of
purgeable items, without actually deleting anything.


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

This command is roughly equivalent to
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
