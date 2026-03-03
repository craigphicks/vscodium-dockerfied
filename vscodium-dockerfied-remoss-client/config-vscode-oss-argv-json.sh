#!/bin/bash
set -xe

echo "==== argv.json before"
cat "${HOME}/.vscode-oss/argv.json"
#/usr/local/bin/merge-xaberus-remote-oss.sh < "${HOME}/.vscode-oss/argv.json" > "${HOME}/.vscode-oss/argv.json"
echo "==== argv.json after"
cat "${HOME}/.vscode-oss/argv.json"


