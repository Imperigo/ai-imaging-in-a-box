"""Der Rauschboden ist keine Konstante des Rauschens, sondern der Maskenlage.

**Der Befund kommt von der HomeStation** (`auf-vis-20260824-10`, 24.08.2026) und trifft
eine Zahl, die seit dem 21.08. als Konstante im Code steht.

`depth-anything-v2-small` hat ein **festes Ortsfeld**: Was es auf einem leeren Bild
ausgibt, ist zu **95,75 %** eine Funktion des Ortes — zirkelfrei gemessen, das Feld aus 15
Rauschbildern gewonnen und an 15 anderen geprüft. Dieselbe Rauschkarte mit derselben, nur
verschobenen Maske:

    96 px hoch    ρ −0,6249
    Mitte         ρ +0,5207   ← genau der Betrag unserer Konstanten
    96 px runter  ρ +0,6387
    96 px rechts  ρ +0,6513

Ausschlag 1,28 **mit Vorzeichenwechsel**. Zwei Kontrollen schliessen aus, dass es am Mass
liegt: Karte und Maske gemeinsam verschoben ändert nichts, und das mittlere Feld allein
sagt den Boden an allen 13 Lagen vorher (Korrelation 0,9993).

**Der Boden wurde bei uns immer schon je Lauf gemessen** — `_nullprobe` läuft je Kamera.
Er wurde nur nie **gelesen**. Das ist die fünfte tote Kante dieser Woche, und die teuerste:
Sie sass unter dem Tor.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aiimaging import abholer, geometrie_qa as g
from aiimaging.geometrie_qa import PAAR_RHO_SCHWELLE


def _anker(**rhos) -> dict:
    return {art: {"rho": wert, "kante": None} for art, wert in rhos.items()}


# --------------------------------------------------------------------------------------
# 1 · Gegen den gemessenen Boden, nicht gegen die Konstante
# --------------------------------------------------------------------------------------

def test_der_abstand_wird_gegen_den_HOECHSTEN_nullanker_gemessen():
    """Ein echtes Bild muss den **besten** Nullanker schlagen, nicht den bequemsten.

    Sonst schlägt man den Boden, indem man sich den Anker aussucht — dieselbe Fehlerart
    wie ein Mittelwert über Urteile, der ein durchgefallenes Bild hinter zwei bestandenen
    verschwinden lässt.
    """
    e = g.rho_gegen_gemessenen_boden(0.91, _anker(rauschen=-0.52, grau=0.10, verlauf=-0.30))

    assert e["boden"] == pytest.approx(0.10)
    assert e["boden_art"] == "grau"
    assert e["abstand"] == pytest.approx(0.81)


def test_liegt_der_boden_ueber_der_schwelle_traegt_das_tor_nicht_mehr():
    """**Der Befund, für den es diese Funktion gibt.**

    Über verschiedene Maskenlagen schwankt der Abstand der Schwelle 0,80 zum Boden
    zwischen 0,15 und 1,42. Wird er negativ, lässt das Tor an dieser Lage Rauschen durch —
    und das ist ein Befund über die **Kameralage**, nicht über das Bild.
    """
    e = g.rho_gegen_gemessenen_boden(0.91, _anker(rauschen=0.85))

    assert e["schwelle_traegt"] is False
    assert any("Rauschen durch" in w for w in e["warnungen"])
    assert any("keine andere Schwelle" in w for w in e["warnungen"]), (
        "die Abhilfe gehoert dazu — sonst senkt jemand die Schwelle, und das waere "
        "genau die falsche Richtung")


def test_gegenprobe_ein_tiefer_boden_traegt():
    """Ohne sie zeigte der Test darüber nur, dass die Prüfung immer anschlägt."""
    e = g.rho_gegen_gemessenen_boden(0.91, _anker(rauschen=-0.52))

    assert e["schwelle_traegt"] is True
    assert e["warnungen"] == []


def test_ohne_nullprobe_steht_rho_gegen_nichts():
    """**Und die Konstante hilft dort ausdrücklich nicht.**

    Wer bei fehlender Nullprobe auf `RAUSCHBODEN_UEBER_MASKE` ausweicht, vergleicht mit
    der Zahl einer anderen Maskenlage — bei einem Ausschlag von 1,28 mit Vorzeichenwechsel
    ist das schlimmer als kein Vergleich.
    """
    e = g.rho_gegen_gemessenen_boden(0.91, None)

    assert e["boden"] is None
    assert e["abstand"] is None
    assert any("gegen NICHTS" in w for w in e["warnungen"])


def test_ohne_rho_ist_der_abstand_nicht_gemessen_und_nicht_null():
    e = g.rho_gegen_gemessenen_boden(None, _anker(rauschen=-0.52))

    assert e["boden"] == pytest.approx(-0.52), "der Boden steht trotzdem da"
    assert e["abstand"] is None
    assert any("NICHT GEMESSEN" in w for w in e["warnungen"])


def test_anker_ohne_rho_werden_uebergangen_und_nicht_als_null_gelesen():
    e = g.rho_gegen_gemessenen_boden(0.91, {"rauschen": {"rho": None, "kante": 0.2},
                                            "grau": {"rho": -0.4}})

    assert e["boden_art"] == "grau"


def test_die_konstante_traegt_ihre_eigene_widerlegung():
    """Wer `-0.5207` liest, muss im selben Blick sehen, dass sie für **eine Lage** gilt.

    Eine Konstante, deren Widerlegung nur im Sitzungsprotokoll steht, wird weiterbenutzt.
    """
    from pathlib import Path

    quelle = Path(g.__file__).read_text(encoding="utf-8")
    ende = quelle.index("RAUSCHBODEN_UEBER_MASKE = -0.5207")
    # Den ganzen zusammenhaengenden Kommentarblock nehmen und nicht eine feste
    # Zeichenzahl davor: Ein Docstring waechst, und ein Fenster in Zeichen bricht dann
    # aus einem Grund, der mit der Sache nichts zu tun hat. (Genau das ist passiert.)
    zeilen = quelle[:ende].splitlines()
    block_zeilen = []
    for zeile in reversed(zeilen):
        if not zeile.startswith("#:"):
            break
        block_zeilen.append(zeile)
    block = "\n".join(reversed(block_zeilen))

    assert "Ortsfeld" in block
    assert "95,75" in block
    assert "Vorzeichenwechsel" in block
    assert "nicht additiv" in block, (
        "auch die Widerlegung des Abzugs gehoert an die Konstante — sonst baut ihn jemand")


# --------------------------------------------------------------------------------------
# 2 · Und es erreicht den Menschen am Terminal
# --------------------------------------------------------------------------------------

def test_der_kurzbefund_nennt_die_kamera_deren_schwelle_nichts_mehr_trennt():
    befund = {"kameras": [
        {"kamera": "s", "bodenabstand": {"schwelle_traegt": False, "boden": 0.85}},
        {"kamera": "sSE", "bodenabstand": {"schwelle_traegt": True, "boden": -0.52}},
    ]}

    treffer = [z for z in abholer.befund_kurz(befund) if "SCHWELLE TRAEGT HIER NICHT" in z]

    assert len(treffer) == 1
    assert "s" in treffer[0] and "sSE" not in treffer[0]


def test_der_kurzbefund_nennt_auch_die_fehlende_nullprobe():
    """Zwei verschiedene Befunde, zwei verschiedene Zeilen.

    Eine Schwelle, die hier nichts mehr trennt, ist etwas anderes als gar kein Vergleich.
    """
    befund = {"kameras": [
        {"kamera": "nNW", "bodenabstand": {"schwelle_traegt": None, "boden": None}}]}

    zeilen = abholer.befund_kurz(befund)

    assert [z for z in zeilen if "Kein gemessener Rauschboden" in z]
    assert not [z for z in zeilen if "SCHWELLE TRAEGT HIER NICHT" in z]


def test_gegenprobe_ein_tragender_boden_erzeugt_keine_zeile():
    befund = {"kameras": [
        {"kamera": "s", "bodenabstand": {"schwelle_traegt": True, "boden": -0.52}}]}

    assert abholer.befund_kurz(befund) == ()


def test_die_schwelle_ist_dieselbe_wie_im_paartest():
    """Eine Zahl, die an zwei Stellen steht, ist an einer davon bereits falsch."""
    e = g.rho_gegen_gemessenen_boden(0.9, _anker(rauschen=-0.5))

    assert e["schwelle"] == PAAR_RHO_SCHWELLE


# --------------------------------------------------------------------------------------
# 3 · Zwei Kameras eines Auftrags vergleichen Zahlen auf verschiedenen Skalen
# --------------------------------------------------------------------------------------
#
# Nachgerechnet fuer MODUS_SHIFT, den Vorgabemodus seit dem 23.08., bei 1600x992:
#
#     Flachbau  8 m auf 40 m   Shift 2.0 mm ->  89 px senkrecht
#     Wohnhaus 15 m auf 35 m   Shift 5.8 mm -> 258 px
#     Wohnhaus 15 m auf 25 m   Shift 8.1 mm -> 361 px
#     Grenze MAX_SHIFT_MM 12 mm            -> 533 px
#
# Das Ortsfeld wurde in Schritten von 96 px vermessen, und dort drehte der Rauschboden um
# 1.28 mit Vorzeichenwechsel. Unsere Kameras liegen also ein bis fuenf Schritte auseinander.

def _kamera(name, rho, abstand):
    return {"kamera": name, "rho_maske": {"gerichtet": rho},
            "bodenabstand": {"abstand": abstand}}


def test_die_zweite_rechnung_deckt_eine_gedrehte_reihenfolge_auf():
    """**Der Fall, für den es diese Rechnung gibt.**

    Kamera `s` hat das niedrigere ρ, steht aber an einer Maskenlage mit sehr tiefem Boden
    — gemessen ist sie die bessere. Roh ausgewählt trüge das Urteil die falsche Kamera.
    """
    e = abholer._bodenspanne([_kamera("s", 0.60, 1.12), _kamera("sSE", 0.72, 0.20)])

    assert e["einig"] is False
    assert e["schlechteste_roh"] == "s"
    assert e["schlechteste_nach_boden"] == "sSE"
    assert "NICHT entschieden" in e["hinweis"], (
        "die Rechnung entscheidet nichts — 'schlechteste bleibt' ist ein Owner-Entscheid")


def test_gegenprobe_stimmen_beide_ueberein_hat_es_keine_folgen():
    """Ohne sie zeigte der Test darüber nur, dass die Rechnung immer streitet."""
    e = abholer._bodenspanne([_kamera("s", 0.60, 0.20), _kamera("sSE", 0.72, 1.12)])

    assert e["einig"] is True
    assert "keine Folgen" in e["hinweis"]


def test_die_rechnung_fasst_die_uebergebenen_urteile_nicht_an():
    """Die Rechnung steht **daneben** und nicht anstelle.

    «Schlechteste bleibt» ist ein Owner-Entscheid vom 22.08. Eine Nebenrechnung, die
    unbemerkt die Auswahl verschiebt, wäre eine stille Regeländerung — und die ist in
    diesem Projekt schon einmal vorgekommen (drei Ansichten haben das Gate verschärft,
    ohne dass es jemand entschieden hatte).
    """
    urteile = [_kamera("s", 0.60, 1.12), _kamera("sSE", 0.72, 0.20)]
    vorher = [dict(u) for u in urteile]

    e = abholer._bodenspanne(urteile)

    assert e["schlechteste_nach_boden"] == "sSE"
    assert urteile == vorher, "die Nebenrechnung hat die Urteile veraendert"


def test_eine_einzelne_kamera_ergibt_keinen_vergleich():
    assert abholer._bodenspanne([_kamera("s", 0.60, 1.12)]) is None
    assert abholer._bodenspanne([]) is None


def test_kameras_ohne_gemessenen_boden_zaehlen_nicht_mit():
    """Nicht gemessen ist nicht null — auch hier nicht.

    Eine Kamera ohne Nullprobe hat keinen Abstand, und sie mit 0 einzusetzen hiesse, ihr
    einen Boden von genau ρ zuzuschreiben.
    """
    e = abholer._bodenspanne([_kamera("s", 0.60, 1.12), _kamera("sSE", 0.72, 0.20),
                              {"kamera": "nNW", "rho_maske": {"gerichtet": 0.10},
                               "bodenabstand": {"abstand": None}}])

    assert e["n"] == 2
    assert "nNW" not in (e["schlechteste_roh"], e["schlechteste_nach_boden"])


def test_der_kurzbefund_meldet_die_uneinigkeit():
    befund = {"kameras": [], "geometrie_urteil": {
        "bodenspanne": {"einig": False, "schlechteste_roh": "s",
                        "schlechteste_nach_boden": "sSE"}}}

    treffer = [z for z in abholer.befund_kurz(befund) if "KAMERAWAHL UNEINIG" in z]

    assert len(treffer) == 1
    assert "NICHT" in treffer[0]


def test_gegenprobe_bei_einigkeit_steht_die_zeile_nicht_da():
    befund = {"kameras": [], "geometrie_urteil": {"bodenspanne": {"einig": True}}}

    assert not [z for z in abholer.befund_kurz(befund) if "KAMERAWAHL UNEINIG" in z]


def test_der_shift_verschiebt_die_maske_in_der_groessenordnung_des_ortsfelds():
    """**Die Rechnung, aus der die ganze Sache folgt** — hier nachvollziehbar, nicht als
    Zahl im Kommentar.

    `MODUS_SHIFT` ist seit dem 23.08. die Vorgabe. Er verschiebt die Bildlage des Bauwerks
    senkrecht, und senkrecht ist die Achse, auf der das Ortsfeld am stärksten wirkt.
    """
    from aiimaging import kameras as k

    sensor_hoehe_mm = k.SENSOR_BREITE_MM * 992 / 1600
    e = k.shift_aus_ziel((0.0, -35.0, k.AUGENHOEHE_M), (0.0, 0.0, 7.5),
                         brennweite_mm=k.BRENNWEITE_MM)
    px = e["shift_mm"] / sensor_hoehe_mm * 992

    assert 96 < px, ("ein gewoehnliches Wohnhaus verschiebt die Maske um mehr als einen "
                     "Schritt des vermessenen Ortsfelds")
    assert k.MAX_SHIFT_MM / sensor_hoehe_mm * 992 > 5 * 96, (
        "die zugelassene Obergrenze allein sind mehr als fuenf Schritte")


# --------------------------------------------------------------------------------------
# 4 · Der Abstand ist ein ANZEIGER und kein besseres ρ
# --------------------------------------------------------------------------------------
#
# Am 24.08.2026 gemessen (acht Bildlagen desselben Bauwerks, gleicher Fuellgrad, ein
# Startwert): Das Ortsfeld legt sich NICHT additiv auf den Inhalt. Alle drei Formen, es
# herauszurechnen, ERHOEHTEN die Streuung — 0.1374 ohne Abzug gegen 0.2882 / 0.3090 /
# 0.4051 — und drehten bei 7, 6 bzw. 1 von 8 Lagen das Vorzeichen um.
#
# Die Verunreinigung selbst ist bestaetigt und beziffert: r = 0.9361 zwischen 'wie gut das
# Feld allein die Wahrheit trifft' und 'wie gut das Mass aussieht'.

def test_zwei_gleich_hohe_rho_sind_verschieden_viel_wert():
    """**Der Kern des Befunds vom 24.08.**

    Eine Lage erreichte ρ 0,9318 bei einem Feldbeitrag von 0,0240 — ehrlich. Eine andere
    sah nur deshalb gut aus, weil das Feld zufällig mit der Geometrie übereinstimmte.
    Die Bildlage entscheidet nicht, ob das Mass gut sein *kann*, sondern ob die Zahl
    ehrlich ist.
    """
    ehrlich = g.rho_gegen_gemessenen_boden(0.9318, _anker(rauschen=0.0240))
    geschmeichelt = g.rho_gegen_gemessenen_boden(0.9414, _anker(rauschen=0.70))

    assert ehrlich["boden_erklaert_anteil"] < 0.05
    assert geschmeichelt["boden_erklaert_anteil"] > 0.7
    assert ehrlich["warnungen"] == []
    assert any("BILDLAGE" in w for w in geschmeichelt["warnungen"])


def test_die_warnung_sagt_dazu_dass_herausrechnen_NICHT_hilft():
    """**Sonst ist der naheliegende Griff der falsche.**

    Wer liest «der Boden erklärt 74 %», will ihn abziehen. Genau das ist gemessen und
    macht die Streuung grösser — die Warnung muss es mitsagen, sonst baut es jemand.
    """
    e = g.rho_gegen_gemessenen_boden(0.94, _anker(rauschen=0.70))

    assert any("Herausrechnen hilft nicht" in w for w in e["warnungen"])


def test_bei_negativem_boden_wird_kein_anteil_behauptet():
    """Ein Boden unter null erklärt nichts von einem positiven ρ — dann steht dort auch
    keine Zahl. Eine Quote aus einem Vorzeichenwechsel wäre Unsinn mit Dezimalpunkt."""
    e = g.rho_gegen_gemessenen_boden(0.91, _anker(rauschen=-0.52))

    assert "boden_erklaert_anteil" not in e
    assert e["abstand"] == pytest.approx(1.43)


def test_der_docstring_traegt_die_widerlegung_des_abzugs():
    """Ein widerlegter Griff, dessen Widerlegung nur im Protokoll steht, wird gebaut.

    Die HomeStation hat uns denselben Dienst mit ihrem Irrweg erwiesen.
    """
    doc = g.rho_gegen_gemessenen_boden.__doc__

    assert "nicht additiv" in doc
    assert "0,9361" in doc
    assert "kein besseres ρ" in doc.replace("**", "")


# --------------------------------------------------------------------------------------
# 5 · Dieselbe Fehlerart bei der Startwertstreuung
# --------------------------------------------------------------------------------------

def test_die_seedstreuung_traegt_ihre_lageabhaengigkeit_mit():
    """**Dieselbe Ursache wie beim Rauschboden: das Ortsfeld.**

    Gemessen am 24.08.2026: Am selben Standort und Füllgrad, nur mit anderer Achsenlage,
    ist die Startwertstreuung 0,0088 gegen 0,1216 — **Faktor 14**. Eine Zahl, die man für
    eine Eigenschaft der Kette hält, ist eine Eigenschaft der Bildlage.

    Sie bleibt stehen, weil sie als Grössenordnung taugt — aber sie muss ihre Grenze
    mittragen, sonst wird sie als Naturkonstante verrechnet. Genau das ist mit
    `RAUSCHBODEN_UEBER_MASKE` eine Woche lang passiert.
    """
    from aiimaging import varianten

    quelle = Path(varianten.__file__).read_text(encoding="utf-8")
    ende = quelle.index("GEMESSENE_SEED_STREUUNG = 0.2269")
    block = "\n".join(z for z in quelle[:ende].splitlines()[-40:] if z.startswith("#:"))

    assert "KAMERALAGE" in block
    assert "Faktor 14" in block
    assert "Ortsfeld" in block, "die gemeinsame Ursache gehoert dazu, nicht nur die Zahl"


def test_der_boden_sagt_im_grund_dass_er_zu_gross_sein_kann():
    """Wer ihn benutzt, urteilt **vorsichtig** und nicht falsch — aber an der Lage vorbei.

    Der Unterschied gehört in den Text: «zu streng» ist eine andere Auskunft als «falsch»,
    und nur die erste erlaubt es, das Ergebnis trotzdem zu benutzen.
    """
    from aiimaging import varianten

    grund = varianten.GEMESSENER_BODEN["begruendung"]

    assert "KAMERALAGE" in grund
    assert "ZU GROSS" in grund
    assert "vorsichtig und nicht falsch" in grund
