"""agregate performance data from log files as json"""

import json
import re
import sys
from argparse import ArgumentParser
from pathlib import Path
from time import monotonic_ns

from idefix_cli.lib import print_err

_LOG_LINE_REGEXP = re.compile(r"^(?P<trailer>TimeIntegrator:)(?P<data>.*\|.*)")


def _parse_token(raw_data: str):
    sdata = raw_data.strip()
    if sdata == "N/A":
        return float("nan")
    try:
        return int(sdata)
    except ValueError:
        pass
    try:
        return float(sdata)
    except ValueError:
        pass
    return sdata


def _log_to_json(log: list[str]):
    tokenized_log = [[_parse_token(t) for t in line.split("|")] for line in log]
    columns: dict[str, list] = {name: [] for name in tokenized_log[0]}
    for i, name in enumerate(columns.keys()):
        columns[name] = [L[i] for L in tokenized_log[1:]]
    return columns


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
    parser.add_argument(
        "--timeit",
        action="store_true",
        help="print time used to perform the operation to stderr",
    )


def command(
    dir: str,
    output=sys.stdout,
    timeit: bool = False,
    *,
    _log_line_regexp=_LOG_LINE_REGEXP,
) -> int:
    pdir = Path(dir)
    if not pdir.is_dir():
        print_err(f"No such directory: {dir!r}")
        return 1

    tstart = monotonic_ns()
    log_files = sorted(pdir.glob(r"idefix*log"))

    if not log_files:
        print_err(f"No log files found in {dir!r}")
        return 1

    data: list[list[str]] = []
    _success = False
    for log in log_files:
        captured: list[str] = []
        for line in log.read_text().splitlines():
            if (match := _log_line_regexp.fullmatch(line)) is not None:
                captured.append(match.group("data"))
                _success = True
        data.append(captured)

    if not _success:
        print_err("Failed to parse any data")
        return 1

    header = data[0][0]  # first line captured from the first log file

    if len(data) > 1:
        for p, c in zip(log_files[1:], data[1:]):
            if c[0] != header:  # pragma: no cover
                print_err(f"header mismatch from {p} and {log_files[0]}")

    final_result = {}
    for p, d in zip(log_files, data):
        final_result.update({str(p.relative_to(dir)): _log_to_json(d)})

    _json = json.dumps(final_result, indent=2)
    if isinstance(output, str):
        with open(output, "w") as fh:
            print(_json, file=fh)
    else:
        print(_json, file=output)

    if timeit:
        tstop = monotonic_ns()
        print(f"took {(tstop-tstart)/1e6:.3f} ms", file=sys.stderr)
    return 0
