"""agregate performance data from log files as json"""

import re
import sys
from argparse import ArgumentParser
from pathlib import Path
from time import monotonic_ns
from typing import Any

from idefix_cli.lib import print_error

_LOG_LINE_REGEXP = re.compile(r"^(?P<trailer>TimeIntegrator:)(?P<data>.*\|.*)")


def _log_to_data(log: list[str]):
    columns: dict[str, list[Any]] = {name.strip(): [] for name in log[0].split("|")}
    tokenized_log = [line.replace("N/A", "NaN").split("|") for line in log[1:]]
    for i, name in enumerate(columns.keys()):
        columns[name] = [L[i] for L in tokenized_log]

    # the very last line in a log may be polluted by a trailing warning or error
    # in practice this is only known to happen on the last column.
    # Let's sanitize this value:

    # rely on Python leaking variables binded by for loops
    data = columns[name]
    last_entry = data[-1]
    if "NaN" in last_entry:
        data[-1] = "NaN"
    else:
        data[-1] = re.sub(r"\D+$", "", last_entry)

    return columns


def _data_to_json(header: str, data: dict[str, list[str]]) -> str:
    res: list[str] = [f'"{header}": {{']
    ncolumns = len(data)
    for icol, (name, record) in enumerate(data.items()):
        if icol < ncolumns - 1:
            trail = ","
        else:
            trail = ""
        res.append(f'"{name}":[{",".join([_.strip() for _ in record])}]{trail}')

    res.append("}")
    return "\n".join(res)


def add_arguments(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--dir",
        nargs="?",
        default=".",
        help="target directory where log files are to be found",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        default=sys.stdout,
        help="output file (stdout by default)",
    )
    select_group = parser.add_mutually_exclusive_group()
    select_group.add_argument(
        "-i",
        "--input",
        dest="input_",
        nargs="*",
        help="target log file",
    )
    select_group.add_argument(
        "--all",
        dest="all_files",
        action="store_true",
        help="parse all log files (by default, only the first one is read)",
    )
    parser.add_argument(
        "--timeit",
        action="store_true",
        help="print time used to perform the operation to stderr",
    )


def command(
    dir: str,
    input_: list[str] | None = None,
    output=sys.stdout,
    all_files: bool = False,
    timeit: bool = False,
    *,
    _log_line_regexp=_LOG_LINE_REGEXP,
) -> int:
    pdir = Path(dir)
    if not pdir.is_dir():
        print_error(f"No such directory: {dir!r}")
        return 1

    tstart = monotonic_ns()
    if input_ is None:
        log_files = sorted(
            pdir.glob(r"idefix*log"),
            key=lambda p: int(re.search(r"\d+", p.name).group()),  # type: ignore [union-attr]
        )
    else:
        log_files = [pdir / _ for _ in input_]

    if not log_files:
        print_error(f"No log files found in {dir!r}")
        return 1

    if input_ is None and not all_files:
        log_files = [log_files[0]]

    data: list[list[str]] = []
    _success = False

    for log in log_files.copy():
        captured: list[str] = []
        for line in log.read_text().splitlines():
            if (match := _log_line_regexp.fullmatch(line)) is not None:
                captured.append(match.group("data"))
                _success = True
        if not captured:
            # dynamically exclude files without any data
            log_files.remove(log)
            continue

        data.append(captured)

    if not _success:
        print_error("Failed to parse any data")
        return 1

    header = data[0][0]  # first line captured from the first log file

    if len(data) > 1:
        for p, c in zip(log_files[1:], data[1:], strict=True):
            if c[0] != header:  # pragma: no cover
                print_error(f"header mismatch from {p} and {log_files[0]}")
                return 1

    final_result: list[str] = []
    for p, d in zip(log_files, data, strict=True):
        columns = _log_to_data(d)
        final_result.append(_data_to_json(p.name, columns))

    _json = "{\n" + ",\n".join(final_result) + "\n}"
    if isinstance(output, str):
        with open(output, "w") as fh:
            print(_json, file=fh)
    else:
        print(_json, file=output)

    if timeit:
        tstop = monotonic_ns()
        print(f"took {(tstop-tstart)/1e6:.3f} ms", file=sys.stderr)
    return 0
