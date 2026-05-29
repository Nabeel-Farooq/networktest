from pathlib import Path

from setuptools import find_packages, setup


BASE_DIR = Path(__file__).parent


setup(
    name="network-tests",
    version="0.1.5",

    packages=find_packages(
        include=[
            "ping",
            "bandwidth",
        ]
    ),

    include_package_data=True,

    package_data={
        "ping": ["hosts.txt"],
    },

    scripts=[
        "download-tester",
        "upload-tester",
        "ping-tester",
    ],

    install_requires=[
        "requests>=2.0.0",
        "pingparsing>=1.4.0",
    ],

    python_requires=">=3.8",

    author="Juan Luis Baptiste",
    author_email="juan.baptiste@gmail.com",

    description=(
        "Collection of scripts to perform network tests "
        "such as download/upload speed and ping latency, "
        "with CSV result export support."
    ),

    long_description=(
        (BASE_DIR / "README.md").read_text(
            encoding="utf-8"
        )
        if (BASE_DIR / "README.md").exists()
        else ""
    ),

    long_description_content_type="text/markdown",

    license="GPLv3",

    keywords=[
        "network",
        "ping",
        "bandwidth",
        "download",
        "upload",
        "speedtest",
        "latency",
        "testing",
    ],

    url="https://github.com/juanluisbaptiste/network-tests",

    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet",
        "Topic :: System :: Networking",
        "Topic :: Utilities",
    ],

    project_urls={
        "Source": (
            "https://github.com/"
            "juanluisbaptiste/network-tests"
        ),
    },

    zip_safe=False,
)
