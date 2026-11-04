#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# A shallow clone cannot prove full-history cleanliness.
if [ "$(git rev-parse --is-shallow-repository)" != false ]; then
  echo 'Refusing incomplete history' >&2
  exit 1
fi
gitleaks git --log-opts='--all --full-history' --redact --exit-code=1 .
gitleaks dir --redact --exit-code=1 .
