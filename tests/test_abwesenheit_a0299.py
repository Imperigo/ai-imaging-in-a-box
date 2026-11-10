"""A0299 «Leeres Grundstück fällt durch» — die Abwesenheitsprüfung und ihr Messsatz.

Der Befund: Ein Bild ohne Bauwerk besteht ``geometrie_gate`` (belegt 0,9530 gegen 0,9839
beim perfekten Bild, ``docs/GEOM_IOU_HALLUZINATION_2026-08-21.md``).

Was diese Proben festhalten:

1. den **heutigen Wert** des Tors ohne Maske (60 von 72 Fehl-Fällen bestehen),
2. die **harte Zusicherung der Runde 3**: Kein gutes Bild gilt als fehlend und kein
   Fehl-Fall als vorhanden, über fünf Formen des Ortsfelds (geradlinig, Schüsseln, schief,
   Mischung) und Stärken von 0,2 bis 0,8,
3. die **Fälle beider Gegenlese-Runden** (N1 und N2 unter einem Schüssel-Ortsfeld; anderes
   Volumen im gleichen Umriss, Bäume, Glasbau, Bodentextur, Hang, Bildrand),
4. **was die Prüfung fängt**, als gemessene Zahl und nicht als Zielwert,
5. dass «nicht beurteilbar» und «kein Fehlen gemessen» **im Gesamturteil stehen**.

Zur Geschichte: Die erste Fassung erreichte am eigenen Satz 72 von 72 und lag an Zufallsfällen
falsch. Die zweite bestand ihre Zufallsfälle und war auf das Ortsfeld des eigenen Erzeugers
zugeschnitten: Unter einem Schüssel-Ortsfeld galt ein volles Haus als fehlend und ein
tieferes Volumen als vorhanden. Die dritte sagt nur noch, was an keiner Form hängt: «fehlt»,
wenn der Umriss im Rauschen der Karte vom Grund daneben nicht zu unterscheiden ist, und nie
«vorhanden».

Alle Karten sind nachgestellt (``tests/abwesenheit_satz.py``). Was hier grün ist, ist an
keinem erzeugten Bild gemessen.
"""
from __future__ import annotations

import inspect
import random

import pytest

import abwesenheit_satz as satz
from aiimaging import gate
from aiimaging import geometrie_qa as g
from aiimaging import tiefenschaetzer as ts

#: Kennt das Tor die Maske? Auf der Basis nicht: Dann fährt ``_urteil`` das Tor ohne sie, und
#: die Zielproben werden an ihrer fachlichen Zusicherung rot (und nicht an einem TypeError).
TOR_KENNT_MASKE = "maske" in inspect.signature(g.geometrie_gate).parameters


def _markiert(soll, roh, polaritaet):
    wort = ts.POLARITAET_DISPARITAET if polaritaet < 0 else ts.POLARITAET_TIEFE
    return ts.markiere_hintergrund(roh, polaritaet=wort, strategie=ts.HG_WIE_SOLL,
                                   n_geometrie=sum(g.silhouette(soll)))["tiefen"]


def _urteil(soll, roh, maske, polaritaet, *, mit_maske: bool) -> dict:
    """Das Tor, wie es der Kettenlauf fährt: Hintergrund nach Vorbild des Soll markiert."""
    markiert = _markiert(soll, roh, polaritaet)
    if not (mit_maske and TOR_KENNT_MASKE):
        return g.geometrie_gate(soll, markiert, polaritaet=polaritaet)
    return g.geometrie_gate(soll, markiert, polaritaet=polaritaet,
                            maske=maske, breite=satz.BREITE, ist_roh=roh)


def _anwesenheit(urteil: dict) -> dict:
    return urteil.get("anwesenheit") or {"vorhanden": None, "grund": None}


@pytest.fixture(scope="module")
def paare():
    return satz.satz_runde2()


@pytest.fixture(scope="module")
def ohne(paare):
    return {p.name: _urteil(p.soll, p.roh, p.maske, p.polaritaet, mit_maske=False)
            for p in paare}


@pytest.fixture(scope="module")
def mit(paare):
    return {p.name: _urteil(p.soll, p.roh, p.maske, p.polaritaet, mit_maske=True)
            for p in paare}


def _runde1(paare):
    return [p for p in paare if p.name[0] == "s"]


# ------------------------------------------------------------------ der Satz selbst

def test_der_satz_der_runde_1_deckt_den_verlangten_bereich(paare):
    """Boden 20 bis 80 %, Haus 10 bis 60 %, alle drei Fehlarten, beide Polaritäten."""
    erste = _runde1(paare)
    assert len(erste) == 132
    assert sum(p.fehlt for p in erste) == 72 and sum(not p.fehlt for p in erste) == 60
    boden = [p.bodenanteil for p in erste]
    haus = [p.hausanteil for p in erste]
    assert 0.19 <= min(boden) <= 0.21 and 0.79 <= max(boden) <= 0.81
    assert 0.09 <= min(haus) <= 0.11 and 0.59 <= max(haus) <= 0.61
    assert {p.art for p in erste} == set(satz.GUT) | set(satz.FEHL)
    assert {p.polaritaet for p in erste} == {-1, +1}


def test_der_satz_der_runde_2_hat_ueber_250_paare_und_die_faelle_des_gegenlesens(paare):
    assert len(paare) == 400
    klassen = {k: sum(p.klasse == k for p in paare)
               for k in ("gut", "fehl", "uebergang", "abgegrenzt")}
    assert klassen == {"gut": 136, "fehl": 212, "uebergang": 48, "abgegrenzt": 4}
    arten = {p.art for p in paare}
    for art in ("gleicher_umriss_1.3x_tiefer", "satteldach", "baeume_dicht", "baeume_licht",
                "haus_halb_hinter_baeumen", "boden_mit_textur", "bau_dahinter", "glasbau",
                "perfekt_rauschen", "maske_versetzt_perfekt", "bildrand_ganz_weg",
                "feld_0.80_ganz_weg", "teil_links_0.70"):
        assert art in arten, art
    assert {"hangm-perfekt", "kleinp-ganz_weg"} <= {p.name for p in paare}


def test_der_satz_ist_wiederholbar():
    a, b = satz.satz_runde2(), satz.satz_runde2()
    assert all(x.roh == y.roh and x.soll == y.soll for x, y in zip(a, b))


# ------------------------------------------------------------------ heute

def test_heute_bestehen_60_von_72_fehl_faellen_das_tor_ohne_maske(paare, ohne):
    """Der gemessene Ausgangswert. Ohne Maske bleibt das Tor, wie es war."""
    erste = _runde1(paare)
    bestehen = [p.name for p in erste if p.fehlt and ohne[p.name]["bestanden"]]
    assert len(bestehen) == 60
    assert sum(n.endswith("ganz_weg") for n in bestehen) == 10   # zehn von zwölf leeren
    assert all(ohne[p.name]["bestanden"] for p in erste if not p.fehlt)
    assert all("anwesenheit" not in u for u in ohne.values())


def test_das_leere_grundstueck_liegt_heute_nahe_am_perfekten_bild(ohne):
    """Der Befund vom 21.08.2026 am Satz nachgestellt: 0,945 gegen 0,982 bei viel Boden."""
    leer = ohne["s08-ganz_weg"]["score"]
    perfekt = ohne["s08-perfekt"]["score"]
    assert leer > 0.9 and perfekt - leer < 0.05


def test_heute_besteht_jedes_paar_der_runde_2_ausser_zwoelf(paare, ohne):
    """Die Basis lässt am ganzen Satz 200 von 212 Fehl-Fällen durch."""
    assert sum(1 for p in paare if p.klasse == "fehl" and ohne[p.name]["bestanden"]) == 200
    assert all(ohne[p.name]["bestanden"] for p in paare if p.klasse == "gut")


# ------------------------------------------------------------------ harte Zusicherung

def test_nie_vorhanden_und_jede_antwort_traegt_ihren_grund(paare, mit):
    """Die Prüfung misst Abwesenheit: ``False`` oder ``None``, nie ``True``."""
    for p in paare:
        anwesenheit = _anwesenheit(mit[p.name])
        assert anwesenheit["vorhanden"] in (False, None), p.name
        assert anwesenheit["grund"], p.name


def test_kein_gutes_bild_des_satzes_gilt_als_fehlend(paare, ohne, mit):
    for p in paare:
        if p.klasse != "gut":
            continue
        assert _anwesenheit(mit[p.name])["vorhanden"] is None, p.name
        assert mit[p.name]["bestanden"] is ohne[p.name]["bestanden"] is True, p.name


def test_gegenlesen_n1_volles_haus_unter_schuessel_ortsfeld_gilt_nicht_als_fehlend():
    """N1: Der Kopf 392be5c3 mass 94 % «Grund» und verwarf das Bild. Die Basis besteht es."""
    fall = satz.gegenlesen_n1()
    basis = _urteil(fall["soll"], fall["roh"], fall["maske"], -1, mit_maske=False)
    neu = _urteil(fall["soll"], fall["roh"], fall["maske"], -1, mit_maske=True)
    assert basis["bestanden"] is True
    assert neu["bestanden"] is True
    assert _anwesenheit(neu)["vorhanden"] is None


@pytest.mark.parametrize("faktor", [1.5, 2.0, 3.0])
def test_gegenlesen_n2_tieferes_volumen_unter_schuessel_ortsfeld_gilt_nicht_als_vorhanden(
        faktor):
    """N2: Der Kopf 392be5c3 mass «vorhanden» (0,81). Jetzt gibt es diese Antwort nicht mehr."""
    fall = satz.gegenlesen_n2(faktor)
    r = g.bauwerk_anwesenheit(fall["soll"], fall["roh"], fall["maske"], breite=satz.BREITE)
    assert r["vorhanden"] is not True and r["grund"]


def test_zufallsfaelle_ueber_alle_formen_kein_fehlalarm_und_nie_vorhanden():
    """500 Zufallsfälle der Runde 3 (6200 von Hand gemessen: 0 Fehlalarme, 0 «vorhanden»).

    Fünf Formen des Ortsfelds, Stärke 0,2 bis 0,8; gute Bilder mit Glas, Giebel, Verdeckung,
    Versatz, Hang. Wo die Prüfung nicht «fehlt» misst, ist das Urteil das der Basis.
    """
    formen = set()
    gut = gefangen = 0
    for startwert in range(500):
        fall = satz.zufallsfall3(startwert)
        formen.add(fall["form"])
        basis = _urteil(fall["soll"], fall["roh"], fall["maske"], fall["polaritaet"],
                        mit_maske=False)
        neu = _urteil(fall["soll"], fall["roh"], fall["maske"], fall["polaritaet"],
                      mit_maske=True)
        vorhanden = _anwesenheit(neu)["vorhanden"]
        assert vorhanden is not True, startwert
        if vorhanden is None:
            assert neu["bestanden"] is basis["bestanden"], startwert
        else:
            assert neu["bestanden"] is False, startwert
        if fall["klasse"] == "gut":
            gut += 1
            assert vorhanden is None, (startwert, fall["art"], fall["form"], fall["feld"])
        elif fall["klasse"] == "fehl":
            gefangen += vorhanden is False
    assert formen == set(satz.ORTSFELD_FORMEN)
    assert gut > 150 and gefangen > 20


@pytest.mark.parametrize("form", satz.ORTSFELD_FORMEN)
@pytest.mark.parametrize("feld", [0.2, 0.5, 0.8])
def test_je_form_und_staerke_faellt_kein_gutes_bild_durch(form, feld):
    """Alle zwölf Szenen, perfekt, versetzt und kleiner: nie «fehlt», bei keiner Form."""
    for nr, szene in enumerate(satz.szenen()):
        soll, maske = satz.soll_karte(szene)
        for art in ("perfekt", "versatz", "kleiner"):
            roh = satz.schaetzkarte(satz.bild_tiefe(szene, satz._koerper_fuer(art, szene)),
                                    polaritaet=+1 if nr % 2 == 0 else -1, startwert=31 + nr,
                                    feld=feld, gamma=1.3, rauschen=0.01, weich=2, form=form)
            r = g.bauwerk_anwesenheit(soll, roh, maske, breite=satz.BREITE)
            assert r["vorhanden"] is None, (nr, art, r["grund"])


# ------------------------------------------------------------------ was die Prüfung fängt

def test_das_urteil_nennt_das_fehlende_bauwerk(mit):
    urteil = mit["s08-ganz_weg"]
    assert urteil["bestanden"] is False
    assert urteil["score"] >= urteil["schwelle"]           # der Score allein bestünde
    assert urteil["begruendung"].startswith(g.SATZ_NICHT_NACHWEISBAR.upper())
    assert "BAUWERK FEHLT" not in urteil["begruendung"]
    assert urteil["anwesenheit"]["grund"] == g.GRUND_FEHLT


def test_gemessen_am_satz_165_von_212_fehl_faellen_fallen_durch(paare, mit):
    """Keine Zielzahl, eine Messung: Sie hält fest, was die vorsichtige Fassung noch fängt.

    Ganz und halb leere Grundstücke der Runde 1 fallen alle durch; ein Bau NEBEN dem Umriss
    (verdeckt die Flanke) und ein Bau weit dahinter nicht mehr, und ab einem Ortsfeld von
    0,6 der Karte schweigt die Prüfung.
    """
    fehl = [p for p in paare if p.klasse == "fehl"]
    gefangen = [p for p in fehl if mit[p.name]["bestanden"] is False
                and _anwesenheit(mit[p.name])["vorhanden"] is False]
    assert len(gefangen) == 165
    je_art = {}
    for p in fehl:
        art = ("R1:" if p.name[0] == "s" else "") + p.art
        treffer, alle = je_art.get(art, (0, 0))
        je_art[art] = (treffer + (_anwesenheit(mit[p.name])["vorhanden"] is False), alle + 1)
    for art in ("R1:ganz_weg", "R1:halb_links_weg", "R1:halb_oben_weg", "R1:ersetzt_flachbau",
                "boden_mit_textur", "bildrand_ganz_weg", "maske_versetzt_ganz_weg",
                "ganz_weg_rauschen", "gleicher_umriss_1.5x_tiefer",
                "gleicher_umriss_3.0x_tiefer", "teil_links_0.55", "teil_oben_0.55",
                "feld_0.55_ganz_weg", "feld_0.55_halb_weg"):
        assert je_art[art][0] == je_art[art][1], (art, je_art[art])
    for art in ("R1:ersetzt_daneben", "bau_dahinter", "feld_0.70_ganz_weg",
                "feld_0.80_halb_weg"):
        assert je_art[art][0] == 0, (art, je_art[art])


@pytest.mark.parametrize("form, mindestens", [
    ("satz", 10), ("schuessel_y", 10), ("schief", 10), ("mischung", 8), ("schuessel", 3)])
def test_leeres_grundstueck_bei_ortsfeld_02_je_form(form, mindestens):
    """Das ganz leere Grundstück, zwölf Szenen, Ortsfeld 0,2: wie viele fallen durch?

    Die Mindestanforderung des Auftrags (90 % bis Ortsfeld 0,5 über beide Formen) ist NICHT
    erreicht; diese Probe hält den gemessenen Stand bei schwachem Ortsfeld fest. Unter der
    Schüssel schweigt die Prüfung am häufigsten, weil sie dort nicht ausschliessen kann,
    dass das Ortsfeld den Sprung vortäuscht.
    """
    gefangen = 0
    for nr, szene in enumerate(satz.szenen()):
        soll, maske = satz.soll_karte(szene)
        roh = satz.schaetzkarte(satz.bild_tiefe(szene, []),
                                polaritaet=+1 if nr % 2 == 0 else -1, startwert=31 + nr,
                                feld=0.2, gamma=1.0, rauschen=0.005, weich=1, form=form)
        r = g.bauwerk_anwesenheit(soll, roh, maske, breite=satz.BREITE)
        assert r["vorhanden"] is not True
        gefangen += r["vorhanden"] is False
    assert gefangen >= mindestens, gefangen


@pytest.mark.parametrize("szene", ["g06m", "g06p", "g03m", "g03p"])
def test_glasbau_faellt_nicht_durch_und_das_gesamturteil_sagt_warum(szene, ohne, mit):
    """M3 und N3: Der Schätzer sieht zu 75 % durch das Haus."""
    urteil = mit[f"{szene}-glasbau"]
    assert urteil["bestanden"] is ohne[f"{szene}-glasbau"]["bestanden"] is True
    assert urteil["anwesenheit"]["vorhanden"] is None
    assert "ABWESENHEIT" in urteil["begruendung"]


@pytest.mark.parametrize("form", satz.ORTSFELD_FORMEN)
def test_glasreihe_unter_80_prozent_durchsicht_gilt_nie_als_nicht_nachweisbar(form):
    """Durchsicht 0,50 bis 0,78 in Stufen von 0,02, vier Szenen, schwaches und starkes Ortsfeld.

    Die Grenze der Prüfung ist ausdrücklich: Ab rund 80 % Durchsicht trennt die Tiefe einen
    Bau nicht mehr vom leeren Grundstück. Darunter darf das Urteil nie fallen.
    """
    for nr in (0, 3, 6, 9):
        szene = satz.szenen()[nr]
        for stufe in range(15):
            durchsicht = 0.50 + 0.02 * stufe
            for feld, rauschen, gamma in ((0.2, 0.005, 1.0), (0.5, 0.02, 1.9)):
                fall = satz.glasbau(szene.haus, szene.horizont, durchsicht,
                                    polaritaet=-1 if nr % 2 else +1,
                                    startwert=nr * 100 + stufe, feld=feld, gamma=gamma,
                                    weich=1, rauschen=rauschen, form=form)
                r = g.bauwerk_anwesenheit(fall["soll"], fall["roh"], fall["maske"],
                                          breite=satz.BREITE)
                assert r["vorhanden"] is None, (nr, round(durchsicht, 2), feld, r["grund"])


def test_gegenlesen_g1_glasbau_unter_der_grenze_besteht_wie_an_der_basis():
    """G1 bei 0,78 und 0,60 Durchsicht: kein Urteil, das Tor besteht wie ohne Maske."""
    for durchsicht in (0.60, 0.70, 0.78):
        fall = satz.gegenlesen_g1(durchsicht)
        basis = _urteil(fall["soll"], fall["roh"], fall["maske"], -1, mit_maske=False)
        neu = _urteil(fall["soll"], fall["roh"], fall["maske"], -1, mit_maske=True)
        assert basis["bestanden"] is True and neu["bestanden"] is True, durchsicht
        assert _anwesenheit(neu)["vorhanden"] is None


@pytest.mark.parametrize("name, fall", [
    ("G1 0,80", lambda: satz.gegenlesen_g1(0.80)),
    ("G1b 0,80", lambda: satz.gegenlesen_g1b(0.80)),
    ("G1b 0,82", lambda: satz.gegenlesen_g1b(0.82)),
    ("G1c 0,92", lambda: satz.gegenlesen_g1c(0.92)),
])
def test_gegenlesen_g1_ab_der_grenze_heisst_es_nicht_nachweisbar_und_nicht_fehlt(name, fall):
    """G1, G1b, G1c: Glasbauten ab 80 % Durchsicht. Das Urteil fällt, und es sagt ehrlich,
    was es weiss: in der Tiefe nicht nachweisbar, leeres Grundstück ODER sehr durchsichtiger Bau.
    """
    f = fall()
    neu = _urteil(f["soll"], f["roh"], f["maske"], f["polaritaet"], mit_maske=True)
    assert neu["bestanden"] is False
    assert neu["begruendung"].startswith(g.SATZ_NICHT_NACHWEISBAR.upper())
    assert "FEHLT" not in neu["begruendung"]
    gesamt = gate.gesamturteil(neu, {"bestanden": True, "score": 0.8, "schwelle": 0.5})
    assert "sehr hoher durchsicht" in gesamt["begruendung"].lower()
    assert gate.als_kosmovis_verdikt(gesamt)[gate.FELD_HINWEISE] == [gate.SATZ_NICHT_NACHWEISBAR]


@pytest.mark.parametrize("szene", ["g06m", "g06p", "g03m", "g03p"])
@pytest.mark.parametrize("seite", ["links", "oben"])
def test_reihe_quer_ueber_die_schwelle(szene, seite, mit):
    """Das Haus in Schritten von 5 % beschnitten: bis 55 % «fehlt», ab 85 % nie, kein Zurückkippen."""
    reihe = [(k / 20, mit[f"{szene}-teil_{seite}_{k / 20:.2f}"]["anwesenheit"]["vorhanden"])
             for k in range(6, 20)]
    for anteil, vorhanden in reihe:
        if anteil <= 0.55:
            assert vorhanden is False, anteil
        if anteil >= 0.85:
            assert vorhanden is None, anteil
    urteile = [v is False for _, v in reihe]
    assert urteile == sorted(urteile, reverse=True)


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
        assert r["anteil"] is None or r["anteil"] < 0.2, (versatz, r["anteil"])


def test_grau_rauschen_und_leeres_ortsfeld_ergeben_nie_vorhanden():
    szene, soll, maske = _leere_szene()
    n = len(soll)
    karten = [[0.5] * n, satz.schaetzkarte([10.0] * n, polaritaet=-1, startwert=5, feld=1.0)]
    karten += [[random.Random(k).random() for _ in soll] for k in range(4)]
    for karte in karten:
        assert g.bauwerk_anwesenheit(soll, karte, maske, breite=satz.BREITE)["vorhanden"] \
            is not True


def test_gleich_weit_entfernter_koerper_hinter_dem_umriss_laesst_das_mass_schweigen():
    """Zeilenhaus: Neben dem Umriss steht laut Soll dasselbe. Dann kein Urteil."""
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
    assert r["grund"] == g.GRUND_GLEICHE_TIEFE
    assert "NICHT BEURTEILBAR" in r["warnungen"][-1]


def test_soll_ohne_gelaende_ist_nicht_messbar():
    szene, soll, maske = _leere_szene()
    ohne_gelaende = [wert if m else satz.MARKE for wert, m in zip(soll, maske)]
    roh = satz.schaetzkarte(satz.bild_tiefe(szene, [szene.haus]), polaritaet=-1, startwert=1)
    r = g.bauwerk_anwesenheit(ohne_gelaende, roh, maske, breite=satz.BREITE)
    assert r["vorhanden"] is None and r["grund"] == g.GRUND_OHNE_GELAENDE


def test_markierte_karte_wird_nicht_gemessen(paare):
    p = paare[0]
    markiert = list(p.roh)
    markiert[0] = float("inf")
    r = g.bauwerk_anwesenheit(p.soll, markiert, p.maske, breite=p.breite)
    assert r["vorhanden"] is None and "ROHE" in r["warnungen"][-1]


def test_ohne_zeilen_ohne_umriss_schweigt_die_pruefung_mit_grund():
    szene = satz.szenen()[8]
    soll, _ = satz.soll_karte(szene)
    maske = [0 < (i % satz.BREITE) - 40 < 12 for i in range(len(soll))]   # Streifen über alle Zeilen
    roh = satz.schaetzkarte(satz.bild_tiefe(szene, []), polaritaet=-1, startwert=2)
    r = g.bauwerk_anwesenheit(soll, roh, maske, breite=satz.BREITE)
    assert r["querfeld_abgezogen"] is False
    assert r["vorhanden"] is None and r["grund"] == g.GRUND_OHNE_FREIE_ZEILEN


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


# ------------------------------------------------------------------ Urteil und Tor

def test_die_pruefung_kann_ein_urteil_nur_senken(paare):
    """Kein gemessenes Fehlen rettet keinen durchgefallenen Score."""
    p = next(x for x in paare if x.name == "s08-perfekt")
    ohne_maske = g.geometrie_gate(p.soll, p.roh, schwelle=1.0, polaritaet=p.polaritaet)
    mit_maske = g.geometrie_gate(p.soll, p.roh, schwelle=1.0, polaritaet=p.polaritaet,
                                 maske=p.maske, breite=p.breite)
    assert ohne_maske["bestanden"] is False and mit_maske["bestanden"] is False
    assert mit_maske["anwesenheit"]["grund"] == g.GRUND_KEIN_FEHLEN


def test_ohne_gemessenes_fehlen_bleibt_das_urteil_wie_an_der_basis_mit_hinweis(paare):
    p = next(x for x in paare if x.name == "s08-perfekt")
    markiert = _markiert(p.soll, p.roh, p.polaritaet)
    ohne_maske = g.geometrie_gate(p.soll, markiert, polaritaet=p.polaritaet)
    for roh, wort in ((None, f"NICHT BEURTEILBAR ({g.GRUND_MARKE})"),
                      (p.roh, "KEIN FEHLEN GEMESSEN")):
        mit_maske = g.geometrie_gate(p.soll, markiert, polaritaet=p.polaritaet,
                                     maske=p.maske, breite=p.breite, ist_roh=roh)
        assert mit_maske["anwesenheit"]["vorhanden"] is None
        assert mit_maske["bestanden"] is ohne_maske["bestanden"] is True
        assert mit_maske["begruendung"].startswith(ohne_maske["begruendung"])
        assert wort in mit_maske["begruendung"]
        assert any(wort in w for w in mit_maske["warnungen"])


def test_zwei_tore_bekommt_ein_drittes_tor_nur_auf_verlangen(mit):
    ohne_drittes = g.zwei_tore(0.9, 0.95)
    assert "tor_anwesend" not in ohne_drittes and ohne_drittes["bestanden"] is True

    kein_fehlen = mit["s08-perfekt"]["anwesenheit"]
    weg = mit["s08-ganz_weg"]["anwesenheit"]
    mit_weg = g.zwei_tore(0.9, 0.95, anwesenheit=weg)
    assert mit_weg["bestanden"] is False
    assert g.SATZ_NICHT_NACHWEISBAR.upper() in mit_weg["begruendung"]
    # Auch wenn die Gegenprobe die beiden anderen Tore auf «nicht entscheidbar» setzt:
    assert g.zwei_tore(0.9, 0.95, rho_maske_fremd=0.9, geom_iou_fremd=0.95,
                       anwesenheit=weg)["bestanden"] is False

    # Kein Fehlen gemessen: Das dritte Tor urteilt nicht mit, und es steht da.
    mit_rest = g.zwei_tore(0.9, 0.95, anwesenheit=kein_fehlen)
    assert mit_rest["bestanden"] is True
    assert mit_rest["tor_anwesend"]["gemessen"] is False
    assert any("NICHT BEURTEILBAR" in w for w in mit_rest["warnungen"])
    assert g.zwei_tore(0.05, 0.95, anwesenheit=kein_fehlen)["bestanden"] is False
    with pytest.raises(g.QaError):
        g.zwei_tore(0.9, 0.95, anwesenheit="ja")


def test_das_doppel_tor_nennt_das_fehlende_bauwerk(mit):
    stil = {"bestanden": True, "score": 0.8, "schwelle": 0.5}
    leer = gate.gesamturteil(mit["s08-ganz_weg"], stil)
    assert leer["bestanden"] is False
    assert gate.SATZ_NICHT_NACHWEISBAR.upper() in leer["begruendung"]
    assert "FEHLT" not in leer["begruendung"]
    verdikt = gate.als_kosmovis_verdikt(leer)
    assert verdikt["released"] is False and verdikt["passed"] is False
    assert gate.GRUND_BAUWERK_FEHLT in verdikt["fail_reasons"]
    assert verdikt[gate.FELD_HINWEISE] == [gate.SATZ_NICHT_NACHWEISBAR]
    assert gate.SATZ_NICHT_NACHWEISBAR == g.SATZ_NICHT_NACHWEISBAR       # zwei Module, ein Satz
    assert gate.SATZ_NICHT_NACHWEISBAR == (
        "Bauwerk in der Tiefe nicht nachweisbar (leeres Grundstück oder Bau mit sehr hoher "
        "Durchsicht)")


@pytest.mark.parametrize("name, marke", [
    ("s08-perfekt", gate.HINWEIS_KEIN_FEHLEN),
    ("g06m-glasbau", gate.HINWEIS_KEIN_FEHLEN),
    ("g06m-baeume_dicht", gate.HINWEIS_KEIN_FEHLEN),
    ("g06m-feld_0.80_halb_weg", gate.HINWEIS_NICHT_BEURTEILBAR + ":" + g.GRUND_FELD),
])
def test_n3_der_hinweis_steht_im_gesamturteil_und_im_uebersetzten_urteil(name, marke, mit):
    """N3: Bis zum zweiten Gegenlesen hiess das «Bestanden: Geometrie UND Stil», ohne ein Wort."""
    stil = {"bestanden": True, "score": 0.8, "schwelle": 0.5}
    gesamt = gate.gesamturteil(mit[name], stil)
    assert gesamt["bestanden"] is True
    assert "Hinweis Abwesenheitsprüfung" in gesamt["begruendung"]
    verdikt = gate.als_kosmovis_verdikt(gesamt)
    assert verdikt["released"] is True and verdikt["fail_reasons"] == []
    assert verdikt[gate.FELD_HINWEISE] == [marke]


def test_ohne_abwesenheitspruefung_bleibt_das_uebersetzte_urteil_wie_es_war(ohne):
    stil = {"bestanden": True, "score": 0.8, "schwelle": 0.5}
    gesamt = gate.gesamturteil(ohne["s08-perfekt"], stil)
    assert "Hinweis" not in gesamt["begruendung"]
    assert gate.FELD_HINWEISE not in gate.als_kosmovis_verdikt(gesamt)
    assert gate.abwesenheit_hinweis(None) is None


def test_bauwerk_fehlt_liest_nur_einen_gemessenen_befund():
    assert gate.bauwerk_fehlt({"anwesenheit": {"vorhanden": False}}) is True
    for urteil in (None, {}, {"anwesenheit": None}, {"anwesenheit": {"vorhanden": None}},
                   {"anwesenheit": {"vorhanden": True}}, {"anwesenheit": "nein"}):
        assert gate.bauwerk_fehlt(urteil) is False
