#!/usr/bin/env python3
"""Startpunkt für Odysseus — dünner Vorspann vor `aiimaging.mcp_server`.

Warum diese Datei überhaupt existiert
-------------------------------------
Odysseus startet MCP-Server über stdio mit `command` + `args` aus seiner Runtime-DB.
Der naheliegende Weg — die venv-Python mit `-m aiimaging.mcp_server` — wurde am
18.08.2026 registriert und scheiterte reproduzierbar mit `Connection closed`,
`exit_code: 1`, **obwohl derselbe Aufruf von Hand unter jeder geprüften Bedingung
sauber lief** (leere Umgebung, fremdes Arbeitsverzeichnis, offener und geschlossener
stdin, jeweils Rückgabe 0).

Die einzige belegte Abweichung zum funktionierenden `KosmoDraw`-Server war die Form:
dort ein **direkter Skriptpfad** unter `/usr/bin/python3`, hier ein `-m`-Aufruf unter
einer venv. Diese Datei stellt die bewährte Form her, statt die Ursache zu erraten.

Das systemweite Python trägt `mcp` 1.27.2 und lädt dieses Paket über den Vorspann
unten; die venv trug 1.29.0. Welche der beiden Abweichungen — Aufrufform oder
SDK-Fassung — den Ausschlag gab, ist damit **nicht** entschieden; belegt ist nur, dass
diese Kombination trägt. Wer es genauer wissen will, tauscht eine Grösse allein.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from mcp.server.stdio import stdio_server  # noqa: E402
from aiimaging.mcp_server import baue_server  # noqa: E402


async def _lauf() -> None:
    server = baue_server()
    async with stdio_server() as (lesen, schreiben):
        await server.run(lesen, schreiben, server.create_initialization_options())


def main() -> int:
    """Wie ``aiimaging.mcp_server.main`` — aber unter ``asyncio`` statt ``anyio``.

    Der Unterschied ist gemessen, nicht vermutet (18.08.2026): Mit ``anyio.run`` meldete
    Odysseus zuerst *«MCP server connected: aiimaging — 3 tools via stdio»* und neun
    Millisekunden später *«tool call failed: Connection closed»*, dazu in seinem eigenen
    Protokoll *«Error closing MCP server: Attempted to exit cancel scope in a different
    task than it was entered in»* — ein anyio-eigener Fehler. Derselbe Aufruf lief von
    Hand über stdio fehlerfrei durch, inklusive vollständiger Werkzeugantwort.

    ``KosmoDraw``, der einzige Server, dessen Werkzeuge in dieser Odysseus-Fassung
    nachweislich antworten, startet mit ``asyncio.run``. Diese Datei stellt dieselbe
    Bedingung her — sie ändert genau eine Grösse.
    """
    asyncio.run(_lauf())
    return 0


if __name__ == "__main__":
    sys.exit(main())
