"""Wo kein Himmel hinter dem Umriss steht, misst die Tiefenkante nichts.

**Der Anlass ist eine Messung, die ein Mass erledigt hat** (HomeStation,
`auf-vis-20260823-07`, 23.08.2026). Dieselbe Kamera, dasselbe Bauwerk, nur der
Hintergrund verschieden:

    g0 flaches Gelände      63,3 % Himmel hinter dem Umriss    Kante +0,4227
    g1 geneigtes Gelände     0,0 %                             Kante +0,1442
    g2 Nachbargebäude        0,0 %                             Kante +0,0016

In g2 trennt das zweite Bein ein **perfektes** Bild nicht mehr von weissem Rauschen
(+0,0016 gegen einen Rauschanker von −0,0024). Der Grund liegt nicht im Mass: Der Nachbar
steht im Soll 15,05 m weiter hinten, und ein monokularer Schätzer legt zwei Betonkörper
in 34 und 49 m praktisch nicht auseinander — der **wahre** Sprung ist dort am grössten
und der **gemessene** am kleinsten.

Daraus folgt keine bessere Normierung, sondern eine Zuständigkeitsgrenze. Diese Datei
prüft, dass der Paartest sie einhält — und zwar in beide Richtungen, denn ein Tor, das
überall schweigt, ist genauso wertlos wie eines, das überall besteht.

Alle Karten sind synthetisch und hier erzeugt (Regel 3).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aiimaging import abholer, geometrie_qa, tiefenschaetzer as ts
from aiimaging.geometrie_qa import MIN_HIMMELANTEIL, QaError

# --------------------------------------------------------------------------------------
# Zwei Szenen, die sich in genau einer Sache unterscheiden
# --------------------------------------------------------------------------------------

BREITE = 32
VON, BIS = 8, 23

#: Der Nachbar im Soll. Weit hinter dem Bauwerk (10–20 m) und trotzdem endlich — genau
#: der Fall, den das Soll kennt und die Schätzung nicht auflöst.
NACHBAR_M = 48.0

HIMMEL = float("inf")


def _maske() -> list[bool]:
    return [(VON <= x <= BIS and VON <= y <= BIS)
            for y in range(BREITE) for x in range(BREITE)]


def _soll(hinter) -> list[float]:
    """Bauwerk 10 → 20 m, dahinter ``hinter``.

    ``hinter`` darf eine Zahl sein oder eine Funktion ``(x, y) -> float``; die zweite Form
    baut den halb/halb-Fall, ohne dass es dafür eine zweite Szene braucht.
    """
    maske = _maske()
    n = 0
    gesamt = sum(maske)
    karte = []
    for i, m in enumerate(maske):
        if m:
            karte.append(10.0 + 10.0 * n / gesamt)
            n += 1
        else:
            x, y = i % BREITE, i // BREITE
            karte.append(hinter(x, y) if callable(hinter) else hinter)
    return karte


def _ist(soll) -> list[float]:
    """Disparität: nah = gross. Der Himmel bekommt einen kleinen Wert, kein ``inf``."""
    return [(1.0 / s if s != HIMMEL else 0.001) for s in soll]


def _himmel(hinter) -> dict:
    return geometrie_qa.himmel_hinter_umriss(_soll(hinter), _maske(), breite=BREITE)


# --------------------------------------------------------------------------------------
# 1 · Die Frage wird am SOLL beantwortet, nicht an der Schätzung
# --------------------------------------------------------------------------------------

def test_hinter_dem_umriss_steht_himmel_oder_ein_nachbar_und_das_mass_unterscheidet_es():
    """Die beiden Fälle als Paar — einzeln belegte keiner von beiden etwas.

    Ein Mass, das nur den Himmelfall sieht, könnte auch schlicht immer 1.0 melden.
    """
    frei = _himmel(HIMMEL)
    verbaut = _himmel(NACHBAR_M)

    assert frei["anteil"] == pytest.approx(1.0)
    assert frei["traegt"] is True
    assert verbaut["anteil"] == pytest.approx(0.0)
    assert verbaut["traegt"] is False


def test_ein_halb_verbauter_umriss_traegt_noch():
    """Die Schwelle verlangt 10 %, nicht 100 %. Halb offen ist messbar."""
    halb = _himmel(lambda x, _y: HIMMEL if x < BREITE // 2 else NACHBAR_M)

    assert 0.3 < halb["anteil"] < 0.7, "die Szene ist etwa halb offen gebaut"
    assert halb["traegt"] is True


def test_die_frage_ist_vor_der_messung_beantwortbar():
    """**Der Punkt, an dem die ganze Konstruktion hängt.**

    Eine Zuständigkeitsprüfung, die das Ergebnis der Messung braucht, ist keine. Das Mass
    liest ausschliesslich Soll und Maske — beide liegen in dieser Kette vor dem ersten
    Renderlauf vor. Der Nachweis: Dieselbe Antwort entsteht ohne jede Schätzkarte.
    """
    e = geometrie_qa.himmel_hinter_umriss(_soll(HIMMEL), _maske(), breite=BREITE)

    assert e["methode"] == "himmelanteil_am_aussenrand"
    assert e["n_himmel"] == e["n_aussen"] > 0


def test_zwei_karten_verschiedener_groesse_ergeben_keine_zahl():
    with pytest.raises(QaError, match="verschieden lang"):
        geometrie_qa.himmel_hinter_umriss(_soll(HIMMEL)[:-1], _maske(), breite=BREITE)


def test_die_schwelle_liegt_zwischen_den_beiden_gemessenen_faellen():
    """Die Setzung in ausführbarer Form — und ihre Lücke offen benannt.

    Gemessen sind 63,3 % (trägt) und 0,0 % (trägt nicht). Dazwischen liegt nichts
    Gemessenes; 10 % ist eine Setzung, kein Ablesewert. Wer die Lücke füllt, ändert die
    Zahl — dieser Test hält nur fest, auf welcher Seite die beiden Messungen liegen.
    """
    assert 0.0 < MIN_HIMMELANTEIL < 0.633


# --------------------------------------------------------------------------------------
# 2 · Der Paartest schweigt statt zu bestehen
# --------------------------------------------------------------------------------------

BESTEHT_RHO = {"gerichtet": 0.95}
BESTEHT_KANTE = {"gerichtet": 0.30}
BESTEHT_ANTEIL = {"anteil": 0.90}

TRAEGT = {"anteil": 0.633, "traegt": True}
TRAEGT_NICHT = {"anteil": 0.0, "traegt": False}


def test_der_paartest_schweigt_wo_er_nichts_messen_kann():
    """**Der Kern des Befunds.** Zwei bestehende Zahlen — und trotzdem kein „bestanden".

    Nicht messbar ist nicht dasselbe wie schlecht, aber es ist auch nicht dasselbe wie
    gut. Ein grünes Abzeichen wäre hier in die gefährliche Richtung falsch: Es behauptete
    Existenz und Lage des Bauwerks aufgrund einer Zahl, die in dieser Szene ein perfektes
    Bild nicht von weissem Rauschen trennt.
    """
    stumm = geometrie_qa.paarurteil(BESTEHT_RHO, BESTEHT_KANTE,
                                    anteil_ergebnis=BESTEHT_ANTEIL,
                                    himmel_ergebnis=TRAEGT_NICHT)

    assert stumm["zustaendig"] is False
    assert stumm["bestanden"] is None
    assert stumm["gemessen"] is False
    assert stumm["traeger"] is None


def test_gegenprobe_dieselben_zahlen_bestehen_wo_himmel_dahintersteht():
    """Ohne diese Gegenprobe bewiese der Test darüber nur, dass der Paartest nie besteht."""
    laut = geometrie_qa.paarurteil(BESTEHT_RHO, BESTEHT_KANTE,
                                   anteil_ergebnis=BESTEHT_ANTEIL,
                                   himmel_ergebnis=TRAEGT)

    assert laut["zustaendig"] is True
    assert laut["bestanden"] is True


def test_das_schweigen_ist_etwas_anderes_als_eine_fehlende_messung():
    """Zwei Wege zu ``bestanden is None`` — und sie meinen Verschiedenes.

    *„Niemand hat gemessen"* verlangt einen Lauf. *„Hier ist nichts zu messen"* verlangt
    eine andere Szene oder einen anderen Schätzer. Wer beides gleich meldet, schickt
    jemanden auf die falsche Suche.
    """
    fehlt = geometrie_qa.paarurteil(BESTEHT_RHO, None)
    stumm = geometrie_qa.paarurteil(BESTEHT_RHO, BESTEHT_KANTE,
                                    anteil_ergebnis=BESTEHT_ANTEIL,
                                    himmel_ergebnis=TRAEGT_NICHT)

    assert fehlt["bestanden"] is stumm["bestanden"] is None
    assert fehlt["zustaendig"] is True, "gemessen wurde nicht — messbar wäre es gewesen"
    assert "NICHT GEMESSEN" in fehlt["begruendung"]
    assert "NICHT ZUSTÄNDIG" in stumm["begruendung"]


def test_die_begruendung_reicht_rho_weiter_statt_es_zu_verschweigen():
    """ρ über der Maske ist von der Sache nicht betroffen — nur das zweite Bein.

    Das Urteil fällt trotzdem aus: ρ beantwortet die Richtigkeit und nicht die Existenz,
    und die Existenzfrage bleibt in dieser Szene unbeantwortet.
    """
    stumm = geometrie_qa.paarurteil(BESTEHT_RHO, BESTEHT_KANTE,
                                    anteil_ergebnis=BESTEHT_ANTEIL,
                                    himmel_ergebnis=TRAEGT_NICHT)

    assert stumm["rho"] == pytest.approx(0.95)
    assert "+0.9500" in stumm["begruendung"]
    assert stumm["himmel"] == pytest.approx(0.0)


def test_ohne_himmelspruefung_urteilt_der_paartest_wie_bisher():
    """Die alte Form bleibt erreichbar — als Rückfall, nicht als Empfehlung.

    Sie ist die schwächere: Sie beantwortet die Zuständigkeitsfrage nicht, sondern
    überspringt sie.
    """
    alt = geometrie_qa.paarurteil(BESTEHT_RHO, BESTEHT_KANTE,
                                  anteil_ergebnis=BESTEHT_ANTEIL)

    assert alt["zustaendig"] is True
    assert alt["bestanden"] is True


# --------------------------------------------------------------------------------------
# 3 · Die Naht — dass die Prüfung auf einem echten Weg überhaupt läuft
# --------------------------------------------------------------------------------------
#
# Ein Mass, das nie gerufen wird, ist von einem fehlenden Mass nicht zu unterscheiden.
# Das ist in diesem Projekt dreimal passiert (komposition.py, befund.json, der
# Bauteilwächter), und darum steht hier der Nachweis am selben Tag wie das Mass.

def _attrappe(werte):
    def modell(_parameter: dict):
        return list(werte)
    return modell


@pytest.fixture()
def bild(tmp_path) -> Path:
    pfad = tmp_path / "render_1.png"
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n")
    return pfad


def _urteil(hinter, bild):
    soll = _soll(hinter)
    return ts.qa_gegen_soll(bild, soll, modell=_attrappe(_ist(soll)),
                            breite=BREITE, hoehe=BREITE, maske=_maske())


def test_der_maskenweg_fragt_nach_dem_himmel_bevor_er_urteilt(bild):
    verbaut = _urteil(NACHBAR_M, bild)

    assert verbaut["himmel"]["traegt"] is False
    assert verbaut["paarurteil"]["zustaendig"] is False
    assert verbaut["paarurteil"]["bestanden"] is None


def test_gegenprobe_am_selben_weg_urteilt_die_freistehende_szene_weiterhin(bild):
    """Sonst hiesse der Test darüber nur, dass der Maskenweg gar nichts mehr sagt."""
    frei = _urteil(HIMMEL, bild)

    assert frei["himmel"]["traegt"] is True
    assert frei["paarurteil"]["zustaendig"] is True
    assert frei["paarurteil"]["bestanden"] is not None


def test_ohne_maske_gibt_es_auch_keine_himmelsfrage(bild):
    """``None`` heisst hier nicht gemessen — und nicht in Ordnung."""
    soll = _soll(HIMMEL)
    ohne = ts.qa_gegen_soll(bild, soll, modell=_attrappe(_ist(soll)),
                            breite=BREITE, hoehe=BREITE, maske=None)

    assert ohne["himmel"] is None
    assert ohne["paarurteil"] is None


# --------------------------------------------------------------------------------------
# 4 · Und der Befund sagt es dem Menschen am Terminal
# --------------------------------------------------------------------------------------

def test_der_kurzbefund_nennt_die_kameras_die_nichts_messen_koennen():
    """Ein „nicht zuständig", das niemand sieht, ist ein bestandenes Tor mit Extraschritt.

    Das ist in diesem Projekt der teuerste wiederkehrende Fehler: eine Zahl entsteht, wird
    abgelegt und nie gelesen. Der Kurzbefund ist die einzige Stelle, an der ein Mensch
    hinsieht.
    """
    befund = {"kameras": [
        {"kamera": "s", "paarurteil": {"zustaendig": False}},
        {"kamera": "sSE", "paarurteil": {"zustaendig": True, "bestanden": True}},
    ]}

    zeilen = abholer.befund_kurz(befund)

    treffer = [z for z in zeilen if "NICHT messbar" in z]
    assert len(treffer) == 1, zeilen
    assert "s" in treffer[0]
    assert "sSE" not in treffer[0], "die messende Kamera gehoert nicht in diese Zeile"


def test_gegenprobe_wo_alles_messbar_ist_steht_die_zeile_nicht_da():
    """Eine Zeile, die immer dasteht, liest nach dem dritten Mal niemand mehr."""
    befund = {"kameras": [{"kamera": "s", "paarurteil": {"zustaendig": True}}]}

    assert not [z for z in abholer.befund_kurz(befund) if "NICHT messbar" in z]
