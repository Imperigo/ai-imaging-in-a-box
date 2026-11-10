"""A0301 «Flügel bleiben ein Haus»: die Gruppierung der Grundrisse am synthetischen Satz.

Ursache, belegt am 10.11.2026 (und als Nebenbefund schon in Sitzung 74, Ergebnis 363): Steht eine Anlage auf
einer grossen Geländeplatte, hängt jedes Teil über diese Platte mit jedem zusammen. Der Haufen wuchs über
``BAU_MAX_FLAECHE_M2`` und wurde nach *gleichem Grundriss* zerlegt. Geschosse übereinander haben denselben
Grundriss und blieben zusammen; Flügel haben verschiedene Grundrisse und fielen auseinander.

Runde 2 (nach dem ersten Gegenlesen): Die erste Lösung entschied mit einer Deckungsschwelle, ob eine Platte
Sockel oder Belag ist, und lag an 8 von 44 neuen Fällen schlechter als die Basis. Die Proben hier halten
darum drei Dinge fest: (1) entscheidbare Fälle sind richtig, (2) wo die Geometrie nicht entscheidet, steht
der Vermerk ``mehrdeutig`` und die Gruppierung ist nicht schlechter als die Basis, (3) ausserhalb eines zu
grossen Haufens ist das Ergebnis wörtlich das der Basis (``fluegel_basis.basis_cluster``).
"""
from __future__ import annotations

import random

import pytest

from aiimaging import umfeld
from fluegel_basis import basis_cluster
from fluegel_satz import (REIHE_ABSTAND, REIHE_ANTEIL, REIHE_BODEN, REIHE_DECKUNG, REIHE_SOCKELHOEHE,
                          REIHE_UEBERRAGT, beurteile, faelle, gruppiere, zufallsfall_schraeg, gemeldet, gruppen_von, miss, schlechter, zufallsfall, zufallsszene)

FAELLE = faelle()
ENTSCHEIDBAR = [f for f in FAELLE if not f["mehrdeutig"] and not f["grenze"]]
MEHRDEUTIG = [f for f in FAELLE if f["mehrdeutig"]]
GRENZE = [f for f in FAELLE if f["grenze"]]
GELAENDE = ((-200.0, -200.0, 0.0), (300.0, 300.0, 2.0))


def test_der_satz_ist_gross_genug_und_deckt_die_verlangten_formen():
    """Der Auftrag verlangt L-, U-, H- und Kammform, Bodenplatte, Verbindungsgang und die Gegenfälle; Runde 2
    dazu die 44 Fälle des Gegenlesens und zusammen mindestens 150 Fälle."""
    namen = [f["name"] for f in FAELLE]
    assert len(FAELLE) >= 150
    assert sum(f["herkunft"] == "runde1" for f in FAELLE) == 66
    assert sum(f["herkunft"] == "gegenlesen" for f in FAELLE) == 44
    for form in ("L-", "U-", "H-", "Kamm-"):
        assert sum(n.startswith(form) for n in namen) >= 6, form
    assert sum(f["gruppe"] == "bodenplatte" for f in FAELLE) >= 4
    assert sum(f["gruppe"] == "gang" for f in FAELLE) >= 2
    assert sum(n.startswith("zwei-haeuser") for n in namen) >= 6
    assert sum(n.startswith("haus-nebenbau") for n in namen) >= 4
    assert sum(f["gegenfall"] for f in ENTSCHEIDBAR) >= 10
    assert len(ENTSCHEIDBAR) >= 100


def test_die_reihen_besetzen_jede_schwelle_von_beiden_seiten():
    """Mangel 3 des Gegenlesens: Eine Schwelle in einer leeren Lücke des Satzes lässt sich nicht widerlegen.
    Jede Zahl, an der die Regel etwas unterscheidet, liegt darum zwischen zwei eng benachbarten Stufen."""
    assert REIHE_DECKUNG[0] == 0.15 and REIHE_DECKUNG[-1] == 0.95
    assert all(b - a <= 0.05 + 1e-9 for a, b in zip(REIHE_DECKUNG, REIHE_DECKUNG[1:]))

    def umschliesst(reihe, schwelle, weite):
        unten = max(v for v in reihe if v < schwelle)
        oben = min(v for v in reihe if v > schwelle)
        return schwelle - unten <= weite and oben - schwelle <= weite
    assert umschliesst(REIHE_SOCKELHOEHE, umfeld.BAU_MIN_HOEHE_M, 0.011) and umfeld.BAU_MIN_HOEHE_M in REIHE_SOCKELHOEHE
    assert umschliesst(REIHE_SOCKELHOEHE, umfeld.FLACH_MAX_M, 0.11) and umfeld.FLACH_MAX_M in REIHE_SOCKELHOEHE
    assert umschliesst(REIHE_ANTEIL, umfeld.TRAEGER_ANTEIL, 0.011) and umfeld.TRAEGER_ANTEIL in REIHE_ANTEIL
    assert umschliesst(REIHE_ABSTAND, umfeld.CLUSTER_LUECKE_M, 0.0011)
    assert umschliesst([s * s for s in REIHE_BODEN], umfeld.BAU_MAX_FLAECHE_M2, 130.0)
    assert umschliesst(REIHE_UEBERRAGT, umfeld.BAU_MIN_HOEHE_M, 0.011) and umfeld.BAU_MIN_HOEHE_M in REIHE_UEBERRAGT


def test_der_satz_ist_wiederholbar_und_ohne_fremde_daten():
    """Regel 3: Der Satz entsteht aus Zahlen im Erzeuger, zweimal erzeugt ist er gleich."""
    assert faelle() == FAELLE
    for f in FAELLE:
        assert len(f["boxen"]) == len(f["haus"]) >= 2
        for lo, hi in f["boxen"]:
            assert all(a < b for a, b in zip(lo, hi)), f["name"]


@pytest.mark.parametrize("fall", ENTSCHEIDBAR, ids=[f["name"] for f in ENTSCHEIDBAR])
def test_entscheidbarer_fall_ist_richtig_gruppiert(fall):
    cluster = gruppiere(umfeld.grundriss_cluster, fall)
    urteil = beurteile(fall, cluster)
    assert urteil["verschmelzungen"] == 0, urteil["grund"]
    assert urteil["richtig"], urteil["grund"]
    assert not gemeldet(cluster), "entscheidbarer Fall trägt den Vermerk mehrdeutig"


@pytest.mark.parametrize("fall", MEHRDEUTIG, ids=[f["name"] for f in MEHRDEUTIG])
def test_mehrdeutiger_fall_ist_gemeldet_und_nicht_schlechter_als_die_basis(fall):
    """Gleiche Körper, zwei Wahrheiten: Die Funktion rät nicht. Sie meldet es und liegt nie schlechter als die
    Basis (sie verschmilzt nichts, was die Basis trennte, und trennt keine Häuser, die die Basis hielt)."""
    cluster = gruppiere(umfeld.grundriss_cluster, fall)
    assert gemeldet(cluster)
    urteil, vorher = beurteile(fall, cluster), beurteile(fall, basis_cluster(fall["boxen"]))
    assert not schlechter(urteil, vorher), (urteil, vorher)
    alle = sorted(i for c in cluster if c["mehrdeutig"] for i in c["teile"])
    for c in cluster:
        if c["mehrdeutig"]:                                    # die andere Lesart deckt dieselben Teile
            assert c["andere_lesart"] and set(c["teile"]) <= {i for g in c["andere_lesart"] for i in g} <= set(alle)
        else:
            assert c["andere_lesart"] == []


def test_die_paare_sind_dieselben_koerper_in_zwei_lesarten():
    """Zu jeder Lesart «zwei Häuser» der Reihen Deckung und Sockelhöhe gibt es die Lesart «ein Haus» mit
    denselben Boxen. Beide sind gemeldet; höchstens eine kann richtig sein, und es ist die, die auch an der
    Basis richtig war."""
    nach_name = {f["name"]: f for f in FAELLE}
    paare = [(f, nach_name[f["name"].replace("-zwei-haeuser-", "-ein-haus-")]) for f in FAELLE
             if f["name"].startswith(("deckung", "sockel")) and "-zwei-haeuser-" in f["name"]]
    assert len(paare) == 2 * (len(REIHE_DECKUNG) + len(REIHE_SOCKELHOEHE))
    for zwei, ein in paare:
        assert zwei["boxen"] == ein["boxen"] and zwei["haus"] != ein["haus"]
        cluster = umfeld.grundriss_cluster(zwei["boxen"])
        assert gruppen_von(cluster) == gruppen_von(basis_cluster(zwei["boxen"])), zwei["name"]
        assert beurteile(zwei, cluster)["richtig"] + beurteile(ein, cluster)["richtig"] <= 1


def test_zielfunktion_runde_2():
    """Die Zielfunktion in Zahlen: 100 % der entscheidbaren Fälle richtig, 0 falsche Verschmelzungen in den
    entscheidbaren Gegenfällen, 0 Rückschritte gegen die Basis, jeder mehrdeutige Fall gemeldet, kein
    entscheidbarer mit Vermerk."""
    m = miss(umfeld.grundriss_cluster, basis_cluster)
    assert m["richtig"] == m["entscheidbar"], m["falsch"]
    assert m["verschmelzungen_gegenfaelle"] == 0 and m["verschmelzungen"] == 0, m["falsch"]
    assert m["rueckschritte"] == []
    assert m["gemeldet"] == m["mehrdeutig"]
    assert m["falsch_gemeldet"] == []
    vorher = miss(basis_cluster, basis_cluster)
    assert m["richtig_alle"] > vorher["richtig_alle"]


def test_kein_fall_des_gegenlesens_ist_schlechter_als_die_basis():
    """Die 44 Fälle, an denen die erste Lösung scheiterte: Die Basis hatte 20 richtig; keiner davon geht
    verloren, und die 15 Verbesserungen auf der Geländeplatte (Blockrand, gedrehte Formen) bleiben."""
    gl = [f for f in FAELLE if f["herkunft"] == "gegenlesen"]
    vorher = [beurteile(f, basis_cluster(f["boxen"])) for f in gl]
    jetzt = [beurteile(f, umfeld.grundriss_cluster(f["boxen"])) for f in gl]
    assert sum(u["richtig"] for u in vorher) == 20
    assert not any(schlechter(j, v) for j, v in zip(jetzt, vorher))
    assert sum(u["richtig"] for u in jetzt) == 35
    assert sum(u["verschmelzungen"] for u in jetzt) <= sum(u["verschmelzungen"] for u in vorher)


def _ohne_vermerk(cluster):
    return [{k: v for k, v in c.items() if k not in ("mehrdeutig", "andere_lesart")} for c in cluster]


def test_ohne_zu_grossen_haufen_ist_das_ergebnis_woertlich_das_der_basis():
    """3000 Zufallsszenen nur aus Körpern und 3000 gemischt mit flachen Platten, alle ohne Geländeplatte: kein
    Haufen wächst über die Flächengrenze, und das Ergebnis ist Feld für Feld das der Basis (0 Abweichungen)."""
    rnd = random.Random(3012)
    for nummer in range(6000):
        boxen = zufallsszene(rnd, flache_platten=nummer % 2 == 1, gelaendeplatte=False)
        assert _ohne_vermerk(umfeld.grundriss_cluster(boxen)) == basis_cluster(boxen), nummer


def _stapel(boxen):
    """Unabhängig von ``umfeld`` nachgerechnet: je Box ihr Stapel (gleicher Grundriss auf 0,5 m) und dessen
    Unter- und Oberkante."""
    schluessel = [tuple(round(v * 2) / 2 for v in (b[0][0], b[1][0], b[0][1], b[1][1])) for b in boxen]
    z: dict = {}
    for s, b in zip(schluessel, boxen):
        lo, hi = z.get(s, (b[0][2], b[1][2]))
        z[s] = (min(lo, b[0][2]), max(hi, b[1][2]))
    return schluessel, [z[s] for s in schluessel]


def _fluegelstoss(boxen, i, j, schluessel, kanten) -> bool:
    """Die Regel des Flügelstosses, hier ein zweites Mal und ohne die Helfer aus ``umfeld`` geschrieben."""
    a, b = boxen[i], boxen[j]
    bx, by = min(a[1][0], b[1][0]) - max(a[0][0], b[0][0]), min(a[1][1], b[1][1]) - max(a[0][1], b[0][1])
    if bx <= 0.01 or by <= 0.01:
        return False
    if schluessel[i] == schluessel[j]:
        return True
    hoehe = [o - u for u, o in kanten]
    fa, fb = (a[1][0] - a[0][0]) * (a[1][1] - a[0][1]), (b[1][0] - b[0][0]) * (b[1][1] - b[0][1])
    if max(fa, fb) > 20_000 or min(hoehe[i], hoehe[j]) < 1.0 or min(bx, by) < 0.5:
        return False
    in_x = abs(bx - min(a[1][0] - a[0][0], b[1][0] - b[0][0])) <= 0.02       # das schmalere steckt ganz drin
    in_y = abs(by - min(a[1][1] - a[0][1], b[1][1] - b[0][1])) <= 0.02
    if not (in_x or in_y):
        return False
    if fa == fb:
        return True
    klein, gross = (i, j) if fa < fb else (j, i)
    gleich_hoch = max(abs(kanten[i][0] - kanten[j][0]), abs(kanten[i][1] - kanten[j][1])) <= 0.01
    k, g = boxen[klein], boxen[gross]
    ganz_drin = all(k[0][s] >= g[0][s] - 0.01 and k[1][s] <= g[1][s] + 0.01 for s in (0, 1))
    if ganz_drin or (not gleich_hoch and bx * by >= 0.9 * min(fa, fb)):
        return False
    return not (hoehe[gross] <= 3.0 and hoehe[klein] - hoehe[gross] >= 1.0)


def _zusammenhaengend(teile, kante) -> bool:
    erreicht, rand = {teile[0]}, [teile[0]]
    while rand:
        i = rand.pop()
        for j in teile:
            if j not in erreicht and kante(i, j):
                erreicht.add(j)
                rand.append(j)
    return erreicht == set(teile)


def test_auf_der_gelaendeplatte_weicht_nur_ab_was_sich_als_fluegel_durchdringt():
    """6000 Zufallsszenen auf einer Geländeplatte (je zur Hälfte nur Körper und gemischt mit flachen Platten).
    Jede Abweichung von der Basis ist eine Vereinigung von Gruppen der Basis, die über Durchdringungen
    zusammenhängt (die Verbesserung, die der Satz in den Gruppen «fluegel» und «gang» belegt) und nicht über
    die Flächengrenze wächst. Nichts, was die Basis zusammenhielt, wird getrennt."""
    rnd = random.Random(3013)
    abweichungen = 0
    for nummer in range(6000):
        boxen = zufallsszene(rnd, flache_platten=nummer % 2 == 1, gelaendeplatte=True)
        vorher, jetzt = gruppen_von(basis_cluster(boxen)), gruppen_von(umfeld.grundriss_cluster(boxen))
        if vorher == jetzt:
            continue
        abweichungen += 1
        schluessel, kanten = _stapel(boxen)
        for gruppe in jetzt - vorher:
            teile = sorted(gruppe)
            assert all(alt <= gruppe or not (alt & gruppe) for alt in vorher), nummer
            assert _zusammenhaengend(teile, lambda i, j: _fluegelstoss(boxen, i, j, schluessel, kanten)), nummer
            flaeche = ((max(boxen[i][1][0] for i in teile) - min(boxen[i][0][0] for i in teile))
                       * (max(boxen[i][1][1] for i in teile) - min(boxen[i][0][1] for i in teile)))
            assert flaeche <= umfeld.BAU_MAX_FLAECHE_M2, nummer
    assert abweichungen > 1000                                  # die Probe prüft wirklich etwas


@pytest.mark.parametrize("gelaendeplatte", [False, True], ids=["frei", "gelaende"])
def test_zufallsszenen_mit_wahrheit_kein_rueckschritt(gelaendeplatte):
    """Je 3000 Zufallsszenen mit bekannter Wahrheit (Flügelbauten, auch gedreht; Häuser auf Belägen; Nachbarn;
    Körper auf gemeinsamer Platte in beiden Lesarten): Keine Szene ist schlechter gruppiert als an der Basis.
    Ohne Geländeplatte ist das Ergebnis das der Basis; mit ihr sind es deutlich mehr richtige Szenen."""
    rnd = random.Random(3014 + gelaendeplatte)
    richtig_vorher = richtig_jetzt = 0
    for nummer in range(3000):
        fall = zufallsfall(rnd, gelaendeplatte=gelaendeplatte)
        cluster = umfeld.grundriss_cluster(fall["boxen"])
        urteil, vorher = beurteile(fall, cluster), beurteile(fall, basis_cluster(fall["boxen"]))
        assert not schlechter(urteil, vorher), (nummer, urteil, vorher)
        richtig_vorher += vorher["richtig"]
        richtig_jetzt += urteil["richtig"]
        if not gelaendeplatte:
            assert gruppen_von(cluster) == gruppen_von(basis_cluster(fall["boxen"])), nummer
        if not urteil["richtig"] and not gemeldet(cluster):
            # Unrichtig ohne Vermerk darf nur sein, was die Basis genauso gruppiert (gedrehte Flügel, deren
            # Hüllquader fast ineinander liegen, oder eine Flügelgruppe über der Flächengrenze).
            assert gruppen_von(cluster) == gruppen_von(basis_cluster(fall["boxen"])), nummer
    assert richtig_jetzt >= richtig_vorher
    if gelaendeplatte:
        assert richtig_jetzt > 1.5 * richtig_vorher


def test_grenze_der_eingabe_ist_gemessen_und_nicht_versteckt():
    """Was die Regel NICHT kann, steht hier als Zahl. Die Funktion sieht nur Hüllquader. Gleich grosse schräge
    Nachbarn überlappen sich nur über Eck und bleiben getrennt. Ein kleiner schräger Nachbar, dessen Hüllquader
    mit ganzer Breite in dem des Hauses steckt, hat dieselben Boxen wie ein Anbau im Hauptbau: Die Regel hält ihn
    für den Anbau (so verlangt es der Auftrag), und in der Lesart «zwei Bauten» ist das auf der Geländeplatte
    schlechter als die Basis. Die Probe hält fest, wie oft das vorkommt, damit es niemand für gelöst hält."""
    for fall in GRENZE:                                         # je Paar ist genau die Lesart «ein Bau» richtig
        ein_bau = "anbau" in fall["name"] or "drei-teile" in fall["name"]
        assert beurteile(fall, umfeld.grundriss_cluster(fall["boxen"]))["richtig"] == ein_bau, fall["name"]
        assert beurteile(fall, basis_cluster(fall["boxen"]))["richtig"] == (not ein_bau), fall["name"]
    rnd = random.Random(3016)
    szenen = schlechter_als_basis = 0
    for _ in range(3000):
        fall = zufallsfall(rnd, gelaendeplatte=True, schopf=True)
        urteil = beurteile(fall, umfeld.grundriss_cluster(fall["boxen"]))
        szenen += 1
        schlechter_als_basis += schlechter(urteil, beurteile(fall, basis_cluster(fall["boxen"])))
    assert 0 < schlechter_als_basis < 0.12 * szenen, schlechter_als_basis        # gemessen: 249 von 3000


@pytest.mark.parametrize("gelaendeplatte", [False, True], ids=["frei", "gelaende"])
def test_mit_echten_grundrissen_ist_die_grenze_weg(gelaendeplatte):
    """Je 3000 Zufallsszenen aus schrägen Flügelbauten und schrägen Zeilen (gleich und ungleich gross, 0,5 bis
    6 m echte Lücke). Bringt jedes Teil sein Vieleck mit, ist JEDE Szene richtig gruppiert, und keine ist
    schlechter als an der Basis. Dieselben Szenen nur mit Hüllquadern zeigen die Grenze der Eingabe: Dort sind
    auf der Geländeplatte Szenen schlechter als an der Basis, und zwar nur solche mit einer Zeile."""
    rnd_a, rnd_b = random.Random(3017 + gelaendeplatte), random.Random(3017 + gelaendeplatte)
    schlechter_nur_huellen = 0
    for nummer in range(3000):
        fall = zufallsfall_schraeg(rnd_a, gelaendeplatte=gelaendeplatte, grundrisse=True)
        cluster = gruppiere(umfeld.grundriss_cluster, fall)
        urteil = beurteile(fall, cluster)
        assert urteil["richtig"], (nummer, urteil["grund"])
        assert not gemeldet(cluster), nummer
        huellen = zufallsfall_schraeg(rnd_b, gelaendeplatte=gelaendeplatte, grundrisse=False)
        assert huellen["boxen"] == fall["boxen"] and huellen["grundrisse"] is None
        vorher = beurteile(huellen, basis_cluster(huellen["boxen"]))
        assert not schlechter(urteil, vorher), nummer
        ohne = beurteile(huellen, umfeld.grundriss_cluster(huellen["boxen"]))
        if schlechter(ohne, vorher):
            schlechter_nur_huellen += 1
            assert gelaendeplatte and ohne["verschmelzungen"] > 0, nummer
    if gelaendeplatte:
        assert 0 < schlechter_nur_huellen < 0.5 * 3000, schlechter_nur_huellen
    else:
        assert schlechter_nur_huellen == 0


def test_grundrisse_die_nichts_sagen_aendern_nichts():
    """``grundrisse=None``, eine leere Liste und eine Liste aus lauter ``None`` sind dasselbe wie kein Grundriss:
    die Boxen gelten. So bleibt jeder bisherige Aufruf, was er war."""
    rnd = random.Random(3018)
    for nummer in range(300):
        boxen = zufallsszene(rnd, flache_platten=True, gelaendeplatte=nummer % 2 == 1)
        ohne = umfeld.grundriss_cluster(boxen)
        assert umfeld.grundriss_cluster(boxen, grundrisse=None) == ohne
        assert umfeld.grundriss_cluster(boxen, grundrisse=[]) == ohne
        assert umfeld.grundriss_cluster(boxen, grundrisse=[None] * len(boxen)) == ohne
        # Ein Vieleck ohne Fläche (ein Punkt, eine Strecke) sagt auch nichts: Fund der eigenen Gegenprobe, ein
        # Ein-Punkt-Vieleck band sonst je nach Reihenfolge der Eingabe.
        entartet = [[(25.0, 5.0)] * 3 if k % 2 else [(0.0, 0.0), (4.0, 4.0)] for k in range(len(boxen))]
        assert umfeld.grundriss_cluster(boxen, grundrisse=entartet) == ohne


def test_echter_grundriss_entscheidet_statt_der_huelle():
    """Zwei um 45 Grad gedrehte Häuser mit 3 m echter Lücke: Ihre Hüllquader überlappen sich, sie selbst nicht.
    Nur mit Hüllquadern ist das ohne Geländeplatte ein Cluster (wie an der Basis, mit Vermerk); mit Grundrissen
    sind es zwei Bauten, frei und auf der Geländeplatte, ohne Vermerk. Der Umlaufsinn des Vielecks ist egal."""
    a = [(0.0, 0.0), (9.9, 9.9), (3.54, 16.26), (-6.36, 6.36)]                  # 14 × 9 m, 45 Grad
    b = [(x + 8.49, y - 8.49) for x, y in a]                                   # 12 m quer versetzt: 3 m Lücke
    boxen = [((min(p[0] for p in v), min(p[1] for p in v), 0.0), (max(p[0] for p in v), max(p[1] for p in v), 9.0))
             for v in (a, b)]
    assert [c["teile"] for c in basis_cluster(boxen)] == [[0, 1]]
    nur_huellen = umfeld.grundriss_cluster(boxen)
    assert [c["teile"] for c in nur_huellen] == [[0, 1]] and nur_huellen[0]["mehrdeutig"]
    for vielecke in ([a, b], [a[::-1], b]):
        for platte in ([], [GELAENDE]):
            c = umfeld.grundriss_cluster(boxen + platte, grundrisse=vielecke)
            assert sorted(x["teile"] for x in c if x["art"] != "boden") == [[0], [1]]
            assert not any(x["mehrdeutig"] for x in c)
    # Schieben sich die echten Grundrisse 2 m ineinander, ist es ein Bau, auch auf der Geländeplatte.
    b2 = [(x + 4.95, y + 4.95) for x, y in a]                                  # 7 m längs versetzt
    boxen2 = [boxen[0], ((min(p[0] for p in b2), min(p[1] for p in b2), 0.0),
                         (max(p[0] for p in b2), max(p[1] for p in b2), 9.0))]
    c = umfeld.grundriss_cluster(boxen2 + [GELAENDE], grundrisse=[a, b2])
    assert sorted(x["teile"] for x in c if x["art"] != "boden") == [[0, 1]]


def test_schnitt_und_mindestbreite_konvexer_vielecke():
    """Die zwei Helfer für echte Grundrisse an Fällen, die man im Kopf nachrechnet."""
    q = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]
    r = [(2.0, 1.0), (6.0, 1.0), (6.0, 3.0), (2.0, 3.0)]
    s = umfeld._schnitt_konvex(q, r)
    assert umfeld._polygon_flaeche(s) == pytest.approx(4.0) and umfeld._mindestbreite(s) == pytest.approx(2.0)
    assert umfeld._schnitt_konvex(q, [(5.0, 0.0), (6.0, 0.0), (6.0, 1.0), (5.0, 1.0)]) == []
    raute = [(2.0, -1.0), (5.0, 2.0), (2.0, 5.0), (-1.0, 2.0)]                # Quadrat, 45 Grad, Kante 4,24
    assert umfeld._mindestbreite(raute) == pytest.approx(18 ** 0.5)
    assert umfeld._polygon_flaeche(umfeld._schnitt_konvex(q, raute)) == pytest.approx(14.0)
    assert umfeld._mindestbreite([(0.0, 0.0), (10.0, 0.0), (10.0, 0.5), (0.0, 0.5)]) == pytest.approx(0.5)


def test_ohne_vermerk_aendert_die_gelaendeplatte_nichts():
    """Der Kern des Befunds als Eigenschaft, jetzt mit seiner Grenze: Trägt keine Gruppe den Vermerk, sind die
    Gruppen mit und ohne Geländeplatte wörtlich dieselben. Mit Vermerk hängt die Antwort von der Umgebung ab
    (wie an der Basis); genau das sagt der Vermerk."""
    rnd = random.Random(301)
    ohne_vermerk = 0
    for nummer in range(2000):
        boxen = zufallsszene(rnd, flache_platten=nummer % 2 == 1, gelaendeplatte=False)
        frei = umfeld.grundriss_cluster(boxen)
        mit = umfeld.grundriss_cluster(boxen + [GELAENDE])
        boden = [c for c in mit if len(boxen) in c["teile"]]
        assert len(boden) == 1 and boden[0]["teile"] == [len(boxen)] and boden[0]["art"] == "boden", nummer
        assert sorted(i for c in mit for i in c["teile"]) == list(range(len(boxen) + 1)), nummer
        auf_platte = {frozenset(c["teile"]): c for c in mit if c is not boden[0]}
        for c in frei:
            if not c["mehrdeutig"]:
                ohne_vermerk += 1
                assert frozenset(c["teile"]) in auf_platte, nummer
                assert _ohne_vermerk([auf_platte[frozenset(c["teile"])]]) == _ohne_vermerk([c]), nummer
            else:                                              # die andere Lesart ist die auf der Platte
                assert {frozenset(g) for g in c["andere_lesart"]} <= set(auf_platte) or any(
                    len(g) > 1 for g in c["andere_lesart"]), nummer
    assert ohne_vermerk > 2000


def test_die_gelaendeplatte_aendert_die_fluegelbauten_nicht():
    """Für jeden entscheidbaren Fall, den es frei und auf der Geländeplatte gibt: dieselben Häuser."""
    def haeuser(fall):
        aus = set()
        for c in gruppiere(umfeld.grundriss_cluster, fall):
            teile = [i for i in c["teile"] if fall["haus"][i] is not None]
            if teile:
                aus.add(frozenset(fall["boxen"][i] for i in teile))
        return aus
    nach_name = {f["name"]: f for f in ENTSCHEIDBAR}
    paare = [(f, nach_name[n]) for f in ENTSCHEIDBAR if f["name"].endswith("-frei")
             for n in [f["name"][:-len("frei")] + "gelaende"] if n in nach_name]
    assert len(paare) >= 30
    for frei, gelaende in paare:
        assert haeuser(frei) == haeuser(gelaende), frei["name"]


def test_die_reihenfolge_der_teile_aendert_die_gruppen_nicht():
    """Dieselben Boxen rückwärts: dieselben Gruppen (als Mengen von Boxen), dieselbe Art, derselbe Vermerk."""
    for fall in FAELLE:
        vor = {(frozenset(fall["boxen"][i] for i in c["teile"]), c["art"], c["mehrdeutig"])
               for c in gruppiere(umfeld.grundriss_cluster, fall)}
        rueck_boxen = fall["boxen"][::-1]
        vielecke = fall["grundrisse"][::-1] if fall["grundrisse"] else None
        rueck = {(frozenset(rueck_boxen[i] for i in c["teile"]), c["art"], c["mehrdeutig"])
                 for c in umfeld.grundriss_cluster(rueck_boxen, grundrisse=vielecke)}
        assert vor == rueck, fall["name"]


def test_eine_kette_knapp_ueberlappender_platten_bleibt_zerlegt():
    """Was Ergebnis 359 festlegt, bleibt: Platten, die nur als Kette über die Flächengrenze wachsen und nichts
    tragen, werden weiter einzeln beurteilt und nicht zu einem Boden verschmolzen."""
    kette = [((119.5 * k, 0.0, 0.0), (119.5 * k + 120.0, 100.0, 2.0)) for k in range(4)]
    c = umfeld.grundriss_cluster(kette)
    assert sorted(x["teile"] for x in c) == [[0], [1], [2], [3]]
    assert all(x["art"] == "bau" and not x["mehrdeutig"] for x in c)


def test_sockel_oder_belag_wird_nicht_geraten():
    """Die erste Lösung entschied mit der Deckung, ob eine Platte Sockel oder Belag ist, und riet damit. Jetzt:
    Frei bleibt die Platte mit allem darauf ein Bau, wie an der Basis, wie viel auch gedeckt ist und wie hoch
    sie ist; auf der Geländeplatte bleiben die Teile getrennt, wie an der Basis. Beides trägt den Vermerk."""
    teile = [((1.0, 1.0, 0.3), (11.0, 9.0, 8.0)), ((14.0, 1.0, 0.3), (24.0, 9.0, 8.0))]
    sockel = ((0.0, 0.0, 0.0), (25.0, 10.0, 0.3))                         # 160 von 250 m² gedeckt
    belag = ((-10.0, -10.0, 0.0), (40.0, 22.0, 0.3))                      # 160 von 1600 m² gedeckt
    podium = ((-10.0, -10.0, -4.5), (40.0, 22.0, 0.3))                    # 4,8 m hoher Sockelbau
    for platte in (sockel, belag, podium):
        frei = umfeld.grundriss_cluster([platte] + teile)
        assert [x["teile"] for x in frei] == [[0, 1, 2]] and frei[0]["bau"] and frei[0]["mehrdeutig"]
        assert frei[0]["andere_lesart"] == [[0], [1], [2]]
        mit = umfeld.grundriss_cluster([platte] + teile + [GELAENDE])
        assert sorted(x["teile"] for x in mit) == [[0], [1], [2], [3]]
        assert all(x["mehrdeutig"] and x["andere_lesart"] == [[0, 1, 2]] for x in mit if x["teile"] != [3])
        assert not [x for x in mit if x["teile"] == [3]][0]["mehrdeutig"]


def test_ein_haus_das_ueber_den_hofbelag_ragt_bindet_ihn_nicht():
    """Mangel 2 des Gegenlesens: Ein Haus, das über den Rand eines Belags ragt, band ihn in der ersten Lösung
    und verschmolz so mit dem Nachbarhaus. Ein Belag (unter ``BAU_MIN_HOEHE_M``) bindet im Haufen nie."""
    belag = ((0.0, 0.0, 0.0), (44.0, 30.0, 0.1))
    a, b = ((8.0, 10.0, 0.0), (20.0, 20.0, 9.0)), ((38.0, 10.0, 0.0), (50.0, 20.0, 9.0))
    mit = umfeld.grundriss_cluster([belag, a, b, GELAENDE])
    assert sorted(x["teile"] for x in mit) == [[0], [1], [2], [3]]
    assert [x["art"] for x in mit if x["teile"] == [0]] == ["belag"]


def test_nur_ueberlappende_teile_kommen_in_eine_gruppe():
    """Was auch immer gelöst wird: Eine Gruppe ist über Überlappungen zusammenhängend. Die Regel aus
    Ergebnis 359 (Berühren genügt nicht) gilt in jeder Gruppe weiter."""
    rnd = random.Random(359)
    for nummer in range(600):
        boxen = zufallsszene(rnd, flache_platten=True, gelaendeplatte=nummer % 2 == 1)
        for c in umfeld.grundriss_cluster(boxen):
            assert _zusammenhaengend(c["teile"], lambda i, j: umfeld._ueberlappt(
                (boxen[i][0][:2], boxen[i][1][:2]), (boxen[j][0][:2], boxen[j][1][:2]),
                rand=umfeld.CLUSTER_LUECKE_M)), (nummer, c["teile"])
