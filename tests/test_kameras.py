"""Die Kamerarechnung — geprüft an von Hand nachrechenbaren Fällen.

Warum diese Tests so aussehen
-----------------------------
Der Bestand, aus dem dieses Modul stammt, hatte **keine Tests** (Bestandsaufnahme A.1,
„Reifegrad"). Belegt ist er trotzdem — durch zwei einkommentierte Vorzeichenkorrekturen.
Jemand hat die Bilder angesehen und für falsch befunden; das ist ein stärkerer Beleg als
ein Test, aber ein flüchtiger. Diese Datei hält fest, was dort nur im Kommentar stand.

Zwei Sorten Prüfung stehen hier:

1. **Von Hand nachrechenbare Erwartungswerte.** Ein Würfel, eine bekannte Brennweite,
   eine Zahl, die aus dem Tangens folgt. Wenn die Trigonometrie kippt, kippt sie hier.
2. **Randwinkel mit physikalisch eindeutiger Antwort.** 0° und 90° Azimut sind die
   Stellen, an denen ``sin`` und ``cos`` einzeln sichtbar werden — genau die Vertauschung,
   die im Bestand nachweislich passiert ist.
"""
from __future__ import annotations

import math

import pytest

from aiimaging import kameras


# --------------------------------------------------------------------------------------
# Bildwinkel
# --------------------------------------------------------------------------------------

def test_bildwinkel_kleinbild_50mm_ist_der_bekannte_wert():
    """50 mm auf Kleinbild sind knapp 40° horizontal — der Wert steht in jedem Handbuch."""
    hfov, _ = kameras.bildwinkel(50.0, seitenverhaeltnis=3 / 2)
    assert math.degrees(hfov) == pytest.approx(39.6, abs=0.1)


def test_bildwinkel_vertikal_folgt_dem_seitenverhaeltnis():
    """Der vertikale Winkel MUSS vom Seitenverhältnis abhängen — sonst ist es ein Faktor.

    Das ist der Punkt, an dem sich dieses Modul von der Hauptfundstelle des Bestands
    unterscheidet: Dort steckt die Sensorhöhe als 27 mm fest im Code, und die
    Bildproportion geht in die Abstandsrechnung schlicht nicht ein.
    """
    _, vfov_16_9 = kameras.bildwinkel(28.0, seitenverhaeltnis=16 / 9)
    _, vfov_4_3 = kameras.bildwinkel(28.0, seitenverhaeltnis=4 / 3)
    assert vfov_4_3 > vfov_16_9


def test_bildwinkel_quadratisch_ist_in_beiden_richtungen_gleich():
    hfov, vfov = kameras.bildwinkel(35.0, seitenverhaeltnis=1.0)
    assert hfov == pytest.approx(vfov)


@pytest.mark.parametrize("brennweite", [0.0, -28.0, float("inf"), float("nan")])
def test_bildwinkel_weist_unbrauchbare_brennweite_ab(brennweite):
    """Brennweite 0 ergäbe 180° — eine Zahl, die entsteht, aber nichts bedeutet."""
    with pytest.raises(ValueError, match="brennweite_mm"):
        kameras.bildwinkel(brennweite)


# --------------------------------------------------------------------------------------
# Richtungen — die Stelle, an der sich der Bestand vertan hat
# --------------------------------------------------------------------------------------

def test_zwoelf_richtungen_und_keine_mehr():
    assert len(kameras.RICHTUNGEN) == 12
    assert set(kameras.RICHTUNGSFOLGE) == set(kameras.RICHTUNGEN)
    assert len(kameras.RICHTUNGSFOLGE) == 12


@pytest.mark.parametrize("kuerzel,azimut", [
    ("n", 0.0), ("e", 90.0), ("s", 180.0), ("w", 270.0),
])
def test_frontale_stehen_senkrecht_auf_der_fassade(kuerzel, azimut):
    assert kameras.richtungen(35.0)[kuerzel] == pytest.approx(azimut)


@pytest.mark.parametrize("kuerzel,himmelsrichtung", [
    ("nNE", 45.0), ("eEN", 45.0),      # beide auf die Nordost-Ecke
    ("eES", 135.0), ("sSE", 135.0),    # beide auf die Südost-Ecke
    ("sSW", 225.0), ("wWS", 225.0),    # beide auf die Südwest-Ecke
    ("wWN", 315.0), ("nNW", 315.0),    # beide auf die Nordwest-Ecke
])
def test_diagonalen_zeigen_bei_45_grad_auf_ihre_ecke(kuerzel, himmelsrichtung):
    """Bei ``bias_grad=45`` MUSS jede Diagonale auf der Ecke landen, die ihr Name nennt.

    **Das ist der Test, den es im Bestand nicht gab und der ihn gebraucht hätte.** Dort
    waren die N/S-Diagonalen invertiert; der Fehler wurde im Betrieb gefunden und im
    Kommentar vermerkt. Ein Name wie ``sSE`` ist eine Behauptung über eine
    Himmelsrichtung, und Behauptungen kann man prüfen.
    """
    assert kameras.richtungen(45.0)[kuerzel] == pytest.approx(himmelsrichtung)


def test_bias_regelt_das_fassadenverhaeltnis():
    """Kleiner Bias heisst: näher an der Frontalen, die primäre Fassade dominiert."""
    eng = kameras.richtungen(30.0)
    weit = kameras.richtungen(45.0)
    assert eng["nNE"] == pytest.approx(30.0)
    assert weit["nNE"] == pytest.approx(45.0)


@pytest.mark.parametrize("bias", [0.0, 90.0, -10.0, 120.0, float("nan")])
def test_bias_ausserhalb_von_null_bis_neunzig_wird_abgewiesen(bias):
    """Bei 0 fiele die Diagonale auf die Frontale, bei 90 auf die nächste."""
    with pytest.raises(ValueError, match="bias_grad"):
        kameras.richtungen(bias)


# --------------------------------------------------------------------------------------
# Sichtbare Breite — die Verbesserung gegenüber dem Bestand
# --------------------------------------------------------------------------------------

def test_frontale_sieht_genau_eine_gebaeudeseite():
    """Von Norden ist die Nordfassade zu sehen, also dx — nicht die Diagonale.

    Der Bestand rechnet hier ``max(breite, tiefe, diagonale)``. Weil die Diagonale eines
    Rechtecks immer mindestens so gross ist wie jede Seite, gewinnt sie ausnahmslos: Das
    ``max`` ist toter Code, und die Frontale steht auf Diagonalabstand.
    """
    masse = (30.0, 12.0, 10.0)
    assert kameras.sichtbare_breite(masse, 0.0) == pytest.approx(30.0)
    assert kameras.sichtbare_breite(masse, 180.0) == pytest.approx(30.0)
    assert kameras.sichtbare_breite(masse, 90.0) == pytest.approx(12.0)
    assert kameras.sichtbare_breite(masse, 270.0) == pytest.approx(12.0)


def test_eckblick_auf_den_wuerfel_sieht_die_diagonale():
    masse = (30.0, 30.0, 10.0)
    assert kameras.sichtbare_breite(masse, 45.0) == pytest.approx(30.0 * math.sqrt(2))


def test_breite_und_tiefe_tauschen_bei_neunzig_grad_die_rollen():
    masse = (30.0, 12.0, 10.0)
    assert kameras.sichtbare_tiefe(masse, 0.0) == pytest.approx(12.0)
    assert kameras.sichtbare_tiefe(masse, 90.0) == pytest.approx(30.0)


def test_der_bestandsfehler_kostet_beim_kubus_ein_drittel_bildflaeche():
    """Die Grösse des behobenen Fehlers, als Zahl statt als Behauptung."""
    masse = (30.0, 30.0, 10.0)
    frontal = kameras.sichtbare_breite(masse, 0.0)
    bestand = math.sqrt(30.0 ** 2 + 30.0 ** 2)      # was der Bestand immer nimmt
    assert frontal == pytest.approx(30.0)
    assert bestand / frontal == pytest.approx(math.sqrt(2), abs=1e-9)


# --------------------------------------------------------------------------------------
# Abstand
# --------------------------------------------------------------------------------------

def test_abstand_folgt_dem_tangens_von_hand_nachgerechnet():
    """Ein flacher, breiter Bau: die Breite ist massgebend, und die Zahl ist prüfbar.

    30 m breit, 1 m tief, bei 28 mm Brennweite und Deckungsgrad 1.0:
    ``15 / tan(hfov/2) + 0.5``.
    """
    masse = (30.0, 1.0, 3.0)
    hfov, _ = kameras.bildwinkel(28.0, seitenverhaeltnis=16 / 9)

    ergebnis = kameras.abstand_aus_bildwinkel(
        masse, 0.0, hoehe_ueber_grund=1.7, brennweite_mm=28.0, deckungsgrad=1.0)
    assert ergebnis["massgebend"] == "breite"

    # Bei der FRONTALEN ist die Handrechnung unverändert richtig, und die neue Rechnung muss
    # sie auf die letzte Stelle reproduzieren: Der seitliche Bildrand liegt hier auf einer
    # senkrechten Kante, die von vorn nach hinten läuft, und im Bild zählt ihr vorderes Ende —
    # also genau die halbe Tiefe. Die Umstellung vom 01.09.2026 wirkt auf die schrägen Blicke;
    # dass sie die frontalen NICHT verschiebt, ist die Hälfte ihrer Richtigkeit.
    assert ergebnis["abstand_m"] == pytest.approx(15.0 / math.tan(hfov / 2.0) + 0.5)

    # Und die Bedingung dahinter, unabhängig von jeder Formel: Bei diesem Abstand füllt die
    # projizierte Silhouette genau die ganze Bildbreite (Deckungsgrad 1.0).
    ecken = kameras._grundrissecken(masse, 0.0)
    anteil = kameras.silhouettenbreite(ecken, ergebnis["abstand_m"]) / (2.0 * math.tan(hfov / 2.0))
    assert anteil == pytest.approx(1.0, abs=1e-9), anteil


def test_kleinerer_deckungsgrad_schiebt_die_kamera_weiter_weg():
    masse = (30.0, 20.0, 10.0)
    nah = kameras.abstand_aus_bildwinkel(masse, 0.0, hoehe_ueber_grund=3.7, deckungsgrad=1.0)
    fern = kameras.abstand_aus_bildwinkel(masse, 0.0, hoehe_ueber_grund=3.7, deckungsgrad=0.55)
    assert fern["abstand_m"] > nah["abstand_m"]


def test_hoher_bau_wird_von_der_hoehe_bestimmt():
    """Ein Turm: nicht die Breite, sondern die Höhe setzt den Abstand."""
    masse = (20.0, 20.0, 100.0)
    ergebnis = kameras.abstand_aus_bildwinkel(masse, 0.0, hoehe_ueber_grund=21.7)
    assert ergebnis["massgebend"] == "hoehe"


def test_kleiner_bau_faellt_auf_die_untergrenze():
    """Ein Gartenhaus soll nicht aus zwei Metern fotografiert werden."""
    masse = (3.0, 3.0, 2.5)
    ergebnis = kameras.abstand_aus_bildwinkel(masse, 0.0, hoehe_ueber_grund=2.2,
                                              deckungsgrad=1.0)
    assert ergebnis["massgebend"] == "untergrenze"
    assert ergebnis["abstand_m"] >= kameras.WANDABSTAND_M


def test_beim_kleinen_bau_gewinnt_die_hoehe_schon_vor_der_untergrenze():
    """Ein Befund, der der Erwartung widerspricht — und darum hier festgehalten wird.

    Man vermutet, dass bei einem 3 m hohen Gartenhaus der Mindestabstand greift. Er tut
    es nicht: Bei einem so flachen Bau steht die Kamera auf 1.7 m, das Blickziel auf
    2.2 m — es liegen also **2.2 m unter** dem Blick und nur 0.3 m darüber. Massgebend
    ist der Weg nach unten, und bei einem Deckungsgrad von 0.55 schiebt der die Kamera
    weiter weg als die Untergrenze es täte.

    Das ist keine Fehlfunktion, sondern die Folge einer absoluten Augenhöhe: Wer auf
    1.7 m steht, sieht bei einem niedrigen Gebäude vor allem Boden.
    """
    ergebnis = kameras.abstand_aus_bildwinkel((3.0, 3.0, 2.5), 0.0, hoehe_ueber_grund=2.2)
    assert ergebnis["massgebend"] == "hoehe"
    assert ergebnis["halbe_hoehe_m"] == pytest.approx(2.2)


def test_hoehenbedarf_wird_asymmetrisch_von_der_zielhoehe_gemessen():
    """Bei einem hohen Bau zählt der Weg nach oben, bei einem flachen der nach unten.

    Eine halbe Gebäudehöhe anzusetzen wäre falsch: Das Blickziel sitzt bei einem
    zwanziggeschossigen Haus im ersten Fünftel der Fassade, nicht in ihrer Mitte.
    """
    hoch = kameras.abstand_aus_bildwinkel((20.0, 20.0, 60.0), 0.0, hoehe_ueber_grund=13.7)
    assert hoch["halbe_hoehe_m"] == pytest.approx(60.0 - 13.7)

    flach = kameras.abstand_aus_bildwinkel((20.0, 20.0, 3.0), 0.0, hoehe_ueber_grund=2.3)
    assert flach["halbe_hoehe_m"] == pytest.approx(2.3)


@pytest.mark.parametrize("deckung", [0.0, -0.5, 1.5, float("nan")])
def test_deckungsgrad_ausserhalb_null_bis_eins_wird_abgewiesen(deckung):
    with pytest.raises(ValueError, match="deckungsgrad"):
        kameras.abstand_aus_bildwinkel((10.0, 10.0, 5.0), 0.0,
                                       hoehe_ueber_grund=2.0, deckungsgrad=deckung)


# --------------------------------------------------------------------------------------
# Eckentest
# --------------------------------------------------------------------------------------

WUERFEL = [[-15.0, -15.0, 0.0], [15.0, 15.0, 20.0]]


def test_kamera_weit_genug_weg_sieht_alle_acht_ecken():
    ergebnis = kameras.ecken_im_bild((0.0, -200.0, 1.7), (0.0, 0.0, 5.7), WUERFEL)
    assert ergebnis["passt"] is True
    assert ergebnis["max_ueberstehen"] < 1.0
    assert ergebnis["ecken_hinter_kamera"] == 0


def test_kamera_zu_nah_meldet_das_ueberstehen_als_zahl():
    ergebnis = kameras.ecken_im_bild((0.0, -25.0, 1.7), (0.0, 0.0, 5.7), WUERFEL)
    assert ergebnis["passt"] is False
    assert ergebnis["max_ueberstehen"] > 1.0


def test_kamera_im_gebaeude_meldet_ecken_hinter_sich():
    """Der Fall, der ohne Sonderbehandlung eine perspektivische Division durch Null wäre."""
    ergebnis = kameras.ecken_im_bild((0.0, 0.0, 1.7), (0.0, 10.0, 5.7), WUERFEL)
    assert ergebnis["passt"] is False
    assert ergebnis["ecken_hinter_kamera"] > 0
    assert "hinter der Kamera" in ergebnis["begruendung"]


def test_entartete_basis_ist_ein_befund_und_keine_ausnahme():
    """Kamera senkrecht über dem Ziel: Welt-Z taugt nicht mehr als Referenz für „oben"."""
    ergebnis = kameras.ecken_im_bild((0.0, 0.0, 100.0), (0.0, 0.0, 5.0), WUERFEL)
    assert ergebnis["passt"] is False
    assert "entartet" in ergebnis["begruendung"]


def test_unbrauchbare_bbox_ist_ein_befund_und_keine_ausnahme():
    """Der Aufrufer sitzt hinter einer Prozessgrenze — alles kann ankommen."""
    for kaputt in (None, [], [[0, 0], [1, 1]], [[0, 0, float("nan")], [1, 1, 1]]):
        ergebnis = kameras.ecken_im_bild((0.0, -50.0, 1.7), (0.0, 0.0, 5.0), kaputt)
        assert ergebnis["passt"] is False
        assert "bbox unbrauchbar" in ergebnis["begruendung"]


def test_engerer_bildrand_verlangt_mehr_abstand():
    """Der Sicherheitsrand ist ein Regler, kein Zierrat."""
    auge, ziel = (0.0, -60.0, 1.7), (0.0, 0.0, 5.7)
    weit = kameras.ecken_im_bild(auge, ziel, WUERFEL, bildrand=1.0)
    eng = kameras.ecken_im_bild(auge, ziel, WUERFEL, bildrand=0.5)
    assert eng["max_ueberstehen"] > weit["max_ueberstehen"]


# --------------------------------------------------------------------------------------
# Rückschub
# --------------------------------------------------------------------------------------

def test_rueckschub_haelt_die_augenhoehe_konstant():
    """Die Kamera weicht horizontal aus, nie nach oben.

    Das ist die Entscheidung, die Augenhöhen-Perspektiven von Drohnenbildern trennt: Nach
    oben auszuweichen ist immer die bequemere Lösung, und darum ist sie verboten.
    """
    ergebnis = kameras.schiebe_bis_im_bild((0.0, -20.0, 1.7), (0.0, 0.0, 5.7), WUERFEL)
    assert ergebnis["auge"][2] == pytest.approx(1.7)
    assert ergebnis["vollstaendig"] is True


def test_rueckschub_endet_mit_allen_ecken_im_bild():
    ergebnis = kameras.schiebe_bis_im_bild((0.0, -20.0, 1.7), (0.0, 0.0, 5.7), WUERFEL)
    nachher = kameras.ecken_im_bild(ergebnis["auge"], (0.0, 0.0, 5.7), WUERFEL)
    assert nachher["passt"] is True


def test_rueckschub_geht_nach_hinten_nicht_nach_vorn():
    start = (0.0, -20.0, 1.7)
    ergebnis = kameras.schiebe_bis_im_bild(start, (0.0, 0.0, 5.7), WUERFEL)
    assert ergebnis["auge"][1] < start[1]


def test_schon_passende_kamera_wird_nicht_angefasst():
    start = (0.0, -200.0, 1.7)
    ergebnis = kameras.schiebe_bis_im_bild(start, (0.0, 0.0, 5.7), WUERFEL)
    assert ergebnis["auge"] == start
    assert ergebnis["durchlaeufe"] == 0


def test_erschoepfter_rueckschub_liefert_eine_gekennzeichnete_antwort():
    """Kein Verweigern — aber auch kein stilles Durchwinken.

    Ohne einen einzigen Durchlauf kann der Rückschub nicht fertig werden. Die Position
    kommt trotzdem zurück, ``vollstaendig`` ist False, und die Begründung sagt, dass sie
    nicht bestätigt ist. Eine Kamera, die knapp schneidet, ist brauchbarer als keine —
    aber sie darf nicht als geprüft gelten.
    """
    ergebnis = kameras.schiebe_bis_im_bild((0.0, -18.0, 1.7), (0.0, 0.0, 5.7), WUERFEL,
                                           max_durchlaeufe=0)
    assert ergebnis["vollstaendig"] is False
    assert "nicht bestätigt" in ergebnis["begruendung"]
    assert ergebnis["auge"] == (0.0, -18.0, 1.7)


def test_der_noetige_rueckschub_ist_gerechnet_und_nicht_getastet():
    """Die Kernaussage des Verfahrens: EIN Durchlauf genügt, nicht zwanzig.

    Ein Rückschub entlang der Blickachse erhöht die Tiefe jeder Ecke um genau diesen
    Betrag und lässt ihre seitlichen Anteile unberührt. Damit ist der nötige Betrag keine
    Schätzung, sondern eine Umstellung — und die Schleife ist nur noch da, um die leichte
    Drehung der Blickrichtung beim waagrechten Ausweichen aufzufangen.
    """
    ergebnis = kameras.schiebe_bis_im_bild((0.0, -20.0, 1.7), (0.0, 0.0, 5.7), WUERFEL)
    assert ergebnis["vollstaendig"] is True
    assert ergebnis["durchlaeufe"] <= 2


def test_der_rueckschub_schiesst_nicht_ueber_das_ziel_hinaus():
    """Zu weit weg fällt keinem Test auf — darum steht diese Schranke hier.

    Der Eckentest kennt nur „passt / passt nicht". Eine Kamera, die das Gebäude auf einen
    Fleck schrumpft, passt bestens. Genau dorthin führt die getastete Schrittweite des
    Bestands: ``(überstehen − 1) · abstand · 0.6 + 3`` erzeugt bei einer Kamera nahe der
    Fassade — wo das Überstehen zweistellig wird — einen Sprung über Kilometer.
    """
    ergebnis = kameras.schiebe_bis_im_bild((0.0, -20.0, 1.7), (0.0, 0.0, 5.7), WUERFEL)
    abstand = abs(ergebnis["auge"][1])
    # Der analytisch richtige Abstand für diesen Würfel liegt bei rund 87 m.
    assert 40.0 < abstand < 200.0, abstand


def test_der_noetige_rueckschub_stimmt_mit_dem_ueberstehen_ueberein():
    """Zwei Wege zur selben Aussage — sie müssen sich einig sein.

    Passt das Bild, ist kein Rückschub nötig; passt es nicht, ist einer nötig. Ein
    Verfahren, bei dem diese beiden Zahlen auseinanderlaufen könnten, wäre eines, dem man
    nicht ansieht, welcher der beiden Werte lügt.
    """
    for y in (-200.0, -120.0, -80.0, -40.0, -20.0):
        ergebnis = kameras.ecken_im_bild((0.0, y, 1.7), (0.0, 0.0, 5.7), WUERFEL)
        if ergebnis["passt"]:
            assert ergebnis["noetiger_rueckschub_m"] == pytest.approx(0.0, abs=1e-9)
        else:
            assert ergebnis["noetiger_rueckschub_m"] > 0.0


def test_kamera_im_gebaeude_findet_trotzdem_hinaus():
    """Der Fall ohne endliches Überstehen: der Schub braucht einen Ersatzwert."""
    ergebnis = kameras.schiebe_bis_im_bild((0.0, -2.0, 1.7), (0.0, 0.0, 5.7), WUERFEL)
    assert ergebnis["vollstaendig"] is True
    assert ergebnis["auge"][1] < -15.0


# --------------------------------------------------------------------------------------
# Heranziehen — die Schrittlogik ohne Blender
# --------------------------------------------------------------------------------------

def test_freie_sicht_bewegt_die_kamera_nicht():
    start = (0.0, -80.0, 1.7)
    ergebnis = kameras.ziehe_bis_frei(start, (0.0, 0.0, 5.7), WUERFEL, lambda a, z: True)
    assert ergebnis["auge"] == start
    assert ergebnis["frei"] is True
    assert ergebnis["schritte"] == 0
    assert ergebnis["abbruch"] == "sicht_frei"


def test_verdeckung_zieht_heran_bis_die_sicht_frei_ist():
    """Die Gegenrichtung zum Rückschub: bei einem Hindernis hilft nur näher herangehen.

    Die Sichtprüfung ist hier drei Zeilen — im Runner ein Strahlenschuss gegen den
    Depsgraph. Genau deshalb wird sie hereingereicht: Der Ablauf bleibt ohne Blender
    prüfbar, und nur der Strahlenschuss bleibt jenseits der Grenze.
    """
    def frei_ab_50m(auge, ziel):
        return math.hypot(ziel[0] - auge[0], ziel[1] - auge[1]) < 50.0

    ergebnis = kameras.ziehe_bis_frei((0.0, -80.0, 1.7), (0.0, 0.0, 5.7), WUERFEL, frei_ab_50m)
    assert ergebnis["frei"] is True
    assert ergebnis["schritte"] > 0
    assert -50.0 < ergebnis["auge"][1] < 0.0


def test_heranziehen_haelt_die_augenhoehe_konstant():
    ergebnis = kameras.ziehe_bis_frei((0.0, -80.0, 1.7), (0.0, 0.0, 5.7), WUERFEL,
                                      lambda a, z: False)
    assert ergebnis["auge"][2] == pytest.approx(1.7)


def test_heranziehen_stoppt_am_erweiterten_huellbox_rand():
    """Die Kamera darf nie in das Gebäude hinein, auch nicht für ein freies Bild."""
    ergebnis = kameras.ziehe_bis_frei((0.0, -30.0, 1.7), (0.0, 0.0, 5.7), WUERFEL,
                                      lambda a, z: False, max_schritte=100)
    assert ergebnis["frei"] is False
    assert ergebnis["abbruch"] in ("huellbox", "untergrenze")
    assert ergebnis["auge"][1] < -(15.0 + kameras.HUELLBOX_PUFFER_M)


def test_heranziehen_stoppt_an_der_untergrenze():
    """Näher als sechs Meter ist kein Gebäudebild mehr, sondern ein Fassadenausschnitt."""
    winzig = [[-0.5, -0.5, 0.0], [0.5, 0.5, 2.0]]
    ergebnis = kameras.ziehe_bis_frei((0.0, -20.0, 1.7), (0.0, 0.0, 2.0), winzig,
                                      lambda a, z: False, puffer=0.0, max_schritte=100)
    assert ergebnis["abbruch"] == "untergrenze"
    rest = math.hypot(ergebnis["auge"][0], ergebnis["auge"][1])
    assert rest >= kameras.MIN_ZIEH_ABSTAND_M


def test_erschoepfte_schritte_werden_als_solche_gemeldet():
    ergebnis = kameras.ziehe_bis_frei((0.0, -200.0, 1.7), (0.0, 0.0, 5.7), WUERFEL,
                                      lambda a, z: False, max_schritte=2)
    assert ergebnis["frei"] is False
    assert ergebnis["abbruch"] == "schritte_erschoepft"
    assert ergebnis["schritte"] == 2


# --------------------------------------------------------------------------------------
# Der ganze Satz
# --------------------------------------------------------------------------------------

def test_zwoelf_kameras_und_alle_sehen_das_gebaeude():
    """Die Gesamtprobe: zwölf Richtungen, zwölf vollständige Eckentests.

    Der Bestand hat für diesen Lauf **keinen Beleg** — der Stress-Test dort bestätigt,
    dass der Knoten fehlerfrei registriert, nicht dass zwölf Bilder entstanden sind. Dass
    etwas registriert ist, ist kein Beleg dafür, dass es je gut aussah.
    """
    satz = kameras.kamerasatz(WUERFEL)
    assert len(satz["kameras"]) == 12
    assert satz["unvollstaendig"] == []
    for kamera in satz["kameras"]:
        pruefung = kameras.ecken_im_bild(kamera["auge"], kamera["blick_auf"], WUERFEL)
        assert pruefung["passt"] is True, f"{kamera['kuerzel']}: {pruefung['begruendung']}"


def test_alle_kameras_stehen_auf_augenhoehe():
    satz = kameras.kamerasatz(WUERFEL)
    for kamera in satz["kameras"]:
        assert kamera["auge"][2] == pytest.approx(kameras.AUGENHOEHE_M)


def test_die_augenhoehe_zaehlt_ab_gelaende_und_nicht_ab_der_nulllinie():
    """Der Test, der meine erste Entscheidung widerlegt hat — und darum hier bleibt.

    Der Bestand trägt drei Augenhöhen: 1.70 absolut, 1.70 über ``zmin``, 1.65. Zuerst
    stand hier **absolut**, mit dem Argument, der Betrachter stehe auf dem Gelände und
    nicht auf der Hüllbox-Unterkante. Das Argument stimmt, die Folgerung war falsch:
    „Absolut" heisst über ``z = 0``, und das ist nur dort das Gelände, wo das Modell
    zufällig auf Meereshöhe sitzt.

    Ein Bauwerk mit Fuss auf 400 m über Meer bekam damit eine Kamera auf 1.70 m —
    **400 Meter unter dem Erdgeschoss**. Nicht an einem Bild aufgefallen, sondern an
    dieser Zeile.
    """
    hoch_gelegen = [[-15.0, -15.0, 400.0], [15.0, 15.0, 420.0]]
    for kamera in kameras.kamerasatz(hoch_gelegen)["kameras"]:
        assert kamera["auge"][2] == pytest.approx(400.0 + 1.70)


def test_am_boden_liegende_bauten_bleiben_unveraendert():
    """Die Gegenprobe: Wo der Fuss auf null liegt, ändert der neue Bezug nichts."""
    for kamera in kameras.kamerasatz(WUERFEL)["kameras"]:
        assert kamera["auge"][2] == pytest.approx(1.70)


def test_ein_untergeschoss_laesst_sich_angeben():
    """Der Einwand, der für „absolut" sprach — jetzt als Parameter statt als Annahme.

    Reicht die Hüllbox in ein Untergeschoss hinunter, ist ihre Unterkante nicht das
    Gelände. Ohne Angabe stünde die Kamera im Keller; mit ``gelaende_z`` steht sie
    draussen. Das ist die ehrliche Form: Die Bibliothek rät nicht, sie fragt.
    """
    mit_keller = [[-15.0, -15.0, -6.0], [15.0, 15.0, 20.0]]
    ohne_angabe = kameras.kamerasatz(mit_keller, kuerzel=["n"])["kameras"][0]
    assert ohne_angabe["auge"][2] == pytest.approx(-6.0 + 1.70)      # im Keller

    mit_angabe = kameras.kamerasatz(mit_keller, kuerzel=["n"],
                                    gelaende_z=0.0)["kameras"][0]
    assert mit_angabe["auge"][2] == pytest.approx(1.70)              # draussen


def test_der_gelaendestand_steht_im_ergebnis():
    """Wer ein Bild später schief findet, soll den Bezugspunkt nachlesen können."""
    satz = kameras.kamerasatz([[-15.0, -15.0, 400.0], [15.0, 15.0, 420.0]])
    assert satz["gelaende_z"] == pytest.approx(400.0)
    assert kameras.kamerasatz(WUERFEL, gelaende_z=7.5)["gelaende_z"] == pytest.approx(7.5)


def test_der_fuellgrad_wird_an_der_nahen_fassade_gemessen():
    """Die Probe darauf, dass das das richtige Mass ist.

    Der Abstand wird zur Gebäudemitte gerechnet, die zugewandte Fassade steht um die halbe
    Bautiefe näher. In der Mitte gemessen erschiene ein 60-m-Riegel von der Schmalseite
    winzig, obwohl seine Stirnfassade den Rahmen füllt.

    Das Mass ist richtig, wenn bei Gebäudemassen genau der ANGEFORDERTE Deckungsgrad
    herauskommt — und genau das tut es, über vier sehr verschiedene Baukörper.
    """
    for bbox in ([[-15.0, -15.0, 0.0], [15.0, 15.0, 20.0]],
                 [[-30.0, -6.0, 0.0], [30.0, 6.0, 10.0]],
                 [[-10.0, -10.0, 0.0], [10.0, 10.0, 100.0]],
                 [[-15.0, -15.0, 400.0], [15.0, 15.0, 415.0]]):
        for kamera in kameras.kamerasatz(bbox)["kameras"]:
            assert kamera["fuellgrad"] == pytest.approx(kameras.DECKUNGSGRAD, abs=0.03), \
                (bbox, kamera["kuerzel"], kamera["fuellgrad"])


def test_frontale_stehen_wo_ihr_name_sagt():
    """``n`` heisst nördlich des Gebäudes — also positives Y."""
    satz = kameras.kamerasatz(WUERFEL, kuerzel=["n", "e", "s", "w"])
    nach_kuerzel = {k["kuerzel"]: k["auge"] for k in satz["kameras"]}
    assert nach_kuerzel["n"][1] > 15.0
    assert nach_kuerzel["s"][1] < -15.0
    assert nach_kuerzel["e"][0] > 15.0
    assert nach_kuerzel["w"][0] < -15.0


def test_frontale_sind_nicht_exakt_mittig():
    """Eine exakt symmetrische Frontale ist bildlich tot — darum der seitliche Versatz."""
    satz = kameras.kamerasatz(WUERFEL, kuerzel=["n"])
    auge = satz["kameras"][0]["auge"]
    assert auge[0] != pytest.approx(0.0, abs=1e-6)


def test_diagonalen_bekommen_keinen_zusaetzlichen_versatz():
    """Bei den Diagonalen erledigt der Bias, wofür bei den Frontalen der Versatz da ist."""
    satz = kameras.kamerasatz(WUERFEL, kuerzel=["nNE"], bias_grad=45.0)
    auge = satz["kameras"][0]["auge"]
    assert auge[0] == pytest.approx(auge[1], rel=1e-6)


def test_blickziel_liegt_ueber_der_augenhoehe():
    """Die Kamera kippt leicht nach oben, das Gebäude sitzt tiefer im Bild.

    Der Modus steht hier ausdrücklich: Seit dem 23.08.2026 ist ``MODUS_SHIFT`` die
    Vorgabe, und dort liegt ``blick_auf`` auf Augenhöhe — der Höhenunterschied wandert
    in den Shift. Die Regel, die dieser Test festhält, gilt trotzdem weiter: Sie ist es,
    aus der der Shift gerechnet wird.
    """
    satz = kameras.kamerasatz(WUERFEL, kuerzel=["n"], modus=kameras.MODUS_GEKIPPT)
    kamera = satz["kameras"][0]
    assert kamera["blick_auf"][2] > kamera["auge"][2]
    assert kamera["blick_auf"][2] == pytest.approx(1.70 + 20.0 * kameras.ZIEL_ANTEIL_HOEHE)


def test_langer_riegel_wird_von_der_schmalseite_naeher_aufgenommen():
    """Die richtungsabhängige Breite als sichtbare Folge: nicht jede Seite braucht gleich viel.

    Von Norden ist der Riegel 60 m breit, von Osten 12 m. Wäre die Diagonale massgebend —
    wie im Bestand —, stünden beide Kameras gleich weit weg.
    """
    riegel = [[-30.0, -6.0, 0.0], [30.0, 6.0, 10.0]]
    satz = kameras.kamerasatz(riegel, kuerzel=["n", "e"])
    nach_kuerzel = {k["kuerzel"]: k for k in satz["kameras"]}
    assert (nach_kuerzel["n"]["abstand_analytisch_m"]
            > nach_kuerzel["e"]["abstand_analytisch_m"])


def test_kamerasatz_meldet_woran_der_abstand_hing():
    """Wer einen Abstand für falsch hält, soll nachsehen können, welcher Kandidat ihn setzte."""
    satz = kameras.kamerasatz(WUERFEL, kuerzel=["n"])
    assert satz["kameras"][0]["massgebend"] in ("breite", "hoehe", "untergrenze")


def test_kamerasatz_haelt_die_reihenfolge_ein():
    satz = kameras.kamerasatz(WUERFEL)
    assert tuple(k["kuerzel"] for k in satz["kameras"]) == kameras.RICHTUNGSFOLGE


def test_unbekanntes_kuerzel_wird_abgewiesen():
    with pytest.raises(ValueError, match="Unbekannte Richtungskürzel"):
        kameras.kamerasatz(WUERFEL, kuerzel=["n", "nordwestlich"])


def test_unbrauchbare_bbox_wirft_mit_erklaerung():
    with pytest.raises(ValueError, match="bbox unbrauchbar"):
        kameras.kamerasatz([[0, 0, 0]])


@pytest.mark.parametrize("bbox", [
    [[-15.0, -15.0, 0.0], [15.0, 15.0, 20.0]],       # Kubus
    [[-30.0, -6.0, 0.0], [30.0, 6.0, 10.0]],         # langer Riegel
    [[-10.0, -10.0, 0.0], [10.0, 10.0, 100.0]],      # Turm
    [[-1.5, -1.5, 0.0], [1.5, 1.5, 2.5]],            # Gartenhaus
    [[-60.0, -40.0, 400.0], [60.0, 40.0, 415.0]],    # weit über Meer, flach und breit
])
def test_der_satz_haelt_ueber_die_ganze_bandbreite(bbox):
    """Vier Gebäudetypen und eine Höhenlage — jedes Mal zwölf brauchbare Kameras."""
    satz = kameras.kamerasatz(bbox)
    assert satz["unvollstaendig"] == [], satz["unvollstaendig"]
    assert len(satz["kameras"]) == 12


@pytest.mark.parametrize("bias", [30.0, 35.0, 45.0])
def test_der_satz_haelt_ueber_die_bias_spanne(bias):
    satz = kameras.kamerasatz(WUERFEL, bias_grad=bias)
    assert satz["unvollstaendig"] == []


@pytest.mark.parametrize("verhaeltnis", [16 / 9, 4 / 3, 1.0, 2.39])
def test_der_satz_haelt_ueber_die_gaengigen_seitenverhaeltnisse(verhaeltnis):
    """Ein 1:1-Bild braucht einen anderen Abstand als ein Cinemascope-Bild.

    Genau das kann die Hauptfundstelle des Bestands nicht — dort steht die Sensorhöhe fest.
    """
    satz = kameras.kamerasatz(WUERFEL, seitenverhaeltnis=verhaeltnis)
    assert satz["unvollstaendig"] == []


def test_kein_bpy_im_modul():
    """Regel 2, an der Stelle, an der die Versuchung am grössten war.

    Die Vorlage hat ``import bpy`` auf Modulebene stehen, obwohl zwei ihrer vier
    Funktionen es nicht brauchen. Genau dieser Kopf macht dort die halbe Datei unprüfbar.
    """
    import inspect
    quelle = inspect.getsource(kameras)
    baum = __import__("ast").parse(quelle)
    for knoten in __import__("ast").walk(baum):
        if isinstance(knoten, __import__("ast").Import):
            for name in knoten.names:
                assert name.name.split(".")[0] != "bpy"
        elif isinstance(knoten, __import__("ast").ImportFrom):
            assert (knoten.module or "").split(".")[0] != "bpy"


# --------------------------------------------------------------------------------------
# Das Blickziel darf das Bauwerk nicht verlassen
#
# Am echten Blender-Lauf aufgefallen (18.08.2026): Bei einem 2 m hohen Körper lag das
# Blickziel auf 2.1 m — ÜBER dem Dach. Die Kamera schaute darüber hinweg, und nur 2.4 %
# der Bildpunkte trugen Tiefe. Die Vorlage aus dem alten Bestand hat dieselbe Lücke; sie
# ist dort nie aufgefallen, weil nur echte Gebäude gerendert wurden.
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("bbox", [
    [[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]],              # niedriger als der Betrachter
    [[0.0, 0.0, 0.0], [3.0, 3.0, 2.5]],              # Gartenhaus
    [[-15.0, -15.0, 0.0], [15.0, 15.0, 20.0]],       # Wohnhaus
    [[-10.0, -10.0, 0.0], [10.0, 10.0, 100.0]],      # Turm
    [[-15.0, -15.0, 400.0], [15.0, 15.0, 404.0]],    # flach und hoch gelegen
])
def test_das_blickziel_liegt_immer_im_bauwerk(bbox):
    """Die Regel, die den Fehler unmöglich macht — über die ganze zugelassene Spanne."""
    fuss, dach = bbox[0][2], bbox[1][2]
    for kamera in kameras.kamerasatz(bbox)["kameras"]:
        assert fuss <= kamera["blick_auf"][2] <= dach, (kamera["kuerzel"], kamera["blick_auf"])


def test_bei_gebaeudemassen_aendert_die_schranke_nichts():
    """Sie greift genau dort, wo sie soll — und sonst nirgends.

    Bei 20 m Höhe liegt das ungeschränkte Ziel bei 5.7 m und die Schranke bei 10 m; es
    gewinnt weiterhin das erste. Eine Schranke, die auch den Normalfall verschöbe, hätte
    jede bisher gemessene Tiefenkarte mitverschoben.
    """
    satz = kameras.kamerasatz(WUERFEL, kuerzel=["n"], modus=kameras.MODUS_GEKIPPT)
    ungeschraenkt = kameras.AUGENHOEHE_M + 20.0 * kameras.ZIEL_ANTEIL_HOEHE
    assert satz["kameras"][0]["blick_auf"][2] == pytest.approx(ungeschraenkt)


def test_bei_einem_niedrigen_bau_schaut_die_kamera_leicht_nach_unten():
    """Und das ist richtig so — der Betrachter ist höher als das Dach."""
    niedrig = [[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]]
    kamera = kameras.kamerasatz(niedrig, kuerzel=["n"],
                                modus=kameras.MODUS_GEKIPPT)["kameras"][0]
    assert kamera["blick_auf"][2] < kamera["auge"][2]
    assert kamera["blick_auf"][2] <= 2.0


# --------------------------------------------------------------------------------------
# Der Füllgrad — die Frage, die der Eckentest nicht stellt
# --------------------------------------------------------------------------------------

def test_der_eckentest_allein_bemerkt_ein_winziges_bauwerk_nicht():
    """Zu klein fällt keiner Prüfung auf, die nur nach „passt es hinein" fragt.

    Genau darum steht der Füllgrad daneben: Ein Bild, auf dem das Bauwerk ein Fleck ist,
    sieht wie ein Fehler des Bildmodells aus — die Ursache liegt in der Kamera, und dort
    würde niemand suchen.
    """
    # 1,5 m und nicht 2 m: Bei der Vorgabe-Brennweite von 35 mm füllt ein 2-m-Körper
    # aus dem Mindestabstand bereits 34,6 % und liegt damit über der Warnschwelle.
    # Die Aussage des Tests hängt nicht an der Grösse, sondern daran, dass es
    # überhaupt einen Bereich gibt, in dem der Eckentest schweigt und der Füllgrad
    # nicht — und den gibt es weiterhin.
    winzig = [[0.0, 0.0, 0.0], [1.5, 1.5, 1.5]]
    satz = kameras.kamerasatz(winzig, kuerzel=["n"])
    assert satz["unvollstaendig"] == []          # der Eckentest ist zufrieden …
    assert satz["warnungen"]                     # … der Füllgrad nicht
    assert satz["kameras"][0]["fuellgrad"] < kameras.DECKUNGSGRAD


@pytest.mark.parametrize("bbox", [
    [[-15.0, -15.0, 0.0], [15.0, 15.0, 20.0]],       # Kubus, die Höhe führt
    [[-30.0, -6.0, 0.0], [30.0, 6.0, 10.0]],         # Riegel, die Breite führt
    [[-10.0, -10.0, 0.0], [10.0, 10.0, 100.0]],      # Turm
])
def test_bei_gebaeudemassen_wird_der_deckungsgrad_annaehernd_erreicht(bbox):
    """Die Probe darauf, dass die Rechnung tut, was sie verspricht.

    ``gelaende_z=0.0`` steht hier seit dem 01.09.2026, und es ist keine Beruhigung der
    Zusicherung, sondern eine Verschaerfung: Alle drei Boxen haben ihren Fuss auf z = 0,
    die Angabe ist also die *wahre* Gelaendehoehe und keine Ausrede. Seit `kamerasatz`
    den unbekannten Gelaendestand meldet, prueft die leere Warnungsliste damit **zwei**
    Dinge auf einmal — dass die Rahmung sitzt, und dass die neue Warnung wieder
    verschwindet, sobald der Bezugspunkt bekannt ist. Ohne die Angabe waere sie hier ein
    stehender Vorbehalt und nichts ueber den Deckungsgrad.
    """
    satz = kameras.kamerasatz(bbox, gelaende_z=0.0)
    assert satz["warnungen"] == (), satz["warnungen"]
    for kamera in satz["kameras"]:
        assert kamera["fuellgrad"] > kameras.DECKUNGSGRAD * kameras.FUELLGRAD_WARNSCHWELLE


def test_der_fuellgrad_wird_in_beiden_richtungen_gemessen():
    """Der Fehler, der hier zuerst stand: nur die Breite zu messen.

    Der Deckungsgrad wird auf Breite und Höhe getrennt angesetzt, und der grössere Bedarf
    gewinnt. Bei einem hohen Bau im 16:9-Rahmen ist das die Höhe — nur die Breite zu
    messen ergäbe eine Warnung für jedes Hochhaus, obwohl der Rahmen vertikal gut gefüllt
    ist. Ein 30 × 30 × 20 m Kubus meldete so 27 % Füllung bei 46 % Höhenfüllung.
    """
    kamera = kameras.kamerasatz(WUERFEL, kuerzel=["n"])["kameras"][0]
    assert kamera["fuellgrad_hoehe"] > kamera["fuellgrad_breite"]
    assert kamera["fuellgrad"] == pytest.approx(kamera["fuellgrad_hoehe"])

    riegel = kameras.kamerasatz([[-30.0, -6.0, 0.0], [30.0, 6.0, 10.0]],
                                kuerzel=["n"])["kameras"][0]
    assert riegel["fuellgrad_breite"] > riegel["fuellgrad_hoehe"]
    assert riegel["fuellgrad"] == pytest.approx(riegel["fuellgrad_breite"])


def test_der_abstand_ist_der_endgueltige_nicht_der_gerechnete():
    """Der Eckentest kann noch zurückgeschoben haben — dann gilt die neue Zahl."""
    kamera = kameras.kamerasatz(WUERFEL, kuerzel=["n"])["kameras"][0]
    auge, ziel = kamera["auge"], kamera["blick_auf"]
    assert kamera["abstand_m"] == pytest.approx(
        math.hypot(ziel[0] - auge[0], ziel[1] - auge[1]))


def test_die_warnung_nennt_die_ursache_und_nicht_nur_die_zahl():
    """Ein Verdacht kostet einen Menschen, der nachsieht; eine Diagnose sagt ihm, wo."""
    # 1,5 m und nicht 2 m: Bei der Vorgabe-Brennweite von 35 mm füllt ein 2-m-Körper
    # aus dem Mindestabstand bereits 34,6 % und liegt damit über der Warnschwelle.
    # Die Aussage des Tests hängt nicht an der Grösse, sondern daran, dass es
    # überhaupt einen Bereich gibt, in dem der Eckentest schweigt und der Füllgrad
    # nicht — und den gibt es weiterhin.
    winzig = [[0.0, 0.0, 0.0], [1.5, 1.5, 1.5]]
    text = " ".join(kameras.kamerasatz(winzig, kuerzel=["n"])["warnungen"])
    assert "füllt nur" in text
    assert "Gebäudemasse" in text or "zurückgeschoben" in text
    assert "die Ursache liegt hier" in text


# --------------------------------------------------------------------------------------
# Der Flächenanteil — was der Füllgrad nicht sagt
#
# Am 19.08.2026 an ZWÖLF echten Blender-Läufen gemessen (40 × 26 × 15 m Baukörper,
# quadratischer Rahmen, 256 px):
#
#     gemeldeter Füllgrad   0.548 – 0.550   bei ALLEN ZWÖLF, praktisch konstant
#     tatsächliche Fläche   3.3 % – 9.6 %   also Faktor DREI Unterschied
#
# Die Zahl war richtig und sagte nichts. Ein breiter, niedriger Bau kann einen
# quadratischen Rahmen nicht füllen: Erfüllt er die Breite, ist die Höhe zwangsläufig leer.
# --------------------------------------------------------------------------------------

#: Der Baukörper der Messung — Sockel, Hauptkörper, Attika, Anbau.
GEMESSENES_HAUS = [[-10.0, 0.0, 0.0], [30.0, 26.0, 15.0]]

#: Der Deckungsgrad, bei dem die zwölf Renders unten entstanden sind.
#:
#: **Die Messung gehört an ihn.** Am 25.08.2026 ist die Vorgabe auf 0.70 gestiegen
#: (Owner-Entscheid); die Zahlen unten stammen von vorher. Sie mit der neuen Vorgabe zu
#: vergleichen hiesse, eine Messung gegen einen Aufbau zu halten, in dem sie nie
#: stattgefunden hat — derselbe Fehler wie ein Rauschboden ohne seine Maskenlage.
#:
#: **Eine Neumessung bei 0.70 steht aus** und gehört in die nächste Grundmessung.
GEMESSEN_BEI_DECKUNGSGRAD = 0.55

#: Was die zwölf Renders wirklich zeigten, Kürzel → Flächenanteil.
GEMESSENE_FLAECHE = {
    "n": 0.0654, "e": 0.0961, "s": 0.0803, "w": 0.0756,
    "nNE": 0.0421, "eEN": 0.0447, "eES": 0.0449, "sSE": 0.0457,
    "sSW": 0.0440, "wWS": 0.0410, "wWN": 0.0327, "nNW": 0.0343,
}


def test_der_fuellgrad_ist_ueber_alle_zwoelf_praktisch_konstant():
    """Die eine Hälfte des Befunds: Die Zahl unterscheidet die zwölf Ansichten nicht.

    Sie ist damit nicht falsch — sie beantwortet die Frage „wurde der Deckungsgrad
    eingehalten", und die Antwort ist zwölfmal ja. Sie beantwortet nur nicht die Frage,
    die ein Mensch stellt.
    """
    satz = kameras.kamerasatz(GEMESSENES_HAUS, seitenverhaeltnis=1.0,
                              deckungsgrad=GEMESSEN_BEI_DECKUNGSGRAD)
    werte = [k["fuellgrad"] for k in satz["kameras"]]
    assert max(werte) - min(werte) < 0.01, werte


def test_der_flaechenanteil_unterscheidet_sie_deutlich():
    """Die andere Hälfte: Dieselben zwölf Kameras, Faktor zwei bis drei Unterschied.

    Gerechnet am MESSSTANDORT — siehe `_flaechenanteil_am_messstandort`. Die zwölf Zahlen,
    gegen die hier geprüft wird, stammen von der Kamera vor dem 01.09.2026.
    """
    satz = kameras.kamerasatz(GEMESSENES_HAUS, seitenverhaeltnis=1.0,
                              deckungsgrad=GEMESSEN_BEI_DECKUNGSGRAD)
    werte = [_flaechenanteil_am_messstandort(k) for k in satz["kameras"]]
    assert max(werte) / min(werte) > 2.0, werte


#: Der Faktor, um den die Kamera am 01.09.2026 NÄHER gerückt ist.
#:
#: Bis dahin setzte `abstand_aus_bildwinkel` die seitlichen Silhouettenkanten auf die
#: Vorderkante (`+ tiefe/2`); wirklich liegen sie bei `seitenecken_tiefe_m`. Die zwölf
#: Messungen unten stammen aus Blender-Läufen VOR dieser Korrektur. An der heutigen, näheren
#: Kamera gerechnet wäre das Bauwerk grösser im Bild — ohne dass sich am Bauwerk etwas
#: geändert hätte. Wer sie so vergliche, prüfte den Formelwechsel und nicht mehr den
#: Baukörper. Der Vergleich gehört an den Standort, an dem gemessen wurde.
#:
#: Zurückgeschoben wird auf der Blickachse, Blickziel und Bildversatz bleiben, wie sie sind —
#: nur der Abstand ist es, der sich geändert hat.
def _flaechenanteil_am_messstandort(kamera):
    """`flaechenanteil` derselben Kamera, aber am historischen (weiteren) Abstand."""
    masse = tuple(abs(GEMESSENES_HAUS[1][i] - GEMESSENES_HAUS[0][i]) for i in range(3))
    azimut = kamera["azimut_grad"]
    hfov, vfov = kameras.bildwinkel(kamera["brennweite_mm"], seitenverhaeltnis=1.0)
    breite = kameras.sichtbare_breite(masse, azimut)
    tiefe = kameras.sichtbare_tiefe(masse, azimut)
    ziel_ueber_fuss = kamera["blick_auf"][2] - min(GEMESSENES_HAUS[0][2], GEMESSENES_HAUS[1][2])
    halbe = max(max(0.0, masse[2] - ziel_ueber_fuss), max(0.0, ziel_ueber_fuss))
    d = GEMESSEN_BEI_DECKUNGSGRAD
    alt = max((breite / 2.0) / math.tan(hfov / 2.0) / d + tiefe / 2.0,
              halbe / math.tan(vfov / 2.0) / d + tiefe / 2.0,
              tiefe / 2.0 + kameras.WANDABSTAND_M)
    auge, blick = kamera["auge"], kamera["blick_auf"]
    jetzt = math.hypot(auge[0] - blick[0], auge[1] - blick[1])
    f = alt / jetzt
    zurueck = (blick[0] + (auge[0] - blick[0]) * f,
               blick[1] + (auge[1] - blick[1]) * f,
               auge[2])
    return kameras.flaechenanteil(zurueck, blick, GEMESSENES_HAUS,
                                  brennweite_mm=kamera["brennweite_mm"],
                                  seitenverhaeltnis=1.0, shift_mm=kamera["shift_mm"])


@pytest.mark.parametrize("kuerzel,gemessen", sorted(GEMESSENE_FLAECHE.items()))
def test_die_rechnung_ist_eine_obergrenze_der_messung(kuerzel, gemessen):
    """Gegen zwölf echte Blender-Läufe geprüft — nicht gegen eine Erwartung.

    Die Hüllbox ist voller als das Gebäude in ihr, die Rechnung muss also **über** dem
    Gemessenen liegen. Läge sie darunter, wäre sie schlicht falsch. Und sie darf auch
    nicht beliebig weit darüber liegen, sonst wäre sie als Auskunft wertlos: Der
    gemessene Baukörper ist ein gestufter Bau, der rund die Hälfte bis zwei Drittel
    seiner Hüllbox füllt.
    """
    kamera = kameras.kamerasatz(GEMESSENES_HAUS, kuerzel=[kuerzel],
                                seitenverhaeltnis=1.0,
                                deckungsgrad=GEMESSEN_BEI_DECKUNGSGRAD)["kameras"][0]
    gerechnet = _flaechenanteil_am_messstandort(kamera)
    assert gerechnet >= gemessen, f"unter dem Gemessenen — die Rechnung ist falsch"
    assert gerechnet <= gemessen * 2.5, f"{gerechnet:.3f} gegen {gemessen:.3f} — zu grob"


def test_die_rangfolge_stimmt_mit_der_messung_ueberein():
    """Eine Obergrenze nützt nur, wenn sie die Ansichten richtig ORDNET.

    Die Frontalen zeigen mehr als die Diagonalen — gerechnet wie gemessen.
    """
    satz = kameras.kamerasatz(GEMESSENES_HAUS, seitenverhaeltnis=1.0,
                              deckungsgrad=GEMESSEN_BEI_DECKUNGSGRAD)
    gerechnet = {k["kuerzel"]: _flaechenanteil_am_messstandort(k) for k in satz["kameras"]}
    frontal = [gerechnet[k] for k in ("n", "e", "s", "w")]
    diagonal = [gerechnet[k] for k in ("nNE", "eES", "sSW", "wWN")]
    assert min(frontal) > max(diagonal)
    gemessen_frontal = [GEMESSENE_FLAECHE[k] for k in ("n", "e", "s", "w")]
    gemessen_diagonal = [GEMESSENE_FLAECHE[k] for k in ("nNE", "eES", "sSW", "wWN")]
    assert min(gemessen_frontal) > max(gemessen_diagonal)


def test_ein_breitbild_zeigt_denselben_bau_groesser():
    """Die Folgerung aus dem Befund: Es ist eine Frage des FORMATS, nicht des Abstands.

    Ein 40 m breiter, 15 m hoher Bau passt nicht in ein Quadrat. Im Breitbild nimmt
    derselbe Bau bei demselben Deckungsgrad deutlich mehr Fläche ein — weil weniger
    Rahmen leer bleibt.
    """
    quadrat = kameras.kamerasatz(GEMESSENES_HAUS, kuerzel=["n"],
                                 seitenverhaeltnis=1.0)["kameras"][0]
    breit = kameras.kamerasatz(GEMESSENES_HAUS, kuerzel=["n"],
                               seitenverhaeltnis=16 / 9)["kameras"][0]
    assert breit["flaechenanteil"] > quadrat["flaechenanteil"]


def test_hinter_der_kamera_ist_keine_flaeche():
    """Eine Projektion hinter der Linse ist keine Fläche, sondern ein Befund."""
    assert kameras.flaechenanteil((0.0, 0.0, 1.7), (0.0, 10.0, 5.0), WUERFEL) == 0.0


def test_die_huellenflaeche_rechnet_bekannte_figuren_richtig():
    """Selbstprobe der Hülle — ein Test, der nichts prüft, bewacht nichts."""
    quadrat = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    assert kameras._huellen_flaeche(quadrat) == pytest.approx(1.0)
    # Ein Punkt innen darf nichts ändern.
    assert kameras._huellen_flaeche(quadrat + [(0.5, 0.5)]) == pytest.approx(1.0)
    assert kameras._huellen_flaeche([(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]) == pytest.approx(0.5)
    assert kameras._huellen_flaeche([(0.0, 0.0), (1.0, 1.0)]) == 0.0      # eine Linie


# ══════════════════════════════════════════════════════════════════════════════════════
# Der Breitenabstand — 01.09.2026
# ══════════════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("azimut", [0.0, 20.0, 35.0, 55.0, 70.0, 90.0, 125.0, 215.0, 305.0])
def test_die_breitenecken_liegen_nicht_auf_der_vorderkante(azimut):
    """Gegen die GEOMETRIE geprüft, nicht gegen die Formel.

    Die seitlichen Silhouettenkanten eines achsparallelen Grundrisses sind zwei einander
    diagonal gegenüberliegende Ecken. Hier werden sie aus den vier Grundrissecken
    ausgerechnet und ihr Tiefenversatz mit `seitenecken_tiefe_m` verglichen. Die Probe kann
    widersprechen: Läge der Versatz wirklich bei `tiefe/2`, fiele sie um.
    """
    dx, dy, dz = 103.84, 57.15, 27.10
    r = kameras.abstand_aus_bildwinkel((dx, dy, dz), azimut, hoehe_ueber_grund=1.7)
    a = math.radians(azimut)
    blick = (math.sin(a), math.cos(a))            # Blickrichtung, s. `sichtbare_tiefe`
    quer = (math.cos(a), -math.sin(a))            # dazu senkrecht, s. `sichtbare_breite`
    ecken = [(sx * dx / 2.0, sy * dy / 2.0) for sx in (-1, 1) for sy in (-1, 1)]
    seitlich = [(p[0] * quer[0] + p[1] * quer[1], p[0] * blick[0] + p[1] * blick[1]) for p in ecken]
    aussen = max(seitlich)                         # die Ecke mit dem grössten Querabstand
    assert aussen[0] == pytest.approx(r["breite_m"] / 2.0, abs=1e-9)
    assert abs(aussen[1]) == pytest.approx(r["seitenecken_tiefe_m"], abs=1e-9)


@pytest.mark.parametrize("azimut", [0.0, 35.0, 55.0, 90.0, 125.0])
@pytest.mark.parametrize("deckung", [0.5, 0.7, 0.9])
def test_der_breitenabstand_fuellt_wirklich_den_deckungsgrad(azimut, deckung):
    """Ein flacher, breiter Bau: die Breite ist massgebend, und sie muss stimmen.

    Bei `abstand_breite_m` muss die projizierte Silhouettenbreite genau `deckung` der
    Bildbreite einnehmen — projiziert wird über beide Breitenecken einzeln, jede an ihrer
    eigenen Tiefe. Die alte Formel füllte hier nur rund die Hälfte.
    """
    masse = (80.0, 44.0, 6.0)
    hfov, _ = kameras.bildwinkel(kameras.BRENNWEITE_MM, seitenverhaeltnis=16 / 9)
    r = kameras.abstand_aus_bildwinkel(masse, azimut, hoehe_ueber_grund=1.7, deckungsgrad=deckung)
    R, breite = r["abstand_breite_m"], r["breite_m"]
    ecken = kameras._grundrissecken(masse, azimut)
    bildbreite = 2.0 * math.tan(hfov / 2.0)
    assert kameras.silhouettenbreite(ecken, R) / bildbreite == pytest.approx(deckung, abs=1e-9)

    # Und die alte Formel füllte NIE mehr, meist weniger — das ist der Befund, nicht eine
    # Geschmacksfrage. Bei der Frontalen sind beide gleich, dort war sie schon richtig.
    alt = (breite / 2.0) / math.tan(hfov / 2.0) / deckung + r["tiefe_m"] / 2.0
    assert alt >= R - 1e-9
    assert kameras.silhouettenbreite(ecken, alt) / bildbreite <= deckung + 1e-12
    frontal = min(azimut % 90.0, 90.0 - azimut % 90.0) < 1e-9
    assert (alt == pytest.approx(R)) if frontal else (alt > R + 1.0)


def test_die_hoehe_bleibt_an_der_vorderkante_gerahmt():
    """Die Gegenrichtung: An der HÖHE ändert sich nichts, und das ist richtig so.

    Oben und unten begrenzt dieselbe zugewandte Kante das Bild. Ihr Versatz IST die halbe
    Tiefe. Bei einem hohen, schmalen Bau muss die Höhe massgebend bleiben und der
    Höhenfüllgrad genau den Deckungsgrad treffen.
    """
    masse = (18.0, 16.0, 60.0)
    _, vfov = kameras.bildwinkel(kameras.BRENNWEITE_MM, seitenverhaeltnis=16 / 9)
    for azimut in (0.0, 35.0, 55.0, 90.0):
        r = kameras.abstand_aus_bildwinkel(masse, azimut, hoehe_ueber_grund=1.7, deckungsgrad=0.7)
        assert r["massgebend"] == "hoehe"
        nah = r["abstand_hoehe_m"] - r["tiefe_m"] / 2.0
        anteil = (2.0 * r["halbe_hoehe_m"]) / (2.0 * math.tan(vfov / 2.0) * nah)
        assert anteil == pytest.approx(0.7, abs=1e-9)
        # unverändert gegenüber der Fassung vor dem 01.09.2026
        assert r["abstand_hoehe_m"] == pytest.approx(
            r["halbe_hoehe_m"] / math.tan(vfov / 2.0) / 0.7 + r["tiefe_m"] / 2.0)
