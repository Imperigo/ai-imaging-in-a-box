"""Eine Innenraum-Bestellung aus KosmoOrbit wird angenommen — Befund vom 22.09.2026.

Was gemessen wurde
------------------
KosmoOrbit sendet seit dem 19.09.2026 ``interior: {rooms: "auto"}`` zusammen mit
``geometry.format: "ifc"`` (Antworten auf auf-31 R3 und auf-91 V1, übertragen am
22.09.2026). ``kosmo_szene.BEKANNTE_FELDER`` kannte das Feld nicht; unser Riegel für
unbekannte Felder wies damit **jede** Innenraum-Bestellung ab. Dieselbe Antwort
(auf-104) nannte acht weitere Felder, die in unserer Karte fehlten.

Was diese Datei bewacht, und zwar über den Produktweg
------------------------------------------------------
Ein synthetischer Auftragsordner der Brücke, gelesen von ``bruecke.lies_auftrag``,
abgeholt von ``abholer.hole_einen``, verarbeitet von ``abholer.verarbeiter`` — dieselbe
Bauform wie ``tests/test_vertrag_jede_kamera_spricht.py``. Geprüft wird, was **beim
Multipass ankommt**, nicht, was in einem Wörterbuch steht.

1. ``interior`` ohne mitgesandte Kameras kommt als **eine** Innenansicht am Multipass
   an: Standpunkt im Raum, Blickziel und die Brennweite des Standpunkts (24 mm).
2. ``interior`` mit mitgesandten Kameras wird angenommen; gerendert werden die Kameras,
   ein zweiter Innenstandpunkt wird nicht gerechnet (auf-31 R6).
3. Was an ``interior`` nicht belegt ist, wird mit einem Satz abgewiesen — der Lauf
   startet nicht.
4. Ohne Räume (glb-Modell) scheitert die Innenansicht laut, statt aussen zu rendern.
5. Die sieben übrigen Felder werden je mit **eigenem** Satz abgewiesen, ``null`` nicht.
6. ``gelaende`` erreicht die Bauwerksmaske und schlägt den Schalter des Prozesses.
7. E79 (auf-107): Ein wegen ``idle_window_only`` abgelehnter Lauf bleibt auf ``queued``,
   mit sichtbarem Grund, und wird beim nächsten Durchgang gerechnet.

Was hier NICHT geprüft ist (und nicht geprüft werden kann): Die Räume kommen aus einer
Attrappe für den Raumleser, der im Betrieb ein Unterprozess im ``.venv-ifc`` ist — so wie
Multipass und Render Attrappen sind. Und das Modell im Ordner ist eine glb, obwohl die
Bestellung ``ifc`` sagt: ``bruecke.lies_auftrag`` sucht heute nur ``model.glb``.

Regel 3: Raum, Kameras und Modell sind synthetisch.
"""
from __future__ import annotations

import json

import pytest

from aiimaging import abholer, bruecke, kosmo_szene, raumkamera

from test_abholer import _auftrag, _kette

#: Ein Raum wie aus ``tools/make_test_ifc.py --raeume`` — synthetisch, kein Projekt.
RAUM = {"name": "Raum-Sued", "z_unten_m": 0.1, "hoehe_m": 2.4,
        "grundriss_m": [[7.7, 0.3], [7.7, 2.5], [5.0, 2.5], [5.0, 0.3]]}


def _raeume(_modell=None) -> dict:
    """Die Raumliste in der Form von ``kette._raeume_lesen``."""
    return {"status": "ok", "grund": "",
            "raeume": [{"raum": RAUM, "kamera": raumkamera.standpunkte(RAUM)}]}


def _szene(**zusatz) -> dict:
    szene = {
        "schema": kosmo_szene.SCHEMA_SZENE,
        "geometry": {"path": "model.ifc", "format": "ifc"},
        "cameras": "auto",
        "interior": {"rooms": "auto"},
        "render": {"resolution": [512, 512], "samples": 64, "faithful": 0.8},
        "style": {"prompt": "ein Raum"},
        "vis": {"backbone": "qwen"},
    }
    szene.update(zusatz)
    return szene


def _lauf(tmp_path, szene, **einstellungen):
    """Durch den Produktweg; zurück kommen Antwort, Protokoll der Attrappen, Ordner."""
    ordner = _auftrag(tmp_path, szene=szene)
    protokoll, attrappen = _kette()
    attrappen.update(einstellungen)
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                       **attrappen))
    return antwort, protokoll, ordner


# --------------------------------------------------------------------------------------
# 1 · Die Innenansicht kommt am Multipass an
# --------------------------------------------------------------------------------------

def test_eine_bestellung_mit_interior_kommt_als_innenansicht_am_multipass_an(tmp_path):
    """**Der Wächter dieses Befundes.** Vor dem 22.09.2026 blieb dieser Auftrag liegen:
    «Unbekannte Felder in der Bestellung: interior»."""
    antwort, protokoll, _ = _lauf(tmp_path, _szene(), _raeume=_raeume)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(protokoll["multipass"]) == 1, (
        "je Auftrag genau EINE Innenansicht (auf-91 V5) — und keine Aussenrichtungen dazu")
    kw = protokoll["multipass"][0]
    erwartet = raumkamera.waehle(_raeume(), raum=None)["standpunkt"]

    assert kw["kamera"] is None, "kein Richtungskuerzel neben dem Standpunkt"
    assert kw["auge"] == list(erwartet["auge"])
    assert kw["blick_auf"] == list(erwartet["blick_auf"])
    assert raumkamera.ist_innen(kw["auge"][:2], RAUM["grundriss_m"]), (
        "das Auge steht im Raum")
    # Die Brennweite des Standpunkts, nicht der Rueckfall des Runners (50 mm).
    assert kw["brennweite"] == erwartet["sichtfeld"]["brennweite_mm"]
    assert kw["brennweite"] == raumkamera.BRENNWEITE_INNEN_MM


def test_ohne_interior_bleibt_es_bei_den_aussenrichtungen(tmp_path):
    """Die Gegenprobe: Dieselbe Bestellung ohne ``interior`` rechnet die drei
    Aussenrichtungen wie bisher und fragt keinen Raumleser."""
    szene = _szene(geometry={"path": "model.glb", "format": "glb"})
    del szene["interior"]

    def nie(_modell):
        raise AssertionError("ohne Innenbestellung wird kein Raum gelesen")

    antwort, protokoll, _ = _lauf(tmp_path, szene, _raeume=nie)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert [kw["kamera"] for kw in protokoll["multipass"]] == list(abholer.AUTO_RICHTUNGEN)
    assert all(kw["auge"] is None for kw in protokoll["multipass"])


def test_interior_ist_eine_bekannte_und_gelesene_bestellung():
    """An der Naht selbst: kein Mangel, und die Innenansicht steht in der Szene."""
    gelesen = kosmo_szene.lies_szene(_szene())

    assert gelesen["maengel"] == ()
    assert gelesen["innenraum"] == {"raum": None, "art": raumkamera.ART_FRONTAL}
    assert "innenraum" in kosmo_szene.DURCHGEREICHT


# --------------------------------------------------------------------------------------
# 2 · Mitgesandte Kameras gehen vor — kein zweiter Innenstandpunkt
# --------------------------------------------------------------------------------------

def test_mit_mitgesandten_kameras_werden_genau_diese_gerendert(tmp_path):
    """So sendet KosmoOrbit heute (auf-91): benannte Kameras UND ``interior``."""
    kameras = [{"name": "Innen-1", "position": [6.0, 1.0, 1.6],
                "target": [6.0, 2.4, 1.6], "fov": 70, "up_axis": "z"}]

    def nie(_modell):
        raise AssertionError("die Standpunkte kamen mit — kein Raum zu lesen")

    antwort, protokoll, _ = _lauf(tmp_path, _szene(cameras=kameras), _raeume=nie)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(protokoll["multipass"]) == 1
    assert protokoll["multipass"][0]["auge"] == (6.0, 1.0, 1.6)
    assert any("KEINEN zweiten Innenstandpunkt" in w for w in antwort["warnungen"]), (
        "dass interior hier ueber die Kameras bedient wird, steht in der Antwort")


# --------------------------------------------------------------------------------------
# 3 · Was an `interior` nicht belegt ist, wird abgewiesen
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("interior, stichwort", [
    ({"rooms": ["Raum-Sued"]}, "interior.rooms"),
    ({}, "interior.rooms"),
    ("auto", "kein Block"),
    ({"rooms": "auto", "view": "corner"}, "interior.view"),
])
def test_eine_unbelegte_form_haelt_den_lauf_auf(tmp_path, interior, stichwort):
    ordner = _auftrag(tmp_path, szene=_szene(interior=interior))

    def nie(auftrag):
        raise AssertionError("eine abgewiesene Bestellung wird nicht gerechnet")

    antwort = abholer.hole_einen(ordner, verarbeite=nie, fremde_freigabe_gilt=True)

    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    assert stichwort in antwort["grund"]


def test_interior_ohne_ifc_wird_abgewiesen():
    """Räume gibt es nur in der IFC; eine glb-Bestellung mit ``interior`` kann nicht
    geliefert werden und wird darum nicht angenommen."""
    gelesen = kosmo_szene.lies_szene(
        _szene(geometry={"path": "model.glb", "format": "glb"}))

    assert gelesen["innenraum"] is None
    assert any("nur in einer IFC" in m for m in gelesen["maengel"])


def test_interior_null_ist_keine_bestellung():
    gelesen = kosmo_szene.lies_szene(_szene(interior=None))

    assert gelesen["maengel"] == ()
    assert gelesen["innenraum"] is None


# --------------------------------------------------------------------------------------
# 4 · Ohne Räume: laut scheitern, nicht aussen rendern
# --------------------------------------------------------------------------------------

def test_ohne_raeume_scheitert_die_innenansicht_laut(tmp_path):
    """Der Raumleser ohne Attrappe: Das Modell im Ordner ist eine glb, aus der sich kein
    Raum gewinnen lässt. Es darf kein Multipass laufen, und der Grund steht da."""
    antwort, protokoll, ordner = _lauf(tmp_path, _szene())

    assert antwort["tat"] == abholer.TAT_FEHLER
    assert "kein Standpunkt" in antwort["grund"]
    assert protokoll["multipass"] == [], "nicht ersatzweise aussen gerendert"
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel["status"] == bruecke.STATUS_ERROR


# --------------------------------------------------------------------------------------
# 5 · Die übrigen Felder: je mit eigenem Satz abgewiesen
# --------------------------------------------------------------------------------------

def _mit_feld(pfad: str, wert) -> dict:
    szene = _szene()
    del szene["interior"]
    szene["geometry"] = {"path": "model.glb", "format": "glb"}
    block, _, name = pfad.rpartition(".")
    if block:
        szene[block] = dict(szene.get(block) or {}, **{name: wert})
    else:
        szene[name] = wert
    return szene


@pytest.mark.parametrize("pfad", sorted(kosmo_szene.ABGEWIESENE_FELDER))
def test_ein_bekanntes_abgewiesenes_feld_haelt_den_lauf_mit_eigenem_satz_auf(pfad):
    gelesen = kosmo_szene.lies_szene(_mit_feld(pfad, {"irgendwas": 1}))

    treffer = [m for m in gelesen["maengel"] if f"'{pfad}'" in m]
    assert len(treffer) == 1, gelesen["maengel"]
    assert "Unbekannte Felder" not in " ".join(gelesen["maengel"]), (
        "ein Feld, das wir kennen, wird nicht als unbekannt gemeldet")


@pytest.mark.parametrize("pfad", sorted(kosmo_szene.ABGEWIESENE_FELDER))
def test_ein_abgewiesenes_feld_auf_null_verlangt_nichts(pfad):
    assert kosmo_szene.lies_szene(_mit_feld(pfad, None))["maengel"] == ()


def test_die_neun_felder_der_antwort_sind_alle_eingeordnet():
    """Die neun Felder aus auf-104: jedes bedient oder mit Satz abgewiesen — keines mehr
    als «unbekannt», und keines still abgestreift."""
    neun = {"interior", "innenansichten", "gelaende", "komposition", "render.environment",
            "render.himmel", "render.belichtung", "render.rauschschwelle",
            "vis.research_only"}
    bedient = {"interior", "gelaende"}

    assert neun - bedient == set(kosmo_szene.ABGEWIESENE_FELDER)
    for pfad in neun:
        assert kosmo_szene.unbekannte_felder(_mit_feld(pfad, None)) == (), pfad


# --------------------------------------------------------------------------------------
# 6 · `gelaende` erreicht die Bauwerksmaske
# --------------------------------------------------------------------------------------

def _maskenbefund(tmp_path, gelaende, **einstellungen) -> dict:
    szene = _mit_feld("gelaende", gelaende)
    szene["cameras"] = [{"name": "s", "position": [0, -20, 1.3], "target": [0, 0, 1.3],
                         "fov": 60, "up_axis": "z"}]
    antwort, _, _ = _lauf(tmp_path, szene, **einstellungen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    urteil = json.loads((tmp_path / "aus" / "vis-1787123048-098c6e" / "s"
                         / abholer.DATEI_URTEIL).read_text(encoding="utf-8"))
    return urteil["urteil"]["maskenbefund"]


#: Der Satz der Maske, wenn jemand «kein Gelaende» erklaert hat und die Regel doch
#: welches findet — die Attrappe fuehrt `Boden_Platte`, und die Regel ordnet sie als
#: Gelaende ein. Er erscheint GENAU DANN, wenn `gelaende_erwartet=False` die Maske
#: erreicht hat.
ERKLAERT_KEIN_GELAENDE = "Der Aufrufer hat erklärt, diese Szene enthalte kein Gelände"


def _erklaert(befund: dict) -> bool:
    return any(ERKLAERT_KEIN_GELAENDE in w for w in befund["warnungen"])


def test_gelaende_false_der_bestellung_erreicht_die_maske(tmp_path):
    """Ohne Angabe gilt der Schalter des Prozesses (Vorgabe: Gelaende erwartet); sagt die
    Bestellung ``gelaende: false``, kommt genau das bei der Maske an."""
    ohne_angabe = _maskenbefund(tmp_path / "a", None)
    bestellt = _maskenbefund(tmp_path / "b", False)

    assert not _erklaert(ohne_angabe), "Vorbedingung: ohne Angabe erklaert niemand etwas"
    assert _erklaert(bestellt)


def test_gelaende_true_der_bestellung_schlaegt_den_schalter_des_prozesses(tmp_path):
    """Der Schalter ``--kein-gelaende`` gilt prozessweit; die Bestellung je Szene."""
    schalter = _maskenbefund(tmp_path / "a", None, gelaende_erwartet=False)
    bestellt = _maskenbefund(tmp_path / "b", True, gelaende_erwartet=False)

    assert _erklaert(schalter), "Vorbedingung: der Schalter wirkt"
    assert not _erklaert(bestellt)


def test_ein_undeutbares_gelaende_wird_abgewiesen():
    gelesen = kosmo_szene.lies_szene(_mit_feld("gelaende", "ja"))

    assert any("'gelaende'" in m for m in gelesen["maengel"])
    assert gelesen["gelaende_erwartet"] is None


# --------------------------------------------------------------------------------------
# 7 · E79: ein abgelehnter Lauf bleibt in der Warteschlange, mit Grund
# --------------------------------------------------------------------------------------

def test_ein_wegen_idle_window_only_abgelehnter_lauf_bleibt_wartend_mit_grund(tmp_path):
    """E79 drüben (21.09.2026, Antwort auf auf-107 V4): Ein abgelehnter Lauf soll in der
    Warteschlange BLEIBEN, mit sichtbarem Grund — nicht zurückkommen. Und er wird
    gerechnet, sobald die Auskunft es erlaubt."""
    ordner = _auftrag(tmp_path, idle_only=True)

    def nie(auftrag):
        raise AssertionError("bei nein wird nicht gerechnet")

    erster = abholer.durchgang(tmp_path, verarbeite=nie, fremde_freigabe_gilt=True,
                               darf_rechnen=lambda: (False, "ein anderer Render laeuft"))
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))

    assert erster["liegengelassen"] == 1
    assert zettel["status"] == bruecke.STATUS_QUEUED, "nicht zurueckgeschickt"
    assert "ein anderer Render laeuft" in zettel[bruecke.FELD_MELDUNG]

    zweiter = abholer.durchgang(tmp_path, verarbeite=lambda a: {"bilder": []},
                                fremde_freigabe_gilt=True,
                                darf_rechnen=lambda: (True, ""))
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))

    assert zweiter["verarbeitet"] == 1
    assert zettel["status"] == bruecke.STATUS_DONE
    assert not zettel.get(bruecke.FELD_MELDUNG), "der Grund von vorhin ist weg"
