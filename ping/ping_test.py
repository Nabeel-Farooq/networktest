#!/usr/bin/env python3
# encoding: utf-8

"""
.. codeauthor:: Juan Luis Baptiste <juan.baptiste@gmail.com>
"""

from __future__ import print_function

import argparse
import os
import signal
import sys
import time
from statistics import mean

import pingparsing
import ping_parsers

try:
    from importlib.metadata import version as get_version
except ImportError:
    from importlib_metadata import version as get_version


DEFAULT_PING_COUNT = 5
VERBOSE = True

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
        default=DEFAULT_PING_COUNT,
        help=f"Ping count. Default: {DEFAULT_PING_COUNT}",
    )

    parser.add_argument(
        "-f",
        "--pingfile",
        required=True,
        help="List of hosts to ping",
    )

    parser.add_argument(
        "-o",
        "--outfile",
        help="Destination file for ping results",
    )

    parser.add_argument(
        "-I",
        dest="interface",
        help="Network interface to use for pinging",
    )

    parser.add_argument(
        "-s",
        "--silent",
        action="store_true",
        help="Don't print verbose output from the test",
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


def get_avg(results, metric):
    """Calculate average value for a metric."""
    values = [
        getattr(result[1], metric, None)
        for result in results
    ]

    valid_values = [v for v in values if v is not None]

    if not valid_values:
        return 0

    return round(mean(valid_values), 2)


def get_std_deviation(results):
    """Calculate average RTT deviation."""
    values = [
        result[1].rtt_mdev
        for result in results
        if result[1].rtt_mdev is not None
    ]

    if not values:
        return 0

    return round(mean(values), 2)


def verbose_print(enabled):
    """Return conditional print function."""
    return print if enabled else lambda *a, **k: None


def load_hosts(filepath):
    """Load valid hosts from file."""
    with open(filepath, "r", encoding="utf-8") as file:
        return [
            line.strip()
            for line in file
            if line.strip() and not line.startswith("#")
        ]


def main():
    """Run main program."""
    global VERBOSE

    options = parse_option()

    if options.silent:
        VERBOSE = False

    vprint = verbose_print(VERBOSE)

    transmitter = pingparsing.PingTransmitter()
    transmitter.interface = options.interface
    transmitter.count = options.count

    script_dir = os.getcwd()
    hosts_path = os.path.join(script_dir, options.pingfile)

    hosts = load_hosts(hosts_path)
    ping_results = []

    vprint(
        f"\nNetwork Interface: "
        f"{transmitter.interface or 'Default'}"
    )

    vprint(f"Ping Count: {transmitter.count}")
    vprint(f"Hosts: {len(hosts)}\n")

    start = time.time()

    for index, host in enumerate(hosts, start=1):
        vprint(f"Test #{index}:")
        vprint(f"Pinging Host {host}")

        transmitter.destination_host = host

        try:
            result = transmitter.ping()

            ping_parser = pingparsing.PingParsing()
            ping_parser.parse(result)

            ping_results.append((host, ping_parser))

            vprint(
                f"  Min: {ping_parser.rtt_min} ms\n"
                f"  Max: {ping_parser.rtt_max} ms\n"
                f"  Average: {ping_parser.rtt_avg} ms\n"
                f"  Packet Loss Count: "
                f"{ping_parser.packet_loss_count}\n"
                f"  Packet Loss Rate: "
                f"{ping_parser.packet_loss_rate}%\n"
            )

        except AttributeError:
            vprint(f"Non-existent Host: {host}\n")

        except Exception as exc:
            vprint(f"Error pinging {host}: {exc}\n")

    time_elapsed = round(time.time() - start, 2)

    vprint(f"\nTime elapsed: {time_elapsed} seconds")

    avg_min = get_avg(ping_results, "rtt_min")
    avg_max = get_avg(ping_results, "rtt_max")
    avg_ping = get_avg(ping_results, "rtt_avg")
    avg_plc = get_avg(ping_results, "packet_loss_count")
    avg_plr = get_avg(ping_results, "packet_loss_rate")
    std_deviation = get_std_deviation(ping_results)

    overall = (
        time.strftime("%c"),
        options.count,
        time_elapsed,
        avg_min,
        avg_max,
        avg_ping,
        avg_plc,
        avg_plr,
        std_deviation,
        f"v{VERSION}",
    )

    vprint(f"\nAverage min: {avg_min} ms")
    vprint(f"Average max: {avg_max} ms")
    vprint(f"Average ping: {avg_ping} ms")
    vprint(f"Average packet loss count: {avg_plc}")
    vprint(f"Average packet loss rate: {avg_plr} %")
    vprint(f"Standard deviation: {std_deviation} ms\n")

    if options.outfile:
        csv_file = os.path.join(script_dir, options.outfile)

        ping_parsers.csv_ping_parser(
            ping_results,
            csv_file,
            overall,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
