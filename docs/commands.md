

# Builtin Commands


## `idfx conf`

`idfx conf` is a unified wrapper for `cmake` and the historical Python script
`$IDEFIX_DIR/configure.py`. All arguments and flags are passed down to the
relevant configuration system.

Arguments that were originally implemented in
`$IDEFIX_DIR/configure.py` (`-mhd`, `-mpi`, `-openmp`, `-cxx`, `-arch`, `-gpu`)
are converted on the fly for cmake.

For instance
```shell
$ idfx conf -mhd -mpi -gpu -arch Ampere86 -cxx g++
```
is equivalent to
```
$ cmake $IDEFIX_DIR \
  -DIdefix_MHD=ON \
  -DIdefix_MPI=ON \
  -DKokkos_ENABLE_CUDA=ON \
  -DKokkos_ARCH_AMPERE86=ON \
  -DCMAKE_CXX_COMPILER=g++
```

`idfx conf` accepts a `--dir <path>` argument.
```shell
idfx conf --dir my/setup/dir
```
is equivalent to
```shell
pushd my/setup/dir && idfx conf ; popd
```


### Configuration

Some configuration options like prefered compiler and target architecture rarely
need to be changed on a single machine.

For instance, one can select a persistent build target (say Ampere86) and custom compiler as
```ini
# idefix.cfg

[compilation]
GPU = Ampere86
compiler = g++
```

A prefered configuration engine can also be stored as
```ini
# idefix.cfg

[idfx conf]
# use configure.py
engine = python
# or CMake
engine = cmake
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
of your setup as your developing it, and run tests problems locally for
very short periods of time.

`idfx run` essentially invokes the `idefix` binary, but will also (re)compiles
it if necessary. If source files were edited since last compilation, an
interactive prompt will offer to recompile.

Note that this command will fail if neither `idefix` or `Makefile` are found in the
specified directory. Use `idfx conf` to generate the `Makefile`.

Additional, arbitrary arguments may be passed to the `idefix` executable via this
command.

*new in `idefix_cli` 1.1.0*

By default, `idfx run` will call `make` before running `idefix` on every invoke,
which is essentially free when the binary is already up to date, and desired in
almost every other cases. Alternative behaviours can be enabled with the persistent
configuration file.

```ini
# idefix.cfg

[idfx run]
# default
recompile = always

# check if source files were updated since
# the last successful compilation, and if so,
# ask wether to recompile via a prompt. Skip
# compilation completely if the binary appears to be
# up to date.
recompile = prompt
```

The 'prompt' mode was the default up to `idefix_cli` 1.0


### minimal example: run a test sequentially

```shell
$ idfx run --dir $IDEFIX_DIR/test/HD/KHI
```
The default behaviour is to use `idefix.ini` contained in the specified directory. If you
want to run a different one, use `-i/--inifile`
```shell
$ idfx run -i myconf.ini
```

Note that `idfx run` looks for the inifile relative to the cwd, and _then_ relative to
the specified directory.

### running a shorter version of a problem
Use the `--duration` and `--time-step` arguments to run a modified version of a base
inifile.

```shell
$ idfx run --duration 1e-4
```

Note that `--time-step` maps to Idefix's inifile `TimeIntegrator.first_dt`.

Use `--one-step/--one` to run a single time step (total simulation time equates to the
first time step).
The length of the time step can be adjusted in combination with `--time-step`, however,
`--one-step` is incompatible with `--duration`.

```shell
$ idfx run --one
```
is a shortcut for
```shell
$ idfx run --duration x --time-step x
```
where `x`, is the existing value found in the inifile. `idfx run --one` also
optionally accepts arbitrary output format identifiers. For instance
```shell
$ idfx run --one dmp vtk
```
will run the curdir setup for one time step and output both a dmp file and a vtk file.

The `--times <n>` argument can also be supplied in combination with `--one` to
run for an arbitry number of steps. It is close to idefix's `-maxcycles`
argument.

### running in parallel

`idfx run` also wraps around `mpirun -> idefix` via the `--nproc` optional argument.
For instance
```shell
$ idfx run --dir mydir --nproc 2
```
is equivalent to
```
$ pushd mydir ; mpirun -n 2 ./idefix ; popd
```

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

Additional files may be included in the clone using the `--include` argument. They
can be specified either by name or POSIX pattern, e.g.
```shell
$ idfx clone $IDEFIX_DIR/test/HD/KHI/ /tmp/myKHI --include "*.log"
```

Note that extra patterns need be escaped, else they'd be interpreted by the
shell before they make it to `idefix_cli`.

### Configuration

Arbitrary patterns can also be stored in the configuration file. For example
```ini
# idefix.cfg

[idfx clone]
include = *py README.*
```
Note that the `--include` argument can be combined with `idefix.cfg`.

</details>

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
