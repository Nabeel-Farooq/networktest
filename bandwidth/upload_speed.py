#!/usr/bin/env python3
# encoding: utf-8

import argparse
import os
import signal
import statistics
import sys
import time
from pathlib import Path

import common
import csv_parser
import uploadtester

try:
    from importlib.metadata import version as get_version
except ImportError:
    from importlib_metadata import version as get_version


tester = uploadtester.UploadTester()

try:
    VERSION = get_version("network-tests")
except Exception:
    VERSION = "dev"


def parse_option():
    """Parse command line arguments."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-c",
        "--count",
        type=int,
        default=tester.DEFAULT_UPLOAD_COUNT,
        help=(
            "Number of uploads to do. "
            f"Default: {tester.DEFAULT_UPLOAD_COUNT}"
        ),
    )

    parser.add_argument(
        "-f",
        "--uploadfile",
        required=True,
        help="Test file to upload",
    )

    parser.add_argument(
        "-o",
        "--outfile",
        help="Destination CSV file for test results",
    )

    parser.add_argument(
        "-s",
        "--silent",
        action="store_true",
        help="Disable verbose upload output",
    )

    parser.add_argument(
        "-l",
        "--host",
        required=True,
        help="FTP server for upload test",
    )

    parser.add_argument(
        "-u",
        "--username",
        required=True,
        help="FTP username for upload test",
    )

    parser.add_argument(
        "-p",
        "--password",
        required=True,
        help="FTP password for upload test",
    )

    parser.add_argument(
        "-P",
        "--passive",
        choices=["yes", "no"],
        default="no",
        help=f"Enable FTP passive mode. Default: {tester.passive}",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"Program Version: {VERSION}",
    )

    return parser.parse_args()


def signal_handler(sig, frame):
    """Handle Ctrl+C."""

    print("\n\nTest cancelled!\n")

    tester.cleanup()

    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def get_verbose_printer(enabled):
    """Return conditional print function."""

    return print if enabled else lambda *a, **k: None


def format_speed(speed):
    """Format speed into MB/s and Mbps."""

    return (
        f"{round(speed * common.SPEED_MB_SEC, 2)}MB/s - "
        f"{round(speed * common.SPEED_MBIT_SEC, 2)}Mbps"
    )


def main():
    """Run main program."""

    options = parse_option()

    tester.host = options.host
    tester.username = options.username
    tester.password = options.password
    tester.passive = options.passive == "yes"

    tester.VERBOSE = not options.silent

    verboseprint = get_verbose_printer(tester.VERBOSE)

    upload_path = Path(options.uploadfile)

    filesize_bytes = upload_path.stat().st_size
    filesize_mb = round(filesize_bytes / 1024 / 1024, 2)

    verboseprint(f"{Path(__file__).name} v{VERSION}\n")
    verboseprint(f"FTP Host: {options.host}")
    verboseprint(f"Username: {tester.username}")
    verboseprint("Password: ************")
    verboseprint(f"File: {options.uploadfile}")
    verboseprint(f"Size: {filesize_mb}MB")
    verboseprint(f"\nTotal Tests: {options.count}\n")

    results = []

    for test_num in range(1, options.count + 1):

        verboseprint(f"Test #{test_num}:")

        result = tester.upload_file(options.uploadfile)

        results.append(result)

        print()

        verboseprint(
            f"\nAverage upload speed: "
            f"{format_speed(result)}\n"
        )

    if not results:
        print("No upload results available.")
        return 1

    overall_speed = statistics.mean(results)
    median_speed = statistics.median(results)

    deviation = (
        statistics.stdev(results)
        if len(results) > 1
        else 0
    )

    min_speed = min(results)
    max_speed = max(results)

    verboseprint("\nTest Results:")
    verboseprint("---- -------\n")

    verboseprint(
        f"Time Elapsed: "
        f"{tester.overall_time_elapsed} seconds\n"
    )

    verboseprint(
        f"Overall Average upload speed: "
        f"{format_speed(overall_speed)}"
    )

    verboseprint(
        f"Maximum upload speed: "
        f"{format_speed(max_speed)}"
    )

    verboseprint(
        f"Minimum upload speed: "
        f"{format_speed(min_speed)}"
    )

    verboseprint(
        f"Median upload speed: "
        f"{format_speed(median_speed)}"
    )

    verboseprint(
        f"Standard Deviation: "
        f"{format_speed(deviation)}\n"
    )

    if options.outfile:

        csv_file = os.path.join(
            os.getcwd(),
            options.outfile,
        )

        overall_headers = [
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
            "Median (MB/sec)",
            "Median (Mbps)",
            "Deviation (MB/sec)",
            "Deviation (Mbps)",
            "Program Version",
        ]

        overall_values = [
            time.strftime("%c"),
            options.host,
            options.uploadfile,
            filesize_mb,
            round(min_speed * common.SPEED_MB_SEC, 2),
            round(min_speed * common.SPEED_MBIT_SEC, 2),
            round(max_speed * common.SPEED_MB_SEC, 2),
            round(max_speed * common.SPEED_MBIT_SEC, 2),
            round(overall_speed * common.SPEED_MB_SEC, 2),
            round(overall_speed * common.SPEED_MBIT_SEC, 2),
            round(median_speed * common.SPEED_MB_SEC, 2),
            round(median_speed * common.SPEED_MBIT_SEC, 2),
            round(deviation * common.SPEED_MB_SEC, 2),
            round(deviation * common.SPEED_MBIT_SEC, 2),
            f"v{VERSION}",
        ]

        overall = (
            overall_headers,
            overall_values,
        )

        csv_parser.csv_parser(
            results,
            csv_file,
            overall,
            filesize_mb,
        )

    tester.cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
