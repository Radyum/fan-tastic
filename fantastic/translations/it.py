"""Italian translations.

Keys are the English msgids used in the code. Plural messages (ngettext) map
to a (singular, plural) tuple. tests/test_i18n.py checks the catalog is complete.
"""

NBSP = " "

MESSAGES = {
    # --- hardware identification (identify.py, hwmon.py, nvidia.py) ---
    "Motherboard ({chip})": "Scheda madre ({chip})",
    "AMD processor": "Processore AMD",
    "Intel processor": "Processore Intel",
    "AMD graphics card": "Scheda grafica AMD",
    "NVIDIA graphics card": "Scheda grafica NVIDIA",
    "Intel graphics card": "Scheda grafica Intel",
    "PWM fan": "Ventola PWM",
    "Corsair power supply": "Alimentatore Corsair",
    "NVMe SSD": "SSD NVMe",
    "Disk": "Disco",
    "ACPI thermal zone": "Zona termica ACPI",
    "Intel Wi-Fi": "Wi-Fi Intel",
    "driver {name}": "driver {name}",
    "NVIDIA driver (NVML)": "driver NVIDIA (NVML)",
    "Pump": "Pompa",
    "Fans": "Ventole",
    "Coolant": "Liquido di raffreddamento",
    "VRM heatsink": "Dissipatore VRM",
    "CPU fan": "Ventola CPU",
    "Pump (W_PUMP)": "Pompa (W_PUMP)",
    "Fan {n}": "Ventola {n}",
    "Temperature {n}": "Temperatura {n}",

    # --- hints (hardware.py) ---
    "the motherboard": "questa scheda madre",
    "Fans connected to {board} are not visible: the {module} driver is not loaded.":
        "Le ventole collegate a {board} non sono visibili: il driver {module} non è caricato.",
    "The {module} driver is loaded but no motherboard controller was found "
    "(possible ACPI resource conflict, see the README).":
        "Il driver {module} è caricato ma non è stato trovato alcun controller della scheda madre "
        "(possibile conflitto di risorse ACPI, vedere il README).",
    "NVIDIA graphics card detected but NVML is unavailable ({error}): the proprietary NVIDIA driver is required.":
        "Scheda grafica NVIDIA rilevata ma NVML non è disponibile ({error}): "
        "è necessario il driver proprietario NVIDIA.",
    "ThinkPad fan control is disabled in the thinkpad_acpi module.":
        "Il controllo della ventola del ThinkPad è disattivato nel modulo thinkpad_acpi.",

    # --- service errors (daemon.py) ---
    "permission denied on {path} (the service must run as root)":
        "permesso negato su {path} (il servizio deve essere eseguito come root)",
    "unknown command: {cmd}": "comando sconosciuto: {cmd}",
    "not authorized: add your user to allowed_users in /etc/fantastic/config.json":
        "non autorizzato: aggiungere il proprio utente a allowed_users in /etc/fantastic/config.json",
    "missing 'fan' parameter": "parametro «fan» mancante",
    "invalid 'percent' parameter": "parametro «percent» non valido",
    "invalid 'hidden' parameter": "parametro «hidden» non valido",
    "invalid 'name' parameter": "parametro «name» non valido",
    "unknown fan: {fan}": "ventola sconosciuta: {fan}",
    "{fan} is read-only": "{fan} è di sola lettura",
    "invalid request": "richiesta non valida",
    "internal error: {error}": "errore interno: {error}",

    # --- units (fmt.py) ---
    "{value} RPM": f"{{value}}{NBSP}giri/min",
    "{value}%": "{value}%",

    # --- shared by the GUI and the command line ---
    "read-only": "sola lettura",
    "manual": "manuale",
    "auto": "auto",
    "automatic": "automatico",
    "controllable": "controllabile",
    "hidden": "nascosta",
    "shown again": "di nuovo visibile",
    "min. {value}": "min. {value}",
    "Error: {error}": "Errore: {error}",

    # --- command line (cli.py) ---
    "Fan detection and control.": "Rilevamento e controllo delle ventole.",
    "list fans (default command)": "elencare le ventole (comando predefinito)",
    "also show temperatures": "mostrare anche le temperature",
    "include hidden fans": "includere le ventole nascoste",
    "JSON output": "output JSON",
    "set the speed of a fan, or of all visible ones with 'all' (0-100%)":
        "impostare la velocità di una ventola, o di tutte quelle visibili con «all» (0-100%)",
    "number, identifier or name of the fan, or 'all'": "numero, identificatore o nome della ventola, o «all»",
    "hand a fan back to automatic control (or 'all')": "riportare una ventola al controllo automatico (o «all»)",
    "give a fan a name (no name: original name)": "dare un nome a una ventola (senza nome: nome originale)",
    "hide a fan (its setting does not change)": "nascondere una ventola (la sua impostazione non cambia)",
    "show a hidden fan again (or 'all')": "mostrare di nuovo una ventola nascosta (o «all»)",
    "detailed hardware inventory, without the service": "inventario dettagliato dell'hardware, senza il servizio",
    "open the graphical interface": "aprire l'interfaccia grafica",
    'run the service (root; see "fantastic daemon --help")': "avviare il servizio (root; vedere «fantastic daemon --help»)",
    "'{value}' is not an integer": "«{value}» non è un numero intero",
    "the value must be between 0 and 100": "il valore deve essere compreso tra 0 e 100",
    "failsafe 100%": "sicurezza 100%",
    "manual {value}": "manuale {value}",
    'no fan matches \'{ref}\' (see "fantastic list")': "nessuna ventola corrisponde a «{ref}» (vedere «fantastic list»)",
    "'{ref}' is ambiguous: {matches}": "«{ref}» è ambiguo: {matches}",
    "Name": "Nome",
    "Device": "Dispositivo",
    "Speed": "Velocità",
    "Duty": "Potenza",
    "Mode": "Modalità",
    "Identifier": "Identificatore",
    "Sensor": "Sensore",
    "Temperature": "Temperatura",
    "{mode} (hidden)": "{mode} (nascosta)",
    "No fan detected.": "Nessuna ventola rilevata.",
    '{n} hidden fan: "fantastic list --all" shows it.': (
        "{n} ventola nascosta: «fantastic list --all» la mostra.",
        "{n} ventole nascoste: «fantastic list --all» le mostra."),
    "Thermal failsafe active (threshold {temp} °C): driven fans forced to 100%.":
        "Sicurezza termica attiva (soglia {temp} °C): ventole controllate forzate al 100%.",
    "Fan '{label}' ({channel}): {reading} — {state}": "Ventola «{label}» ({channel}): {reading} — {state}",
    "Temperature '{label}': {value}": "Temperatura «{label}»: {value}",
    "Error on {fan}: {error}": "Errore su {fan}: {error}",
    "original name": "nome originale",
    "{n} fan shown again": ("{n} ventola di nuovo visibile", "{n} ventole di nuovo visibili"),
    "graphical interface unavailable ({error}).": "interfaccia grafica non disponibile ({error}).",
    "Install: {command}": "Installare: {command}",
    "Refused by the service: {error}": "Rifiutato dal servizio: {error}",
    "fantasticd service unreachable ({error}): reading the hardware directly.":
        "Servizio fantasticd non raggiungibile ({error}): lettura diretta dell'hardware.",
    "fantasticd service unreachable ({error}). Is it running? sudo systemctl start fantasticd":
        "Servizio fantasticd non raggiungibile ({error}). È in esecuzione? sudo systemctl start fantasticd",

    # --- graphical interface (gui.py) ---
    "Detecting…": "Rilevamento…",
    "Language: {name}": "Lingua: {name}",
    "Look for new fans": "Cerca nuove ventole",
    "Show hidden fans again": "Mostra di nuovo le ventole nascoste",
    "Auto": "Auto",
    "Hand every fan, hidden ones included, back to automatic control":
        "Riporta tutte le ventole, comprese quelle nascoste, al controllo automatico",
    "Every visible fan at {value} (or at its minimum)": "Tutte le ventole visibili al {value} (o al loro minimo)",
    "Hide this fan": "Nascondi questa ventola",
    "Let the hardware set the speed": "Lascia che l'hardware regoli la velocità",
    "Empty = original name": "Vuoto = nome originale",
    "Rename": "Rinomina",
    "Rename this fan": "Rinomina questa ventola",
    "thermal failsafe: 100%": "sicurezza termica: 100%",
    "Copy the command": "Copia il comando",
    "Command copied": "Comando copiato",
    "{n} fan at {value}": ("{n} ventola al {value}", "{n} ventole al {value}"),
    "(hardware minimum applied for some)": "(minimo hardware applicato ad alcune)",
    "{n} fan failed: {error}": ("{n} ventola non riuscita: {error}", "{n} ventole non riuscite: {error}"),
    "'{name}' hidden": "«{name}» nascosta",
    "Undo": "Annulla",
    "{n} hidden fan will reappear in the window. Its setting does not change.": (
        "{n} ventola nascosta riapparirà nella finestra. La sua impostazione non cambia.",
        "{n} ventole nascoste riappariranno nella finestra. Le loro impostazioni non cambiano."),
    "Show hidden fans again?": "Mostrare di nuovo le ventole nascoste?",
    "Cancel": "Annulla",
    "Show": "Mostra",
    "Read error: {error}": "Errore di lettura: {error}",
    'fantasticd service unreachable: read-only display. Start it with "sudo systemctl start fantasticd".':
        "Servizio fantasticd non raggiungibile: visualizzazione in sola lettura. "
        "Avviarlo con «sudo systemctl start fantasticd».",
    "Your account is not allowed to control fans: see allowed_users in /etc/fantastic/config.json.":
        "Il tuo account non è autorizzato a controllare le ventole: vedere allowed_users in /etc/fantastic/config.json.",
    "Thermal failsafe: a temperature exceeds {temp} °C, manually set fans run at 100%.":
        "Sicurezza termica: una temperatura supera {temp} °C, le ventole impostate manualmente girano al 100%.",
    "{n} fan": ("{n} ventola", "{n} ventole"),
    "{n} controllable": ("{n} controllabile", "{n} controllabili"),
    "{n} hidden": ("{n} nascosta", "{n} nascoste"),
    "Suggestions": "Suggerimenti",
    "All fans are hidden": "Tutte le ventole sono nascoste",
    "The eye-shaped button, top left, shows them again.": "Il pulsante a forma di occhio, in alto a sinistra, le mostra di nuovo.",
    "No fan detected": "Nessuna ventola rilevata",
    "See the suggestions and the README.": "Consultare i suggerimenti e il README.",
    "Temperatures ({n})": "Temperature ({n})",
    "Other temperatures": "Altre temperature",
}
