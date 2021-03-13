import argparse
import os
import re
from pathlib import Path

from idefix_cli._commons import _make, pushd, requires_idefix

cpuarch = frozenset(("HSW", "BDW", "SKX", "EPYC"))

gpuarch = frozenset(
    (
        "Kepler30",
        "Maxwell50",
        "Pascal60",
        "Pascal61",
        "Volta70",
        "Volta72",
        "Turing75",
    )
)
known_archs = {"CPU": cpuarch, "GPU": gpuarch}
default_cpu_arch = "BDW"
default_gpu_arch = "Pascal60"
SETUP_DEFAULTS = {"arch": [default_cpu_arch, default_gpu_arch]}


def _add_setup_args(parser):
    parser.add_argument("directory", help="target directory")

    parser.add_argument("-mhd", action="store_true", help="enable MHD")
    parser.add_argument(
        "-gpu", dest="use_gpu", action="store_true", help="enable KOKKOS+CUDA"
    )

    parser.add_argument("-cxx", help="override default compiler")

    parser.add_argument(
        "-arch",
        nargs="+",
        default=SETUP_DEFAULTS["arch"],
        choices=cpuarch.union(gpuarch),
        help="Target Kokkos architecture",
    )
    parser.add_argument(
        "-openmp", help="enable OpenMP parallelism", action="store_true"
    )
    parser.add_argument("-mpi", help="enable MPI parallelism", action="store_true")
    parser.add_argument(
        "--make",
        "--compile",
        action="store_true",
        help="also compile idefix executable",
    )


@requires_idefix
def setup(
    directory: str,
    arch: str = SETUP_DEFAULTS["arch"],
    use_gpu: bool = False,
    cxx: str = None,
    openmp: bool = False,
    mpi: bool = False,
    mhd: bool = False,
    make: bool = False,
):
    """This is the $IDEFIX_DIR/configure.py script in a reusable form"""

    makefileOptions = {
        "extraIncludeDir": "",
        "extraVpath": "",
        "extraHeaders": "",
        "extraObj": "",
        "extraLine": "",
        "cxxflags": "",
        "ldflags": "",
    }

    # extract cpu & gpu architectures from arch
    selected_archs = {"CPU": default_cpu_arch, "GPU": default_gpu_arch}

    for core_type, archs in known_archs.items():
        vals = list(archs.intersection(set(arch)))
        if not vals:
            continue
        if len(vals) > 1:
            print("Error: received more than one {} arch: {} ".format(core_type, vals))
            return 1
        selected_archs[core_type] = vals[0]

    # todo: remove those confusing aliases and rename `use_gpu` into `gpu`
    cpu = selected_archs["CPU"]
    gpu = selected_archs["GPU"]

    if use_gpu:
        makefileOptions.update(
            {
                "extraLine": '\nKOKKOS_CUDA_OPTIONS = "enable_lambda"',
                "cxx": "${KOKKOS_PATH}/bin/nvcc_wrapper",
                "kokkosDevices": '"Cuda"',
                "kokkosArch": cpu + "," + gpu,
                "cxxflags": "-O3 ",
            }
        )

        # Enforce backend compiler for nvcc
        add = "\nexport NVCC_WRAPPER_DEFAULT_COMPILER = "
        if cxx:
            makefileOptions["extraLine"] += add + cxx
        elif mpi:
            makefileOptions["extraLine"] += add + "mpicxx"
    else:
        if cxx:
            makefileOptions["cxx"] = cxx
        else:
            if mpi:
                makefileOptions["cxx"] = "mpicxx"
            else:
                makefileOptions["cxx"] = "g++"

        makefileOptions["kokkosArch"] = cpu
        makefileOptions["cxxflags"] = "-O3"
        if openmp:
            makefileOptions["kokkosDevices"] = '"OpenMP"'
        else:
            makefileOptions["kokkosDevices"] = '"Serial"'

    if mpi:
        makefileOptions["extraIncludeDir"] += " -I$(SRC)/dataBlock/mpi"
        makefileOptions["extraVpath"] += ":$(SRC)/dataBlock/mpi"
        makefileOptions["extraHeaders"] += " mpi.hpp"
        makefileOptions["extraObj"] += " mpi.o"
        makefileOptions["cxxflags"] += " -DWITH_MPI"

    if mhd:
        makefileOptions["extraIncludeDir"] += " -I$(SRC)/hydro/MHDsolvers"
        makefileOptions["extraVpath"] += ":$(SRC)/hydro/MHDsolvers"
        makefileOptions["extraHeaders"] += " solversMHD.hpp"
        makefileOptions["cxxflags"] += " -DMHD=YES"
    else:
        makefileOptions["extraIncludeDir"] += " -I$(SRC)/hydro/HDsolvers"
        makefileOptions["extraVpath"] += ":$(SRC)/hydro/HDsolvers"
        makefileOptions["extraHeaders"] += " solversHD.hpp"
        makefileOptions["cxxflags"] += " -DMHD=NO"

    # Makefile substitution
    data = (Path(os.getenv("IDEFIX_DIR")) / "Makefile.in").read_text()

    for key, val in makefileOptions.items():
        data = re.sub(r"@{0}@".format(key), val, data)

    with pushd(directory):
        Path("Makefile").write_text(data)

    # print information
    def _print_status(name: str, flag: bool):
        prefix = {True: "en", False: "dis"}[flag]
        print("{}: {}abled".format(name, prefix))

    print("-----------------------------------------------------------")
    print("Idefix succesfully configured with the following options:\n")
    _print_status("MHD", mhd)

    print("Compiler: {}".format(makefileOptions["cxx"]))
    _print_status("MPI", mpi)
    if use_gpu:
        print("Execution target: GPU")
        print("Target architecture: " + gpu)
    else:
        print("Execution target: CPU")
        print("Target architecture: " + cpu)
        _print_status("OpenMP", openmp)

    print("Cflags: {}".format(makefileOptions["cxxflags"]))
    print("-----------------------------------------------------------")
    if make:
        _make(directory)
    return 0


def main():
    parser = argparse.ArgumentParser("Setup an Idefix problem.")
    _add_setup_args(parser)
    args = parser.parse_args()

    return setup(
        args.directory,
        args.arch,
        args.use_gpu,
        args.cxx,
        args.openmp,
        args.mpi,
        args.mhd,
        args.make,
    )


if __name__ == "__main__":  # pragma: no coverage
    exit(main())
