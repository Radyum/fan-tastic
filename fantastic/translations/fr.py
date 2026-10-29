"""French translations.

Keys are the English msgids used in the code. Plural messages (ngettext) map
to a (singular, plural) tuple; French uses the singular for 0 and 1.
tests/test_i18n.py checks that every msgid of the code is translated here.
"""

NBSP = " "

MESSAGES = {
    # --- hardware identification (identify.py, hwmon.py, nvidia.py) ---
    "Motherboard ({chip})": "Carte mère ({chip})",
    "AMD processor": "Processeur AMD",
    "Intel processor": "Processeur Intel",
    "AMD graphics card": "Carte graphique AMD",
    "NVIDIA graphics card": "Carte graphique NVIDIA",
    "Intel graphics card": "Carte graphique Intel",
    "PWM fan": "Ventilateur PWM",
    "Corsair power supply": "Alimentation Corsair",
    "NVMe SSD": "SSD NVMe",
    "Disk": "Disque",
    "ACPI thermal zone": "Zone thermique ACPI",
    "Intel Wi-Fi": "Wi-Fi Intel",
    "driver {name}": "pilote {name}",
    "NVIDIA driver (NVML)": "pilote NVIDIA (NVML)",
    "Pump": "Pompe",
    "Fans": "Ventilateurs",
    "Coolant": "Liquide de refroidissement",
    "VRM heatsink": "Dissipateur VRM",
    "CPU fan": "Ventilateur CPU",
    "Pump (W_PUMP)": "Pompe (W_PUMP)",
    "Fan {n}": "Ventilateur {n}",
    "Temperature {n}": "Température {n}",

    # --- hints (hardware.py) ---
    "the motherboard": "la carte mère",
    "Fans connected to {board} are not visible: the {module} driver is not loaded.":
        "Les ventilateurs branchés sur {board} ne sont pas visibles : le pilote {module} n'est pas chargé.",
    "The {module} driver is loaded but no motherboard controller was found "
    "(possible ACPI resource conflict, see the README).":
        "Le pilote {module} est chargé mais aucun contrôleur de carte mère n'a été trouvé "
        "(conflit de ressources ACPI possible, voir le README).",
    "NVIDIA graphics card detected but NVML is unavailable ({error}): the proprietary NVIDIA driver is required.":
        "Carte graphique NVIDIA détectée mais NVML est indisponible ({error}) : "
        "le pilote propriétaire NVIDIA est nécessaire.",
    "ThinkPad fan control is disabled in the thinkpad_acpi module.":
        "Le pilotage du ventilateur ThinkPad est désactivé dans le module thinkpad_acpi.",

    # --- service errors (daemon.py) ---
    "permission denied on {path} (the service must run as root)":
        "permission refusée sur {path} (le service doit tourner en root)",
    "unknown command: {cmd}": "commande inconnue : {cmd}",
    "not authorized: add your user to allowed_users in /etc/fantastic/config.json":
        "non autorisé : ajoutez votre utilisateur à allowed_users dans /etc/fantastic/config.json",
    "missing 'fan' parameter": "paramètre « fan » manquant",
    "invalid 'percent' parameter": "paramètre « percent » invalide",
    "invalid 'hidden' parameter": "paramètre « hidden » invalide",
    "invalid 'name' parameter": "paramètre « name » invalide",
    "unknown fan: {fan}": "ventilateur inconnu : {fan}",
    "{fan} is read-only": "{fan} est en lecture seule",
    "invalid request": "requête invalide",
    "internal error: {error}": "erreur interne : {error}",

    # --- units (fmt.py) ---
    "{value} RPM": f"{{value}}{NBSP}tr/min",
    "{value}%": f"{{value}}{NBSP}%",

    # --- shared by the GUI and the command line ---
    "read-only": "lecture seule",
    "manual": "manuel",
    "auto": "auto",
    "automatic": "automatique",
    "controllable": "pilotable",
    "hidden": "masqué",
    "shown again": "réaffiché",
    "min. {value}": "min. {value}",
    "Error: {error}": "Erreur : {error}",

    # --- command line (cli.py) ---
    "Fan detection and control.": "Détection et contrôle des ventilateurs.",
    "list fans (default command)": "lister les ventilateurs (commande par défaut)",
    "also show temperatures": "afficher aussi les températures",
    "include hidden fans": "inclure les ventilateurs masqués",
    "JSON output": "sortie JSON",
    "set the speed of a fan, or of all visible ones with 'all' (0-100%)":
        f"fixer la vitesse d'un ventilateur, ou de tous les visibles avec « all » (0-100{NBSP}%)",
    "number, identifier or name of the fan, or 'all'": "numéro, identifiant ou nom du ventilateur, ou « all »",
    "hand a fan back to automatic control (or 'all')": "rendre un ventilateur au contrôle automatique (ou « all »)",
    "give a fan a name (no name: original name)": "donner un nom à un ventilateur (sans nom : nom d'origine)",
    "hide a fan (its setting does not change)": "masquer un ventilateur (son réglage ne change pas)",
    "show a hidden fan again (or 'all')": "réafficher un ventilateur masqué (ou « all »)",
    "detailed hardware inventory, without the service": "inventaire détaillé du matériel, sans passer par le service",
    "open the graphical interface": "ouvrir l'interface graphique",
    'run the service (root; see "fantastic daemon --help")': "lancer le service (root ; voir « fantastic daemon --help »)",
    "'{value}' is not an integer": "« {value} » n'est pas un nombre entier",
    "the value must be between 0 and 100": "la valeur doit être comprise entre 0 et 100",
    "failsafe 100%": f"sécurité 100{NBSP}%",
    "manual {value}": "manuel {value}",
    'no fan matches \'{ref}\' (see "fantastic list")':
        "aucun ventilateur ne correspond à « {ref} » (voir « fantastic list »)",
    "'{ref}' is ambiguous: {matches}": "« {ref} » est ambigu : {matches}",
    "Name": "Nom",
    "Device": "Appareil",
    "Speed": "Vitesse",
    "Duty": "Puissance",
    "Mode": "Mode",
    "Identifier": "Identifiant",
    "Sensor": "Capteur",
    "Temperature": "Température",
    "{mode} (hidden)": "{mode} (masqué)",
    "No fan detected.": "Aucun ventilateur détecté.",
    '{n} hidden fan: "fantastic list --all" shows it.': (
        "{n} ventilateur masqué : « fantastic list --all » pour le voir.",
        "{n} ventilateurs masqués : « fantastic list --all » pour les voir."),
    "Thermal failsafe active (threshold {temp} °C): driven fans forced to 100%.":
        f"Sécurité thermique active (seuil {{temp}} °C) : ventilateurs pilotés forcés à 100{NBSP}%.",
    "Fan '{label}' ({channel}): {reading} — {state}": "Ventilateur « {label} » ({channel}) : {reading} — {state}",
    "Temperature '{label}': {value}": "Température « {label} » : {value}",
    "Error on {fan}: {error}": "Erreur sur {fan} : {error}",
    "original name": "nom d'origine",
    "{n} fan shown again": ("{n} ventilateur réaffiché", "{n} ventilateurs réaffichés"),
    "graphical interface unavailable ({error}).": "interface graphique indisponible ({error}).",
    "Install: {command}": "Installez : {command}",
    "Refused by the service: {error}": "Refusé par le service : {error}",
    "fantasticd service unreachable ({error}): reading the hardware directly.":
        "Service fantasticd injoignable ({error}) : lecture directe du matériel.",
    "fantasticd service unreachable ({error}). Is it running? sudo systemctl start fantasticd":
        "Service fantasticd injoignable ({error}). Est-il démarré ? sudo systemctl start fantasticd",

    # --- graphical interface (gui.py) ---
    "Detecting…": "Détection…",
    "Language: {name}": "Langue : {name}",
    "Look for new fans": "Rechercher de nouveaux ventilateurs",
    "Show hidden fans again": "Réafficher les ventilateurs masqués",
    "Auto": "Auto",
    "Hand every fan, hidden ones included, back to automatic control":
        "Rendre tous les ventilateurs, masqués compris, au contrôle automatique",
    "Every visible fan at {value} (or at its minimum)": "Tous les ventilateurs visibles à {value} (ou à leur minimum)",
    "Hide this fan": "Masquer ce ventilateur",
    "Let the hardware set the speed": "Laisser le matériel régler la vitesse",
    "Empty = original name": "Vide = nom d'origine",
    "Rename": "Renommer",
    "Rename this fan": "Renommer ce ventilateur",
    "thermal failsafe: 100%": f"sécurité thermique : 100{NBSP}%",
    "Copy the command": "Copier la commande",
    "Command copied": "Commande copiée",
    "{n} fan at {value}": ("{n} ventilateur à {value}", "{n} ventilateurs à {value}"),
    "(hardware minimum applied for some)": "(minimum matériel appliqué pour certains)",
    "{n} fan failed: {error}": ("{n} ventilateur en échec : {error}", "{n} ventilateurs en échec : {error}"),
    "'{name}' hidden": "« {name} » masqué",
    "Undo": "Annuler",
    "{n} hidden fan will reappear in the window. Its setting does not change.": (
        "{n} ventilateur masqué va réapparaître dans la fenêtre. Son réglage ne change pas.",
        "{n} ventilateurs masqués vont réapparaître dans la fenêtre. Leurs réglages ne changent pas."),
    "Show hidden fans again?": "Réafficher les ventilateurs masqués ?",
    "Cancel": "Annuler",
    "Show": "Réafficher",
    "Read error: {error}": "Erreur de lecture : {error}",
    'fantasticd service unreachable: read-only display. Start it with "sudo systemctl start fantasticd".':
        "Service fantasticd injoignable : affichage en lecture seule. "
        "Démarrez-le avec « sudo systemctl start fantasticd ».",
    "Your account is not allowed to control fans: see allowed_users in /etc/fantastic/config.json.":
        "Votre compte n'est pas autorisé à piloter les ventilateurs : "
        "voir allowed_users dans /etc/fantastic/config.json.",
    "Thermal failsafe: a temperature exceeds {temp} °C, manually set fans run at 100%.":
        "Sécurité thermique : une température dépasse {temp} °C, "
        f"les ventilateurs réglés manuellement tournent à 100{NBSP}%.",
    "{n} fan": ("{n} ventilateur", "{n} ventilateurs"),
    "{n} controllable": ("{n} pilotable", "{n} pilotables"),
    "{n} hidden": ("{n} masqué", "{n} masqués"),
    "Suggestions": "Suggestions",
    "All fans are hidden": "Tous les ventilateurs sont masqués",
    "The eye-shaped button, top left, shows them again.": "Le bouton en forme d'œil, en haut à gauche, les réaffiche.",
    "No fan detected": "Aucun ventilateur détecté",
    "See the suggestions and the README.": "Consultez les suggestions et le README.",
    "Temperatures ({n})": "Températures ({n})",
    "Other temperatures": "Autres températures",

    # --- fan stop warning (GUI and CLI) ---
    "Warning: below {value} the fan stops spinning.": "Attention : en dessous de {value}, le ventilateur s'arrête.",
    "fan stopped": "ventilateur à l'arrêt",

    # --- profiles ---
    'invalid profile name (1 to {n} characters)': 'nom de profil invalide (de 1 à {n} caractères)',
    'too many profiles (maximum {n})': 'trop de profils (maximum {n})',
    'unknown profile: {name}': 'profil inconnu : {name}',
    'No profile.': 'Aucun profil.',
    "Profile '{name}' saved": 'Profil « {name} » enregistré',
    "Profile '{name}' deleted": 'Profil « {name} » supprimé',
    "Profile '{name}' applied": 'Profil « {name} » appliqué',
    'manage profiles (saved sets of fan settings)': 'gérer les profils (jeux de réglages enregistrés)',
    'what to do with profiles': 'action à effectuer sur les profils',
    'profile name (10 characters max)': 'nom du profil (10 caractères maximum)',
    'a profile name is required': 'un nom de profil est requis',
    'Save the current settings as a profile': 'Enregistrer les réglages actuels comme profil',
    'Profile name': 'Nom du profil',
    'Save': 'Enregistrer',
    "Delete profile '{name}'": 'Supprimer le profil « {name} »',
    "Apply profile '{name}'": 'Appliquer le profil « {name} »',
}
