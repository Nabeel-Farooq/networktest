#!/usr/bin/env python3
# encoding: utf-8


# Inspired by netspeed.sh script from:
# https://bitbucket.org/rsvp/gists/src

import argparse
import os
import signal
import statistics
import sys
import time
from pathlib import Path

import requests

import common
import csv_parser
import downloadtester

try:
    from importlib.metadata import version as get_version
except ImportError:
    from importlib_metadata import version as get_version


tester = downloadtester.DownloadTester()

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
        default=tester.DEFAULT_DOWNLOAD_COUNT,
        help=(
            "Number of downloads to do. "
            f"Default: {tester.DEFAULT_DOWNLOAD_COUNT}"
        ),
    )

    parser.add_argument(
        "-l",
        "--location",
        choices=tester.LOCATIONS.keys(),
        default=tester.DEFAULT_LOCATION,
        help=(
            "Server location for the test. "
            f"Default: {tester.DEFAULT_LOCATION}"
        ),
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
        help="Disable verbose output",
    )

    parser.add_argument(
        "-u",
        "--url",
        help=(
            "Alternate download URL "
            "(must include path and filename)"
        ),
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

    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def get_verbose_printer(enabled):
    """Return conditional print function."""

    return print if enabled else lambda *a, **k: None


def validate_url(url):
    """Validate download URL."""

    try:
        response = requests.head(
            url,
            timeout=10,
            allow_redirects=True,
        )

        return response.ok

    except requests.RequestException:
        return False


def format_speed(speed):
    """Format speed into MB/s and Mbps."""

    return (
        f"{round(speed * common.SPEED_MB_SEC, 2)}MB/s - "
        f"{round(speed * common.SPEED_MBIT_SEC, 2)}Mbps"
    )


def main():
    """Run main program."""

    options = parse_option()

    tester.VERBOSE = not options.silent

    verboseprint = get_verbose_printer(
        tester.VERBOSE
    )

    verboseprint(
        f"{Path(__file__).name} v{VERSION}\n"
    )

    if options.url:

        if not validate_url(options.url):
            print(
                "ERROR: Download URL does not exist."
            )
            return 1

        url = options.url

    else:
        location = options.location

        verboseprint(f"Location: {location}")

        url = tester.get_location(location)

    verboseprint(f"URL: {url}")

    if options.outfile:

        output_dir = os.path.dirname(
            options.outfile
        )

        if output_dir and not os.path.exists(
            output_dir
        ):
            print(
                "\nERROR: Output file destination "
                f"directory does not exist: "
                f"{output_dir}\n"
            )

            return 1

    verboseprint(
        f"Total Tests: {options.count}\n"
    )

    print()

    results = []
    filesize = 0

    for test_num in range(
        1,
        options.count + 1,
    ):

        verboseprint(f"Test #{test_num}:")

        result = tester.download_file(url)

        filesize = round(
            tester.get_filesize() / 1024 / 1024,
            2,
        )

        results.append(result)

        verboseprint(
            f"\nDownloaded file size: "
            f"{filesize} MB"
        )

        verboseprint(
            f"\nAverage download speed: "
            f"{format_speed(result)}\n"
        )

    if not results:
        print("No download results available.")
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
        f"Overall Average Download Speed: "
        f"{format_speed(overall_speed)}"
    )

    verboseprint(
        f"Maximum download speed: "
        f"{format_speed(max_speed)}"
    )

    verboseprint(
        f"Minimum download speed: "
        f"{format_speed(min_speed)}"
    )

    verboseprint(
        f"Median download speed: "
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
            "URL",
            "Size (MB)",
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

        overall_values = [
            time.strftime("%c"),
            url,
            filesize,
            round(
                min_speed * common.SPEED_MB_SEC,
                2,
            ),
            round(
                min_speed * common.SPEED_MBIT_SEC,
                2,
            ),
            round(
                max_speed * common.SPEED_MB_SEC,
                2,
            ),
            round(
                max_speed * common.SPEED_MBIT_SEC,
                2,
            ),
            round(
                overall_speed
                * common.SPEED_MB_SEC,
                2,
            ),
            round(
                overall_speed
                * common.SPEED_MBIT_SEC,
                2,
            ),
            round(
                median_speed
                * common.SPEED_MB_SEC,
                2,
            ),
            round(
                median_speed
                * common.SPEED_MBIT_SEC,
                2,
            ),
            round(
                deviation
                * common.SPEED_MB_SEC,
                2,
            ),
            round(
                deviation
                * common.SPEED_MBIT_SEC,
                2,
            ),
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
            filesize,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
