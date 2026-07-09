"""NGSpice subprocess runner."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class NgSpiceResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def combined(self) -> str:
        return self.stdout + "\n" + self.stderr


def ngspice_version_line() -> str:
    try:
        proc = subprocess.run(
            ["ngspice", "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        text = (proc.stdout + proc.stderr).strip().splitlines()
        return text[0] if text else "ngspice (version unknown)"
    except (OSError, subprocess.TimeoutExpired):
        return "ngspice (not found)"


def run_batch(
    deck_path: Path,
    *,
    cwd: Path | None = None,
    timeout_s: float | None = None,
) -> NgSpiceResult:
    """Run ngspice -b on deck_path (basename only if cwd is set)."""
    work = cwd or deck_path.parent
    deck_name = deck_path.name if cwd else str(deck_path)
    proc = subprocess.run(
        ["ngspice", "-b", deck_name],
        cwd=work,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_s,
    )
    return NgSpiceResult(
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def resolve_model_path() -> Path | None:
    """Return SPICE_MODEL_PATH if set and exists."""
    raw = os.environ.get("SPICE_MODEL_PATH", "").strip()
    if not raw:
        return None
    path = Path(raw).expanduser().resolve()
    return path if path.is_file() else None
