#!/usr/bin/env python3
# encoding: utf-8

import os
import sys
import time
from pathlib import Path
from tempfile import gettempdir

import requests

import common


class DownloadTester:
    """Class to perform download speed tests."""

    DEFAULT_LOCATION = "use"
    DEFAULT_DOWNLOAD_COUNT = 1
    VERBOSE = True

    LOCATIONS = {
        "london": (
            "http://speedtest.london.linode.com/"
            "100MB-london.bin"
        ),
        "sanjose": (
            "http://speedtest.sjc01.softlayer.com/"
            "speedtest/speedtest/random500x500.jpg"
        ),
        "tokyo": (
            "http://speedtest.tokyo.linode.com/"
            "100MB-tokyo.bin"
        ),
        "use": (
            "http://speedtest.newark.linode.com/"
            "100MB-newark.bin"
        ),
        "usw": (
            "http://speedtest.fremont.linode.com/"
            "100MB-fremont.bin"
        ),
        "washington": (
            "http://speedtest.wdc01.softlayer.com/"
            "downloads/test500.zip"
        ),
    }

    def __init__(self):
        self.local_filename = "100MB-newark.bin"
        self.overall_time_elapsed = 0
        self._size = 0

    def get_filesize(self):
        """Return downloaded file size."""

        return self._size

    def get_location(self, location=None):
        """
        Return test file download URL.

        Arguments:
        location -- Location key
        """

        return self.LOCATIONS.get(
            location or self.DEFAULT_LOCATION
        )

    @staticmethod
    def get_local_filename(url):
        """Extract local filename from URL."""

        return url.rsplit("/", 1)[-1]

    def download_file(self, url):
        """
        Download file and return speed.

        Arguments:
        url -- File URL
        """

        self.local_filename = (
            self.get_local_filename(url)
        )

        temp_path = (
            Path(gettempdir()) / self.local_filename
        )

        self._size = 0
        download_speed = 0

        start = time.time()

        try:
            with requests.get(
                url,
                stream=True,
                timeout=30,
            ) as response:

                response.raise_for_status()

                total_length = int(
                    response.headers.get(
                        "content-length",
                        0,
                    )
                )

                with temp_path.open("wb") as file:

                    for chunk in response.iter_content(
                        chunk_size=8192
                    ):

                        if not chunk:
                            continue

                        chunk_len = len(chunk)

                        self._size += chunk_len

                        file.write(chunk)

                        time_elapsed = (
                            time.time() - start
                        )

                        if time_elapsed > 0:
                            download_speed = (
                                self._size / time_elapsed
                            )

                            self.overall_time_elapsed = round(
                                time_elapsed,
                                2,
                            )

                        if (
                            self.VERBOSE
                            and total_length > 0
                        ):
                            done = int(
                                50
                                * self._size
                                / total_length
                            )

                            sys.stdout.write(
                                "\r[%s%s] %s MB/s - %s Mbps"
                                % (
                                    "=" * done,
                                    " " * (50 - done),
                                    round(
                                        download_speed
                                        * common.SPEED_MB_SEC,
                                        2,
                                    ),
                                    round(
                                        download_speed
                                        * common.SPEED_MBIT_SEC,
                                        2,
                                    ),
                                )
                            )

                            sys.stdout.flush()

        finally:
            self.cleanup(temp_path)

        return download_speed

    @staticmethod
    def cleanup(filepath):
        """
        Delete downloaded temporary file.

        Arguments:
        filepath -- File path to remove
        """

        try:
            if filepath.exists():
                filepath.unlink()

        except OSError:
            pass
