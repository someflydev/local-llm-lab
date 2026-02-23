#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/release_prep.sh --check [--allow-dirty]
  ./scripts/release_prep.sh --help

Checks (non-destructive):
  - required files exist
  - version consistency (pyproject.toml vs src/lab/__init__.py)
  - git working tree clean (strict mode unless --allow-dirty)
  - ruff check
  - unittest suite

Exit codes:
  0  all requested checks passed
  1  one or more checks failed
  2  usage / invalid arguments
EOF
}

MODE=""
ALLOW_DIRTY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --check)
      MODE="check"
      shift
      ;;
    --allow-dirty)
      ALLOW_DIRTY=1
      shift
      ;;
    *)
      echo "[release-prep] Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "${MODE}" != "check" ]]; then
  usage >&2
  exit 2
fi

failures=0

pass() { echo "[release-prep] PASS: $*"; }
warn() { echo "[release-prep] WARN: $*"; }
fail() { echo "[release-prep] FAIL: $*"; failures=$((failures + 1)); }

required_files=(
  "LICENSE"
  "README.md"
  "CHANGELOG.md"
  "RELEASE_CHECKLIST.md"
  "pyproject.toml"
  "src/lab/__init__.py"
)

for path in "${required_files[@]}"; do
  if [[ -f "$path" ]]; then
    pass "required file exists: $path"
  else
    fail "missing required file: $path"
  fi
done

pyproject_version="$(python3 - <<'PY'
from pathlib import Path
for line in Path("pyproject.toml").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line.startswith("version = "):
        print(line.split("=", 1)[1].strip().strip('"'))
        break
PY
)"
package_version="$(python3 - <<'PY'
from pathlib import Path
for line in Path("src/lab/__init__.py").read_text(encoding="utf-8").splitlines():
    if line.strip().startswith("__version__"):
        print(line.split("=", 1)[1].strip().strip('"'))
        break
PY
)"

if [[ -n "${pyproject_version}" && "${pyproject_version}" == "${package_version}" ]]; then
  pass "version consistency (${pyproject_version})"
else
  fail "version mismatch (pyproject=${pyproject_version:-missing}, package=${package_version:-missing})"
fi

if git diff --quiet && git diff --cached --quiet; then
  pass "git working tree clean"
else
  if [[ ${ALLOW_DIRTY} -eq 1 ]]; then
    warn "git working tree is dirty (allowed by --allow-dirty)"
  else
    fail "git working tree is dirty (rerun with --allow-dirty only for prompt-time verification)"
  fi
fi

if uv run --python 3.12 --with ruff ruff check .; then
  pass "ruff check"
else
  fail "ruff check failed"
fi

if uv run --python 3.12 python -m unittest discover -s tests; then
  pass "unittest suite"
else
  fail "unittest suite failed"
fi

if [[ ${failures} -eq 0 ]]; then
  echo "[release-prep] Summary: all checks passed"
  exit 0
fi

echo "[release-prep] Summary: ${failures} check(s) failed"
exit 1
