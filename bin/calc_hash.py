#!/usr/bin/env python3
#  Copyright (c) 2022, Andrey "Limych" Khrolenok <andrey@khrolenok.ru>
#  Creative Commons BY-NC-SA 4.0 International Public License
#  (see LICENSE.md or https://creativecommons.org/licenses/by-nc-sa/4.0/)
"""The module checksum calculator."""
import argparse
import logging
import os
import re
import sys
from typing import List

import yaml

# http://docs.python.org/2/howto/logging.html#library-config
# Avoids spurious error messages if no logger is configured by the user
logging.getLogger(__name__).addHandler(logging.NullHandler())

logging.basicConfig(level=logging.CRITICAL)

_LOGGER = logging.getLogger(__name__)

VERSION = "1.0.0"

ROOT = os.path.dirname(os.path.abspath(f"{__file__}/.."))


def data_hash(data: str, hash_len: int) -> List[int]:
    """Calculate hash of given data."""
    i = 0
    khash = [0] * hash_len

    for char in data:
        khash[i] = (khash[i] + ord(char)) % 256
        i = (i + 1) % hash_len

    return khash


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
    fpath = f"{pkg_dir}/const.py"

    with open(fpath, encoding="utf8") as fp:
        src = fp.read()
    metadata = dict(re.findall(r'([a-z_]+) = "([^"]*)"', src, re.IGNORECASE))
    metadata.update(dict(re.findall(r"([a-z_]+) = '([^']*)'", src, re.IGNORECASE)))

    khash = "".join(
        chr(a ^ ord(b))
        for a, b in zip(data_hash(metadata.get("ISSUE_URL"), len(key)), key)
    )
    _LOGGER.debug("Encode key: %s => %s", repr(key), repr(khash))

    khash = re.sub(r"\\\$", "$", re.sub(r"^'|'$", '"', re.escape(repr(khash))))
    res = re.sub(r"KHASH = [^\n]+", f"KHASH = {khash}", src)

    if args.dry_run:
        print(f"Hash would be stored to {fpath}")
    else:
        _LOGGER.debug("Storing hash to %s", fpath)
        with open(fpath, "w", encoding="utf8") as fp:
            fp.write(res)


if __name__ == "__main__":
    main()
