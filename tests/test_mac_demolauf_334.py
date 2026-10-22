"""Mac-Demolauf «Skizze vom iPad bis zum Bild» (Visbox 0.3.34, 22.10.2026) — Funde E, A–D, F15.

Die Verhaltensproben liegen dort, wo das Verhalten liegt: vitest in ``kosmovis/`` (Knotenansicht),
XCTest in ``ipad/VisboxKern`` (Mac-Kern, über die Mac-CI). Hier steht, was der Heim-PC dazu tut, und
dass die Nähte an ihrem Platz bleiben (eine Datei, die still zurückgedreht wird, macht diese Probe rot).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from aiimaging import bruecke, knotenweg

REPO = Path(__file__).resolve().parents[1]
KENNUNG = "vis-1761120000-334aaa"


def _szene(skizze: str | None = None) -> dict:
    s = {"schema": "kosmovis.render-scene/v1", "cameras": "auto",
         "render": {"resolution": [1600, 1000], "samples": 128, "faithful": 0.8},
         "style": {"mode": "none", "prompt": "Wohnhaus"},
         "vis": {"skip": False, "backbone": "z-image-turbo", "upscale": False},
         "geometry": {"format": "glb"}, "out": ""}
    if skizze:
        s["skizze"] = {"quelle": "mappe", "name": skizze}
    return s


def _lies(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------- Fund E (zweite Hälfte)

def test_jeder_auftrag_wartet_am_heim_pc_auf_freigeben(tmp_path):
    """Nach «Anwenden» einer Render-Karte geht der Auftrag an die Brücke — und wartet dort auf den
    Klick «Freigeben» des Architekten. Die Grafikkarte startet nie ohne ihn."""
    zettel = knotenweg.lege_an(tmp_path / "ablage", _szene(), b"glTF", "model.glb", kennung=KENNUNG)
    assert zettel["status"] == bruecke.STATUS_AWAITING
    assert "Freigeben" in zettel[bruecke.FELD_MELDUNG]


def test_die_maus_der_ki_darf_die_erzaehlzeile_nicht_druecken():
    maus = _lies("kosmovis/apps/kosmo-orbit/src/state/kosmo-maus.ts")
    start = maus.index("export const KARTEN_SELEKTOR")
    assert '[data-testid="erzaehl-zeile"]' in maus[start:start + 600]


# ---------------------------------------------------------------- Fund D / C (Ursache)

def test_eine_skizze_aus_der_mappe_am_mac_ohne_zwilling_wird_mit_satz_abgewiesen(tmp_path):
    """Die Skizze vom iPad liegt in der Mappe am Mac (``ipad/…``). Hat die Mappe am Heim-PC keinen
    Zwilling, kommt der Auftrag ohne Mappe an — 400 mit Satz. Bis zum Fix stand am Knoten nur
    «Bridge antwortet mit: 400», jetzt der Satz (``BRUECKE_SATZ_STATUS`` in ``mappe.ts``)."""
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path / "ablage", _szene("ipad/skizze-20261022-101500.png"), b"glTF",
                          "model.glb", kennung=KENNUNG, mappe="Demohaus Test", mappe_pfad=None)
    assert fehler.value.code == 400
    assert "nur aus einer offenen Mappe" in str(fehler.value)


def test_die_seite_zeigt_den_satz_einer_400_und_reicht_bei_409_das_modell_nach():
    mappe = _lies("kosmovis/apps/visbox-knoten/src/mappe.ts")
    assert "export const BRUECKE_SATZ_STATUS: readonly number[] = [400, 502, 503];" in mappe


def test_kein_token_satz_im_eigenen_adressschema():
    jobs = _lies("kosmovis/apps/kosmo-orbit/src/modules/vis/vis-jobs.ts")
    assert "adresse.protocol !== 'http:' && adresse.protocol !== 'https:'" in jobs


# ---------------------------------------------------------------- Fund B

def test_mit_skizze_heisst_der_knopf_bild_aus_skizze_erzeugen():
    grundlage = _lies("kosmovis/apps/kosmo-orbit/src/modules/vis/grundlage.ts")
    assert "export const BILD_AUS_SKIZZE_KNOPF = 'Bild aus Skizze erzeugen';" in grundlage
    jobs = _lies("kosmovis/apps/kosmo-orbit/src/modules/vis/vis-jobs.ts")
    assert "const bildAusSkizze = opts?.stufe === 'variante' && !!auftrag.skizze" in jobs


# ---------------------------------------------------------------- Fund A und F15 (Mac-Kern)

def test_die_mac_werkzeuge_lesen_die_mappe_der_knotenansicht():
    zentrale = _lies("ipad/VisboxMac/Sources/VisboxMac/Claude/Kizentrale.swift")
    assert "func ausDerMacMappe(" in zentrale
    assert "setzeKartenmappe(mappe, ordner: quelle.mappe)" in _lies(
        "ipad/VisboxMac/Sources/VisboxMac/Start/Arbeitsansicht.swift")


def test_kartennummern_nur_fuer_vorschlaege():
    kern = _lies("ipad/Visbox.swiftpm/Kern/Mcpkern.swift")
    assert 'public static let lesevorsatz = "L-"' in kern
    assert "public static func keinVorschlag(" in kern
