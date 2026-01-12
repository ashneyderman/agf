#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "shortuuid",
#   "sqids",
#   "GitPython"
# ]
# ///

import asyncio
import os
import random
import secrets
import sqlite3

import shortuuid
from git import Repo
from sqids import Sqids

conn = sqlite3.connect(
    "/Users/alex/gh_ashneyderman/tac/agentic_flow/.agf/logs/agf-021.db"
)


def main():
    print("Hello from agentic-flow!")
    git_tests()
    generate_random_strings()
    init_sql()


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


async def bounded_task(sem, coro):
    async with sem:
        return await coro


async def job(name):
    sleep_time = random.uniform(1, 3)
    print(f"{name} started will finish in {sleep_time:.0f}")
    await asyncio.sleep(sleep_time)

    cursor = conn.cursor()
    data = [
        {
            "worktree_id": "agf-021",
            "task_id": "zfsdcg",
            "commit_sha": "5caa163",
            "agent": "claude-code",
            "model": "sonnet",
            "message": """{
                "message": "rename method `run_prompt` in `AgentRunner` to `run_command`. Make sure all call references are updated and all tests are still passing. {chore}"
            }""",
        }
    ]
    cursor.executemany(
        """
        INSERT INTO Logs(worktree_id, task_id, commit_sha, agent, model, message)
        VALUES (:worktree_id, :task_id, :commit_sha, :agent, :model, :message)
        """,
        data,
    )
    conn.commit()

    print(f"{name} finished")


async def run_pooled():
    sem = asyncio.Semaphore(4)

    async with asyncio.TaskGroup() as tg:
        for i in range(10):
            tg.create_task(bounded_task(sem, job(f"Task-{i}")))


def init_sql():
    cursor = conn.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS Logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worktree_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        commit_sha TEXT,
        agent TEXT,
        model TEXT,
        message JSON NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(create_table_query)
    conn.commit()


def query_logs():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Logs")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()


if __name__ == "__main__":
    main()
    asyncio.run(run_pooled())
    query_logs()
