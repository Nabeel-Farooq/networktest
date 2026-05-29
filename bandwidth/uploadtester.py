#!/usr/bin/env python3
# encoding: utf-8

"""
.. codeauthor:: Juan Luis Baptiste <juan.baptiste@gmail.com>
"""

import errno
import ftplib
import os
import sys
import time
from pathlib import Path
from socket import error as SocketError

import common


class UploadTester:
    """Class to perform upload speed tests."""

    DEFAULT_UPLOAD_COUNT = 1
    VERBOSE = True

    def __init__(self):
        self.host = ""
        self.username = ""
        self.password = ""
        self.passive = False
        self.current_dir = "/"
        self.overall_time_elapsed = 0

        self._size_written = 0
        self._filesize = 0
        self._filename = ""
        self._start = 0.0

        self._ftp = ftplib.FTP()

    def cleanup(self):
        """Cleanup after test ends or it is cancelled."""

        try:
            if self._filename:
                self._ftp.delete(self._filename)

            self._ftp.quit()

        except (
            ftplib.error_temp,
            ftplib.error_perm,
            ftplib.error_reply,
            OSError,
        ):
            pass

        finally:
            try:
                self._ftp.close()
            except Exception:
                pass

    def connect(self):
        """Connect and authenticate to FTP server."""

        self._ftp.connect(self.host, 21)

        try:
            self._ftp.login(self.username, self.password)

        except ftplib.error_perm as exc:
            error_message = str(exc)

            if "530" in error_message:
                print("ERROR: Bad username or password.\n")
                sys.exit(1)

            raise

        self._ftp.set_pasv(self.passive)
        self._ftp.cwd(self.current_dir)

    def upload_file(self, upload_file):
        """
        Upload file to FTP server and return upload speed.

        Arguments:
        upload_file -- File path to upload
        """

        chunk_size = 8192
        self._size_written = 0

        upload_path = Path(upload_file)

        self._filename = upload_path.name
        self._filesize = upload_path.stat().st_size

        self.connect()

        self._start = time.time()

        try:
            with upload_path.open("rb") as file:
                self._ftp.storbinary(
                    f"STOR {self._filename}",
                    file,
                    blocksize=chunk_size,
                    callback=self.print_progress,
                )

        except SocketError as exc:
            if exc.errno != errno.ECONNRESET:
                raise

            print("ERROR: Connection reset, retrying upload...")
            return 0

        finally:
            self.overall_time_elapsed = round(
                time.time() - self._start,
                2,
            )

        if self.overall_time_elapsed <= 0:
            return 0

        upload_speed = (
            self._filesize / self.overall_time_elapsed
        )

        return upload_speed

    def print_progress(self, chunk):
        """
        Print upload progress.

        Arguments:
        chunk -- Uploaded data chunk
        """

        self._size_written += len(chunk)

        if self._filesize <= 0:
            return

        done = int(
            50 * self._size_written / self._filesize
        )

        time_elapsed = time.time() - self._start

        if time_elapsed <= 0:
            return

        upload_speed = self._size_written / time_elapsed

        avg_speed_mb = upload_speed / 1_000_000
        avg_speed_mbps = (
            upload_speed * common.SPEED_MBIT_SEC
        )

        if self.VERBOSE:
            sys.stdout.write(
                "\r[%s%s] %s MB/s - %s Mbps"
                % (
                    "=" * done,
                    " " * (50 - done),
                    round(avg_speed_mb, 2),
                    round(avg_speed_mbps, 2),
                )
            )

            sys.stdout.flush()
