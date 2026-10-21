"""Die Befunde aus ``auf-20261020-294`` (HomeStation, 20.10.2026): Frontallicht und fünf mehr.

Die HomeStation hat Fassung 0.3.8 gerechnet: Das Haus steht in allen acht Stimmungen vor dem
Hintergrund, aber die Sonne stand in allen acht Himmelsbildern 0–40° neben der Blickachse der
Kamera (B1, Frontallicht), der weiche Rückfall warf harte Schatten (B2), die Blaue Stunde blieb
pastell (B3), abend war fast weiss und das KI-Bild Nacht, ein gemischter Prompt wurde nicht
übersetzt (B4), bei «voll» fehlte der Vermerk der KI-Grösse (B5), und das Bildmodell baute über
den Umriss hinaus, ohne dass eine Zahl es sah (B6). Je Befund eine Probe — reine Funktionen,
der Runner mit Attrappen (Regel 2: kein ``bpy`` im Produkt-venv). Testdaten synthetisch
(Regel 3).
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from aiimaging import abholer, baumasse, bruecke, kosmo_szene, prompts, sprache, stimmung
from aiimaging import tiefenschaetzer as ts

from test_heimfehler_auf292 import _runner
from test_heimfehler_auf293 import MIT_SONNE

# Die Kompassrichtungen der HomeStation (294, 1_zusammenfassung): Kamera sSE 145°, Sonne je
# Stimmung. Kompass = 90° − Azimut der Blender-Welt (x Ost, y Nord, gegen den Uhrzeiger).
KAMERA_KOMPASS_294 = 145.0
SONNE_KOMPASS_294 = {"mittag": 125.2, "morgen": 115.2, "abend": 140.0, "blaue-stunde": 125.7,
                     "bedeckt": 103.7, "nebel": 119.8, "winter": 120.0, "weiss": 183.8}


def _azimut(kompass: float) -> float:
    return 90.0 - kompass


def _richtung(azimut_grad: float, hoehe_grad: float = 20.0):
    a, h = math.radians(azimut_grad), math.radians(hoehe_grad)
    return [math.cos(h) * math.cos(a), math.cos(h) * math.sin(a), math.sin(h)]


def _seite(kamera_azimut: float, sonne_azimut: float) -> str:
    """Von der Kamera aus gesehen: liegt die Sonne links oder rechts des Blicks?"""
    blick = math.radians(kamera_azimut + 180.0)
    s = math.radians(sonne_azimut)
    kreuz = math.cos(blick) * math.sin(s) - math.sin(blick) * math.cos(s)
    return "links" if kreuz > 0 else "rechts"


# ====================================================================== B1 · Sonne seitlich

def test_der_befund_aus_294_ist_frontallicht():
    """Die Gegenprobe zum Befund: Mit Drehung 0 steht die Sonne 0–40° neben der Achse
    (bedeckt 41°) — weit unter dem Bereich 60–100°."""
    for preset, kompass in SONNE_KOMPASS_294.items():
        winkel = stimmung.winkel_zur_blickachse(_azimut(kompass), _azimut(KAMERA_KOMPASS_294))
        assert winkel < stimmung.SONNE_SEITLICH_BEREICH_GRAD[0] - 15.0, preset
    assert stimmung.winkel_zur_blickachse(_azimut(140.0), _azimut(145.0)) == 5.0


@pytest.mark.parametrize("kamera_kompass", [145.0, 325.0, 10.0, 250.0])
@pytest.mark.parametrize("preset", stimmung.PRESETS)
def test_die_sonne_steht_je_kamera_seitlich(preset, kamera_kompass):
    """Kamera aus zwei (vier) Richtungen: Die Drehung bringt die Sonne jedes Himmelsbilds auf
    ``sonne_seitlich_grad`` neben die Achse Haus–Kamera, auf die Seite der Stimmung — die Lampe
    rechnet aus demselben gedrehten Bild."""
    licht = stimmung.licht_der_stimmung(preset)
    lo, hi = stimmung.SONNE_SEITLICH_BEREICH_GRAD
    assert lo <= licht["sonne_seitlich_grad"] <= hi
    kamera = _azimut(kamera_kompass)
    auge = [20.0 * math.cos(math.radians(kamera)), 20.0 * math.sin(math.radians(kamera)), 1.7]
    assert stimmung.kamera_azimut_grad(auge, [0.0, 0.0, 5.0]) == pytest.approx(
        (kamera + 180.0) % 360.0 - 180.0)
    bild = _azimut(SONNE_KOMPASS_294[preset])
    analyse = {"gefunden": True, "richtung_bild": _richtung(bild), "farbe": [1, 1, 1],
               "e_himmel_h": 1.0, "weg": "sonnenscheibe"}
    drehung = stimmung.drehung_zur_kamera(bild, kamera, seitlich_grad=licht["sonne_seitlich_grad"],
                                          seite=licht["sonne_seite"])
    assert 0.0 <= drehung < 360.0
    lampe = stimmung.lampe_aus_himmel(analyse, licht, drehung_grad=drehung)
    assert stimmung.winkel_zur_blickachse(lampe["azimut_welt_grad"], kamera) == pytest.approx(
        licht["sonne_seitlich_grad"], abs=1e-3)
    assert _seite(kamera, lampe["azimut_welt_grad"]) == licht["sonne_seite"]


def test_die_seite_ist_waehlbar():
    licht = stimmung.licht_der_stimmung("mittag", sonne_seite="rechts")
    assert licht["sonne_seite"] == "rechts"
    kamera, bild = _azimut(145.0), _azimut(125.2)
    for seite in stimmung.SONNE_SEITEN:
        d = stimmung.drehung_zur_kamera(bild, kamera, seitlich_grad=70.0, seite=seite)
        lampe = stimmung.lampe_aus_himmel({"gefunden": True, "richtung_bild": _richtung(bild),
                                           "e_himmel_h": 1.0}, licht, drehung_grad=d)
        assert _seite(kamera, lampe["azimut_welt_grad"]) == seite
    with pytest.raises(ValueError):
        stimmung.licht_der_stimmung("mittag", sonne_seite="oben")
    with pytest.raises(ValueError):
        stimmung.drehung_zur_kamera(0.0, 0.0, seitlich_grad=70.0, seite="oben")
    assert stimmung.kamera_azimut_grad([1, 1, 50], [1, 1, 0]) is None, "senkrecht: keine Seite"


def test_der_runner_dreht_zur_kamera_und_eine_bestellte_drehung_hat_vorrang(monkeypatch):
    modul, bpy = _runner(monkeypatch)
    bild = _azimut(140.0)
    monkeypatch.setattr(modul, "_himmelsfarben", lambda b: {
        "horizont": [0.6] * 3, "zenit": [0.4] * 3, "weg": "himmelsbild", "grund": "",
        "sonne": {"gefunden": True, "kappung": 9.5, "richtung_bild": _richtung(bild, 4.0),
                  "azimut_bild_grad": bild, "e_himmel_h": 1.0}})
    licht = stimmung.licht_der_stimmung("abend")
    kamera = _azimut(145.0)
    befund = modul._welt_setzen((0.5,) * 3, 1.0, hdr="/x/abend.hdr", licht=licht,
                                drehung_grad=None, kamera_azimut=kamera)
    assert befund["drehung"]["weg"] == "zur_kamera"
    assert befund["drehung_grad"] == pytest.approx(stimmung.drehung_zur_kamera(
        bild, kamera, seitlich_grad=80.0, seite="rechts"))
    # Die Lampe liest dieselbe Drehung und meldet den Winkel zur Achse.
    a = SimpleNamespace(umgebung_hdr="h.hdr", sonne_hoehe=None, sonne_azimut=None,
                        sonne_staerke=None, sonne_kelvin=None, sonne_winkel=None,
                        umgebung_licht=json.dumps(licht))
    _objekt, sonne = modul._sonne_setzen([0, 0, 0], 10.0, a, umgebung=dict(
        befund, staerke=1.0, toenung=None))
    assert sonne["drehung_weg"] == "zur_kamera"
    assert sonne["winkel_zur_blickachse_grad"] == pytest.approx(80.0, abs=1e-3)
    # Bestellt: Wort fuer Wort die bestellte Drehung, auch 0.
    for bestellt in (0.0, 30.0):
        befund = modul._welt_setzen((0.5,) * 3, 1.0, hdr="/x/abend.hdr", licht=licht,
                                    drehung_grad=bestellt, kamera_azimut=kamera)
        assert befund["drehung"]["weg"] == "bestellt" and befund["drehung_grad"] == bestellt
    # Ohne Lichtdaten (vor 293): 0 wie bisher.
    befund = modul._welt_setzen((0.5,) * 3, 1.0, hdr="/x/abend.hdr", drehung_grad=None,
                                kamera_azimut=kamera)
    assert befund["drehung_grad"] == 0.0 and "drehung" not in befund
    # Ohne Blickrichtung: 0 mit Grund, nie eine Ausnahme.
    befund = modul._welt_setzen((0.5,) * 3, 1.0, hdr="/x/abend.hdr", licht=licht,
                                drehung_grad=None, kamera_azimut=None)
    assert befund["drehung_grad"] == 0.0 and befund["drehung"]["grund"]


def test_die_drehung_wird_erst_nach_dem_lesen_der_sonne_gestellt():
    from test_heimfehler_auf293 import RUNNER
    quelle = RUNNER.read_text(encoding="utf-8")
    welt = quelle[quelle.index("def _welt_setzen("):quelle.index("def _look_setzen(")]
    assert welt.index("_himmelsfarben(himmel.image)") < welt.index(
        'abbild.inputs["Rotation"].default_value')
    haupt = quelle[quelle.index("def main()"):]
    assert haupt.index("_kamera_setzen(kam_lo, kam_hi, a)") < haupt.index("kamera_azimut_grad(")
    assert "drehung_grad=None if a.umgebung_drehung is None" in haupt


def _stimmungsauftrag(tmp_path, monkeypatch, environment, richtungen=("sSE", "nNW")):
    from test_kettenlauf_26august import _auftragsordner, _kette, _lauf
    from test_knoten_stimmung import _alle_himmel
    _alle_himmel(tmp_path, monkeypatch)
    ordner = _auftragsordner(tmp_path / "a")
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene["render"]["environment"] = environment
    szene["cameras_auto"] = {"richtungen": list(richtungen)}
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    protokoll, attrappen = _kette(tmp_path)
    return protokoll, _lauf(tmp_path, ordner, attrappen)


def test_ohne_rotation_dreht_blender_je_kamera(tmp_path, monkeypatch):
    """Zwei Kameras, zwei Blender-Laeufe: jeder mit seiner Kamera, keiner mit einer Drehung —
    der Runner rechnet sie je Kamera aus den Lichtdaten."""
    protokoll, antwort = _stimmungsauftrag(tmp_path, monkeypatch, {"preset": "mittag"})
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    laeufe = protokoll["multipass"]
    assert sorted(kw["kamera"] for kw in laeufe) == ["nNW", "sSE"]
    for kw in laeufe:
        assert "umgebung_drehung" not in kw
        licht = json.loads(kw["umgebung_licht"])
        assert licht["sonne_seitlich_grad"] == 65.0 and licht["sonne_seite"] == "links"
    assert antwort["ergebnis"]["angewandt"]["environment"]["drehung_weg"] == "zur_kamera"


def test_ein_bestelltes_rotation_grad_hat_vorrang(tmp_path, monkeypatch):
    protokoll, antwort = _stimmungsauftrag(tmp_path, monkeypatch,
                                           {"preset": "mittag", "rotationGrad": 0},
                                           richtungen=("sSE",))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert protokoll["multipass"][0]["umgebung_drehung"] == 0.0
    assert antwort["ergebnis"]["angewandt"]["environment"]["drehung_weg"] == "bestellt"


def test_der_schluessel_bildet_kamera_und_drehung_ab(tmp_path):
    """Die Drehung entsteht in Blender aus Kamera und Lichtdaten — beide stehen im Schluessel
    des Zwischenspeichers, eine bestellte Drehung ebenso."""
    glb, hdr = tmp_path / "m.glb", tmp_path / "h.hdr"
    glb.write_bytes(b"glb")
    hdr.write_bytes(b"#?RADIANCE\n")
    licht = json.dumps(stimmung.licht_der_stimmung("mittag"), sort_keys=True)
    e = dict(glb_path=str(glb), up_axis="Y", aufloesung=480, samples=64,
             umgebung_hdr=str(hdr), umgebung_licht=licht)
    s = abholer.multipass_schluessel(dict(e, kamera="sSE"), blender="4.2")
    n = abholer.multipass_schluessel(dict(e, kamera="nNW"), blender="4.2")
    gedreht = abholer.multipass_schluessel(dict(e, kamera="sSE", umgebung_drehung=0.0),
                                           blender="4.2")
    seite = abholer.multipass_schluessel(dict(e, kamera="sSE", umgebung_licht=json.dumps(
        stimmung.licht_der_stimmung("mittag", sonne_seite="rechts"), sort_keys=True)),
        blender="4.2")
    assert len({s, n, gedreht, seite}) == 4


# ====================================================================== B2 · weicher Rueckfall

def test_der_weiche_rueckfall_hat_einen_grossen_winkel():
    for preset in ("morgen", "winter", "mittag", "abend"):
        licht = stimmung.licht_der_stimmung(preset)
        assert 20.0 <= licht["winkel_weich_grad"] <= 30.0, preset
        weich = stimmung.lampe_aus_himmel({"gefunden": False, "richtung_bild": [1, 0, 0.5],
                                           "e_himmel_h": 1.0}, licht)
        assert weich["art"] == "weich" and weich["winkel_grad"] == licht["winkel_weich_grad"]
        hart = stimmung.lampe_aus_himmel({"gefunden": True, "richtung_bild": [1, 0, 0.5],
                                          "e_himmel_h": 1.0}, licht)
        assert hart["art"] == "sonne" and hart["winkel_grad"] == licht["winkel_grad"] <= 2.0
    # Ohne Sonne bleibt der grosse Winkel der Stimmung (bedeckt 40, nebel 50).
    for preset in ("bedeckt", "nebel", "blaue-stunde", "weiss"):
        licht = stimmung.licht_der_stimmung(preset)
        lampe = stimmung.lampe_aus_himmel({"gefunden": False, "richtung_bild": [1, 0, 0.5],
                                           "e_himmel_h": 1.0}, licht)
        assert lampe["winkel_grad"] == stimmung.STIMMUNGEN[preset]["winkel_grad"]
    # Alte Lichtdaten ohne eigenen Wert: mindestens WEICH_WINKEL_GRAD.
    alt = {"sonne": True, "sonnen_staerke": 3.0, "winkel_grad": 1.0}
    assert stimmung.lampe_aus_himmel({"gefunden": False, "richtung_bild": [1, 0, 0.5]},
                                     alt)["winkel_grad"] == stimmung.WEICH_WINKEL_GRAD


# ====================================================================== B3 · Blaue Stunde, abend

def test_die_blaue_stunde_ist_dunkler_mit_zwei_stufen_abstand():
    licht = stimmung.licht_der_stimmung("blaue-stunde")
    assert licht["belichtung_ev"] == -1.5 and licht["hintergrund_abstand_ev"] == 2.0
    haus = 0.5
    aus = stimmung.hintergrund_mit_abstand([0.4] * 3, [0.45] * 3, haus, richtung="dunkler",
                                           abstand_ev=licht["hintergrund_abstand_ev"])
    assert max(stimmung.leuchtdichte(aus["horizont"]),
               stimmung.leuchtdichte(aus["zenit"])) <= haus / 4.0 + 1e-6
    # Die anderen Stimmungen behalten eine Stufe.
    assert stimmung.licht_der_stimmung("mittag")["hintergrund_abstand_ev"] == 1.0


def test_abend_ist_dunkler_belichtet_und_bestellt_keine_nacht():
    eintrag = stimmung.STIMMUNGEN["abend"]
    assert eintrag["belichtung_ev"] == -0.5, "Belichtung, nicht Sonnenstaerke (Verhaeltnis bleibt)"
    assert eintrag["sonnen_staerke"] == 3.5
    assert "glowing" not in eintrag["prompt_en"] and "interiors" not in eintrag["prompt_en"]
    satz, schon = stimmung.prompt_satz("abend", "a house")
    assert satz == eintrag["prompt_en"] and not schon
    assert stimmung.prompt_satz("abend", satz) == (None, True), "merkmale tragen den Satz"
    assert not any(w in eintrag["prompt_en"].split() for w in prompts.BAUTEILWOERTER)


def test_licht_mit_schatten_bleibt_bei_den_stimmungen_mit_sonne():
    for preset in stimmung.PRESETS:
        assert stimmung.licht_der_stimmung(preset)["sonne"] is (preset in MIT_SONNE)


# ====================================================================== B4 · gemischter Prompt

GEMISCHT = "zeitgenoessisches Wohnhaus, Sichtbeton, Architekturfotografie, no people"


def test_der_gemischte_prompt_wird_uebersetzt_und_der_englische_teil_bleibt():
    assert sprache.sieht_englisch_aus(GEMISCHT)["englisch"] is True, "der Befund aus 294"
    assert sprache.ist_gemischt(GEMISCHT) and sprache.ist_deutsch(GEMISCHT)
    aus = sprache.uebersetze(GEMISCHT)
    assert aus["noetig"] is True and aus["anlass"] == "gemischt"
    assert set(aus["evidenz"]) == {"wohnhaus", "sichtbeton", "architekturfotografie"}
    assert aus["uebersetzt"] == ("contemporary residential building, exposed concrete, "
                                 "architectural photography, no people")
    assert "Gemischt" in sprache.sprachwarnung(GEMISCHT)


@pytest.mark.parametrize("englisch", [
    "overcast sky, no people", "a modern concrete building with glass facade, four storeys",
    "exterior view, afternoon light, soft shadows", "photorealistic render of a house",
    "I can see the wind in the film", "warm light, no people, loggia with patina",
])
def test_ein_englischer_prompt_bleibt_unberuehrt(englisch):
    assert sprache.ist_gemischt(englisch) is False
    aus = sprache.uebersetze(englisch)
    assert aus["noetig"] is False and aus["uebersetzt"] == englisch


def test_der_gemischte_prompt_geht_englisch_in_den_ki_schritt():
    s = kosmo_szene.lies_szene({"geometry": {"path": "/x/m.glb", "format": "glb"},
                                "cameras": "auto", "render": {}, "style": {"prompt": GEMISCHT},
                                "vis": {"material_vorne": False}})
    # «material_vorne: false» — seit Entscheid 126 stuende sonst der Stoff vorne.
    assert s["prompt"].startswith("contemporary residential building, exposed concrete")
    assert s["prompt_sprache"]["noetig"] is True
    assert s["prompt_original"] == GEMISCHT


# ====================================================================== B5 · Vermerk bei «voll»

def test_der_vermerk_der_vollen_guete_nur_wenn_hochgerechnet():
    steuer = {"hochgerechnet": True, "ki_groesse": [1024, 640], "grundlage_groesse": [960, 600],
              "verkleinert": True, "weg": "pillow"}
    vermerk = abholer._guete_vermerk_voll("z-image-turbo", steuer)
    assert vermerk["guete"] == kosmo_szene.GUETE_VOLL and vermerk["hochgerechnet"] is True
    assert vermerk["ki_groesse"] == [1024, 640] and vermerk["grundlage_groesse"] == [960, 600]
    assert any("960x600" in h and "1024x640" in h for h in vermerk["hinweise"])
    assert abholer._guete_vermerk_voll("z-image-turbo", dict(steuer, hochgerechnet=False)) is None
    assert abholer._guete_vermerk_voll("z-image-turbo", None) is None


def test_bei_voll_steht_der_vermerk_am_urteil_ohne_vorschausatz(tmp_path, monkeypatch):
    pytest.importorskip("PIL")
    from test_grundlage_varianten import _vertrag
    from test_vorschau_guete import _attrappen, _rechne
    monkeypatch.setattr(abholer, "ki_mindest_lange_seite", lambda _name: 256)
    _protokoll, attrappen = _attrappen(tmp_path)
    ordner, antwort = _rechne(tmp_path, attrappen, "voll", guete="voll")
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    for k in abholer.lies_befund(ordner)["kameras"]:
        vermerk = k[kosmo_szene.URTEIL_GUETE]
        assert vermerk["guete"] == "voll" and vermerk["hochgerechnet"] is True
        assert vermerk["ki_groesse"] == [256, 160]
    assert not _vertrag(ordner)["qa"]["verdict"]["reason"].startswith(
        kosmo_szene.VORSCHAU_ANFANG)


# ====================================================================== B6 · ueber den Umriss

B, H = 40, 30


def _szene_umriss(*, anbau=False, wolke=False):
    """Haus Spalten 16–23, Zeilen 8–21; Platte Zeile 22; Himmel darueber, Boden darunter.
    Nähe (Disparität): Haus 1,0, Platte 1,2, Boden 1,5, Himmel 0,02. ``anbau``: das KI-Bild baut
    links neben dem Haus (Spalten 2–9, Zeilen 10–21) einen Flügel in Hausnähe; ``wolke``: ein
    heller Fleck am Himmel, weit weg."""
    soll, haus, naehe, boden = [], [], [], []
    for y in range(H):
        for x in range(B):
            ist_haus = 16 <= x <= 23 and 8 <= y <= 21
            platte = y == 22
            soll.append(ist_haus or platte)
            haus.append(ist_haus)
            boden.append(y > 22)
            if ist_haus:
                naehe.append(1.0)
            elif platte:
                naehe.append(1.2)
            elif y > 22:
                naehe.append(1.5)
            elif anbau and 2 <= x <= 9 and 10 <= y <= 21:
                naehe.append(1.05)
            elif wolke and 28 <= x <= 36 and 1 <= y <= 5:
                # Wolken liegen bei Depth Anything V2 wie der Himmel bei null (gemessen an
                # 295-297, Eichung auf-20261021-297): unter einem Zwanzigstel der Hausnaehe.
                # Bis 297 stand hier 0,1 — seit der Eichung zaehlt das als ferne Struktur.
                naehe.append(0.03)
            else:
                naehe.append(0.02)
    return naehe, soll, haus, boden


def test_neue_baumasse_neben_dem_haus_wird_gezaehlt():
    naehe, soll, haus, boden = _szene_umriss(anbau=True)
    aus = baumasse.ausserhalb_umriss(naehe, soll, B, H, haus=haus, trennhilfe=boden)
    assert aus["rand_px"] == 3
    # Der Anbau (8 x 12) liegt im Bereich bis auf die drei Zeilen ueber der Platte (Rand).
    assert aus["n_neu"] == 8 * 9 and aus["n_haus"] == 8 * 14
    assert aus["anteil_haus"] == pytest.approx(72 / 112, abs=1e-4)
    assert 0 < aus["anteil_hintergrund"] < 1 and not aus["grund"]


def test_himmel_wolken_und_boden_zaehlen_nicht():
    for wolke in (False, True):
        naehe, soll, haus, boden = _szene_umriss(wolke=wolke)
        aus = baumasse.ausserhalb_umriss(naehe, soll, B, H, haus=haus, trennhilfe=boden)
        assert aus["n_neu"] == 0 and aus["anteil_haus"] == 0.0
    # Ohne gedachten Boden: nur ueber dem Fuss des Hauses — der Boden davor ist naeher.
    naehe, soll, haus, _ = _szene_umriss()
    assert baumasse.ausserhalb_umriss(naehe, soll, B, H, haus=haus)["n_neu"] == 0
    # Der Rand um die Silhouette zaehlt nicht (dort verwischt der Schaetzer).
    naehe = list(naehe)
    for y in range(8, 22):
        naehe[y * B + 15] = naehe[y * B + 24] = 1.0
    assert baumasse.ausserhalb_umriss(naehe, soll, B, H, haus=haus)["n_neu"] == 0


def test_nie_eine_ausnahme():
    assert baumasse.ausserhalb_umriss([1.0], [True], B, H)["anteil_haus"] is None
    leer = baumasse.ausserhalb_umriss([0.0] * (B * H), [False] * (B * H), B, H)
    assert leer["anteil_haus"] is None and leer["grund"]
    assert baumasse.erweitere([True] + [False] * 8, 3, 3, 1) == [True, True, False,
                                                                 True, True, False,
                                                                 False, False, False]


def test_die_zahl_kommt_aus_der_geometrie_qa(tmp_path):
    from test_tiefenschaetzer import attrappe
    pfad = tmp_path / "bild.png"
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n")
    naehe, soll, haus, boden = _szene_umriss(anbau=True)
    soll_m = [20.0 if s else math.inf for s in soll]
    aus = ts.qa_gegen_soll(pfad, soll_m, modell=attrappe(naehe), breite=B, hoehe=H,
                           maske=haus, trennhilfe=boden)
    assert aus["ausserhalb_umriss"]["anteil_haus"] == pytest.approx(72 / 112, abs=1e-4)


def _urteil(kamera, anteil, **mehr):
    return dict({"kamera": kamera, "score": 0.7, "bestanden": True, "geom_iou": 0.5,
                 "spearman": -0.4, "n_gemeinsam": 10, "n_soll": 12, "n_ist": 12},
                **({"ausserhalb_umriss": {"anteil_haus": anteil}} if anteil is not None else {}),
                **mehr)


def test_im_ergebnis_die_groesste_mit_satz_und_der_vertrag_bleibt():
    je = [{"kamera": "sSE", "geometrie_urteil": _urteil("sSE", 0.82)},
          {"kamera": "nNW", "geometrie_urteil": _urteil("nNW", 0.1)}]
    e = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png", "b.png"],
                                 geometrie_urteil=je[0]["geometrie_urteil"], je_kamera=je)
    assert e["qa"][kosmo_szene.FELD_AUSSERHALB] == 0.82
    assert [k.get(kosmo_szene.FELD_AUSSERHALB) for k in e["qa_je_kamera"]] == [0.82, 0.1]
    assert any(h.startswith(kosmo_szene.SATZ_AUSSERHALB) and "'sSE'" in h
               for h in e["qa"]["verdict"].get("hinweise") or ())
    # Dieselben Urteile ohne die neue Zahl: jedes bestehende Feld gleich.
    je_alt = [{"kamera": k["kamera"], "geometrie_urteil": _urteil(k["kamera"], None)}
              for k in je]
    alt = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png", "b.png"],
                                   geometrie_urteil=je_alt[0]["geometrie_urteil"],
                                   je_kamera=je_alt)
    assert kosmo_szene.FELD_AUSSERHALB not in alt["qa"], "kein null (ihr .optional())"
    assert e["qa"]["geometry"] == alt["qa"]["geometry"]
    for neu, vorher in zip(e["qa_je_kamera"], alt["qa_je_kamera"]):
        assert {k: v for k, v in neu.items() if k != kosmo_szene.FELD_AUSSERHALB} == vorher
    for feld in set(alt) - {"qa", "qa_je_kamera", "hinweise"}:
        assert e[feld] == alt[feld], feld
    assert [h for h in e["hinweise"] if not h.startswith(kosmo_szene.SATZ_AUSSERHALB)] == \
        list(alt["hinweise"])
    # Unter der Schwelle: Zahl ja, Satz nein.
    klein = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"],
                                     geometrie_urteil=_urteil("s", 0.1))
    assert klein["qa"][kosmo_szene.FELD_AUSSERHALB] == 0.1
    assert not any(h.startswith(kosmo_szene.SATZ_AUSSERHALB)
                   for h in klein["qa"]["verdict"].get("hinweise") or ())


def test_ohne_gemeinsame_silhouette_weiter_kein_null_in_geometry_gates():
    """Die Probe aus 292 mit der neuen Zahl daneben: ``geometry_gates`` traegt weiter kein
    ``null`` (KosmoOrbit v0.1.8 verwirft sonst das ganze Ergebnis)."""
    from test_heimfehler_auf292 import test_ohne_gemeinsame_silhouette_kein_null_in_geometry_gates
    test_ohne_gemeinsame_silhouette_kein_null_in_geometry_gates()
    assert baumasse.SCHWELLE_ANTEIL_HAUS == 0.25 and "gesetzt" in baumasse.HERKUNFT

