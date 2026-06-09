#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FTP Upload Speed Tester

Refactored and optimized version.
"""

from __future__ import annotations

import errno
import ftplib
import sys
import time
from pathlib import Path
from socket import error as SocketError
from typing import Optional

import common


class UploadTester:
    """Perform FTP upload speed tests."""

    DEFAULT_UPLOAD_COUNT: int = 1
    VERBOSE: bool = True

    FTP_PORT: int = 21
    CHUNK_SIZE: int = 8192
    PROGRESS_BAR_WIDTH: int = 50
    CONNECTION_TIMEOUT: int = 30

    def __init__(self) -> None:
        self.host: str = ""
        self.username: str = ""
        self.password: str = ""
        self.passive: bool = False
        self.current_dir: str = "/"

        self.overall_time_elapsed: float = 0.0

        self._size_written: int = 0
        self._filesize: int = 0
        self._filename: str = ""
        self._start_time: float = 0.0

        self._ftp = ftplib.FTP(timeout=self.CONNECTION_TIMEOUT)

    # ------------------------------------------------------------------
    # Connection Management
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Connect and authenticate to the FTP server."""

        self._ftp.connect(self.host, self.FTP_PORT)

        try:
            self._ftp.login(self.username, self.password)
        except ftplib.error_perm as exc:
            if "530" in str(exc):
                raise RuntimeError(
                    "Bad FTP username or password."
                ) from exc
            raise

        self._ftp.set_pasv(self.passive)
        self._ftp.cwd(self.current_dir)

    def cleanup(self) -> None:
        """Clean up FTP session and uploaded test file."""

        try:
            if self._filename:
                try:
                    self._ftp.delete(self._filename)
                except (
                    ftplib.error_perm,
                    ftplib.error_temp,
                    ftplib.error_reply,
                    OSError,
                ):
                    pass

            try:
                self._ftp.quit()
            except (
                ftplib.error_perm,
                ftplib.error_temp,
                ftplib.error_reply,
                OSError,
            ):
                pass

        finally:
            try:
                self._ftp.close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Upload Logic
    # ------------------------------------------------------------------

    def upload_file(self, upload_file: str | Path) -> float:
        """
        Upload a file and return average upload speed in bytes/sec.

        Args:
            upload_file: Path to file.

        Returns:
            Upload speed in bytes per second.
        """

        file_path = Path(upload_file)

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        if not file_path.is_file():
            raise ValueError(f"Not a valid file: {file_path}")

        self._filename = file_path.name
        self._filesize = file_path.stat().st_size
        self._size_written = 0

        if self._filesize <= 0:
            return 0.0

        self.connect()

        self._start_time = time.perf_counter()

        try:
            with file_path.open("rb") as file_handle:
                self._ftp.storbinary(
                    f"STOR {self._filename}",
                    file_handle,
                    blocksize=self.CHUNK_SIZE,
                    callback=self.print_progress,
                )

        except SocketError as exc:
            if exc.errno == errno.ECONNRESET:
                print(
                    "\nERROR: Connection reset by remote host. "
                    "Retrying upload..."
                )
                return 0.0
            raise

        finally:
            self.overall_time_elapsed = round(
                time.perf_counter() - self._start_time,
                2,
            )

        if self.overall_time_elapsed <= 0:
            return 0.0

        if self.VERBOSE:
            print()

        return (
            self._filesize
            / self.overall_time_elapsed
        )

    # ------------------------------------------------------------------
    # Progress Reporting
    # ------------------------------------------------------------------

    def print_progress(self, chunk: bytes) -> None:
        """
        FTP upload callback.

        Args:
            chunk: Uploaded chunk.
        """

        chunk_size = len(chunk)
        self._size_written += chunk_size

        if self._filesize <= 0:
            return

        elapsed = time.perf_counter() - self._start_time

        if elapsed <= 0:
            return

        uploaded = self._size_written

        progress = min(
            uploaded / self._filesize,
            1.0,
        )

        completed = int(
            progress * self.PROGRESS_BAR_WIDTH
        )

        upload_speed = uploaded / elapsed

        speed_mb_s = upload_speed / 1_000_000
        speed_mbps = (
            upload_speed * common.SPEED_MBIT_SEC
        )

        if not self.VERBOSE:
            return

        progress_bar = (
            "=" * completed
            + " "
            * (
                self.PROGRESS_BAR_WIDTH
                - completed
            )
        )

        sys.stdout.write(
            f"\r[{progress_bar}] "
            f"{speed_mb_s:.2f} MB/s - "
            f"{speed_mbps:.2f} Mbps"
        )

        sys.stdout.flush()
