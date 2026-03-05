#!/bin/bash
set -e

echo "==== argv.json before"
cat "${HOME}/.vscode-oss/argv.json"


if [ ! -s "${VSCODE_OSS_DIR}/argv.json" ]; then
  cat <<'EOF' > "${VSCODE_OSS_DIR}/argv.json"
{
    "enable-crash-reporter": false,
    "enable-proposed-api": [
        "xaberus.remote-oss"
    ]
}
EOF
  chmod 644 "${VSCODE_OSS_DIR}/argv.json"
fi


echo "==== argv.json after"
cat "${HOME}/.vscode-oss/argv.json"


