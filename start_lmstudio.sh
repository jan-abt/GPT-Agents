#!/usr/bin/env bash
# Start LM Studio's local server and load the models this repo uses.
# See README.md ("Before starting").
#
#   ./start_lmstudio.sh                         # chat model + embedding model
#   ./start_lmstudio.sh llama-3.2-3b-instruct   # load other models instead
#
# Safe to run again: a model that's already loaded is skipped. (Running
# `lms load` twice would start a second copy, using its memory twice.)
set -euo pipefail

LMS="${LMS:-$HOME/.lmstudio/bin/lms}"     # LM Studio's command-line tool
if [ ! -x "$LMS" ]; then
    echo "lms not found at $LMS - install LM Studio and start it once, or set LMS=/path/to/lms" >&2
    exit 1
fi

if [ "$#" -gt 0 ]; then
    MODELS=("$@")
else
    MODELS=(
        qwen2.5-7b-instruct                    # chat, tool calls, code, judging
        text-embedding-nomic-embed-text-v1.5   # embeddings (DIY GPTs, chapters 8 and 11)
    )
fi

# 1. The server (http://localhost:1234/v1) - the scripts' OPENAI_BASE_URL.
if "$LMS" server status 2>&1 | grep -q "is running"; then
    echo "Server: already running"
else
    "$LMS" server start
fi

# 2. The models, unless they're loaded already.
loaded=$("$LMS" ps 2>/dev/null | awk 'NR > 1 { print $1 }')   # first column: identifiers
for model in "${MODELS[@]}"; do
    if grep -qx "$model" <<< "$loaded"; then
        echo "Model $model: already loaded"
    else
        echo "Model $model: loading..."
        "$LMS" load "$model" --yes
    fi
done

echo
"$LMS" ps
