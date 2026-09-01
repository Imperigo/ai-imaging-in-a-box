"""Drei Standpunkte auf Augenhöhe — und woran die Wahl einen guten erkennt.

``kamerasatz`` konnte seit jeher zwölf Richtungen rechnen und über ``kuerzel`` eine
Auswahl entgegennehmen. Es fehlte die **Wahl**: Wer nichts angibt, bekommt zwölf; wer
etwas angibt, hat selbst entschieden. Auf der Nachbarseite (``kamera.ts`` in KosmoOrbit)
stehen zwei bis drei Standpunkte fest im Quelltext, ohne eine Zahl, die sie begründet.

Diese Datei prüft nicht, ob die Auswahl *gefällt* — sondern ob die Grössen, auf denen sie
steht, überhaupt unterscheiden können. **Ein Kriterium, das auf allen Kandidaten denselben
Wert hat, wählt nichts aus; es sortiert die Liste.**
"""
from __future__ import annotations

import itertools

import pytest

from aiimaging import kameras

#: Drei Bauformen, an denen die Auswahl verschieden ausgehen muss.
#:
#: Der erste Fall ist der **gemessene Hochbau der Bestandsdatei vom 28.08.2026**, auf
#: Nullpunkt geschoben — die Masse sind Geometrie und keine Projektdaten (Regel 3).
BAUFORMEN = {
    "gedrungen": [[0.0, 0.0, 0.0], [94.5, 82.75, 25.6]],
    "riegel": [[0.0, 0.0, 0.0], [60.0, 12.0, 15.0]],
    "kubus": [[0.0, 0.0, 0.0], [20.0, 20.0, 20.0]],
}


# --------------------------------------------------------------------------------------
# 1 · Warum der Füllgrad NICHT das Kriterium sein kann
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(BAUFORMEN))
def test_der_fuellgrad_kann_die_zwoelf_richtungen_nicht_unterscheiden(name):
    """Die naheliegendste Kennzahl ist die unbrauchbarste — und das ist messbar.

    ``fuellgrad`` ist die **Vorgabe**, die ``kamerasatz`` einhält, nicht ein Ergebnis der
    Richtung. Über alle zwölf Richtungen und alle drei Bauformen liegt er zwischen 0,697
    und 0,700. Wer danach auswählt, wählt in Wahrheit die Reihenfolge der Liste.

    Diese Probe steht **vor** allen anderen, weil sie das Kriterium begründet: Ohne sie
    wäre ``zweite_fassade`` eine Erfindung statt eine Notwendigkeit.
    """
    satz = kameras.kamerasatz(BAUFORMEN[name], gelaende_z=0.0)
    werte = [k["fuellgrad"] for k in satz["kameras"]]
    spanne = max(werte) - min(werte)
    assert spanne < 0.01, (spanne, werte)


@pytest.mark.parametrize("name", ["gedrungen", "riegel"])
def test_der_flaechenanteil_unterscheidet_sehr_wohl(name):
    """Die Gegenprobe. Ohne sie wäre oben nur belegt, dass irgendetwas gleich ist.

    Am gedrungenen Bau schwankt der Flächenanteil über die zwölf Richtungen um den
    Faktor 2,3, am Riegel um 1,9 — er *kann* also unterscheiden, und darum steht er in
    ``guete_standpunkt``.
    """
    satz = kameras.kamerasatz(BAUFORMEN[name], gelaende_z=0.0)
    werte = [k["flaechenanteil"] for k in satz["kameras"]]
    assert max(werte) / min(werte) > 1.5, werte


# --------------------------------------------------------------------------------------
# 2 · Die zweite Fassade — und warum sie ein Ausschluss ist, kein Abzug
# --------------------------------------------------------------------------------------

def test_die_frontalen_zeigen_genau_eine_fassade():
    """``zweite_fassade`` ist bei den vier Frontalen null und bei den acht Diagonalen nicht.

    Damit trennt die Schwelle nicht nach Geschmack, sondern nach der Frage, ob ein Körper
    im Bild steht oder ein Aufriss.
    """
    masse = (94.5, 82.75, 25.6)
    azimute = kameras.richtungen()
    for kuerzel, azimut in azimute.items():
        anteil = kameras.zweite_fassade(masse, azimut)
        if kameras.RICHTUNGEN[kuerzel][1] == 0:                  # frontal
            assert anteil == 0.0, (kuerzel, azimut, anteil)
        else:
            assert anteil > 0.05, (kuerzel, azimut, anteil)


def test_auch_ost_sued_und_west_zaehlen_als_frontal():
    """**Der Fehler, der hier zuerst stand, und er sah aus wie keiner.**

    Gefragt wird „gibt es eine zweite Fassade?" mit ``> 0``. Aber ``cos(90°)`` ist in
    Fliesskomma **6,1e-17** und nicht null: Nur bei Nord (dort ist ``sin(0)`` exakt null)
    kam eine glatte Null heraus, bei Ost, Süd und West ein Anteil um 1e-18. Gemessen fiel
    darum **eine** der vier Frontalen aus der Auswahl und drei liefen weiter. Der Filter
    sah richtig aus und war zu drei Vierteln unwirksam.

    Diese Probe hält die Ecke fest, an der es passiert ist — nicht nur die eine Richtung,
    bei der es zufällig funktionierte.
    """
    masse = (94.5, 82.75, 25.6)
    for azimut in (0.0, 90.0, 180.0, 270.0):
        assert kameras.zweite_fassade(masse, azimut) == 0.0, azimut


@pytest.mark.parametrize("name", sorted(BAUFORMEN))
def test_keine_frontale_wird_vorgeschlagen(name):
    """Sie füllen gemessen MEHR Bild als jede Diagonale — und sind trotzdem der falsche Bildtyp.

    Das ist die Stelle, an der die beiden messbaren Kriterien gegeneinanderziehen und
    entschieden werden muss: Der Deckungsgrad stellt die schmale Silhouette der Frontalen
    näher heran, also gewinnen sie nach Fläche. Wer nur danach auswählt, bekommt vier
    Aufrissaufnahmen von einem Bau — und ``kamerasatz`` selbst nennt die mittige Frontale
    „bildlich tot".
    """
    aus = kameras.standpunkte(BAUFORMEN[name], gelaende_z=0.0)
    gewaehlt = {s["kuerzel"] for s in aus["standpunkte"]}
    frontale = {k for k, (_, faktor) in kameras.RICHTUNGEN.items() if faktor == 0}
    assert not (gewaehlt & frontale), gewaehlt
    assert frontale <= {k for k, _ in aus["verworfen"]}, aus["verworfen"]


def test_ein_untauglicher_standpunkt_ist_ausgeschlossen_und_nicht_nur_schlechter():
    """Produkt statt Summe: Eine Null bleibt eine Null.

    Bei einer Summe liesse sich die fehlende zweite Fassade mit doppeltem Flächenanteil
    erkaufen — und genau das ist der Fall, der gemessen eintritt.
    """
    satz = kameras.kamerasatz(BAUFORMEN["gedrungen"], gelaende_z=0.0)
    bester = max(k["flaechenanteil"] for k in satz["kameras"])
    frontal = next(k for k in satz["kameras"] if k["kuerzel"] == "e")
    diagonal = next(k for k in satz["kameras"] if k["kuerzel"] == "nNE")

    g_frontal = kameras.guete_standpunkt(frontal, satz["masse_m"], bester_flaechenanteil=bester)
    g_diagonal = kameras.guete_standpunkt(diagonal, satz["masse_m"], bester_flaechenanteil=bester)

    assert frontal["flaechenanteil"] > diagonal["flaechenanteil"], "Voraussetzung der Probe"
    assert g_frontal["taugt"] is False
    assert g_frontal["guete"] == 0.0
    assert g_diagonal["guete"] > 0.0


# --------------------------------------------------------------------------------------
# 3 · Drei Standpunkte sind nicht ein Standpunkt, dreimal
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(BAUFORMEN))
def test_die_drei_stehen_auseinander(name):
    """Zwei Kameras nebeneinander sind ein Standpunkt.

    Gemessen am **kleinsten** paarweisen Winkelabstand und nicht am mittleren: Ein
    Mittelwert verrechnete zwei dicht beieinander stehende Kameras mit einer weit
    entfernten dritten und sähe gesund aus.
    """
    aus = kameras.standpunkte(BAUFORMEN[name], gelaende_z=0.0)
    azimute = [s["azimut_grad"] for s in aus["standpunkte"]]
    assert len(azimute) == 3, azimute
    eng = min(kameras._winkelabstand(a, b) for a, b in itertools.combinations(azimute, 2))
    assert eng >= 70.0, (eng, azimute)
    assert aus["streuung_grad"] == pytest.approx(eng)


def test_die_streuung_aendert_die_wahl_wirklich():
    """Ohne den Streuungsfaktor faellt die Auswahl anders aus — sonst waere er Zierat.

    **Ein Faktor, der nichts aendert, ist nicht bewiesen, sondern unbemerkt.** Am
    gedrungenen Bau liegen die vier besten Einzelwerte auf ``nNE``, ``sSE``, ``sSW``,
    ``nNW`` und sind praktisch gleich; die drei besten davon stehen enger als die drei,
    die die Rechnung mit Streuung waehlt.
    """
    bbox = BAUFORMEN["gedrungen"]
    satz = kameras.kamerasatz(bbox, gelaende_z=0.0)
    bester = max(k["flaechenanteil"] for k in satz["kameras"])
    bewertet = [(k, kameras.guete_standpunkt(k, satz["masse_m"], bester_flaechenanteil=bester))
                for k in satz["kameras"]]
    tauglich = [(k, g) for k, g in bewertet if g["taugt"]]

    # Die naive Wahl: die drei besten Einzelwerte, Gleichstand nach RICHTUNGSFOLGE.
    naiv = sorted(tauglich, key=lambda p: -p[1]["guete"])[:3]
    eng_naiv = min(kameras._winkelabstand(a[0]["azimut_grad"], b[0]["azimut_grad"])
                   for a, b in itertools.combinations(naiv, 2))

    mit_streuung = kameras.standpunkte(bbox, gelaende_z=0.0)
    assert mit_streuung["streuung_grad"] > eng_naiv, (mit_streuung["streuung_grad"], eng_naiv)


def test_bei_zu_wenigen_tauglichen_kommen_weniger_zurueck_statt_fuellwerte():
    """Eine kürzere Liste ist ein Befund. Drei Plätze mit schlechten Blicken zu füllen wäre keiner."""
    aus = kameras.standpunkte(BAUFORMEN["kubus"], anzahl=20, gelaende_z=0.0)
    assert len(aus["standpunkte"]) == 8, [s["kuerzel"] for s in aus["standpunkte"]]
    assert any("bestehen die Pruefungen" in w for w in aus["warnungen"]), aus["warnungen"]


def test_kuerzel_ist_hier_nicht_zulaessig():
    """Wer die Auswahl mitgibt, will die andere Funktion."""
    with pytest.raises(ValueError, match="kuerzel"):
        kameras.standpunkte(BAUFORMEN["kubus"], kuerzel=("n", "e"))


# --------------------------------------------------------------------------------------
# 4 · Die Rahmungsfrage reist mit
# --------------------------------------------------------------------------------------

def test_ohne_bauwerksbox_sagt_die_auswahl_dass_sie_es_nicht_weiss():
    """Die dritte Antwort. „Die Rahmung sitzt" und „ich kann es nicht sagen" sind zwei Dinge."""
    aus = kameras.standpunkte(BAUFORMEN["gedrungen"], gelaende_z=0.0)
    assert aus["rahmung"]["traegt"] is None
    assert any("NICHT FESTSTELLBAR" in w for w in aus["warnungen"]), aus["warnungen"]


def test_mit_bauwerksbox_auf_grosser_platte_wird_der_abbruch_gemeldet():
    """Der Fall, für den ``rahmungsverhaeltnis`` gebaut ist — jetzt schon bei der Wahl.

    Die beste von zwölf Richtungen ist immer noch zu weit weg, wenn nach der ganzen
    Geländeplatte gerahmt wird. Die Auswahl wird trotzdem getroffen; das Urteil steht
    **daneben** und nicht an ihrer Stelle.
    """
    szene = [[0.0, 0.0, 0.0], [200.0, 200.0, 25.6]]
    bauwerk = [[0.0, 0.0, 0.0], [20.0, 20.0, 25.6]]
    aus = kameras.standpunkte(szene, bauwerk_bbox=bauwerk, gelaende_z=0.0)
    assert aus["rahmung"]["abbruch"] is True
    assert "NICHT RENDERN" in aus["warnungen"][0], aus["warnungen"]
    assert len(aus["standpunkte"]) == 3, "die Wahl wird trotzdem getroffen"


# --------------------------------------------------------------------------------------
# 5 · Die Auswahl ist wiederholbar
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(BAUFORMEN))
def test_dieselbe_eingabe_liefert_dieselbe_wahl(name):
    """Bei Gleichstand entscheidet RICHTUNGSFOLGE und nicht die Laune der Sortierung.

    Am gedrungenen Bau sind vier Kandidaten bis auf vier Nachkommastellen gleich gut; ohne
    eine feste Reihenfolge waere der Vorschlag von Lauf zu Lauf ein anderer — und ein
    Vorschlag, der sich ohne Grund aendert, ist keine Begruendung wert.
    """
    erste = [s["kuerzel"] for s in kameras.standpunkte(BAUFORMEN[name], gelaende_z=0.0)["standpunkte"]]
    for _ in range(3):
        assert [s["kuerzel"] for s in
                kameras.standpunkte(BAUFORMEN[name], gelaende_z=0.0)["standpunkte"]] == erste
