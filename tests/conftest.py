"""Local, isolated Git repositories for deterministic integration tests."""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest


@dataclass
class GitRepo:
    path: Path

    def git(self, *args: str, input: bytes | None = None) -> str:
        result = subprocess.run(
            ["git", "--literal-pathspecs", "-C", str(self.path), *args],
            input=input, capture_output=True, check=True, timeout=30,
        )
        return result.stdout.decode("utf-8").strip()

    def write(self, name: str, content: str | bytes) -> None:
        target = self.path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)

    def commit(self) -> str:
        self.git("add", "-A")
        self.git("commit", "--allow-empty", "-qm", "fixture")
        return self.git("rev-parse", "HEAD")


@pytest.fixture
def git_repo(tmp_path, monkeypatch):
    # Test Git must not load user hooks, signing settings, aliases or repository routing.
    for name in tuple(os.environ):
        if name.startswith("GIT_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    repo = GitRepo(tmp_path / "repo")
    repo.path.mkdir()
    repo.git("init", "-q")
    repo.git("config", "user.name", "TC1 fixture")
    repo.git("config", "user.email", "tc1-fixture@example.invalid")
    repo.git("config", "commit.gpgsign", "false")
    repo.git("config", "core.autocrlf", "false")
    return repo
