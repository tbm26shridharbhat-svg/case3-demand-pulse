"""The audit lock is the most important test: it asserts that every quoted number
in the submission still matches what the canonical script computes from raw data.

This is what gives AUDIT.md its teeth — any code change that drifts a number breaks
the CI build."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_audit_matches_locked_truth():
    result = subprocess.run(
        ["python", "scripts/canonical_audit.py", "--verify"],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    assert result.returncode == 0, (
        f"\n=== audit verification failed ===\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
    assert "AUDIT OK" in result.stdout
