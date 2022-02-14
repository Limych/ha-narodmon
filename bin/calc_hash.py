#!/usr/bin/env python3
#  Copyright (c) 2022, Andrey "Limych" Khrolenok <andrey@khrolenok.ru>
#  Creative Commons BY-NC-SA 4.0 International Public License
#  (see LICENSE.md or https://creativecommons.org/licenses/by-nc-sa/4.0/)
"""The module checksum calculator."""
import argparse
import glob
import hashlib
import logging
import os
import sys

import yaml

# http://docs.python.org/2/howto/logging.html#library-config
# Avoids spurious error messages if no logger is configured by the user
logging.getLogger(__name__).addHandler(logging.NullHandler())

logging.basicConfig(level=logging.CRITICAL)

_LOGGER = logging.getLogger(__name__)

VERSION = "1.0.0"

ROOT = os.path.dirname(os.path.abspath(f"{__file__}/.."))


def dir_hash(path: str) -> str:
    """Calculate cumulative hash of all Python files in directory."""
    dhash = hashlib.md5()

    for file in glob.iglob(f"{path}/**.py", recursive=True):
        with open(file, "rb") as fp:
            _LOGGER.debug("Hashing file %s", file)
            dhash.update(fp.read())

    _LOGGER.debug("Cumulative hash of all files: %s", dhash.hexdigest())
    return dhash.hexdigest()


def main():
    """Execute script."""
    parser = argparse.ArgumentParser(
        description=f"The module checksum calculator. Version {VERSION}"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debugging output.",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        "--dryrun",
        action="store_true",
        help="Preview release notes generation without running it.",
    )
    args = parser.parse_args()

    if args.verbose:
        _LOGGER.setLevel(logging.DEBUG)

    if args.dry_run:
        _LOGGER.debug("Dry run mode ENABLED")
        print("!!! Dry Run !!!")

    secrets_file = f"{ROOT}/secrets.yaml"
    with open(secrets_file, encoding="utf8") as fp:
        key = (yaml.safe_load(fp) or {}).get("api_key")

    if key is None:
        print(f"Key is not defined. Please add key field to {secrets_file}")
        sys.exit(1)

    pkg_dir = f"{ROOT}/custom_components/narodmon"
    dhash = "".join(chr(ord(a) ^ ord(b)) for a, b in zip(dir_hash(pkg_dir), key))
    _LOGGER.debug("Encode key: %s => %s", repr(key), repr(dhash))

    data_file = f"{pkg_dir}/checksum.bin"
    if args.dry_run:
        print(f"Hash would be stored to {data_file}")
    else:
        _LOGGER.debug("Storing hash to %s", data_file)
        with open(data_file, "wb") as fp:
            fp.write(dhash.encode("utf8"))


if __name__ == "__main__":
    main()
