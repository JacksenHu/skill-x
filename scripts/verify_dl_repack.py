#!/usr/bin/env python3
"""Offline check for api/server.py fetch_repack across upstream layouts."""
import importlib.util
import io
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("sx", ROOT / "api" / "server.py")
sx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sx)


class FakeResp:
    def __init__(self, body):
        self.body = body

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def make_tar(root, entries):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for rel, text in entries.items():
            data = text.encode()
            ti = tarfile.TarInfo(f"{root}/{rel}")
            ti.size = len(data)
            tf.addfile(ti, io.BytesIO(data))
    return buf.getvalue()


def run(root, entries, suite, skill):
    payload = make_tar(root, entries)
    sx.urllib.request.urlopen = lambda req, timeout=60: FakeResp(payload)
    blob = sx.fetch_repack(suite, skill)
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tf:
        return sorted(m.name for m in tf.getmembers())


def case(name, root, entries, suite, skill, expect):
    got = run(root, entries, suite, skill)
    missing = [e for e in expect if e not in got]
    extra = [g for g in got if g not in expect]
    ok = not missing and not extra
    print(("[PASS] " if ok else "[FAIL] ") + name, got)
    if not ok:
        print("  missing:", missing, "extra:", extra)
    return ok


def main():
    ok = True
    ok &= case(
        "skills/<name>/ layout",
        "repo-main",
        {"skills/foo/SKILL.md": "# foo", "skills/foo/scripts/a.sh": "echo"},
        {"namespace": "o/r", "skills": ["foo"]},
        "foo",
        ["foo/SKILL.md", "foo/scripts/a.sh"],
    )
    ok &= case(
        "repo-root SKILL.md layout",
        "repo-main",
        {"SKILL.md": "# root"},
        {"namespace": "o/r", "skills": ["browser-search"],
         "paths": {"browser-search": "SKILL.md"}},
        "browser-search",
        ["browser-search/SKILL.md"],
    )
    ok &= case(
        ".github/skills hidden layout",
        "repo-main",
        {".github/skills/auth/biometric-auth/SKILL.md": "# bio"},
        {"namespace": "o/r", "skills": ["biometric-auth"],
         "paths": {"biometric-auth": ".github/skills/auth/biometric-auth/SKILL.md"}},
        "biometric-auth",
        ["biometric-auth/SKILL.md"],
    )
    ok &= case(
        "test/fixtures layout",
        "repo-main",
        {"test/fixtures/safe-docstring-zip/SKILL.md": "# fixture"},
        {"namespace": "o/r", "skills": ["docstring-zip"],
         "paths": {"docstring-zip": "test/fixtures/safe-docstring-zip/SKILL.md"}},
        "docstring-zip",
        ["docstring-zip/SKILL.md"],
    )
    ok &= case(
        "no paths map, legacy fallback",
        "repo-main",
        {"skills/bar/SKILL.md": "# bar"},
        {"namespace": "o/r", "skills": ["bar"]},
        "bar",
        ["bar/SKILL.md"],
    )
    try:
        run("repo-main", {"other/x.md": "x"}, {"namespace": "o/r", "skills": ["nope"]}, "nope")
        print("[FAIL] missing skill should raise FileNotFoundError")
        ok = False
    except FileNotFoundError:
        print("[PASS] missing skill raises FileNotFoundError")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
