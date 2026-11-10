"""Fensterprüfung je Bauteil (A0291, «Masstreue je Bauteil»): Ein einzeln übermaltes Fenster fällt auf.

Der Eichsatz ist synthetisch und im Repo erzeugbar (``tests/fenster_paare.py``, 105 Paare): je
Szene drei Paare mit EINEM übermalten Fenster (grau, Fassadenfarbe, warm) und vier Gegenfälle
(dunkel spiegelndes Glas, Schatten, Vorhang, gemischte Scheiben), über fünf Fassaden und drei
Blickrichtungen. Dazu die echten Ausschnitte von A0158 (``fixtures/glas-v5``) als Gegenprobe.

Zielfunktion des Auftrags: mindestens 90 % der einzeln übermalten Fenster erkannt (am richtigen
Ort), 0 Fehlalarme, und kein bestehendes Urteil ändert sich.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import fenster_paare
from aiimaging import bildlesen, fenster_bauteile, varianten

ECHT = Path(__file__).parent / "fixtures" / "glas-v5"
AUSSCHNITT = json.loads((ECHT / "ausschnitt.json").read_text(encoding="utf-8"))
GLAS = varianten.glasfarben(fenster_paare.TABELLE)
AUSSER = varianten.nicht_fassade_farben(fenster_paare.TABELLE)


@pytest.fixture(scope="module")
def messung():
    """Der ganze Eichsatz einmal durch ``varianten.fenster_gehalten`` (rund 25 Sekunden)."""
    return fenster_paare.miss()


def _echt(name):
    punkte, breite, _ = bildlesen.lies_png_farben(ECHT / f"{name}.png")
    return list(punkte), breite


def _echt_befund(ki):
    grund, breite = _echt("grund")
    kennung, _ = _echt("kennung")
    return fenster_bauteile.pruefe_bauteile(ki, grund, kennung, varianten.glasfarben(AUSSCHNITT["tabelle"]),
                                            breite=breite)


# ---------------------------------------------------------------- der Eichsatz und sein Erzeuger

def test_der_eichsatz_hat_mindestens_vierzig_paare_in_der_verlangten_mischung(messung):
    assert messung["paare"] == 105 >= 40
    assert messung["uebermalt"] == 45 and messung["gegenfaelle"] == 60
    assert {art: n for art, (_, n) in messung["je_art"].items()} == {"grau": 15, "fassade": 15, "warm": 15}
    assert {blick: n for blick, (_, n) in messung["je_blick"].items()} == {
        "augenhoehe": 15, "erhoeht": 15, "von-oben": 15}
    faelle = [b["paar"]["fall"] for b in messung["befunde"].values() if not b["paar"]["uebermalt"]]
    assert {f: faelle.count(f) for f in set(faelle)} == {"dunkel": 15, "schatten": 15, "vorhang": 15,
                                                         "gemischt": 15}
    assert {b["paar"]["anordnung"] for b in messung["befunde"].values()} == {"einzel", "band"}


def test_der_erzeuger_ist_fest_gesaet():
    a = fenster_paare._paar(1, 2, "grau", 0)
    b = fenster_paare._paar(1, 2, "grau", 0)
    assert a["ki"] == b["ki"] and a["grund"] == b["grund"] and a["kennung"] == b["kennung"]
    assert fenster_paare._paar(1, 2, "grau", 0, "andere-saat")["ki"] != a["ki"]


def test_in_jedem_uebermalungs_paar_ist_genau_ein_fenster_uebermalt(messung):
    for name, b in messung["befunde"].items():
        ziel = b["paar"]["ziel"]
        assert (ziel is not None) is b["paar"]["uebermalt"], name
        if ziel:
            assert ziel["x1"] - ziel["x0"] >= 20 and ziel["y1"] - ziel["y0"] >= 6, name


# ---------------------------------------------------------------- der Stand vor A0291

def test_die_pruefung_je_band_allein_merkt_die_einzelnen_fenster_nicht(messung):
    """Der heutige Wert vor A0291: ``gehalten`` fällt bei höchstens 5 von 45, und ohne Ort."""
    assert messung["band_merkt"] <= 5, messung["band_merkt"]


# ---------------------------------------------------------------- die Zielfunktion

def test_zielwert_mindestens_neunzig_prozent_erkannt(messung):
    assert messung["rate"] >= 0.9, (messung["erkannt"], messung["verfehlt"])


def test_zielwert_null_fehlalarme(messung):
    assert messung["fehlalarme"] == 0, messung["falsch"]


@pytest.mark.parametrize("art", fenster_paare.UEBERMALUNGEN)
def test_jede_uebermalungsart_einzeln(messung, art):
    erkannt, anzahl = messung["je_art"][art]
    assert erkannt / anzahl >= 0.8, (art, erkannt, anzahl)


@pytest.mark.parametrize("blick", [b[0] for b in fenster_paare.BLICKE])
def test_jede_blickrichtung_einzeln(messung, blick):
    erkannt, anzahl = messung["je_blick"][blick]
    assert erkannt / anzahl >= 0.8, (blick, erkannt, anzahl)


@pytest.mark.parametrize("fall", fenster_paare.GEGENFAELLE)
def test_kein_gegenfall_meldet_ein_uebermaltes_fenster(messung, fall):
    for name, b in messung["befunde"].items():
        if b["paar"]["fall"] == fall:
            assert b["befund"]["bauteil_uebermalt"] == [], name
            assert b["befund"]["bauteil_hinweis"] is None, name


@pytest.mark.parametrize("name,art", [
    ("putz-weiss/augenhoehe/fassade", fenster_bauteile.ART_WAND),
    ("putz-beige/erhoeht/warm", fenster_bauteile.ART_WARM),
    ("klinker-rot/von-oben/grau", fenster_bauteile.ART_REIHE),
])
def test_der_fund_sagt_welches_fenster_und_warum(messung, name, art):
    """Je eine Gegenprobe für Augenhöhe, erhöht und von oben, und für jede der drei Regeln.

    Fassadenfarbe ist «wie die Wand daneben»; grau in einer farbigen Wand hebt sich von der Wand
    ab und fällt erst am Glaston der Nachbarfenster auf.
    """
    b = messung["befunde"][name]
    funde = [x for x in b["befund"]["bauteile"] if x["urteil"] == fenster_bauteile.UEBERMALT]
    assert len(funde) == 1, funde
    assert fenster_paare._im_ziel(funde[0]["ort"], b["paar"]["ziel"]) >= 0.5
    assert funde[0]["art"] == art
    assert funde[0]["nr"] in b["befund"]["bauteil_uebermalt"]
    satz = b["befund"]["bauteil_hinweis"]
    assert satz.startswith(fenster_bauteile.SATZ_BAUTEIL_UEBERMALT)
    assert f"x {funde[0]['ort']['x0']} bis {funde[0]['ort']['x1']}" in satz and funde[0]["lage"] in satz
    assert chr(0x2013) not in satz                         # der Halbgeviertstrich ist im Projekt gesperrt


def test_im_band_ist_der_fund_ein_feld_und_das_band_bleibt_als_gehalten_stehen(messung):
    b = messung["befunde"]["putz-weiss/augenhoehe/warm"]
    assert b["paar"]["anordnung"] == "band"
    fund = next(x for x in b["befund"]["bauteile"] if x["urteil"] == fenster_bauteile.UEBERMALT)
    assert fund["feld"] is True
    band = next(x for x in b["befund"]["bauteile"]
                if x["glasstueck"] == fund["glasstueck"] and x["urteil"] != fenster_bauteile.UEBERMALT)
    assert band["urteil"] == fenster_bauteile.GEHALTEN and band["felder_uebermalt"] >= 1


# ---------------------------------------------------------------- kein bestehendes Urteil ändert sich

def test_der_hinweis_aendert_das_urteil_gehalten_nicht(messung, monkeypatch):
    """Dieselben Paare ohne die Prüfung je Bauteil: ``gehalten``, ``anteil`` und Bänder gleich."""
    def kaputt(*a, **k):
        raise RuntimeError("abgeschaltet")
    monkeypatch.setattr(fenster_bauteile, "pruefe_indizes", kaputt)
    for paar in fenster_paare.eichsatz()[::9]:
        ohne = varianten.fenster_gehalten(paar["ki"], paar["grund"], paar["kennung"], GLAS,
                                          ausser=AUSSER, breite=paar["breite"])
        mit = messung["befunde"][paar["name"]]["befund"]
        assert ohne["bauteile"] is None and "abgeschaltet" in ohne["bauteil_grund"]
        for feld in ("gehalten", "anteil", "baender", "band_nicht_gehalten", "trennung", "farbton"):
            assert ohne[feld] == mit[feld], (paar["name"], feld)


def test_ein_uebermaltes_einzelfenster_laesst_gehalten_stehen_und_steht_als_hinweis_da(messung):
    """Der Kern des Auftrags: Das Urteil der Kamera hält, der Hinweis nennt das Fenster."""
    b = messung["befunde"]["putz-beige/augenhoehe/fassade"]["befund"]
    assert b["gehalten"] is True and b["band_nicht_gehalten"] == []
    assert len(b["bauteil_uebermalt"]) == 1 and b["bauteil_hinweis"]


def test_ohne_breite_gibt_es_keine_bauteile():
    paar = fenster_paare._paar(0, 0, "dunkel", 3)
    befund = varianten.fenster_gehalten(paar["ki"], paar["grund"], paar["kennung"], GLAS, ausser=AUSSER)
    assert "bauteile" not in befund and "baender" not in befund


def test_fenster_aus_bildern_traegt_den_hinweis_bis_in_den_bericht_der_kamera(tmp_path):
    """Der Weg des Abholers: drei Bilddateien hinein, der Befund mit Hinweis heraus."""
    paar = fenster_paare._paar(1, 0, "fassade", 1)
    for name in ("ki", "grund", "kennung"):
        fenster_paare.schreibe_png(tmp_path / f"{name}.png", paar[name], paar["breite"], paar["hoehe"])
    befund = varianten.fenster_aus_bildern(tmp_path / "ki.png", tmp_path / "grund.png",
                                           tmp_path / "kennung.png", paar["tabelle"])
    assert befund["gehalten"] is True
    assert len(befund["bauteil_uebermalt"]) == 1
    assert befund["bauteil_hinweis"].startswith(fenster_bauteile.SATZ_BAUTEIL_UEBERMALT)
    json.dumps(befund)                                    # der Befund geht als JSON ins Ergebnis


# ---------------------------------------------------------------- echte Bildgrösse: breite Rahmen

def _vergroessert(paar, k):
    def gross(bild):
        aus = []
        for y in range(paar["hoehe"]):
            zeile = [p for p in bild[y * paar["breite"]:(y + 1) * paar["breite"]] for _ in range(k)]
            for _ in range(k):
                aus.extend(zeile)
        return aus
    return gross(paar["ki"]), gross(paar["grund"]), gross(paar["kennung"])


def test_ein_breiter_rahmen_ist_nicht_die_wand():
    """Im vierfachen Massstab ist der Rahmen vier Bildpunkte breit und füllt den Ring von v5 zur Hälfte.

    Die erste Fassung verglich dort Glas mit Rahmen und meldete dunkle Scheiben als übermalt
    (13 Fehlalarme im vierfachen Massstab). Der Ring wächst darum mit der Höhe des Bauteils.
    """
    paar = fenster_paare._paar(3, 2, "dunkel", 3)          # Klinker, von oben, Einzelfenster
    assert paar["anordnung"] == "einzel"
    ki, grund, kennung = _vergroessert(paar, 4)
    befund = fenster_bauteile.pruefe_bauteile(ki, grund, kennung, GLAS, ausser=AUSSER,
                                              breite=paar["breite"] * 4)
    assert befund["uebermalt"] == [], befund["hinweis"]
    assert all(b["urteil"] == fenster_bauteile.GEHALTEN for b in befund["bauteile"])


def test_im_vierfachen_massstab_wird_das_uebermalte_fenster_weiter_gefunden():
    paar = fenster_paare._paar(3, 2, "warm", 2)
    ki, grund, kennung = _vergroessert(paar, 4)
    befund = fenster_bauteile.pruefe_bauteile(ki, grund, kennung, GLAS, ausser=AUSSER,
                                              breite=paar["breite"] * 4)
    ziel = {k: v * 4 + (3 if k in ("x1", "y1") else 0) for k, v in paar["ziel"].items()}
    wert = fenster_paare.werte(dict(paar, ziel=ziel), befund["bauteile"])
    assert wert == {"erkannt": True, "fehlalarme": 0}


# ---------------------------------------------------------------- die echten Ausschnitte (A0158)

def test_echter_voller_lauf_kein_fund():
    befund = _echt_befund(_echt("ki_voll")[0])
    assert befund["uebermalt"] == [] and befund["hinweis"] is None
    assert [b["urteil"] for b in befund["bauteile"]] == [fenster_bauteile.GEHALTEN] * 2


def test_echte_vorschau_beide_baender_uebermalt():
    befund = _echt_befund(_echt("ki_vorschau")[0])
    funde = [b for b in befund["bauteile"] if b["urteil"] == fenster_bauteile.UEBERMALT]
    assert {b["glasstueck"] for b in funde} == {0, 1}


def test_echtes_band_mit_einem_uebermalten_abschnitt_nennt_den_abschnitt():
    """Ein Stück der echten grauen Übermalung in den vollen Lauf gesetzt: ein Fenster im Band.

    Der Ausschnitt ist nur zwei Felder breit; dass die Prüfung je Band hier ebenfalls anschlägt,
    liegt daran. Die Lücke des Auftrags (ein Fenster von fünf) zeigt der synthetische Eichsatz.
    """
    voll, breite = _echt("ki_voll")
    vorschau, _ = _echt("ki_vorschau")
    von, bis = 40, 170                                    # Spalten im Obergeschoss, gut 1,4 Felder
    ki = [vorschau[i] if von <= i % breite <= bis and i // breite < AUSSCHNITT["grenze_og_eg"] else p
          for i, p in enumerate(voll)]
    befund = _echt_befund(ki)
    funde = [b for b in befund["bauteile"] if b["urteil"] == fenster_bauteile.UEBERMALT]
    assert len(funde) == 1 and funde[0]["feld"] is True and funde[0]["glasstueck"] == 0
    # Der Ort stimmt auf ein halbes Feld genau (ein Feld ist hier so breit wie das Band hoch, rund
    # 100 Bildpunkte): Der Fund enthält den Abschnitt, und ein Teil des Bands bleibt gehalten.
    assert funde[0]["ort"]["x0"] <= von and bis <= funde[0]["ort"]["x1"]
    assert funde[0]["ort"]["y1"] < AUSSCHNITT["grenze_og_eg"]
    rest = next(b for b in befund["bauteile"] if b["glasstueck"] == 0 and b is not funde[0])
    assert rest["urteil"] == fenster_bauteile.GEHALTEN and rest["felder_uebermalt"] < rest["felder"]


def test_grenze_ein_abschnitt_schmaler_als_ein_feld_wird_nicht_gemeldet():
    """Die benannte Grenze: Im Band zählt ein Fund erst ab etwa 1,2 Feldbreiten (Schutz vor Vorhängen)."""
    voll, breite = _echt("ki_voll")
    vorschau, _ = _echt("ki_vorschau")
    ki = [vorschau[i] if 60 <= i % breite <= 150 and i // breite < AUSSCHNITT["grenze_og_eg"] else p
          for i, p in enumerate(voll)]
    assert _echt_befund(ki)["uebermalt"] == []


# ---------------------------------------------------------------- die Bibliothek (Regel 4)

def test_ohne_glas_ist_die_liste_leer():
    kennung = [(200, 10, 10)] * 400
    befund = fenster_bauteile.pruefe_bauteile(kennung, kennung, kennung, {(10, 200, 30)}, breite=20)
    assert befund == {"bauteile": [], "uebermalt": [], "hinweis": None,
                      "methode": fenster_bauteile.METHODE_BAUTEILE}


def test_ein_zu_kleines_fenster_ist_nicht_messbar_und_sagt_warum():
    breite, hoehe = 40, 30
    kennung = [(200, 10, 10)] * (breite * hoehe)
    for y in range(10, 13):
        for x in range(10, 14):
            kennung[y * breite + x] = (10, 200, 30)
    bild = [(159, 179, 191) if k == (10, 200, 30) else (200, 180, 150) for k in kennung]
    befund = fenster_bauteile.pruefe_bauteile(bild, bild, kennung, {(10, 200, 30)}, breite=breite)
    (bauteil,) = befund["bauteile"]
    assert bauteil["urteil"] == fenster_bauteile.NICHT_MESSBAR and "Zu klein" in bauteil["grund"]
    assert bauteil["ort"] == {"x0": 10, "y0": 10, "x1": 13, "y1": 12}


def test_glas_das_im_grundbild_wie_die_wand_aussieht_ist_nicht_messbar():
    breite, hoehe = 60, 40
    kennung = [(200, 10, 10)] * (breite * hoehe)
    for y in range(10, 30):
        for x in range(20, 40):
            kennung[y * breite + x] = (10, 200, 30)
    bild = [(150, 150, 150)] * (breite * hoehe)
    (bauteil,) = fenster_bauteile.pruefe_bauteile(bild, bild, kennung, {(10, 200, 30)},
                                                  breite=breite)["bauteile"]
    assert bauteil["urteil"] == fenster_bauteile.NICHT_MESSBAR and "wie die Wand" in bauteil["grund"]


def test_falsche_breite_und_ungleiche_laengen_werden_gemeldet():
    bild = [(0, 0, 0)] * 100
    with pytest.raises(ValueError):
        fenster_bauteile.pruefe_bauteile(bild, bild, bild, {(1, 2, 3)}, breite=7)
    with pytest.raises(ValueError):
        fenster_bauteile.pruefe_bauteile(bild[:50], bild, bild, {(1, 2, 3)}, breite=10)


def test_die_maske_grenzt_glas_und_wand_ein():
    """Ausserhalb der Bauwerksmaske zählt weder Glas noch Wand."""
    paar = fenster_paare._paar(1, 0, "fassade", 1)
    maske = [i % paar["breite"] < 60 for i in range(len(paar["kennung"]))]
    befund = fenster_bauteile.pruefe_bauteile(paar["ki"], paar["grund"], paar["kennung"], GLAS,
                                              breite=paar["breite"], maske=maske, ausser=AUSSER)
    assert befund["bauteile"] and all(b["ort"]["x1"] < 60 for b in befund["bauteile"])


def test_das_modul_bleibt_reine_bibliothek():
    quelle = Path(fenster_bauteile.__file__).read_text(encoding="utf-8")
    einfuhren = [z.strip() for z in quelle.splitlines() if z.startswith(("import ", "from "))]
    assert einfuhren == ["from __future__ import annotations", "import math",
                         "from . import varianten as _v"]
