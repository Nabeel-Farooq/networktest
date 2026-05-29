#!/usr/bin/env python3
# encoding: utf-8

from __future__ import print_function

import csv
from statistics import mean


OVERALL_HEADERS = [
    "Date",
    "Count",
    "Time Elapsed (s)",
    "Min (ms)",
    "Max (ms)",
    "Average (ms)",
    "Packet Loss Count",
    "Packet Loss Rate (%)",
    "Standard Deviation (ms)",
    "Program Version",
]

RESULT_HEADERS = [
    "Count",
    "Min (ms)",
    "Max (ms)",
    "Average (ms)",
    "Std Deviation (ms)",
    "Lost",
    "% Lost",
    "Host",
]


def csv_ping_parser(results, csv_file, overall_values):
    """
    Create CSV file from test results.

    Arguments:
    results -- Array with the test results
    csv_file -- Destination CSV file
    overall_values -- Array with overall test data
    """

    with open(csv_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(OVERALL_HEADERS)
        writer.writerow(overall_values)
        writer.writerow([])

        writer.writerow(RESULT_HEADERS)

        for host, parser in results:
            writer.writerow([
                parser.packet_transmit,
                parser.rtt_min,
                parser.rtt_max,
                parser.rtt_avg,
                parser.rtt_mdev,
                parser.packet_loss_count,
                parser.packet_loss_rate,
                host,
            ])


def print_ping_parser(ping_parser):
    """
    Print results for testing.

    Arguments:
    ping_parser -- PingParser instance
    """

    print(f"packet_transmit: {ping_parser.packet_transmit:d} packets")
    print(f"packet_receive: {ping_parser.packet_receive:d} packets")

    print(
        f"packet_loss_rate: "
        f"{ping_parser.packet_loss_rate:.1f} %"
    )

    print(
        f"packet_loss_count: "
        f"{ping_parser.packet_loss_count:d} packets"
    )

    duplicate_rate = (
        f"{ping_parser.packet_duplicate_rate:.1f} %"
        if ping_parser.packet_duplicate_rate is not None
        else "NaN"
    )

    duplicate_count = (
        f"{ping_parser.packet_duplicate_count:d} packets"
        if ping_parser.packet_duplicate_count is not None
        else "NaN"
    )

    print(f"packet_duplicate_rate: {duplicate_rate}")
    print(f"packet_duplicate_count: {duplicate_count}")

    print(f"rtt_min: {ping_parser.rtt_min}")
    print(f"rtt_avg: {ping_parser.rtt_avg}")
    print(f"rtt_max: {ping_parser.rtt_max}")
    print(f"rtt_mdev: {ping_parser.rtt_mdev}")
    print()


def calculate_overall_values(results):
    """
    Calculate overall speeds.

    Arguments:
    results -- Array with the test results
    """

    if not results:
        return 0, 0

    avg_speed = round(
        mean(result[0] for result in results),
        2,
    )

    avg_speed_mbps = round(
        mean(result[1] for result in results),
        2,
    )

    return avg_speed, avg_speed_mbps
