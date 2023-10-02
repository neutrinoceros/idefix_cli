# How to define additional commands

`idefix_cli` can be extended to include arbitrary, user-defined commands, to be written as
individual Python modules, later refered to as *plugins*.


## Configuration

To enable plugins, select a directory that will contain their definitions
through the configuration file, e.g.

```ini
# idefix.cfg
[idefix_cli]
plugins_directory = path/to/my/plugins/
```


## A basic plugin example

Here's simple example illustrating all the requirements for a plugin file.
Say that we want to define a `idfx hello` command
```python
# hello.py
"Say hello n times"

from idefix_cli.lib import print_error


def add_arguments(parser) -> None:
    # Define arbitrary arguments
    # parser is a argparse.ArgumentParser object
    # https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser
    #
    # this function is required, its signature is mandatory, but the body can be left empty
    parser.add_argument(
        "nrepeat",
        type=int,
        help="number of times to say 'hello'. Must be (>=1)",
    )


def command(nrepeat:int) -> int:
    # Define the actual script
    #
    # this function is required and its return type must be int
    # (return 0 is all goes well, otherwise return 1)
    # the arguments must match those defined in add_arguments
    if nrepeat <= 0:
        # illustrate how to deal with exceptions
        print_error(f"Cannot greet less than 1 time !")
        return 1

    print(nrepeat * "Hello " + "!")
    return 0
```

Note that the name of the file (here `hello.py`) defines the name of the command (`idfx hello`).
The module-level docstring is also required and serves as the description of the command when `idfx --help` is invoked.

## Public API

The `idefix_cli.lib` module contains some common utility functions that can be imported

### print_error
::: idefix_cli.lib.print_error

### print_warning
::: idefix_cli.lib.print_warning

### print_success
::: idefix_cli.lib.print_success

### print_subcommand
::: idefix_cli.lib.print_subcommand

### run_subcommand
::: idefix_cli.lib.run_subcommand

### chdir

This function is backported [from the standard library](https://docs.python.org/3/library/contextlib.html?highlight=chdir#contextlib.chdir), and is provided for portability.

If you are running Python 3.11 or newer, you may import this directly from the standard library,

```python
# with Python 3.11
from contextlib import chdir
# with any Python
from idefix_cli.lib import chdir
```

### files_from_pattenrs
::: idefix_cli.lib.files_from_patterns

### make_file_tree
::: idefix_cli.lib.make_file_tree

### requires_idefix (decorator)
::: idefix_cli.lib.requires_idefix

### get_idefix_version
::: idefix_cli.lib.get_idefix_version

### get_config_file
::: idefix_cli.lib.get_config_file

### get_configuration
::: idefix_cli.lib.get_configuration

### get_option
::: idefix_cli.lib.get_option

### prompt_ask
::: idefix_cli.lib.prompt_ask
