

# Builtin Commands


## `idfx conf`

`idfx conf` is a unified wrapper for `(c)cmake` and the historical Python script
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

Switching from `cmake` to `ccmake` is done by passing the `-i/--interactive` flag
```shell
$ idfx conf -i
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
# use CMake
engine = cmake
# or configure.py (Idefix < 1.0)
engine = python
```
though this is mostly useful for testing purposes. In general `idfx conf`
automatically determines which configuration system to use based on
available resources. CMake is prefered over Python when both are available.

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
Use the `--tstop` and `--time-step` arguments to override `TimeIntegrator.tstop`
and `TimeIntegrator.fixed_dt` parameters from the inifile.

```shell
$ idfx run --tstop 1e-4
```

Note that `--time-step` maps to Idefix's inifile `TimeIntegrator.first_dt`.

### running idefix step-by-step

`idefix` (since version 1.0) supports running step-by-step via the `-maxcycles` argument.

`idfx run` augments this mode by providing an `--out` option, which
can be used to specify arbitrary output types to be produced *on each cycle*.

Use `--one-step/--one` to run a single cycle (total simulation time equates to the first
cycle). The length of the cycle can be adjusted in combination with `--time-step`,
however, `--one-step` is incompatible with `--tstop`.

```shell
$ idfx run --one
```
is a shortcut for
```shell
$ idfx run -maxcycles 1
```
where `x`, is the existing value found in the inifile. `--one` can optionally be followed by output types, which will be interpreted as the `--out` parameter. For instance
```shell
$ idfx run --one dmp vtk
```
is equivalent to
```shell
$ idfx run -maxcycles 1 --out dmp vtk
```
and will run the curdir setup for one time step and output both a dmp file and a vtk file (not including outputs 0 for initial conditions).

All of these options can also be combined with `-restart`.


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

*new in idefix_cli 2.2.0*

`--nproc` can be left unspecified if domain decomposition is explicitly set with
idefix's `-dec` argument.

### Configuration
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

## `idfx clean`

Removes intermediate compilation files (`*.o`, `*.host`, `*.cuda`) as well as
CMake cache files and directories

```shell
$ idfx clean
```
This command will print a list of purgable files from the current working directory, and will not remove anything
without confirmation (unless confirmation is explicitly skipped with `--no-confirm`).

To also remove `Makefile`, `idefix` executables, use the `--all` flag
```shell
$ idfx clean --all
```

Use the `--dry-run/--dry` flag to skip the prompt and only display the list of
purgeable items, without actually deleting anything.

`idfx clean` also accepts a `--dir <path>` argument.

## `idfx clone`

Clone an idefix problem directory by copying the main source files
(`definitions.hpp`, `setup.cpp`, `idefix.ini`).

```shell
$ idfx clone $IDEFIX_DIR/test/HD/KHI/ /tmp/myKHI
```

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

## `idfx digest`
*new in idefix_cli 2.4*

Reduce idefix performance logs to a `json` report, outputted to stdout by default, or to
a file specified by `-o/--output`, e.g., the following styles are equivalent

```shell
$ idfx digest > report.json
$ idfx digest -o report.json
```
No data reduction is performed other than type casting. This choice allows the resulting
report to be plugged in arbitrary plotting scripts.

By default, files matching the expression `idefix.*.log` are listed, and only the first
one is parsed. Adding the `--all` flag enables parsing *all* files matching this expression.
Alternatively, one or more file(s) with arbitrary name(s) may be specified via `--input` (*new in idefix_cli 3.2*).

Pass the `--timeit` flag to output execution time to stderr.

Here's an example Python script to process the report into a plot of simulation
performance VS time, for each MPI process

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

series = pd.read_json("report.json", typ="series")

stacked = np.empty((len(series.iloc[0]["time"]), len(series)), dtype="float")

fig, ax = plt.subplots()
ax.set(
    xlabel="time",
    ylabel="perf (cell updates/s)",
    yscale="log",
)
for i, s in enumerate(series):
    stacked[:, i] = s["cell (updates/s)"]
    ax.plot("time", "cell (updates/s)", data=s, lw=0.3, alpha=0.7, color="C0")

ax.plot(series.iloc[0]["time"], stacked.mean(axis=1), color="C0", lw=2)
ax.axhline(np.nanmean(stacked), ls="--", color="black")

sfile = "perfs.png"
print(f"saving to {sfile}")
fig.savefig(sfile)
```


## `idfx switch`

Switch to another existing git branch in `$IDEFIX_DIR`.
No cleaning is performed, this command simply wraps the following script
```shell
$ pushd $IDEFIX_DIR && git checkout mybranch ; popd
```
into
```
$ idfx switch mybranch
```

Bonus: if no branch is specified, switch to the most recently visited other branch.


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
