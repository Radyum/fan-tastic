"""Spanish translations.

Keys are the English msgids used in the code. Plural messages (ngettext) map
to a (singular, plural) tuple. tests/test_i18n.py checks the catalog is complete.
"""

NBSP = " "

MESSAGES = {
    # --- hardware identification (identify.py, hwmon.py, nvidia.py) ---
    "Motherboard ({chip})": "Placa base ({chip})",
    "AMD processor": "Procesador AMD",
    "Intel processor": "Procesador Intel",
    "AMD graphics card": "Tarjeta gráfica AMD",
    "NVIDIA graphics card": "Tarjeta gráfica NVIDIA",
    "Intel graphics card": "Tarjeta gráfica Intel",
    "PWM fan": "Ventilador PWM",
    "Corsair power supply": "Fuente de alimentación Corsair",
    "NVMe SSD": "SSD NVMe",
    "Disk": "Disco",
    "ACPI thermal zone": "Zona térmica ACPI",
    "Intel Wi-Fi": "Wi-Fi Intel",
    "driver {name}": "controlador {name}",
    "NVIDIA driver (NVML)": "controlador NVIDIA (NVML)",
    "Pump": "Bomba",
    "Fans": "Ventiladores",
    "Coolant": "Líquido refrigerante",
    "VRM heatsink": "Disipador VRM",
    "CPU fan": "Ventilador de CPU",
    "Pump (W_PUMP)": "Bomba (W_PUMP)",
    "Fan {n}": "Ventilador {n}",
    "Temperature {n}": "Temperatura {n}",

    # --- hints (hardware.py) ---
    "the motherboard": "la placa base",
    "Fans connected to {board} are not visible: the {module} driver is not loaded.":
        "Los ventiladores conectados a {board} no son visibles: el controlador {module} no está cargado.",
    "The {module} driver is loaded but no motherboard controller was found "
    "(possible ACPI resource conflict, see the README).":
        "El controlador {module} está cargado pero no se encontró ningún controlador de placa base "
        "(posible conflicto de recursos ACPI, consulte el README).",
    "NVIDIA graphics card detected but NVML is unavailable ({error}): the proprietary NVIDIA driver is required.":
        "Tarjeta gráfica NVIDIA detectada pero NVML no está disponible ({error}): "
        "se necesita el controlador propietario de NVIDIA.",
    "ThinkPad fan control is disabled in the thinkpad_acpi module.":
        "El control del ventilador del ThinkPad está desactivado en el módulo thinkpad_acpi.",

    # --- service errors (daemon.py) ---
    "permission denied on {path} (the service must run as root)":
        "permiso denegado en {path} (el servicio debe ejecutarse como root)",
    "unknown command: {cmd}": "comando desconocido: {cmd}",
    "not authorized: add your user to allowed_users in /etc/fantastic/config.json":
        "no autorizado: añada su usuario a allowed_users en /etc/fantastic/config.json",
    "missing 'fan' parameter": "falta el parámetro «fan»",
    "invalid 'percent' parameter": "parámetro «percent» no válido",
    "invalid 'hidden' parameter": "parámetro «hidden» no válido",
    "invalid 'name' parameter": "parámetro «name» no válido",
    "unknown fan: {fan}": "ventilador desconocido: {fan}",
    "{fan} is read-only": "{fan} es de solo lectura",
    "invalid request": "solicitud no válida",
    "internal error: {error}": "error interno: {error}",

    # --- units (fmt.py) ---
    "{value} RPM": f"{{value}}{NBSP}rpm",
    "{value}%": f"{{value}}{NBSP}%",

    # --- shared by the GUI and the command line ---
    "read-only": "solo lectura",
    "manual": "manual",
    "auto": "auto",
    "automatic": "automático",
    "controllable": "controlable",
    "hidden": "oculto",
    "shown again": "visible de nuevo",
    "min. {value}": "mín. {value}",
    "Error: {error}": "Error: {error}",

    # --- command line (cli.py) ---
    "Fan detection and control.": "Detección y control de ventiladores.",
    "list fans (default command)": "listar los ventiladores (comando por defecto)",
    "also show temperatures": "mostrar también las temperaturas",
    "include hidden fans": "incluir los ventiladores ocultos",
    "JSON output": "salida JSON",
    "set the speed of a fan, or of all visible ones with 'all' (0-100%)":
        f"fijar la velocidad de un ventilador, o de todos los visibles con «all» (0-100{NBSP}%)",
    "number, identifier or name of the fan, or 'all'": "número, identificador o nombre del ventilador, o «all»",
    "hand a fan back to automatic control (or 'all')": "devolver un ventilador al control automático (o «all»)",
    "give a fan a name (no name: original name)": "dar un nombre a un ventilador (sin nombre: nombre original)",
    "hide a fan (its setting does not change)": "ocultar un ventilador (su ajuste no cambia)",
    "show a hidden fan again (or 'all')": "volver a mostrar un ventilador oculto (o «all»)",
    "detailed hardware inventory, without the service": "inventario detallado del hardware, sin el servicio",
    "open the graphical interface": "abrir la interfaz gráfica",
    'run the service (root; see "fantastic daemon --help")': "ejecutar el servicio (root; ver «fantastic daemon --help»)",
    "'{value}' is not an integer": "«{value}» no es un número entero",
    "the value must be between 0 and 100": "el valor debe estar entre 0 y 100",
    "failsafe 100%": f"seguridad 100{NBSP}%",
    "manual {value}": "manual {value}",
    'no fan matches \'{ref}\' (see "fantastic list")': "ningún ventilador coincide con «{ref}» (ver «fantastic list»)",
    "'{ref}' is ambiguous: {matches}": "«{ref}» es ambiguo: {matches}",
    "Name": "Nombre",
    "Device": "Dispositivo",
    "Speed": "Velocidad",
    "Duty": "Potencia",
    "Mode": "Modo",
    "Identifier": "Identificador",
    "Sensor": "Sensor",
    "Temperature": "Temperatura",
    "{mode} (hidden)": "{mode} (oculto)",
    "No fan detected.": "No se ha detectado ningún ventilador.",
    '{n} hidden fan: "fantastic list --all" shows it.': (
        "{n} ventilador oculto: «fantastic list --all» lo muestra.",
        "{n} ventiladores ocultos: «fantastic list --all» los muestra."),
    "Thermal failsafe active (threshold {temp} °C): driven fans forced to 100%.":
        f"Seguridad térmica activa (umbral {{temp}} °C): ventiladores controlados forzados al 100{NBSP}%.",
    "Fan '{label}' ({channel}): {reading} — {state}": "Ventilador «{label}» ({channel}): {reading} — {state}",
    "Temperature '{label}': {value}": "Temperatura «{label}»: {value}",
    "Error on {fan}: {error}": "Error en {fan}: {error}",
    "original name": "nombre original",
    "{n} fan shown again": ("{n} ventilador visible de nuevo", "{n} ventiladores visibles de nuevo"),
    "graphical interface unavailable ({error}).": "interfaz gráfica no disponible ({error}).",
    "Install: {command}": "Instale: {command}",
    "Refused by the service: {error}": "Rechazado por el servicio: {error}",
    "fantasticd service unreachable ({error}): reading the hardware directly.":
        "Servicio fantasticd inaccesible ({error}): lectura directa del hardware.",
    "fantasticd service unreachable ({error}). Is it running? sudo systemctl start fantasticd":
        "Servicio fantasticd inaccesible ({error}). ¿Está en marcha? sudo systemctl start fantasticd",

    # --- graphical interface (gui.py) ---
    "Detecting…": "Detectando…",
    "Language: {name}": "Idioma: {name}",
    "Look for new fans": "Buscar nuevos ventiladores",
    "Show hidden fans again": "Volver a mostrar los ventiladores ocultos",
    "Auto": "Auto",
    "Hand every fan, hidden ones included, back to automatic control":
        "Devolver todos los ventiladores, ocultos incluidos, al control automático",
    "Every visible fan at {value} (or at its minimum)": "Todos los ventiladores visibles al {value} (o a su mínimo)",
    "Hide this fan": "Ocultar este ventilador",
    "Let the hardware set the speed": "Dejar que el hardware regule la velocidad",
    "Empty = original name": "Vacío = nombre original",
    "Rename": "Renombrar",
    "Rename this fan": "Renombrar este ventilador",
    "thermal failsafe: 100%": f"seguridad térmica: 100{NBSP}%",
    "Copy the command": "Copiar el comando",
    "Command copied": "Comando copiado",
    "{n} fan at {value}": ("{n} ventilador al {value}", "{n} ventiladores al {value}"),
    "(hardware minimum applied for some)": "(mínimo del hardware aplicado a algunos)",
    "{n} fan failed: {error}": ("{n} ventilador con error: {error}", "{n} ventiladores con error: {error}"),
    "'{name}' hidden": "«{name}» oculto",
    "Undo": "Deshacer",
    "{n} hidden fan will reappear in the window. Its setting does not change.": (
        "{n} ventilador oculto volverá a aparecer en la ventana. Su ajuste no cambia.",
        "{n} ventiladores ocultos volverán a aparecer en la ventana. Sus ajustes no cambian."),
    "Show hidden fans again?": "¿Volver a mostrar los ventiladores ocultos?",
    "Cancel": "Cancelar",
    "Show": "Mostrar",
    "Read error: {error}": "Error de lectura: {error}",
    'fantasticd service unreachable: read-only display. Start it with "sudo systemctl start fantasticd".':
        "Servicio fantasticd inaccesible: visualización de solo lectura. "
        "Inícielo con «sudo systemctl start fantasticd».",
    "Your account is not allowed to control fans: see allowed_users in /etc/fantastic/config.json.":
        "Su cuenta no tiene permiso para controlar los ventiladores: vea allowed_users en /etc/fantastic/config.json.",
    "Thermal failsafe: a temperature exceeds {temp} °C, manually set fans run at 100%.":
        "Seguridad térmica: una temperatura supera los {temp} °C, "
        f"los ventiladores ajustados manualmente funcionan al 100{NBSP}%.",
    "{n} fan": ("{n} ventilador", "{n} ventiladores"),
    "{n} controllable": ("{n} controlable", "{n} controlables"),
    "{n} hidden": ("{n} oculto", "{n} ocultos"),
    "Suggestions": "Sugerencias",
    "All fans are hidden": "Todos los ventiladores están ocultos",
    "The eye-shaped button, top left, shows them again.":
        "El botón con forma de ojo, arriba a la izquierda, los vuelve a mostrar.",
    "No fan detected": "No se ha detectado ningún ventilador",
    "See the suggestions and the README.": "Consulte las sugerencias y el README.",
    "Temperatures ({n})": "Temperaturas ({n})",
    "Other temperatures": "Otras temperaturas",
}
