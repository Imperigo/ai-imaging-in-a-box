"""Der MCP-Server — dünne Übersetzungsschicht, optionaler Zusatz.

Warum dieses Modul so wenig tut
-------------------------------
Regel 4 verlangt, dass jede Fähigkeit aus Python heraus nutzbar ist, ohne dass eine
Oberfläche läuft. Läge hier Logik, wäre die Bibliothek ohne Cockpit unvollständig — die
Regel wäre verletzt, nur unauffälliger als bei einer GUI.

Dieses Modul übersetzt daher ausschliesslich: MCP-Aufruf hinein, Bibliotheksaufruf
hinaus, Ergebnis als `structuredContent` zurück. Wer es löscht, verliert die Anbindung an
KosmoOrbit — sonst nichts.

Abhängigkeit
------------
Das MCP-SDK ist **MIT**-lizenziert (geprüft 2026-08-18 gegen die PyPI-Metadaten von
`mcp` 2.0.0) und damit unter Regel 1 zulässig. Es bringt allerdings 19 transitive
Abhängigkeiten mit, die **nicht** einzeln geprüft sind — deshalb ist es ein optionaler
Zusatz (`pip install aiimaging[mcp]`) und keine Kernabhängigkeit. Der Import erfolgt
absichtlich erst in `baue_server()`, damit der blosse Import dieses Moduls nichts
nachzieht.

Registrierung bei Kosmo
-----------------------
Belegt in Phase 0 aus KosmoDraws `register_in_odysseus.sh`:

    POST /api/auth/login          → Session-Cookie
    POST /api/mcp/servers         name, transport=stdio, command, args, env

Der Server läuft über **stdio**; Odysseus startet ihn. Schreibziele müssen unter `$HOME`
oder `/tmp` liegen (Pfad-Sandbox des Ökosystems).

    python3 -m aiimaging.mcp_server
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from aiimaging import werkzeuge as _w
from aiimaging.mcp_schemas import LANE, WERKZEUGE


def rufe_werkzeug(name: str, argumente: dict) -> dict:
    """Ein Werkzeug bei Namen aufrufen und `structuredContent` zurückgeben.

    Diese Funktion ist die eigentliche Naht — und sie ist **SDK-frei**, damit sie ohne
    installiertes MCP-Paket getestet werden kann. Der Server unten ist nur noch
    Verkabelung.

    Fehler werden als Ergebnis gemeldet, nicht als Ausnahme nach aussen geworfen: Ein
    Werkzeugaufruf, der im Cockpit einen Traceback erzeugt, sagt dem Benutzer nichts.
    """
    try:
        return _w.RUFTABELLE[name](argumente or {})
    except KeyError:
        return {"error": f"Unbekanntes Werkzeug {name!r}. "
                         f"Bekannt: {', '.join(sorted(WERKZEUGE))}"}
    except Exception as e:                       # noqa: BLE001 — bewusst breit, siehe Docstring
        return {"error": f"{type(e).__name__}: {e}"}


def baue_server():
    """Den MCP-Server bauen. Importiert das SDK erst hier — siehe Modul-Docstring."""
    try:
        from mcp.server import Server                     # noqa: PLC0415
        from mcp.types import TextContent, Tool           # noqa: PLC0415
    except ImportError as e:
        raise ImportError(
            "Das MCP-SDK fehlt. Es ist ein optionaler Zusatz, kein Kernbestandteil:\n"
            "    pip install 'aiimaging[mcp]'\n"
            "Die Bibliothek selbst läuft ohne — nur die Anbindung an KosmoOrbit nicht."
        ) from e

    server = Server(LANE)

    @server.list_tools()
    async def _liste():
        return [
            Tool(name=v["name"], description=v["description"],
                 inputSchema=v["inputSchema"], outputSchema=v["outputSchema"])
            for v in WERKZEUGE.values()
        ]

    @server.call_tool()
    async def _rufe(name: str, arguments: dict):
        ergebnis = rufe_werkzeug(name, arguments)
        # Beides zurückgeben: `structuredContent` für den Datenfluss der Pipeline,
        # Text für die Anzeige. KosmoOrbit liest das strukturierte Feld.
        return [TextContent(type="text", text=json.dumps(ergebnis, ensure_ascii=False))], ergebnis

    return server


def main() -> int:
    """Über stdio laufen — so startet Odysseus den Server."""
    import anyio                                          # noqa: PLC0415
    from mcp.server.stdio import stdio_server             # noqa: PLC0415

    server = baue_server()

    async def _lauf():
        async with stdio_server() as (lesen, schreiben):
            await server.run(lesen, schreiben, server.create_initialization_options())

    anyio.run(_lauf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
