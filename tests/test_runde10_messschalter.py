"""Zwei Messschalter fuer die Tiefenkarte — Vorgabe aus, und aus heisst bitgleich (23.09.2026).

Der Anlass
----------
Auf der HomeStation folgte ein Endbild der Tiefe nicht (``auf-137`` V3: score 0,000,
rho +0,037). Ein Verdrahtungsfehler fand sich nicht. Die wahrscheinlichste Ursache liegt
in unserer Aufbereitung: ``bildschreiben.normalisiere_tiefe`` gibt dem ENTFERNTESTEN
Geometriepixel denselben Grauwert wie dem Hintergrund (0). Fuer z-image wird die Karte vor
dem Bildmodell umgedreht — dann sind beide 255. Bei einem freistehenden Quader
verschwindet so dessen Rueckkante im Hintergrund; mit Bodenplatte ist das Fernste der
Boden, und das faellt nicht auf.

Die Schalter
------------
* ``ferne_abstand`` legt die Geometrie auf ``[a, 1]`` statt ``[0, 1]``; der Hintergrund
  bleibt 0. Die Normierung traegt den Abstand, und jeder Leser rechnet dieselben Meter
  zurueck.
* ``tiefe_invertieren`` ueberschreibt das Register (``None`` = Register). Das Ergebnis sagt,
  ob und womit.

Ob einer davon die Steuerung verbessert, ist NICHT gemessen — dafuer sind sie da.

Was hier bewacht wird
---------------------
(a) Ohne Schalter ist das PNG bitgleich zu vorher, und die Aufrufe unterwegs sind es auch.
(b) Mit Abstand liegt das fernste Geometriepixel ueber dem Hintergrund — auch nach der
    8-Bit-Umrechnung und der Umkehrung, die das Bildmodell wirklich sieht —, und die
    Tiefenordnung bleibt.
(c) Die Rueckrechnung ergibt mit und ohne Abstand dieselben Meter.
(d) ``tiefe_invertieren`` kommt bis zum Bild, das die Pipeline als ``control_image`` sieht,
    und steht im Ergebnis.
(e) Ueber die Kette und ueber die Mappe kommen beide an.

Ohne Blender, ohne GPU, ohne Gewichte: Die EXR ist synthetisch (``schreibe_exr`` aus
tests/test_bildlesen.py), die Pipeline eine Attrappe, Pillow und numpy echt (Dev-Abhaengig-
keiten, siehe ``pyproject.toml``).
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import warnings
from pathlib import Path

import pytest

from aiimaging import (
    arbeitsgang, backbone, bildlesen, bildschreiben, graph, kette, render, seams,
)
from aiimaging.bildschreiben import normalisiere_tiefe, tiefe_exr_zu_png
from aiimaging.kette import (
    ART_GEOMETRIE, ART_MULTIPASS, ART_NACHRENDER, ART_RENDER, KNOTEN_MULTIPASS,
    KNOTEN_RENDER,
)

from test_bildlesen import schreibe_exr
from test_render import Pipelineattrappe, _Torchattrappe

B, H = 16, 12
HIMMEL = 1.0e10


def quader(*, boden: bool = False) -> list[float]:
    """Ein freistehender Quader, 16 x 12, Rueckkante rechts unten am weitesten weg.

    Mit ``boden`` eine Platte darunter, die dann das Fernste ist — der Fall, in dem die
    Steuerung frueher gut war (auf-92, auf-96). Synthetisch (Regel 3)."""
    werte = []
    for y in range(H):
        for x in range(B):
            if 3 <= x <= 12 and 2 <= y <= 8:
                werte.append(8.0 + 0.25 * x + 0.1 * y)
            elif boden and y >= 9:
                werte.append(14.0 + 0.5 * y + 0.01 * x)
            else:
                werte.append(HIMMEL)
    return werte


#: Das Fernste des Quaders: x = 12, y = 8.
FERN = 8 * B + 12
#: Ein Hintergrundpunkt.
LEER = 0


def _leser(werte):
    return lambda _pfad: (list(werte), B, H)


def _stufen(pfad) -> tuple:
    """Die Pixel als ganze Stufen samt Kopf — unabhaengig davon, wie zlib packt."""
    grau, breite, hoehe, tiefe = bildlesen._png_lesen(pfad)
    n = (1 << tiefe) - 1
    return breite, hoehe, tiefe, [round(g * n) for g in grau]


def _hash(obj) -> str:
    return hashlib.sha256(obj.encode() if isinstance(obj, str) else obj).hexdigest()


# ======================================================================================
# (a) Ohne Schalter: bitgleich
# ======================================================================================

#: Mit dem Stand VOR dem Messschalter aufgenommen (Commit 8c02410, 23.09.2026, derselbe
#: Aufruf): Pixelstufen samt Kopf, und die Normierung als JSON. Die Pixel werden
#: dekodiert verglichen und nicht als Dateibytes — zlib darf auf einer anderen Maschine
#: anders packen, ohne dass sich ein Pixel aendert.
SCHNAPPSCHUSS = {
    "quader": ({}, "20078938f83df91050becb6e9f551857409d88a873c6bb9a658c2872563124f6",
               "d7d0f069507f33cf03455f2bb0458b83570a6c7c243eaa1c7ab0ebf1c68d2261"),
    "boden": ({}, "59c17677694562021d603c60835699e28edbda68f08dcb3f646b0d7aa824ef5e",
              "1a1f0cf5db80d02c8f7d3c653d1afad32d9ee7fb0c4ec34437c171b12a904d7b"),
    "quader8": ({"bittiefe": 8},
                "58dc8af7bbdea612ec0b6cb28e8ec79884db60a6979a0f953888aaabc658154f",
                "c7ab6becd520aa4ed1b33c1dfc4ed9926f1c337311890f99128922c2db3b4560"),
}


def _szene(name):
    return quader(boden=(name == "boden"))


@pytest.mark.parametrize("name", sorted(SCHNAPPSCHUSS))
@pytest.mark.parametrize("aus", [{}, {"ferne_abstand": None}, {"ferne_abstand": 0},
                                 {"ferne_abstand": 0.0}])
def test_ohne_abstand_ist_die_tiefenkarte_bitgleich_zu_vorher(tmp_path, name, aus):
    """**Die Probe, die die HomeStation schuetzt.** Sie faehrt diesen Code nach einem
    ``git pull`` aus unserem Repo; was sie nicht bestellt hat, darf sich nicht aendern —
    weder ein Pixel noch ein Feld der Normierung."""
    kw, pixel, normierung = SCHNAPPSCHUSS[name]
    ziel = tmp_path / "t.png"
    norm = tiefe_exr_zu_png("x.exr", ziel, _leser=_leser(_szene(name)), **kw, **aus)

    assert _hash(repr(_stufen(ziel))) == pixel, "ein Pixel hat sich geaendert"
    assert _hash(json.dumps(norm, sort_keys=True)) == normierung, (
        "die Normierung hat sich geaendert")
    assert "ferne_abstand" not in norm and "grau_boden" not in norm


def test_mit_ferne_trennen_allein_bleibt_das_png_bitgleich(tmp_path):
    """Der Boden ist jetzt EINE Variable fuer beide Schalter. Das darf den alten Schalter
    nicht um ein Pixel verschieben (aufgenommen vor der Aenderung, wie oben)."""
    ziel = tmp_path / "t.png"
    werte = [2.0, 4.0, 6.0, 8.0, 500.0, 600.0] + [HIMMEL] * (B * H - 6)
    norm = tiefe_exr_zu_png("x.exr", ziel, _leser=_leser(werte), ferne_trennen=True)
    assert norm["ferne_getrennt"] is True, "sonst prueft die Probe nichts"
    assert _hash(repr(_stufen(ziel))) == (
        "0e4e6202e431db18b1720e52be4c8f8d7521099ce1513669bdc1d9d7ea59540e")


def _bau(glb_path="m.glb", **kw):
    return kette.baue_kette(glb_path=str(glb_path), up_axis="Y", prompt="Haus",
                            bbox=[[0, 0, 0], [8, 5, 3]], **kw)


def _glb_datei(tmp_path) -> Path:
    """Der Geometrie-Knoten hasht seine Eingangsdatei — sie muss da sein. Inhalt egal:
    Die Geometriestufe ist hier eine Attrappe."""
    pfad = tmp_path / "m.glb"
    pfad.write_bytes(b"glb")
    return pfad


@pytest.mark.parametrize("aus", [{"ferne_abstand": None, "tiefe_invertieren": None},
                                 {"ferne_abstand": 0}, {"ferne_abstand": 0.0}])
def test_ohne_schalter_bleibt_der_graph_samt_hash_der_alte(aus):
    """Nicht angefasst heisst: kein Eintrag im Knoten, derselbe Hash — jeder gemessene
    Lauf bleibt ein Zwischenspeicher-Treffer."""
    vorher, nachher = _bau(), _bau(**aus)
    for kid, knoten in vorher.knoten.items():
        assert nachher.knoten[kid].params == knoten.params
        assert "ferne_abstand" not in knoten.params
        assert "tiefe_invertieren" not in knoten.params
    assert (graph.inhalts_hash(nachher.knoten[KNOTEN_MULTIPASS], [])
            == graph.inhalts_hash(vorher.knoten[KNOTEN_MULTIPASS], []))


def test_ohne_schalter_sind_die_aufrufe_unterwegs_wort_fuer_wort_die_alten(
        tmp_path, monkeypatch):
    """Nicht nur das Ergebnis — auch was an den Nahten ankommt: Der Normierer bekommt
    kein neues Argument, die Bildstufe auch nicht, und der Multipass wird kein zweites Mal
    normiert."""
    exr = schreibe_exr(tmp_path / "t.exr", B, H, {"V": quader()})
    normierer = []
    echt = bildschreiben.tiefe_exr_zu_png

    def mitschreiben(*a, **kw):
        normierer.append(sorted(kw))
        return echt(*a, **kw)

    monkeypatch.setattr(bildschreiben, "tiefe_exr_zu_png", mitschreiben)
    bericht = seams._tiefe_nachbearbeiten({"depth_exr": str(exr)}, tmp_path)
    assert bericht["depth_png"]
    assert normierer == [["_starte", "timeout"]], "der Aufruf von vorher, Wort fuer Wort"

    # Die Kette: Multipass einmal normiert, Render ohne neues Argument.
    normierer.clear()
    gerufen = []
    _multipass_attrappe(monkeypatch, exr)
    monkeypatch.setattr(render, "rendere",
                        lambda a, **kw: gerufen.append(sorted(kw)) or {"status": "ok"})
    g = _bau(_glb_datei(tmp_path), qa=False)
    ergebnis = kette.fuehre_aus(g, ausfuehrer=_tabelle(kette.render_ausfuehrer()),
                                out_dir=tmp_path / "lauf")
    assert ergebnis["knoten"][KNOTEN_MULTIPASS]["status"] == kette.STATUS_OK
    assert len(normierer) == 1, "ohne Abstand wird nicht nachnormiert"
    assert gerufen == [["_lader", "modell"]]


# ======================================================================================
# (b) Mit Abstand: die Rueckkante trennt sich, die Ordnung bleibt
# ======================================================================================

@pytest.mark.parametrize("abstand", [bildschreiben.FERNE_ABSTAND_MINDESTENS, 0.1, 0.25,
                                     bildschreiben.FERNE_ABSTAND_HOECHSTENS])
def test_mit_abstand_liegt_die_rueckkante_ueber_dem_hintergrund(abstand):
    tiefe = quader()
    grau, norm = normalisiere_tiefe(tiefe, ferne_abstand=abstand)

    assert grau[LEER] == bildschreiben.HINTERGRUND_GRAUWERT == 0.0
    assert grau[FERN] == pytest.approx(abstand), "das Fernste liegt auf dem Abstand"
    assert grau[FERN] > grau[LEER]
    assert max(grau) == pytest.approx(1.0), "das Naechste bleibt das Hellste"
    assert norm["ferne_abstand"] == norm["grau_boden"] == abstand
    assert norm["konvention"] == bildschreiben.KONVENTION_MIT_ABSTAND
    assert norm["rueckrechnung"] == bildschreiben.RUECKRECHNUNG_MIT_BODEN


def test_mit_abstand_bleibt_die_tiefenordnung():
    tiefe = quader(boden=True)
    grau, _norm = normalisiere_tiefe(tiefe, ferne_abstand=0.2)
    geometrie = [i for i, t in enumerate(tiefe) if t < HIMMEL]
    for i in geometrie:
        for j in geometrie:
            if tiefe[i] < tiefe[j]:
                assert grau[i] > grau[j], (tiefe[i], tiefe[j], grau[i], grau[j])


def test_ohne_abstand_verschwindet_die_rueckkante_im_hintergrund():
    """Der Befund selbst, als Probe: Ohne Schalter IST die Rueckkante Hintergrund."""
    grau, _norm = normalisiere_tiefe(quader())
    assert grau[FERN] == grau[LEER] == 0.0


def _was_das_modell_sieht(tmp_path, abstand, *, umdrehen: bool):
    """Das 8-Bit-RGB-Bild, das die Pipeline bekommt — ueber den echten Weg:
    16-Bit-PNG schreiben, ``render._tiefe_als_rgb``, und die Umkehrung, wenn gedreht."""
    pil = pytest.importorskip("PIL.Image")
    ops = pytest.importorskip("PIL.ImageOps")
    ziel = tmp_path / f"t{abstand}.png"
    tiefe_exr_zu_png("x.exr", ziel, _leser=_leser(quader()), ferne_abstand=abstand)
    bild = render._tiefe_als_rgb(pil.open(ziel))
    return ops.invert(bild) if umdrehen else bild


def _px(bild, i):
    return bild.getpixel((i % B, i // B))[0]


@pytest.mark.parametrize("umdrehen", [False, True])
def test_die_rueckkante_ueberlebt_die_8_bit_und_die_umkehrung(tmp_path, umdrehen):
    """**Was das Bildmodell wirklich sieht.** Die Karte geht in 8 Bit an die Pipeline,
    fuer z-image umgedreht. Ohne Abstand sind Rueckkante und Hintergrund dort dasselbe
    Byte (0 bzw. 255); mit dem kleinsten zulaessigen Abstand nicht mehr."""
    ohne = _was_das_modell_sieht(tmp_path, None, umdrehen=umdrehen)
    mit = _was_das_modell_sieht(tmp_path, bildschreiben.FERNE_ABSTAND_MINDESTENS,
                                umdrehen=umdrehen)
    hintergrund = 255 if umdrehen else 0
    assert _px(ohne, FERN) == _px(ohne, LEER) == hintergrund
    assert _px(mit, LEER) == hintergrund
    assert _px(mit, FERN) != hintergrund


@pytest.mark.parametrize("wert", [True, "0.2", -0.1, math.nan, math.inf, 0.001, 0.51])
def test_ein_unbrauchbarer_abstand_wird_abgewiesen_und_nicht_gedeutet(wert):
    with pytest.raises(bildschreiben.SchreibError):
        normalisiere_tiefe(quader(), ferne_abstand=wert)
    with pytest.raises(kette.KettenError):
        _bau(ferne_abstand=wert)


def test_ein_von_hand_gebauter_knoten_mit_falschem_abstand_startet_blender_nicht(
        tmp_path, monkeypatch):
    def darf_nicht(*a, **kw):
        raise AssertionError("Blender fuer einen unbrauchbaren Abstand gestartet")

    monkeypatch.setattr(seams, "glb_zu_multipass", darf_nicht)
    knoten = kette.Knoten(KNOTEN_MULTIPASS, ART_MULTIPASS,
                          {"aufloesung": 16, "samples": 1, "beauty": True,
                           "material_id": True, "ferne_abstand": 0.9})
    aus = kette.AUSFUEHRER[ART_MULTIPASS](
        knoten=knoten, eingaben=[{"glb_path": "m.glb", "up_axis": "Y"}], out_dir=tmp_path)
    assert aus["status"] == kette.STATUS_FEHLER
    assert "ferne_abstand" in aus["error"]


def test_abstand_und_ferne_trennen_vertragen_sich_mit_einem_boden():
    """Entschieden 23.09.2026: kein Widerspruch. Beide heben die Geometrie vom Hintergrund
    ab; der Abstand ist nie kleiner als der Mindestgrau und ersetzt ihn als Boden. Die
    geklemmten Punkte tragen den Abstand — ueber dem Hintergrund, und nicht heller als
    die echten hintersten Punkte."""
    karte = [2.0, 4.0, 6.0, 8.0, 500.0, 600.0, HIMMEL]
    grau, norm = normalisiere_tiefe(karte, ferne_trennen=True, ferne_abstand=0.2)

    assert norm["ferne_getrennt"] is True and norm["n_geklemmt"] == 2
    assert grau[4] == grau[5] == pytest.approx(0.2) == norm["geklemmt_mindestgrau"]
    assert grau[6] == 0.0 < grau[5]
    assert grau[3] >= grau[4], "die Ordnung ueber die Klemmgrenze hinweg bleibt"
    assert norm["grau_boden"] == 0.2
    assert "Grauwert des Bodens" in norm["rueckrechnung_vorbehalt"]


# ======================================================================================
# (c) Die Rueckrechnung: dieselben Meter mit und ohne Abstand
# ======================================================================================

def _geometrie(tiefe):
    return [i for i, t in enumerate(tiefe) if t < HIMMEL]


@pytest.mark.parametrize("abstand", [0.05, 0.2, 0.5])
def test_die_rueckrechnung_ergibt_mit_und_ohne_abstand_dieselben_meter(abstand):
    """Am ungerundeten Grauwert: auf Rundungsrest genau — derselbe Leser, der auch hinter
    ``tiefen_aus_png`` und ``tiefen_aus_report`` steht."""
    tiefe = quader(boden=True)
    grau_aus, norm_aus = normalisiere_tiefe(tiefe)
    grau_an, norm_an = normalisiere_tiefe(tiefe, ferne_abstand=abstand)

    def meter(grau, norm):
        min_m, max_m = bildlesen._normalisierung_lesen(norm)
        return bildlesen._rueckrechnen(grau, B, H, min_m, max_m,
                                       bildlesen.GRAU_NULL_GEOMETRIE, "t",
                                       boden=bildlesen._boden_lesen(norm))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", bildlesen.SilhouettenVerlust)
        aus, an = meter(grau_aus, norm_aus), meter(grau_an, norm_an)
    for i in _geometrie(tiefe):
        assert an[i] == pytest.approx(tiefe[i], abs=1e-9)
        assert an[i] == pytest.approx(aus[i], abs=1e-9)


@pytest.mark.parametrize("abstand", [None, 0.2])
def test_das_png_gibt_ueber_jeden_leser_dieselben_meter(tmp_path, abstand):
    """Durch die Datei — 16 Bit, gerundet —, ueber ``tiefen_aus_png`` und den PNG-Weg von
    ``tiefen_aus_report``. Die Grenze ist ein halber Quantisierungsschritt der Geometrie,
    und genau den nennt ``png_befund``."""
    tiefe = quader()
    ziel = tmp_path / "t.png"
    norm = tiefe_exr_zu_png("x.exr", ziel, _leser=_leser(tiefe), ferne_abstand=abstand)
    befund = bildlesen.png_befund(ziel, norm)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", bildlesen.SilhouettenVerlust)
        direkt = bildlesen.tiefen_aus_png(ziel, norm)
        bericht, _b, _h = bildlesen.tiefen_aus_report(
            {"depth_png": str(ziel), "depth_normalisierung": norm},
            quelle=bildlesen.QUELLE_PNG)
    for i in _geometrie(tiefe):
        if abstand is None and i == FERN:
            continue                        # der dokumentierte Verlust, siehe unten
        assert direkt[i] == bericht[i]
        assert abs(direkt[i] - tiefe[i]) <= befund["quantisierungsschritt_m"] / 2 + 1e-9
    assert direkt[LEER] == math.inf, "der Hintergrund bleibt Hintergrund"
    # Das Fernste: ohne Abstand ist es verloren (inf), mit Abstand wieder da.
    if abstand is None:
        assert direkt[FERN] == math.inf
    else:
        assert direkt[FERN] == pytest.approx(tiefe[FERN],
                                             abs=befund["quantisierungsschritt_m"])


def test_mit_abstand_warnt_der_leser_nicht_vor_einem_verlust_den_es_nicht_gibt(tmp_path):
    """Ohne Abstand warnt er — Hintergrund und Rueckkante sind ein Wert. Mit Abstand ist
    Grauwert 0 nur noch Hintergrund; eine Warnung waere ein falscher Alarm."""
    ziel = tmp_path / "t.png"
    norm = tiefe_exr_zu_png("x.exr", ziel, _leser=_leser(quader()), ferne_abstand=0.2)
    with warnings.catch_warnings():
        warnings.simplefilter("error", bildlesen.SilhouettenVerlust)
        bildlesen.tiefen_aus_png(ziel, norm)
    norm_aus = tiefe_exr_zu_png("x.exr", ziel, _leser=_leser(quader()))
    with pytest.warns(bildlesen.SilhouettenVerlust):
        bildlesen.tiefen_aus_png(ziel, norm_aus)


def test_der_leser_kennt_jetzt_auch_den_boden_von_ferne_trennen():
    """**Befund 23.09.2026, eine Luecke daneben.** Die Normierung mit ``ferne_trennen``
    nannte die Formel mit Boden, der Leser rechnete ohne ihn: jeder Punkt um bis zu
    ``spanne / 255`` zu nah. Seit heute liest er ``geklemmt_mindestgrau``."""
    karte = [1.75 + 8.25 * i / 200 for i in range(200)] + [1600.0] * 3
    grau, norm = normalisiere_tiefe(karte, ferne_trennen=True)
    assert norm["ferne_getrennt"] is True
    min_m, max_m = bildlesen._normalisierung_lesen(norm)
    zurueck = bildlesen._rueckrechnen(grau, len(karte), 1, min_m, max_m,
                                      bildlesen.GRAU_NULL_HINTERGRUND, "t",
                                      boden=bildlesen._boden_lesen(norm))
    for z, t in zip(zurueck[:200], karte[:200]):
        assert z == pytest.approx(t, abs=1e-9)


@pytest.mark.parametrize("boden", [-0.1, 1.0, "0.2", True, math.nan])
def test_ein_unbrauchbarer_boden_in_der_normierung_wird_abgewiesen(boden):
    with pytest.raises(bildlesen.BildError, match="grau_boden"):
        bildlesen._boden_lesen({"min_m": 1.0, "max_m": 2.0, "grau_boden": boden})


# ======================================================================================
# (d) tiefe_invertieren: bis zum control_image, und im Ergebnis
# ======================================================================================

@pytest.fixture
def adapter(monkeypatch):
    """Der ECHTE Adapter ueber einer Pipeline-Attrappe — mit echtem Pillow, damit das
    Bild, das als ``control_image`` ankommt, ein Bild ist und kein Stellvertreter."""
    pytest.importorskip("PIL.Image")
    pytest.importorskip("numpy")
    monkeypatch.setattr(render, "_vertraegliche_argumente", lambda p, a: (dict(a), []))
    pipeline = Pipelineattrappe(schritte=2)

    def bauen(name):
        return render._pipeline_adapter(pipeline, backbone.hole(name), _Torchattrappe())
    bauen.pipeline = pipeline
    return bauen


def _tiefenkarte(tmp_path):
    ziel = tmp_path / "tiefe_norm.png"
    tiefe_exr_zu_png("x.exr", ziel, _leser=_leser(quader()))
    return ziel


@pytest.mark.parametrize("name, schalter, gedreht", [
    ("z-image-turbo", None, True),          # Register: nah = dunkel, wird gedreht
    ("z-image-turbo", False, False),        # ueberschrieben
    ("z-image-turbo", True, True),
    ("qwen-image-2512", None, False),       # Register: nicht gemessen, nicht gedreht
    ("qwen-image-2512", True, True),        # ueberschrieben
])
def test_tiefe_invertieren_kommt_als_control_image_an(tmp_path, adapter, name, schalter,
                                                      gedreht):
    tiefe = _tiefenkarte(tmp_path)
    auftrag = render.RenderAuftrag(depth_png=str(tiefe), prompt="a house", backbone=name,
                                   schritte=2, ausgabe_png=str(tmp_path / "b.png"))
    weiter = {} if schalter is None else {"tiefe_invertieren": schalter}
    ergebnis = render.rendere(auftrag, modell=adapter(name), **weiter)

    assert ergebnis["status"] == render.STATUS_OK, ergebnis["error"]
    bild = adapter.pipeline.gesehen["control_image"]
    # Hintergrund 0 in der Datei: umgedreht 255, sonst 0. Der naechste Punkt umgekehrt.
    assert _px(bild, LEER) == (255 if gedreht else 0)
    assert ergebnis["parameter"]["tiefe_invertiert"] is gedreht
    assert ergebnis["parameter"]["tiefe_invertiert_ueberschrieben"] is schalter
    messsatz = [h for h in ergebnis["hinweise"] if h.startswith("MESSSCHALTER")]
    assert len(messsatz) == (0 if schalter is None else 1)


@pytest.mark.parametrize("wert", ["ja", 1, 0])
def test_ein_unbrauchbarer_invertierschalter_wird_abgelehnt(tmp_path, wert):
    gerufen = []
    auftrag = render.RenderAuftrag(depth_png=str(_tiefenkarte(tmp_path)), prompt="a house",
                                   ausgabe_png=str(tmp_path / "b.png"))
    ergebnis = render.rendere(auftrag, modell=lambda p: gerufen.append(p),
                              tiefe_invertieren=wert)
    assert ergebnis["status"] == render.STATUS_ABGELEHNT
    assert any("tiefe_invertieren" in m for m in ergebnis["maengel"])
    assert gerufen == [], "nichts gerechnet"
    with pytest.raises(kette.KettenError):
        _bau(tiefe_invertieren=wert)


def test_der_nachrender_erbt_den_invertierschalter(tmp_path, monkeypatch):
    g = kette.haenge_nachrender_an(_bau(tiefe_invertieren=False), prompt="ein Balkon",
                                   eingangsbild=str(tmp_path / "s.png"))
    nach = [k for k in g.knoten.values() if k.art == ART_NACHRENDER][0]
    assert nach.params["tiefe_invertieren"] is False
    ohne = kette.haenge_nachrender_an(_bau(), prompt="ein Balkon",
                                      eingangsbild=str(tmp_path / "s.png"))
    assert "tiefe_invertieren" not in [k for k in ohne.knoten.values()
                                       if k.art == ART_NACHRENDER][0].params

    gerufen = []
    monkeypatch.setattr(render, "rendere",
                        lambda a, **kw: gerufen.append(kw) or {"status": "ok"})
    kette.nachrender_ausfuehrer()(
        knoten=nach, eingaben=[{"depth_png": "t.png"}, {"bild_png": "s.png"}],
        out_dir=tmp_path)
    assert gerufen[0]["tiefe_invertieren"] is False


@pytest.mark.parametrize("schalter", [False, True])
def test_auf_dem_skizzenweg_geht_der_invertierschalter_nicht_verloren(tmp_path, schalter):
    """**Durchsicht Runde 10.** ``_skizzengraph`` nimmt den Renderknoten aus dem Graphen,
    bevor der Nachrender eine Vorlage sucht — der Schalter aus der Mappe ging dort still
    verloren. Angenommen und ohne Wirkung ist schlimmer als abgewiesen."""
    g = arbeitsgang._skizzengraph(
        "m.glb", {"prompt": "a house", "up_axis": "Y", "tiefe_invertieren": schalter},
        {}, pfad=tmp_path / "s.png", anweisung="ein Balkon")
    nach = [k for k in g.knoten.values() if k.art == ART_NACHRENDER][0]
    assert nach.params["tiefe_invertieren"] is schalter
    ohne = arbeitsgang._skizzengraph("m.glb", {"prompt": "a house", "up_axis": "Y"}, {},
                                     pfad=tmp_path / "s.png", anweisung="ein Balkon")
    assert "tiefe_invertieren" not in [k for k in ohne.knoten.values()
                                       if k.art == ART_NACHRENDER][0].params


def test_der_nachrender_nimmt_den_schalter_auch_ausdruecklich(tmp_path):
    g = kette.haenge_nachrender_an(_bau(tiefe_invertieren=True), prompt="x",
                                   eingangsbild=str(tmp_path / "s.png"),
                                   tiefe_invertieren=False)
    assert [k for k in g.knoten.values()
            if k.art == ART_NACHRENDER][0].params["tiefe_invertieren"] is False
    with pytest.raises(kette.KettenError):
        kette.haenge_nachrender_an(_bau(), prompt="x", eingangsbild="s.png",
                                   tiefe_invertieren="nein")


# ======================================================================================
# (e) Ueber die Kette und ueber die Mappe
# ======================================================================================

def _multipass_attrappe(monkeypatch, exr: Path):
    """``seams.glb_zu_multipass`` ohne Blender: legt die EXR in den Arbeitsordner und
    endet wie das Original — mit ``_tiefe_nachbearbeiten``, also dem echten Normierer."""
    angekommen = []

    def multipass(glb, out_dir, **kw):
        angekommen.append(kw)
        ziel = Path(out_dir) / "tiefe_0001.exr"
        ziel.write_bytes(Path(exr).read_bytes())
        return seams._tiefe_nachbearbeiten({"status": "ok", "depth_exr": str(ziel)},
                                           Path(out_dir))

    monkeypatch.setattr(seams, "glb_zu_multipass", multipass)
    return angekommen


def _geometrie_attrappe(*, knoten, eingaben, out_dir):
    glb = Path(out_dir) / "modell.glb"
    glb.write_text("glb", encoding="utf-8")
    return {"status": "ok", "glb_path": str(glb), "up_axis": "Y",
            "bbox": [[0, 0, 0], [8.0, 5.0, 3.25]]}


def _tabelle(render_stufe) -> dict:
    return {ART_GEOMETRIE: _geometrie_attrappe, ART_MULTIPASS: kette._fuehre_multipass,
            ART_RENDER: render_stufe}


def _pruefe_angekommen(multipass: dict, bild_ergebnis: dict, pipeline, abstand):
    norm = multipass["depth_normalisierung"]
    assert norm["ferne_abstand"] == abstand
    grau, _b, _h = bildlesen.lies_png_graustufen(multipass["depth_png"])
    assert grau[FERN] == pytest.approx(abstand, abs=1e-4), "das PNG traegt den Abstand"
    assert grau[LEER] == 0.0
    bild = pipeline.gesehen["control_image"]
    assert _px(bild, LEER) == 0, "nicht umgedreht, obwohl das Register dreht"
    assert _px(bild, FERN) > 0, "und die Rueckkante ist beim Modell angekommen"
    assert bild_ergebnis["parameter"]["tiefe_invertiert"] is False
    assert bild_ergebnis["parameter"]["tiefe_invertiert_ueberschrieben"] is False


def test_ueber_die_kette_kommen_beide_schalter_an(tmp_path, monkeypatch, adapter):
    exr = schreibe_exr(tmp_path / "quelle.exr", B, H, {"V": quader()})
    runner = _multipass_attrappe(monkeypatch, exr)
    g = kette.baue_kette(glb_path=str(_glb_datei(tmp_path)), up_axis="Y",
                         prompt="a house",
                         bbox=[[0, 0, 0], [8, 5, 3]], qa=False, schritte=2,
                         backbone="z-image-turbo", ferne_abstand=0.25,
                         tiefe_invertieren=False)
    lauf = kette.fuehre_aus(
        g, ausfuehrer=_tabelle(kette.render_ausfuehrer(modell=adapter("z-image-turbo"))),
        out_dir=tmp_path / "lauf")

    assert lauf["status"] == kette.STATUS_OK, lauf.get("error")
    assert "ferne_abstand" not in runner[0], "Blender bekommt den Messschalter nicht"
    _pruefe_angekommen(lauf["knoten"][KNOTEN_MULTIPASS]["ausgaben"],
                       lauf["knoten"][KNOTEN_RENDER]["ausgaben"], adapter.pipeline, 0.25)


@pytest.fixture
def glb(tmp_path):
    """Ein gueltiges glb — Weg «durchgereicht», also ohne jeden Subprozess."""
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    pfad = tmp_path / "quelle" / "haus.glb"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    return pfad


def test_ueber_die_mappe_kommen_beide_schalter_an(tmp_path, monkeypatch, adapter, glb):
    """**Der Produktweg.** Die Mappe gibt ihre Einstellungen als Kettenargumente an
    ``baue_kette`` — ohne dass ``arbeitsgang`` die beiden Namen kennt."""
    exr = schreibe_exr(tmp_path / "quelle.exr", B, H, {"V": quader()})
    _multipass_attrappe(monkeypatch, exr)
    wurzel = tmp_path / "projekt"
    arbeitsgang.lege_an(wurzel, glb, name="Probe",
                        einstellungen={"prompt": "a house", "up_axis": "Y",
                                       "backbone": "z-image-turbo", "schritte": 2,
                                       "ferne_abstand": 0.25, "tiefe_invertieren": False})
    ergebnis = arbeitsgang.rechne(
        wurzel, qa=False, cache=None,
        ausfuehrer=_tabelle(kette.render_ausfuehrer(modell=adapter("z-image-turbo"))))

    knoten = ergebnis["lauf"]["knoten"]
    assert knoten[KNOTEN_MULTIPASS]["status"] == kette.STATUS_OK, knoten[KNOTEN_MULTIPASS]
    assert knoten[KNOTEN_RENDER]["status"] == kette.STATUS_OK, knoten[KNOTEN_RENDER]
    _pruefe_angekommen(knoten[KNOTEN_MULTIPASS]["ausgaben"],
                       knoten[KNOTEN_RENDER]["ausgaben"], adapter.pipeline, 0.25)
