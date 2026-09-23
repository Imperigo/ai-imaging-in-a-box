"""Der Zwilling spricht in ``verdict.reason`` (Runde 11, 23.09.2026).

Der Befund
----------
Ein **Zwilling** ist eine Kamera, deren Soll-Karte mit der einer frueheren Kamera
desselben Auftrags identisch ist; sie wird nicht neu gerendert, sondern uebernimmt Bild
und Urteil ihres Vorbilds (``abholer.verarbeiter``: ``dict(zwilling["urteil"],
kamera=…, doppelt_von=…)``). Damit erbt sie auch ``bild_png``.

``abholer._nicht_gerendert_kurz`` uebersprang bis zum 23.09.2026 jeden Eintrag mit
``bild_png`` — also auch jeden Zwilling eines gerenderten Vorbilds, bevor
``_art_ohne_bild`` «doppelt» sagen konnte. ``verdict.reason``, das Feld, das KosmoOrbit
liest, sagte darum nichts ueber Zwillinge. Genannt waren sie nur in
``lieferstatus_grund`` und im eigenen Kurzbefund. Der Satz fuer sie stand schon da
(``abholer._satz_ohne_bild('doppelt', …)``) und wurde auf diesem Weg nie erreicht.

Was diese Datei bewacht
-----------------------
Ueber den Produktweg — ``bruecke`` → ``abholer.hole_einen`` → ``abholer.verarbeiter``
mit Attrappen fuer Multipass, Render und Soll-Karte (aus
``tests/test_kettenlauf_26august.py``) → die GESCHRIEBENE Ergebnisdatei:

1. Ein Auftrag mit Zwilling nennt ihn in ``verdict.reason``, mit dem vorhandenen Satz,
   an der Stelle der uebrigen nicht gerenderten Kameras.
2. **Vorher/nachher am selben Auftrag.** «Vorher» ist derselbe Produktweg, nur mit dem
   alten Filter (jedes ``bild_png`` fiel weg) — nachgebildet als der neue Leser, dem die
   Eintraege mit ``bild_png`` vorenthalten werden. Die beiden Filter unterscheiden sich
   genau darin; ist der alte nachgebildet, ist der Unterschied zwischen den beiden
   Dateien die ganze Wirkung dieser Aenderung.
3. Ohne Zwilling ist die Datei **bitgleich** zu vorher (bis auf die Laufzeiten, die
   zwischen zwei Laeufen schwanken duerfen).
4. Mit Zwilling aendert sich an der Datei **nur** ``verdict.reason`` — Score,
   ``passed``, ``qa_je_kamera``, ``lieferstatus`` und ``lieferstatus_grund`` bleiben.

Regel 3: alle Szenen, Kameras und Karten sind synthetisch.
"""
from __future__ import annotations

import json

import pytest

from aiimaging import abholer, bruecke

from test_kettenlauf_26august import _auftragsordner, _kamerablock, _kette, _lauf

#: Der Satz, wie ihn ``abholer._satz_ohne_bild('doppelt', …)`` baut — hier WOERTLICH,
#: weil er an KosmoOrbit angesagt ist. Aendert er sich, ist das eine Vertragsaenderung.
ZWILLING_NNW = "Nicht neu gerendert (identische Soll-Karte), nNW"

#: Karten fuer ``cameras: auto`` (s, sSE, nNW): ``nNW`` ist Zwilling von ``s``.
KARTEN_EIN_ZWILLING = [[[1.0]], [[2.0]], [[1.0]]] + [[[float(i)]] for i in range(3, 30)]


def _alter_filter(echt):
    """Der Leser, wie er bis zum 23.09.2026 filterte: Jeder Eintrag mit ``bild_png``
    fiel weg. Nachgebildet, indem der heutige Leser diese Eintraege nicht zu sehen
    bekommt — alles andere (Einteilung, Gruppierung, Wortlaut) bleibt das heutige."""
    def vorher(kameras):
        return echt([k for k in kameras or ()
                     if isinstance(k, dict) and not k.get("bild_png")])
    return vorher


def _vertrag(wurzel, **kette) -> dict:
    """Ein Auftrag (``cameras: auto``) durch den Produktweg; zurueck kommt die
    GESCHRIEBENE Datei, nicht ein Rueckgabewert."""
    wurzel.mkdir(parents=True)
    ordner = _auftragsordner(wurzel)
    _protokoll, attrappen = _kette(wurzel, **kette)
    antwort = _lauf(wurzel, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    return json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))


def _vorher_nachher(tmp_path, monkeypatch, **kette) -> tuple[dict, dict]:
    """Derselbe Auftrag zweimal: einmal mit dem alten Filter, einmal wie ausgeliefert."""
    echt = abholer._nicht_gerendert_kurz
    with monkeypatch.context() as m:
        m.setattr(abholer, "_nicht_gerendert_kurz", _alter_filter(echt))
        vorher = _vertrag(tmp_path / "vorher", **kette)
    nachher = _vertrag(tmp_path / "nachher", **kette)
    return vorher, nachher


def _ohne(vertrag: dict, *, grund: bool) -> dict:
    """Die Datei ohne Laufzeiten — und auf Wunsch ohne ``verdict.reason``."""
    kopie = json.loads(json.dumps(vertrag))
    kopie.pop("timings", None)
    if grund:
        kopie["qa"]["verdict"].pop("reason")
    return kopie


def _grund(vertrag: dict) -> str:
    return vertrag["qa"]["verdict"]["reason"]


def _hoch(kuerzel):
    """``sSE`` steht ueber dem Dach — abgebrochen vor dem Render (Kamerahoehe)."""
    block = _kamerablock(kuerzel)
    return dict(block, auge=[0.0, -30.0, 77.0]) if kuerzel == "sSE" else block


# ======================================================================================
# 1 · Mit Zwilling
# ======================================================================================

def test_der_zwilling_steht_in_verdict_reason(tmp_path, monkeypatch):
    """``nNW`` ist Zwilling von ``s``. Vorher schwieg ``verdict.reason`` ueber ihn;
    nachher steht der vorhandene Satz vorn — und sonst aendert sich nichts am Grund."""
    vorher, nachher = _vorher_nachher(tmp_path, monkeypatch, karten=KARTEN_EIN_ZWILLING)

    assert nachher["images"] == ["s.png", "sSE.png"], "Vorbedingung: nNW nicht gerendert"
    assert "identische Soll-Karte" not in _grund(vorher), (
        "Vorbedingung: der alte Filter verschweigt den Zwilling")
    assert _grund(nachher) == f"{ZWILLING_NNW}; {_grund(vorher)}"
    assert _grund(nachher).count("identische Soll-Karte") == 1


def test_mit_zwilling_aendert_sich_nur_verdict_reason(tmp_path, monkeypatch):
    """Score, ``passed``, ``qa_je_kamera``, ``lieferstatus`` und sein Grund — die ganze
    Datei bis auf ``verdict.reason`` ist dieselbe wie vorher."""
    vorher, nachher = _vorher_nachher(tmp_path, monkeypatch, karten=KARTEN_EIN_ZWILLING)

    assert _ohne(nachher, grund=True) == _ohne(vorher, grund=True)
    # Belegt einzeln, was der Auftrag nennt — damit ein leerer Vergleich nicht gruen wird.
    assert nachher["qa"]["geometry"]["geometry_fidelity"] == 0.81
    assert nachher["qa"]["verdict"]["passed"] is True
    assert nachher["lieferstatus"] == "geliefert"
    je = {e["kamera"]: e for e in nachher["qa_je_kamera"]}
    assert (je["nNW"]["lieferstatus"], je["nNW"]["bilder_ist"]) == ("uebersprungen", 0)
    assert je["s"]["lieferstatus"] == je["sSE"]["lieferstatus"] == "geliefert"


def test_zwei_zwillinge_stehen_in_einer_zeile(tmp_path, monkeypatch):
    """Drei gleiche Karten: ``sSE`` und ``nNW`` sind Zwillinge von ``s``. Gruppiert wird
    nach Grund, nicht je Kamera — eine Zeile mit beiden Kuerzeln."""
    vorher, nachher = _vorher_nachher(tmp_path, monkeypatch, karten=[[[1.0]]] * 5)

    assert nachher["images"] == ["s.png"], "Vorbedingung: einmal gerendert"
    assert _grund(nachher) == (
        f"Nicht neu gerendert (identische Soll-Karte), sSE, nNW; {_grund(vorher)}")
    assert _ohne(nachher, grund=True) == _ohne(vorher, grund=True)


def test_der_zwilling_steht_hinter_einem_abbruch_in_kamerafolge(tmp_path, monkeypatch):
    """``sSE`` bricht ueber dem Dach ab (verbraucht keine Karte), ``nNW`` ist Zwilling
    von ``s``. Der Zwillingssatz steht an der Stelle der nicht gerenderten Kameras und
    in ihrer Reihenfolge: nach dem Abbruch von ``sSE``, vor allem Uebrigen."""
    vorher, nachher = _vorher_nachher(tmp_path, monkeypatch, kamerablock=_hoch,
                                      karten=[[[1.0]], [[1.0]]])

    assert nachher["images"] == ["s.png"], "Vorbedingung: nur s gerendert"
    teile_vorher = _grund(vorher).split("; ")
    assert teile_vorher[0].startswith("NICHT GERENDERT (Aufnahme nicht beurteilbar), sSE")
    assert _grund(nachher).split("; ") == [teile_vorher[0], ZWILLING_NNW,
                                           *teile_vorher[1:]]
    assert _ohne(nachher, grund=True) == _ohne(vorher, grund=True)


# ======================================================================================
# 2 · Ohne Zwilling — bitgleich zu vorher
# ======================================================================================

@pytest.mark.parametrize("kette", [
    pytest.param({}, id="alle-gerendert"),
    pytest.param({"kamerablock": _hoch}, id="einer-ueber-dem-dach"),
    pytest.param({"bbox_bauwerk": [[0, 0, 0], [1.0, 1.0, 1.0]]}, id="alle-rahmung"),
])
def test_ohne_zwilling_ist_die_datei_bitgleich_zu_vorher(tmp_path, monkeypatch, kette):
    vorher, nachher = _vorher_nachher(tmp_path, monkeypatch, **kette)

    assert "identische Soll-Karte" not in _grund(nachher)
    assert _grund(nachher) == _grund(vorher)
    assert _ohne(nachher, grund=False) == _ohne(vorher, grund=False)
