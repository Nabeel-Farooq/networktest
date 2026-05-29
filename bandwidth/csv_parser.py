#!/usr/bin/env python3
# encoding: utf-8

import csv

import common


RESULT_HEADERS = [
    "Sample#",
    "File Size",
    "Average Speed (MB/sec)",
    "Average Throughput (Mbps)",
]


def csv_parser(results, csv_file, overall, filesize):
    """
    Create CSV file from test results.

    Arguments:
    results -- Array with test results
    csv_file -- Destination CSV file
    overall -- Tuple containing overall headers and values
    filesize -- Size of uploaded/downloaded file
    """

    overall_header, overall_values = overall

    with open(
        csv_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(overall_header)
        writer.writerow(overall_values)
        writer.writerow([])

        writer.writerow(RESULT_HEADERS)

        for sample_num, result in enumerate(
            results,
            start=1,
        ):

            writer.writerow([
                sample_num,
                filesize,
                round(
                    result * common.SPEED_MB_SEC,
                    2,
                ),
                round(
                    result * common.SPEED_MBIT_SEC,
                    2,
                ),
            ])
