#!/bin/bash
set -e
codium --no-sandbox --disable-gpu --disable-gpu-sandbox --disable-workspace-trust
while pgrep -f "codium --no-sandbox" >/dev/null; do
    sleep 1
done