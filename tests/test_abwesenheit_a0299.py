"""A0299 «Leeres Grundstück fällt durch» — die Abwesenheitsprüfung und ihr Messsatz.

Der Befund: Ein Bild ohne Bauwerk besteht ``geometrie_gate`` (belegt 0,9530 gegen 0,9839
beim perfekten Bild, ``docs/GEOM_IOU_HALLUZINATION_2026-08-21.md``).

Was diese Proben festhalten:

1. den **heutigen Wert** des Tors ohne Maske (60 von 72 Fehl-Fällen bestehen),
2. den **Zielwert der Runde 2** am Satz von 400 Paaren: Jeder Fehl-Fall fällt durch oder ist
   mit Grund «nicht beurteilbar» (höchstens 10 %), kein gutes Bild fällt durch,
3. die **Fälle des Gegenlesens** (anderes Volumen im gleichen Umriss, Bäume, Glasbau,
   Bodentextur, Bau dahinter, Hang, Bildrand, verschobene Maske),
4. **Reihen quer über die Schwelle** und einen **Zufallsvergleich gegen die Basis**,
5. die **Nullproben**, an denen die Vorgänger des Masses gescheitert sind.

Zur Geschichte: Die erste Fassung erreichte am eigenen Satz 72 von 72 und lag an Zufallsfällen
und an den Fällen des Gegenlesens falsch. Ein Satz, in dessen leerer Lücke die Schwelle steht,
belegt wenig.

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


# ------------------------------------------------------------------ Zielwert Runde 2

def test_ziel_runde_1_alle_72_fehl_faelle_fallen_durch(paare, mit):
    durchgekommen = [p.name for p in _runde1(paare)
                     if p.fehlt and mit[p.name]["bestanden"] is not False]
    assert durchgekommen == []


def test_ziel_jeder_fehl_fall_faellt_durch_oder_ist_mit_grund_nicht_beurteilbar(paare, mit):
    fehl = [p for p in paare if p.klasse == "fehl"]
    als_vorhanden = [p.name for p in fehl if _anwesenheit(mit[p.name])["vorhanden"] is True]
    assert als_vorhanden == []
    durchgekommen = [p for p in fehl if mit[p.name]["bestanden"] is not False]
    for p in durchgekommen:
        anwesenheit = _anwesenheit(mit[p.name])
        assert anwesenheit["vorhanden"] is None and anwesenheit["grund"], p.name
        assert any("NICHT BEURTEILBAR" in w for w in mit[p.name]["warnungen"]), p.name
    assert len(durchgekommen) == 9                         # gemessen: 4,2 % der Fehl-Fälle
    assert len(durchgekommen) <= 0.10 * len(fehl)
    assert {p.art for p in durchgekommen} == {
        "feld_0.80_halb_weg", "gleicher_umriss_1.3x_tiefer", "baeume_licht"}


def test_ziel_kein_gutes_bild_faellt_durch_und_keines_ist_schlechter_als_an_der_basis(
        paare, ohne, mit):
    for p in paare:
        if p.klasse != "gut":
            continue
        assert _anwesenheit(mit[p.name])["vorhanden"] is not False, p.name
        assert mit[p.name]["bestanden"] is ohne[p.name]["bestanden"] is True, p.name


def test_das_urteil_nennt_das_fehlende_bauwerk(mit):
    urteil = mit["s08-ganz_weg"]
    assert urteil["bestanden"] is False
    assert urteil["score"] >= urteil["schwelle"]           # der Score allein bestünde
    assert urteil["begruendung"].startswith("BAUWERK FEHLT")
    assert urteil["anwesenheit"]["grund"] == g.GRUND_FEHLT


# ------------------------------------------------------------------ die Fälle des Gegenlesens

@pytest.mark.parametrize("szene", ["g06m", "g06p", "g03m", "g03p"])
def test_glasbau_faellt_nicht_durch_und_sagt_warum(szene, ohne, mit):
    """M3: Der Schätzer sieht zu 75 % durch das Haus. Die Tiefe entscheidet das nicht."""
    urteil = mit[f"{szene}-glasbau"]
    assert urteil["bestanden"] is ohne[f"{szene}-glasbau"]["bestanden"] is True
    assert urteil["anwesenheit"]["vorhanden"] is None
    assert urteil["anwesenheit"]["grund"] in (g.GRUND_UNKLAR, g.GRUND_SCHWACH)
    assert any("ABWESENHEIT NICHT BEURTEILBAR" in w for w in urteil["warnungen"])


@pytest.mark.parametrize("szene", ["g06m", "g06p", "g03m", "g03p"])
def test_anderes_volumen_im_gleichen_umriss_wird_ab_anderthalbfacher_tiefe_erkannt(szene, mit):
    """M2: gemessene Grenze. Ab 1,5-facher Tiefe «Fuss fehlt» oder «Grund im Umriss»."""
    for faktor in ("1.5", "3.0"):
        anwesenheit = mit[f"{szene}-gleicher_umriss_{faktor}x_tiefer"]["anwesenheit"]
        assert anwesenheit["vorhanden"] is False, faktor
    # 1,3-fach: erkannt oder nicht beurteilbar, nie «vorhanden».
    assert mit[f"{szene}-gleicher_umriss_1.3x_tiefer"]["anwesenheit"]["vorhanden"] \
        is not True


@pytest.mark.parametrize("szene", ["g06m", "g06p", "g03m", "g03p"])
def test_dichte_baeume_in_haustiefe_sind_abgegrenzt_und_gelten_nie_als_vorhanden(szene, mit):
    """M1: abgegrenzt (Formfrage, A0300). Am Satz: «fehlt» oder «nicht beurteilbar»."""
    anwesenheit = mit[f"{szene}-baeume_dicht"]["anwesenheit"]
    assert anwesenheit["vorhanden"] is not True
    assert anwesenheit["grund"] in (g.GRUND_FEHLT, g.GRUND_UNKLAR)


@pytest.mark.parametrize("art, erwartet", [
    ("satteldach", True), ("haus_halb_hinter_baeumen", True), ("perfekt_rauschen", True),
    ("maske_versetzt_perfekt", True), ("bildrand_perfekt", True),
    ("boden_mit_textur", False), ("bau_dahinter", False), ("ganz_weg_rauschen", False),
    ("maske_versetzt_ganz_weg", False), ("bildrand_ganz_weg", False),
])
def test_faelle_des_gegenlesens(art, erwartet, mit):
    for szene in ("g06m", "g06p", "g03m", "g03p"):
        vorhanden = mit[f"{szene}-{art}"]["anwesenheit"]["vorhanden"]
        if erwartet:
            assert vorhanden is not False, szene       # gut: bestätigt oder nicht beurteilbar
        else:
            assert vorhanden is False, szene


def test_hang_und_kleines_haus(mit):
    for name in ("hangm", "hangp", "kleinm", "kleinp"):
        assert mit[f"{name}-perfekt"]["anwesenheit"]["vorhanden"] is not False
        assert mit[f"{name}-ganz_weg"]["bestanden"] is False


# ------------------------------------------------------------------ dicht an der Schwelle

@pytest.mark.parametrize("szene", ["g06m", "g06p", "g03m", "g03p"])
@pytest.mark.parametrize("seite", ["links", "oben"])
def test_reihe_quer_ueber_die_schwelle(szene, seite, mit):
    """Das Haus in Schritten von 5 % beschnitten, von 30 bis 95 %.

    Bis 55 % «fehlt», ab 85 % nie «fehlt»; dazwischen ein Übergang. Die Reihe kippt nie
    zurück: Nach dem ersten Urteil, das nicht «fehlt» lautet, kommt kein «fehlt» mehr.
    """
    reihe = [(k / 20, mit[f"{szene}-teil_{seite}_{k / 20:.2f}"]["anwesenheit"]["vorhanden"])
             for k in range(6, 20)]
    for anteil, vorhanden in reihe:
        if anteil <= 0.55:
            assert vorhanden is False, anteil
        if anteil >= 0.85:
            assert vorhanden is not False, anteil
    urteile = [v is False for _, v in reihe]
    assert urteile == sorted(urteile, reverse=True)


def test_die_ortsfeld_reihe_von_03_bis_08(paare, mit):
    """M4: Bis 0,7 fällt das leere und das halbe Grundstück durch, das gute Bild nie.

    Bei 0,8 ist das halbe Grundstück nicht mehr beurteilbar (mehr Ortsfeld als Tiefensprung);
    das leere fällt auch dort durch. Diese Grenze ist gemessen, nicht geschätzt.
    """
    for p in paare:
        if "-feld_" not in p.name:
            continue
        vorhanden = mit[p.name]["anwesenheit"]["vorhanden"]
        feld = float(p.art.split("_")[1])
        if p.art.endswith("perfekt"):
            assert vorhanden is not False, p.name
        elif p.art.endswith("ganz_weg") or feld <= 0.7:
            assert vorhanden is False, p.name
        else:
            assert vorhanden is None, p.name


# ------------------------------------------------------------------ Zufall gegen die Basis

def test_zufallspaare_gegen_die_basis_kein_rueckschritt_kein_phantom():
    """400 Zufallspaare der Runde 2 (5200 von Hand gemessen, siehe Sitzungsprotokoll).

    * Kein gutes Bild (auch Glas, Giebel, halb verdeckt, Hang), das die Basis besteht, fällt
      durch.
    * Kein Fehl-Fall wird als «vorhanden» gemessen.
    * Nicht beurteilbar heisst: Urteil wie an der Basis. Die Prüfung hebt nie ein Urteil.
    """
    gut = gefangen = fehl_durchgelassen = 0
    for startwert in range(400):
        fall = satz.zufallsfall2(startwert)
        basis = _urteil(fall["soll"], fall["roh"], fall["maske"], fall["polaritaet"],
                        mit_maske=False)
        neu = _urteil(fall["soll"], fall["roh"], fall["maske"], fall["polaritaet"],
                      mit_maske=True)
        vorhanden = _anwesenheit(neu)["vorhanden"]
        assert not (neu["bestanden"] and not basis["bestanden"]), startwert
        if vorhanden is not False:
            assert neu["bestanden"] is basis["bestanden"], startwert
        if fall["klasse"] == "gut":
            gut += 1
            assert vorhanden is not False, (startwert, fall["art"], fall["lage"])
        elif fall["klasse"] == "fehl":
            assert vorhanden is not True, (startwert, fall["art"], fall["lage"])
            if basis["bestanden"]:
                fehl_durchgelassen += 1
                gefangen += neu["bestanden"] is False
    assert gut > 100 and fehl_durchgelassen > 100
    assert gefangen >= 0.6 * fehl_durchgelassen


@pytest.mark.parametrize("startwert, art", [
    (545, "giebel"),      # Giebelhaus ganz unter dem Horizont, starkes Ortsfeld: 39 % «Grund»
    (658, "glas"),        # Glas bei starkem Rauschen: einzeln im Rauschen, zusammen nicht
    (805, "verdeckt"),    # übereck stehendes Haus hinter Bäumen: «Fuss fehlt»
    (793, "giebel"),      # fernes Haus, Ortsfeld 0,8: jeder Punkt «Grund»
])
def test_rueckfallproben_gute_bilder_die_eine_fruehere_fassung_verwarf(startwert, art):
    fall = satz.zufallsfall2(startwert)
    assert fall["art"] == art and fall["klasse"] == "gut"
    r = g.bauwerk_anwesenheit(fall["soll"], fall["roh"], fall["maske"], breite=satz.BREITE)
    assert r["vorhanden"] is not False, r["grund"]


@pytest.mark.parametrize("startwert, erwartet", [
    (373, None),     # leeres Grundstück, fernes breites Haus: erste Fassung mass 0,88
    (252, None),     # 45 % vorhanden: erste Fassung mass 0,81 und «vorhanden»
    (542, True),     # hohes Haus, starkes Ortsfeld: erste Fassung mass 0,47 bei vollem Haus
    (588, True),     # Haus am Bildrand: erste Fassung mass 0,38 bei vollem Haus
])
def test_rueckfallproben_aus_dem_ersten_zufallsvergleich(startwert, erwartet):
    fall = satz.zufallsfall(startwert)
    r = g.bauwerk_anwesenheit(fall["soll"], fall["roh"], fall["maske"], breite=satz.BREITE)
    assert r["vorhanden"] is erwartet, r["grund"]


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


def test_ohne_freie_zeilen_wird_das_querfeld_nicht_abgezogen_und_das_steht_da():
    szene = satz.szenen()[8]
    soll, _ = satz.soll_karte(szene)
    maske = [0 < (i % satz.BREITE) - 40 < 12 for i in range(len(soll))]   # Streifen über alle Zeilen
    roh = satz.schaetzkarte(satz.bild_tiefe(szene, []), polaritaet=-1, startwert=2)
    r = g.bauwerk_anwesenheit(soll, roh, maske, breite=satz.BREITE)
    assert r["querfeld_abgezogen"] is False
    assert any("quer durchs Bild" in w for w in r["warnungen"])
    assert r["vorhanden"] is not True


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
    {"feld": 0.0}, {"feld": 0.35}, {"feld": 0.5, "gamma": 1.3}, {"feld": 0.7, "gamma": 1.3},
    {"gamma": 0.5}, {"gamma": 2.0}, {"rauschen": 0.02}, {"weich": 6},
])
def test_ueber_ortsfeld_kruemmung_rauschen_und_weichheit_nie_ein_falsches_urteil(einstellung):
    """Alle zwölf Szenen, andere Startwerte: gut nie «fehlt», fehl nie «vorhanden».

    Mit ``gamma`` 1,3 und Ortsfeld 0,5 und 0,7 sind das die Einstellungen, an denen das
    Gegenlesen die erste Fassung kippen sah (Fehl bis 0,919, Gut ab 0,216).
    """
    gefangen = fehl = 0
    for nr, szene in enumerate(satz.szenen()):
        soll, maske = satz.soll_karte(szene)
        for art in ("perfekt", "versatz", "kleiner", "ganz_weg", "halb_links_weg",
                    "halb_oben_weg", "ersetzt_turm"):
            roh = satz.schaetzkarte(satz.bild_tiefe(szene, satz._koerper_fuer(art, szene)),
                                    polaritaet=+1 if nr % 2 == 0 else -1,
                                    startwert=77 + nr, **einstellung)
            vorhanden = g.bauwerk_anwesenheit(soll, roh, maske,
                                              breite=satz.BREITE)["vorhanden"]
            if art in satz.GUT:
                assert vorhanden is not False, (nr, art)
            else:
                assert vorhanden is not True, (nr, art)
                fehl += 1
                gefangen += vorhanden is False
    assert gefangen >= 0.75 * fehl


# ------------------------------------------------------------------ Urteil und Tor

def test_die_pruefung_kann_ein_urteil_nur_senken(paare):
    """Ein vorhandenes Bauwerk rettet keinen durchgefallenen Score."""
    p = next(x for x in paare if x.name == "s08-perfekt")
    rauschen = [random.Random(4).random() for _ in p.roh]
    ohne_maske = g.geometrie_gate(p.soll, p.roh, schwelle=1.0, polaritaet=p.polaritaet)
    mit_maske = g.geometrie_gate(p.soll, p.roh, schwelle=1.0, polaritaet=p.polaritaet,
                                 maske=p.maske, breite=p.breite)
    assert ohne_maske["bestanden"] is False and mit_maske["bestanden"] is False
    assert mit_maske["anwesenheit"]["vorhanden"] is True
    assert g.geometrie_gate(p.soll, rauschen, maske=p.maske,
                            breite=p.breite)["bestanden"] is not True


def test_nicht_beurteilbare_anwesenheit_laesst_das_urteil_wie_an_der_basis(paare):
    """Nicht beurteilbar heisst: urteilen wie ohne Maske, und es sagen."""
    p = next(x for x in paare if x.name == "s08-perfekt")
    markiert = _markiert(p.soll, p.roh, p.polaritaet)
    ohne_maske = g.geometrie_gate(p.soll, markiert, polaritaet=p.polaritaet)
    mit_maske = g.geometrie_gate(p.soll, markiert, polaritaet=p.polaritaet,
                                 maske=p.maske, breite=p.breite)        # ohne rohe Karte
    assert mit_maske["anwesenheit"]["vorhanden"] is None
    assert mit_maske["bestanden"] is ohne_maske["bestanden"] is True
    assert mit_maske["begruendung"] == ohne_maske["begruendung"]
    assert any("ABWESENHEIT NICHT BEURTEILBAR" in w for w in mit_maske["warnungen"])


def test_zwei_tore_bekommt_ein_drittes_tor_nur_auf_verlangen(mit):
    ohne_drittes = g.zwei_tore(0.9, 0.95)
    assert "tor_anwesend" not in ohne_drittes and ohne_drittes["bestanden"] is True

    da = mit["s08-perfekt"]["anwesenheit"]
    weg = mit["s08-ganz_weg"]["anwesenheit"]
    glas = mit["g06m-glasbau"]["anwesenheit"]
    mit_da = g.zwei_tore(0.9, 0.95, anwesenheit=da)
    assert mit_da["bestanden"] is True and mit_da["tor_anwesend"]["bestanden"] is True
    mit_weg = g.zwei_tore(0.9, 0.95, anwesenheit=weg)
    assert mit_weg["bestanden"] is False and "BAUWERK FEHLT" in mit_weg["begruendung"]

    # Auch wenn die Gegenprobe die beiden anderen Tore auf «nicht entscheidbar» setzt:
    # Ein fehlendes Bauwerk bleibt ein Nein.
    assert g.zwei_tore(0.9, 0.95, rho_maske_fremd=0.9, geom_iou_fremd=0.95,
                       anwesenheit=weg)["bestanden"] is False
    assert g.zwei_tore(0.9, 0.95, rho_maske_fremd=0.9, geom_iou_fremd=0.95,
                       anwesenheit=da)["bestanden"] is None

    # Nicht beurteilbar: Das dritte Tor urteilt nicht mit, und es steht da.
    mit_glas = g.zwei_tore(0.9, 0.95, anwesenheit=glas)
    assert mit_glas["bestanden"] is True
    assert mit_glas["tor_anwesend"]["gemessen"] is False
    assert any("NICHT BEURTEILBAR" in w for w in mit_glas["warnungen"])
    assert g.zwei_tore(0.05, 0.95, anwesenheit=glas)["bestanden"] is False
    with pytest.raises(g.QaError):
        g.zwei_tore(0.9, 0.95, anwesenheit="ja")


def test_das_doppel_tor_nennt_das_fehlende_bauwerk(mit):
    stil = {"bestanden": True, "score": 0.8, "schwelle": 0.5}
    leer = gate.gesamturteil(mit["s08-ganz_weg"], stil)
    assert leer["bestanden"] is False
    assert "DAS BAUWERK FEHLT IM BILD" in leer["begruendung"]
    verdikt = gate.als_kosmovis_verdikt(leer)
    assert verdikt["released"] is False and verdikt["passed"] is False
    assert gate.GRUND_BAUWERK_FEHLT in verdikt["fail_reasons"]

    for name in ("s08-perfekt", "g06m-glasbau"):
        gut = gate.gesamturteil(mit[name], stil)
        assert gut["bestanden"] is True
        assert gate.als_kosmovis_verdikt(gut)["fail_reasons"] == []


def test_bauwerk_fehlt_liest_nur_einen_gemessenen_befund():
    assert gate.bauwerk_fehlt({"anwesenheit": {"vorhanden": False}}) is True
    for urteil in (None, {}, {"anwesenheit": None}, {"anwesenheit": {"vorhanden": None}},
                   {"anwesenheit": {"vorhanden": True}}, {"anwesenheit": "nein"}):
        assert gate.bauwerk_fehlt(urteil) is False
