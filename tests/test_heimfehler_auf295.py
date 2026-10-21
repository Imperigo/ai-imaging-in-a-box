"""Die Befunde aus ``auf-20261020-295`` (HomeStation, 21.10.2026): vier Punkte nach der Nachmessung.

Erfüllt war: Sonne seitlich genau auf dem Sollwinkel, weicher Rückfall, Blaue Stunde, gemischter
Prompt, Vermerk bei «voll», ohne Stimmung bildpunktgleich. Offen blieben vier Befunde: abend unter
der Kontrastschwelle (N1), «abend voll» zeigte das Haus nicht, und eine Umriss-IoU aus Farbe
meldete trotzdem 0,60 (N2), ``angewandt.environment`` nannte bei der Drehung zur Kamera
``rotationGrad 0`` (N3), und die Schwelle von ``ausserhalb_umriss_anteil`` war nicht prüfbar (N4).
Je Befund eine Probe — reine Funktionen, der Runner mit Attrappen (Regel 2: kein ``bpy`` im
Produkt-venv). Testdaten synthetisch (Regel 3).
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from aiimaging import abholer, auftrag, baumasse, belichtung, bruecke, kosmo_szene, stimmung
from aiimaging import umriss

from test_heimfehler_auf292 import _runner
from test_heimfehler_auf293 import MIT_SONNE

WURZEL = Path(__file__).resolve().parents[1]


# ====================================================================== N1 · abend Kontrast

def _zweiseitiges_haus(*, hell=2.0, dunkel=0.1, anteil_hell=0.26, n=100):
    """Ein Haus wie abend in 295: ein Viertel Sonnenseite, drei Viertel Schattenseite (RGBA)."""
    n_hell = round(n * anteil_hell)
    return [hell, hell, hell, 1.0] * n_hell + [dunkel, dunkel, dunkel, 1.0] * (n - n_hell)


def _grau(hell, *, mitte=0.18, grau_mitte=110.0, je_stufe=31.0):
    """Ein Modell der Tonwertkurve in den Mitten: Grauwert wächst mit den Blendenstufen.

    Nur ein Modell (AgX ist in Blender), geeicht an 295: Schattenseite 98, Sonnenseite 230,
    Hintergrund 115 — rund 31 Grauwerte je Stufe. Es zeigt die RICHTUNG des Fehlers, nicht
    seine Grösse am Heim-PC; die misst ``auf-20261021-296``.
    """
    return max(0.0, min(255.0, grau_mitte + je_stufe * math.log2(max(hell, 1e-9) / mitte)))


def test_das_mittel_in_stufen_gehoert_der_schattenseite():
    px = _zweiseitiges_haus()
    linear = stimmung.haus_leuchtdichte(px, mass="linear")
    stufen = stimmung.haus_leuchtdichte(px)
    assert stufen["mass"] == stimmung.HAUS_MASS == "stufen"
    assert linear["leuchtdichte"] == pytest.approx(0.26 * 2.0 + 0.74 * 0.1)
    assert stufen["leuchtdichte"] == pytest.approx(2 ** (0.26 * 1 + 0.74 * math.log2(0.1)))
    # Das lineare Mittel liegt fast drei Stufen ueber der Schattenseite, das in Stufen gut eine.
    assert math.log2(linear["leuchtdichte"] / 0.1) > 2.5
    assert math.log2(stufen["leuchtdichte"] / 0.1) == pytest.approx(0.26 * math.log2(20), abs=1e-9)
    # Beide stehen im Ergebnis, gleich welches gilt.
    assert stufen["linear"] == linear["leuchtdichte"] and linear["stufen"] == stufen["leuchtdichte"]
    # Ein gleichmaessiges Haus: beide Mittel gleich — dort aendert sich nichts.
    gleich = stimmung.haus_leuchtdichte([0.5, 0.5, 0.5, 1.0] * 4 + [0.0] * 4 * 4)
    assert gleich["leuchtdichte"] == pytest.approx(0.5) and gleich["linear"] == pytest.approx(0.5)
    # Ein schwarzer Punkt macht das Mittel nicht unendlich klein.
    assert stimmung.haus_leuchtdichte([0.0, 0.0, 0.0, 1.0])["leuchtdichte"] == pytest.approx(
        stimmung.STUFEN_UNTERGRENZE)
    with pytest.raises(ValueError, match="Mass"):
        stimmung.haus_leuchtdichte(px, mass="median")


def test_mit_dem_mittel_in_stufen_hebt_sich_das_haus_ab():
    """Der Fall aus 295 im Modell: Hintergrund knapp ueber der Schattenseite. Gegen das lineare
    Mittel liegt er schon zwei Stufen darunter (Faktor 1, Kontrast unter 20), gegen das Mittel in
    Stufen nicht — er wird dunkler, und der Kontrast im Grauwert kommt ueber die Schwelle."""
    px = _zweiseitiges_haus()
    hintergrund = 0.1 * 2 ** (17 / 31)                       # 115 gegen 98 im Grauwert
    haus_grau = 0.26 * _grau(2.0) + 0.74 * _grau(0.1)

    def kontrast(mass):
        haus = stimmung.haus_leuchtdichte(px, mass=mass)["leuchtdichte"]
        ab = stimmung.hintergrund_mit_abstand([hintergrund] * 3, [hintergrund] * 3, haus,
                                              richtung="dunkler")
        return ab, haus_grau - _grau(hintergrund * ab["faktor"])

    alt, k_alt = kontrast("linear")
    neu, k_neu = kontrast("stufen")
    assert alt["faktor"] == 1.0 and k_alt < belichtung.KONTRAST_SCHWELLE
    assert neu["faktor"] < 1.0 and k_neu >= belichtung.KONTRAST_SCHWELLE
    assert neu["abstand_ev_nachher"] == pytest.approx(-1.0, abs=1e-3)


def test_das_mass_reist_als_lichtdatum_bis_blender():
    """Als Lichtdatum, damit eine Grundlage mit Stimmung von vorher kein Treffer mehr ist."""
    for preset in stimmung.PRESETS:
        assert stimmung.licht_der_stimmung(preset)["haus_mass"] == "stufen"
    assert "haus_mass" in abholer.LICHT_AN_BLENDER
    # abend bleibt bei einer Stufe Abstand: zwei Stufen gaeben einen fast nachtdunklen Himmel,
    # und die Nacht war der Fehler von 294.
    assert stimmung.licht_der_stimmung("abend")["hintergrund_abstand_ev"] == 1.0
    assert stimmung.licht_der_stimmung("blaue-stunde")["hintergrund_abstand_ev"] == 2.0


class _Knoten:
    def __init__(self, staerke):
        self.inputs = {"Strength": SimpleNamespace(default_value=staerke)}


def _vorprobe(monkeypatch, tmp_path, licht, pixel):
    modul, bpy = _runner(monkeypatch)
    bpy.data.objects = []
    grund = _Knoten(1.0)
    bpy.context.scene.world.node_tree.nodes.get = lambda name: (
        grund if name == modul.RUHIGER_GRUND else None)
    szene = SimpleNamespace(
        render=SimpleNamespace(resolution_percentage=100, film_transparent=False,
                               filepath="/x/beauty_",
                               image_settings=SimpleNamespace(file_format="PNG",
                                                              color_depth="8",
                                                              color_mode="RGBA")),
        cycles=SimpleNamespace(samples=64, use_denoising=True))

    def rendern(write_still=True):
        Path(szene.render.filepath + ".exr").write_bytes(b"exr")

    bpy.ops.render.render = rendern
    bpy.data.images.load = lambda pfad: SimpleNamespace(pixels=pixel, channels=4)
    hg = 0.1 * 2 ** (17 / 31)
    umgebung = {"toenung": None, "hintergrund": {"horizont": [hg] * 3, "zenit": [hg] * 3}}
    return modul._hintergrund_abstimmen(szene, tmp_path, licht, umgebung), grund


def test_die_vorprobe_misst_in_stufen_und_sagt_es(monkeypatch, tmp_path):
    licht = stimmung.licht_der_stimmung("abend")
    befund, grund = _vorprobe(monkeypatch, tmp_path, licht, _zweiseitiges_haus())
    assert befund["weg"] == "vorprobe" and befund["haus_mass"] == "stufen"
    assert befund["haus_linear"] > befund["haus_stufen"] > 0.1
    assert befund["faktor"] < 1.0 and grund.inputs["Strength"].default_value < 1.0
    # Ohne `haus_mass` in den Lichtdaten das lineare Mittel wie bis 295 — Faktor 1.
    ohne = {k: v for k, v in licht.items() if k != "haus_mass"}
    alt, grund_alt = _vorprobe(monkeypatch, tmp_path, ohne, _zweiseitiges_haus())
    assert alt["haus_mass"] == "linear" and alt["faktor"] == 1.0
    assert grund_alt.inputs["Strength"].default_value == 1.0


# ====================================================================== N2 · Haus nicht wiederzuerkennen

def test_die_umrisstreue_gilt_erst_ab_einer_ueberdeckung():
    assert umriss.WIEDERERKENNUNG_GEOM_IOU == 0.1
    assert umriss.umriss_gilt(0.005) is False
    assert umriss.umriss_gilt(0.384) is True and umriss.umriss_gilt(0.1) is True
    assert umriss.umriss_gilt(None) is None and umriss.umriss_gilt(True) is None
    assert umriss.umriss_gilt(float("nan")) is None


def _urteil(kamera, iou, **mehr):
    return dict({"kamera": kamera, "score": 0.05, "bestanden": False, "geom_iou": iou,
                 "spearman": -0.5, "n_gemeinsam": 763, "n_soll": 67541, "n_ist": 86044}, **mehr)


def _saetze(ergebnis):
    return [h for h in ergebnis["qa"]["verdict"].get("hinweise") or ()
            if h.startswith(kosmo_szene.SATZ_NICHT_WIEDERZUERKENNEN)]


def test_der_satz_steht_bei_niedriger_ueberdeckung_und_der_vertrag_bleibt():
    je = [{"kamera": "sSE", "geometrie_urteil": _urteil("sSE", 0.004992736647864836)},
          {"kamera": "nNW", "geometrie_urteil": _urteil("nNW", 0.45)}]
    e = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png", "b.png"],
                                 geometrie_urteil=je[0]["geometrie_urteil"], je_kamera=je)
    saetze = _saetze(e)
    assert len(saetze) == 1 and "'sSE'" in saetze[0] and "0.005" in saetze[0]
    assert "763 von 67541" in saetze[0] and "Umriss-IoU" in saetze[0]
    assert saetze[0] in e["hinweise"]
    # Dieselben Urteile mit erkennbarem Haus: kein Satz, und qa.geometry / geometry_gates /
    # qa_je_kamera tragen dieselben Schluessel wie vorher.
    gut = [{"kamera": k["kamera"], "geometrie_urteil": _urteil(k["kamera"], 0.45)} for k in je]
    g = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png", "b.png"],
                                 geometrie_urteil=gut[0]["geometrie_urteil"], je_kamera=gut)
    assert _saetze(g) == []
    assert set(e["qa"]["geometry"]) == set(g["qa"]["geometry"])
    assert e["qa"]["geometry"]["geom_iou"] == pytest.approx(0.004992736647864836)
    assert set(e.get("geometry_gates") or {}) == set(g.get("geometry_gates") or {})
    assert [set(k) for k in e["qa_je_kamera"]] == [set(k) for k in g["qa_je_kamera"]]


def test_kein_satz_wo_nicht_gemessen_wurde():
    leer = _urteil("s", 0.0, n_gemeinsam=0)
    assert _saetze(kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"],
                                            geometrie_urteil=leer)) == []
    grundlage = _urteil("s", None, nur_grundlage=True)
    assert _saetze(kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"],
                                            geometrie_urteil=grundlage)) == []


def test_im_lauf_steht_der_satz_und_die_seedwahl_vermerkt_es(tmp_path):
    from test_kettenlauf_26august import _auftragsordner, _kette, _lauf
    ordner = _auftragsordner(tmp_path / "a")
    _protokoll, attrappen = _kette(tmp_path)
    attrappen["_qa"] = lambda *a, **k: {"score": 0.05, "bestanden": False, "geom_iou": 0.005,
                                        "n_gemeinsam": 3, "n_soll": 600, "n_ist": 700}
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert _saetze(antwort["ergebnis"])
    for k in abholer.lies_befund(ordner)["kameras"]:
        if k.get("doppelt_von"):
            continue
        assert k["seedauswahl"]["umriss_gilt"] is False
        assert "0.005" in k["seedauswahl"]["umriss_grund"]


# ====================================================================== N3 · Drehung je Kamera

def _stimmungsauftrag(tmp_path, monkeypatch, environment, drehungen):
    from test_heimfehler_auf294 import _stimmungsauftrag as auftrag294
    from test_kettenlauf_26august import _kette

    def kette_mit_drehung(tp, **kw):
        protokoll, attrappen = _kette(tp, **kw)
        alt = attrappen["_multipass"]

        def multipass(glb, aus, **mkw):
            bericht = alt(glb, aus, **mkw)
            if "umgebung_drehung" in mkw:
                weg, grad = "bestellt", mkw["umgebung_drehung"]
            else:
                weg, grad = "zur_kamera", drehungen[mkw.get("kamera")]
            bericht["umgebung"] = {"drehung": {"weg": weg, "drehung_grad": grad,
                                               "kamera_azimut_grad": -55.0}}
            return bericht

        attrappen["_multipass"] = multipass
        return protokoll, attrappen

    monkeypatch.setattr("test_kettenlauf_26august._kette", kette_mit_drehung)
    return auftrag294(tmp_path, monkeypatch, environment, richtungen=tuple(drehungen))


def test_zur_kamera_ohne_rotation_grad_mit_drehung_je_kamera(tmp_path, monkeypatch):
    _p, antwort = _stimmungsauftrag(tmp_path, monkeypatch, {"preset": "mittag"},
                                    {"sSE": 84.82402, "nNW": 264.82402})
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    env = antwort["ergebnis"]["angewandt"]["environment"]
    assert env["drehung_weg"] == "zur_kamera"
    assert "rotationGrad" not in env, "die Vorgabe 0 wurde nicht gerechnet"
    assert env["drehung_je_kamera"] == {"nNW": 264.824, "sSE": 84.824}
    assert "rotationGrad" in env["vorgaben"], "nicht bestellt — das bleibt wahr"


def test_bestellt_bleibt_rotation_grad_ohne_drehung_je_kamera(tmp_path, monkeypatch):
    _p, antwort = _stimmungsauftrag(tmp_path, monkeypatch, {"preset": "mittag", "rotationGrad": 30},
                                    {"sSE": 0.0})
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    env = antwort["ergebnis"]["angewandt"]["environment"]
    assert env["drehung_weg"] == "bestellt" and env["rotationGrad"] == 30.0
    assert "drehung_je_kamera" not in env


def test_die_drehung_kommt_nur_aus_einem_bericht_zur_kamera():
    assert abholer.drehung_aus_bericht(
        {"umgebung": {"drehung": {"weg": "zur_kamera", "drehung_grad": 285.00802}}}) == 285.008
    assert abholer.drehung_aus_bericht(
        {"umgebung": {"drehung": {"weg": "bestellt", "drehung_grad": 0.0}}}) is None
    assert abholer.drehung_aus_bericht({"umgebung": None}) is None
    assert abholer.drehung_aus_bericht(None) is None
    # Vor jeder Kamera (abgewiesen, ohne Lauf): zur_kamera ohne rotationGrad und ohne Liste.
    szene = {"umgebung": {"preset": "abend", "hdri": "belfast_sunset_puresky",
                          "intensitaet": 1.0, "rotationGrad": 0.0},
             "umgebung_vorgaben": ("hdri", "intensitaet", "rotationGrad")}
    env = abholer.angewandt_der_szene(szene)["environment"]
    assert env["drehung_weg"] == "zur_kamera" and "rotationGrad" not in env
    assert "drehung_je_kamera" not in env


# ====================================================================== N4 · Bezug der Zahl

B, H = 40, 30


def test_der_anteil_ist_auf_das_haus_bezogen_und_kann_ueber_eins_liegen():
    """Haus 4 x 6 = 24 Punkte, das KI-Bild baut die ganze Zeile 6–19 neben dem Haus zu: Der
    Anteil liegt weit ueber 1 — und hoechstens bei Bereich ÷ Haus. Platte und Boden unter dem
    Fuss zaehlen nicht, auch wenn sie im KI-Bild nah sind."""
    soll, haus, naehe = [], [], []
    for y in range(H):
        for x in range(B):
            ist_haus = 18 <= x <= 21 and 14 <= y <= 19
            platte = y == 20 and 10 <= x <= 29
            soll.append(ist_haus or platte)
            haus.append(ist_haus)
            if ist_haus:
                naehe.append(1.0)
            elif platte or y > 20:
                naehe.append(2.0)                            # Platte und Boden: sehr nah
            elif 6 <= y <= 19:
                naehe.append(1.0)                            # Gebaeude ueber die ganze Breite
            else:
                naehe.append(0.02)                           # Himmel
    aus = baumasse.ausserhalb_umriss(naehe, soll, B, H, haus=haus)
    assert aus["n_haus"] == 24 and aus["anteil_haus"] > 1.0
    assert aus["anteil_haus"] <= aus["n_bereich"] / aus["n_haus"]
    assert aus["n_neu"] <= aus["n_bereich"]
    # Nur Zeilen bis zum Fuss des Hauses (19): Platte (20) und Boden (21+) sind draussen.
    nur_unten = [2.0 if (y >= 20) else (1.0 if s else 0.02)
                 for y in range(H) for s in soll[y * B:(y + 1) * B]]
    assert baumasse.ausserhalb_umriss(nur_unten, soll, B, H, haus=haus)["n_neu"] == 0


def test_der_bezug_steht_im_modul():
    doc = baumasse.__doc__
    assert "grösser als 1" in doc and "n_bereich ÷ n_haus" in doc
    assert baumasse.SCHWELLE_ANTEIL_HAUS == 0.25, "die Schwelle bleibt, bis 296 sie prueft"


# ====================================================================== der Messauftrag 296

def test_der_messauftrag_296_ist_gueltig_und_fragt_alle_punkte():
    pfad = WURZEL / "auftraege" / "offen" / "auf-20261021-296.json"
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    assert auftrag.pruefe_auftrag(daten) == []
    assert daten["worker"] == "local" and daten["art"] == "qa" and daten["rang"] == 83
    assert daten["params"]["folgt_auf"] == "auf-20261020-295"
    text = daten["anweisung"]
    for stichwort in ("haus_mass", "drehung_je_kamera", "NICHT WIEDERZUERKENNEN",
                      "ausserhalb_umriss_anteil", "bildpunktgleich", "faithful"):
        assert stichwort in text, stichwort
    for preset in ("abend", "mittag"):
        assert preset in text
    assert all(m in stimmung.PRESETS for m in MIT_SONNE)
