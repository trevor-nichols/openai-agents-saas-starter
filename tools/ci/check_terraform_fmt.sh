#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_DIR="$ROOT_DIR/ops/infra"

if [ ! -d "$TARGET_DIR" ]; then
  echo "No ops/infra directory found."
  exit 0
fi

if ! command -v terraform >/dev/null 2>&1; then
  echo "terraform not found. Skipping terraform fmt check."
  exit 0
fi

terraform fmt -check -recursive "$TARGET_DIR"
