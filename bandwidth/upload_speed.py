#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import signal
import statistics
import sys
import time
from pathlib import Path
from typing import Callable

import common
import csv_parser
import uploadtester

try:
    from importlib.metadata import version as get_version
except ImportError:
    from importlib_metadata import version as get_version


try:
    VERSION = get_version("network-tests")
except Exception:
    VERSION = "dev"


# ----------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------


def get_verbose_printer(enabled: bool) -> Callable:
    """Return print function or no-op."""

    return print if enabled else lambda *args, **kwargs: None


def format_speed(speed: float) -> str:
    """
    Format speed value.

    Args:
        speed: Bytes per second.

    Returns:
        Formatted string.
    """

    mb_s = speed * common.SPEED_MB_SEC
    mbps = speed * common.SPEED_MBIT_SEC

    return f"{mb_s:.2f} MB/s - {mbps:.2f} Mbps"


def get_file_size_mb(file_path: Path) -> float:
    """Return file size in MB."""

    return round(
        file_path.stat().st_size / (1024 * 1024),
        2,
    )


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    default_count = uploadtester.UploadTester.DEFAULT_UPLOAD_COUNT

    parser = argparse.ArgumentParser(
        description="FTP Upload Speed Tester"
    )

    parser.add_argument(
        "-c",
        "--count",
        type=int,
        default=default_count,
        help=f"Number of upload tests (default: {default_count})",
    )

    parser.add_argument(
        "-f",
        "--uploadfile",
        required=True,
        metavar="FILE",
        help="File to upload",
    )

    parser.add_argument(
        "-o",
        "--outfile",
        metavar="CSV",
        help="Export results to CSV file",
    )

    parser.add_argument(
        "-s",
        "--silent",
        action="store_true",
        help="Disable verbose output",
    )

    parser.add_argument(
        "-l",
        "--host",
        required=True,
        help="FTP server hostname",
    )

    parser.add_argument(
        "-u",
        "--username",
        required=True,
        help="FTP username",
    )

    parser.add_argument(
        "-p",
        "--password",
        required=True,
        help="FTP password",
    )

    parser.add_argument(
        "-P",
        "--passive",
        choices=("yes", "no"),
        default="no",
        help="Enable FTP passive mode",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    return parser.parse_args()


# ----------------------------------------------------------------------
# Statistics
# ----------------------------------------------------------------------


def build_statistics(results: list[float]) -> dict[str, float]:
    """Calculate test statistics."""

    return {
        "average": statistics.mean(results),
        "median": statistics.median(results),
        "minimum": min(results),
        "maximum": max(results),
        "deviation": (
            statistics.stdev(results)
            if len(results) > 1
            else 0.0
        ),
    }


# ----------------------------------------------------------------------
# CSV Export
# ----------------------------------------------------------------------


def export_csv(
    results: list[float],
    outfile: str,
    host: str,
    uploadfile: str,
    filesize_mb: float,
    stats: dict[str, float],
) -> None:
    """Export test results."""

    csv_path = str(Path.cwd() / outfile)

    headers = [
        "Date",
        "Server",
        "File",
        "Size",
        "Min (MB/s)",
        "Min (Mbps)",
        "Max (MB/s)",
        "Max (Mbps)",
        "Average (MB/s)",
        "Average (Mbps)",
        "Median (MB/s)",
        "Median (Mbps)",
        "Deviation (MB/s)",
        "Deviation (Mbps)",
        "Program Version",
    ]

    values = [
        time.strftime("%c"),
        host,
        uploadfile,
        filesize_mb,
        round(stats["minimum"] * common.SPEED_MB_SEC, 2),
        round(stats["minimum"] * common.SPEED_MBIT_SEC, 2),
        round(stats["maximum"] * common.SPEED_MB_SEC, 2),
        round(stats["maximum"] * common.SPEED_MBIT_SEC, 2),
        round(stats["average"] * common.SPEED_MB_SEC, 2),
        round(stats["average"] * common.SPEED_MBIT_SEC, 2),
        round(stats["median"] * common.SPEED_MB_SEC, 2),
        round(stats["median"] * common.SPEED_MBIT_SEC, 2),
        round(stats["deviation"] * common.SPEED_MB_SEC, 2),
        round(stats["deviation"] * common.SPEED_MBIT_SEC, 2),
        f"v{VERSION}",
    ]

    csv_parser.csv_parser(
        results,
        csv_path,
        (headers, values),
        filesize_mb,
    )


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> int:
    """Program entry point."""

    options = parse_args()

    upload_path = Path(options.uploadfile)

    if not upload_path.exists():
        print(f"ERROR: File not found: {upload_path}")
        return 1

    if not upload_path.is_file():
        print(f"ERROR: Not a valid file: {upload_path}")
        return 1

    tester = uploadtester.UploadTester()

    tester.host = options.host
    tester.username = options.username
    tester.password = options.password
    tester.passive = options.passive == "yes"
    tester.VERBOSE = not options.silent

    verbose = get_verbose_printer(tester.VERBOSE)

    def signal_handler(sig, frame):
        """Handle Ctrl+C gracefully."""

        print("\n\nTest cancelled.\n")
        tester.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    filesize_mb = get_file_size_mb(upload_path)

    verbose(f"{Path(__file__).name} v{VERSION}\n")
    verbose(f"FTP Host: {options.host}")
    verbose(f"Username: {options.username}")
    verbose("Password: ********")
    verbose(f"File: {upload_path}")
    verbose(f"Size: {filesize_mb} MB")
    verbose(f"\nTotal Tests: {options.count}\n")

    results: list[float] = []

    try:
        for test_number in range(
            1,
            options.count + 1,
        ):
            verbose(f"Test #{test_number}")

            speed = tester.upload_file(upload_path)

            if speed > 0:
                results.append(speed)

            print()

            verbose(
                f"\nAverage upload speed: "
                f"{format_speed(speed)}\n"
            )

        if not results:
            print("No successful uploads recorded.")
            return 1

        stats = build_statistics(results)

        verbose("\nTest Results")
        verbose("------------\n")

        verbose(
            f"Time Elapsed: "
            f"{tester.overall_time_elapsed:.2f} seconds\n"
        )

        verbose(
            f"Average Speed: "
            f"{format_speed(stats['average'])}"
        )

        verbose(
            f"Maximum Speed: "
            f"{format_speed(stats['maximum'])}"
        )

        verbose(
            f"Minimum Speed: "
            f"{format_speed(stats['minimum'])}"
        )

        verbose(
            f"Median Speed: "
            f"{format_speed(stats['median'])}"
        )

        verbose(
            f"Standard Deviation: "
            f"{format_speed(stats['deviation'])}\n"
        )

        if options.outfile:
            export_csv(
                results=results,
                outfile=options.outfile,
                host=options.host,
                uploadfile=str(upload_path),
                filesize_mb=filesize_mb,
                stats=stats,
            )

    finally:
        tester.cleanup()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
