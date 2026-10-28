"""A0004 — ein von Hand ersetztes ``modell.glb`` in der Mappe wird erkannt.

Drei Fälle am Laden einer Mappe: ersetzt → «geändert» mit altem und neuem Abdruck; unverändert →
«unverändert»; alte Mappe ohne Abdruck → «kein Abdruck», ohne Fehler und ohne Hinweis. Dazu der Weg bis
zum Knoten (``mappe_fuer_knoten``), das Verschwinden des Hinweises nach «Andere Datei …» und das
Nachtragen beim nächsten Speichern.

Regel 3: alles synthetisch (``tools/make_test_glb.py``), keine Namen.
"""
from __future__ import annotations

import importlib.util
import os
import time
from pathlib import Path

from aiimaging import arbeitsgang, knotenweg, projekt

WURZEL = Path(__file__).resolve().parents[1]


def _baue(teile: int) -> bytes:
    spec = importlib.util.spec_from_file_location("mk_glb", WURZEL / "tools" / "make_test_glb.py")
    mk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mk)
    return mk.baue_glb([(f"Teil_{i}", (i, 0, 0), (i + 0.5, 3, 5)) for i in range(teile)])


def _mappe(tmp_path, teile=1):
    quelle = tmp_path / "haus.glb"
    quelle.write_bytes(_baue(teile))
    mappe = tmp_path / "mappe"
    mappe.mkdir()
    arbeitsgang.lege_an(mappe, quelle, name="Testbau")
    return mappe, quelle


def _stand(mappe):
    return projekt.glb_stand(projekt.oeffne(mappe)["projekt"], mappe)


def _glb(mappe) -> Path:
    """Die glb, die die Mappe als ihr Modell nennt (``import.glb``) — bei einer glb-Quelle die
    durchgereichte Datei, bei IFC/OBJ ``modell.glb`` in der Mappe."""
    return Path(projekt.loese_pfad(projekt.oeffne(mappe)["projekt"]["import"]["glb"], mappe))


def _ersetze_von_hand(mappe, teile):
    glb = _glb(mappe)
    glb.write_bytes(_baue(teile))
    # Eine Aenderungszeit, die sich sicher unterscheidet (grobe Dateisysteme).
    spaeter = time.time() + 5
    os.utime(glb, (spaeter, spaeter))


def test_ersetzt_nach_dem_speichern_liefert_geaendert_mit_beiden_abdruecken(tmp_path):
    mappe, _ = _mappe(tmp_path)
    alt = projekt.oeffne(mappe)["projekt"]["import"]["glb_abdruck"]
    _ersetze_von_hand(mappe, 3)
    st = _stand(mappe)
    assert st["stand"] == projekt.GLB_GEAENDERT
    assert st["alt"]["summe"] == alt["summe"]
    assert st["neu"]["summe"] and st["neu"]["summe"] != alt["summe"]
    assert st["neu"]["groesse_byte"] != alt["groesse_byte"]
    assert "Modell geändert seit" in st["satz"]


def test_unveraendert_und_gleiche_bytes_neuer_zeitstempel_sind_unveraendert(tmp_path):
    mappe, _ = _mappe(tmp_path)
    assert _stand(mappe)["stand"] == projekt.GLB_UNVERAENDERT
    assert _stand(mappe)["satz"] == ""
    # Nur angefasst (etwa durch Abgleich zwischen Geraeten): kein Hinweis.
    glb = _glb(mappe)
    glb.write_bytes(glb.read_bytes())
    spaeter = time.time() + 5
    os.utime(glb, (spaeter, spaeter))
    assert _stand(mappe)["stand"] == projekt.GLB_UNVERAENDERT


def test_alte_mappe_ohne_abdruck_ist_gueltig_und_bekommt_ihn_beim_speichern(tmp_path):
    mappe, _ = _mappe(tmp_path)
    p = projekt.oeffne(mappe)["projekt"]
    del p["import"]["glb_abdruck"]
    (mappe / projekt.PROJEKTDATEI).write_text(
        __import__("json").dumps(p), encoding="utf-8")
    st = _stand(mappe)
    assert st["stand"] == projekt.GLB_KEIN_ABDRUCK and st["satz"] == ""
    assert knotenweg.mappe_fuer_knoten(mappe)["glb_stand"]["satz"] == ""
    # Naechstes Speichern traegt ihn nach.
    p = projekt.oeffne(mappe)["projekt"]
    projekt.speichere(p, mappe)
    assert projekt.oeffne(mappe)["projekt"]["import"]["glb_abdruck"]["summe"]
    assert _stand(mappe)["stand"] == projekt.GLB_UNVERAENDERT


def test_speichern_erklaert_eine_ersetzte_glb_nicht_fuer_gueltig(tmp_path):
    mappe, _ = _mappe(tmp_path)
    _ersetze_von_hand(mappe, 3)
    p = projekt.oeffne(mappe)["projekt"]
    projekt.speichere(p, mappe)
    assert _stand(mappe)["stand"] == projekt.GLB_GEAENDERT


def test_der_knoten_bekommt_den_hinweis_und_verliert_ihn_nach_andere_datei(tmp_path):
    mappe, quelle = _mappe(tmp_path)
    assert knotenweg.mappe_fuer_knoten(mappe)["glb_stand"]["satz"] == ""
    _ersetze_von_hand(mappe, 3)
    antwort = knotenweg.mappe_fuer_knoten(mappe)
    assert antwort["glb_stand"]["stand"] == projekt.GLB_GEAENDERT
    assert "Modell geändert seit" in antwort["glb_stand"]["satz"]
    # Der Architekt uebernimmt das Modell: neu einlesen (die Mappe speichert dabei).
    quelle.write_bytes(_baue(3))
    arbeitsgang.ersetze_modell(mappe, quelle)
    antwort = knotenweg.mappe_fuer_knoten(mappe)
    assert antwort["glb_stand"]["stand"] == projekt.GLB_UNVERAENDERT
    assert antwort["glb_stand"]["satz"] == ""


def test_fehlende_glb_wirft_nicht(tmp_path):
    mappe, _ = _mappe(tmp_path)
    _glb(mappe).unlink()
    assert _stand(mappe)["stand"] == projekt.GLB_FEHLT
