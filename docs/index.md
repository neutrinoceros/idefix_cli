# idefix_cli

`idefix_cli` is command line framework to facilitate working with
[Idefix](https://github.com/idefix-code/idefix), written by
[Lesur et al](https://ui.adsabs.harvard.edu/abs/2023arXiv230413746L/abstract).

It defines a `idfx` command namespace, ships with a collection of common helper
script (`idfx conf`, `idfx run`, ...), and can be extended to include arbitrary
helper scripts.


## Installation

`idefix_cli` is distributed via the Python Packaging Index (PyPI).

It is recommended to install this tool in isolation with [`uv`](https://docs.astral.sh/uv/) as
```shell
$ uv tool install idefix-cli
```

Otherwise, the most portable way to install the latest stable version is
```shell
$ python -m pip install --user idefix-cli
```

Note that most `idfx` commands explicitly require that the env variable `$IDEFIX_DIR` be
set at runtime.

## Get help

The following contains usage examples. Get a complete description of available options with
```shell
$ idfx --help
```
Likewise, get help for each command therein as, for instance
```shell
$ idfx run --help
```

## Configuration

`idfx_cli` supports persistent configuration. It follows the last version of
`$IDEFIX_DIR/configure.py` and looks for options stored in
`$HOME/.config/idefix.cfg`.

Command specific options are stored in corresponding sections
, e.g., `idfx conf` looks into the `[idfx conf]` section.

More detail is given about each option in [Builtin Commands](commands.md).
