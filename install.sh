#!/usr/bin/env bash
# Installs Fantastic: fantasticd service (root, systemd), "fantastic" command and desktop launcher.
# Usage: sudo ./install.sh [--no-apt]
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX=/opt/fantastic
BIN=/usr/local/bin/fantastic
UNIT=/etc/systemd/system/fantasticd.service
SHARE=/usr/local/share
APP_ID=io.fantastic.Fantastic
MODULES_CONF=/etc/modules-load.d/fantastic.conf

use_apt=1
for arg in "$@"; do
    case "$arg" in
        --no-apt) use_apt=0 ;;
        -h|--help) sed -n '2,3p' "$0"; exit 0 ;;
        *) echo "Unknown option: $arg" >&2; exit 2 ;;
    esac
done

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run with sudo: sudo $0 $*" >&2
    exit 1
fi
TARGET_USER="${SUDO_USER:-}"

step() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

step "Dependencies"
if [[ $use_apt -eq 1 ]] && command -v apt-get >/dev/null; then
    apt-get install -y python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
else
    echo "Package installation skipped. Required: Python ≥ 3.10, PyGObject, GTK 4, libadwaita ≥ 1.5."
fi

step "Copying the program to $PREFIX"
rm -rf "$PREFIX/fantastic"
install -d "$PREFIX"
cp -r "$SRC/fantastic" "$PREFIX/"
install -m 644 "$SRC/README.md" "$PREFIX/README.md"
find "$PREFIX" -name '__pycache__' -prune -exec rm -rf {} +
chown -R root:root "$PREFIX"
chmod -R u=rwX,go=rX "$PREFIX"

# -I: the service runs as root, so PYTHON* variables and the current directory are ignored.
cat > "$BIN" <<EOF
#!/usr/bin/python3 -I
import sys
sys.path.insert(0, "$PREFIX")
from fantastic.cli import main
sys.exit(main())
EOF
chmod 755 "$BIN"
echo "Command installed: $BIN"

step "Configuration"
install -d /etc/fantastic
if [[ -f /etc/fantastic/config.json ]]; then
    echo "/etc/fantastic/config.json already exists: kept."
else
    cat > /etc/fantastic/config.json <<EOF
{
  "allowed_users": [${TARGET_USER:+\"$TARGET_USER\"}],
  "allowed_groups": ["sudo", "wheel", "admin", "fantastic"],
  "failsafe_temp": 90,
  "failsafe_hysteresis": 10,
  "poll_interval": 2,
  "rescan_interval": 15,
  "nvidia": true
}
EOF
    echo "Configuration created: /etc/fantastic/config.json"
fi

step "Desktop launcher"
install -Dm 644 "$SRC/data/$APP_ID.desktop" "$SHARE/applications/$APP_ID.desktop"
install -Dm 644 "$SRC/data/$APP_ID.svg" "$SHARE/icons/hicolor/scalable/apps/$APP_ID.svg"
update-desktop-database -q "$SHARE/applications" 2>/dev/null || true

step "Motherboard fan controller driver"
superio_loaded() { grep -qsE '^(nct6|it8|f71|w83)' /sys/class/hwmon/hwmon*/name; }
persisted() { grep -qsxE "[[:space:]]*$1[[:space:]]*" /etc/modules /etc/modules-load.d/*.conf; }
chassis=$(cat /sys/class/dmi/id/chassis_type 2>/dev/null || echo 0)
if superio_loaded; then
    loaded=""
    for m in nct6775 it87; do [[ -d /sys/module/$m ]] && loaded=$m; done
    if [[ -n $loaded ]] && ! persisted "$loaded"; then
        # Loaded by hand (modprobe): make it permanent so it comes back at boot.
        echo "$loaded" > "$MODULES_CONF"
        echo "Driver $loaded added to $MODULES_CONF for the next boots."
    else
        echo "Controller already available."
    fi
elif [[ " 8 9 10 11 14 30 31 32 " == *" $chassis "* ]]; then
    echo "Laptop detected: no Super I/O controller to load."
else
    vendor=$(cat /sys/class/dmi/id/board_vendor 2>/dev/null || true)
    module=nct6775
    [[ ${vendor,,} == *gigabyte* ]] && module=it87
    answer=n
    if [[ -t 0 ]]; then
        read -rp "Motherboard fans are not visible. Load the $module driver (now and at every boot)? [Y/n] " answer || true
        answer=${answer:-y}
    fi
    if [[ ${answer,,} == y* || ${answer,,} == o* ]]; then
        if modprobe "$module" && sleep 1 && superio_loaded; then
            echo "$module" > "$MODULES_CONF"
            echo "Driver $module loaded, and added to $MODULES_CONF for the next boots."
        else
            modprobe -r "$module" 2>/dev/null || true
            echo "The $module driver found no controller: see the Troubleshooting section of docs/INSTALL.md."
        fi
    else
        echo "Skipped. To do it later: sudo modprobe $module"
    fi
fi

step "fantasticd service"
install -m 644 "$SRC/data/fantasticd.service" "$UNIT"
systemctl daemon-reload
systemctl enable fantasticd.service
systemctl restart fantasticd.service
sleep 2
if systemctl is-active --quiet fantasticd.service; then
    echo "Service running."
    "$BIN" list || true
else
    echo "The service did not start: journalctl -u fantasticd -n 50" >&2
    exit 1
fi

step "Done"
echo "Graphical interface: applications menu → Fantastic, or \"fantastic gui\"."
