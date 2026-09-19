"""Die geometrische Gegenprobe zur Hochachse — trägt die Vermutung?

Der Anlass steht in :func:`aiimaging.contracts.normalize_up_axis`: Die Verschärfung vom
19.09.2026 fängt den **Tippfehler** (``"Zeichnung"`` galt als ``Z``), nicht den
**Irrtum** (wer ``"Z"`` schreibt, während das Modell Y-up ist). Die Vermutung, mit der
:mod:`aiimaging.hochachse` den Irrtum fangen will, lautet: *Gelände ist in der Hochachse
flach.*

**Diese Datei prüft die Vermutung, sie setzt sie nicht voraus.** Zwei der Fälle unten
belegen, dass sie NICHT trägt — der Hang ab 4,1 m Anstieg (sie schweigt) und die
stehende Platte (sie irrt). Beide stehen hier, damit sie nicht als Überraschung
wiederkommen.

**Regel 3:** Alle Geometrie ist synthetisch und im Repo erzeugt — von Hand als
Knotenliste oder über ``tools/make_test_glb.py``. Kein echtes Modell, keine Namen aus
echten Aufträgen.
"""
from __future__ import annotations

import importlib.util
import json
import re
import struct
import sys
from pathlib import Path

import pytest

from aiimaging import gelaendeform, glbbox, hochachse
from aiimaging.contracts import ContractError

WERKZEUG = Path(__file__).resolve().parents[1] / "tools" / "make_test_glb.py"


def _erzeuger():
    """``tools/make_test_glb.py`` über den Dateipfad laden — es ist kein Paketmodul."""
    spez = importlib.util.spec_from_file_location("make_test_glb_hochachse", WERKZEUG)
    modul = importlib.util.module_from_spec(spez)
    sys.modules[spez.name] = modul
    spez.loader.exec_module(modul)
    return modul


# --------------------------------------------------------------------------------------
# Die Szenen. Alle in glTF-Koordinaten (Y oben), sofern nicht anders gesagt.
# --------------------------------------------------------------------------------------

#: Eine Geländeplatte 40 × 30 × 0,5 m und ein Haus 12 × 9 × 15 m darauf.
#:
#: Bewusst **asymmetrisch** — dieselbe Überlegung wie bei ``make_test_glb.VORGABE_SZENE``:
#: Bei gleichen Kantenlängen sähe eine verdrehte Achse zufällig richtig aus.
GELAENDE_UND_HAUS = (
    ("Gelaendeplatte", (-14.0, -0.5, -12.0), (26.0, 0.0, 18.0)),
    ("Haus", (0.0, 0.0, 0.0), (12.0, 15.0, 9.0)),
)


def nach_z_up(knoten):
    """Dieselbe Szene, aber als Datei mit **Z oben** geschrieben.

    ``(x, y, z)_gltf → (x, −z, y)`` — dieselbe Umrechnung, die
    :func:`aiimaging.glbbox.nach_welt` benutzt, hier aber auf die Knoten angewandt statt
    auf die fertige Box. So entsteht aus derselben Geometrie eine Datei, in der die
    Hochachse Z ist, ohne dass zweite Zahlen von Hand gepflegt werden müssten.
    """
    aus = []
    for name, lo, hi in knoten:
        aus.append((name, [lo[0], -hi[2], lo[1]], [hi[0], -lo[2], hi[1]]))
    return tuple(aus)


def hang(anstieg: float):
    """Dieselbe Platte, aber geneigt: Der Höhenunterschied ``anstieg`` über 40 m.

    Die Hüllbox eines geneigten Geländes ist so dick wie sein Höhenunterschied — das ist
    der ganze Grund, warum ein Hang der Messung entgleitet.
    """
    return (
        ("Gelaendeplatte", (-14.0, -0.5, -12.0), (26.0, anstieg, 18.0)),
        ("Haus", (0.0, anstieg, 0.0), (12.0, anstieg + 15.0, 9.0)),
    )


#: Der Fall, in dem die Vermutung **irrt**: eine stehende Platte ohne Gelände.
FASSADE_OHNE_GELAENDE = (
    ("Fassadenplatte", (-2.0, 0.0, -0.3), (14.0, 15.0, 0.0)),
    ("Haus", (0.0, 0.0, 0.0), (12.0, 15.0, 9.0)),
)


# --------------------------------------------------------------------------------------
# 1 · Trägt die Vermutung? Die beiden Fälle, für die sie gebaut ist
# --------------------------------------------------------------------------------------

def test_flaches_gelaende_und_bauwerk_in_y_up_wird_als_y_erkannt():
    befund = hochachse.hochachse_aus_knoten(GELAENDE_UND_HAUS)

    assert befund["achse"] == "Y", befund["satz"]
    assert befund["grund"] == hochachse.GEMESSEN
    assert befund["sicherheit"] == "eindeutig"
    # WORAN sie es festmacht — nicht nur das Urteil. Eine Formaussage ohne ihre Zahlen
    # ist von aussen nicht nachpruefbar.
    y = befund["achsen"]["Y"]
    assert y["n_gelaende"] == 1
    assert y["grundrissanteil"] == pytest.approx(1.0)
    assert y["flachheit"] == pytest.approx(0.5 / 30.0)       # 0,5 m dick, 30 m kurze Kante
    assert y["tieflage"] == pytest.approx(0.5 / 15.5)        # Oberkante ganz unten
    # UND die beiden anderen Achsen antworten gar nicht — daran haengt der Vorsprung.
    assert befund["achsen"]["X"]["staerke"] == 0.0
    assert befund["achsen"]["Z"]["staerke"] == 0.0


def test_dieselbe_szene_in_z_up_wird_als_z_erkannt():
    """Die Gegenrichtung, und sie ist der eigentliche Punkt.

    Eine Messung, die immer ``"Y"`` sagt, wäre an der Y-up-Szene grün und trotzdem
    wertlos: Genau der Fall, den sie fangen soll — eine Z-up-Datei, die als Y-up
    angegeben ist — käme nie vor.
    """
    befund = hochachse.hochachse_aus_knoten(nach_z_up(GELAENDE_UND_HAUS))

    assert befund["achse"] == "Z", befund["satz"]
    assert befund["sicherheit"] == "eindeutig"
    assert befund["achsen"]["Y"]["staerke"] == 0.0


# --------------------------------------------------------------------------------------
# 2 · Die drei Wege zu ``None`` — und jeder mit eigenem Grund
# --------------------------------------------------------------------------------------

def test_ohne_gelaende_sagt_sie_nichts_und_nennt_den_grund():
    """Zwei Baukörper, keine Platte. ``None`` heisst NICHT ENTSCHEIDBAR."""
    befund = hochachse.hochachse_aus_knoten((
        ("HausA", (0.0, 0.0, 0.0), (12.0, 15.0, 9.0)),
        ("HausB", (20.0, 0.0, 2.0), (30.0, 11.0, 12.0)),
    ))

    assert befund["achse"] is None
    assert befund["grund"] == hochachse.KEIN_GELAENDE
    assert befund["sicherheit"] is None
    assert "NICHT ENTSCHEIDBAR" in befund["satz"]
    assert "kein erkennbares Gelaende" in befund["satz"]


def test_ein_turm_ohne_gelaende_ergibt_NICHT_die_groesste_achse():
    """**Der Fall, an dem eine naive Regel stirbt.**

    Ein Turm ist in der Hochachse die *grösste* Ausdehnung, ein Flachbau die *kleinste*.
    Wer aus der Hüllbox allein auf oben schliesst, hat für den einen Bau recht und für
    den anderen unrecht — und sieht der Zahl nicht an, welcher Fall vorlag.
    """
    befund = hochachse.hochachse_aus_knoten((("Turm", (0.0, 0.0, 0.0), (10.0, 40.0, 10.0)),))

    assert befund["achse"] is None, befund["satz"]
    assert befund["grund"] == hochachse.KEIN_GELAENDE
    # Y IST HIER DIE GROESSTE AUSDEHNUNG (40 gegen 10 und 10) und trotzdem nicht die
    # Antwort. Genau das trennt eine Messung von einer Vermutung.
    assert befund["achsen"]["Y"]["staerke"] == 0.0


def test_ein_flachbau_ohne_gelaende_ergibt_auch_nicht_die_kleinste_achse():
    """Die Gegenprobe zum Turm: Beim Flachbau wäre die Hochachse die kleinste Achse.

    Beide Fälle ``None`` zu nennen ist das Ergebnis — nicht das Ausweichen.
    """
    befund = hochachse.hochachse_aus_knoten((("Flachbau", (0.0, 0.0, 0.0), (30.0, 4.0, 24.0)),))

    assert befund["achse"] is None, befund["satz"]
    assert befund["grund"] == hochachse.KEIN_GELAENDE


def test_eine_leere_szene_hat_einen_eigenen_grund():
    befund = hochachse.hochachse_aus_knoten(())

    assert befund["achse"] is None
    assert befund["grund"] == hochachse.KEINE_KNOTEN
    assert befund["grund"] != hochachse.KEIN_GELAENDE, (
        "Kein Koerper ist etwas anderes als kein Gelaende — wer beides gleich nennt, "
        "sucht spaeter das falsche Wort.")


def test_eine_szene_ohne_ausdehnung_wird_nicht_zu_einer_zahl():
    """Alle Körper in einer Ebene: Jeder Anteil daran wäre beliebig."""
    befund = hochachse.hochachse_aus_knoten((
        ("Blatt", (0.0, 0.0, 0.0), (10.0, 0.0, 10.0)),
        ("Blatt2", (2.0, 0.0, 2.0), (4.0, 0.0, 4.0)),
    ))

    assert befund["achse"] is None
    assert befund["grund"] == hochachse.KEINE_AUSDEHNUNG


def test_zwei_achsen_mit_gelaendebefund_ergeben_keine_antwort():
    """Eine liegende **und** eine stehende Platte — die Form trennt das nicht.

    Sie könnte sich hier für die stärkere entscheiden; der Vorsprung von 1,03 wäre eine
    Zahl, und die Antwort sähe fertig aus. Sie tut es nicht.
    """
    befund = hochachse.hochachse_aus_knoten((
        ("Gelaendeplatte", (-14.0, -0.5, -12.0), (26.0, 0.0, 18.0)),
        ("Wandscheibe", (-14.0, -0.5, -12.0), (26.0, 14.5, -11.7)),
        ("Haus", (0.0, 0.0, 0.0), (12.0, 15.0, 9.0)),
    ))

    assert befund["achse"] is None, befund["satz"]
    assert befund["grund"] == hochachse.MEHRDEUTIG
    assert befund["achsen"]["Y"]["staerke"] > 0.0
    assert befund["achsen"]["Z"]["staerke"] > 0.0
    assert befund["vorsprung"] < hochachse.VORSPRUNG_MIN


def test_gewinnt_x_wird_nicht_auf_die_zweitbeste_achse_ausgewichen():
    """X ist keine Vertragsachse — und die Antwort darauf ist ``None``, nicht ``Y``.

    Die Messung darf nur zwischen zwei Achsen wählen; die Geometrie kennt drei. Wer die
    dritte wegwirft, statt sie zu melden, macht aus einer fremden Konvention eine stille
    Verdrehung.
    """
    befund = hochachse.hochachse_aus_knoten((
        ("Gelaendeplatte", (-0.5, -12.0, -14.0), (0.0, 18.0, 26.0)),
        ("Haus", (0.0, 0.0, 0.0), (15.0, 9.0, 12.0)),
    ))

    assert befund["achse"] is None, befund["satz"]
    assert befund["grund"] == hochachse.AUSSERHALB_DES_VERTRAGS
    assert befund["achsen"]["X"]["staerke"] > 0.0
    assert "X" in befund["satz"]


# --------------------------------------------------------------------------------------
# 3 · Wo die Vermutung nicht trägt — gemessen, nicht vermutet
# --------------------------------------------------------------------------------------

#: Bis zu welchem Höhenunterschied über 40 m ein geneigtes Gelände noch erkannt wird.
#:
#: **GEMESSEN am 19.09.2026** an der Szene aus :func:`hang`, in Schritten von 0,1 m: bei
#: 4,0 m noch ``"Y"``, bei 4,1 m schon ``None`` (nachgemessen in Schritten von 0,1 m;
#: die erste Messung fuhr 0,2er-Schritte und nannte darum 4,2). Die Zahl ist keine Setzung dieses
#: Moduls, sondern die Folge von
#: :data:`aiimaging.gelaendeform.FLACHHEIT_MAX` (0,15) an der kurzen Plattenkante von
#: 30 m: ``(4,0 + 0,5) / 30 = 0,15``.
HANG_GRENZE_M = 4.0


@pytest.mark.parametrize("anstieg, erwartet", [
    (1.0, "Y"),
    (3.0, "Y"),
    (HANG_GRENZE_M, "Y"),
    (4.2, None),
    (6.0, None),
    (10.0, None),
])
def test_ein_geneigtes_gelaende_entgleitet_der_messung_ab_vier_metern(anstieg, erwartet):
    """**Hier trägt die Vermutung nur bis zu einer Neigung** — und darüber schweigt sie.

    Ein Hang ist in der Hochachse nicht mehr dünn: Seine Hüllbox ist so dick wie sein
    Höhenunterschied. Ab 4,2 m auf 40 m (rund 10 % Gefälle, etwa 6°) gilt er der Form
    nicht mehr als Platte.

    *Das Wichtige ist die Richtung des Fehlers:* Sie wird **still**, nicht falsch — in
    keiner der drei Achsen findet sie dann noch Gelände. Eine Messung, die am Hang eine
    andere Achse nennte, wäre ungleich teurer.
    """
    befund = hochachse.hochachse_aus_knoten(hang(anstieg))

    assert befund["achse"] == erwartet, befund["satz"]
    if erwartet is None:
        assert befund["grund"] == hochachse.KEIN_GELAENDE


def test_eine_stehende_platte_fuehrt_die_messung_in_die_irre():
    """**DER FALL, IN DEM DIE VERMUTUNG IRRT — und zwar zuversichtlich.**

    Eine grosse dünne Platte ist geometrisch dasselbe, ob sie liegt oder steht. Diese
    Szene ist Y-up und enthält kein Gelände, aber eine Fassade, die den Grundriss
    aufspannt und am Rand der Szene sitzt. In ihrer dünnen Achse — Z, also waagrecht —
    ist sie «gross, flach und unten».

    Die Messung antwortet ``"Z"`` und nennt sich dabei ``eindeutig``. **Sie irrt.**

    Dieser Test steht hier, damit der Befund im Repo ist und nicht in einer Erinnerung.
    Er wird *nicht* zu ``None`` repariert: Es gibt kein billiges Merkmal, das eine
    liegende von einer stehenden Platte trennt, und ein nachgezogener Schwellenwert wäre
    an genau dieser Datei geeicht.
    """
    befund = hochachse.hochachse_aus_knoten(FASSADE_OHNE_GELAENDE)

    assert befund["achse"] == "Z", befund["satz"]
    assert befund["sicherheit"] == "eindeutig", (
        "Die Messung merkt ihren Irrtum nicht — genau das macht ihn teuer.")


def test_mit_einem_echten_gelaende_verschwindet_der_falsche_kandidat():
    """Was den Irrtum oben einordnet: Er braucht eine Szene **ohne** Gelände.

    Dieselbe Fassade, aber die Geländeplatte dazu: Die Platte dehnt die Szene in Z, die
    Fassade rutscht aus dem unteren Drittel und gilt der Form als ``nicht
    entscheidbar``. Übrig bleibt Y — richtig, und eindeutig.
    """
    befund = hochachse.hochachse_aus_knoten(GELAENDE_UND_HAUS + FASSADE_OHNE_GELAENDE[:1])

    assert befund["achse"] == "Y", befund["satz"]
    assert befund["achsen"]["Z"]["staerke"] == 0.0
    assert befund["achsen"]["Z"]["n_unklar"] == 1, (
        "Die Fassade soll NICHT still zu Bauwerk werden — sie bleibt der Form unklar.")


# --------------------------------------------------------------------------------------
# 4 · Gekacheltes Gelände: was die Familienprüfung ausmacht
# --------------------------------------------------------------------------------------

def _kacheln():
    """Ein Gelände als **zwanzig** Stücke — so liefert es echter Bestand.

    Die Namen sind der Gestalt nachgebaut, die ``gelaendeform.familienschluessel``
    zerlegt (``<IfcKlasse>_<Typ>:<Ausprägung>:<Nummer>``), aber frei erfunden: Regel 3
    verbietet Namen aus echten Projekten, nicht ihre Form.
    """
    aus = [(f"IfcCovering_Teilflaeche:Kies:{i}{j}",
            (-14.0 + i * 10.0, -0.5, -12.0 + j * 6.0),
            (-4.0 + i * 10.0, 0.0, -6.0 + j * 6.0))
           for i in range(4) for j in range(5)]
    aus.append(("IfcWall_Haus_1", (0.0, 0.0, 0.0), (12.0, 15.0, 9.0)))
    return tuple(aus)


def test_ein_gekacheltes_gelaende_braucht_die_familienpruefung():
    """Zwanzig Kacheln sind einzeln zu klein — zusammen sind sie die Platte.

    Ohne Familienprüfung schweigt die Messung; mit ihr trifft sie. Das ist der Grund,
    warum sie hier Vorgabe **an** ist und in :mod:`aiimaging.gelaendeform` aus: Dort
    änderte sie die Bauwerksmaske, hier hängt nichts daran.
    """
    ohne = hochachse.hochachse_aus_knoten(_kacheln(), als_familie=False)
    mit = hochachse.hochachse_aus_knoten(_kacheln(), als_familie=True)

    assert ohne["achse"] is None, ohne["satz"]
    assert ohne["grund"] == hochachse.KEIN_GELAENDE
    assert mit["achse"] == "Y", mit["satz"]
    assert mit["entschieden_durch_familie"] is True
    assert "Familienpruefung" in mit["satz"], (
        "Wer die Antwort liest, soll sehen, dass sie an der Familienpruefung haengt.")


def _kacheln_ueberlappend():
    """Dieselben zwanzig Stücke, aber mit Überlappung — 12 × 8 m im 10 × 6-m-Raster.

    **Die Überlappung ist der ganze Zweck dieser Szene**, und sie steht hier, weil die
    Mutationsprobe vom 19.09.2026 die erste Fassung des Tests darunter als zahnlos
    entlarvt hat: Bei lückenlos aneinandergelegten Kacheln ist die Summe der Anteile
    *gleich* der Hülle (beides 1,0), und ein Test darauf hielte still, obwohl die
    Rechnung vertauscht wäre. Mit Überlappung ergibt die Summe 1,43 und die Hülle 1,0 —
    erst jetzt trennt die Zahl die beiden Rechnungen.

    Überlappende Geländestücke sind ausserdem der realistischere Fall: Wer eine Fläche
    in Teilflächen zerlegt, stösst sie selten auf den Millimeter aneinander.
    """
    aus = [(f"IfcCovering_Teilflaeche:Kies:{i}{j}",
            (-14.0 + i * 10.0, -0.5, -12.0 + j * 6.0),
            (-2.0 + i * 10.0, 0.0, -4.0 + j * 6.0))
           for i in range(4) for j in range(5)]
    aus.append(("IfcWall_Haus_1", (0.0, 0.0, 0.0), (12.0, 15.0, 9.0)))
    return tuple(aus)


def test_die_staerke_ist_die_huelle_und_nicht_die_summe():
    """Zwanzig Anteile zu addieren gäbe eine «Stärke» über 1,0 — und das wäre kein Anteil.

    Eine Stärke jenseits von 1,0 zerstörte still den Vorsprung: Sie wüchse mit der Zahl
    der Stücke statt mit der Fläche, und eine in zwanzig Teile zerlegte Achse schlüge
    eine in einem Stück gelieferte allein deshalb.
    """
    befund = hochachse.hochachse_aus_knoten(_kacheln_ueberlappend())

    assert befund["achsen"]["Y"]["n_gelaende"] == 20
    # Die Summe der zwanzig Einzelanteile waere 1,43 — nachgerechnet, damit die Zahl
    # oben nicht zufaellig auch die Summe ist.
    summe = sum(gelaendeform.merkmale(k, _kacheln_ueberlappend(), hoch=1)["grundrissanteil"]
                for k in _kacheln_ueberlappend()[:20])
    assert summe == pytest.approx(1.4286, abs=0.001), summe
    assert befund["staerke"] == pytest.approx(1.0)


# --------------------------------------------------------------------------------------
# 5 · Die Gegenprobe zur Angabe
# --------------------------------------------------------------------------------------

def test_eine_richtige_angabe_bleibt_still():
    befund = hochachse.hochachse_aus_knoten(GELAENDE_UND_HAUS)
    aus = hochachse.gegenprobe("Y", befund)

    assert aus["stimmt"] is True
    assert aus["gemessen"] == "Y"
    assert "WIDERSPRUCH" not in aus["satz"]


def test_eine_falsche_angabe_bekommt_einen_widerspruch():
    """**Der Irrtum, den ``normalize_up_axis`` nicht fangen kann.**

    ``"Z"`` ist eine syntaktisch tadellose Angabe; der Vertrag hat daran nichts zu
    beanstanden. Erst die Geometrie widerspricht.
    """
    befund = hochachse.hochachse_aus_knoten(GELAENDE_UND_HAUS)
    aus = hochachse.gegenprobe("Z", befund)

    assert aus["stimmt"] is False
    assert aus["angegeben"] == "Z"
    assert aus["gemessen"] == "Y"
    assert "WIDERSPRUCH" in aus["satz"]


def test_der_widerspruch_verurteilt_die_angabe_nicht():
    """Welche Seite irrt, sagt die Probe ausdrücklich nicht — sie kann es nicht wissen.

    Die Fassadenszene oben belegt, dass die *Messung* die Irrende sein kann.
    """
    aus = hochachse.gegenprobe("Z", hochachse.hochachse_aus_knoten(GELAENDE_UND_HAUS))

    assert "Welche der beiden Seiten irrt, sagt diese Probe NICHT" in aus["satz"]


def test_nicht_messbar_ergibt_None_und_ausdruecklich_nicht_falsch():
    """**Der wichtigste Test dieser Datei.**

    Ein ``None``, das still zu ``False`` wird, meldet einen Fehler, den niemand gefunden
    hat — und schickt jemanden auf die Suche nach einer Verdrehung, die es nicht gibt.
    Ein ``None``, das still zu ``True`` wird, meldet eine Prüfung, die nie stattfand.
    """
    befund = hochachse.hochachse_aus_knoten((("Turm", (0.0, 0.0, 0.0), (10.0, 40.0, 10.0)),))
    aus = hochachse.gegenprobe("Z", befund)

    assert aus["stimmt"] is None
    assert aus["stimmt"] is not False
    assert aus["stimmt"] is not True
    assert "NICHT GEPRUEFT" in aus["satz"]
    # Und der Grund der Messung wird DURCHGEREICHT, nicht verschluckt: Wer nur
    # «nicht geprueft» liest, weiss nicht, ob er etwas nachliefern kann.
    assert befund["satz"] in aus["satz"]


def test_die_angabe_wird_mit_der_vertragsfunktion_gelesen():
    """Keine zweite Deutung der Angabe — sonst gäbe es zwei Regeln, und eine wäre falsch.

    ``"Y_UP"`` muss durchgehen (der Vertrag lässt Zusätze zu), ``"Zeichnung"`` nicht (die
    Verschärfung vom 19.09.2026), ``None`` schon gar nicht.
    """
    befund = hochachse.hochachse_aus_knoten(GELAENDE_UND_HAUS)

    assert hochachse.gegenprobe("Y_UP", befund)["stimmt"] is True
    assert hochachse.gegenprobe("y", befund)["stimmt"] is True
    with pytest.raises(ContractError):
        hochachse.gegenprobe("Zeichnung", befund)
    with pytest.raises(ContractError):
        hochachse.gegenprobe(None, befund)


# --------------------------------------------------------------------------------------
# 6 · Aus der Datei heraus — derselbe Weg wie die Bauwerksbox, ohne Blender
# --------------------------------------------------------------------------------------

def test_aus_einer_glb_heraus_kommt_dieselbe_antwort(tmp_path):
    pfad = tmp_path / "szene.glb"
    pfad.write_bytes(_erzeuger().baue_glb(GELAENDE_UND_HAUS))

    aus_datei = hochachse.hochachse_aus_geometrie(pfad)
    aus_knoten = hochachse.hochachse_aus_knoten(GELAENDE_UND_HAUS)

    assert aus_datei["achse"] == aus_knoten["achse"] == "Y"
    assert aus_datei["staerke"] == pytest.approx(aus_knoten["staerke"])
    assert hochachse.gegenprobe_datei(pfad, "Z")["stimmt"] is False


def test_eine_z_up_datei_mit_angabe_Y_wird_beanstandet(tmp_path):
    """Der Vollzug des Befundes: Die Datei ist Z-up, die Angabe sagt Y — und niemand
    hätte es gemerkt, weil ``"Y"`` durch jeden Vertrag geht."""
    pfad = tmp_path / "szene_z.glb"
    pfad.write_bytes(_erzeuger().baue_glb(nach_z_up(GELAENDE_UND_HAUS)))

    aus = hochachse.gegenprobe_datei(pfad, "Y")

    assert aus["stimmt"] is False
    assert aus["gemessen"] == "Z"


def test_ein_mesh_ohne_min_max_beendet_die_messung_mit_None(tmp_path):
    """Auf einem Ausschnitt gemessen könnte gerade das Gelände fehlen.

    Dieselbe Weigerung wie in :func:`aiimaging.glbbox.bauwerksbox` — dort als Ausnahme,
    hier als ``None`` mit Grund, weil dieses Modul auf jede Frage antwortet.
    """
    roh = _erzeuger().baue_glb(GELAENDE_UND_HAUS)
    laenge = struct.unpack("<I", roh[12:16])[0]
    js = json.loads(roh[20:20 + laenge])
    del js["accessors"][0]["min"]
    neu = json.dumps(js, separators=(",", ":")).encode("utf-8")
    neu += b" " * (-len(neu) % 4)
    rest = roh[20 + laenge:]
    kopf = struct.pack("<III", glbbox.GLB_MAGIC, 2, 12 + 8 + len(neu) + len(rest))
    pfad = tmp_path / "kaputt.glb"
    pfad.write_bytes(kopf + struct.pack("<II", len(neu), glbbox.CHUNK_JSON) + neu + rest)

    befund = hochachse.hochachse_aus_geometrie(pfad)

    assert befund["achse"] is None
    assert befund["grund"] == hochachse.OHNE_GRENZEN
    assert "min/max" in befund["satz"]
    assert hochachse.gegenprobe("Y", befund)["stimmt"] is None


# --------------------------------------------------------------------------------------
# 7 · Was das Modul NICHT tut
# --------------------------------------------------------------------------------------

def test_die_formschwellen_stehen_nur_an_einer_stelle():
    """Dieses Modul setzt **keine** eigene Formschwelle.

    Die drei Zahlen, an denen ein Körper als Platte gilt, gehören
    :mod:`aiimaging.gelaendeform`. Stünden sie hier noch einmal, wäre eine der beiden
    Kopien beim nächsten Nachziehen falsch — und niemand wüsste welche.
    """
    quelle = (Path(hochachse.__file__)).read_text(encoding="utf-8")
    for verboten in ("GRUNDRISSANTEIL_MIN =", "FLACHHEIT_MAX =", "TIEFLAGE_MAX ="):
        assert verboten not in quelle, verboten
    # Und die geliehenen Schwellen sind die, die dort stehen — nicht abgeschriebene.
    assert gelaendeform.FLACHHEIT_MAX == 0.15
    assert gelaendeform.GRUNDRISSANTEIL_MIN == 0.25


def test_die_eigene_schwelle_ist_als_gesetzt_gekennzeichnet():
    """Jede Zahl in diesem Projekt sagt, ob sie GEMESSEN oder GESETZT ist."""
    quelle = (Path(hochachse.__file__)).read_text(encoding="utf-8")
    kopf = quelle.split("VORSPRUNG_MIN = ")[0]
    assert "GESETZT UND NICHT GEMESSEN" in kopf
    assert "Woran sie kippt" in kopf


def test_nichts_ist_verdrahtet():
    """Eine Gegenprobe, die ein Tor wird, bevor sie an echten Modellen gemessen ist,
    wäre genau der Fehler, den sie verhindern soll.

    Solange niemand dieses Modul aufruft, kann es auch nichts still verdrehen.
    """
    # Gesucht wird der IMPORT, nicht das Wort: «Hochachse» steht in halbem `src/` als
    # Fliesstext, und ein Test, der darauf anspringt, ist am naechsten Kommentar rot.
    muster = re.compile(r"^\s*(from\s+\.?\S*\s+import\s+[^\n]*\bhochachse\b"
                        r"|import\s+\S*\bhochachse\b)", re.MULTILINE)
    paket = Path(hochachse.__file__).parent
    rufer = sorted(p.name for p in paket.rglob("*.py")
                   if p.name != "hochachse.py"
                   and muster.search(p.read_text(encoding="utf-8")))
    assert rufer == [], (
        f"{rufer} ruft das Modul bereits auf. Der Einbau ist nicht entschieden — "
        f"siehe Modulkopf.")
