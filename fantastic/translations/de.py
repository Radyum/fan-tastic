"""German translations.

Keys are the English msgids used in the code. Plural messages (ngettext) map
to a (singular, plural) tuple. tests/test_i18n.py checks the catalog is complete.
"""

NBSP = " "

MESSAGES = {
    # --- hardware identification (identify.py, hwmon.py, nvidia.py) ---
    "Motherboard ({chip})": "Mainboard ({chip})",
    "AMD processor": "AMD-Prozessor",
    "Intel processor": "Intel-Prozessor",
    "AMD graphics card": "AMD-Grafikkarte",
    "NVIDIA graphics card": "NVIDIA-Grafikkarte",
    "Intel graphics card": "Intel-Grafikkarte",
    "PWM fan": "PWM-Lüfter",
    "Corsair power supply": "Corsair-Netzteil",
    "NVMe SSD": "NVMe-SSD",
    "Disk": "Festplatte",
    "ACPI thermal zone": "ACPI-Thermalzone",
    "Intel Wi-Fi": "Intel-WLAN",
    "driver {name}": "Treiber {name}",
    "NVIDIA driver (NVML)": "NVIDIA-Treiber (NVML)",
    "Pump": "Pumpe",
    "Fans": "Lüfter",
    "Coolant": "Kühlflüssigkeit",
    "VRM heatsink": "VRM-Kühlkörper",
    "CPU fan": "CPU-Lüfter",
    "Pump (W_PUMP)": "Pumpe (W_PUMP)",
    "Fan {n}": "Lüfter {n}",
    "Temperature {n}": "Temperatur {n}",

    # --- hints (hardware.py) ---
    "the motherboard": "das Mainboard",
    "Fans connected to {board} are not visible: the {module} driver is not loaded.":
        "Die an {board} angeschlossenen Lüfter sind nicht sichtbar: Der Treiber {module} ist nicht geladen.",
    "The {module} driver is loaded but no motherboard controller was found "
    "(possible ACPI resource conflict, see the README).":
        "Der Treiber {module} ist geladen, aber es wurde kein Mainboard-Controller gefunden "
        "(möglicher ACPI-Ressourcenkonflikt, siehe README).",
    "NVIDIA graphics card detected but NVML is unavailable ({error}): the proprietary NVIDIA driver is required.":
        "NVIDIA-Grafikkarte erkannt, aber NVML ist nicht verfügbar ({error}): "
        "Der proprietäre NVIDIA-Treiber wird benötigt.",
    "ThinkPad fan control is disabled in the thinkpad_acpi module.":
        "Die ThinkPad-Lüftersteuerung ist im Modul thinkpad_acpi deaktiviert.",

    # --- service errors (daemon.py) ---
    "permission denied on {path} (the service must run as root)":
        "Zugriff verweigert auf {path} (der Dienst muss als root laufen)",
    "unknown command: {cmd}": "unbekannter Befehl: {cmd}",
    "not authorized: add your user to allowed_users in /etc/fantastic/config.json":
        "nicht berechtigt: Fügen Sie Ihren Benutzer zu allowed_users in /etc/fantastic/config.json hinzu",
    "missing 'fan' parameter": "Parameter „fan“ fehlt",
    "invalid 'percent' parameter": "ungültiger Parameter „percent“",
    "invalid 'hidden' parameter": "ungültiger Parameter „hidden“",
    "invalid 'name' parameter": "ungültiger Parameter „name“",
    "unknown fan: {fan}": "unbekannter Lüfter: {fan}",
    "{fan} is read-only": "{fan} ist schreibgeschützt",
    "invalid request": "ungültige Anfrage",
    "internal error: {error}": "interner Fehler: {error}",

    # --- units (fmt.py) ---
    "{value} RPM": f"{{value}}{NBSP}U/min",
    "{value}%": f"{{value}}{NBSP}%",

    # --- shared by the GUI and the command line ---
    "read-only": "schreibgeschützt",
    "manual": "manuell",
    "auto": "auto",
    "automatic": "automatisch",
    "controllable": "steuerbar",
    "hidden": "ausgeblendet",
    "shown again": "wieder eingeblendet",
    "min. {value}": "min. {value}",
    "Error: {error}": "Fehler: {error}",

    # --- command line (cli.py) ---
    "Fan detection and control.": "Erkennung und Steuerung von Lüftern.",
    "list fans (default command)": "Lüfter auflisten (Standardbefehl)",
    "also show temperatures": "auch Temperaturen anzeigen",
    "include hidden fans": "ausgeblendete Lüfter einbeziehen",
    "JSON output": "JSON-Ausgabe",
    "set the speed of a fan, or of all visible ones with 'all' (0-100%)":
        f"Drehzahl eines Lüfters festlegen, oder aller sichtbaren mit „all“ (0-100{NBSP}%)",
    "number, identifier or name of the fan, or 'all'": "Nummer, Kennung oder Name des Lüfters, oder „all“",
    "hand a fan back to automatic control (or 'all')":
        "einen Lüfter an die automatische Steuerung zurückgeben (oder „all“)",
    "give a fan a name (no name: original name)": "einem Lüfter einen Namen geben (ohne Namen: ursprünglicher Name)",
    "hide a fan (its setting does not change)": "einen Lüfter ausblenden (seine Einstellung ändert sich nicht)",
    "show a hidden fan again (or 'all')": "einen ausgeblendeten Lüfter wieder einblenden (oder „all“)",
    "detailed hardware inventory, without the service": "detaillierte Hardware-Übersicht, ohne den Dienst",
    "open the graphical interface": "die grafische Oberfläche öffnen",
    'run the service (root; see "fantastic daemon --help")': "den Dienst starten (root; siehe „fantastic daemon --help“)",
    "'{value}' is not an integer": "„{value}“ ist keine ganze Zahl",
    "the value must be between 0 and 100": "der Wert muss zwischen 0 und 100 liegen",
    "failsafe 100%": f"Schutz 100{NBSP}%",
    "manual {value}": "manuell {value}",
    'no fan matches \'{ref}\' (see "fantastic list")': "kein Lüfter passt zu „{ref}“ (siehe „fantastic list“)",
    "'{ref}' is ambiguous: {matches}": "„{ref}“ ist mehrdeutig: {matches}",
    "Name": "Name",
    "Device": "Gerät",
    "Speed": "Drehzahl",
    "Duty": "Leistung",
    "Mode": "Modus",
    "Identifier": "Kennung",
    "Sensor": "Sensor",
    "Temperature": "Temperatur",
    "{mode} (hidden)": "{mode} (ausgeblendet)",
    "No fan detected.": "Kein Lüfter erkannt.",
    '{n} hidden fan: "fantastic list --all" shows it.': (
        "{n} ausgeblendeter Lüfter: „fantastic list --all“ zeigt ihn an.",
        "{n} ausgeblendete Lüfter: „fantastic list --all“ zeigt sie an."),
    "Thermal failsafe active (threshold {temp} °C): driven fans forced to 100%.":
        f"Übertemperaturschutz aktiv (Schwelle {{temp}} °C): gesteuerte Lüfter auf 100{NBSP}% gesetzt.",
    "Fan '{label}' ({channel}): {reading} — {state}": "Lüfter „{label}“ ({channel}): {reading} — {state}",
    "Temperature '{label}': {value}": "Temperatur „{label}“: {value}",
    "Error on {fan}: {error}": "Fehler bei {fan}: {error}",
    "original name": "ursprünglicher Name",
    "{n} fan shown again": ("{n} Lüfter wieder eingeblendet", "{n} Lüfter wieder eingeblendet"),
    "graphical interface unavailable ({error}).": "grafische Oberfläche nicht verfügbar ({error}).",
    "Install: {command}": "Installieren: {command}",
    "Refused by the service: {error}": "Vom Dienst abgelehnt: {error}",
    "fantasticd service unreachable ({error}): reading the hardware directly.":
        "Dienst fantasticd nicht erreichbar ({error}): Hardware wird direkt gelesen.",
    "fantasticd service unreachable ({error}). Is it running? sudo systemctl start fantasticd":
        "Dienst fantasticd nicht erreichbar ({error}). Läuft er? sudo systemctl start fantasticd",

    # --- graphical interface (gui.py) ---
    "Detecting…": "Erkennung…",
    "Language: {name}": "Sprache: {name}",
    "Look for new fans": "Nach neuen Lüftern suchen",
    "Show hidden fans again": "Ausgeblendete Lüfter wieder einblenden",
    "Auto": "Auto",
    "Hand every fan, hidden ones included, back to automatic control":
        "Alle Lüfter, auch ausgeblendete, an die automatische Steuerung zurückgeben",
    "Every visible fan at {value} (or at its minimum)": "Alle sichtbaren Lüfter auf {value} (oder auf ihr Minimum)",
    "Hide this fan": "Diesen Lüfter ausblenden",
    "Let the hardware set the speed": "Die Hardware die Drehzahl regeln lassen",
    "Empty = original name": "Leer = ursprünglicher Name",
    "Rename": "Umbenennen",
    "Rename this fan": "Diesen Lüfter umbenennen",
    "thermal failsafe: 100%": f"Übertemperaturschutz: 100{NBSP}%",
    "Copy the command": "Befehl kopieren",
    "Command copied": "Befehl kopiert",
    "{n} fan at {value}": ("{n} Lüfter auf {value}", "{n} Lüfter auf {value}"),
    "(hardware minimum applied for some)": "(Hardware-Minimum für einige angewendet)",
    "{n} fan failed: {error}": ("{n} Lüfter fehlgeschlagen: {error}", "{n} Lüfter fehlgeschlagen: {error}"),
    "'{name}' hidden": "„{name}“ ausgeblendet",
    "Undo": "Rückgängig",
    "{n} hidden fan will reappear in the window. Its setting does not change.": (
        "{n} ausgeblendeter Lüfter wird wieder im Fenster angezeigt. Seine Einstellung ändert sich nicht.",
        "{n} ausgeblendete Lüfter werden wieder im Fenster angezeigt. Ihre Einstellungen ändern sich nicht."),
    "Show hidden fans again?": "Ausgeblendete Lüfter wieder einblenden?",
    "Cancel": "Abbrechen",
    "Show": "Einblenden",
    "Read error: {error}": "Lesefehler: {error}",
    'fantasticd service unreachable: read-only display. Start it with "sudo systemctl start fantasticd".':
        "Dienst fantasticd nicht erreichbar: schreibgeschützte Anzeige. "
        "Starten Sie ihn mit „sudo systemctl start fantasticd“.",
    "Your account is not allowed to control fans: see allowed_users in /etc/fantastic/config.json.":
        "Ihr Konto darf die Lüfter nicht steuern: siehe allowed_users in /etc/fantastic/config.json.",
    "Thermal failsafe: a temperature exceeds {temp} °C, manually set fans run at 100%.":
        "Übertemperaturschutz: Eine Temperatur überschreitet {temp} °C, "
        f"manuell eingestellte Lüfter laufen mit 100{NBSP}%.",
    "{n} fan": ("{n} Lüfter", "{n} Lüfter"),
    "{n} controllable": ("{n} steuerbar", "{n} steuerbar"),
    "{n} hidden": ("{n} ausgeblendet", "{n} ausgeblendet"),
    "Suggestions": "Vorschläge",
    "All fans are hidden": "Alle Lüfter sind ausgeblendet",
    "The eye-shaped button, top left, shows them again.": "Die Schaltfläche mit dem Auge oben links blendet sie wieder ein.",
    "No fan detected": "Kein Lüfter erkannt",
    "See the suggestions and the README.": "Siehe Vorschläge und README.",
    "Temperatures ({n})": "Temperaturen ({n})",
    "Other temperatures": "Weitere Temperaturen",

    # --- fan stop warning (GUI and CLI) ---
    "Warning: below {value} the fan stops spinning.": "Warnung: Unter {value} bleibt der Lüfter stehen.",
    "fan stopped": "Lüfter steht",

    # --- profiles ---
    'invalid profile name (1 to {n} characters)': 'ungültiger Profilname (1 bis {n} Zeichen)',
    'too many profiles (maximum {n})': 'zu viele Profile (maximal {n})',
    'unknown profile: {name}': 'unbekanntes Profil: {name}',
    'No profile.': 'Kein Profil.',
    "Profile '{name}' saved": 'Profil „{name}“ gespeichert',
    "Profile '{name}' deleted": 'Profil „{name}“ gelöscht',
    "Profile '{name}' applied": 'Profil „{name}“ angewendet',
    'manage profiles (saved sets of fan settings)': 'Profile verwalten (gespeicherte Lüftereinstellungen)',
    'what to do with profiles': 'was mit den Profilen geschehen soll',
    'profile name (10 characters max)': 'Profilname (höchstens 10 Zeichen)',
    'a profile name is required': 'ein Profilname ist erforderlich',
    'Save the current settings as a profile': 'Aktuelle Einstellungen als Profil speichern',
    'Profile name': 'Profilname',
    'Save': 'Speichern',
    "Delete profile '{name}'": 'Profil „{name}“ löschen',
    "Apply profile '{name}'": 'Profil „{name}“ anwenden',
}
