#!/usr/bin/env python3
"""Calculate a reproducible SHA-256 identifier for a committed PR diff."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys


def git(*arguments: str) -> bytes:
    try:
        return subprocess.run(
            ["git", *arguments], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).stdout
    except FileNotFoundError:
        raise SystemExit("git is required but was not found") from None
    except subprocess.CalledProcessError as error:
        message = error.stderr.decode("utf-8", errors="replace").strip()
        raise SystemExit(message or "git command failed") from None


def resolve_commit(reference: str) -> str:
    return git("rev-parse", "--verify", f"{reference}^{{commit}}").decode("ascii").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Hash the committed diff between a PR base and head.")
    parser.add_argument("--base", required=True, help="PR base ref or commit")
    parser.add_argument("--head", default="HEAD", help="PR head ref or commit")
    arguments = parser.parse_args()

    base_commit = resolve_commit(arguments.base)
    head_commit = resolve_commit(arguments.head)
    diff = git("diff", "--binary", "--no-ext-diff", f"{base_commit}...{head_commit}")

    print("Algorithm: SHA-256")
    print(f"Input: git diff --binary --no-ext-diff {arguments.base}...{arguments.head}")
    print(f"Base-commit: {base_commit}")
    print(f"Head-commit: {head_commit}")
    print(f"Digest: {hashlib.sha256(diff).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
