"""Was jeden Auftrag gleich trifft, steht nicht unter seinen Warnungen.

**Der Anlass ist eine Zählung, und sie ist schärfer als der gemeldete Befund**
(HomeStation `auf-vis-20260824-12`, nachgemessen am 26.08.2026): `tools/abholen.py`
zeigte `warnungen[:3]`. Genau **drei** Warnungen aus `kosmo_szene.lies_szene` feuern bei
einem gewöhnlichen Auftrag:

===================================  =========================================
Bildmasse 1600×1000 → 1600×992       die Vertragsvorgabe ist nie ein Vielfaches von 16
``faithful`` → ``controlnet_staerke``  steht ohne jede Bedingung da
keine Sonnenangabe                   die Vertragsvorgabe hat keine
===================================  =========================================

Sie füllten also **alle drei Plätze**. Eine echte, auftragsspezifische Warnung, die im
Code später steht, war damit unsichtbar. Die immer feuernde Warnung verdrängt nicht nur
sich selbst — sie **verdeckt die anderen**. Der Deckel hat nicht die Geschwätzigkeit
begrenzt, sondern die Auskunft gelöscht.

Dieselbe Trennung wie in `abholer._kompositionszeilen`: Was alle betrifft, steht einmal
da. Und es verschwindet nicht — es steht nur woanders.
"""
from __future__ import annotations

import pytest

from aiimaging import bruecke, kosmo_szene
from aiimaging.kosmo_szene import DURCHGEREICHT, STEHENGEBLIEBEN

BESTELLUNG = {"geometry": {"path": "/irgendwo/bau.glb", "format": "glb"}}


def _szene(**fremd):
    return kosmo_szene.lies_szene({**BESTELLUNG, **fremd})


# ======================================================================================
# Die Trennung selbst
# ======================================================================================

def test_ein_gewoehnlicher_auftrag_hat_keine_eigene_warnung():
    """**Der Kern.** Vorher waren es drei, und sie waren alle drei angezeigten Zeilen."""
    szene = _szene()

    assert szene["warnungen"] == ()
    assert len(szene["vertragsvorgaben"]) == 3


def test_die_drei_vorgaben_gehen_nicht_verloren_sondern_stehen_woanders():
    """Die Gegenprobe zur Trennung. Wer eine Dauerwarnung einfach löscht, hat sie nicht
    eingeordnet, sondern verschwiegen."""
    vorgaben = " ".join(_szene()["vertragsvorgaben"])

    assert "1600x992" in vorgaben, "die Rundung auf Vielfache von 16"
    assert "controlnet_staerke" in vorgaben, "die faithful-Zuordnung"
    assert "Sonnenangabe" in vorgaben, "die fehlende Sonne"


def test_eine_echte_warnung_erscheint_und_wird_nicht_verdraengt():
    """Der Fall, der vorher unsichtbar war: eine Warnung, die im Code **nach** den drei
    Dauerwarnungen steht."""
    szene = _szene(style={"prompt": "ein Haus mit Satteldach"})

    assert szene["warnungen"], "der Bauteilwaechter steht im Code weit hinter den dreien"
    assert any("dach" in w.lower() for w in szene["warnungen"])


# ======================================================================================
# Die Bildmasse — wo der Hinweis landet, hängt daran, ob jemand gewählt hat
# ======================================================================================

def test_die_geerbte_bildmasse_ist_eine_vertragsvorgabe():
    """Niemand hat 1600×1000 für DIESEN Auftrag gewählt; es ist die Vorgabe des fremden
    Vertrags, und sie ist nie ein Vielfaches von 16."""
    szene = _szene(render={"samples": 64})

    assert any("1600x1000" in v for v in szene["vertragsvorgaben"])
    assert szene["warnungen"] == ()


def test_eine_selbst_gewaehlte_bildmasse_ist_eine_warnung():
    """**Die Gegenprobe, und sie trägt die Unterscheidung.** Wer 999×777 bestellt, hat
    eine Entscheidung getroffen — und der Beschnitt betrifft dann seinen Auftrag und
    nicht den Vertrag."""
    szene = _szene(render={"resolution": [999, 777]})

    assert any("999x777" in w for w in szene["warnungen"])
    assert not any("999x777" in v for v in szene["vertragsvorgaben"])
    assert len(szene["vertragsvorgaben"]) == 2, "die anderen beiden bleiben, wo sie sind"


def test_eine_bildmasse_die_passt_erzeugt_gar_keinen_hinweis():
    """Sonst wäre auch das wieder eine Dauerzeile — nur an einer neuen Stelle."""
    szene = _szene(render={"resolution": [1024, 1024]})

    assert not any("1024" in t for t in szene["warnungen"] + szene["vertragsvorgaben"])


def test_ein_kaputtes_resolution_feld_bleibt_eine_warnung():
    """Es ist ein Fehler in DIESER Bestellung und keine Eigenschaft des Vertrags."""
    szene = _szene(render={"resolution": "gross"})

    assert any("kein Paar" in w for w in szene["warnungen"])


# ======================================================================================
# Die Tabelle — der Wächter, der einen neuen Feldnamen nicht durchrutschen lässt
# ======================================================================================

def test_das_neue_feld_steht_in_der_tabelle():
    """`tests/test_naht_durchreichung.py` erzwingt das ohnehin; hier steht es noch einmal
    ausdrücklich, weil die Tabelle der Grund für dieses ganze Feld ist."""
    assert DURCHGEREICHT["vertragsvorgaben"]
    assert "vertragsvorgaben" not in STEHENGEBLIEBEN


# ======================================================================================
# Und es erreicht den Weg nach draussen
# ======================================================================================

def test_die_bruecke_reicht_die_vorgaben_getrennt_weiter(tmp_path):
    """Eine Trennung, die an der Naht wieder zusammenfällt, ist keine."""
    import json

    (tmp_path / "vis-1-aaaaaa").mkdir()
    ordner = tmp_path / "vis-1-aaaaaa"
    (ordner / "job.json").write_text(json.dumps(
        {"job_id": "vis-1-aaaaaa", "status": "queued", "approval_token": "appr_xyz"}),
        encoding="utf-8")
    (ordner / "render-scene.json").write_text(json.dumps(BESTELLUNG), encoding="utf-8")
    (ordner / "model.glb").write_bytes(b"glTF")

    auftrag = bruecke.lies_auftrag(ordner)

    assert len(auftrag["vertragsvorgaben"]) == 3
    assert not [w for w in auftrag["warnungen"] if w in auftrag["vertragsvorgaben"]], (
        "keine Zeile steht in beiden Listen — sonst wuerde sie doppelt gelesen")


def test_das_werkzeug_deckelt_die_warnungen_nicht_mehr():
    """Der Deckel `[:3]` ist der eigentliche Schaden gewesen. Er steht hier als Zeichen,
    weil ein Test am Ausgabetext des Werkzeugs sonst nur seine eigene Formatierung
    prüfte."""
    from pathlib import Path

    quelle = (Path(__file__).resolve().parents[1] / "tools" / "abholen.py").read_text(
        encoding="utf-8")

    assert 'e.get("warnungen") or ())[:3]' not in quelle
    assert 'e.get("vertragsvorgaben")' in quelle, (
        "die drei muessen irgendwo hin — geloescht waeren sie verschwiegen")
