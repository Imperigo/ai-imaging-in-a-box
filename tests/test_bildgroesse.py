"""Die Bildgroesse — **gemessen, nicht gedeckelt.** Und die Einheit, an der es starb.

**Was hier bis zum 04.09.2026 geprueft wurde.** Diese Datei hiess ``test_blattfassung``
und bewachte einen Deckel: 1 048 576 Base64-Zeichen, abgeschrieben vom Tor in KosmoOrbit.
Sie prueft ihn nicht mehr, weil es ihn nicht mehr gibt.

**Warum er fiel** (gemessen 03.09.2026, entschieden 04.09.2026):

* Er HIESS 1.0 MB und WAR 0.79 MB — verglichen wurden Zeichen, gemeldet wurden Bytes.
  1 048 576 Zeichen sind 786 432 Byte. Wer der Meldung folgte und auf 1.0 MB
  verkleinerte, wurde ein zweites Mal abgewiesen (1 000 000 Byte → 1 333 336 Zeichen,
  27 % darueber).
* 60 von 66 Nutzbildern lagen darueber, Median 1 277 231 Byte. Die Ablehnung war der
  Regelfall.
* Ein technischer Grund fuer die Zahl war nirgends auffindbar.

**Was diese Datei jetzt prueft — drei Dinge, und jedes kann widersprechen:**

1. dass die Kette den Zwang wirklich losgeworden ist (kein Vorgabedeckel, keine
   ungefragte zweite Datei) — :func:`test_es_gibt_keinen_vorgabedeckel_mehr` und
   :func:`test_die_kette_verkleinert_nicht_mehr_ungefragt`;
2. dass sie die Messung NICHT verloren hat — :func:`test_die_messung_bleibt_und_stimmt`;
3. dass jede Meldung, die noch eine Grenze nennt, sie in derselben Einheit nennt wie die
   gemessene Groesse — :func:`test_jede_zahl_traegt_die_einheit_die_zu_ihr_gehoert`.
   **Das ist die Probe, die den Fehler vom 03.09. gefunden haette.**

Alle Bilder hier sind synthetisch und werden im Test erzeugt (Regel 3).
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import bildlesen, bildschreiben  # noqa: E402

#: Der gefallene Deckel, nur noch als Zahl fuer die Proben — nicht als Regel im Code.
GEFALLENER_DECKEL_ZEICHEN = 1_048_576
GEFALLENER_DECKEL_BYTE = 786_432


def _rauschbild(ziel, breite: int, hoehe: int, seed: int = 11):
    """Rauschen laesst sich kaum komprimieren — so entsteht eine verlaesslich grosse Datei."""
    wuerfel = random.Random(seed)
    farben = [(wuerfel.randrange(256), wuerfel.randrange(256), wuerfel.randrange(256))
              for _ in range(breite * hoehe)]
    return bildschreiben.schreibe_farb_png(ziel, farben, breite, hoehe)


def _flaeche(ziel, breite: int, hoehe: int):
    """Eine einfarbige Flaeche komprimiert sehr gut — verlaesslich klein."""
    return bildschreiben.schreibe_farb_png(ziel, [(30, 60, 90)] * (breite * hoehe),
                                           breite, hoehe)


# ── 1 · Der Zwang ist weg ─────────────────────────────────────────────────────────────

def test_es_gibt_keinen_vorgabedeckel_mehr(tmp_path):
    """**Die Probe gegen den Rueckfall.** Ein Vorgabewert waere der stille Deckel zurueck.

    Sie widerspricht auf zwei Wegen: wenn die alten Konstanten zurueckkehren, und wenn
    jemand ``deckel_byte`` wieder einen Vorgabewert gibt.
    """
    for name in ("BLATT_DECKEL_BASE64_ZEICHEN", "BLATT_DECKEL_BYTE", "BLATT_MIN_KANTE",
                 "passt_aufs_blatt", "blattfassung"):
        assert not hasattr(bildschreiben, name), (
            f"{name} ist am 04.09.2026 gefallen und darf nicht stillschweigend "
            f"zurueckkommen")

    datei = _flaeche(tmp_path / "klein.png", 100, 100)
    with pytest.raises(TypeError):
        bildschreiben.passt_unter(datei)                       # type: ignore[call-arg]
    with pytest.raises(TypeError):
        bildschreiben.kleinere_fassung(datei, tmp_path / "x.png")  # type: ignore[call-arg]


def test_die_kette_verkleinert_nicht_mehr_ungefragt(tmp_path):
    """**Der eigentliche Entscheid, als Probe am Abholer.**

    Ein Bild weit ueber dem gefallenen Deckel laeuft durch die Naht, an der bis gestern
    automatisch eine kleinere Kopie entstand. Es darf keine zweite Bilddatei geben.
    """
    from aiimaging import abholer

    bild = _rauschbild(tmp_path / "Eingang.png", 700, 500)
    assert bild.stat().st_size > GEFALLENER_DECKEL_BYTE, (
        "der Fall traegt nur, wenn das Bild ueber dem alten Deckel liegt")

    abholer._groesse_ablegen(tmp_path, "Eingang", bild)

    pngs = sorted(p.name for p in tmp_path.glob("*.png"))
    assert pngs == ["Eingang.png"], f"eine ungefragte zweite Bilddatei: {pngs}"
    bericht = json.loads((tmp_path / "Eingang_groesse.json").read_text(encoding="utf-8"))
    assert "passt" not in bericht, "die Groesse ist eine Zahl, kein Urteil"
    assert "blatt_png" not in bericht


def test_ein_fehlschlag_der_messung_kostet_den_lauf_nicht(tmp_path):
    """Das Bild ist da; die Groesse ist eine Auskunft ueber es, keine Stufe."""
    from aiimaging import abholer

    abholer._groesse_ablegen(tmp_path, "Eingang", tmp_path / "gibtsnicht.png")
    assert not (tmp_path / "Eingang_groesse.json").exists()


# ── 2 · Die Messung bleibt ────────────────────────────────────────────────────────────

def test_die_messung_bleibt_und_stimmt(tmp_path):
    """**Die andere Haelfte des Entscheids.** Der Deckel war falsch, die Zahl nicht.

    Gemessen wird gegen ``stat()`` und nicht gegen den eigenen Rueckgabewert.
    """
    from aiimaging import abholer

    bild = _rauschbild(tmp_path / "Eingang.png", 700, 500)
    abholer._groesse_ablegen(tmp_path, "Eingang", bild)

    bericht = json.loads((tmp_path / "Eingang_groesse.json").read_text(encoding="utf-8"))
    assert bericht["bytes"] == bild.stat().st_size
    assert bericht["zeichen"] == bildschreiben.base64_zeichen(bild.stat().st_size)
    assert str(bild.stat().st_size) in bericht["text"]


def test_drei_bytes_werden_vier_zeichen():
    """Die Umrechnung bleibt — wer base64 kodiert, braucht sie. Falsch war ihr Gebrauch."""
    assert bildschreiben.base64_zeichen(3) == 4
    assert bildschreiben.base64_zeichen(1) == 4      # aufgefuellt
    assert bildschreiben.base64_zeichen(1_241_264) == 1_655_020
    assert bildschreiben.base64_zeichen(GEFALLENER_DECKEL_BYTE) == GEFALLENER_DECKEL_ZEICHEN


def test_eine_fehlende_datei_ist_ein_fehler_und_kein_null(tmp_path):
    """0 Byte hiesse «gemessen und leer». Es gab aber nichts zu messen."""
    with pytest.raises(bildschreiben.SchreibError, match="keine Datei"):
        bildschreiben.bildgroesse(tmp_path / "gibtsnicht.png")


# ── 3 · Die Einheit darf nicht mehr luegen ────────────────────────────────────────────

_BYTEZAHLEN = re.compile(r"(\d+)\s+Byte")
_ZEICHENZAHLEN = re.compile(r"(\d+)\s+Zeichen")


def test_jede_zahl_traegt_die_einheit_die_zu_ihr_gehoert(tmp_path):
    """**Die Probe, die den Fehler vom 03.09.2026 gefunden haette.**

    Die alte Meldung nannte die gemessene Groesse in Rohbytes und die Grenze in
    Base64-Zeichen — beide beschriftet als «MB». Hier wird der Satz wieder in Zahlen
    zerlegt: Was als Byte beschriftet ist, muss eine Byte-Zahl sein, was als Zeichen
    beschriftet ist, eine Zeichen-Zahl. Keine darf an der Stelle der anderen stehen.

    Der Fall ist bewusst der historische: eine Datei von 1 000 000 Byte gegen die Grenze
    von 786 432 Byte. Wer hier die Zeichenzahl als Byte-Grenze schreibt, nennt 1 048 576
    — und der Vergleich unten faellt.
    """
    datei = tmp_path / "eine_million.png"
    datei.write_bytes(b"\x00" * 1_000_000)

    befund = bildschreiben.passt_unter(datei, deckel_byte=GEFALLENER_DECKEL_BYTE)
    assert befund["passt"] is False
    assert befund["bytes"] == 1_000_000
    assert befund["zeichen"] == 1_333_336

    grund = befund["grund"]
    assert {int(z) for z in _BYTEZAHLEN.findall(grund)} == {1_000_000, GEFALLENER_DECKEL_BYTE}
    assert {int(z) for z in _ZEICHENZAHLEN.findall(grund)} == {1_333_336, GEFALLENER_DECKEL_ZEICHEN}
    assert "MB" not in grund, (
        "MB ist zweideutig (10^6 gegen 2^20) — genau daran hing der Fehler")


def test_die_einheitenprobe_kann_widersprechen():
    """**Eine Probe, die nicht widersprechen kann, ist keine.**

    Hier steht der Fehler von gestern nachgebaut: derselbe Satzbau, aber die Grenze in
    Zeichen und als Byte beschriftet. Die Probe oben muss ihn ablehnen — sonst prueft sie
    nichts.
    """
    falsch = (f"1000000 Byte gegen eine Grenze von {GEFALLENER_DECKEL_ZEICHEN} Byte — "
              f"darueber.")
    assert {int(z) for z in _BYTEZAHLEN.findall(falsch)} != {1_000_000, GEFALLENER_DECKEL_BYTE}


def test_eine_grenze_von_null_ist_keine_grenze(tmp_path):
    datei = _flaeche(tmp_path / "klein.png", 100, 100)
    with pytest.raises(bildschreiben.SchreibError, match="mindestens 1"):
        bildschreiben.passt_unter(datei, deckel_byte=0)


# ── 4 · Das Werkzeug bleibt ───────────────────────────────────────────────────────────

def test_die_fassung_passt_und_die_gegenprobe_bestaetigt_es(tmp_path):
    """Wer bewusst verkleinern will, kann es weiter — er muss nur sagen, wie klein."""
    quelle = _rauschbild(tmp_path / "quelle.png", 700, 500)
    ergebnis = bildschreiben.kleinere_fassung(quelle, tmp_path / "klein.png",
                                              deckel_byte=GEFALLENER_DECKEL_BYTE)

    assert ergebnis["passt"] is True
    assert ergebnis["verkleinert"] is True
    assert ergebnis["quelle_bytes"] > GEFALLENER_DECKEL_BYTE
    # Nicht dem Rueckgabewert glauben, sondern die Datei messen:
    assert (tmp_path / "klein.png").stat().st_size <= GEFALLENER_DECKEL_BYTE
    _farben, b, h = bildlesen.lies_png_farben(tmp_path / "klein.png")
    assert (b, h) == (ergebnis["breite"], ergebnis["hoehe"])
    assert b < 700 and h < 500


def test_was_schon_passt_wird_nicht_verkleinert(tmp_path):
    """Eine Fassung, die vorsichtshalber Aufloesung wegwirft, waere schlechter als keine."""
    quelle = _flaeche(tmp_path / "quelle.png", 400, 300)
    ergebnis = bildschreiben.kleinere_fassung(quelle, tmp_path / "klein.png",
                                              deckel_byte=GEFALLENER_DECKEL_BYTE)
    assert ergebnis["passt"] is True
    assert ergebnis["verkleinert"] is False
    assert ergebnis["versuche"] == 0
    assert (tmp_path / "klein.png").read_bytes() == quelle.read_bytes()


def test_die_fassung_schummelt_sich_NICHT_unter_die_grenze(tmp_path):
    """Ein unerreichbares Ziel muss zu ``passt=False`` fuehren, nicht zu einem
    Briefmarkenbild, das die Frage nicht mehr beantwortet."""
    quelle = _rauschbild(tmp_path / "quelle.png", 700, 500)
    ergebnis = bildschreiben.kleinere_fassung(
        quelle, tmp_path / "klein.png", deckel_byte=3_000, min_kante=400)
    assert ergebnis["passt"] is False
    assert ergebnis["warnungen"], "ein Fehlschlag ohne Begruendung ist keine Meldung"
    assert "400" in " ".join(ergebnis["warnungen"])


def test_die_genannte_grenze_gilt_und_nicht_eine_andere(tmp_path):
    """Die Grenze ist ein Argument. Wer eine andere nennt, bekommt eine andere Fassung."""
    quelle = _rauschbild(tmp_path / "quelle.png", 500, 400)
    gross = bildschreiben.kleinere_fassung(quelle, tmp_path / "a.png", deckel_byte=150_000,
                                           min_kante=50)
    klein = bildschreiben.kleinere_fassung(quelle, tmp_path / "b.png", deckel_byte=30_000,
                                           min_kante=50)
    assert gross["passt"] and klein["passt"]
    assert (tmp_path / "a.png").stat().st_size <= 150_000
    assert (tmp_path / "b.png").stat().st_size <= 30_000
    assert klein["breite"] < gross["breite"], "die kleinere Grenze muss kleiner ausfallen"


def test_kastenmittel_mittelt_und_nimmt_nicht_den_naechsten_nachbarn():
    """Ein Render traegt duenne Linien; der naechste Nachbar laesst sie verschwinden."""
    farben = [(0, 0, 0), (100, 100, 100),
              (200, 200, 200), (255, 255, 255)]        # 2x2
    klein = bildschreiben._kastenmittel(farben, 2, 2, 1, 1)
    assert klein == [((0 + 100 + 200 + 255) // 4,) * 3]
    assert klein != [(0, 0, 0)], "das waere der naechste Nachbar"
