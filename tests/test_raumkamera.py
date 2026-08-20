"""``aiimaging.raumkamera`` — wo eine Kamera IM Raum steht.

Die Testräume sind **nicht erfunden**: Es sind die beiden Räume, die
``tools/make_test_ifc.py --raeume`` erzeugt und die der Raumleser am 22.08.2026
end-to-end geliefert hat. Der eine ist L-förmig (mit einspringender Ecke), der andere
rechteckig — und die Flächen 26,62 m² und 5,94 m² addieren sich exakt zum umschliessenden
Rechteck 7,40 × 4,40 m. Wer die Zahlen hier ändert, ändert damit die Bindung an den
Runner, und dann prüft diese Datei nur noch sich selbst.
"""
from __future__ import annotations

import math

import pytest

from aiimaging import raumkamera as rk

# Die beiden echten Räume aus dem Runner-Lauf.
L_FOERMIG = {
    "name": "Raum-Nord", "z_unten_m": 0.0, "hoehe_m": 2.7,
    "grundriss_m": [[0.3, 0.3], [5.0, 0.3], [5.0, 2.5], [7.7, 2.5], [7.7, 4.7], [0.3, 4.7]],
}
RECHTECKIG = {
    "name": "Raum-Sued", "z_unten_m": 0.1, "hoehe_m": 2.4,
    "grundriss_m": [[7.7, 0.3], [7.7, 2.5], [5.0, 2.5], [5.0, 0.3]],
}


# ======================================================================================
# Geometrie in der Waagerechten
# ======================================================================================

@pytest.mark.parametrize("raum,erwartet", [(L_FOERMIG, 26.62), (RECHTECKIG, 5.94)])
def test_die_flaechen_stimmen_mit_dem_runner_ueberein(raum, erwartet):
    """Die Bindung an den echten Lauf — ohne sie prüft diese Datei nur sich selbst."""
    assert abs(rk.flaeche(raum["grundriss_m"])) == pytest.approx(erwartet, abs=0.01)


def test_die_beiden_raeume_fuellen_das_umschliessende_rechteck():
    assert (abs(rk.flaeche(L_FOERMIG["grundriss_m"]))
            + abs(rk.flaeche(RECHTECKIG["grundriss_m"]))) == pytest.approx(7.4 * 4.4, abs=0.01)


def test_die_kerbe_des_L_raums_liegt_AUSSEN():
    """**Der Grund, warum es Strahlensatz sein muss und keine Mittelpunktsrechnung.**

    Räume sind nicht konvex. Der Punkt (6.0, 1.0) liegt in der Kerbe des L — innerhalb der
    Hüllbox, ausserhalb des Raums. Eine Kamera dort stünde im Nachbarzimmer.
    """
    assert rk.ist_innen((6.0, 3.5), L_FOERMIG["grundriss_m"]) is True
    assert rk.ist_innen((6.0, 1.0), L_FOERMIG["grundriss_m"]) is False


def test_der_umlaufsinn_wird_vereinheitlicht_und_nicht_vorausgesetzt():
    """Der Raumleser MELDET den Umlaufsinn und begradigt ihn nicht — hier fällt die
    Entscheidung.

    Ohne Vereinheitlichung zeigte dieselbe Rechnung je nach Datei nach innen oder nach
    aussen, und die Kamera stünde in der Wand statt davor. Geprüft am Verhalten: derselbe
    Raum, einmal andersherum aufgeschrieben, ergibt denselben Standpunkt.
    """
    gedreht = dict(RECHTECKIG, grundriss_m=list(reversed(RECHTECKIG["grundriss_m"])))

    a = rk.frontaler_standpunkt(RECHTECKIG)["auge"]
    b = rk.frontaler_standpunkt(gedreht)["auge"]

    assert a is not None and b is not None
    assert a == pytest.approx(b)


def test_der_abstand_zum_rand_sagt_nichts_ueber_innen_und_aussen():
    """Beides zu vermischen wäre bequem und falsch."""
    innen = rk.abstand_zum_rand((1.0, 1.0), L_FOERMIG["grundriss_m"])
    aussen = rk.abstand_zum_rand((6.0, 1.0), L_FOERMIG["grundriss_m"])

    assert innen > 0 and aussen > 0
    assert rk.ist_innen((6.0, 1.0), L_FOERMIG["grundriss_m"]) is False


# ======================================================================================
# Die Kamerahöhe — halbe Raumhöhe, und keine Ersatzhöhe
# ======================================================================================

@pytest.mark.parametrize("raum,erwartet", [(L_FOERMIG, 1.35), (RECHTECKIG, 0.1 + 1.2)])
def test_die_kamera_steht_auf_halber_raumhoehe(raum, erwartet):
    """Dann bekommen Boden und Decke exakt gleich viel Bildfläche — unabhängig von
    Brennweite und Abstand (nachgerechnet 21.08.2026)."""
    assert rk.frontaler_standpunkt(raum)["auge"][2] == pytest.approx(erwartet)


def test_der_bezugspunkt_der_hoehe_wird_MITGERECHNET():
    """`z_unten_m` ist nicht null, und das darf nicht untergehen.

    Genau an einem Bezugspunkt hat dieses Projekt schon zweimal verloren — einmal eine
    Kamera vierhundert Meter unter dem Erdgeschoss.
    """
    tief = dict(RECHTECKIG, z_unten_m=400.0)

    assert rk.frontaler_standpunkt(tief)["auge"][2] == pytest.approx(401.2)


@pytest.mark.parametrize("fehlt", ["hoehe_m", "z_unten_m"])
def test_ohne_hoehe_gibt_es_KEINE_ersatzhoehe(fehlt):
    """1,70 m aus der Aussenaufnahme einzusetzen wäre bequem und nachweislich falsch:
    In einem 2,55-m-Raum erzeugt sie 28 Prozentpunkte Ungleichgewicht."""
    raum = dict(RECHTECKIG, **{fehlt: None})

    ergebnis = rk.frontaler_standpunkt(raum)

    assert ergebnis["auge"] is None
    assert "geraten" in ergebnis["befund"] or "Ersatzhöhe" in ergebnis["befund"]


# ======================================================================================
# Die Standpunkte
# ======================================================================================

def test_die_kamera_bleibt_WAAGRECHT():
    """Die einzige institutionell verbindliche Regel des Fachs: lotrechte Bildebene.

    Blickziel auf Kamerahöhe heisst Neigung null heisst parallele Vertikalen. `kameras.py`
    tut das bis heute anders und erzeugt 9,46° — hier nicht.
    """
    for raum in (L_FOERMIG, RECHTECKIG):
        for s in rk.standpunkte(raum)["standpunkte"]:
            assert s["auge"][2] == pytest.approx(s["blick_auf"][2]), (
                f"{s['art']}: Blickziel nicht auf Kamerahöhe — die Kamera kippt")


def test_beide_standpunkte_liegen_im_raum_und_nicht_in_der_wand():
    for raum in (L_FOERMIG, RECHTECKIG):
        for s in rk.standpunkte(raum)["standpunkte"]:
            xy = (s["auge"][0], s["auge"][1])
            assert rk.ist_innen(xy, raum["grundriss_m"]), f"{s['art']} steht ausserhalb"
            assert rk.abstand_zum_rand(xy, raum["grundriss_m"]) >= \
                rk.WANDABSTAND_INNEN_M - 1e-6, f"{s['art']} steht zu nah an der Wand"


def test_der_frontale_standpunkt_nimmt_die_laengste_wand_und_sagt_dass_es_eine_setzung_ist():
    """Die Praxis wählt die Wand mit dem MOTIV. Ein Motiv steht in keiner IFC-Datei."""
    ergebnis = rk.frontaler_standpunkt(L_FOERMIG)

    assert ergebnis["zielwand"]["laenge_m"] == pytest.approx(7.4)
    assert [h for h in ergebnis["hinweise"] if "Setzung" in h]


def test_der_eckstandpunkt_meidet_die_einspringende_ecke():
    """Dort zeigt die Winkelhalbierende nach aussen, und die Kamera sähe weniger."""
    ergebnis = rk.eck_standpunkt(L_FOERMIG)

    assert ergebnis["ecke"] != [5.0, 2.5], "das ist die einspringende Ecke"
    assert rk.ist_innen((ergebnis["auge"][0], ergebnis["auge"][1]),
                        L_FOERMIG["grundriss_m"])


def test_einspringende_ecken_schliessen_sich_SELBST_aus():
    """**Warum hier kein Wächter steht** — und wie das herauskam.

    Zuerst stand im Modul eine Abfrage auf das Kreuzprodukt, die einspringende Ecken
    überging. Die Mutationsprobe hat sie überlebt: Wird sie herausgeschnitten, bleiben
    alle Tests grün. Die Nachprüfung zeigte den Grund — an einer einspringenden Ecke ist
    der Innenwinkel grösser als 180°, die Winkelhalbierende zeigt nach **aussen**, und der
    Lauf nach innen findet von dort keinen einzigen gültigen Punkt.

    Ein Wächter, der nie greift, ist eine tote Kante, auch wenn er richtig gedacht ist.
    Er ist entfernt; die Tatsache steht hier.
    """
    polygon = rk._gegen_uhrzeigersinn(rk._als_polygon(L_FOERMIG["grundriss_m"]))
    einspringend = (5.0, 2.5)
    i = polygon.index(einspringend)
    vor, hier, nach = polygon[i - 1], polygon[i], polygon[(i + 1) % len(polygon)]
    ein = (hier[0] - vor[0], hier[1] - vor[1])
    aus = (nach[0] - hier[0], nach[1] - hier[1])
    assert ein[0] * aus[1] - ein[1] * aus[0] < 0, "diese Ecke ist wirklich einspringend"

    r1, r2 = math.hypot(*ein), math.hypot(*aus)
    bx, by = (-ein[0] / r1) + (aus[0] / r2), (-ein[1] / r1) + (aus[1] / r2)
    laenge = math.hypot(bx, by)

    assert rk._lauf_nach_innen(hier, (bx / laenge, by / laenge), polygon,
                               abstand=rk.WANDABSTAND_INNEN_M) is None


def test_beide_arten_kommen_zurueck_auch_die_unbrauchbaren():
    """Einen wegzulassen verwischte den Unterschied zwischen *ging nicht* und
    *wurde nicht versucht*."""
    ergebnis = rk.standpunkte(RECHTECKIG)

    assert [s["art"] for s in ergebnis["standpunkte"]] == [rk.ART_FRONTAL, rk.ART_UEBER_ECK]


def test_ein_zu_enger_raum_bekommt_KEINEN_standpunkt():
    """Der Schritt, den ein Programm auslässt und ein Fotograf selbstverständlich geht.

    Ein Kämmerchen von 40 × 40 cm hat nach zweimal 30 cm Wandabstand nichts mehr übrig.
    Die ehrliche Antwort ist *kein Standpunkt*, nicht *irgendein Standpunkt*.
    """
    kammer = {"name": "zu eng", "z_unten_m": 0.0, "hoehe_m": 2.4,
              "grundriss_m": [[0, 0], [0.4, 0], [0.4, 0.4], [0, 0.4]]}

    ergebnis = rk.standpunkte(kammer)

    assert ergebnis["n_brauchbar"] == 0
    assert "zu eng" in ergebnis["befund"] or "Teilausschnitt" in ergebnis["befund"]


# ======================================================================================
# Passt der Raum ins Bild?
# ======================================================================================

def test_der_L_raum_fasst_seine_zielwand_NICHT():
    """**Der Befund, der diesen Abschnitt nötig gemacht hat.**

    Der frontale Standpunkt steht 4,10 m vor einer 7,40 m breiten Wand und sieht bei
    24 mm davon 6,15 m. Ein Standpunkt, der geometrisch zulässig ist und seine Wand nicht
    fasst, wäre stillschweigend irreführend.
    """
    sichtfeld = rk.frontaler_standpunkt(L_FOERMIG)["sichtfeld"]

    assert sichtfeld["passt"] is False
    assert sichtfeld["sichtbare_breite_m"] == pytest.approx(6.15, abs=0.05)
    assert sichtfeld["noetige_brennweite_mm"] == pytest.approx(20.0, abs=0.5)


def test_der_rechteckige_raum_fasst_seine_zielwand():
    """Die Gegenprobe — sonst prüfte der Test oben nur, dass irgendetwas False ist."""
    sichtfeld = rk.frontaler_standpunkt(RECHTECKIG)["sichtfeld"]

    assert sichtfeld["passt"] is True
    assert sichtfeld["noetige_brennweite_mm"] is None


def test_unter_der_belegten_grenze_wird_es_ausdruecklich_benannt():
    """Airbnb schreibt *„never capture wider than 16mm"* vor — eine Plattformvorgabe.

    Für ein Projekt, das Geometrietreue prüft, zählt das doppelt: Ein Objektiv, das den
    Raum grösser macht, als er ist, baut genau den Fehler ein, den die QA finden soll.
    """
    eng = rk._sichtfeld(1.0, 5.0, brennweite_mm=24.0, seitenverhaeltnis=1.6)

    assert eng["noetige_brennweite_mm"] < rk.BRENNWEITE_GRENZE_MM
    assert "UNTER der belegten Grenze" in eng["hinweis"]
    assert "Teilausschnitt" in eng["hinweis"]


def test_ueber_eck_hat_kein_ziel_und_behauptet_darum_kein_passt():
    """Es gibt dort keine Wand, die ganz ins Bild soll. `None` heisst nicht gemessen."""
    sichtfeld = rk.eck_standpunkt(L_FOERMIG)["sichtfeld"]

    assert sichtfeld["passt"] is None
    assert "NICHT GEMESSEN" in sichtfeld["hinweis"]


def test_die_noetige_brennweite_ist_die_umkehrung_und_stimmt():
    """Geprüft gegen die Vorwärtsrechnung, nicht gegen sich selbst."""
    noetig = rk.noetige_brennweite(4.10, 7.40)
    sichtbar = rk._sichtbare_breite(4.10, noetig, 1.6)

    assert sichtbar == pytest.approx(7.40, abs=1e-9)


# ======================================================================================
# Was dieses Modul NICHT kann, und es sagt es
# ======================================================================================

def test_der_verdeckungstest_fehlt_und_das_steht_im_modul():
    """Ob ein Möbel im Weg steht, weiss nur die Szene — und die lebt jenseits der
    Prozessgrenze. Notwendig ist nicht hinreichend, und das gehört gesagt."""
    # Zeilenumbrüche vereinheitlichen: Die Zusicherung meint den INHALT, nicht das
    # Layout. Ohne das wäre der Test von der Zeilenbreite abhängig und bräche beim
    # nächsten Umformatieren, ohne dass sich etwas Wahres geändert hätte.
    fliesstext = " ".join(rk.__doc__.split())

    assert "Verdeckungstest" in fliesstext
    assert "notwendig und nicht hinreichend" in fliesstext


# ======================================================================================
# Auswahl — und warum nicht ausgewichen wird
# ======================================================================================

def _raumliste():
    """Die Form, in der `kette._raeume_lesen` seine Räume liefert."""
    return {"status": "ok", "raeume": [
        {"raum": L_FOERMIG, "kamera": rk.standpunkte(L_FOERMIG)},
        {"raum": RECHTECKIG, "kamera": rk.standpunkte(RECHTECKIG)},
    ]}


def test_ohne_angabe_kommt_der_erste_raum_MIT_standpunkt():
    """`None` heisst nicht „irgendeiner": Einen Raum ohne Standpunkt zu wählen und dann
    zu scheitern wäre eine Auswahl, die keine ist."""
    w = rk.waehle(_raumliste())

    assert w["gefunden"] is True
    assert w["raum"] == "Raum-Nord"
    assert w["standpunkt"]["art"] == rk.ART_FRONTAL


def test_ein_raum_laesst_sich_beim_namen_nennen():
    w = rk.waehle(_raumliste(), raum="Raum-Sued", art=rk.ART_UEBER_ECK)

    assert w["raum"] == "Raum-Sued"
    assert w["standpunkt"]["art"] == rk.ART_UEBER_ECK


def test_auf_einen_anderen_raum_wird_NICHT_ausgewichen():
    """Ein stiller Ersatz wäre ein anderes Bild als das bestellte — und niemand sähe es
    dem Ergebnis an."""
    w = rk.waehle(_raumliste(), raum="Kueche")

    assert w["gefunden"] is False
    assert w["standpunkt"] is None
    assert "Raum-Nord" in w["grund"], "der Befund soll nennen, was es stattdessen gibt"


def test_auf_eine_andere_BLICKART_wird_ebenfalls_nicht_ausgewichen():
    """Wer frontal verlangt, bekommt nicht über Eck."""
    kammer = {"name": "zu eng", "z_unten_m": 0.0, "hoehe_m": 2.4,
              "grundriss_m": [[0, 0], [0.4, 0], [0.4, 0.4], [0, 0.4]]}
    liste = {"status": "ok",
             "raeume": [{"raum": kammer, "kamera": rk.standpunkte(kammer)}]}

    w = rk.waehle(liste, art=rk.ART_FRONTAL)

    assert w["gefunden"] is False
    assert w["standpunkt"] is None


def test_ohne_raeume_heisst_es_NICHT_GEMESSEN():
    """Entweder wurde über eine glb eingestiegen — dann gibt es keinen Raumbegriff — oder
    der Raumleser fand nichts. Beides ist etwas anderes als „hat keine Räume"."""
    w = rk.waehle(None)

    assert w["gefunden"] is False
    assert "NICHT GEMESSEN" in w["grund"]


def test_eine_erfundene_blickart_wird_abgewiesen():
    with pytest.raises(rk.RaumkameraError, match="art ist"):
        rk.waehle(_raumliste(), art="von_oben")


def test_der_verdacht_gegen_die_frontale_ansicht_steht_im_modul_und_ist_UNGEMESSEN():
    """`auf-20260822-29`: Für ρ über der Maske muss der Blick mehr als eine Fläche zeigen.

    Aussen gemessen — frontal vor der Langseite lieferte dieselbe Szene −0.8305, +0.6509
    und +0.8159, mit Vorzeichenwechsel. Innen ist die Lage aber **nicht dieselbe**: Boden,
    Decke und die anschneidenden Seitenwände tragen Tiefe, auch wenn die Stirnwand es
    nicht tut.

    Die frontale Ansicht wird darum weiter geliefert. Dieser Test hält fest, dass der
    Verdacht **benannt** ist — und dass er als ungemessen dasteht und nicht als Befund.
    """
    fliesstext = " ".join(rk.__doc__.split())

    assert "MEHR ALS EINE Fläche" in fliesstext
    assert "ungemessen" in fliesstext
    assert rk.frontaler_standpunkt(RECHTECKIG)["auge"] is not None, (
        "der Verdacht darf die Ansicht nicht stillschweigend abschalten")
