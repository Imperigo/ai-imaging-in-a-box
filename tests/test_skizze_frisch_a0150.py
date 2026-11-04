"""«Bild aus Skizze» rechnet vom frischen Grundbild, unvollständige Aufträge enden sofort (A0150).

Befund Geräteprobe R98: Die Bestellung mit ``skizze.grundlage: "frisch"`` wurde angenommen, die
frische Grundlage entstand, dann endete der Lauf mit «MASSTREUE … NICHT angekommen». Die Proben von
A0094 waren grün, weil ihre Attrappe den Rechenschritt ganz ersetzt. Darum läuft hier das echte
``render.rendere``; ersetzt ist erst der Rechner selbst, und der verhält sich wie Z-Image am Gerät:
Ein ``image`` nimmt die Pipeline nicht, nur der eigene Start (``bild_und_tiefe``) kommt an.

Ohne GPU, ohne Blender (Regel 3).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import abholer, bildlesen, bruecke, knotenweg, kosmo_szene, render

from test_skizze_frisch_a0094 import (GRUEN, KENNUNG, KAMERA, ROT, _attrappen, _bestellen_abholen,
                                      _glb_bytes, _szene, mappe)  # noqa: F401 — die Fixture


def _wie_z_image(gesehen: list):
    """Der Rand des Rechners: wie die Z-Image-Pipeline am Gerät (Geräteprobe R98)."""
    def modell(parameter):
        gesehen.append({"modus": parameter["modus"],
                        "staerke": parameter.get("bildeingang_staerke"),
                        "start": bildlesen.lies_png_farben(parameter["beauty_png"])[0]})
        ziel = parameter["ausgabe_png"]
        Path(ziel).write_bytes(Path(parameter["depth_png"]).read_bytes())
        angekommen = parameter["modus"] == render.MODUS_BILD_UND_TIEFE
        return {"bild_png": ziel, "hinweise": (), "modus_bestellt": parameter["modus"],
                "modus_gerechnet": parameter["modus"] if angekommen else render.MODUS_TXT2IMG}
    return modell


def _abholen_mit_echtem_render(tmp_path, mappe_, szene):
    ablage = tmp_path / "ablage"
    zettel = knotenweg.lege_an(ablage, szene, _glb_bytes(), "model.glb", kennung=KENNUNG,
                               mappe=mappe_.name, mappe_pfad=mappe_)
    knotenweg.freigeben(ablage, KENNUNG, zettel["approval_token"])
    gesehen: list = []
    _, naehte = _attrappen()
    naehte["_rendere"] = lambda a, **kw: render.rendere(a, modell=_wie_z_image(gesehen))
    antwort = abholer.hole_einen(ablage / KENNUNG, verarbeite=abholer.verarbeiter(**naehte),
                                 darf_rechnen=lambda: (True, "frei"))
    datei = ablage / KENNUNG / bruecke.DATEI_ERGEBNIS
    ergebnis = json.loads(datei.read_text("utf-8")) if datei.is_file() else {}
    return antwort, gesehen, ergebnis


def test_das_frische_grundbild_kommt_am_rand_des_rechners_an(tmp_path, mappe):
    """Satz 2: auf main rot. Das Startbild erreicht das Modell über den Weg, den es nimmt."""
    antwort, gesehen, ergebnis = _abholen_mit_echtem_render(
        tmp_path, mappe, _szene(anweisung="a wooden canopy"))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort.get("grund")
    assert gesehen and gesehen[0]["modus"] == render.MODUS_BILD_UND_TIEFE
    # Das Grundbild ist das Beauty (GRÜN) mit der Skizze darauf (ROT), nicht die alte Unterlage.
    start = gesehen[0]["start"]
    assert start[1 * 4 + 1] == ROT and GRUEN in start
    assert len(ergebnis["images"]) == 1


def test_die_staerke_ist_die_der_skizze_aus_dem_register(tmp_path, mappe):
    """E154: Skizzen-Vorgabe Z-Image Turbo 0,55, gelesen aus dem Register, nicht neu festgelegt."""
    gelesen = kosmo_szene.lies_szene(_szene(anweisung="x") | {
        "geometry": {"path": "m.glb", "format": "glb"}})
    assert gelesen["bildeingang"] == 0.55
    herkunft = gelesen["messschalter"]["bildeingang"]["herkunft"]
    assert herkunft == kosmo_szene.HERKUNFT_VORGABE_SKIZZE
    _, gesehen, ergebnis = _abholen_mit_echtem_render(tmp_path, mappe, _szene(anweisung="x"))
    assert gesehen[0]["staerke"] == 0.55
    assert "Vorgabe fuer eine Skizze" in " ".join(ergebnis["qa"]["verdict"]["hinweise"])


def test_eine_bestellte_staerke_gewinnt():
    gelesen = kosmo_szene.lies_szene(_szene(anweisung="x", vis={"bildeingang": 0.7}) | {
        "geometry": {"path": "m.glb", "format": "glb"}})
    assert gelesen["bildeingang"] == 0.7


def test_das_situationsmodell_senkt_die_skizzen_staerke_nicht():
    """Die Senkung auf 0,5 (Entscheid 149, ergänzt) gilt für Varianten, nicht für E154."""
    gelesen = kosmo_szene.lies_szene(_szene(anweisung="x") | {
        "geometry": {"path": "m.glb", "format": "glb"}})
    assert kosmo_szene.bildeingang_fuer_situationsmodell(
        gelesen, {"ja": True, "grund": "Anlage"})["bildeingang"] == 0.55


def test_die_skizze_auf_ihrer_unterlage_bleibt_wie_sie_war():
    """Ohne «frisch» bleibt der Visbox-Skizzenweg: dort setzt der Nachrender die Stärke."""
    gelesen = kosmo_szene.lies_szene(_szene(grundlage=None, kameras="auto", anweisung="x") | {
        "geometry": {"path": "m.glb", "format": "glb"}})
    assert gelesen["bildeingang"] is None


def _bestellen(tmp_path, mappe_, szene):
    ablage = tmp_path / "ablage"
    zettel = knotenweg.lege_an(ablage, szene, _glb_bytes(), "model.glb", kennung=KENNUNG,
                               mappe=mappe_.name, mappe_pfad=mappe_)
    knotenweg.freigeben(ablage, KENNUNG, zettel["approval_token"])
    _, naehte = _attrappen()
    antwort = abholer.hole_einen(ablage / KENNUNG, verarbeite=abholer.verarbeiter(**naehte),
                                 darf_rechnen=lambda: (True, "frei"))
    zettel = json.loads((ablage / KENNUNG / "job.json").read_text("utf-8"))
    return antwort, zettel


def test_ein_auftrag_ohne_up_axis_endet_sofort_mit_satz(tmp_path, mappe):
    """Satz 3: rot vor grün. Er blieb auf «queued» und wartete auf nichts."""
    kamera = {k: v for k, v in KAMERA.items() if k != "up_axis"}
    antwort, zettel = _bestellen(tmp_path, mappe, _szene(kameras=[kamera], anweisung="x"))
    assert antwort["tat"] == abholer.TAT_FEHLER, antwort
    assert zettel["status"] == "error"
    assert "up_axis" in zettel["error"]


def test_ohne_skizze_bleibt_der_auftrag_ohne_up_axis_liegen():
    """Der Weg vom 23.09.2026 (test_ifc_bestellung) bleibt: nur «frisch» endet sofort."""
    kamera = {k: v for k, v in KAMERA.items() if k != "up_axis"}
    szene = _szene(kameras=[kamera], anweisung="x") | {
        "geometry": {"path": "m.glb", "format": "glb"}}
    ohne = {k: v for k, v in szene.items() if k != "skizze"}
    with pytest.raises(kosmo_szene.KameraOhneHochachse) as fehler:
        kosmo_szene.lies_szene(ohne)
    assert fehler.value.endgueltig is False


def test_cameras_auto_bei_frisch_endet_sofort_mit_satz(tmp_path, mappe):
    antwort, zettel = _bestellen(tmp_path, mappe, _szene(kameras="auto", anweisung="x"))
    assert antwort["tat"] == abholer.TAT_FEHLER, antwort
    assert zettel["status"] == "error"
    assert kosmo_szene.SATZ_SKIZZE_FRISCH_OHNE_KAMERA in zettel["error"]


def test_eine_falsche_achse_bleibt_wie_sie_war():
    """Nur das fehlende Pflichtfeld ist neu; ein falscher Wert bleibt die alte Ausnahme."""
    with pytest.raises(kosmo_szene.SzenenError) as fehler:
        kosmo_szene._hochachse("x")
    assert not isinstance(fehler.value, kosmo_szene.KameraOhneHochachse)
