[![PyPI](https://img.shields.io/pypi/v/idefix_cli)](https://pypi.org/project/idefix-cli/)
![PyPI](https://img.shields.io/badge/requires-Python%20≥%203.8-blue?logo=python&logoColor=white)
[![Documentation Status](https://readthedocs.org/projects/idefix-cli/badge/?version=latest)](https://idefix-cli.readthedocs.io/en/latest/?badge=latest)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/neutrinoceros/idefix_cli/main.svg)](https://results.pre-commit.ci/badge/github/neutrinoceros/idefix_cli/main.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)

# `idefix_cli`

`idefix_cli` is command line framework to facilitate working with
[Idefix](https://gricad-gitlab.univ-grenoble-alpes.fr/lesurg/idefix-public),
written by Geoffroy Lesur et al.

It defines a `idfx` command namespace, ships with a collection of common helper
script (`idfx conf`, `idfx run`, ...), and can be extended to include arbitrary
helper scripts.


## Installation

`idefix_cli` is distributed via the Python Packaging Index (PyPI).

It is recommended to install this tool in isolation with [`pipx`](https://pipxproject.github.io/pipx/) as
```shell
$ pipx install "idefix_cli[isolated]"
```
(adding `[isolated]` has the effect of pinning dependencies)

Otherwise, the most portable way to install the latest stable version is
```shell
$ python -m pip install --user idefix_cli
```

Note that most `idfx` commands explicitly require that the env variable `$IDEFIX_DIR` be
set at runtime.

## Get help

Get a complete description of available commands with
```shell
$ idfx --help
```
Likewise, get help for each command therein as, for instance
```shell
$ idfx run --help
```

For more, read [the documentation !](https://idefix-cli.readthedocs.io/en/latest/?badge=latest)
