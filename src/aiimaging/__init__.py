"""AI Imaging in a Box — geometrie-treue KI-Architektur-Visualisierung.

Der Kern ist eine Bibliothek: jede Fähigkeit ist aus Python heraus nutzbar, ohne dass
eine Oberfläche läuft (Regel 4). Die MCP-Schicht darüber ist eine dünne Übersetzung, kein
Bestandteil des Kerns — wer sie weglässt, verliert die Anbindung an KosmoOrbit und sonst
nichts.

Dieses Paket enthält **kein** ``import bpy`` und **kein** ``import ifcopenshell``. Beide
liegen jenseits einer Prozessgrenze und werden als eigenständige Programme aufgerufen
(Regel 2 und die LGPL-Präzisierung zu Regel 1). Die dafür bestimmten Skripte liegen in
``aiimaging.runners`` — sie werden von *anderen* Interpretern ausgeführt, nie von diesem
importiert.

Aufbau
------
``contracts``    Verträge, insbesondere die Up-Achsen-Regel
``herkunft``     Connector-Schicht: was eine Datei selbst über Einheit und Up-Achse sagt
``lizenzquelle`` eine Vokabel für die Herkunft einer Lizenzangabe, für alle Registries
``lora``         LoRA-Stiltraining als Subprozess — wo Regel 1 und Regel 3 sich treffen
``kosmo_naht``   Übersetzung unserer Felder in die Protokollnamen des Ökosystems
``stilstudie``   der Boden des Einbetters — wovon die Stil-Schwelle abhängt
``schwellenstudie`` Kalibrierung der Geometrie-Schwelle: Störung, Kurve, Trennschärfe
``paarschwellen`` aus benannten Fällen eine Schwelle ableiten — mit BEIDEN Fehlerzahlen
``seams``        die Prozessgrenzen zu IfcOpenShell und Blender — dort auch
                 ``ifc_raeume``: Räume aus einer IFC als schlichte Daten, die
                 Voraussetzung für alles Innere
``torwaechter``  Massstabs- und Georeferenzprüfung vor teurer GPU-Zeit
``graph``        der innere Knotengraph der Bildkette
``kette``        die Bildkette ALS Graph — mit Zwischenspeicher über Inhalts-Hashes
``jobs``         Auftragsverwaltung mit Freigabe (Freeze-Schutz)
``werkzeuge``    was die MCP-Naht anbietet — gewöhnliche Bibliotheksaufrufe
``auftrag``      Aufträge an die HomeStation, über das Repo als Übergabeort
``auftragspost`` ein Auftrag als EIN Block — für Adressaten ohne unser Repo
``geometrie_qa`` die Geometrie-Treue-Metrik — der wissenschaftliche Kern
``stil_qa``      das zweite Gate: Stil-Ähnlichkeit
``einbau``       Was gebaut ist, was davon in der Software steht, und wer es einbaut
``einbetter``    Registry der Einbettungsmodelle samt Lizenz (DINOv3 ausgeschlossen)
``gate``         das Doppel-Gate — bestanden nur, wenn beide bestehen
``backbone``     Registry der Bildmodelle samt Lizenz (Regel 1 in ausführbarer Form)
``render``       die Bildmodell-Stufe über `diffusers`, Modell injizierbar
``bildlesen``    EXR und PNG → Zahlen für die Metrik; stdlib, Blender nur als Rückfall
``bildschreiben`` die Gegenseite: Zahlen → PNG, und die Normalisierung der Tiefenkarte
``tiefenschaetzer`` die **Ist-Seite** der QA: Tiefe aus dem erzeugten Bild schätzen
``mcp_schemas``  die Werkzeugverträge als reine Daten
``mcp_server``   optionaler Zusatz, braucht das MIT-lizenzierte MCP-SDK
"""
__version__ = "0.0.2"

from aiimaging import (  # noqa: F401
    auftrag, auftragspost, backbone, bildlesen, bildschreiben, contracts,
    einbau, einbetter, gate, geometrie_qa,
    graph, herkunft, jobs, kette, konversionstreue, kosmo_naht, lizenzquelle, lora,
    mcp_schemas, paarschwellen, render, schwellenstudie, seams, stil_qa,
    stilstudie, tiefenschaetzer,
    torwaechter, werkzeuge,
)
from aiimaging.contracts import (  # noqa: F401
    ContractError,
    LANE_FIELDS,
    SCHEMA_ID,
    load_render_scene,
    needs_rotation,
    normalize_up_axis,
    validate_render_scene,
)
from aiimaging.seams import (  # noqa: F401
    SeamError, glb_zu_tiefenkarte, ifc_raeume, ifc_zu_glb,
)
from aiimaging.gate import gesamturteil  # noqa: F401
from aiimaging.geometrie_qa import geometrie_gate, geometrie_score  # noqa: F401
from aiimaging.stil_qa import stil_gate, stil_score  # noqa: F401
from aiimaging.werkzeuge import check_geometry, enqueue_render, query_render  # noqa: F401
