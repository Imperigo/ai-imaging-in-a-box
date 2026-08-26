"""Der Zwischenspeicher um den Multipass — und die Messungen, auf denen er steht.

Warum es ihn gibt, in Zahlen dieser Umgebung
--------------------------------------------
Gemessen am 26.08.2026 (Blender 4.2.1 LTS, CPU, der synthetische Testbau 8 × 5 × 3 m):

    256 px,   8 Samples:   2,1 s
    800 px,  32 Samples:   7,5 s
   1600 px, 128 Samples:  40,0 s      ← die Vorgaben des Vertrags

Drei Kameras sind damit **zwei Minuten Blender je Auftrag**, auf einem trivialen Quader.
Und jeder Lauf, der nur den Prompt ändert, zahlt sie erneut — der Abholer fährt die Stufen
als gerade Abfolge, ohne Gedächtnis. Ende zu Ende gemessen: **27,7 s → 0,00 s.**

Die Voraussetzung, und sie wäre beinahe falsch gewesen
------------------------------------------------------
Ein Inhalts-Cache steht und fällt damit, dass dieselbe Rechnung dasselbe Ergebnis liefert.
Zweimal dasselbe gerechnet und verglichen:

* ``ifc_zu_glb`` ist **bytegleich** reproduzierbar → der Schlüssel über den glb-Inhalt ist
  stabil.
* ``glb_zu_multipass`` ist **pixelgleich**, aber **nicht bytegleich**: Blender stempelt die
  Uhrzeit in jede Ausgabe (``tEXt Date`` im PNG, ``Date``-Attribut im EXR). Drei von
  30 659 Bytes im EXR, 33 von 64 235 im PNG — die Bilddaten selbst identisch.

*Die zweite Messung ist die wichtigere.* Hätte ich sie nicht gemacht und den Cache über
einen Hash der Ausgaben geprüft, hätte er **nie** einen Treffer gehabt, und niemand hätte
gesehen warum — er wäre einfach folgenlos gewesen.

Was hier NICHT geprüft wird
---------------------------
Ob Blender richtig rendert. Hier geht es allein darum, wann ein Ergebnis
wiederverwendet werden darf und wann nicht.
"""
from __future__ import annotations

import json

import pytest

from aiimaging import abholer, graph, kette

FASSUNG = "Blender 4.2.1 LTS"


@pytest.fixture()
def glb(tmp_path):
    """Eine Datei mit Inhalt — der Schlüssel hängt an ihm, nicht am Pfad."""
    pfad = tmp_path / "modell.glb"
    pfad.write_bytes(b"glTF-Attrappe mit Inhalt")
    return pfad


@pytest.fixture()
def einstellungen(glb):
    return dict(glb_path=str(glb), up_axis="Y", aufloesung=1600, hoehe=1000,
                samples=128, kamera="sSE", out_dir="/irgendwo")


# ── Der Schlüssel ────────────────────────────────────────────────────────────────────

def test_der_ausgabeordner_geht_nicht_in_den_schluessel(einstellungen):
    """Genau darum geht es: Derselbe Schnitt in einem anderen Ordner ist dasselbe Bild."""
    a = abholer.multipass_schluessel(einstellungen, blender=FASSUNG)
    b = abholer.multipass_schluessel(dict(einstellungen, out_dir="/woanders"),
                                     blender=FASSUNG)
    assert a == b


@pytest.mark.parametrize("feld", sorted(abholer.MULTIPASS_NICHT_IM_SCHLUESSEL))
def test_kein_betriebsschalter_verwirft_den_speicher(feld, einstellungen):
    """Eine geänderte Wachfrist darf den ganzen Zwischenspeicher nicht wegwerfen."""
    a = abholer.multipass_schluessel(einstellungen, blender=FASSUNG)
    b = abholer.multipass_schluessel(dict(einstellungen, **{feld: 12345}),
                                     blender=FASSUNG)
    assert a == b, (
        f"{feld!r} steht in MULTIPASS_NICHT_IM_SCHLUESSEL und ändert den Schlüssel "
        f"trotzdem. Grund laut Tabelle: "
        f"{abholer.MULTIPASS_NICHT_IM_SCHLUESSEL[feld]}"
    )


@pytest.mark.parametrize("feld,wert", [
    ("aufloesung", 800), ("samples", 64), ("kamera", "s"), ("up_axis", "Z"),
    ("hoehe", 600), ("gelaende_z", 1.5), ("deckungsgrad", 0.55),
])
def test_jede_bildwirksame_einstellung_aendert_den_schluessel(feld, wert, einstellungen):
    """Die Gegenprobe. Ein Schlüssel, der sich nie ändert, ist kein Schlüssel."""
    a = abholer.multipass_schluessel(einstellungen, blender=FASSUNG)
    b = abholer.multipass_schluessel(dict(einstellungen, **{feld: wert}), blender=FASSUNG)
    assert a != b


def test_der_schluessel_haengt_am_inhalt_der_glb_und_nicht_am_pfad(tmp_path, einstellungen):
    """Ein verschobener Projektordner darf den Zwischenspeicher nicht verwerfen."""
    zwilling = tmp_path / "anders benannt.glb"
    zwilling.write_bytes(b"glTF-Attrappe mit Inhalt")
    gleich = abholer.multipass_schluessel(dict(einstellungen, glb_path=str(zwilling)),
                                          blender=FASSUNG)
    assert gleich == abholer.multipass_schluessel(einstellungen, blender=FASSUNG)

    zwilling.write_bytes(b"eine ANDERE Geometrie")
    anders = abholer.multipass_schluessel(dict(einstellungen, glb_path=str(zwilling)),
                                          blender=FASSUNG)
    assert anders != gleich, "Andere Bytes müssen einen anderen Schlüssel ergeben."


def test_die_blender_fassung_steht_im_schluessel(einstellungen):
    """4.2 und 5.2 sind zwei Renderer.

    Ein Eintrag aus 4.2 unter 5.2 als Treffer zu nehmen hiesse, ein Bild zu benutzen,
    das dieser Rechner so nie erzeugt hätte — und der Unterschied fiele erst am fertigen
    Bild auf.
    """
    a = abholer.multipass_schluessel(einstellungen, blender="Blender 4.2.1 LTS")
    b = abholer.multipass_schluessel(einstellungen, blender="Blender 5.2.0")
    assert a != b


def test_eine_unbekannte_fassung_ist_keine_erlaubnis(einstellungen):
    """Nicht feststellbar ist kein Abbruchgrund — aber auch keine Erlaubnis.

    Die Marke passt zu keinem ermittelten Wert, der Lauf rechnet also neu, statt einen
    fremden Eintrag zu nehmen.
    """
    unbekannt = abholer._blender_fassung(_lauf=lambda: (_ for _ in ()).throw(OSError("x")))
    assert unbekannt.startswith("unbekannt:")
    assert (abholer.multipass_schluessel(einstellungen, blender=unbekannt)
            != abholer.multipass_schluessel(einstellungen, blender=FASSUNG))


def test_die_fassung_wird_aus_der_ersten_zeile_gelesen():
    class Antwort:
        stdout = "Blender 4.2.1 LTS\n\tbuild date: 2024-08-19\n"
    assert abholer._blender_fassung(_lauf=lambda: Antwort()) == "Blender 4.2.1 LTS"


# ── Wann ein Eintrag KEIN Treffer ist ────────────────────────────────────────────────

def _lege_ab(cache, schluessel, tmp_path, **abweichend):
    dateien = {}
    for feld in kette.BEDARF["multipass"].dateien:
        p = tmp_path / f"{feld}.bin"
        p.write_bytes(b"x")
        dateien[feld] = str(p)
    eintrag = {"status": "ok", "blender": "4.2.1 LTS", **dateien, **abweichend}
    cache.lege_ab(schluessel, eintrag,
                  zusagen=[v for v in dateien.values() if v])
    return eintrag


def test_ein_vollstaendiger_eintrag_ist_ein_treffer(tmp_path):
    cache = graph.ArtefaktCache(tmp_path / "cache")
    _lege_ab(cache, "abc", tmp_path)
    assert abholer._aus_dem_zwischenspeicher(cache, "abc") is not None


def test_ein_eintrag_mit_leerem_pflichtfeld_ist_kein_treffer(tmp_path):
    """**Der teuerste Fehler dieses Projekts**, gefangen von `kette._cache_maengel`.

    In Sitzung 07 galt ein Multipass-Eintrag mit ``depth_png = None`` als Treffer. Die
    teure Stufe lief nie wieder, und die Kette scheiterte für immer eine Stufe später —
    mit einer Meldung, die auf den falschen Knoten zeigte.
    """
    cache = graph.ArtefaktCache(tmp_path / "cache")
    _lege_ab(cache, "abc", tmp_path, depth_png=None)
    assert abholer._aus_dem_zwischenspeicher(cache, "abc") is None


def test_eine_zusage_ins_leere_ist_kein_treffer(tmp_path):
    """Ein aufgeräumtes /tmp genügt. Der Eintrag speichert Pfade, nicht Bilder."""
    cache = graph.ArtefaktCache(tmp_path / "cache")
    eintrag = _lege_ab(cache, "abc", tmp_path)
    (tmp_path / "depth_exr.bin").unlink()
    assert abholer._aus_dem_zwischenspeicher(cache, "abc") is None
    assert (tmp_path / "cache" / "abc.json").is_file(), (
        "Der Eintrag bleibt liegen — ein Cache, der beim Lesen löscht, wäre bei zwei "
        "gleichzeitigen Läufen ein Rennen."
    )


def test_ohne_speicher_gibt_es_nie_einen_treffer(tmp_path):
    """`None` heisst AUS, und das ist die Vorgabe."""
    assert abholer._aus_dem_zwischenspeicher(None, "abc") is None


# ── Und am Produktivweg ──────────────────────────────────────────────────────────────

def _auftrag(tmp_path, glb):
    return {"modell": glb, "job_id": "vis-1-aaaaaa", "verzeichnis": tmp_path,
            "szene": {"kameras": "auto", "aufloesung": 64, "hoehe": 64,
                      "samples": 1, "prompt": "a house"}}


def _multipass_zaehler(zaehler: list, tmp_path):
    def multipass(glb, aus, **kw):
        zaehler.append(kw)
        dateien = {}
        for feld in kette.BEDARF["multipass"].dateien:
            p = tmp_path / f"{len(zaehler)}_{feld}.bin"
            p.write_bytes(b"x")
            dateien[feld] = str(p)
        return {"status": "ok", "blender": "4.2.1 LTS", "bbox": [[0, 0, 0], [8, 5, 3]],
                **dateien}
    return multipass


def test_ohne_zwischenspeicher_wird_jedes_mal_gerechnet(tmp_path, glb):
    """Die Vorgabe ändert nichts am bisherigen Verhalten."""
    zaehler: list = []
    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path, auto_richtungen=("s",),
                                     _multipass=_multipass_zaehler(zaehler, tmp_path))
    for _ in range(2):
        with pytest.raises(Exception):
            verarbeite(_auftrag(tmp_path, glb))
    assert len(zaehler) == 2


def test_mit_zwischenspeicher_wird_die_zweite_kamera_nicht_gerechnet(tmp_path, glb):
    """Die eigentliche Behauptung — und sie wird am Produktivweg geprüft, nicht am Modul."""
    zaehler: list = []
    cache = graph.ArtefaktCache(tmp_path / "cache")
    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path, auto_richtungen=("s",),
                                     zwischenspeicher=cache,
                                     _multipass=_multipass_zaehler(zaehler, tmp_path))
    for _ in range(2):
        with pytest.raises(Exception):
            verarbeite(_auftrag(tmp_path, glb))
    assert len(zaehler) == 1, (
        f"Der Multipass lief {len(zaehler)}-mal statt einmal — der Zwischenspeicher "
        f"greift nicht."
    )


def test_ein_echter_treffer_wird_auch_als_treffer_gemeldet(tmp_path, glb):
    """**Die Mutationsprobe hat diesen Test erzwungen.**

    Der erste Anlauf prüfte die Meldung nur an einem von Hand gebauten Befund. Ein
    Treffer, der sich als «gerechnet» ausgibt, blieb damit grün — und ein Lauf aus dem
    Speicher sähe aus wie ein frisch gerechneter. *Dieselbe Form wie beim Hochachsen-Test
    am selben Tag: Der Wert wird dort geprüft, wo er entsteht, und nicht dort, wo er
    ankommt.*

    Geprüft wird darum über die **volle Kette** mit Attrappen — dieselbe Bauform wie in
    ``test_abholer.py``.
    """
    from test_abholer import _kette

    protokoll, attrappen = _kette(scores=(0.8,))
    cache = graph.ArtefaktCache(tmp_path / "cache")
    szene = {"kameras": "auto", "aufloesung": 64, "hoehe": 64, "samples": 1,
             "prompt": "a house"}

    def lauf(nr):
        verarbeite = abholer.verarbeiter(
            out_wurzel=tmp_path / f"aus{nr}", auto_richtungen=("s",),
            nullprobe=False, seeds=(0,), zwischenspeicher=cache, **attrappen)
        return verarbeite({"modell": glb, "job_id": "vis-1-aaaaaa",
                           "verzeichnis": tmp_path, "szene": dict(szene)})

    erst = lauf(1)
    zweit = lauf(2)

    assert len(protokoll["multipass"]) == 1, (
        f"Der Multipass lief {len(protokoll['multipass'])}-mal — der Speicher greift nicht.")
    assert erst["kameras"][0]["zwischenspeicher"]["treffer"] is False, (
        "Der erste Lauf hat gerechnet und muss das auch sagen.")
    assert zweit["kameras"][0]["zwischenspeicher"]["treffer"] is True, (
        "Der zweite Lauf kam aus dem Speicher und gibt sich als gerechnet aus. Dann "
        "sieht ein Lauf aus dem Speicher aus wie ein frischer — nur schneller, und "
        "niemand weiss warum.")

    zeilen = abholer.befund_kurz(zweit)
    assert any("AUS DEM ZWISCHENSPEICHER" in z for z in zeilen)
    assert not any("AUS DEM ZWISCHENSPEICHER" in z for z in abholer.befund_kurz(erst))


def test_ein_bericht_der_kein_treffer_waere_wird_gar_nicht_erst_abgelegt(tmp_path, glb):
    """Abgelegt wird, was als Treffer taugen würde — dieselbe Prüfung, nicht eine zweite.

    Sonst füllt sich der Speicher mit Einträgen, die nie treffen können, und ein
    gescheiterter Lauf hinterlässt einen Eintrag, der so aussieht, als sei er gelungen.
    """
    cache = graph.ArtefaktCache(tmp_path / "cache")

    def kaputt(glb_pfad, aus, **kw):
        # Ein Lauf, der die Tiefenkarte nicht hinbekommen hat — genau der Fall, in dem
        # ein Eintrag am teuersten wäre (Sitzung 07).
        return {"status": "ok", "blender": "4.2.1 LTS", "depth_png": None}

    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path, auto_richtungen=("s",),
                                     zwischenspeicher=cache, _multipass=kaputt)
    with pytest.raises(Exception):
        verarbeite(_auftrag(tmp_path, glb))
    assert not list((tmp_path / "cache").glob("*.json")), (
        "Ein Bericht, der als Treffer abgelehnt würde, ist abgelegt worden. Der Speicher "
        "füllt sich dann mit Einträgen, die nie greifen — und ein gescheiterter Lauf "
        "hinterlässt einen, der aussieht wie ein gelungener."
    )


def test_die_kurzform_sagt_dass_ein_bild_aus_dem_speicher_kam():
    """Sonst sähe ein Lauf aus dem Speicher genauso aus wie ein gerechneter, nur schneller."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "s", "zwischenspeicher": {"treffer": True, "schluessel": "abc",
                                             "gerechnet_unter": "4.2.1 LTS"}},
        {"kamera": "sSE", "zwischenspeicher": {"treffer": False, "schluessel": "def",
                                               "gerechnet_unter": "4.2.1 LTS"}},
    ]})
    text = " ".join(zeilen)
    assert "AUS DEM ZWISCHENSPEICHER" in text
    assert "1 von 2 Kameras" in text
    assert "4.2.1 LTS" in text


def test_die_kurzform_schweigt_ohne_treffer():
    """Selbstlöschend — der Speicher ist voreingestellt aus, und ohne Treffer gibt es
    nichts zu melden."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "s", "zwischenspeicher": {"treffer": False, "schluessel": "abc"}},
        {"kamera": "sSE"},
    ]})
    assert not any("ZWISCHENSPEICHER" in z for z in zeilen)


def test_der_eintrag_verspricht_genau_die_dateien_aus_dem_bedarf(tmp_path, glb):
    """Nicht eine eigene Liste — `kette.BEDARF` ist die Stelle, an der sie deklariert ist."""
    zaehler: list = []
    cache = graph.ArtefaktCache(tmp_path / "cache")
    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path, auto_richtungen=("s",),
                                     zwischenspeicher=cache,
                                     _multipass=_multipass_zaehler(zaehler, tmp_path))
    with pytest.raises(Exception):
        verarbeite(_auftrag(tmp_path, glb))
    eintraege = list((tmp_path / "cache").glob("*.json"))
    assert len(eintraege) == 1
    inhalt = json.loads(eintraege[0].read_text(encoding="utf-8"))
    versprochen = inhalt.get(graph.ZUSAGEN_FELD) or []
    assert len(versprochen) == len(kette.BEDARF["multipass"].dateien)
