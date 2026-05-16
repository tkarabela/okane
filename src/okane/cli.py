import argparse
import sys
from io import BytesIO, StringIO
from enum import Enum

from okane.models import BankToCustomerStatement

try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore[assignment]


class OutputFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"


def main(argv: list[str]) -> int:
    from okane import __version__

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_files", nargs="+", metavar="statement.xml",
                        help="path to input camt.053 XML file(s)")
    parser.add_argument("--version", "-V", action="version", version=__version__)
    parser.add_argument("--output", "-o", metavar="FILE", default="-", help="path to output file "
                        "(default: write to stdout)")
    parser.add_argument("--format", "-f", choices=[fmt.value for fmt in OutputFormat],
                        type=OutputFormat, default=OutputFormat.JSON, help="set output format (default: json)")
    parser.add_argument("--no-indent", action="store_true", help="do not indent JSON output files")

    args = parser.parse_args(argv)
    input_files = args.input_files
    output_path = args.output
    output_format = args.format
    no_indent = args.no_indent

    statements = [BankToCustomerStatement.from_file(path) for path in input_files]

    output_bytes = b""

    match output_format:
        case OutputFormat.JSON:
            for statement in statements:
                output_bytes += statement.model_dump_json(indent=None if no_indent else 4).encode("utf-8")
                output_bytes += b"\n"
        case OutputFormat.CSV:
            dfs = []
            for statement in statements:
                df = statement.as_dataframe()
                dfs.append(df)
            assert pd is not None
            all_df = pd.concat(dfs)
            buf = StringIO()
            all_df.to_csv(buf, index=False)
            output_bytes = buf.getvalue().encode("utf-8")
        case OutputFormat.XLSX:
            dfs = []
            for statement in statements:
                df = statement.as_dataframe()
                dfs.append(df)
            assert pd is not None
            all_df = pd.concat(dfs)
            buf_bin = BytesIO()
            all_df.to_excel(buf_bin, index=False)
            output_bytes = buf_bin.getvalue()
        case _:
            raise NotImplementedError(f"Unsupported output format {output_format}")

    if output_path == "-":
        sys.stdout.buffer.write(output_bytes)
    else:
        with open(output_path, "wb") as fp:
            fp.write(output_bytes)

    return 0
