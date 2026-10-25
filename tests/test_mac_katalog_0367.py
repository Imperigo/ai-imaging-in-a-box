"""Mac-Test 0.3.67 (25.10.2026, Mappe «Demohaus Test»): der Werkzeugkatalog, den die Mac-App Claude nennt.

Protokoll 74 §293a. Drei Funde:

A. **``freies_bild`` fehlte am Mac** — weder im Schema von ``vis_render`` noch in ``graph_lesen katalog:true``.
   Woher der Katalog am Mac kommt (am Code geprüft): aus dem **Bau der Knotenansicht im App-Bündel**. ``ipad.yml``
   legt ``kosmovis/apps/visbox-knoten/dist`` nach ``Visbox.app/Contents/Resources/Knoten``; ``Kizentrale`` nennt
   Claude die Werkzeuge der offenen Seite (``visboxKi.werkzeuge()``, dieselben Bausteine im selben Bau) und vorher
   ``Knoten/ki-werkzeugliste.json``. Der Heim-PC liefert ihn seit dem 20.10.2026 («Visbox eigenständig», Schritt 1) nicht
   mehr; ``src/aiimaging/mcp_schemas.py`` kennt die Vis-Werkzeuge nicht. Ein neuer Katalog braucht darum einen
   neuen Bau der Mac-App (jede Freigabe baut sie). Der Katalog von ``graph_lesen`` nannte nur Ports, keine
   Parameter — jetzt ``parameter`` je Knotentyp (``knotenKatalog``), im Bau als ``knotenkatalog`` mitgeschrieben.
B. **Der Satz zu «Voll»**: Eine Claude-Sitzung fragte in «Voll» nach, weil die Beschreibung von einer Karte sprach.
C. **``vis_grundlage`` ohne neuen Lauf** sagte trotzdem «Grundlage rendern … (rechnet ohne Freigabe,
   Vollautomatik)» — jetzt «Grundlage vorhanden, nicht neu gerechnet: gl-…».

Gelesen wird genau die Datei, die ins Mac-Bündel geht. Swift wird hier nicht gebaut (Text).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
DIST = WURZEL / "kosmovis" / "apps" / "visbox-knoten" / "dist"
LISTE = DIST / "ki-werkzeugliste.json"
KERN = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern"

VOLL_SATZ = ("Im Modus Voll: rechnet ohne Karte und ohne Freigabe (höchstens 5 je Stunde; Modelle mit offener "
             "Lizenz bleiben eine Karte — Ausnahme: Bild aus Skizze mit Qwen-Image, Entscheid 153).")
KARTE_SATZ = "Im Modus Karte (und Coop): eine Karte, der Architekt gibt frei."


def _liste() -> dict:
    return json.loads(LISTE.read_text(encoding="utf-8"))


def _werkzeug(name: str) -> dict:
    return next(w for w in _liste()["werkzeuge"] if w["name"] == name)


def _bau_js() -> str:
    index = (DIST / "index.html").read_text(encoding="utf-8")
    teil = re.search(r'src="\./assets/(index-[A-Za-z0-9_-]+\.js)"', index)
    assert teil, "index.html nennt kein Skript"
    return (DIST / "assets" / teil.group(1)).read_text(encoding="utf-8")


# ================================================================ woher der Mac-Katalog kommt

def test_der_mac_katalog_ist_der_bau_im_buendel():
    ci = (WURZEL / ".github" / "workflows" / "ipad.yml").read_text(encoding="utf-8")
    assert 'ditto ../../kosmovis/apps/visbox-knoten/dist "$BUENDEL/Contents/Resources/Knoten"' in ci
    # Jeder neue Bau der Knotenansicht baut die Mac-App neu (Pfadfilter).
    assert ci.count('"kosmovis/apps/visbox-knoten/dist/**"') >= 2
    assert 'ordnerImBuendel = "Knoten"' in (KERN / "Knotenwege.swift").read_text(encoding="utf-8")
    assert 'listendatei = "ki-werkzeugliste.json"' in (KERN / "Kibedienung.swift").read_text(encoding="utf-8")
    zentrale = (WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac" / "Claude" / "Kizentrale.swift").read_text(
        encoding="utf-8")
    assert "(liveWerkzeuge ?? gebuendelt) + Macwerkzeuge.alle" in zentrale
    assert _liste()["format"] == "visbox.ki-werkzeugliste/v1"


# ================================================================ A: freies_bild im Katalog

def test_freies_bild_an_vis_render_und_vis_varianten():
    for name in ("vis_render", "vis_varianten"):
        feld = _werkzeug(name)["inputSchema"]["properties"].get("freies_bild")
        assert feld, f"{name}: freies_bild fehlt im Katalog des Mac-Bündels"
        assert feld["type"] == "boolean"
        assert "ohne Grundbild" in feld["description"]
    assert "standpunkte" in _werkzeug("vis_varianten")["inputSchema"]["properties"]


def test_graph_lesen_katalog_nennt_freies_bild_als_parameter():
    assert "Parametern" in _werkzeug("graph_lesen")["inputSchema"]["properties"]["katalog"]["description"]
    katalog = {t["typ"]: t for t in _liste()["knotenkatalog"]}
    for typ in ("render", "varianten"):
        assert "freiesBild:boolean" in katalog[typ]["parameter"], typ
        assert "ohne das Grundbild" in katalog[typ]["parameterHilfe"]["freiesBild"]
    assert "preset:string" in katalog["stimmung"]["parameter"]


def test_die_seite_im_buendel_traegt_dasselbe():
    js = _bau_js()
    assert "parameterHilfe" in js
    assert "Ausnahme: Bild aus Skizze mit Qwen-Image, Entscheid 153" in js
    assert "Grundlage vorhanden, nicht neu gerechnet" in js


# ================================================================ B: der Satz je Modus

def test_bildwerkzeuge_sagen_karte_und_voll_je_modus():
    for name in ("vis_render", "vis_varianten", "vis_grundlage"):
        d = _werkzeug(name)["description"]
        assert KARTE_SATZ in d, name
        assert VOLL_SATZ in d, name
        assert "Freigeben selbst ist kein Werkzeug" in d
        assert "Immer eine Karte" not in d
        assert "startet erst" not in d
    # Löschen bleibt immer eine Karte.
    assert "Immer eine Karte, in jedem Modus." in _werkzeug("vis_nodeLoeschen")["description"]


def test_spielregel_der_mac_app_nennt_die_ausnahme():
    kern = (KERN / "Mcpkern.swift").read_text(encoding="utf-8")
    assert "einem Bildmodell mit offener Lizenz (Ausnahme: Bild aus Skizze mit Qwen-Image, Entscheid 153)" in kern


# ================================================================ C: vis_grundlage ohne neuen Lauf

def test_vis_grundlage_sagt_nicht_neu_gerechnet():
    quelle = (WURZEL / "kosmovis" / "apps" / "visbox-knoten" / "src" / "grundlage-werkzeug.ts").read_text(
        encoding="utf-8")
    assert "const da = vorhandeneGrundlage(doc, p.graphId, p.nodeId);" in quelle
    assert "return da ? grundlageVorhandenZeile(da) : grundlageZeile();" in quelle
    werkzeuge = (WURZEL / "kosmovis" / "apps" / "kosmo-orbit" / "src" / "modules" / "vis" / "ki-werkzeuge.ts")
    text = werkzeuge.read_text(encoding="utf-8")
    assert "export const NICHT_NEU_GERECHNET = 'Grundlage vorhanden, nicht neu gerechnet';" in text
    assert "ohneLauf ? VOLL_OHNE_LAUF_KOPF : VOLL_RENDER_KOPF" in text
