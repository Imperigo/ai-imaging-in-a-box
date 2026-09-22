"""Die Innenansicht war gerechnet, aber nicht bestellbar — Befund vom 22.09.2026.

Was gemessen wurde
------------------
``kette._fuehre_multipass`` wertet die Angabe ``innenraum`` aus und lässt
``raumkamera.waehle`` daraus Auge, Blickziel und die gemessene 24-mm-Brennweite rechnen.
``kette.baue_kette`` nahm sie nicht entgegen. Die Innenansicht war damit nur erreichbar,
wenn jemand den Multipass-Knoten von Hand zusammensetzte.

Über das Produkt gab es sie gar nicht: Die Oberfläche gewinnt ihre Bedienfelder aus der
Signatur von ``baue_kette``; was dort nicht steht, kann niemand bestellen.

    *Eine Naht, die nur der direkte Aufrufer erreicht, gibt es für den Weg nicht, den das
    Produkt wirklich geht.*

Es ist dieselbe Fehlerart wie am 21.09.2026, als elf Kameraangaben über einen der beiden
Wege nicht bestellbar waren — eine Ebene tiefer.

Bestellbar ist noch nicht lieferbar (Durchsicht 22.09.2026)
------------------------------------------------------------
Räume gibt es nur beim Einstieg über ``ifc_path``. Der Weg über die Projektmappe baut
immer aus der umgewandelten glb — dort ist ``raeume`` ``None``. Über die Fläche ist die
Innenansicht damit seit heute **bestellbar, aber nicht lieferbar**: Jeder Lauf endet im
Fehlerknoten. Die Probe 1 unten bewacht darum den **Bibliotheksweg** (``baue_kette``
mit den Räumen, die der IFC-Einstieg liefert), nicht den Weg der Fläche; die Proben 5
und 6 halten fest, dass der glb-Weg laut scheitert statt aussen zu rendern.

Warum diese Proben
------------------
1. **Die Bestellung kommt an** — auf dem Bibliotheksweg. Nicht nur als Eintrag im
   Knoten: Der gebaute Knoten wird durch den Ausführer geschickt, und geprüft wird, was
   beim Runner ankommt — ein Standpunkt im Raum. Die Räume werden dabei so eingereicht,
   wie der IFC-Einstieg sie liefert. *Ein Wächter, der nur nachsieht, ob ein Wort im
   Knoten steht, bewacht eine Schreibweise.*
2. **Ohne Bestellung ändert sich nichts.** ``None`` heisst in dieser Gruppe NICHT
   ANGEFASST. Stünde die Angabe auch ungefragt im Knoten, hätte jede früher gemessene
   Aufnahme einen anderen Hash — und der Zwischenspeicher wäre für alle bisherigen Läufe
   wertlos.
3. **Zwei Bestellungen, zwei Hashes.** Sonst wäre die Aufnahme aus dem einen Raum ein
   Zwischenspeicher-Treffer für die Bestellung des anderen.
4. **Der Weg der Oberfläche.** Geprüft wird die Wirkung: dass die Feldliste, die die
   Fläche wirklich baut, die Angabe enthält und sie dem Multipass-Knoten zuordnet. Der
   Quelltext der Fläche wird dabei nicht gelesen — er wird ausgeführt.
5. **Über den glb-Einstieg scheitert die Bestellung laut.** Die ganze Kette läuft über
   die echten Ausführer von Geometrie und Multipass; es darf nicht gerendert werden, und
   der Fehler muss sagen, warum.
6. **Zwei Standpunktquellen über** ``baue_kette`` **werden abgewiesen** — die Zusage des
   Docstrings, bisher nur am handgebauten Knoten belegt.

Ohne Blender, ohne GPU: Der Runner wird abgefangen. Die glb ist in den Proben 1–4 ein
Pfad und keine Datei, in 5 und 6 eine synthetische Szene aus ``tools/make_test_glb.py``.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from aiimaging import graph, kette, raumkamera
from aiimaging.kette import KNOTEN_MULTIPASS

WURZEL = Path(__file__).resolve().parents[1]

#: Der Raum aus ``tools/make_test_ifc.py --raeume``, wie ihn der Raumleser liefert —
#: synthetisch erzeugt, kein echtes Projekt (Regel 3).
RAUM_SUED = {"name": "Raum-Sued", "z_unten_m": 0.1, "hoehe_m": 2.4,
             "grundriss_m": [[7.7, 0.3], [7.7, 2.5], [5.0, 2.5], [5.0, 0.3]]}


def _raeume() -> dict:
    return {"status": "ok",
            "raeume": [{"raum": RAUM_SUED, "kamera": raumkamera.standpunkte(RAUM_SUED)}]}


def _kette(**angaben):
    """Die Kette über den Produktweg bauen — glb-Eingang, damit keine Konversion läuft."""
    return kette.baue_kette(glb_path="haus.glb", up_axis="Y", prompt="Abendlicht",
                            **angaben)


# ------------------------------------------------------------------ 1 · Die Bestellung

def test_eine_ueber_baue_kette_bestellte_innenansicht_erreicht_den_standpunkt(
        monkeypatch, tmp_path):
    """**Bestellt über** ``baue_kette``, **angekommen am Runner** — der Bibliotheksweg.

    Die Räume werden so eingereicht, wie der IFC-Einstieg sie liefert. Über die
    Projektmappe gibt es sie heute nicht (siehe Modulkopf und Probe 5).

    Nicht geprüft wird, ob ein Wort im Knoten steht — sondern ob aus der Bestellung ein
    Standpunkt IM Raum wird. Auf halber Raumhöhe (0,1 m + 2,4 m / 2 = 1,3 m), waagrecht,
    und mit der 24-mm-Brennweite statt des 50-mm-Rückfalls des Runners.
    """
    gesehen = {}

    def falscher_runner(glb, out, **kw):
        gesehen.update(kw)
        return {"status": "ok", "depth_exr": str(tmp_path / "t.exr"),
                "depth_png": str(tmp_path / "t.png")}

    monkeypatch.setattr(kette.seams, "glb_zu_multipass", falscher_runner)

    bestellt = _kette(innenraum={"raum": "Raum-Sued", "art": raumkamera.ART_FRONTAL})
    kette.AUSFUEHRER[kette.ART_MULTIPASS](
        knoten=bestellt.knoten[KNOTEN_MULTIPASS],
        eingaben=[{"glb_path": "haus.glb", "up_axis": "Y", "raeume": _raeume()}],
        out_dir=tmp_path)

    assert gesehen.get("auge") is not None, (
        "die über baue_kette bestellte Innenansicht kommt am Runner gar nicht an")
    assert gesehen["auge"][2] == pytest.approx(1.3), "halbe Raumhöhe ab z_unten"
    assert gesehen["auge"][2] == pytest.approx(gesehen["blick_auf"][2]), "Kamera waagrecht"
    assert gesehen.get("brennweite") == pytest.approx(raumkamera.BRENNWEITE_INNEN_MM), (
        "ohne die gemessene Brennweite gilt drüben der 50-mm-Rückfall — und die "
        "Tiefenkarte trägt dann einen einzigen Wert (gemessen 09.09.2026)")


def test_die_bestellung_steht_im_knoten_und_damit_im_hash():
    """Zwei verschiedene Räume müssen zwei verschiedene Bestellungen sein.

    Stünde die Angabe nicht im Knoten, wäre eine Aufnahme aus der Küche ein Treffer für
    eine Bestellung aus dem Wohnraum — der Lauf gelänge, das Bild läge da, und niemand
    sähe ihm an, dass etwas anderes bestellt war.
    """
    sued = _kette(innenraum={"raum": "Raum-Sued"})
    kueche = _kette(innenraum={"raum": "Kueche"})

    assert sued.knoten[KNOTEN_MULTIPASS].params["innenraum"] == {"raum": "Raum-Sued"}
    assert (sued.knoten[KNOTEN_MULTIPASS].params
            != kueche.knoten[KNOTEN_MULTIPASS].params), \
        "zwei Bestellungen, zwei Parametersätze"


# ------------------------------------------------------------ 2 · Ohne Bestellung nichts

def test_ohne_die_angabe_bleibt_der_graph_derselbe():
    """``None`` heisst NICHT ANGEFASST — und nicht »keine Innenansicht bestellt«.

    Eine Angabe, die auch ungefragt im Knoten stünde, änderte den Hash jeder bisher
    gemessenen Aufnahme. Der Zusatz ist rein additiv, und diese Probe hält das fest.
    """
    ohne = _kette()
    ausdruecklich_nicht = _kette(innenraum=None)

    assert "innenraum" not in ohne.knoten[KNOTEN_MULTIPASS].params, \
        "nicht bestellt heisst NICHT ANGEFASST — dann gilt die Vorgabe des Runners"
    assert ohne == ausdruecklich_nicht, (
        "ein ausdrückliches None darf keinen anderen Graphen ergeben als gar nichts")
    assert (graph.inhalts_hash(ohne.knoten[KNOTEN_MULTIPASS], [])
            == graph.inhalts_hash(ausdruecklich_nicht.knoten[KNOTEN_MULTIPASS], [])), \
        "gleicher Knoten, gleicher Zwischenspeicher — sonst rechnet jeder alte Lauf neu"


# ---------------------------------------------------------- 3 · Der Weg der Oberfläche

@pytest.fixture(scope="module")
def flaeche():
    """Die Oberfläche als Modul — sie wird gelesen, nicht gestartet.

    Der Kern importiert sie nie (Regel 4); hier ist die Richtung umgekehrt, und genau
    darum lässt sich an ihr prüfen, was der Benutzer wirklich angeboten bekommt.
    """
    sys.path.insert(0, str(WURZEL / "oberflaeche"))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(WURZEL / "oberflaeche"))


def test_die_innenansicht_steht_in_der_feldliste_der_flaeche(flaeche):
    """**Geprüft an der Wirkung: die Liste, die die Fläche baut — nicht ihr Quelltext.**

    Die Fläche zählt ihre Felder nicht auf, sie liest sie aus ``baue_kette``. Was dort
    nicht steht, gibt es für den Benutzer nicht; wer es trotzdem schickt, bekommt
    »Diese Einstellung kennt das Programm nicht«.

    Zusätzlich geprüft wird die **Zuordnung**: Die Angabe muss beim Multipass-Knoten
    landen. Ein Feld, das die Fläche anbietet und keinem Knoten zuordnen kann, steht dort
    ohne Auskunft darüber, was es überhaupt anfasst.
    """
    einstellungen = {"prompt": "Abendlicht", "up_axis": "Y"}
    gebaut = kette.baue_kette(glb_path="haus.glb", **einstellungen)
    felder = {f["name"]: f for f in
              flaeche.bedienfelder(einstellungen, gebaut, "haus.glb")}

    assert "innenraum" in felder, (
        "die Fläche bietet die Innenansicht nicht an — über das Produkt gibt es sie dann "
        "nicht, und niemand sieht es, weil nichts kaputtgeht, sondern nur fehlt")
    assert felder["innenraum"]["vorgabe"] is None, "nicht bestellt ist die Vorgabe"
    assert felder["innenraum"]["gesetzt"] is False
    assert felder["innenraum"]["knoten"] == KNOTEN_MULTIPASS, (
        "die Probe der Fläche findet nicht, wo die Angabe wirkt")


# ------------------------------------------------- 5 · Bestellbar ist nicht lieferbar

#: Bauwerk 12 × 9 × 15 m auf einer Geländeplatte — synthetisch, in glTF-Koordinaten.
SZENE = (
    ("IfcSlab_Gelaende_0aBcDeFgHiJkLmNoPqRsTu", (-14.0, -0.5, -12.0), (26.0, 0.0, 18.0)),
    ("IfcWall_Aussenwand_1aBcDeFgHiJkLmNoPqRsT", (0.0, 0.0, 0.0), (12.0, 15.0, 9.0)),
)


@pytest.fixture
def szene_glb(tmp_path):
    werkzeug = WURZEL / "tools" / "make_test_glb.py"
    spez = importlib.util.spec_from_file_location("make_test_glb_fuer_innenraum", werkzeug)
    modul = importlib.util.module_from_spec(spez)
    sys.modules[spez.name] = modul
    spez.loader.exec_module(modul)
    pfad = tmp_path / "szene.glb"
    pfad.write_bytes(modul.baue_glb(SZENE))
    return pfad


def _lauf_ueber_den_glb_einstieg(glb, tmp_path, monkeypatch, **angaben):
    """Die ganze Kette, Geometrie und Multipass mit ihren echten Ausführern.

    Gerendert werden darf nicht: Der Runner wirft, und die Bildstufe ebenfalls.
    """
    def darf_nicht_rendern(*args, **kw):
        raise AssertionError("es darf gar nicht erst gerendert werden")

    monkeypatch.setattr(kette.seams, "glb_zu_multipass", darf_nicht_rendern)
    tabelle = {**kette.AUSFUEHRER,
               kette.ART_RENDER: lambda **kw: darf_nicht_rendern(),
               kette.ART_QA: lambda **kw: darf_nicht_rendern()}
    gebaut = kette.baue_kette(glb_path=str(glb), up_axis="Y", prompt="Abendlicht",
                              **angaben)
    return kette.fuehre_aus(gebaut, ausfuehrer=tabelle, out_dir=tmp_path / "out")


def test_ueber_den_glb_einstieg_scheitert_die_innenansicht_laut(tmp_path, monkeypatch,
                                                                 szene_glb):
    """**Der Weg, den die Projektmappe geht: bestellbar, aber nicht lieferbar.**

    Die Geometrie muss durchkommen — sonst prüfte diese Probe einen anderen Fehler. Danach
    muss der Multipass-Knoten mit der ehrlichen Begründung stehen bleiben, und es darf
    nicht ersatzweise eine Aussenaufnahme entstehen: *Wer innen bestellt und aussen
    bekommt, sieht es dem Ergebnis nicht an.*
    """
    ergebnis = _lauf_ueber_den_glb_einstieg(
        szene_glb, tmp_path, monkeypatch, innenraum={"raum": "Raum-Sued"})

    geometrie = ergebnis["knoten"][kette.KNOTEN_GEOMETRIE]
    assert geometrie["status"] == kette.STATUS_OK, geometrie.get("error")
    assert geometrie["ausgaben"]["raeume"] is None, "aus einer glb gibt es keine Räume"

    multipass = ergebnis["knoten"][KNOTEN_MULTIPASS]
    assert multipass["status"] == kette.STATUS_FEHLER
    fehler = multipass["error"] or multipass["ausgaben"].get("error") or ""
    assert "Innenansicht verlangt" in fehler, fehler


def test_zwei_standpunktquellen_ueber_baue_kette_werden_abgewiesen(tmp_path, monkeypatch,
                                                                   szene_glb):
    """Die Zusage des Docstrings, über den Weg, auf dem sie gemacht wird.

    ``innenraum`` und ``auge`` zugleich: abgewiesen, nicht geordnet — und zwar auch dann,
    wenn beide über ``baue_kette`` kommen und nicht von Hand an den Knoten gesetzt sind.
    """
    ergebnis = _lauf_ueber_den_glb_einstieg(
        szene_glb, tmp_path, monkeypatch,
        innenraum={"raum": "Raum-Sued"}, auge=[1.0, 2.0, 3.0])

    multipass = ergebnis["knoten"][KNOTEN_MULTIPASS]
    assert multipass["status"] == kette.STATUS_FEHLER
    fehler = multipass["error"] or multipass["ausgaben"].get("error") or ""
    assert "zweimal bestellt" in fehler, fehler
