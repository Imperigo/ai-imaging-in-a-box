"""Das fotografische Regelwissen — geprüft an nachrechenbaren Fällen und an der Recherche.

Warum diese Tests so aussehen
-----------------------------
Dieses Projekt hat kürzlich einen grünen Test gefunden, der die Umkehrfunktion seiner
eigenen Definition prüfte und gar nicht rot werden konnte. Die Frage bei jeder Zusicherung
hier lautet deshalb: **Könnte sie die Behauptung im Namen überhaupt falsifizieren?**

Daraus drei Regeln für diese Datei:

1. **Erwartungswerte stehen als Zahl da**, nicht als zweiter Aufruf derselben Rechnung.
   Wo die Recherche eine Tabelle liefert (Mindestabstände, Horizontlage, Bildanteile),
   steht ihre Zahl im Test — dann prüft der Test die Bibliothek gegen die Quelle und
   nicht gegen sich selbst.
2. **Unabhängigkeitsaussagen werden mit mehreren Werten geprüft**, nie mit einem. Ein
   einzelner Wert kann Unabhängigkeit nicht zeigen. Und zu jeder Unabhängigkeit gehört
   die Gegenprobe: Was die Grösse *doch* verändert, muss sie auch messbar verändern —
   sonst besteht eine Funktion, die schlicht immer dasselbe zurückgibt.
3. **Keine Zusicherung über eine womöglich leere Sammlung.** Jede Schleife über eine
   Registratur prüft zuerst, dass sie nicht leer ist.
"""
from __future__ import annotations

import pytest

from aiimaging import kameras, komposition


# ======================================================================================
# Die Dreiteilung belegt / gesetzt / ungemessen
# ======================================================================================

def test_jede_belegte_zahl_gibt_es_als_konstante_und_traegt_denselben_wert():
    """Die Registratur darf nicht neben dem Code herlaufen.

    Ein Eintrag in ``BELEGT``, zu dem es keine Konstante gibt, ist eine Behauptung über
    Code, den es nicht gibt. Eine Konstante, die einen anderen Wert trägt als ihre
    Registratur, ist schlimmer — dann steht die Quelle bei der falschen Zahl.
    """
    assert komposition.BELEGT, "BELEGT ist leer — dann prüft diese Schleife nichts"
    for name, eintrag in komposition.BELEGT.items():
        assert hasattr(komposition, name), f"BELEGT nennt {name}, das Modul kennt es nicht"
        assert getattr(komposition, name) == eintrag["wert"]


def test_jede_setzung_gibt_es_als_konstante_und_traegt_denselben_wert():
    assert komposition.SETZUNGEN, "SETZUNGEN ist leer"
    for name, eintrag in komposition.SETZUNGEN.items():
        assert hasattr(komposition, name), f"SETZUNGEN nennt {name}, das Modul kennt es nicht"
        assert getattr(komposition, name) == eintrag["wert"]


def test_die_drei_ablagen_ueberschneiden_sich_nicht():
    """Ein Name darf nicht zugleich belegt und gesetzt sein — sonst ist die Stufe beliebig."""
    belegt = set(komposition.BELEGT)
    gesetzt = set(komposition.SETZUNGEN)
    ungemessen = set(komposition.UNGEMESSEN)
    assert belegt and gesetzt and ungemessen
    assert not belegt & gesetzt
    assert not belegt & ungemessen
    assert not gesetzt & ungemessen


def test_belegte_werte_stammen_nie_aus_ratgeberliteratur():
    """Die schärfste Trennlinie dieses Moduls, und sie muss maschinell gehalten werden.

    Ratgeberquellen sind zahlenmässig in der Überzahl und schreiben voneinander ab. Wer
    eine ihrer Zahlen nach ``BELEGT`` schiebt, macht aus Folklore einen Beleg.
    """
    assert komposition.BELEGT
    assert "ratgeber" not in komposition.BELEG_ARTEN
    for name, eintrag in komposition.BELEGT.items():
        assert eintrag["art"] in komposition.BELEG_ARTEN, name
        assert eintrag["quelle"].strip(), f"{name} nennt keine Quelle"


def test_jede_setzung_nennt_wer_sie_gesetzt_hat_und_wann_und_keine_quelle():
    """Der Test, den der Auftrag verlangt: Setzungen sind als Setzungen gekennzeichnet."""
    assert komposition.SETZUNGEN
    for name, eintrag in komposition.SETZUNGEN.items():
        assert komposition.belegstufe(name) == "gesetzt"
        assert isinstance(eintrag["gesetzt_von"], str) and eintrag["gesetzt_von"].strip()
        assert re_iso_datum(eintrag["gesetzt_am"]), f"{name}: {eintrag['gesetzt_am']!r}"
        assert eintrag["stand"] in ("entschieden", "vorgeschlagen")
        assert "quelle" not in eintrag, (
            f"{name} trägt eine Quelle — eine Setzung hat keine, sonst wäre sie ein Fund"
        )
        assert eintrag["recherche"].strip(), f"{name} sagt nicht, was die Recherche fand"


def re_iso_datum(text) -> bool:
    """``JJJJ-MM-TT``? Absichtlich hier und nicht als Regexmodul-Import: ein Datum ist
    das einzige Format, das dieser Test prüfen muss."""
    if not isinstance(text, str) or len(text) != 10:
        return False
    teile = text.split("-")
    if len(teile) != 3:
        return False
    return all(t.isdigit() for t in teile) and len(teile[0]) == 4


def test_die_stuetzenregel_ist_eine_setzung_und_kein_fund():
    """Der Beispielfall des Owners. Zur Stütze findet die Recherche keine Positionsaussage."""
    eintrag = komposition.herkunft("SETZUNG_STUETZE_BILDANTEIL")
    assert eintrag["belegstufe"] == "gesetzt"
    assert eintrag["stand"] == "vorgeschlagen"
    assert "NICHTS GEFUNDEN" in eintrag["recherche"]
    assert eintrag["wert"] == pytest.approx(2.0 / 3.0)


def test_ungemessene_fragen_tragen_keinen_wert():
    """``wert is None`` ist hier die Aussage, nicht eine fehlende Angabe."""
    assert komposition.UNGEMESSEN
    for name, eintrag in komposition.UNGEMESSEN.items():
        assert eintrag["wert"] is None, (
            f"{name} trägt einen Wert und ist damit nicht ungemessen")
        assert eintrag["frage"].strip()
        assert eintrag["befund"].strip()


def test_der_ueber_eck_winkel_von_45_grad_gilt_als_ungemessen():
    """45° stehen in jedem Ratgeber und in keiner Norm — HABS verlangt die Ansicht,
    nennt aber keinen Winkel. Die Zahl steht darum als Zitat da, nicht als Wert."""
    assert komposition.belegstufe("ueber_eck_winkel") == "ungemessen"
    assert komposition.UNGEMESSEN["ueber_eck_winkel"]["wert"] is None
    assert komposition.UEBER_ECK_WINKEL_BEHAUPTET_GRAD == 45.0


def test_belegstufe_weist_einen_unbekannten_namen_ab():
    with pytest.raises(komposition.KompositionError, match="Unbekannter Name"):
        komposition.belegstufe("AUGENHOEHE_DES_FOTOGRAFEN")


def test_herkunft_gibt_eine_kopie_und_nicht_die_registratur():
    eintrag = komposition.herkunft("SHIFT_HOECHSTWERT_MM")
    eintrag["wert"] = 999.0
    assert komposition.BELEGT["SHIFT_HOECHSTWERT_MM"]["wert"] == 11.0


def test_kompositionsfehler_ist_ein_valueerror():
    """Damit bestehendes ``except ValueError`` weiter greift — wie bei QaError."""
    assert issubclass(komposition.KompositionError, ValueError)


# ======================================================================================
# Neigung: der Befund über kameras.py
# ======================================================================================

@pytest.mark.parametrize("gebaeudehoehe", [6.0, 8.0, 15.0, 40.0])
def test_zielanhebung_um_ein_fuenftel_kippt_immer_um_dieselben_9_46_grad(
        gebaeudehoehe):
    """Der Befund, um den herum das Modul gebaut ist.

    ``kameras.ZIEL_ANTEIL_HOEHE = 0.20`` hebt das Blickziel um ein Fünftel der
    Gebäudehöhe über die Augenhöhe. Bei einem Abstand von 1,2 × Gebäudehöhe kürzt sich
    das Gebäudemass heraus: ``atan(0.20/1.2)`` = 9,4623°, für den Schuppen wie für das
    Hochhaus. Genau das prüft dieser Test über eine Spanne von 6 bis 40 m.
    """
    neigung = komposition.neigung_grad(hoehendifferenz_m=0.20 * gebaeudehoehe,
                                       abstand_m=1.2 * gebaeudehoehe)
    assert neigung == pytest.approx(9.4623, abs=1e-4)


def test_die_neigung_ist_bei_gleicher_hoehe_exakt_null():
    """Nicht „ungefähr null". Die Regel des Fachs bindet die Neigung auf exakt 0°."""
    assert komposition.neigung_grad(hoehendifferenz_m=0.0, abstand_m=25.0) == 0.0


def test_ein_ziel_unter_der_kamera_kippt_nach_unten():
    assert komposition.neigung_grad(hoehendifferenz_m=-2.0, abstand_m=10.0) < 0.0


def test_neigung_weist_abstand_null_ab():
    with pytest.raises(komposition.KompositionError, match="abstand_m"):
        komposition.neigung_grad(hoehendifferenz_m=1.0, abstand_m=0.0)


# ======================================================================================
# Konvergenz
# ======================================================================================

@pytest.mark.parametrize("gebaeudehoehe,kamerahoehe,abstand", [
    (6.0, 1.70, 7.2),
    (15.0, 1.60, 30.0),
    (40.0, 1.70, 48.0),
    (3.0, 0.0, 5.0),
])
def test_die_waagrechte_kamera_hat_exakt_keine_konvergenz(gebaeudehoehe, kamerahoehe,
                                                          abstand):
    """Die Regel des Fachs, in eine Zahl gefasst — und sie ist exakt 0, nicht fast 0.

    Vier verschiedene Aufbauten, damit die Null nicht zufällig aus einem einzelnen
    Zahlenpaar fällt.
    """
    assert komposition.konvergenz(neigung_grad=0.0, gebaeudehoehe_m=gebaeudehoehe,
                                  kamerahoehe_m=kamerahoehe, abstand_m=abstand) == 0.0


def test_der_griff_aus_kameras_py_laesst_die_vertikalen_um_gut_zwoelf_prozent_zusammenlaufen():
    """Der Zahlenwert zum Befund, mit ausgeschriebenem Aufbau.

    6-m-Bau, Kamera auf 1,70 m, Abstand 1,2 × Höhe = 7,2 m, Neigung 9,4623°. Die Fassade
    erscheint an der Oberkante 12,63 % schmaler als am Fuss.
    """
    konv = komposition.konvergenz(neigung_grad=9.4623220820, gebaeudehoehe_m=6.0,
                                  kamerahoehe_m=1.70, abstand_m=7.2)
    assert konv == pytest.approx(0.1263, abs=1e-4)


def test_bei_mitwachsendem_abstand_bleibt_die_konvergenz_nahezu_gleich():
    """Widerspruch zur Auftragsannahme „12 bis 22 %", und er ist nachrechenbar.

    Wächst der Abstand mit der Gebäudehöhe mit, bleibt der Winkel, unter dem das Bauwerk
    erscheint, konstant — und damit auch die Konvergenz. Sie fällt sogar leicht, statt
    zu steigen. Der Test hält die Richtung fest, nicht nur die Grössenordnung: Wäre die
    Konvergenz von 6 auf 40 m wachsend, fiele er um.
    """
    werte = [
        komposition.konvergenz(neigung_grad=9.4623220820, gebaeudehoehe_m=H,
                               kamerahoehe_m=1.70, abstand_m=1.2 * H)
        for H in (6.0, 8.0, 15.0, 40.0)
    ]
    assert werte == sorted(werte, reverse=True)
    assert max(werte) - min(werte) < 0.005
    assert all(0.12 < w < 0.13 for w in werte)


def test_mehr_neigung_heisst_mehr_konvergenz():
    werte = [komposition.konvergenz(neigung_grad=g, gebaeudehoehe_m=15.0,
                                    kamerahoehe_m=1.70, abstand_m=20.0)
             for g in (0.0, 5.0, 10.0, 20.0)]
    assert werte == sorted(werte)
    assert werte[0] == 0.0
    assert werte[-1] > werte[0]


def test_nach_unten_geneigt_laufen_die_vertikalen_auseinander():
    """Derselbe Fehler mit anderem Vorzeichen — der 11°-Griff der ML-Datensätze."""
    assert komposition.konvergenz(neigung_grad=-11.0, gebaeudehoehe_m=15.0,
                                  kamerahoehe_m=1.70, abstand_m=20.0) < 0.0


def test_konvergenz_verweigert_die_auskunft_wenn_der_fuss_hinter_der_kamera_liegt():
    """Bei extremer Neigung wandert der Gebäudefuss hinter die Kameraebene. Dort gibt es
    kein Breitenverhältnis mehr — und eine Zahl wäre eine Lüge."""
    with pytest.raises(komposition.KompositionError, match="nicht definiert"):
        komposition.konvergenz(neigung_grad=85.0, gebaeudehoehe_m=15.0,
                               kamerahoehe_m=1.70, abstand_m=1.0)


# ======================================================================================
# Horizont und Bodenanteil
# ======================================================================================

@pytest.mark.parametrize("sensor", [komposition.SENSOR_HOEHE_QUER_MM,
                                    komposition.SENSOR_HOEHE_HOCH_MM,
                                    30.0])
def test_ohne_shift_liegt_der_horizont_exakt_in_der_bildmitte(sensor):
    """Keine Wahl, sondern die Folge der waagrechten Kamera — für jedes Format."""
    assert komposition.horizontanteil(shift_mm=0.0, sensor_hoehe_mm=sensor) == 0.5


@pytest.mark.parametrize("shift,sensor,erwartet", [
    (0.0, 24.0, 0.500),
    (6.0, 24.0, 0.250),
    (12.0, 24.0, 0.000),
    (0.0, 36.0, 0.500),
    (6.0, 36.0, 1 / 3),
    (12.0, 36.0, 1 / 6),
    (11.0, 24.0, 1 / 24),
])
def test_horizontanteil_trifft_die_recherchetabelle(shift, sensor, erwartet):
    """KOMPOSITION_AUSSEN.md 4.4a, Zeile für Zeile."""
    assert komposition.horizontanteil(shift_mm=shift,
                                      sensor_hoehe_mm=sensor) == pytest.approx(erwartet)


def test_aussen_haengt_der_bodenanteil_nicht_an_hoehe_abstand_und_brennweite():
    """Die Aussage der Funktion ist, dass drei ihrer Argumente nicht eingehen.

    Gegenprobe im selben Test: Der Shift, der als einziger eingeht, muss den Wert auch
    wirklich verändern — sonst bestünde eine Funktion, die schlicht immer 0,5 liefert.
    """
    werte = [
        komposition.bodenanteil(kamerahoehe_m=h, abstand_m=d, brennweite_mm=f,
                                sensor_hoehe_mm=24.0, shift_mm=0.0)
        for h, d, f in [(1.0, 5.0, 17.0), (1.7, 40.0, 24.0), (3.0, 120.0, 50.0)]
    ]
    assert werte == [0.5, 0.5, 0.5]
    assert komposition.bodenanteil(kamerahoehe_m=1.7, sensor_hoehe_mm=24.0,
                                   shift_mm=6.0) == pytest.approx(0.25)


def test_shift_nach_oben_regelt_den_bodenanteil_von_der_haelfte_abwaerts():
    werte = [komposition.bodenanteil(kamerahoehe_m=1.7, sensor_hoehe_mm=24.0, shift_mm=v)
             for v in (0.0, 3.0, 6.0, 9.0, 11.0)]
    assert werte == sorted(werte, reverse=True)
    assert werte[0] == 0.5
    assert werte[-1] == pytest.approx(1 / 24, abs=1e-6)


def test_shift_ausserhalb_des_sensors_wird_abgewiesen():
    with pytest.raises(komposition.KompositionError, match="ausserhalb des Sensors"):
        komposition.horizontanteil(shift_mm=13.0, sensor_hoehe_mm=24.0)


# ======================================================================================
# Die 59,8 % — der Brückenschlag zur Messreihe
# ======================================================================================

def test_die_gemessenen_598_prozent_liegen_ueber_dem_shiftfreien_normalfall():
    befund = komposition.bodenanteil_erreichbar(
        komposition.BODENANTEIL_MESSREIHE_2026_08_20, sensor_hoehe_mm=24.0)
    assert befund["ueber_der_haelfte"] is True
    assert komposition.BODENANTEIL_MESSREIHE_2026_08_20 > komposition.BODENANTEIL_OHNE_SHIFT


def test_die_598_prozent_verlangen_einen_shift_nach_unten_und_sind_damit_erreichbar():
    """Hier widerspricht die Geometrie der Recherche, und der Test hält das fest.

    Der übliche Satz lautet „über 50 % geht nur mit Kippen". Der belegte Verstellweg ist
    aber ±11 mm, in jede Richtung: −2,35 mm am Querformat erzeugen 59,8 % Boden bei
    lotrechter Sensorebene, also **ohne** Konvergenz. Unüblich ist das, nicht unmöglich.
    """
    befund = komposition.bodenanteil_erreichbar(0.598, sensor_hoehe_mm=24.0)
    assert befund["richtung"] == "abwaerts"
    assert befund["shift_mm"] == pytest.approx(-2.352, abs=1e-3)
    assert befund["erreichbar"] is True
    assert abs(befund["shift_mm"]) < komposition.SHIFT_HOECHSTWERT_MM


def test_der_nach_unten_geshiftete_bodenanteil_stimmt_mit_der_geometrie_ueberein():
    """Gegenprobe von der anderen Seite: der ausgerechnete Shift, in die Bildgeometrie
    eingesetzt, muss die 59,8 % wieder hergeben — und die Kamera bleibt dabei waagrecht."""
    assert komposition.bodenanteil(kamerahoehe_m=1.70, sensor_hoehe_mm=24.0,
                                   shift_mm=-2.352) == pytest.approx(0.598, abs=1e-4)
    assert komposition.konvergenz(neigung_grad=komposition.NEIGUNG_WAAGRECHT_GRAD,
                                  gebaeudehoehe_m=8.0, kamerahoehe_m=1.70,
                                  abstand_m=12.0) == 0.0


def test_die_haelfte_ist_der_shiftfreie_fall():
    befund = komposition.bodenanteil_erreichbar(0.5, sensor_hoehe_mm=24.0)
    assert befund["shift_mm"] == 0.0
    assert befund["richtung"] == "kein_shift"
    assert befund["ueber_der_haelfte"] is False


def test_ein_bodenanteil_jenseits_des_verstellwegs_ist_nicht_erreichbar():
    """99 % Boden bräuchten 11,76 mm Shift nach unten — mehr, als das Objektiv hergibt."""
    befund = komposition.bodenanteil_erreichbar(0.99, sensor_hoehe_mm=24.0)
    assert befund["erreichbar"] is False
    assert "Nicht erreichbar" in befund["bemerkung"]


def test_bodenanteil_erreichbar_weist_werte_ausserhalb_von_null_bis_eins_ab():
    with pytest.raises(komposition.KompositionError, match="zwischen 0 und 1"):
        komposition.bodenanteil_erreichbar(1.4)


# ======================================================================================
# Mindestabstand — und der Term, den eine naive Umsetzung übersieht
# ======================================================================================

def test_bei_vollem_shift_bindet_der_gebaeudefuss_und_nicht_das_dach():
    """Der Fall, den der Auftrag ausdrücklich festgehalten haben will.

    8 m Bau, Kamera auf 1,70 m, 24 mm im Hochformat, Shift 12 mm: Der Mindestabstand
    beträgt 6,8 m — und zwar wegen des **Sockels**, nicht wegen der Traufe. Der
    Dach-Term liegt bei 5,04 m und verliert. Eine Umsetzung, die nur den ersten Term
    kennt, stellt die Kamera 1,76 m zu nah und schneidet den Gebäudefuss ab.
    """
    r = komposition.mindestabstand(gebaeudehoehe_m=8.0, kamerahoehe_m=1.70,
                                   brennweite_mm=24.0, sensor_hoehe_mm=36.0,
                                   shift_mm=12.0)
    assert r["bindend"] == "fuss"
    assert r["fuss_m"] > r["dach_m"]
    assert r["abstand_m"] == pytest.approx(6.8, abs=1e-9)
    assert r["dach_m"] == pytest.approx(5.04, abs=1e-9)


def test_beim_projektueblichen_shift_von_elf_millimetern_bindet_ebenfalls_der_fuss():
    """Nicht nur bei den 12 mm der Recherchetabelle, auch beim belegten Regelwert."""
    r = komposition.mindestabstand(gebaeudehoehe_m=8.0, kamerahoehe_m=1.70,
                                   brennweite_mm=24.0, sensor_hoehe_mm=36.0,
                                   shift_mm=komposition.SHIFT_HOECHSTWERT_MM)
    assert r["bindend"] == "fuss"
    assert r["abstand_m"] == pytest.approx(40.8 / 7.0, abs=1e-9)


def test_ohne_shift_bindet_bei_demselben_bau_das_dach():
    """Die Gegenprobe. Der bindende Term **wechselt** — das ist die eigentliche Aussage."""
    r = komposition.mindestabstand(gebaeudehoehe_m=8.0, kamerahoehe_m=1.70,
                                   brennweite_mm=24.0, sensor_hoehe_mm=36.0,
                                   shift_mm=0.0)
    assert r["bindend"] == "dach"
    assert r["abstand_m"] == pytest.approx(8.4, abs=1e-9)


@pytest.mark.parametrize("hoehe,erwartet", [(8.0, 8.4), (15.0, 17.73), (30.0, 37.73),
                                            (60.0, 77.73)])
def test_mindestabstand_trifft_die_recherchetabelle(hoehe, erwartet):
    """KOMPOSITION_AUSSEN.md 4.3, Zeile „24 mm, hoch, kein Shift"."""
    r = komposition.mindestabstand(gebaeudehoehe_m=hoehe, kamerahoehe_m=1.70,
                                   brennweite_mm=24.0, sensor_hoehe_mm=36.0)
    assert r["abstand_m"] == pytest.approx(erwartet, abs=0.02)


def test_bei_doppelter_kamerahoehe_binden_beide_terme_zugleich():
    """H = 2h ist der Umschlagpunkt ohne Shift. Genau dort ist ``bindend`` weder noch."""
    r = komposition.mindestabstand(gebaeudehoehe_m=3.4, kamerahoehe_m=1.70,
                                   brennweite_mm=24.0, sensor_hoehe_mm=36.0)
    assert r["bindend"] == "beide"
    assert r["dach_m"] == pytest.approx(r["fuss_m"])


def test_der_faktor_abstand_durch_hoehe_ist_nicht_konstant():
    """Damit niemand die Formel durch eine Faustregel „Abstand = k × Höhe" ersetzt.

    Der Faktor wächst mit der Gebäudehöhe: eine feste Zahl wäre bei kleinen Bauten zu
    grosszügig und bei grossen zu knapp.
    """
    faktoren = [
        komposition.mindestabstand(gebaeudehoehe_m=H, kamerahoehe_m=1.70,
                                   brennweite_mm=24.0,
                                   sensor_hoehe_mm=36.0)["faktor_hoehe"]
        for H in (8.0, 15.0, 30.0, 60.0)
    ]
    assert faktoren == sorted(faktoren)
    assert faktoren[-1] - faktoren[0] > 0.2


def test_shift_gleich_halber_sensorhoehe_ist_ein_fehler_mit_erklaerung():
    """Querformat und 12 mm Shift: Der Horizont sitzt auf der Bildunterkante. Kein
    Abstand bringt den Gebäudefuss ins Bild — das ist keine grosse Zahl, sondern keine."""
    with pytest.raises(komposition.KompositionError, match="nicht definiert"):
        komposition.mindestabstand(gebaeudehoehe_m=8.0, kamerahoehe_m=1.70,
                                   brennweite_mm=24.0, sensor_hoehe_mm=24.0,
                                   shift_mm=12.0)


def test_kamera_ueber_dem_dach_ist_die_falsche_frage():
    with pytest.raises(komposition.KompositionError, match="über gebaeudehoehe_m"):
        komposition.mindestabstand(gebaeudehoehe_m=1.5, kamerahoehe_m=1.70)


@pytest.mark.parametrize("grossformat,kleinbild", [(65, 18.3), (90, 25.3), (150, 42.2),
                                                   (210, 59.1)])
def test_der_habs_objektivsatz_umgerechnet(grossformat, kleinbild):
    assert komposition.kleinbild_aequivalent(grossformat) == pytest.approx(kleinbild,
                                                                          abs=0.05)


def test_der_habs_normalwert_und_die_heutige_arbeitsbrennweite_treffen_sich():
    """Bundesstandard von 1933 (90 mm auf 4×5) und heutige Praxis (24 mm) — zwei
    unabhängige Wege, ein Ergebnis. Der Abstand beträgt gut ein Millimeter."""
    aus_habs = komposition.kleinbild_aequivalent(90.0)
    assert abs(aus_habs - komposition.ARBEITSBRENNWEITE_AUSSEN_MM) < 1.5


# ======================================================================================
# Kamerahöhe und Bezugspunkt
# ======================================================================================

def test_der_bezugspunkt_ist_ein_pflichtargument():
    """Es gibt hier bewusst keine Vorgabe — jede wäre irgendwo falsch."""
    with pytest.raises(TypeError):
        komposition.kamerahoehe(1.70)


def test_ein_unbekannter_bezugspunkt_wird_abgewiesen():
    with pytest.raises(komposition.KompositionError, match="Unbekannter bezugspunkt"):
        komposition.kamerahoehe(1.70, bezugspunkt="augenhoehe")


def test_ein_unzuverlaessiger_bezugspunkt_wird_gemeldet_ein_zuverlaessiger_nicht():
    """Die Hüllbox-Unterkante ist im Projekt schon schiefgegangen; das Gelände nicht."""
    schlecht = komposition.kamerahoehe(1.70, bezugspunkt="huellbox_unterkante")
    gut = komposition.kamerahoehe(1.70, bezugspunkt="terrain_an_kamera")
    assert schlecht["verlaesslich"] is False
    assert any("schiefgegangen" in w for w in schlecht["warnungen"])
    assert gut["verlaesslich"] is True
    assert not any("schiefgegangen" in w for w in gut["warnungen"])


def test_die_gesetzten_170_meter_werden_als_hoher_wert_gemeldet():
    """1,70 m liegt **nahe** dem 95. Perzentil der Männer (1,735 m), aber darunter.

    Der Test hält fest, dass die Bibliothek genau da die Grenze zieht: 1,70 m löst die
    Perzentilwarnung nicht aus, 1,80 m schon — und dann auch die zweite Warnung, dass
    der Wert die anthropometrische Spanne verlassen hat. Eine Warnung, die schon bei
    1,70 m käme, wäre Lärm; eine, die auch bei 1,80 m schwiege, wäre nutzlos.
    """
    normal = komposition.kamerahoehe(komposition.SETZUNG_AUGENHOEHE_AUSSEN_M,
                                     bezugspunkt="terrain_an_kamera")
    hoch = komposition.kamerahoehe(1.80, bezugspunkt="terrain_an_kamera")
    assert not any("95. Perzentil" in w for w in normal["warnungen"])
    assert any("95. Perzentil" in w for w in hoch["warnungen"])
    assert any("anthropometrischen" in w for w in hoch["warnungen"])


def test_eine_kamerahoehe_ist_niemals_belegt():
    """Keine institutionelle Vorgabe der Recherche nennt eine Kamerahöhe. Was das Modul
    hier zurückgibt, ist darum immer eine Setzung — auch wenn die Zahl vertraut aussieht."""
    assert komposition.kamerahoehe(
        1.70, bezugspunkt="terrain_an_kamera")["belegstufe"] == "gesetzt"
    assert komposition.belegstufe("SETZUNG_AUGENHOEHE_AUSSEN_M") == "gesetzt"


@pytest.mark.parametrize("hoehe,erwartet", [(1.60, 0.200), (1.70, 0.2125), (3.00, 0.375)])
def test_horizont_am_baukoerper_trifft_die_recherchetabelle(hoehe, erwartet):
    """KOMPOSITION_AUSSEN.md 4.4b, Spalte H = 8 m."""
    assert komposition.horizont_am_baukoerper(
        kamerahoehe_m=hoehe, gebaeudehoehe_m=8.0) == pytest.approx(erwartet)


def test_die_hundert_millimeter_sind_gleichgueltig_der_bezugspunkt_ist_es_nicht():
    """Die quantitative Fassung des Bezugspunkt-Problems dieses Projekts.

    1,60 gegen 1,70 m verschiebt den Horizont am Baukörper um gut einen Prozentpunkt.
    Ein Geschoss daneben verschiebt ihn um mehr als das Zehnfache. Der Test hält beides
    fest — die Zahl allein sagte nichts.
    """
    geschmack = komposition.horizont_verschiebung_pp(gebaeudehoehe_m=8.0,
                                                     hoehe_a_m=1.60, hoehe_b_m=1.70)
    fehler = komposition.horizont_verschiebung_pp(gebaeudehoehe_m=8.0,
                                                  hoehe_a_m=1.70, hoehe_b_m=3.00)
    assert geschmack == pytest.approx(1.25, abs=0.01)
    assert fehler == pytest.approx(16.25, abs=0.01)
    assert fehler > 5.0 * geschmack


# ======================================================================================
# Boden, Decke, Wand — innen
# ======================================================================================

def test_die_gleichgewichtshoehe_liegt_auf_halber_raumhoehe():
    """2,55 m lichte Höhe → 1,275 m. Die Zahl steht in der Recherche, nicht in einer
    Umkehrrechnung dieses Moduls."""
    assert komposition.hoehe_fuer_bild_gleichgewicht(2.55) == pytest.approx(1.275)
    assert komposition.hoehe_fuer_bild_gleichgewicht(3.00) == pytest.approx(1.50)


@pytest.mark.parametrize("brennweite", [24.0, 35.0, 50.0])
@pytest.mark.parametrize("abstand", [3.0, 5.0, 8.0])
def test_auf_halber_raumhoehe_bekommen_boden_und_decke_exakt_gleich_viel_bild(brennweite,
                                                                              abstand):
    """Die einzige harte, geometrisch beweisbare Bildpositionsregel dieses Moduls.

    Geprüft über drei Brennweiten **und** drei Abstände, weil ein einzelnes Wertepaar
    Unabhängigkeit nicht zeigen kann. Verglichen werden die **rohen** Anteile: Bei
    50 mm aus 3 m Abstand fallen beide Kanten aus dem Bild, und zwei auf null
    begrenzte Werte wären trivial gleich.

    Die Kamerahöhe steht hier als ``2.55 / 2`` da und nicht als Aufruf der
    Umkehrfunktion — sonst prüfte der Test seine eigene Herleitung.
    """
    anteile = komposition.bildanteile(kamerahoehe_m=2.55 / 2.0, raumhoehe_m=2.55,
                                      abstand_m=abstand, brennweite_mm=brennweite,
                                      sensor_hoehe_mm=24.0)
    assert anteile["roh"]["boden"] == pytest.approx(anteile["roh"]["decke"], abs=1e-12)


def test_auf_gleichgewichtshoehe_sind_die_sichtbaren_anteile_gleich_und_nicht_null():
    """Gegenprobe zum Vorigen: ein Aufbau, bei dem beide Kanten wirklich im Bild sind."""
    anteile = komposition.bildanteile(kamerahoehe_m=1.275, raumhoehe_m=2.55,
                                      abstand_m=5.0, brennweite_mm=24.0,
                                      sensor_hoehe_mm=24.0)
    assert anteile["bodenanteil"] == pytest.approx(0.245)
    assert anteile["deckenanteil"] == pytest.approx(0.245)
    assert anteile["boden_kante_im_bild"] is True
    assert anteile["decken_kante_im_bild"] is True


@pytest.mark.parametrize("hoehe,boden,decke", [(1.10, 0.28, 0.21),
                                               (1.275, 0.245, 0.245),
                                               (1.50, 0.20, 0.29)])
def test_bildanteile_treffen_die_recherchetabelle(hoehe, boden, decke):
    """KOMPOSITION_INNEN.md 4.4, Beispiel H_r = 2,55 m, D = 5,0 m, 24 mm."""
    anteile = komposition.bildanteile(kamerahoehe_m=hoehe, raumhoehe_m=2.55,
                                      abstand_m=5.0, brennweite_mm=24.0,
                                      sensor_hoehe_mm=24.0)
    assert anteile["bodenanteil"] == pytest.approx(boden, abs=1e-9)
    assert anteile["deckenanteil"] == pytest.approx(decke, abs=1e-9)
    assert anteile["wandanteil"] == pytest.approx(0.51, abs=1e-9)


def test_die_projektuebliche_augenhoehe_kippt_das_verhaeltnis_zur_decke():
    """1,70 m in einem 2,55-m-Raum: Die Decke bekommt gut das Doppelte des Bodens.

    Der Auftrag nennt hier 28 Prozentpunkte. Diese Zahl entsteht aus der **unbegrenzten**
    Formel der Recherche bei 3,0 m Abstand — dort liefert sie −6,7 % Boden. Ein Anteil
    kann nicht negativ sein; sichtbar sind 0 % gegen 21,7 %. Der Test hält beide Fassungen
    fest, damit die Differenz nicht wieder als Widerspruch auftaucht.
    """
    aus_fuenf = komposition.bildanteile(kamerahoehe_m=1.70, raumhoehe_m=2.55,
                                        abstand_m=5.0, brennweite_mm=24.0,
                                        sensor_hoehe_mm=24.0)
    assert aus_fuenf["bodenanteil"] == pytest.approx(0.16)
    assert aus_fuenf["deckenanteil"] == pytest.approx(0.33)

    aus_drei = komposition.bildanteile(kamerahoehe_m=1.70, raumhoehe_m=2.55,
                                       abstand_m=3.0, brennweite_mm=24.0,
                                       sensor_hoehe_mm=24.0)
    assert aus_drei["roh"]["boden"] == pytest.approx(-1 / 15, abs=1e-9)
    assert aus_drei["roh"]["decke"] - aus_drei["roh"]["boden"] == pytest.approx(0.2833,
                                                                               abs=1e-3)
    assert aus_drei["bodenanteil"] == 0.0
    assert aus_drei["boden_kante_im_bild"] is False


@pytest.mark.parametrize("hoehe", [0.50, 1.00, 1.275, 1.70, 2.20])
def test_der_wandanteil_haengt_nicht_von_der_kamerahoehe_ab(hoehe):
    """Die Kamerahöhe verteilt nur zwischen Boden und Decke um — sie ändert nicht,
    wieviel Wand zu sehen ist. Fünf Höhen über die ganze brauchbare Spanne."""
    anteile = komposition.bildanteile(kamerahoehe_m=hoehe, raumhoehe_m=2.55,
                                      abstand_m=5.0, brennweite_mm=24.0,
                                      sensor_hoehe_mm=24.0)
    assert anteile["wandanteil"] == pytest.approx(0.51, abs=1e-9)


def test_shift_nach_oben_nimmt_dem_boden_genau_das_was_er_der_decke_gibt():
    """Der einzige Vorzeichenunterschied zwischen Boden- und Deckenformel — und die
    Stelle, an der die Gleichgewichtsregel hängt.

    Aufbau: 2,55 m Raumhöhe, Kamera auf 1,275 m, 5 m Abstand, 24 mm quer. Ohne Shift
    bekommen Boden und Decke je 24,5 %. Drei Millimeter Shift nach oben verschieben
    genau ``3/24 = 12,5`` Prozentpunkte vom Boden zur Decke — die **Summe** bleibt
    gleich, weil der Wandanteil vom Shift nicht abhängt.
    """
    fest = dict(kamerahoehe_m=1.275, raumhoehe_m=2.55, abstand_m=5.0,
                brennweite_mm=24.0, sensor_hoehe_mm=24.0)
    ohne = komposition.bildanteile(shift_mm=0.0, **fest)
    mit = komposition.bildanteile(shift_mm=3.0, **fest)

    assert ohne["bodenanteil"] == pytest.approx(0.245)
    assert ohne["deckenanteil"] == pytest.approx(0.245)
    assert mit["bodenanteil"] == pytest.approx(0.245 - 0.125)
    assert mit["deckenanteil"] == pytest.approx(0.245 + 0.125)
    assert (mit["bodenanteil"] + mit["deckenanteil"]
            == pytest.approx(ohne["bodenanteil"] + ohne["deckenanteil"]))
    assert komposition.deckenanteil(shift_mm=3.0, **fest) == pytest.approx(0.37)


def test_der_wandanteil_haengt_sehr_wohl_vom_abstand_ab():
    """Gegenprobe: Wäre der Wandanteil einfach konstant, sagte der Test darüber nichts."""
    nah = komposition.bildanteile(kamerahoehe_m=1.275, raumhoehe_m=2.55, abstand_m=4.0,
                                  brennweite_mm=24.0, sensor_hoehe_mm=24.0)
    fern = komposition.bildanteile(kamerahoehe_m=1.275, raumhoehe_m=2.55, abstand_m=8.0,
                                   brennweite_mm=24.0, sensor_hoehe_mm=24.0)
    assert nah["wandanteil"] > fern["wandanteil"]


def test_die_abstaende_ab_denen_boden_und_deckenkante_im_bild_liegen():
    """Dieselbe Formel wie draussen, nur mit der Raumhöhe statt der Gebäudehöhe.

    KOMPOSITION_INNEN.md 4.4 Nr. 3: bei h = 1,10 m, H_r = 2,55 m und 24 mm liegt die
    Bodenkante ab 2,20 m im Bild, die Deckenkante ab 2,90 m.
    """
    r = komposition.mindestabstand(gebaeudehoehe_m=2.55, kamerahoehe_m=1.10,
                                   brennweite_mm=24.0, sensor_hoehe_mm=24.0)
    assert r["fuss_m"] == pytest.approx(2.20, abs=1e-9)
    assert r["dach_m"] == pytest.approx(2.90, abs=1e-9)
    assert r["bindend"] == "dach"


def test_mit_shift_verschiebt_sich_die_gleichgewichtshoehe_nach_unten():
    """``h = H_r/2 − v·D/f``. Bei 2 mm Shift, 5 m Abstand und 24 mm sind das 0,4167 m
    weniger als die halbe Raumhöhe."""
    h = komposition.hoehe_fuer_bild_gleichgewicht(2.55, shift_mm=2.0, abstand_m=5.0,
                                                  brennweite_mm=24.0)
    assert h == pytest.approx(1.275 - 2.0 * 5.0 / 24.0)
    anteile = komposition.bildanteile(kamerahoehe_m=h, raumhoehe_m=2.55, abstand_m=5.0,
                                      brennweite_mm=24.0, sensor_hoehe_mm=24.0,
                                      shift_mm=2.0)
    assert anteile["roh"]["boden"] == pytest.approx(anteile["roh"]["decke"], abs=1e-12)
    assert anteile["bodenanteil"] == pytest.approx(0.245)
    assert anteile["deckenanteil"] == pytest.approx(0.245)


def test_gleichgewicht_mit_shift_verlangt_abstand_und_brennweite():
    """Ohne Shift gilt ``H_r/2``. Mit Shift gilt es nicht — und dann ist eine stille
    Näherung schlechter als ein Fehler."""
    with pytest.raises(komposition.KompositionError, match="Abstand"):
        komposition.hoehe_fuer_bild_gleichgewicht(2.55, shift_mm=2.0)


def test_der_innenraum_bodenanteil_verlangt_den_abstand():
    with pytest.raises(komposition.KompositionError, match="abstand_m"):
        komposition.bodenanteil(kamerahoehe_m=1.10, raumhoehe_m=2.55)


def test_aussen_gibt_es_keinen_decken_und_keinen_wandanteil():
    """Über dem Horizont steht der Himmel. Eine Zahl dafür wäre erfunden."""
    anteile = komposition.bildanteile(kamerahoehe_m=1.70, sensor_hoehe_mm=36.0)
    assert anteile["lage"] == "aussen"
    assert anteile["deckenanteil"] is None
    assert anteile["wandanteil"] is None
    assert anteile["bodenanteil"] == 0.5


# ======================================================================================
# Der Ansichtenkatalog nach HABS
# ======================================================================================

def test_der_katalog_benutzt_die_richtungstabelle_aus_kameras():
    """Es gibt in diesem Projekt genau eine Richtungstabelle. Dieses Modul erfindet
    keine zweite — es bildet nur ab."""
    katalog = komposition.ansichtenkatalog()
    assert len(katalog) == 4
    for ansicht in katalog:
        assert ansicht["richtung"] in kameras.RICHTUNGSFOLGE
        assert ansicht["azimut_grad"] == kameras.richtungen()[ansicht["richtung"]]


def test_die_frontale_ist_frontal_und_die_ueber_eck_ansichten_sind_diagonal():
    katalog = {a["name"]: a["richtung"] for a in komposition.ansichtenkatalog()}
    assert kameras.RICHTUNGEN[katalog["frontal"]][1] == 0
    assert kameras.RICHTUNGEN[katalog["ueber_eck_vorn"]][1] != 0
    assert kameras.RICHTUNGEN[katalog["ueber_eck_hinten"]][1] != 0


@pytest.mark.parametrize("bias", [20.0, 35.0, 45.0, 60.0])
def test_die_beiden_ueber_eck_ansichten_liegen_sich_genau_gegenueber(bias):
    """HABS verlangt „front and one side" und „rear and opposing side" — also
    gegenüberliegende Diagonalen. Geprüft über vier Bias-Werte, weil sich die Azimute
    mit dem Bias verschieben und ein einzelner Wert Zufall sein könnte."""
    katalog = {a["name"]: a["azimut_grad"]
               for a in komposition.ansichtenkatalog(bias_grad=bias)}
    differenz = (katalog["ueber_eck_hinten"] - katalog["ueber_eck_vorn"]) % 360.0
    assert differenz == pytest.approx(180.0)


@pytest.mark.parametrize("frontal,seite,vorn,hinten", [
    ("s", -1, "sSE", "nNW"),
    ("s", +1, "sSW", "nNE"),
    ("e", -1, "eEN", "wWS"),
    ("w", +1, "wWN", "eES"),
])
def test_die_zuordnung_der_ueber_eck_kuerzel(frontal, seite, vorn, hinten):
    """Die Vorzeichen dieser Tabelle sind die Stelle, an der sich der Bestand
    nachweislich vertan hat. Darum jede Kombination einzeln."""
    katalog = {a["name"]: a["richtung"]
               for a in komposition.ansichtenkatalog(frontal=frontal, seite=seite)}
    assert katalog["frontal"] == frontal
    assert katalog["ueber_eck_vorn"] == vorn
    assert katalog["ueber_eck_hinten"] == hinten


def test_die_heutige_projektvorgabe_deckt_drei_der_vier_habs_ansichten_nicht_ab():
    """``abholer.AUTO_RICHTUNGEN = ("sSE",)`` — eine einzige Richtung.

    Das ist keine Forderung nach zwölf Kameras; wieviele Standpunkte ein Auftrag wert
    ist, ist eine Betriebsentscheidung. Es ist die Auskunft, was dabei wegfällt.
    """
    assert komposition.fehlende_ansichten(("sSE",)) == ("umgebung", "frontal",
                                                        "ueber_eck_hinten")


def test_der_volle_habs_satz_laesst_nichts_fehlen():
    """Gegenprobe: Wäre ``fehlende_ansichten`` schlicht „alles fehlt", sagte der
    vorige Test nichts."""
    assert komposition.fehlende_ansichten(("s", "sSE", "nNW")) == ()


def test_ansichtenkatalog_weist_eine_diagonale_als_frontal_ab():
    with pytest.raises(komposition.KompositionError, match="eine der vier Frontalen"):
        komposition.ansichtenkatalog(frontal="sSE")


def test_ansichtenkatalog_weist_eine_unbrauchbare_seite_ab():
    with pytest.raises(komposition.KompositionError, match="seite"):
        komposition.ansichtenkatalog(seite=0)


def test_die_habs_zitate_stehen_woertlich_im_katalog():
    """Der Ansichtenkatalog ist die härteste Fundstelle der Recherche. Er trägt die
    Vorschrift im Wortlaut, damit niemand sie nacherzählen muss."""
    katalog = {a["name"]: a["habs"] for a in komposition.ansichtenkatalog()}
    assert katalog["ueber_eck_vorn"] == "Perspective view, front and one side"
    assert katalog["ueber_eck_hinten"] == "Perspective view, rear and opposing side"


# ======================================================================================
# Die Aufnahme als Ganzes
# ======================================================================================

def test_eine_waagrechte_aufnahme_meldet_weder_konvergenz_noch_neigung():
    a = komposition.aufnahme(kamerahoehe_m=1.70, bezugspunkt="terrain_an_kamera",
                             gebaeudehoehe_m=8.0, abstand_m=12.0)
    assert a["neigung_grad"] == 0.0
    assert a["rollwinkel_grad"] == 0.0
    assert a["konvergenz"] == 0.0
    assert a["abstand_genuegt"] is True
    assert a["warnungen"] == []


def test_eine_geneigte_aufnahme_wird_mit_ihrer_konvergenz_gemeldet():
    a = komposition.aufnahme(kamerahoehe_m=1.70, bezugspunkt="terrain_an_kamera",
                             gebaeudehoehe_m=8.0, abstand_m=12.0, neigung_grad=9.4623)
    assert a["konvergenz"] > 0.0
    assert len(a["warnungen"]) == 1
    assert "HABS" in a["warnungen"][0]


def test_ein_zu_kurzer_abstand_wird_gemeldet_und_nennt_den_bindenden_term():
    a = komposition.aufnahme(kamerahoehe_m=1.70, bezugspunkt="terrain_an_kamera",
                             gebaeudehoehe_m=8.0, abstand_m=6.0,
                             sensor_hoehe_mm=36.0, shift_mm=12.0)
    assert a["abstand_genuegt"] is False
    assert a["mindestabstand"]["bindend"] == "fuss"
    assert any("fuss" in w for w in a["warnungen"])


def test_die_aufnahme_reicht_die_warnung_zum_bezugspunkt_durch():
    a = komposition.aufnahme(kamerahoehe_m=1.70, bezugspunkt="weltnull",
                             gebaeudehoehe_m=8.0, abstand_m=12.0)
    assert any("weltnull" in w for w in a["warnungen"])
    assert a["kamerahoehe"]["verlaesslich"] is False
