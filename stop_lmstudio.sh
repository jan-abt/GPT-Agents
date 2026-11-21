#!/usr/bin/env bash
# Shut LM Studio down: unload all models, stop the server, and stop LM Studio's
# background service. The counterpart of start_lmstudio.sh.
#
#   ./stop_lmstudio.sh               # everything
#   ./stop_lmstudio.sh --keep-daemon # unload models + stop the server only
#
# Unloading frees the models' memory (about 5 GB for Qwen). Nothing is
# deleted: the model files stay on disk, and ./start_lmstudio.sh brings
# everything back.
set -euo pipefail

LMS="${LMS:-$HOME/.lmstudio/bin/lms}"
if [ ! -x "$LMS" ]; then
    echo "lms not found at $LMS - set LMS=/path/to/lms" >&2
    exit 1
fi

# 1. Unload every model from memory.
if [ -n "$("$LMS" ps 2>/dev/null | awk 'NR > 1 && NF')" ]; then
    "$LMS" unload --all
else
    echo "Models: none loaded"
fi

# 2. Stop the server on port 1234.
if "$LMS" server status 2>&1 | grep -q "is running"; then
    "$LMS" server stop
else
    echo "Server: not running"
fi

# 3. Stop LM Studio's background service (the "llmster" daemon), unless asked
#    to keep it. Any lms command, or start_lmstudio.sh, starts it again.
#    If the LM Studio app is running, the service is part of it and refuses to
#    stop on its own: then quit the app (its window or tray icon) to finish.
if [ "${1:-}" != "--keep-daemon" ]; then
    if message=$("$LMS" daemon down 2>&1); then
        echo "${message:-Background service: stopped}"
    elif grep -q "part of LM Studio" <<< "$message"; then
        echo "Background service: belongs to the running LM Studio app - quit the app to stop it."
        echo "(Models and server are already off, so it uses little memory.)"
    else
        echo "$message" >&2
        exit 1
    fi
fi
