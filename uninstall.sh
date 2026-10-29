#!/usr/bin/env bash
# Uninstalls Fantastic. Fans go back to automatic mode when the service stops.
# Usage: sudo ./uninstall.sh [--purge]   (--purge also removes the configuration and the state)
set -euo pipefail

APP_ID=io.fantastic.Fantastic
purge=0
[[ ${1:-} == --purge ]] && purge=1

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run with sudo: sudo $0 $*" >&2
    exit 1
fi

systemctl disable --now fantasticd.service 2>/dev/null || true
rm -f /etc/systemd/system/fantasticd.service
systemctl daemon-reload

rm -rf /opt/fantastic
rm -f /usr/local/bin/fantastic
rm -f "/usr/local/share/applications/$APP_ID.desktop"
rm -f "/usr/local/share/icons/hicolor/scalable/apps/$APP_ID.svg"
update-desktop-database -q /usr/local/share/applications 2>/dev/null || true

if [[ -f /etc/modules-load.d/fantastic.conf ]]; then
    echo "Kept: /etc/modules-load.d/fantastic.conf (driver $(cat /etc/modules-load.d/fantastic.conf) loaded at boot)."
    echo "Remove it by hand if you no longer want it."
fi

if [[ $purge -eq 1 ]]; then
    rm -rf /etc/fantastic /var/lib/fantastic
    echo "Configuration and state removed."
else
    echo "Kept: /etc/fantastic (configuration) and /var/lib/fantastic (targets, names). Use --purge to remove them."
fi
echo "Fantastic is uninstalled."
