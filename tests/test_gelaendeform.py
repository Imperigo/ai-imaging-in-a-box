"""Gelände an der Form — die Zweitmeinung, wenn der Name nichts trägt.

Warum es dieses Modul und diese Proben gibt
-------------------------------------------
Die Namensregel versagt auf echtem Bestand messbar: Am 4771-Knoten-Modell schrumpft die
Bauwerksbox um **2,32 %**. Der Kommentar an `maske.WOERTER_AUSDRUECKLICH_NICHT` zieht den
Schluss selbst — *«der Befund ist nicht, welches Wort noch fehlt, sondern dass es keines
gibt»*: `decke` wäre nötig (111 von 112 Geländeknoten heissen so) und ist unmöglich (418
von 2742 Knoten einer Gebäudedatei ebenso).

Der Prüfstein ist gemessen und kein Gedankenspiel: Zwanzig `IfcCovering_Sub-Division:…`
bilden am echten Bestand **47 % der Szenenspannweite** und blieben nach der Namensregel
der grösste «Bauwerks»-Knoten.

Die Namen hier sind **Muster, keine Projektdaten** (Regel 3): `Sub-Division`, `Toposolid`
und `Decke` sind Werkzeug- und Klassenbegriffe.
"""
from __future__ import annotations

import pytest

from aiimaging import gelaendeform as gf

#: Eine Platte, die 47 % der Spannweite einnimmt, und ein aufragender Körper darauf.
#: glTF-Koordinaten, Y oben — genau die Form, die `glbbox.knotenboxen` liefert.
PRUEFSTEIN = [
    ("IfcCovering_Sub-Division:1", (-47, -0.5, -47), (47, 0, 47)),
    ("Stuetze-01", (-8, 0, -8), (8, 36, 8)),
]


def test_der_pruefstein_wird_erkannt():
    """**Der Fall, an dem sich die Regel beweisen muss.** Erkennt die Form ihn nicht,
    taugt sie nicht — dann bliebe nur ein weiteres Wort, und der Quelltext sagt, dass es
    keines gibt."""
    befund = gf.gelaende_knoten(PRUEFSTEIN)
    assert befund["gelaende"] == ("IfcCovering_Sub-Division:1",)
    assert befund["bauwerk"] == ("Stuetze-01",)
    assert befund["unklar"] == ()


def test_die_drei_merkmale_stehen_einzeln_da_und_sind_nachrechenbar():
    """*Eine Formaussage ohne die Zahlen dahinter kann man nur glauben oder verwerfen.*"""
    m = gf.merkmale(PRUEFSTEIN[0], PRUEFSTEIN)
    # Szene: 94 x 94 im Grundriss, Platte 94 x 94 -> voller Anteil.
    assert m["grundrissanteil"] == pytest.approx(1.0)
    # Platte 0,5 hoch auf 94 Kante.
    assert m["flachheit"] == pytest.approx(0.5 / 94)
    # Oberkante der Platte liegt 0,5 ueber dem tiefsten Punkt, Szene ist 36,5 hoch.
    assert m["tieflage"] == pytest.approx(0.5 / 36.5)


def test_ein_zu_kleiner_koerper_ist_bauwerk_egal_wie_flach():
    """Eine flache Platte von 5 % Grundriss ist ein Bauteil, kein Gelände."""
    szene = [("Platte-klein", (-5, 0, -5), (5, 0.2, 5)),
             ("Halle", (-50, 0, -50), (50, 20, 50))]
    u = gf.urteil(szene[0], szene)
    assert u["urteil"] == gf.BAUWERK
    assert "zu klein" in u["grund"]


def test_ein_aufragender_koerper_ist_bauwerk_egal_wie_gross():
    """Ein Baukörper mit dem Grundriss des Geländes ist trotzdem keiner."""
    szene = [("Sockelbau", (-50, 0, -50), (50, 40, 50)),
             ("Anbau", (-10, 0, 60), (10, 8, 70))]
    u = gf.urteil(szene[0], szene)
    assert u["urteil"] == gf.BAUWERK
    assert "ragt auf" in u["grund"]


def test_die_flachheit_misst_gegen_die_KLEINERE_kante():
    """Sonst wäre ein langer schmaler Steg «flach», obwohl er aufragt."""
    szene = [("Steg", (-50, 0, -1), (50, 6, 1)), ("Boden", (-50, -1, -50), (50, 0, 50))]
    m = gf.merkmale(szene[0], szene)
    assert m["flachheit"] == pytest.approx(6 / 2), "6 hoch auf 2 breit, nicht auf 100 lang"
    assert gf.urteil(szene[0], szene)["urteil"] == gf.BAUWERK


def test_eine_grosse_flache_platte_auf_halber_hoehe_bleibt_NICHT_ENTSCHEIDBAR():
    """**Der teure Gegenfall, und die dritte Antwort ist hier der richtige Ausgang.**

    Eine Geschossdecke sieht an der Form aus wie ein Geländesockel. Sie stillschweigend
    dem einen oder anderen zuzuschlagen wäre eine Entscheidung, die niemand gemessen hat.
    """
    szene = [("IfcCovering_Toposolid_1", (-50, -1, -50), (50, 0, 50)),
             ("Decke-025", (-30, 14, -30), (30, 14.4, 30)),
             ("Wand-01", (-30, 0, -30), (30, 30, 30))]
    befund = gf.gelaende_knoten(szene)
    assert befund["unklar"] == ("Decke-025",)
    assert befund["gelaende"] == ("IfcCovering_Toposolid_1",)


def test_ein_dach_ganz_oben_ist_bauwerk_und_nicht_unklar():
    """Die Gegenprobe zum Vorigen: Wo die Höhe eindeutig ist, wird auch entschieden."""
    szene = [("Dach", (-22, 30, -22), (22, 31, 22)),
             ("Wand-01", (-20, 0, -20), (20, 30, 20))]
    u = gf.urteil(szene[0], szene)
    assert u["urteil"] == gf.BAUWERK
    assert "Dach oder eine Decke" in u["grund"]


def test_gelaende_auf_zwei_ebenen_wird_zweimal_erkannt():
    """Eine Terrasse über der Platte ist auch Gelände — sie liegt tief genug."""
    szene = [("IfcCovering_Toposolid_1", (-50, -1, -50), (50, 0, 50)),
             ("Terrasse", (-40, 3, 10), (40, 3.4, 45)),
             ("Wand-01", (-20, 0, -20), (20, 26, 20))]
    assert set(gf.gelaende_knoten(szene)["gelaende"]) == {
        "IfcCovering_Toposolid_1", "Terrasse"}


def test_eine_szene_ohne_ausdehnung_bekommt_keine_zahl_sondern_einen_fehler():
    """**Kein Rückfall auf einen Vorgabewert.** Ein Anteil an einer Fläche von null ist
    unendlich oder beliebig, und beides sähe wie eine Messung aus."""
    flach = [("A", (0, 0, 0), (10, 5, 0)), ("B", (0, 0, 0), (10, 5, 0))]
    with pytest.raises(gf.GelaendeformError, match="keine Ausdehnung"):
        gf.merkmale(flach[0], flach)


def test_eine_leere_szene_ebenso():
    with pytest.raises(gf.GelaendeformError, match="leere Szene"):
        gf.merkmale(("A", (0, 0, 0), (1, 1, 1)), [])


def test_unklar_zaehlt_als_bauwerk_und_das_steht_im_docstring():
    """*Gelände in der Maske ist teurer als Gelände daneben* — die strengere Auslegung.

    Die Hülle `ist_gelaende_nach_form` kann die dritte Antwort nicht ausdrücken; wer sie
    sehen will, nimmt `gelaende_knoten`. Genau das muss dort stehen, sonst hält der
    nächste die Hülle für die ganze Auskunft.
    """
    szene = [("IfcCovering_Toposolid_1", (-50, -1, -50), (50, 0, 50)),
             ("Decke-025", (-30, 14, -30), (30, 14.4, 30)),
             ("Wand-01", (-30, 0, -30), (30, 30, 30))]
    regel = gf.ist_gelaende_nach_form(szene)
    assert regel("Decke-025") is False, "unklar ist hier Bauwerk, und zwar mit Absicht"
    assert regel("IfcCovering_Toposolid_1") is True
    assert "strengere Auslegung" in gf.ist_gelaende_nach_form.__doc__


def test_die_regel_hat_die_gestalt_der_namensregel():
    """Damit sie dort einsetzbar ist, wo heute `ist_gelaende` steht — ohne dass der
    Aufrufer etwas über Formen wissen muss."""
    regel = gf.ist_gelaende_nach_form(PRUEFSTEIN)
    assert callable(regel)
    assert isinstance(regel("Stuetze-01"), bool)


# ======================================================================================
# Die Familienprüfung — kein Schwellenproblem, ein Korngrössenproblem
# ======================================================================================

def _zerlegte_platte(stuecke=20, kante=100.0, dicke=0.3):
    """Eine Geländeplatte, in ``stuecke`` Streifen zerlegt — wie ein Bestandsexport sie
    liefert. Jeder Streifen allein ist zu schmal für :data:`GRUNDRISSANTEIL_MIN`."""
    breite = kante / stuecke
    knoten = [(f"IfcCovering_Sub-Division:Kies:{i}",
               (i * breite, -dicke, 0.0), ((i + 1) * breite, 0.0, kante))
              for i in range(stuecke)]
    # Ein Bauwerk darauf, damit die Szene eine Höhe hat.
    knoten.append(("IfcWall_Aussenwand_ABC", (40.0, 0.0, 40.0), (60.0, 12.0, 60.0)))
    return knoten


def test_eine_zerlegte_platte_faellt_knoten_fuer_knoten_durch():
    """Der gemessene Ausgangspunkt (`auf-20260907-82`): **kein einziger** Streifen
    erreicht den Grundrissanteil, obwohl sie zusammen das ganze Gelände sind."""
    alle = _zerlegte_platte()
    befund = gf.gelaende_knoten(alle)

    assert befund["gelaende"] == ()
    grosster = max(gf.merkmale(k, alle)["grundrissanteil"] for k in alle[:-1])
    assert grosster < gf.GRUNDRISSANTEIL_MIN


def test_als_familie_beurteilt_erkennt_sie_dieselbe_platte():
    """Die Hüllbox über die Familie urteilt Gelände — und dann gelten alle Streifen.

    *Die drei Merkmale sind richtig gewählt; sie treffen die Platte, sobald sie eine
    Platte ist.* Geändert wird die Korngrösse, nicht die Schwelle.
    """
    alle = _zerlegte_platte()
    befund = gf.gelaende_knoten(alle, als_familie=True)

    assert len(befund["gelaende"]) == 20
    assert all(n.startswith("IfcCovering_Sub-Division") for n in befund["gelaende"])
    assert "IfcWall_Aussenwand_ABC" in befund["bauwerk"], "die Wand bleibt Bauwerk"


def test_der_grund_nennt_die_familie_und_das_einzelurteil():
    """Ein Urteil, das die Korngrösse gewechselt hat, muss sagen, dass es das tat."""
    alle = _zerlegte_platte()
    befund = gf.gelaende_knoten(alle, als_familie=True)
    einer = next(u for u in befund["urteile"] if u["urteil"] == gf.GELAENDE)

    assert einer["familie"] == "IfcCovering_Sub-Division"
    assert "Einzeln nicht entschieden" in einer["grund"]
    assert "20 Knoten" in einer["grund"]


def test_die_familienpruefung_ist_vorgabe_aus():
    """**Sie ändert, was als Gelände gilt** — und daran hängt die Bauwerksmaske.

    Eine stillschweigend geänderte Maske wäre genau die Sorte Änderung, die eine
    Messreihe unbrauchbar macht, ohne dass es auffällt.
    """
    alle = _zerlegte_platte()
    assert gf.gelaende_knoten(alle) == gf.gelaende_knoten(
        alle, als_familie=False)
    assert gf.gelaende_knoten(alle)["gelaende"] == ()


def test_aufragende_bauteile_werden_nicht_zur_familie_zusammengefasst():
    """Die Gegenprobe, und ohne sie prüfte der Test darüber nur, dass irgendetwas grün wird.

    Zwanzig Fassadentafeln teilen sich einen Namensstamm wie die Geländestreifen. Ihre
    gemeinsame Hüllbox ragt aber auf — die Flachheit fängt sie.
    """
    tafeln = [(f"IfcCurtainWall_Fassadentafel:Alu:{i}",
               (i * 5.0, 0.0, 0.0), ((i + 1) * 5.0, 15.0, 0.4)) for i in range(20)]
    tafeln.append(("IfcSlab_Boden_XYZ", (0.0, -0.3, -40.0), (100.0, 0.0, 60.0)))

    befund = gf.gelaende_knoten(tafeln, als_familie=True)
    assert not any(n.startswith("IfcCurtainWall") for n in befund["gelaende"])


def test_ein_paar_ist_keine_familie():
    """Drei ist die kleinste Zahl, die eine Familie von einem Paar unterscheidet.

    Zwei grosse flache Körper nebeneinander sind eher zwei Decken als eine zerlegte
    Platte — und wer aus zweien eine Familie macht, fasst irgendwann alles zusammen.
    """
    zwei = [("IfcSlab_Decke:OG:1", (0.0, 5.0, 0.0), (50.0, 5.3, 100.0)),
            ("IfcSlab_Decke:OG:2", (50.0, 5.0, 0.0), (100.0, 5.3, 100.0)),
            ("IfcWall_W_ABC", (40.0, 0.0, 40.0), (60.0, 12.0, 60.0))]
    assert gf.familien(zwei) == {}
