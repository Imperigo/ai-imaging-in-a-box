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
    erwartet = 15.0 / math.tan(hfov / 2.0) + 0.5

    ergebnis = kameras.abstand_aus_bildwinkel(
        masse, 0.0, hoehe_ueber_grund=1.7, brennweite_mm=28.0, deckungsgrad=1.0)
    assert ergebnis["massgebend"] == "breite"
    assert ergebnis["abstand_m"] == pytest.approx(erwartet)


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


def test_augenhoehe_ist_absolut_und_nicht_ueber_dem_gebaeudefuss():
    """Der Vertrag aus dem Modulkopf, als Test.

    Der Bestand trägt drei Augenhöhen — 1.70 absolut, 1.70 über ``zmin``, 1.65. Bei einem
    Gebäude, dessen Fuss auf 400 m über Meer liegt, sind die ersten beiden 400 m
    auseinander. Hier gilt: absolut.
    """
    hoch_gelegen = [[-15.0, -15.0, 400.0], [15.0, 15.0, 420.0]]
    satz = kameras.kamerasatz(hoch_gelegen)
    for kamera in satz["kameras"]:
        assert kamera["auge"][2] == pytest.approx(1.70)


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
    """Die Kamera kippt leicht nach oben, das Gebäude sitzt tiefer im Bild."""
    satz = kameras.kamerasatz(WUERFEL, kuerzel=["n"])
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
