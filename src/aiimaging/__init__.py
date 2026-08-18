"""AI Imaging in a Box — geometrie-treue KI-Architektur-Visualisierung.

Der Kern ist eine Bibliothek: jede Fähigkeit ist aus Python heraus nutzbar, ohne dass
eine Oberfläche läuft (Regel 4).

Dieses Paket enthält **kein** ``import bpy`` und **kein** ``import ifcopenshell``. Beide
liegen jenseits einer Prozessgrenze und werden als eigenständige Programme aufgerufen
(Regel 2 und die LGPL-Präzisierung zu Regel 1). Die dafür bestimmten Skripte liegen in
``aiimaging.runners`` — sie werden von *anderen* Interpretern ausgeführt, nie von diesem
importiert.
"""
__version__ = "0.0.1"

from aiimaging.contracts import (  # noqa: F401
    ContractError,
    LANE_FIELDS,
    SCHEMA_ID,
    load_render_scene,
    needs_rotation,
    normalize_up_axis,
    validate_render_scene,
)
