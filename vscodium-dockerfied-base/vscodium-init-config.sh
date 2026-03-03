#!/bin/bash
set -ex
VSCODIUM_CONFIG_DIR="/home/${CLIENT_USERNAME}/.config/VSCodium"
VSCODIUM_CONFIG_DIR_USER="${VSCODIUM_CONFIG_DIR}/User"
VSCODE_OSS_DIR="/home/${CLIENT_USERNAME}/.vscode-oss"

# VSCODIUM_CONFIG_DIR and VSCODE_OSS_DIR
# were created in the Dockerfile.
# They might or might not be mounted to host directories.
# In case they are mounted we sync here.
# In case the are not mounted, no harm is done by syncing.
# If sync fails, those directories have probably not been created as intended.
sync ${VSCODIUM_CONFIG_DIR}
sync ${VSCODE_OSS_DIR}

echo "=== ls -alt ${VSCODIUM_CONFIG_DIR} ==="
ls -alt ${VSCODIUM_CONFIG_DIR}

echo "=== ls -alt ${VSCODE_OSS_DIR} ==="
ls -alt ${VSCODE_OSS_DIR}

echo ===================


if [ ! -f ${VSCODIUM_CONFIG_DIR_USER}/settings.json ]; then
    if [ ! -d  ${VSCODIUM_CONFIG_DIR_USER} ]; then
        mkdir -p ${VSCODIUM_CONFIG_DIR_USER}
    fi
cat << 'EOF' > ${VSCODIUM_CONFIG_DIR_USER}/settings.json
{
    "editor.fontSize": 14,
    "extensions.autoUpdate": false,
    "telemetry.enableTelemetry": false,
    "telemetry.telemetryLevel": "off",
    "workbench.startupEditor": "none",
    "workbench.welcomePage.enabled": false,
    "update.mode": "none",
    "git.ignoreMissingGitWarning": true,
    "files.autoSave": "afterDelay"
}
EOF
    chmod 644 ${VSCODIUM_CONFIG_DIR_USER}/settings.json
fi


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

