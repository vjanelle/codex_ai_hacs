#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${containerWorkspaceFolder:-/workspaces/codex-ai-hacs}"
CORE_DIR="/workspaces/home-assistant-core"
CUSTOM_COMPONENTS_DIR="$CORE_DIR/config/custom_components"

git config --global --add safe.directory "$REPO_DIR"

if [ ! -d "$CORE_DIR/.git" ]; then
  git clone https://github.com/home-assistant/core.git "$CORE_DIR"
fi

git config --global --add safe.directory "$CORE_DIR"

cd "$CORE_DIR"
script/setup

mkdir -p "$CUSTOM_COMPONENTS_DIR"
ln -sfn "$REPO_DIR/custom_components/codex_ai" "$CUSTOM_COMPONENTS_DIR/codex_ai"

uv pip install openai==2.21.0

echo "Codex AI linked into $CUSTOM_COMPONENTS_DIR/codex_ai"
echo "Run Home Assistant: cd $CORE_DIR && hass -c config"
echo "Run Codex AI tests: cd $REPO_DIR && python -m unittest discover -s tests"
