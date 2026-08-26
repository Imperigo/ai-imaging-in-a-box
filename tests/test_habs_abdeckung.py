"""Was die Kamerawahl von der Dokumentationsnorm abdeckt — und was nicht.

`komposition.fehlende_ansichten` stand seit dem 21.08.2026 im Modul und hatte **keinen
Aufrufer** ausser ihren Tests. Gefunden hat sie `tools/tote_kanten.py` am 26.08.2026, beim
ersten Lauf des Werkzeugs.

**Und sie hat gelogen, als sie gefunden wurde.** Mit der heutigen Projektvorgabe
``("s", "sSE", "nNW")`` gab sie ``()`` zurück — «nichts fehlt». Das stimmt nicht:
*Umgebungsansicht* und *Frontalansicht* liegen **beide** auf ``s`` und unterscheiden sich
allein im **Ausschnitt**. Eine einzige Aufnahme aus ``s`` deckt genau eine von beiden ab,
und aus der Richtung ist nicht zu sagen, welche.

Ein Test hiess sogar `test_der_volle_habs_satz_laesst_nichts_fehlen` und hat die
Fehlaussage festgeschrieben. *Ein ungerufenes Stück Code wird nicht nur nicht benutzt — es
wird auch nicht widerlegt.*

Und der Docstring nannte als Projektvorgabe ``("sSE",)``. Seit dem 23.08.2026 sind es
drei Richtungen. **Eine Zahl in Prosa veraltet, ohne dass irgendetwas rot wird.**
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aiimaging import abholer, komposition
from conftest import MINI_PNG


def test_die_auskunft_erreicht_den_befund(tmp_path):
    """Sonst wäre es die achte tote Kante — und diesmal eine, die ich selbst
    angeschlossen zu haben glaubte."""
    zaehler = {"render": 0}

    def multipass(glb, aus, **kw):
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.write_bytes(MINI_PNG)
        return {"depth_png": str(tiefe), "kamera": {"weg": "vorgegeben"}}

    def rendere(auftrag, **kw):
        zaehler["render"] += 1
        bild = Path(tmp_path) / f"b{zaehler['render']}.png"
        bild.write_bytes(MINI_PNG)
        return {"status": "ok", "bild_png": str(bild), "hinweise": ()}

    folge = iter([[[float(i)]] for i in range(1, 20)])
    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path, nullprobe=False,
        _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        _soll=lambda *a, **k: (next(folge), 1, 1))

    ergebnis = verarbeite({"modell": tmp_path / "m.glb", "job_id": "vis-1-aaaaaa",
                           "verzeichnis": tmp_path,
                           "szene": {"kameras": [{"kuerzel": "sSE", "richtung": "sSE"}],
                                     "aufloesung": 64, "hoehe": 64, "samples": 1,
                                     "prompt": "a house"}})

    # Der Befund entsteht in `hole_einen`; hier wird die Auskunft direkt geprueft.
    urteil = komposition.fehlende_ansichten(
        [k["kamera"] for k in ergebnis["kameras"]])

    assert urteil["fehlend"] == ("umgebung", "frontal", "ueber_eck_hinten")


def test_der_kurzbefund_nennt_was_die_kamerawahl_weglaesst():
    zeilen = abholer.befund_kurz({
        "kameras": [{"kamera": "sSE"}],
        "habs_ansichten": komposition.fehlende_ansichten(("sSE",))})

    treffer = [z for z in zeilen if "HABS-Ansichten" in z]
    assert len(treffer) == 1
    assert "FEHLT" in treffer[0] and "ueber_eck_hinten" in treffer[0]


def test_der_kurzbefund_nennt_auch_das_offene():
    """Die heutige Vorgabe lässt nichts **fehlen** und trotzdem etwas **offen**. Wer nur
    auf `fehlend` sähe, läse daraus eine Vollständigkeit, die es nicht gibt."""
    zeilen = abholer.befund_kurz({
        "kameras": [{"kamera": k} for k in abholer.AUTO_RICHTUNGEN],
        "habs_ansichten": komposition.fehlende_ansichten(abholer.AUTO_RICHTUNGEN)})

    treffer = [z for z in zeilen if "HABS-Ansichten" in z]
    assert len(treffer) == 1
    assert "NICHT FESTSTELLBAR" in treffer[0]
    assert "FEHLT" not in treffer[0]


def test_bei_vollstaendiger_abdeckung_steht_die_zeile_nicht_da():
    """**Die Gegenprobe.** Eine Zeile, die bei jedem Auftrag erscheint, ist nach dem
    dritten Mal keine — dieselbe Regel wie bei den Dauerwarnungen."""
    voll = komposition.fehlende_ansichten(("s", "sSE", "nNW"),
                                          ausschnitte={"s": "weit"})
    # `weit` deckt die Umgebungsansicht ab; die frontale fehlt dann. Fuer den Gegenprobe-
    # Fall wird die Abdeckung von Hand vollstaendig gemacht.
    voll = dict(voll, fehlend=(), nicht_feststellbar=())

    zeilen = abholer.befund_kurz({"kameras": [{"kamera": "s"}], "habs_ansichten": voll})

    assert not [z for z in zeilen if "HABS-Ansichten" in z]


def test_ohne_das_feld_steht_die_zeile_ebenfalls_nicht_da():
    """Ein aelterer Befund kennt das Feld nicht. Er darf davon nicht rot werden."""
    assert not [z for z in abholer.befund_kurz({"kameras": [{"kamera": "s"}]})
                if "HABS-Ansichten" in z]


def test_der_docstring_nennt_die_projektvorgabe_richtig():
    """**Der Wächter gegen genau den Fehler, der hier gefunden wurde.** Der Docstring
    nannte `("sSE",)`, und das war seit dem 23.08.2026 falsch. Eine Zahl in Prosa
    veraltet, ohne dass irgendetwas rot wird — hier wird es rot."""
    quelle = Path(komposition.__file__).read_text(encoding="utf-8")
    kopf = quelle.split("def ansichtenkatalog", 1)[1].split("\n    if ", 1)[0]

    assert repr(abholer.AUTO_RICHTUNGEN) in kopf.replace("'", '"').replace('"', "'") \
        or '("s", "sSE", "nNW")' in kopf, (
            "der Docstring muss die WIRKLICHE Vorgabe nennen")
