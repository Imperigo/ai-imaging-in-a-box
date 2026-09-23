"""Runde 7: Die Richtungsgrenze gilt in BEIDE Richtungen, und in beiden Wegen gleich.

**Befund vom 23.09.2026.** Runde 6 hat die NEGATIVE Seite der Richtungsmeldung an
:func:`geometrie_qa.richtungsgrenze` gebunden: «vorne und hinten vertauscht» erst unter der
Grenze, dazwischen «kein messbarer Zusammenhang». Die POSITIVE Seite blieb ohne Schwelle.
Score-Weg und Maskenweg meldeten jedes ``rho < 0`` bei Polarität −1 als «den ERWARTETEN
Fall» — auch ``rho = −0,01`` über 849 Punkte, wo die Grenze bei 0,069 liegt: eine Richtung
aus Rauschen. Und bei Polarität +1 mit kleinem positivem ``rho`` schrieb keiner der
Zweige etwas.

Seither gilt EINE Regel, die beide Wege rufen: Betrag unter der Grenze → «Richtung nicht
bestimmbar»; darüber in der erwarteten Richtung → die Bestätigung; darüber in der falschen
→ «vertauscht». Kein Urteil verschiebt sich — es sind nur Hinweise.

Geprüft wird über den Weg, den das Produkt geht: ``tiefenschaetzer.qa_gegen_soll`` (so
ruft ihn ``tools/homeworker.py``) mit einer Tiefenattrappe und einer Maske, sodass Score-Weg
(``geometrie_gate``) und Maskenweg (``rho_ueber_maske``) im selben Lauf antworten. Der Fall
Polarität +1, den der Produktschätzer nicht hat, läuft über dieselben beiden öffentlichen
Funktionen direkt — so rufen sie die Studien und Beweisskripte. Alle Karten sind
synthetisch, ganzzahlig und ohne Zufall hier erzeugt.
"""

from __future__ import annotations

import math

import pytest

from aiimaging import geometrie_qa
from aiimaging import tiefenschaetzer as ts

#: Am Gerät waren es 848 gemeinsame Punkte (auf-20260922-137); hier 849, in einem Bild
#: von 32 × 32 mit 175 Himmelspunkten. Grenze: 2/sqrt(848) = 0,0687.
N_GERAET = 849
BREITE = 32

#: Hintergrundmarke für die direkten Aufrufe — in beiden Karten gleich, damit die
#: Silhouette nicht das ganze Bild ist und keine fremde Warnung mitläuft.
HINTERGRUND = 1.0e10


# --------------------------------------------------------------------------------------
# Karten
# --------------------------------------------------------------------------------------

def _grundordnung(n: int, schritt: int, steigung: float) -> list[float]:
    """``steigung * k`` trägt die Soll-Ordnung, ``(k * schritt) % n`` ist ein Sägezahn
    ohne sie. Mit ``steigung = 0`` bleibt ρ nahe null, je nach ``schritt`` etwas darüber
    oder darunter — ganzzahlig und bei jedem Lauf dieselbe Zahl."""
    return [steigung * k + float((k * schritt) % n) for k in range(n)]


def _produktszene(n: int, schritt: int, steigung: float, vorzeichen: int, breite: int):
    """Soll (Meter, Himmel ``inf``), rohe Ist-Karte und Maske für ``qa_gegen_soll``.

    ``vorzeichen`` +1: Ist ordnet wie die Soll-Ordnung (metrisch), −1: umgekehrt
    (Disparität). Der Himmel der Ist-Karte bekommt einen kleinen endlichen Wert, wie ein
    Disparitätsschätzer ihn schreibt; die Maske liegt genau auf den Geometriepunkten.
    """
    gesamt = breite * breite
    assert n < gesamt
    soll = [10.0 + 10.0 * k / n for k in range(n)] + [math.inf] * (gesamt - n)
    ist = ([10000.0 + vorzeichen * w for w in _grundordnung(n, schritt, steigung)]
           + [0.001] * (gesamt - n))
    maske = [True] * n + [False] * (gesamt - n)
    return soll, ist, maske


@pytest.fixture()
def bild(tmp_path):
    """Ein Bild, das existiert. Der Inhalt liest niemand — die Attrappe schätzt."""
    pfad = tmp_path / "render_1.png"
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n")
    return pfad


def _produktlauf(bild, n=N_GERAET, *, schritt, steigung, vorzeichen, breite=BREITE):
    soll, ist, maske = _produktszene(n, schritt, steigung, vorzeichen, breite)

    def attrappe(_parameter):
        return {"tiefen": list(ist), "breite": breite, "hoehe": breite}

    urteil = ts.qa_gegen_soll(bild, soll, modell=attrappe, breite=breite, hoehe=breite,
                              maske=maske)
    assert urteil["status"] == ts.STATUS_OK, urteil
    assert urteil["polaritaet_zeichen"] == geometrie_qa.POLARITAET_DISPARITAET, \
        "Vorbedingung: der Produktschätzer rechnet mit der gemessenen Polarität −1"
    return urteil


def _direkt(n, *, schritt, steigung, vorzeichen, polaritaet, n_hintergrund=151):
    """Score-Weg und Maskenweg ohne Tiefenschätzer — so rufen Studien und Beweise sie."""
    werte = _grundordnung(n, schritt, steigung)
    soll = [float(k) + 1.0 for k in range(n)] + [HINTERGRUND] * n_hintergrund
    ist = [10000.0 + vorzeichen * w for w in werte] + [HINTERGRUND] * n_hintergrund
    maske = [True] * n + [False] * n_hintergrund
    tor = geometrie_qa.geometrie_gate(soll, ist, hintergrund=HINTERGRUND,
                                      polaritaet=polaritaet)
    weg = geometrie_qa.rho_ueber_maske(soll, ist, maske, polaritaet=polaritaet)
    return tor, weg


# --------------------------------------------------------------------------------------
# Die Sätze erkennen — an ihren festen Wendungen
# --------------------------------------------------------------------------------------

def _unbestimmt(warnungen):
    return [w for w in warnungen if "Richtung ist nicht bestimmbar" in w]


def _bestaetigt(warnungen):
    return [w for w in warnungen if "erwartete Richtung" in w]


def _vertauscht(warnungen):
    # «falsche Richtung» und nicht bloss «vertauscht»: Das Wort steht auch im
    # Polaritätsvorbehalt, der keine Richtung meldet, sondern ihr Fehlen.
    return [w for w in warnungen if "falsche Richtung" in w and "vertauscht" in w]


def _richtungssaetze(warnungen):
    return _unbestimmt(warnungen) + _bestaetigt(warnungen) + _vertauscht(warnungen)


def _fall(warnungen) -> str:
    """Welche der drei Antworten dasteht — und dass es GENAU EINE ist."""
    saetze = _richtungssaetze(warnungen)
    assert len(saetze) == 1, f"genau ein Richtungssatz erwartet, waren {saetze}"
    if _unbestimmt(warnungen):
        return "unbestimmt"
    if _bestaetigt(warnungen):
        return "bestaetigt"
    return "vertauscht"


def _beide(urteil):
    """Die Antwort des Score-Wegs und die des Maskenwegs aus EINEM Produktlauf."""
    return _fall(urteil["warnungen"]), _fall(urteil["rho_maske"]["warnungen"])


# --------------------------------------------------------------------------------------
# 1 · Der Befund: eine Richtung aus Rauschen, auf der angenehmen Seite
# --------------------------------------------------------------------------------------

def test_rho_minus_null_komma_null_eins_ist_keine_bestaetigte_richtung(bild):
    """Der Fall aus dem Befund: ρ ≈ −0,01 über 849 Punkte bei Polarität −1.

    Bis zum 23.09.2026 stand hier in BEIDEN Wegen «das ist hier der ERWARTETE Fall».
    Gewertet sind das +0,01 — ein Siebtel der Grenze 0,069.
    """
    urteil = _produktlauf(bild, schritt=235, steigung=0.0, vorzeichen=-1)

    assert -0.012 < urteil["spearman"] < -0.008, "Vorbedingung: ρ ≈ −0,01"
    assert urteil["rho_maske"]["rho"] == pytest.approx(urteil["spearman"]), \
        "Vorbedingung: beide Wege sehen dieselben Punkte"
    assert _beide(urteil) == ("unbestimmt", "unbestimmt"), (
        urteil["warnungen"], urteil["rho_maske"]["warnungen"])
    assert not _bestaetigt(urteil["warnungen"])
    assert not _bestaetigt(urteil["rho_maske"]["warnungen"])


def test_derselbe_betrag_ist_auf_beiden_seiten_dieselbe_antwort(bild):
    """ρ ≈ ∓0,035 über 849 Punkte: gewertet ±0,035, beides unter der Grenze.

    Runde 6 sagte für −0,035 «nicht bestimmbar» und für +0,035 «der ERWARTETE Fall». Eine
    Grenze, die nur auf einer Seite gilt, ist keine Grenze, sondern eine Vorliebe.
    """
    erwartete_seite = _produktlauf(bild, schritt=49, steigung=0.0, vorzeichen=-1)
    falsche_seite = _produktlauf(bild, schritt=49, steigung=0.0, vorzeichen=+1)

    assert erwartete_seite["spearman"] == pytest.approx(-falsche_seite["spearman"])
    assert 0.03 < abs(erwartete_seite["spearman"]) < 0.04, "Vorbedingung"
    assert _beide(erwartete_seite) == ("unbestimmt", "unbestimmt")
    assert _beide(falsche_seite) == ("unbestimmt", "unbestimmt")


# --------------------------------------------------------------------------------------
# 2 · Über der Grenze: Bestätigung und Umkehrung, in beiden Wegen gleich
# --------------------------------------------------------------------------------------

def test_ueber_der_grenze_in_erwarteter_richtung_steht_die_bestaetigung(bild):
    urteil = _produktlauf(bild, schritt=49, steigung=2.0, vorzeichen=-1)

    assert urteil["spearman"] < -0.85, "Vorbedingung: deutlich, in erwarteter Richtung"
    assert _beide(urteil) == ("bestaetigt", "bestaetigt")
    satz = _bestaetigt(urteil["warnungen"])[0]
    assert "Disparität" in satz, "das negative Vorzeichen bleibt erklärt"
    assert "ERWARTETE" not in satz, "sachlich, ohne Grossbuchstaben"


def test_ueber_der_grenze_in_falscher_richtung_bleibt_vertauscht(bild):
    urteil = _produktlauf(bild, schritt=49, steigung=2.0, vorzeichen=+1)

    assert urteil["spearman"] > 0.85, "Vorbedingung: deutlich, in falscher Richtung"
    assert _beide(urteil) == ("vertauscht", "vertauscht")


@pytest.mark.parametrize("vorzeichen, erwartet", [(-1, "bestaetigt"), (+1, "vertauscht")])
def test_dieselbe_zahl_traegt_bei_vielen_punkten_eine_richtung_und_bei_wenigen_nicht(
        bild, vorzeichen, erwartet):
    """|ρ| ≈ 0,11: über 849 Punkte deutlich (Grenze 0,069), über 101 Punkte nicht
    (Grenze 0,200) — und das auf BEIDEN Seiten. Runde 6 prüfte nur die negative."""
    viele = _produktlauf(bild, schritt=106, steigung=0.0, vorzeichen=-vorzeichen)
    wenige = _produktlauf(bild, 101, schritt=20, steigung=0.0, vorzeichen=-vorzeichen,
                          breite=12)

    for u in (viele, wenige):
        gerichtet = geometrie_qa.POLARITAET_DISPARITAET * u["spearman"]
        assert 0.09 < abs(gerichtet) < 0.13, f"Vorbedingung: {u['spearman']}"
        assert (gerichtet > 0) == (erwartet == "bestaetigt"), "Vorbedingung: Seite"
    assert _beide(viele) == (erwartet, erwartet)
    assert _beide(wenige) == ("unbestimmt", "unbestimmt")


# --------------------------------------------------------------------------------------
# 3 · Polarität +1: bisher schwieg dort die positive Seite ganz
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("schritt, steigung, erwartet", [
    (49, 0.0, "unbestimmt"),      # ρ ≈ +0,035: vorher kein Satz
    (49, 2.0, "bestaetigt"),      # ρ ≈ +0,90: vorher kein Satz
])
def test_bei_polaritaet_plus_eins_antworten_beide_wege(schritt, steigung, erwartet):
    tor, weg = _direkt(N_GERAET, schritt=schritt, steigung=steigung, vorzeichen=+1,
                       polaritaet=geometrie_qa.POLARITAET_TIEFE)

    assert tor["spearman"] > 0.0 and weg["rho"] > 0.0, "Vorbedingung: positive Seite"
    assert _fall(tor["warnungen"]) == erwartet, tor["warnungen"]
    assert _fall(weg["warnungen"]) == erwartet, weg["warnungen"]
    if erwartet == "bestaetigt":
        assert "Disparität" not in _bestaetigt(tor["warnungen"])[0], \
            "bei positivem ρ gibt es kein Vorzeichen zu erklären"


def test_ohne_polaritaet_gibt_es_keinen_richtungssatz():
    """Keine Polarität, keine Richtung — dafür steht der ausführliche Vorbehalt da. Das
    ist die dritte Antwort und bleibt es; die Regel greift nur bei gemessener Polarität."""
    tor, weg = _direkt(N_GERAET, schritt=49, steigung=2.0, vorzeichen=+1, polaritaet=None)

    assert not _richtungssaetze(tor["warnungen"]), tor["warnungen"]
    assert not _richtungssaetze(weg["warnungen"]), weg["warnungen"]
    assert any("KEINE POLARITÄT" in w for w in tor["warnungen"])


# --------------------------------------------------------------------------------------
# 4 · Eine Regel: beide Wege antworten über eine ganze Reihe von ρ gleich
# --------------------------------------------------------------------------------------

#: (schritt, steigung, vorzeichen) — vom Rauschen bis zur vollen Ordnung, beide Seiten.
REIHE = [(235, 0.0, -1), (235, 0.0, +1), (49, 0.0, -1), (49, 0.0, +1),
         (106, 0.0, -1), (106, 0.0, +1), (49, 0.15, -1), (49, 0.15, +1),
         (49, 2.0, -1), (49, 2.0, +1)]


@pytest.mark.parametrize("schritt, steigung, vorzeichen", REIHE)
def test_score_weg_und_maskenweg_folgen_derselben_regel(bild, schritt, steigung,
                                                         vorzeichen):
    """Dieselben Punkte, dasselbe ρ — dieselbe Antwort, und sie folgt aus der Grenze."""
    urteil = _produktlauf(bild, schritt=schritt, steigung=steigung, vorzeichen=vorzeichen)
    gerichtet = urteil["polaritaet_zeichen"] * urteil["spearman"]
    grenze = geometrie_qa.richtungsgrenze(urteil["n_gemeinsam"])
    soll_fall = ("vertauscht" if gerichtet <= -grenze
                 else "bestaetigt" if gerichtet >= grenze else "unbestimmt")

    assert _beide(urteil) == (soll_fall, soll_fall), (gerichtet, grenze)


def test_die_reihe_deckt_alle_drei_antworten_ab(bild):
    """Gegenprobe zur Reihe darüber: Ohne alle drei Fälle wäre «dieselbe Regel» vakuös."""
    faelle = {_beide(_produktlauf(bild, schritt=s, steigung=m, vorzeichen=v))[0]
              for s, m, v in REIHE}
    assert faelle == {"unbestimmt", "bestaetigt", "vertauscht"}


# --------------------------------------------------------------------------------------
# 5 · Kein Urteil verschiebt sich — es sind nur Hinweise
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("schritt, steigung, vorzeichen", REIHE)
def test_score_urteil_und_gerichteter_wert_folgen_allein_der_rechnung(
        bild, schritt, steigung, vorzeichen):
    """Score, Bestehen und ``gerichtet`` hängen an ρ und geom_iou, nicht am Hinweis.

    Die Rechnung steht hier ausgeschrieben, wie sie vor und nach dem 23.09.2026 lautet:
    ``sqrt(max(0, polaritaet * spearman) * geom_iou)``. Die Probe vorher/nachher (alte
    gegen neue Fassung des Moduls, dieselbe Reihe) ergab dieselben Zahlen auf die Stelle.
    """
    urteil = _produktlauf(bild, schritt=schritt, steigung=steigung, vorzeichen=vorzeichen)
    p = urteil["polaritaet_zeichen"]
    erwartet = math.sqrt(max(0.0, p * urteil["spearman"]) * urteil["geom_iou"])

    assert urteil["score"] == pytest.approx(erwartet, abs=1e-12)
    assert urteil["bestanden"] is (urteil["score"] >= urteil["schwelle"])
    assert urteil["rho_maske"]["gerichtet"] == pytest.approx(p * urteil["rho_maske"]["rho"])


def test_die_begruendung_ohne_score_nennt_den_grund_und_nicht_die_richtung(bild):
    """Zu kleine gemeinsame Silhouette (20 Punkte): kein Score, und die Begründung sagt,
    warum — nicht, in welche Richtung die 20 Punkte zeigen.

    ``geometrie_gate`` nahm dafür die LETZTE Warnung, und die Richtung steht hinter der
    Punktzählung. Seit dem 23.09.2026 schreibt jede gemessene Polarität einen
    Richtungssatz; ohne Filter hätte er bei Polarität +1 den Grund neu verdrängt (bei −1
    tat er es schon vorher, mit «ERWARTETE Fall»).
    """
    produkt = _produktlauf(bild, 20, schritt=1, steigung=1.0, vorzeichen=-1, breite=5)
    # Fünf Hintergrundpunkte: 80 % Geometrie, damit «Geringer Geometrieanteil» nicht
    # selbst als letzte Warnung dasteht und der Test nichts mehr prüfte.
    tor_plus, _ = _direkt(20, schritt=1, steigung=1.0, vorzeichen=+1, n_hintergrund=5,
                          polaritaet=geometrie_qa.POLARITAET_TIEFE)

    for urteil in (produkt, tor_plus):
        assert urteil["n_gemeinsam"] == 20, "Vorbedingung"
        assert urteil["score"] is None and urteil["bestanden"] is False
        assert _richtungssaetze(urteil["warnungen"]), "der Hinweis steht weiter da"
        assert "Gemeinsame Silhouette zu klein" in urteil["begruendung"], \
            urteil["begruendung"]
        assert not _richtungssaetze([urteil["begruendung"]]), urteil["begruendung"]
