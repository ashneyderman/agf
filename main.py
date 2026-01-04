#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "shortuuid",
#   "sqids",
#   "GitPython"
# ]
# ///

import os
import secrets
import string

import shortuuid
from git import Repo
from sqids import Sqids


def main():
    print("Hello from agentic-flow!")
    git_tests()
    generate_random_strings()


def generate_short_id(length):
    """Generate a cryptographically secure random string of a given length."""
    alphabet = "ABCDEFGHJKLMNPQRSTUWXYZ"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_random_strings():
    print(f"Hello UUID: {shortuuid.uuid()[:6]}")
    print(f"Hello Sqids: {Sqids().encode([123, 456])}")
    print(f"Hello Secure Random: {generate_short_id(8).lower()}")


def git_tests():
    repo = Repo.init(os.path.dirname(__file__))

    print(repo.git.execute(["git", "worktree", "list"]))

    # git worktree add --no-checkout .worktrees/<worktree_dir> -b <branch>
    # print(
    #     repo.git.execute(
    #         ["git", "worktree", "add", "--no-checkout", ".worktrees/test", "test"]
    #     )
    # )

    # repo1 = Repo.init(os.path.join(os.path.dirname(__file__), ".worktrees/test"))

    # repo1.git.checkout()

    # print(os.listdir(os.path.join(os.path.dirname(__file__), ".worktrees/test")))

    # print(repo.git.execute(["git", "worktree", "list"]))
    pass


if __name__ == "__main__":
    main()
