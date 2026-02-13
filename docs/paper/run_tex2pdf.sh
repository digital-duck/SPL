#!/usr/bin/env bash
# run_tex2pdf.sh — Compile spl-paper.tex to PDF using xelatex
# Usage:
#   ./run_tex2pdf.sh          # compile
#   ./run_tex2pdf.sh --clean  # compile then remove aux files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PAPER="spl-paper"
TEX="${PAPER}.tex"
PDF="${PAPER}.pdf"
CLEAN=false
MAX_PASSES=5

# Parse args
for arg in "$@"; do
  case "$arg" in
    --clean) CLEAN=true ;;
    --help)
      echo "Usage: $0 [--clean]"
      echo "  --clean   Remove auxiliary files after successful compilation"
      exit 0
      ;;
    *) echo "Unknown option: $arg" >&2; exit 1 ;;
  esac
done

# Check required tools
for cmd in xelatex bibtex; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: '$cmd' not found. Install TeX Live: sudo apt install texlive-full texlive-xetex"
    exit 1
  fi
done

if [[ ! -f "$TEX" ]]; then
  echo "ERROR: $TEX not found in $SCRIPT_DIR"
  exit 1
fi

# Run one xelatex pass; suppress stdout, surface errors from log
run_xelatex() {
  local pass=$1
  echo "==> xelatex pass ${pass}"
  set +e
  xelatex -interaction=nonstopmode "$PAPER" > /dev/null 2>&1
  local rc=$?
  set -e
  # Fatal errors start with '!' in the log
  if grep -q "^!" "${PAPER}.log" 2>/dev/null; then
    echo "ERROR: xelatex failed on pass ${pass}:"
    grep "^!" "${PAPER}.log" | head -10
    exit 1
  fi
  # Show the output summary line (pages, size)
  grep "^Output written\|^No pages of output" "${PAPER}.log" 2>/dev/null || true
}

# Pass 1
run_xelatex 1

# bibtex — show only warnings/errors, suppress preamble chatter
echo "==> bibtex"
bibtex_out=$(bibtex "$PAPER" 2>&1 || true)
echo "$bibtex_out" | grep -Ei "warning|error" || echo "    OK (no warnings)"

# Passes 2+ — loop until cross-references stabilise
pass=2
while [[ $pass -le $MAX_PASSES ]]; do
  run_xelatex "$pass"
  if ! grep -qE "Rerun to get cross-references right|Rerun LaTeX" "${PAPER}.log" 2>/dev/null; then
    break
  fi
  if [[ $pass -eq $MAX_PASSES ]]; then
    echo "WARNING: cross-references did not stabilise after ${MAX_PASSES} passes"
    break
  fi
  ((pass++))
done

if [[ ! -f "$PDF" ]]; then
  echo "ERROR: PDF not produced. Check ${PAPER}.log for details."
  exit 1
fi

echo ""
echo "==> Done: $SCRIPT_DIR/$PDF (${pass} xelatex passes)"

# Surface non-trivial LaTeX warnings (suppress known benign ones)
WARNINGS=$(grep "^LaTeX Warning:" "${PAPER}.log" 2>/dev/null \
  | grep -v "float specifier changed\|Label(s) may have changed" \
  | sort -u || true)
if [[ -n "$WARNINGS" ]]; then
  echo ""
  echo "--- LaTeX warnings ---"
  echo "$WARNINGS"
fi

# Optional cleanup
if [[ "$CLEAN" == true ]]; then
  echo ""
  echo "==> Cleaning auxiliary files"
  rm -f "${PAPER}".{aux,bbl,blg,log,out,toc,lof,lot,fls,fdb_latexmk}
  echo "    Done"
fi
