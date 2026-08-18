"""Die MCP-Werkzeugverträge — als reine Daten, ohne SDK.

Warum die Schemas hier und nicht im Server stehen
-------------------------------------------------
Das MCP-SDK ist MIT-lizenziert und damit zulässig, bringt aber 19 transitive
Abhängigkeiten mit. Der Kern dieses Projekts hat bewusst **keine** Laufzeitabhängigkeit
(Regel 4: aus Python heraus nutzbar, ohne dass irgendetwas läuft). Die Verträge sind
Daten — sie brauchen kein SDK. Nur der Server in `mcp_server.py` braucht eines, und der
ist ein optionaler Zusatz.

Damit bleibt auch die Lizenzprüfung überschaubar: Wer die Bibliothek benutzt, zieht sich
nichts ein; wer den Server betreibt, entscheidet das bewusst.

Was KosmoOrbit von uns verlangt
-------------------------------
Aus `KosmoOrbit/src/lib/pipeline.ts` gelesen (Phase 0/2, Commit `a69af5d`):

* **`inputSchema` UND `outputSchema`** je Werkzeug. Fehlt eines, meldet
  `pipelineReadiness` unsere Kanten als tot — das Werkzeug erschiene im Cockpit, wäre
  aber nicht verdrahtbar.
* **Kanten entstehen über Feldnamen-Gleichheit.** `mergeInputs` legt die Ausgaben aller
  Vorgänger übereinander; eine Kante trägt nur, wenn ein Ausgabefeld des einen genauso
  heisst wie ein Eingabefeld des nächsten.
* **Kein `additionalProperties: false`.** `mergeInputs` reicht ohnehin sämtliche
  Vorgängerfelder durch; ein geschlossenes Schema würde daran scheitern.

Die Entscheidung zu `required`
------------------------------
KosmoOrbits Prüfung liest ausschliesslich die flache Liste `inputSchema.required`. Sie
kennt kein `anyOf`. Unser Werkzeug akzeptiert aber **entweder** `ifc_path` **oder**
`glb_path` — beide Verdrahtungen sind gültig (eigener IFC-Pfad nach Regel 4, oder
Einfügen hinter `kosmodraw_export_glb`).

Stünde `ifc_path` in `required`, meldete die Prüfung bei einer Verdrahtung ab
`export_glb` ein fehlendes Pflichtfeld — und umgekehrt. Ein Entweder-oder lässt sich dort
nicht ausdrücken.

Deshalb bleibt `required` leer, und die Bedingung „genau eine Geometriequelle" wird zur
**Laufzeit** geprüft (`contracts.validate_render_scene`). Das ist kein Aufweichen: Der
Fehler wird weiterhin laut gemeldet, nur eben dort, wo er sich vollständig ausdrücken
lässt. Der Preis ist ehrlich zu benennen — die Prüfung im Cockpit kann diesen einen
Fehler nicht vorab sehen.
"""
from __future__ import annotations

LANE = "aiimaging"

#: Werkzeugnamen tragen den Lane-Namen nochmals — KosmoOrbit ruft
#: `mcp__<servername>__<toolname>`, also `mcp__aiimaging__aiimaging_enqueue_render`.
#: Die Doppelung ist Ökosystem-Konvention (belegt an `mcp__kosmodraw__kosmodraw_*`).
WERKZEUG_ENQUEUE = f"{LANE}_enqueue_render"
WERKZEUG_QUERY = f"{LANE}_query_render"
WERKZEUG_PRUEFE = f"{LANE}_check_geometry"

#: Feldnamen der Nachbar-Lanes, belegt in Phase 0 aus `kosmodraw_mcp_server.py:274-300`.
#: Sie sind bindend: Ein abweichender Name erzeugt keine Kante und keine Fehlermeldung.
GEOMETRIE_FELDER = ("ifc_path", "glb_path", "up_axis", "bbox")


_GEOMETRIE_EINGANG = {
    "ifc_path": {
        "type": "string",
        "description": "Quell-IFC (IFC4 oder IFC2X3; ArchiCAD liefert IFC2X3). "
                       "Eigener Pfad — wir konvertieren selbst und erzeugen "
                       "glTF-konformes Y-up. Kommt üblicherweise aus kosmodraw_export_ifc.",
    },
    "glb_path": {
        "type": "string",
        "description": "Fertige glb statt IFC. Dann ist up_axis PFLICHT — siehe dort.",
    },
    "up_axis": {
        "type": "string",
        "description": "Up-Achse der glb: 'Y' (glTF-Standard) oder 'Z' (rohe "
                       "IFC-Koordinaten, z.B. aus kosmodraw_export_glb). Pflicht bei "
                       "glb_path. Wird NICHT geraten: glTF kennt kein Up-Achsen-Feld, "
                       "und eine Z-up-glb landet in Blender liegend auf der Seite — "
                       "Tiefenkarte und Geometrie-QA wären still verdreht.",
    },
    "bbox": {
        "type": "array",
        "description": "Optionale Bounding-Box [[xmin,ymin,zmin],[xmax,ymax,zmax]] in "
                       "Metern. Erlaubt die Massstabs- und Georeferenzprüfung, bevor "
                       "GPU-Zeit verbraucht wird.",
    },
}


def _eingang_enqueue() -> dict:
    return {
        "type": "object",
        # KEIN additionalProperties: false — mergeInputs reicht alle Vorgängerfelder durch.
        "properties": {
            **_GEOMETRIE_EINGANG,
            "out_dir": {
                "type": "string",
                "description": "Ausgabeverzeichnis. Optional — ohne Angabe wird unter "
                               "/tmp gewählt. Muss unter $HOME oder /tmp liegen "
                               "(Pfad-Sandbox des Ökosystems).",
            },
            "aufloesung": {"type": "integer", "description": "Kantenlänge in Pixeln, Vorgabe 512."},
            "samples": {"type": "integer", "description": "Cycles-Samples, Vorgabe 16."},
            "approval_token": {
                "type": "string",
                "description": "Freigabe CONFIRMED_RENDER_*. OHNE Token bleibt der "
                               "Auftrag auf awaiting_approval und rührt die GPU nicht an "
                               "— das ist der Regelfall und der Freeze-Schutz.",
            },
        },
        # Bewusst leer, siehe Modul-Docstring: KosmoOrbits Prüfung kennt kein Entweder-oder.
        "required": [],
    }


def _ausgang_enqueue() -> dict:
    return {
        "type": "object",
        "properties": {
            "job_id": {"type": "string"},
            "status": {"type": "string",
                       "description": "awaiting_approval | queued — nie 'running'. "
                                      "Dieses Werkzeug führt nichts aus."},
            "geometry_ref": {"type": ["string", "null"],
                             "description": "Ökosystem-Begriff für 'hier liegt die "
                                            "3D-Geometrie'. Zeigt auf die glb."},
            "glb_path": {"type": ["string", "null"]},
            "up_axis": {"type": ["string", "null"]},
            "bbox": {"type": ["array", "null"]},
            "out_dir": {"type": ["string", "null"]},
            "torwaechter": {"type": "object",
                            "description": "Urteil der Massstabs-/Georeferenzprüfung."},
            "error": {"type": ["string", "null"]},
        },
    }


def _eingang_query() -> dict:
    return {
        "type": "object",
        "properties": {
            "job_id": {"type": "string", "description": "Auftrag aus enqueue_render."},
        },
        "required": ["job_id"],
    }


def _ausgang_query() -> dict:
    return {
        "type": "object",
        "properties": {
            "job_id": {"type": "string"},
            "status": {"type": "string"},
            "geometry_ref": {"type": ["string", "null"]},
            "depth_exr": {"type": ["string", "null"]},
            "images": {"type": "array"},
            "erstellt": {"type": ["string", "null"]},
            "geaendert": {"type": ["string", "null"]},
            "error": {"type": ["string", "null"]},
        },
    }


def _eingang_pruefe() -> dict:
    return {
        "type": "object",
        "properties": dict(_GEOMETRIE_EINGANG),
        "required": [],
    }


def _ausgang_pruefe() -> dict:
    return {
        "type": "object",
        "properties": {
            "entscheidung": {"type": "string",
                             "description": "annehmen | ablehnen_massstab | ablehnen_konversion"},
            "begruendung": {"type": "string"},
            "bbox": {"type": ["array", "null"]},
            "up_axis": {"type": ["string", "null"]},
            "empfiehlt_neuzentrierung": {"type": "boolean"},
            "error": {"type": ["string", "null"]},
        },
    }


#: Die vollständigen Werkzeugverträge. Reine Daten — der Server in `mcp_server.py`
#: übersetzt sie nur, er trägt keine Logik (Regel 4: die Bibliothek muss ohne ihn laufen).
WERKZEUGE: dict[str, dict] = {
    WERKZEUG_ENQUEUE: {
        "name": WERKZEUG_ENQUEUE,
        "description": (
            "Geometrie → gegateter Render-Auftrag. Konvertiert IFC→glb (bzw. übernimmt "
            "eine fertige glb), prüft Massstab und Georeferenz und legt einen Auftrag ab. "
            "Rührt die GPU NICHT an: ohne Freigabe-Token bleibt der Auftrag auf "
            "awaiting_approval. Die Ausführung geschieht ausserhalb der Pipeline."
        ),
        "inputSchema": _eingang_enqueue(),
        "outputSchema": _ausgang_enqueue(),
        "readonly": True,
    },
    WERKZEUG_QUERY: {
        "name": WERKZEUG_QUERY,
        "description": "Status und Ergebnis eines Render-Auftrags lesen. Rein lesend.",
        "inputSchema": _eingang_query(),
        "outputSchema": _ausgang_query(),
        "readonly": True,
    },
    WERKZEUG_PRUEFE: {
        "name": WERKZEUG_PRUEFE,
        "description": (
            "Geometrie auf Massstab und Georeferenzierung prüfen, ohne einen Auftrag "
            "anzulegen. Fängt mm-als-m (Faktor 1000) und LV95-Koordinaten ab, bevor "
            "GPU-Zeit verbraucht wird. Rein rechnend."
        ),
        "inputSchema": _eingang_pruefe(),
        "outputSchema": _ausgang_pruefe(),
        "readonly": True,
    },
}


def werkzeug(name: str) -> dict:
    """Einen Werkzeugvertrag holen. Unbekannter Name ist ein Fehler, kein `None`."""
    try:
        return WERKZEUGE[name]
    except KeyError:
        raise KeyError(
            f"Unbekanntes Werkzeug {name!r}. Bekannt: {', '.join(sorted(WERKZEUGE))}"
        ) from None


def voller_name(name: str, servername: str = LANE) -> str:
    """Der Name, unter dem KosmoOrbit das Werkzeug anspricht: `mcp__<server>__<werkzeug>`."""
    return f"mcp__{servername}__{name}"


# ── Portierte Prüfung: würde KosmoOrbit unsere Werkzeuge verdrahten können? ───────────
# Nachbau der beiden Regeln aus `KosmoOrbit/src/lib/pipeline.ts:nodeReadinessIssues`.
# Nachbau statt Aufruf, weil jene Prüfung in TypeScript steckt und nur im Cockpit läuft.
# So lässt sich die Verdrahtbarkeit hier im Test belegen, statt sie zu behaupten.

#: Feldnamen-Synonyme über Lane-Grenzen (KosmoOrbit `FIELD_ALIAS_GROUPS`).
FELD_SYNONYME: tuple[tuple[str, ...], ...] = (
    ("parzelle_flaeche_m2", "landflaeche_m2", "site_area_m2"),
    ("az", "az_limit", "max_az"),
    ("total_hnf_m2", "programm_hnf_m2"),
)


def _mit_synonymen(namen) -> set[str]:
    ergebnis = set(namen)
    for gruppe in FELD_SYNONYME:
        if ergebnis & set(gruppe):
            ergebnis |= set(gruppe)
    return ergebnis


def schema_felder(schema) -> list[str]:
    """Die Feldnamen eines Schemas — leer, wenn keine aufzählbar sind."""
    if not isinstance(schema, dict):
        return []
    eigenschaften = schema.get("properties")
    return list(eigenschaften) if isinstance(eigenschaften, dict) else []


def pruefe_verdrahtbarkeit(erzeuger: dict, verbraucher: dict,
                           gesetzte_args: set[str] | None = None) -> list[dict]:
    """Meldet, was KosmoOrbits Entwurfszeit-Prüfung an einer Kante bemängeln würde.

    Args:
        erzeuger: Werkzeugvertrag des Vorgängers (mit `outputSchema`).
        verbraucher: unser Werkzeugvertrag (mit `inputSchema`).
        gesetzte_args: Felder, die im Knoten von Hand gesetzt sind.

    Returns:
        Liste von Befunden `{art, schwere, detail}`. **Leer heisst verdrahtbar.**
    """
    befunde: list[dict] = []
    verfuegbar = _mit_synonymen(
        set(gesetzte_args or ()) | set(schema_felder(erzeuger.get("outputSchema")))
    )

    pflicht = verbraucher.get("inputSchema", {}).get("required") or []
    fehlend = [f for f in pflicht if f not in verfuegbar]
    if fehlend:
        befunde.append({
            "art": "missing-required", "schwere": "error",
            "detail": f"Pflichtfeld(er) {', '.join(fehlend)} fehlt/fehlen: kein Vorgänger "
                      f"liefert sie, nicht als Arg gesetzt",
        })

    # Tote Kante: nur prüfbar, wenn BEIDE Seiten aufzählbare Felder haben.
    aus = set(schema_felder(erzeuger.get("outputSchema")))
    ein = set(schema_felder(verbraucher.get("inputSchema")))
    if aus and ein and not (aus & ein):
        befunde.append({
            "art": "dead-edge", "schwere": "warn",
            "detail": "Kante trägt nichts: keine gemeinsamen Feldnamen zwischen "
                      "outputSchema des Erzeugers und inputSchema des Verbrauchers",
        })
    return befunde


def pruefe_vertrag(vertrag: dict) -> list[str]:
    """Prüft einen eigenen Werkzeugvertrag gegen die Anforderungen des Ökosystems.

    Returns:
        Liste von Verstössen. **Leer heisst in Ordnung.**
    """
    maengel: list[str] = []
    for feld in ("name", "description", "inputSchema", "outputSchema"):
        if not vertrag.get(feld):
            maengel.append(f"{feld} fehlt — ohne das meldet pipelineReadiness tote Kanten")

    for feld in ("inputSchema", "outputSchema"):
        schema = vertrag.get(feld)
        if isinstance(schema, dict) and schema.get("additionalProperties") is False:
            maengel.append(
                f"{feld} setzt additionalProperties:false — mergeInputs reicht alle "
                f"Vorgängerfelder durch, das Schema würde daran scheitern"
            )
    if not schema_felder(vertrag.get("outputSchema")):
        maengel.append(
            "outputSchema hat keine aufzählbaren properties — nachgelagerte Knoten "
            "können dann kein Pflichtfeld aus uns beziehen"
        )
    return maengel
