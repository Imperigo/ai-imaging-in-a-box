"""A0299 «Leeres Grundstück fällt durch» — die Abwesenheitsprüfung und ihr Messsatz.

Der Befund: Ein Bild ohne Bauwerk besteht ``geometrie_gate`` (belegt 0,9530 gegen 0,9839
beim perfekten Bild, ``docs/GEOM_IOU_HALLUZINATION_2026-08-21.md``). Diese Proben halten
drei Dinge fest:

1. den **heutigen Wert** des Tors ohne Maske auf dem synthetischen Satz (er bleibt, wie er
   ist: 59 von 72 Fehl-Fällen bestehen),
2. den **Zielwert** mit eingehängter Abwesenheitsprüfung (72 von 72 fallen durch, kein
   Fehlalarm unter 60 guten Bildern),
3. die **Nullproben**, an denen die Vorgänger des Masses gescheitert sind (in Y verschobene
   Maske, leeres Ortsfeld, Rauschen).

Alle Karten sind nachgestellt (``tests/abwesenheit_satz.py``). Was hier grün ist, ist an
keinem erzeugten Bild gemessen.
"""
from __future__ import annotations

import random

import pytest

import abwesenheit_satz as satz
from aiimaging import gate
from aiimaging import geometrie_qa as g
from aiimaging import tiefenschaetzer as ts


@pytest.fixture(scope="module")
def paare():
    return satz.satz()


def _urteil(paar, *, mit_maske: bool) -> dict:
    """Das Tor, wie es der Kettenlauf fährt: Hintergrund nach Vorbild des Soll markiert."""
    wort = ts.POLARITAET_DISPARITAET if paar.polaritaet < 0 else ts.POLARITAET_TIEFE
    markiert = ts.markiere_hintergrund(paar.roh, polaritaet=wort, strategie=ts.HG_WIE_SOLL,
                                       n_geometrie=sum(g.silhouette(paar.soll)))["tiefen"]
    if not mit_maske:
        return g.geometrie_gate(paar.soll, markiert, polaritaet=paar.polaritaet)
    return g.geometrie_gate(paar.soll, markiert, polaritaet=paar.polaritaet,
                            maske=paar.maske, breite=paar.breite, ist_roh=paar.roh)


@pytest.fixture(scope="module")
def urteile_ohne(paare):
    return {p.name: _urteil(p, mit_maske=False) for p in paare}


@pytest.fixture(scope="module")
def urteile_mit(paare):
    return {p.name: _urteil(p, mit_maske=True) for p in paare}


# ------------------------------------------------------------------ der Satz selbst

def test_der_satz_deckt_den_verlangten_bereich(paare):
    """Mindestens 40 Paare, Boden 20 bis 80 %, Haus 10 bis 60 %, alle drei Fehlarten."""
    assert len(paare) == 132
    assert sum(p.fehlt for p in paare) == 72 and sum(not p.fehlt for p in paare) == 60
    boden = [p.bodenanteil for p in paare]
    haus = [p.hausanteil for p in paare]
    assert 0.19 <= min(boden) <= 0.21 and 0.79 <= max(boden) <= 0.81
    assert 0.09 <= min(haus) <= 0.11 and 0.59 <= max(haus) <= 0.61
    assert {p.art for p in paare} == set(satz.GUT) | set(satz.FEHL)
    assert {p.polaritaet for p in paare} == {-1, +1}


def test_fehl_und_gut_sind_am_bild_ablesbar_verschieden(paare):
    """Der Satz behauptet nichts über Grenzfälle: gut füllt den Umriss, fehl höchstens halb."""
    for p in paare:
        if p.fehlt:
            assert p.anteil_im_umriss <= 0.55, p.name
        else:
            assert p.anteil_im_umriss >= 0.80, p.name


def test_der_satz_ist_wiederholbar():
    a, b = satz.satz(), satz.satz()
    assert all(x.roh == y.roh and x.soll == y.soll for x, y in zip(a, b))


# ------------------------------------------------------------------ heute und Ziel

def test_heute_bestehen_59_von_72_fehl_faellen_das_tor_ohne_maske(paare, urteile_ohne):
    """Der gemessene Ausgangswert. Ohne Maske bleibt das Tor, wie es war."""
    bestehen = [p.name for p in paare if p.fehlt and urteile_ohne[p.name]["bestanden"]]
    assert len(bestehen) == 59
    ganz_weg = [n for n in bestehen if n.endswith("ganz_weg")]
    assert len(ganz_weg) == 9                      # neun von zwölf leeren Grundstücken
    assert all(urteile_ohne[p.name]["bestanden"] for p in paare if not p.fehlt)
    assert all("anwesenheit" not in u for u in urteile_ohne.values())


def test_das_leere_grundstueck_liegt_heute_nahe_am_perfekten_bild(urteile_ohne):
    """Der Befund vom 21.08.2026 am Satz nachgestellt: 0,945 gegen 0,982 bei viel Boden."""
    leer = urteile_ohne["s08-ganz_weg"]["score"]
    perfekt = urteile_ohne["s08-perfekt"]["score"]
    assert leer > 0.9 and perfekt - leer < 0.05


def test_ziel_alle_fehl_faelle_fallen_durch(paare, urteile_mit):
    durchgekommen = [p.name for p in paare
                     if p.fehlt and urteile_mit[p.name]["bestanden"] is not False]
    assert durchgekommen == []


def test_ziel_kein_fehlalarm_bei_guten_bildern(paare, urteile_mit):
    gesperrt = [(p.name, urteile_mit[p.name]["begruendung"][:80]) for p in paare
                if not p.fehlt and urteile_mit[p.name]["bestanden"] is not True]
    assert gesperrt == []


def test_die_schwelle_steht_mit_luft_in_der_gemessenen_luecke(paare, urteile_mit):
    gut = [urteile_mit[p.name]["anwesenheit"]["anteil"] for p in paare if not p.fehlt]
    fehl = [urteile_mit[p.name]["anwesenheit"]["anteil"] for p in paare if p.fehlt]
    assert None not in gut and None not in fehl
    assert min(gut) == pytest.approx(0.805, abs=0.005)
    assert max(fehl) == pytest.approx(0.528, abs=0.005)
    assert max(fehl) + 0.10 < g.ANWESENHEIT_SCHWELLE < min(gut) - 0.10


def test_das_urteil_nennt_das_fehlende_bauwerk(urteile_mit):
    urteil = urteile_mit["s08-ganz_weg"]
    assert urteil["bestanden"] is False
    assert urteil["score"] >= urteil["schwelle"]           # der Score allein bestünde
    assert urteil["begruendung"].startswith("BAUWERK FEHLT")
    assert urteil["anwesenheit"]["vorhanden"] is False


# ------------------------------------------------------------------ die Nullproben

def _leere_szene():
    szene = satz.szenen()[8]
    soll, maske = satz.soll_karte(szene)
    return szene, soll, maske


def test_in_y_verschobene_maske_auf_leerem_boden_ist_kein_bauwerk():
    """Die Falle von R2: Dort bekam jede Maske im unteren Bildteil denselben hohen Wert."""
    szene, soll, _ = _leere_szene()
    roh = satz.schaetzkarte(satz.bild_tiefe(szene, []), polaritaet=-1, startwert=3)
    h = szene.haus
    for versatz in (0, 6, 12, 18):
        maske = [False] * len(soll)
        soll_v = list(soll)
        for y in range(h.yt + versatz, min(satz.HOEHE - 2, h.yf + versatz)):
            for x in range(h.x0, h.x1):
                maske[y * satz.BREITE + x] = True
                soll_v[y * satz.BREITE + x] = h.tiefe
        r = g.bauwerk_anwesenheit(soll_v, roh, maske, breite=satz.BREITE)
        assert r["vorhanden"] is not True, versatz
        assert r["anteil"] is None or r["anteil"] < 0.2, (versatz, r["anteil"])


def test_leeres_ortsfeld_und_grau_sind_kein_bauwerk():
    szene, soll, maske = _leere_szene()
    n = len(soll)
    feld = satz.schaetzkarte([10.0] * n, polaritaet=-1, startwert=5, feld=1.0)
    assert g.bauwerk_anwesenheit(soll, feld, maske, breite=satz.BREITE)["vorhanden"] \
        is not True
    grau = g.bauwerk_anwesenheit(soll, [0.5] * n, maske, breite=satz.BREITE)
    assert grau["anteil"] is None and grau["vorhanden"] is None


def test_rauschen_ist_kein_bauwerk():
    _, soll, maske = _leere_szene()
    for startwert in range(8):
        zufall = random.Random(startwert)
        rauschen = [zufall.random() for _ in soll]
        r = g.bauwerk_anwesenheit(soll, rauschen, maske, breite=satz.BREITE)
        assert r["vorhanden"] is not True, startwert


def test_gleich_weit_entfernter_koerper_hinter_dem_umriss_laesst_das_mass_schweigen():
    """Zeilenhaus: «da» und «weg» sagen dasselbe voraus. Dann kein Urteil statt eines falschen."""
    szene, soll, maske = _leere_szene()
    h = szene.haus
    wand = satz.Koerper(0, satz.BREITE, h.yt, h.yf, h.tiefe)
    soll_wand = list(soll)
    for y in range(h.yt, h.yf):
        for x in range(satz.BREITE):
            soll_wand[y * satz.BREITE + x] = h.tiefe
    roh = satz.schaetzkarte(satz.bild_tiefe(szene, [wand]), polaritaet=-1, startwert=9)
    r = g.bauwerk_anwesenheit(soll_wand, roh, maske, breite=satz.BREITE)
    assert r["vorhanden"] is None and r["anteil"] is None
    assert "NICHT GEMESSEN" in r["warnungen"][-1]


def test_soll_ohne_gelaende_ist_nicht_messbar():
    szene, soll, maske = _leere_szene()
    ohne = [wert if m else satz.MARKE for wert, m in zip(soll, maske)]
    roh = satz.schaetzkarte(satz.bild_tiefe(szene, [szene.haus]), polaritaet=-1, startwert=1)
    r = g.bauwerk_anwesenheit(ohne, roh, maske, breite=satz.BREITE)
    assert r["vorhanden"] is None and "ohne Gelände" in r["warnungen"][-1]


def test_markierte_karte_wird_nicht_gemessen(paare):
    p = paare[0]
    markiert = list(p.roh)
    markiert[0] = float("inf")
    r = g.bauwerk_anwesenheit(p.soll, markiert, p.maske, breite=p.breite)
    assert r["vorhanden"] is None and "ROHE" in r["warnungen"][-1]


def test_eingabefehler_werden_benannt(paare):
    p = paare[0]
    with pytest.raises(g.QaError):
        g.bauwerk_anwesenheit(p.soll, p.roh, None, breite=p.breite)
    with pytest.raises(g.QaError):
        g.bauwerk_anwesenheit(p.soll, p.roh[:-1], p.maske, breite=p.breite)
    with pytest.raises(g.QaError):
        g.bauwerk_anwesenheit(p.soll, p.roh, p.maske, breite=7)
    with pytest.raises(g.QaError):
        g.bauwerk_anwesenheit(p.soll, p.roh, p.maske, breite=p.breite, schwelle=1.5)
    with pytest.raises(g.QaError):
        g.geometrie_gate(p.soll, p.roh, maske=p.maske)          # Maske ohne Breite


# ------------------------------------------------------------------ Belastung

@pytest.mark.parametrize("einstellung", [
    {"feld": 0.0}, {"feld": 0.35}, {"gamma": 0.5}, {"gamma": 2.0},
    {"rauschen": 0.02}, {"weich": 6},
])
def test_die_trennung_haelt_ueber_kruemmung_rauschen_weichheit_und_ortsfeld(einstellung):
    """Jede Einstellung der nachgestellten Schätzkarte einzeln verstellt, andere Startwerte."""
    gut_min, fehl_max = 2.0, -1.0
    for nr, szene in enumerate(satz.szenen()):
        soll, maske = satz.soll_karte(szene)
        for art in ("perfekt", "versatz", "kleiner", "ganz_weg", "halb_links_weg",
                    "halb_oben_weg", "ersetzt_turm"):
            roh = satz.schaetzkarte(satz.bild_tiefe(szene, satz._koerper_fuer(art, szene)),
                                    polaritaet=+1 if nr % 2 == 0 else -1,
                                    startwert=77 + nr, **einstellung)
            anteil = g.bauwerk_anwesenheit(soll, roh, maske, breite=satz.BREITE)["anteil"]
            assert anteil is not None, (nr, art)
            if art in satz.GUT:
                gut_min = min(gut_min, anteil)
            else:
                fehl_max = max(fehl_max, anteil)
    assert fehl_max < g.ANWESENHEIT_SCHWELLE - 0.05 < g.ANWESENHEIT_SCHWELLE + 0.05 < gut_min


# ------------------------------------------------------------------ Urteil und Tor

def test_die_pruefung_kann_ein_urteil_nur_senken(paare):
    """Ein vorhandenes Bauwerk rettet keinen durchgefallenen Score."""
    p = next(x for x in paare if x.name == "s08-perfekt")
    rauschen = [random.Random(4).random() for _ in p.roh]
    ohne = g.geometrie_gate(p.soll, p.roh, schwelle=1.0, polaritaet=p.polaritaet)
    mit = g.geometrie_gate(p.soll, p.roh, schwelle=1.0, polaritaet=p.polaritaet,
                           maske=p.maske, breite=p.breite)
    assert ohne["bestanden"] is False and mit["bestanden"] is False
    assert mit["anwesenheit"]["vorhanden"] is True
    assert g.geometrie_gate(p.soll, rauschen, maske=p.maske,
                            breite=p.breite)["bestanden"] is not True


def test_nicht_messbare_anwesenheit_macht_aus_bestanden_nicht_entscheidbar(paare):
    """Markierte Karte ohne rohe daneben: Der Score besteht, die Anwesenheit ist ungemessen."""
    p = next(x for x in paare if x.name == "s08-perfekt")
    wort = ts.POLARITAET_DISPARITAET if p.polaritaet < 0 else ts.POLARITAET_TIEFE
    markiert = ts.markiere_hintergrund(p.roh, polaritaet=wort, strategie=ts.HG_WIE_SOLL,
                                       n_geometrie=sum(g.silhouette(p.soll)))["tiefen"]
    urteil = g.geometrie_gate(p.soll, markiert, polaritaet=p.polaritaet,
                              maske=p.maske, breite=p.breite)
    assert urteil["score"] >= urteil["schwelle"]
    assert urteil["bestanden"] is None
    assert urteil["begruendung"].startswith("NICHT ENTSCHEIDBAR")


def test_zwei_tore_bekommt_ein_drittes_tor_nur_auf_verlangen(urteile_mit):
    ohne = g.zwei_tore(0.9, 0.95)
    assert "tor_anwesend" not in ohne and ohne["bestanden"] is True

    da = urteile_mit["s08-perfekt"]["anwesenheit"]
    weg = urteile_mit["s08-ganz_weg"]["anwesenheit"]
    mit_da = g.zwei_tore(0.9, 0.95, anwesenheit=da)
    assert mit_da["bestanden"] is True and mit_da["tor_anwesend"]["bestanden"] is True
    mit_weg = g.zwei_tore(0.9, 0.95, anwesenheit=weg)
    assert mit_weg["bestanden"] is False and "anwesenheit" in mit_weg["begruendung"]

    # Auch wenn die Gegenprobe die beiden anderen Tore auf «nicht entscheidbar» setzt:
    # Ein fehlendes Bauwerk bleibt ein Nein.
    fremd = g.zwei_tore(0.9, 0.95, rho_maske_fremd=0.9, geom_iou_fremd=0.95,
                        anwesenheit=weg)
    assert fremd["bestanden"] is False
    assert g.zwei_tore(0.9, 0.95, rho_maske_fremd=0.9, geom_iou_fremd=0.95,
                       anwesenheit=da)["bestanden"] is None

    # Fail-closed: nicht gemessen ist nicht bestanden.
    ungemessen = g.zwei_tore(0.9, 0.95, anwesenheit={"anteil": None, "schwelle": 0.67})
    assert ungemessen["bestanden"] is False
    assert ungemessen["tor_anwesend"]["gemessen"] is False
    with pytest.raises(g.QaError):
        g.zwei_tore(0.9, 0.95, anwesenheit="ja")


def test_das_doppel_tor_nennt_das_fehlende_bauwerk(urteile_mit):
    stil = {"bestanden": True, "score": 0.8, "schwelle": 0.5}
    leer = gate.gesamturteil(urteile_mit["s08-ganz_weg"], stil)
    assert leer["bestanden"] is False
    assert "DAS BAUWERK FEHLT IM BILD" in leer["begruendung"]
    verdikt = gate.als_kosmovis_verdikt(leer)
    assert verdikt["released"] is False and verdikt["passed"] is False
    assert gate.GRUND_BAUWERK_FEHLT in verdikt["fail_reasons"]

    gut = gate.gesamturteil(urteile_mit["s08-perfekt"], stil)
    assert gut["bestanden"] is True
    assert gate.als_kosmovis_verdikt(gut)["fail_reasons"] == []


def test_bauwerk_fehlt_liest_nur_einen_gemessenen_befund():
    assert gate.bauwerk_fehlt({"anwesenheit": {"vorhanden": False}}) is True
    for urteil in (None, {}, {"anwesenheit": None}, {"anwesenheit": {"vorhanden": None}},
                   {"anwesenheit": {"vorhanden": True}}, {"anwesenheit": "nein"}):
        assert gate.bauwerk_fehlt(urteil) is False
