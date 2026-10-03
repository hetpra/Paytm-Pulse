#!/usr/bin/env bash
set -euo pipefail
if git ls-files | grep -vE '^(\.env$|scripts/secret_scan\.sh$)' | xargs grep -nE 'sk-[A-Za-z0-9]{12,}|AIza[A-Za-z0-9_-]{12,}|service_role|eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]+\.' ; then
  echo "Potential secret found" >&2; exit 1
fi
echo "Secret scan clean"
