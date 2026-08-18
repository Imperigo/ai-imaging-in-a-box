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
``seams``        die Prozessgrenzen zu IfcOpenShell und Blender
``torwaechter``  Massstabs- und Georeferenzprüfung vor teurer GPU-Zeit
``graph``        der innere Knotengraph der Bildkette
``jobs``         Auftragsverwaltung mit Freigabe (Freeze-Schutz)
``werkzeuge``    was die MCP-Naht anbietet — gewöhnliche Bibliotheksaufrufe
``auftrag``      Aufträge an die HomeStation, über das Repo als Übergabeort
``geometrie_qa`` die Geometrie-Treue-Metrik — der wissenschaftliche Kern
``stil_qa``      das zweite Gate: Stil-Ähnlichkeit
``einbetter``    Registry der Einbettungsmodelle samt Lizenz (DINOv3 ausgeschlossen)
``gate``         das Doppel-Gate — bestanden nur, wenn beide bestehen
``backbone``     Registry der Bildmodelle samt Lizenz (Regel 1 in ausführbarer Form)
``mcp_schemas``  die Werkzeugverträge als reine Daten
``mcp_server``   optionaler Zusatz, braucht das MIT-lizenzierte MCP-SDK
"""
__version__ = "0.0.2"

from aiimaging import (  # noqa: F401
    auftrag, backbone, contracts, einbetter, gate, geometrie_qa, graph, jobs,
    mcp_schemas, seams, stil_qa, torwaechter, werkzeuge,
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
from aiimaging.seams import SeamError, glb_zu_tiefenkarte, ifc_zu_glb  # noqa: F401
from aiimaging.gate import gesamturteil  # noqa: F401
from aiimaging.geometrie_qa import geometrie_gate, geometrie_score  # noqa: F401
from aiimaging.stil_qa import stil_gate, stil_score  # noqa: F401
from aiimaging.werkzeuge import check_geometry, enqueue_render, query_render  # noqa: F401
