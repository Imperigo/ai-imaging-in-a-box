"""TIEFENSCHÄTZER — die Ist-Seite der Geometrie-QA, samt Lizenz je Modellgrösse.

Warum dieses Modul existiert
----------------------------
``geometrie_qa`` vergleicht zwei Tiefenkarten desselben Bildausschnitts:

* das **Soll** — von Blender aus der entworfenen Geometrie gerendert. Das haben wir;
  ``bildlesen`` liest es aus EXR oder PNG.
* das **Ist** — aus dem *erzeugten Bild* zurückgerechnet. Das fehlte vollständig.

Ohne die zweite Seite kann die Metrik nur Soll gegen Soll messen. Sie ist damit belegt,
aber nicht **angewandt** — sie sagt nichts über ein einziges erzeugtes Bild. Dieses Modul
schliesst genau dieses Loch.

Das Verfahren heisst **monokulare Tiefenschätzung**: Ein neuronales Netz schätzt aus
einem einzelnen RGB-Bild — ohne zweite Kamera, ohne Laser, ohne Bewegung — für jeden
Bildpunkt, wie weit das Gezeigte entfernt ist. „Monokular" heisst wörtlich einäugig: Es
gibt keine zweite Ansicht, aus der sich die Entfernung geometrisch berechnen liesse. Das
Netz schliesst sie aus dem, was es an Millionen Bildern gelernt hat. Es ist damit eine
**Schätzung** und keine Messung — der Unterschied ist für jede Auswertung mitzulesen
(``geometrie_qa``, Vorbehalt 6: ein Fehler der Schätzung ist von einer Halluzination des
Bildmodells hier nicht unterscheidbar).

Die Lizenzlage — und die geerbte Annahme, die wir nicht übernehmen
-------------------------------------------------------------------
``Depth-Anything-V2`` ist **nach Modellgrösse unterschiedlich lizenziert** (an den
Modellkarten geprüft, 2026-08-18):

* **Small (≈25 M Parameter): Apache-2.0** → unter Regel 1 zulässig. Die einzige
  brauchbare Wahl, und damit die Vorgabe.
* **Base, Large, Giant: CC-BY-NC-4.0** → *NonCommercial*. Unter Regel 1
  **ausgeschlossen**, genau wie FLUX.1-dev und FLUX.2-dev. Modellgewichte zählen mit.

Der Vorläufer KosmoVis benutzt **ViT-L (Large)** — also die Non-Commercial-Variante. Das
ist eine geerbte Annahme, und sie wird hier **nicht** übernommen. Alle vier Grössen
stehen trotzdem in der Registry: die drei ausgeschlossenen mit ``zulaessig=False`` und
voller Begründung, damit der Grund auffindbar bleibt und nicht jemand später „das nimmt
KosmoVis doch auch" denkt. Dieselbe Bauform und derselbe Grund wie bei DINOv3 in
``einbetter.py``.

Warum hier nicht in Meter zurückgerechnet wird
-----------------------------------------------
Eine geschätzte Tiefe hat einen **anderen Massstab und einen anderen Nullpunkt** als
echte Meter. Depth-Anything V2 liefert zudem *relative inverse* Tiefe — eine
**Disparität**: nah = grosser Wert, fern = kleiner Wert, also gegenüber Metern genau
umgekehrt sortiert.

Diese Zahlen in Meter umzurechnen verlangte zwei Grössen, die es nicht gibt: einen
Massstab und einen Nullpunkt. Wer sie setzt, erfindet sie — und bekommt eine Karte, die
aussieht wie eine Messung in Metern und keine ist. Das wäre **Scheingenauigkeit**, also
genau die Fehlerklasse, gegen die dieses Projekt durchgehend antritt.

Deshalb wird hier nichts umgerechnet. Die geschätzten Werte gehen **roh** in die Metrik,
und die Metrik ist dafür gebaut: ``geometrie_qa`` misst rangbasiert (nur die
*Reihenfolge* zählt, nicht der Wert) und wertet ``abs(spearman)`` (das Vorzeichen einer
Disparität ist eine Konvention, kein Geometriefehler). Eine treue, aber invertierte
Schätzung erhält dort denselben Score wie eine treue nicht invertierte —
``tests/test_tiefenschaetzer.py`` belegt das.

Die Silhouettenfrage — die eigentliche Entscheidung dieses Moduls
------------------------------------------------------------------
Ein Renderer schreibt für „Strahl hat nichts getroffen" eine Marke: ``inf`` oder 1e10.
Ein **Schätzer tut das nicht.** Er liefert für den Himmel eine ganz gewöhnliche endliche
Zahl — er weiss nicht, dass dort nichts ist, er schätzt dort nur „sehr weit weg".

Damit steht die Ist-Silhouette ohne Zutun auf dem **ganzen Bild**, und ``geom_iou`` wird
strukturell zu klein: Deckt der Bau 30 % des Bildes, ist ``geom_iou`` nach oben durch
0.30 begrenzt, der Score durch ``sqrt(0.30) ≈ 0.55`` — unter der Schwelle 0.65, egal wie
treu das Bild ist. ``geometrie_qa`` benennt das als Vorbehalt 7 und schiebt die Lösung
ausdrücklich hierher: „Die Hintergrundmarke gehört vor dem Aufruf gesetzt — an der
Prozessgrenze, wo das Bild gelesen wird." Das ist dieses Modul.

Drei Wege stehen offen, und keiner ist gratis:

1. :data:`HG_KEINE` — gar nichts markieren. Erfindet nichts, ist aber, wie eben gezeigt,
   strukturell zu streng: Das Gate fällt fast immer durch, und zwar aus einem Grund, der
   nichts mit dem Bild zu tun hat. Ein Urteil, das immer gleich ausfällt, ist kein Urteil.
2. :data:`HG_QUANTIL` — einen festen Anteil des Bildes (etwa „die fernsten 40 %") zum
   Hintergrund erklären. Verlangt eine Annahme über die Himmelsfläche, die niemand hat.
   Bleibt für Fälle, in denen es kein Soll gibt.
3. :data:`HG_WIE_SOLL` — bis 18.08.2026 die Vorgabe in :func:`qa_gegen_soll`. Die Soll-Karte kennt
   ihren Hintergrund exakt; daraus ist die **Anzahl** der Geometriepunkte bekannt. Genau
   so viele Punkte der Ist-Karte werden auf der Geometrieseite behalten, der Rest als
   Hintergrund markiert.

**Warum 3 gewählt ist, und was es kostet.** Die Anzahl wird nicht geraten, sondern der
einzigen Quelle entnommen, die sie wirklich kennt. Der Preis ist präzise benennbar und
wird in jedem Ergebnis unter ``unsicherheit`` mitgeführt: Weil ``n_ist`` per Konstruktion
gleich ``n_soll`` ist, misst ``geom_iou`` nur noch die **Lage** der Silhouette, nicht mehr
ihre **Grösse**. Ein erfundenes Gebäude an der falschen Stelle fällt weiterhin auf — bei
gleicher Punktzahl ist ``iou = |A∩B| / (2·|A| − |A∩B|)``, das geht bei fehlender Deckung
gegen 0. Ein Gebäude an der richtigen Stelle, aber doppelt so gross, fällt **nicht** mehr
auf; es wird auf die richtige Punktzahl beschnitten.

Das ist eine Vereinbarung, keine Messung — und sie wird als solche gemeldet, nicht
versteckt. Wer die Grössenprüfung braucht, nimmt :data:`HG_KEINE` und liest
``geom_iou_obergrenze``, die dort mitgeliefert wird.

**Auf welcher Seite der Hintergrund liegt**, hängt an der Polarität des Schätzers: Bei
Disparität (nah = gross) sind die **kleinsten** Werte Himmel, bei metrischer Tiefe die
**grössten**. Die Polarität steht darum im Registry-Eintrag und wird nicht aus den Daten
erraten — ein Rateschluss wäre zirkulär, weil er genau die Ordnung voraussetzt, die
gemessen werden soll. Bei :data:`POLARITAET_UNBEKANNT` wird nicht markiert, sondern
abgebrochen.

Was dieses Modul nicht belegt
------------------------------
Hier gibt es weder GPU noch Gewichte. Geprüft ist alles, was **entscheidbar** ist:
Lizenzen, Registry, Hintergrundmarkierung, Längen- und Formprüfungen, der Bogen zur
Metrik. **Nicht belegt** ist alles, was echte Gewichte verlangt: dass der Schätzer
Architekturbilder brauchbar staffelt, welche Scores treue und halluzinierte Renders
tatsächlich erreichen, und ob die Schwelle 0.65 auf dieser Naht überhaupt trennt. Der
:func:`_pipeline_adapter` ist die einzige Funktion des Moduls, die hier nie ausgeführt
werden kann; sie ist deshalb so kurz wie möglich gehalten.

Abhängigkeiten: reine stdlib. ``torch``/``transformers`` werden **ausschliesslich lokal
in** :func:`lade_modell` **importiert** — auf Modulebene machten sie
``import aiimaging.tiefenschaetzer`` auf jedem Rechner ohne GPU-Stack unmöglich und damit
auch jeden Test darüber. Kein ``bpy``, kein ``ifcopenshell`` (Regel 2).
"""
from __future__ import annotations

import math
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from aiimaging import geometrie_qa

# Dieselbe Vokabel für die Herkunft einer Lizenzangabe wie in `backbone` und `einbetter`.
# Sie lag bis zum 18.08.2026 nur in `backbone`, und dieses Modul trug stattdessen freien
# Text — dieselbe Sache in drei Schreibweisen (Prüfbericht Abschnitt 5).
from aiimaging import lizenzquelle
from aiimaging.lizenzquelle import QUELLE_UNGEPRUEFT, hinweis_zur_herkunft, ist_belegt

#: Lizenzen, die Regel 1 zulässt. Wortgleich mit :data:`aiimaging.einbetter.ZUGELASSENE_LIZENZEN`
#: — bewusst noch einmal hier, damit dieses Modul für sich lesbar bleibt.
ZUGELASSENE_LIZENZEN = frozenset(
    {"MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "MPL-2.0"}
)

#: Schätzer liefert *relative inverse* Tiefe (Disparität): nah = grosser Wert.
#: Der Hintergrund liegt damit bei den **kleinsten** Werten.
POLARITAET_DISPARITAET = "disparitaet"

#: Schätzer liefert Tiefe im üblichen Sinn: nah = kleiner Wert. Hintergrund bei den
#: **grössten** Werten.
POLARITAET_TIEFE = "tiefe"

#: Polarität nicht deklariert. Es wird dann nicht geraten, sondern abgebrochen.
POLARITAET_UNBEKANNT = "unbekannt"

POLARITAETEN = (POLARITAET_DISPARITAET, POLARITAET_TIEFE, POLARITAET_UNBEKANNT)

#: Hintergrundstrategie: gar nichts markieren. Ehrlich, aber strukturell zu streng —
#: siehe Modul-Docstring.
HG_KEINE = "keine"

#: Hintergrundstrategie: die extremsten ``anteil`` des Bildes auf der Hintergrundseite
#: markieren. Verlangt eine Annahme über die Himmelsfläche.
HG_QUANTIL = "quantil"

#: Hintergrundstrategie: genau so viele Punkte Geometrie behalten, wie die Soll-Karte
#: hat. Nur mit einem Soll verfügbar, denn nur dort gibt es die Anzahl.
#:
#: **War bis zum 18.08.2026 die Vorgabe in** :func:`qa_gegen_soll` **und ist es nicht
#: mehr.** Am Gerät gemessen (`auf-20260818-12`) lagen damit nur **40,7 %** der gewählten
#: Punkte auf dem Bauwerk — der Rest war eine vom Schätzer in den leeren Grund gelegte
#: Bodenebene. Die Regel wählt nach Nähe und fragt nicht, **wo** die nahen Punkte liegen;
#: siehe :data:`HG_OHNE_RANDBERUEHRUNG`.
HG_WIE_SOLL = "wie_soll"

#: Hintergrundstrategie: wie :data:`HG_WIE_SOLL`, aber anschliessend werden alle
#: zusammenhängenden Flächen verworfen, die den **Bildrand berühren**.
#:
#: **AM GERÄT GEMESSEN** (``auf-20260818-12``, HomeStation, 18.08.2026), an Blenders
#: eigenem Beauty-Pass — einem Bild, das die Geometrie exakt zeigt:
#:
#:     Regel                  geom_iou   Score    Punkte auf dem Bauwerk
#:     wie_soll (bis dahin)     0.256    0.504          40.7 %
#:     groesste_flaeche         0.000     n/a            0.0 %
#:     ohne_randberuehrung      0.406    0.635          99.2 %
#:     rand_10                  0.366    0.603          53.6 %
#:     nur_spearman_in_soll     1.000    0.997         100.0 %
#:
#: **Warum es wirkt:** Der Fehler war nie der Schätzer, sondern die *Ortlosigkeit* der
#: Auswahl. ``wie_soll`` nimmt die n nächsten Punkte, gleich wo sie liegen; ein
#: monokularer Schätzer legt aber in eine flache Fläche eine Bodenebene, die zur Bildecke
#: hin auf die Kamera zuläuft, und dieser Keil verdrängt echte Bauwerkspunkte eins zu
#: eins. Die Randberührung ist genau das Merkmal, das ihn unterscheidet: Ein
#: freistehender Baukörper in der Bildmitte berührt den Rand nicht, eine
#: hineinhalluzinierte Bodenebene immer.
#:
#: **Der lehrreiche Gegenkandidat:** ``groesste_flaeche`` — der naheliegendste Filter und
#: der, den man ohne Messung gebaut hätte — fällt komplett durch: **0 %** der gewählten
#: Punkte liegen auf dem Bauwerk. Die grösste zusammenhängende Fläche der „nächsten n"
#: *ist* der Hintergrundkeil. Eingebaut statt gemessen wäre die Lage schlechter gewesen
#: als vorher, und der Grund unauffindbar.
#:
#: **Und der, der zu gut aussah:** ``nur_spearman_in_soll`` erreicht am perfekten Bild
#: 0.997 — aber auch 0.79 und 0.65 an den *gestörten* Karten. Es hat den **kleinsten**
#: Abstand zwischen treu und gestört von allen sechs Regeln und ist damit genau die Sorte
#: Verbesserung, die alles nach oben schiebt statt zu trennen. ``ohne_randberuehrung``
#: gewinnt auf **beiden** Achsen: höchster treuer Score UND grösster Abstand.
#:
#: **Ehrliche Grenze:** Auch damit erreicht das perfekte Bild nur 0.635 und bleibt knapp
#: unter der Schwelle 0.65. Der Deckel ist gehoben, nicht beseitigt.
#:
#: **Und der Vorbehalt hat sich bewahrheitet (20.08.2026, `auf-20260819-15`).** Hier stand:
#: *„an einer Szene mit echtem Gelände ist die Regel ungeprüft".* Sie ist jetzt geprüft,
#: an drei Szenen mit Boden, und wählt in **allen dreien null Punkte** — sobald ein Boden
#: da ist, berührt jede Fläche den Rand.
#:
#: Die Regel ist damit **kein Vorgabewert mehr**, sondern das Werkzeug für genau einen
#: Fall: eine freigestellte Szene ohne Grund, in der eine grosse randberührende Fläche
#: wirklich eine Halluzination ist. Wer sie wählt, soll wissen, was er wählt.
HG_OHNE_RANDBERUEHRUNG = "ohne_randberuehrung"

#: Vorgabe von :func:`qa_gegen_soll`: :data:`HG_WIE_SOLL`.
#:
#: **Zurückgenommen am 20.08.2026.** Vom 18. bis zum 20.08. stand hier
#: :data:`HG_OHNE_RANDBERUEHRUNG`, sobald die Bildmasse bekannt waren. Das war an einer
#: Szene **ohne Boden** gemessen, und der Docstring jener Regel trug den Vorbehalt
#: wörtlich: *„an einer Szene mit echtem Gelände ist die Regel ungeprüft".*
#:
#: `auf-20260819-15` hat sie geprüft, an vier Szenen. Das Ergebnis ist eindeutig:
#:
#: =====================  ==================  ===========================
#: Szene                  ``wie_soll``        ``ohne_randberuehrung``
#: =====================  ==================  ===========================
#: ohne Boden             iou 0.256           iou **0.406** (besser)
#: Platte, endlich        iou 0.967           **0 Punkte gewählt**
#: Ebene bis zum Rand     iou 0.974           **0 Punkte gewählt**
#: Ebene mit Horizont     iou 1.000           **0 Punkte gewählt**
#: =====================  ==================  ===========================
#:
#: **Sobald ein Boden da ist, berührt jede Fläche den Rand.** Die Regel gewann in
#: `auf-20260818-12`, *weil* die Szene keinen Boden hatte — dort verwarf sie eine
#: Halluzination. In jeder Szene mit Gelände verwirft sie **richtige Geometrie**, und zwar
#: restlos: kein einziger Punkt bleibt übrig, ``score`` ist ``None``.
#:
#: Ein echtes Gebäude steht auf dem Boden. Die Vorgabe ist damit zurückgenommen; die Regel
#: bleibt **wählbar** für den Fall, den sie wirklich löst — eine freigestellte Szene.
#:
#: *Die Lehre, und sie ist dieselbe wie beim Blender-Takt drei Tage später: Eine Messung
#: gilt so weit, wie gemessen wurde. Der Vorbehalt stand da, und er war die halbe
#: Erkenntnis.*
HG_VORGABE = "vorgabe"

HG_STRATEGIEN = (HG_KEINE, HG_QUANTIL, HG_WIE_SOLL, HG_OHNE_RANDBERUEHRUNG)

#: Was ein Aufrufer angeben darf — die Strategien plus die auflösende Vorgabe.
HG_WAEHLBAR = HG_STRATEGIEN + (HG_VORGABE,)


def loese_strategie(strategie: str, *, breite=None, hoehe=None) -> tuple[str, tuple]:
    """:data:`HG_VORGABE` in eine wirkliche Strategie auflösen.

    Returns:
        ``(strategie, warnungen)``. Jede andere Angabe kommt unverändert zurück — die
        Wahl des Aufrufers wird nicht überstimmt, auch nicht zu seinem Besten.
    """
    if strategie != HG_VORGABE:
        return strategie, ()
    return HG_WIE_SOLL, ()

#: Anteil des Bildes, den :data:`HG_QUANTIL` ohne eigene Angabe als Hintergrund wertet.
#:
#: 0.4 ist eine **Setzung**, kein Messwert: In den Aussenperspektiven, um die es geht,
#: nimmt Himmel grob ein Drittel bis die Hälfte des Bildes ein. Die Zahl ist der Grund,
#: warum diese Strategie nicht die Vorgabe ist — sie behauptet etwas über das Bild, das
#: niemand geprüft hat.
HG_QUANTIL_VORGABE = 0.4

STATUS_OK = "ok"
STATUS_ABGELEHNT = "abgelehnt"
STATUS_FEHLER = "fehler"
STATUSSE = (STATUS_OK, STATUS_ABGELEHNT, STATUS_FEHLER)

#: Kurzform des Rechenwegs, wandert in jedes Ergebnis — wie ``geometrie_qa.METHODE``.
METHODE_IST = (
    "monokulare Tiefenschaetzung, Rohwerte ohne Umrechnung in Meter, "
    "Hintergrund per Vereinbarung markiert, v1"
)


class TiefenschaetzerError(ValueError):
    """Ein Schätzer ist unbekannt, unter Regel 1 nicht zulässig, oder die Eingabe taugt nicht.

    Erbt von ``ValueError``, damit bestehendes ``except ValueError`` weiter greift —
    dieselbe Entscheidung wie bei :class:`aiimaging.geometrie_qa.QaError`.
    """


# --------------------------------------------------------------------------------------
# Die Registry
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Tiefenschaetzer:
    """Ein monokularer Tiefenschätzer samt Lizenzlage.

    ``zulaessig`` ist bewusst ein eigenes Feld und nicht aus ``lizenz`` abgeleitet: Die
    Begründung ist länger als „Lizenz nicht in der Liste", und sie soll am Modell stehen
    und nicht im Kopf des Lesers. Dieselbe Bauform wie
    :class:`aiimaging.einbetter.Einbetter`.

    Args:
        name: Schlüssel in :data:`TIEFENSCHAETZER`.
        modell_id: Hugging-Face-Repo-Kennung.
        lizenz: Lizenz der **Gewichte**, nicht des Codes. Genau hier trennen sich die
            vier Depth-Anything-Grössen.
        zulaessig: Ob der Schätzer unter Regel 1 verwendet werden darf.
        begruendung: Warum — in Klartext, auch und gerade beim Ausschluss.
        parameter_m: Parameterzahl in Millionen. Grössenordnung, kein Datenblatt.
        polaritaet: Einer der Werte aus :data:`POLARITAETEN`. Entscheidet, auf welcher
            Seite der Werte der Hintergrund liegt.
        lizenz_quelle: Wie gut die Lizenzangabe belegt ist — eine der Vokabeln aus
            :mod:`aiimaging.lizenzquelle` oder ein Vermerk der Form
            ``"geprueft <datum> (<url>)"``. Ob ein Wert ein Beleg ist, beantwortet
            :func:`aiimaging.lizenzquelle.ist_belegt` und kein Vergleich von Hand.

    ``frozen=True``: Die Registry ist ein Nachschlagewerk und kein Zustand. Ein
    versehentliches ``TIEFENSCHAETZER["..."].zulaessig = True`` an irgendeiner Stelle im
    Programm hebelte Regel 1 lautlos aus.
    """

    name: str
    modell_id: str
    lizenz: str
    zulaessig: bool
    begruendung: str
    parameter_m: float
    polaritaet: str = POLARITAET_UNBEKANNT
    lizenz_quelle: str = QUELLE_UNGEPRUEFT


#: Der Satz, der bei allen drei ausgeschlossenen Grössen gleich lautet. Ausgelagert,
#: damit sich die Begründung nicht dreimal auseinanderentwickeln kann.
_NC_GRUND = (
    "AUSGESCHLOSSEN unter Regel 1: CC-BY-NC-4.0 ist eine NonCommercial-Lizenz und damit "
    "keine der vier permissiven (MIT, Apache-2.0, BSD, MPL-2.0). Modellgewichte zaehlen "
    "unter Regel 1 mit — derselbe Grund, aus dem FLUX.1-dev und FLUX.2-dev ausscheiden. "
    "Bemerkenswert ist die Aufteilung: Bei Depth-Anything-V2 haengt die Lizenz an der "
    "MODELLGROESSE, nicht am Projekt. Nur Small ist Apache-2.0. "
    "KosmoVis verwendet ViT-L (Large) und damit die NC-Variante; wir uebernehmen diese "
    "geerbte Annahme bewusst NICHT."
)

TIEFENSCHAETZER: dict[str, Tiefenschaetzer] = {
    "depth-anything-v2-small": Tiefenschaetzer(
        name="depth-anything-v2-small",
        modell_id="depth-anything/Depth-Anything-V2-Small-hf",
        lizenz="Apache-2.0",
        zulaessig=True,
        begruendung=(
            "Apache-2.0, nicht gated, keine Auflagen — erfuellt Regel 1 unmittelbar. "
            "Die einzige Depth-Anything-V2-Groesse, die das tut, und damit die Vorgabe. "
            "Der Preis ist Genauigkeit: ~25 M Parameter gegen ~335 M bei Large. Wie viel "
            "das an Architekturbildern ausmacht, ist HIER NICHT GEPRUEFT und gehoert auf "
            "die HomeStation."
        ),
        parameter_m=24.8,
        polaritaet=POLARITAET_DISPARITAET,
        # Nachgeprueft 2026-08-18: Front-Matter "license: apache-2.0", Repo offen.
        lizenz_quelle="geprueft 2026-08-18 (https://huggingface.co/depth-anything/Depth-Anything-V2-Small-hf)",
    ),
    "depth-anything-v2-base": Tiefenschaetzer(
        name="depth-anything-v2-base",
        modell_id="depth-anything/Depth-Anything-V2-Base-hf",
        lizenz="CC-BY-NC-4.0",
        zulaessig=False,
        begruendung=_NC_GRUND,
        parameter_m=97.5,
        polaritaet=POLARITAET_DISPARITAET,
        # Nachgeprueft 2026-08-18: Front-Matter "license: cc-by-nc-4.0", Repo offen.
        lizenz_quelle="geprueft 2026-08-18 (https://huggingface.co/depth-anything/Depth-Anything-V2-Base-hf)",
    ),
    "depth-anything-v2-large": Tiefenschaetzer(
        name="depth-anything-v2-large",
        modell_id="depth-anything/Depth-Anything-V2-Large-hf",
        lizenz="CC-BY-NC-4.0",
        zulaessig=False,
        begruendung=(
            _NC_GRUND
            + " Dies ist genau die Groesse, die der Vorlaeufer KosmoVis einsetzt (ViT-L)."
        ),
        parameter_m=335.3,
        polaritaet=POLARITAET_DISPARITAET,
        # Nachgeprueft 2026-08-18: Front-Matter "license: cc-by-nc-4.0", Repo offen.
        lizenz_quelle="geprueft 2026-08-18 (https://huggingface.co/depth-anything/Depth-Anything-V2-Large-hf)",
    ),
    "depth-anything-v2-giant": Tiefenschaetzer(
        name="depth-anything-v2-giant",
        modell_id="depth-anything/Depth-Anything-V2-Giant-hf",
        lizenz="CC-BY-NC-4.0",
        zulaessig=False,
        begruendung=(
            _NC_GRUND
            + " Die Verfuegbarkeit der Giant-Gewichte ist eine andere Frage als ihre "
            "Lizenz; beantwortet werden muss hier nur die Lizenz, und die schliesst aus."
        ),
        parameter_m=1300.0,
        polaritaet=POLARITAET_DISPARITAET,
        # Sonderfall, geprueft 2026-08-18: Das oben eingetragene Repo
        # "depth-anything/Depth-Anything-V2-Giant-hf" ist oeffentlich NICHT erreichbar
        # (HTTP 401, und die HF-Suche nach "Depth-Anything-V2-Giant" liefert nichts).
        # Belegt ist die Lizenz darum nicht an einer Modellkarte, sondern am
        # LICENSE-Abschnitt des Projekt-README der Autoren: "Depth-Anything-V2-Small model
        # is under the Apache-2.0 license. Depth-Anything-V2-Base/Large/Giant models are
        # under the CC-BY-NC-4.0 license."
        lizenz_quelle="geprueft 2026-08-18 (https://github.com/DepthAnything/Depth-Anything-V2 — README, Abschnitt LICENSE; HF-Repo nicht oeffentlich)",
    ),
}

#: Vorgabe. Small, weil es die einzige Groesse unter Apache-2.0 ist — nicht, weil sie
#: die beste waere. Regel 1 entscheidet vor der Technik.
VORGABE_TIEFENSCHAETZER = "depth-anything-v2-small"


def hole(name: str) -> Tiefenschaetzer:
    """Einen Schätzer nachschlagen. Unbekannter Name ist ein Fehler, kein ``None``."""
    try:
        return TIEFENSCHAETZER[name]
    except (KeyError, TypeError):
        raise TiefenschaetzerError(
            f"Unbekannter Tiefenschaetzer {name!r}. Bekannt: "
            f"{', '.join(sorted(TIEFENSCHAETZER))}"
        ) from None


def pruefe_lizenz(name: str) -> dict:
    """Die Lizenzlage eines Schätzers — für den ausführbaren Pfad, nicht nur zum Lesen.

    ``lizenz_belegt`` und ``lizenz_hinweis`` sind am 18.08.2026 dazugekommen. Vorher gab
    dieses Modul die Herkunft nur als Text weiter, und wer wissen wollte, ob sie ein Beleg
    ist, musste selbst auf Zeichenketten suchen. Genau diese Suche ist in ``backbone``
    schiefgegangen (Prüfbericht Abschnitt 5) — die Antwort gehört als Datum in den Satz.

    ``lizenz_hinweis`` ist ``None``, wenn die Angabe belegt ist; sonst benennt es die
    Lücke. Über die Zulässigkeit sagt es nichts: Das entscheidet ``zulaessig``, und ein
    belegter Ausschluss (Base, Large, Giant) ist ein besonders gut belegter.
    """
    t = hole(name)
    return {
        "regel_1_spannung": lizenzquelle.regel_1_spannung(t.name, t.lizenz, t.zulaessig),
        "name": t.name,
        "modell_id": t.modell_id,
        "lizenz": t.lizenz,
        "zulaessig": t.zulaessig,
        "begruendung": t.begruendung,
        "parameter_m": t.parameter_m,
        "lizenz_quelle": t.lizenz_quelle,
        "lizenz_belegt": ist_belegt(t.lizenz_quelle),
        "lizenz_hinweis": hinweis_zur_herkunft(t.lizenz_quelle),
    }


def waehle(*, nur_zulaessige: bool = True) -> list[Tiefenschaetzer]:
    """Die verwendbaren Schätzer.

    Mit ``nur_zulaessige=True`` (Vorgabe) erscheinen Base, Large und Giant **nicht** —
    Regel 1 in ausführbarer Form, wie bei :func:`aiimaging.einbetter.waehle`. Ohne Filter
    erscheinen sie doch, damit die Registry vollständig einsehbar bleibt und der
    Ausschluss auffindbar ist.
    """
    kandidaten = list(TIEFENSCHAETZER.values())
    if nur_zulaessige:
        kandidaten = [t for t in kandidaten if t.zulaessig]
    return kandidaten


def fordere_zulaessigen(name: str) -> Tiefenschaetzer:
    """Einen Schätzer holen und ablehnen, wenn er unter Regel 1 nicht zulässig ist.

    Raises:
        TiefenschaetzerError: mit der vollen Begründung aus der Registry — nicht nur
            „geht nicht", sondern warum, und mit dem Hinweis auf KosmoVis, damit der
            Ausschluss nicht in der nächsten Sitzung erneut diskutiert wird.
    """
    t = hole(name)
    if not t.zulaessig:
        raise TiefenschaetzerError(
            f"{t.name} ist unter Regel 1 nicht zulaessig: {t.begruendung}"
        )
    return t


# --------------------------------------------------------------------------------------
# Hintergrund markieren — die Entscheidung dieses Moduls, als Funktion
# --------------------------------------------------------------------------------------

def _als_zahlen(werte, name: str) -> list[float]:
    """Eingabefolge → Liste von ``float``; nicht-endliche Werte bleiben erhalten.

    Dieselbe Strenge wie :func:`aiimaging.geometrie_qa._als_zahlen`, und aus denselben
    Gründen: Generatoren wären nach dem ersten Durchlauf leer, ``bool`` ist als Tiefenwert
    immer ein Irrtum, und ``"27.3"`` stillschweigend zu deuten wäre eine Reparatur mit
    erfundenem Ergebnis. Wiederholt statt importiert, weil ein privater Name eines
    Nachbarmoduls kein Vertrag ist.
    """
    if isinstance(werte, (str, bytes, bytearray)) or not isinstance(werte, Sequence):
        raise TiefenschaetzerError(
            f"{name}: Sequenz von Zahlen erwartet (Liste oder Tupel), war "
            f"{type(werte).__name__}. Generatoren sind nicht zulaessig — sie waeren nach "
            f"dem ersten Durchlauf leer."
        )
    zahlen: list[float] = []
    for i, wert in enumerate(werte):
        if isinstance(wert, bool) or not isinstance(wert, (int, float)):
            raise TiefenschaetzerError(
                f"{name}[{i}]: Zahl erwartet, war {wert!r} ({type(wert).__name__}). "
                f"Es wird nichts umgedeutet."
            )
        zahlen.append(float(wert))
    return zahlen


def _verwirf_randflaechen(werte, breite: int, hoehe: int):
    """Jede zusammenhängende Geometriefläche verwerfen, die den Bildrand berührt.

    Vierer-Nachbarschaft, nicht Achter: Zwei Flächen, die sich nur über eine Ecke
    berühren, sind im Bild getrennt. Mit Achter-Nachbarschaft genügte ein einziger
    diagonaler Kontakt zwischen Bauwerk und Bodenkeil, damit beide gemeinsam verworfen
    würden — die Regel wäre an einer einzigen Pixelecke zerbrechlich.

    Iterativ (Stapel) statt rekursiv: Bei 512 × 512 = 262 144 Punkten kann eine Fläche
    das halbe Bild umfassen, und eine Rekursion dieser Tiefe erreicht Pythons Grenze.

    Returns:
        ``(neue_werte, anzahl_verworfener_flaechen)``. Die Eingabe bleibt unverändert.
    """
    ergebnis = list(werte)
    gesehen = bytearray(len(werte))
    verworfen = 0

    for start in range(len(werte)):
        if gesehen[start] or not math.isfinite(werte[start]):
            continue
        flaeche = []
        stapel = [start]
        gesehen[start] = 1
        am_rand = False
        while stapel:
            i = stapel.pop()
            flaeche.append(i)
            y, x = divmod(i, breite)
            if x == 0 or y == 0 or x == breite - 1 or y == hoehe - 1:
                am_rand = True
            if x > 0 and not gesehen[i - 1] and math.isfinite(werte[i - 1]):
                gesehen[i - 1] = 1
                stapel.append(i - 1)
            if x < breite - 1 and not gesehen[i + 1] and math.isfinite(werte[i + 1]):
                gesehen[i + 1] = 1
                stapel.append(i + 1)
            if y > 0 and not gesehen[i - breite] and math.isfinite(werte[i - breite]):
                gesehen[i - breite] = 1
                stapel.append(i - breite)
            if y < hoehe - 1 and not gesehen[i + breite] and math.isfinite(werte[i + breite]):
                gesehen[i + breite] = 1
                stapel.append(i + breite)
        if am_rand:
            verworfen += 1
            for i in flaeche:
                ergebnis[i] = math.inf
    return ergebnis, verworfen


def markiere_hintergrund(tiefen: Sequence[float], *, polaritaet: str,
                         strategie: str = HG_KEINE, anteil: float | None = None,
                         n_geometrie: int | None = None,
                         breite: int | None = None, hoehe: int | None = None,
                  maske: Sequence[bool] | None = None) -> dict:
    """Aus einer geschätzten Karte eine Karte mit **Hintergrundmarke** machen.

    Markiert wird durch Ersetzen mit ``math.inf``. Das ist kein Trick, sondern die
    Konvention, die ``geometrie_qa.silhouette`` ohnehin liest — und dieselbe, mit der
    ``bildlesen._rueckrechnen`` den Grauwert 0 behandelt. Der Vorteil gegenüber einer
    Zahlenschwelle: Sie funktioniert unabhängig davon, ob die Rohwerte Disparitäten in
    ``0..1`` oder Tiefen in Metern sind, und unabhängig vom Parameter ``hintergrund``,
    den der Aufrufer später an die Metrik gibt.

    Args:
        tiefen: Rohwerte des Schätzers, zeilenweise von oben. Werden nicht umgerechnet.
        polaritaet: Einer aus :data:`POLARITAETEN`. Bestimmt, auf welcher Seite der
            Werteordnung der Hintergrund liegt: bei Disparität die **kleinsten** Werte,
            bei Tiefe die **grössten**. Wird nicht aus den Daten erraten — ein Rateschluss
            setzte genau die Ordnung voraus, die gemessen werden soll.
        strategie: :data:`HG_KEINE`, :data:`HG_QUANTIL` oder :data:`HG_WIE_SOLL`.
        anteil: nur für :data:`HG_QUANTIL` — Anteil des Bildes, der als Hintergrund gilt,
            in ``(0, 1)``. ``None`` nimmt :data:`HG_QUANTIL_VORGABE`.
        n_geometrie: für :data:`HG_WIE_SOLL` und :data:`HG_OHNE_RANDBERUEHRUNG` —
            Anzahl Geometriepunkte der Soll-Karte.
        breite, hoehe: Bildmasse in Punkten. **Pflicht** für
            :data:`HG_OHNE_RANDBERUEHRUNG`: Ohne sie ist nicht entscheidbar, welcher
            Punkt am Rand liegt, und genau darauf beruht die Regel.

    Returns:
        ``{tiefen, strategie, polaritaet, n_punkte, n_hintergrund, anteil_hintergrund,
        n_bereits_nicht_endlich, unsicherheit, warnungen}``

        ``tiefen`` ist eine **neue** Liste; die Eingabe bleibt unverändert. Das ist
        wichtig, weil der Aufrufer dieselbe Rohkarte mit zwei Strategien vergleichen
        können soll, ohne sie zweimal schätzen zu lassen.

        ``unsicherheit`` nennt in Klartext, was diese Markierung **behauptet** statt misst.
        Sie ist bei jeder Strategie nicht leer — auch bei :data:`HG_KEINE`, denn auch
        „nichts markieren" ist eine Entscheidung mit Folgen.

    Raises:
        TiefenschaetzerError: unbekannte Strategie oder Polarität, leere Karte,
            unbrauchbares ``anteil``/``n_geometrie``, oder eine Markierung ohne
            deklarierte Polarität. Letzteres ist der wichtigste Fall: Ohne zu wissen, auf
            welcher Seite der Himmel liegt, schnitte die Markierung mit 50 %
            Wahrscheinlichkeit **das Gebäude** heraus statt des Himmels — und zwar
            lautlos.
    """
    if strategie not in HG_STRATEGIEN:
        raise TiefenschaetzerError(
            f"Unbekannte Hintergrundstrategie {strategie!r}. Erlaubt: "
            f"{', '.join(HG_STRATEGIEN)}. Es wird nicht auf die Vorgabe zurueckgesetzt — "
            f"welche Deutung gilt, kann dieses Modul nicht fuer den Aufrufer entscheiden."
        )
    if polaritaet not in POLARITAETEN:
        raise TiefenschaetzerError(
            f"Unbekannte Polaritaet {polaritaet!r}. Erlaubt: {', '.join(POLARITAETEN)}."
        )

    werte = _als_zahlen(tiefen, "tiefen")
    n = len(werte)
    if n == 0:
        raise TiefenschaetzerError(
            "Leere Tiefenkarte — es gibt nichts zu markieren und nichts zu messen."
        )

    bereits = [i for i, w in enumerate(werte) if not math.isfinite(w)]
    warnungen: list[str] = []
    unsicherheit: list[str] = []

    if bereits:
        warnungen.append(
            f"{len(bereits)} von {n} geschaetzten Werten sind nicht endlich (NaN/inf). "
            f"Ein Schaetzer sollte das nicht liefern; sie gelten hier als Hintergrund."
        )

    if strategie == HG_KEINE:
        ziel = len(bereits)
        unsicherheit.append(
            "Es wurde KEIN Hintergrund markiert. Die Ist-Silhouette traegt damit das "
            "ganze Bild, und geom_iou ist nach oben durch den Bildanteil der "
            "Soll-Geometrie begrenzt (Feld 'geom_iou_obergrenze'). Das Urteil faellt "
            "dadurch strukturell zu streng aus — aus einem Grund, der nicht am Bild liegt."
        )
    elif strategie == HG_QUANTIL:
        wert = HG_QUANTIL_VORGABE if anteil is None else anteil
        if isinstance(wert, bool) or not isinstance(wert, (int, float)):
            raise TiefenschaetzerError(
                f"anteil: Zahl oder None erwartet, war {wert!r} ({type(wert).__name__})."
            )
        wert = float(wert)
        if not math.isfinite(wert) or not 0.0 < wert < 1.0:
            raise TiefenschaetzerError(
                f"anteil muss echt zwischen 0 und 1 liegen, war {wert!r}. 0 markierte "
                f"nichts, 1 erklaerte das ganze Bild zum Himmel."
            )
        ziel = int(round(wert * n))
        unsicherheit.append(
            f"Hintergrund per Quantil: Die {wert:.0%} extremsten Werte auf der "
            f"Hintergrundseite gelten als Himmel. Das ist eine ANNAHME ueber die "
            f"Himmelsflaeche dieses Bildes, keine Messung. Stimmt sie nicht, verschiebt "
            f"sich geom_iou in beide Richtungen."
        )
    else:                                    # HG_WIE_SOLL und HG_OHNE_RANDBERUEHRUNG
        if isinstance(n_geometrie, bool) or not isinstance(n_geometrie, int):
            raise TiefenschaetzerError(
                f"n_geometrie: ganze Zahl erwartet, war {n_geometrie!r} "
                f"({type(n_geometrie).__name__}). Die Strategie {strategie!r} braucht "
                f"die Punktzahl der Soll-Silhouette — ohne Soll gibt es sie nicht."
            )
        if not 0 <= n_geometrie <= n:
            raise TiefenschaetzerError(
                f"n_geometrie={n_geometrie} passt nicht zu einer Karte mit {n} Punkten."
            )
        ziel = n - n_geometrie
        unsicherheit.append(
            "Hintergrund nach Vorbild der Soll-Silhouette: Die Ist-Karte behaelt genau "
            "so viele Geometriepunkte, wie das Soll hat. Damit misst geom_iou nur noch "
            "die LAGE der Silhouette, nicht mehr ihre GROESSE — ein Bau an der richtigen "
            "Stelle in falscher Groesse faellt hier nicht auf. Die Anzahl ist der "
            "Soll-Karte entnommen und nicht geraten; das ist der Grund fuer diese Wahl."
        )

    if strategie != HG_KEINE and polaritaet == POLARITAET_UNBEKANNT:
        raise TiefenschaetzerError(
            f"Strategie {strategie!r} verlangt eine deklarierte Polaritaet. Bei "
            f"{POLARITAET_UNBEKANNT!r} ist unbekannt, ob der Himmel bei den kleinsten "
            f"oder den groessten Werten liegt — eine Markierung schnitte dann mit halber "
            f"Wahrscheinlichkeit das Gebaeude heraus, und zwar lautlos."
        )

    ergebnis = list(werte)
    zusaetzlich = max(0, ziel - len(bereits))
    if zusaetzlich:
        endlich = [i for i, w in enumerate(werte) if math.isfinite(w)]
        # Stabil sortiert (Wert, Index), damit eine Bindung an der Schnittkante
        # reproduzierbar aufgelöst wird statt zufällig.
        endlich.sort(key=lambda i: (werte[i], i))
        zusaetzlich = min(zusaetzlich, len(endlich))
        if polaritaet == POLARITAET_DISPARITAET:
            # Kleinste Disparität = fernster Punkt = Himmel.
            gewaehlt = endlich[:zusaetzlich]
            rest = endlich[zusaetzlich:]
            kante = (gewaehlt[-1], rest[0]) if gewaehlt and rest else None
        else:
            # Grösste Tiefe = fernster Punkt = Himmel.
            schnitt = len(endlich) - zusaetzlich
            gewaehlt = endlich[schnitt:]
            rest = endlich[:schnitt]
            kante = (gewaehlt[0], rest[-1]) if gewaehlt and rest else None
        for i in gewaehlt:
            ergebnis[i] = math.inf
        if kante is not None and werte[kante[0]] == werte[kante[1]]:
            warnungen.append(
                "An der Schnittkante zwischen Himmel und Geometrie stehen gleiche Werte. "
                "Welche davon Hintergrund werden, entscheidet die Reihenfolge im Bild und "
                "nicht die Schaetzung — die Silhouettengrenze ist dort willkuerlich."
            )

    n_randflaechen = 0
    if strategie == HG_OHNE_RANDBERUEHRUNG:
        if breite is None or hoehe is None:
            raise TiefenschaetzerError(
                f"Strategie {HG_OHNE_RANDBERUEHRUNG!r} braucht 'breite' und 'hoehe'. "
                f"Ohne Bildmasse ist nicht entscheidbar, welcher Punkt am Rand liegt — "
                f"und genau die Randberuehrung ist das Merkmal, auf dem die Regel beruht."
            )
        if breite * hoehe != n:
            raise TiefenschaetzerError(
                f"{breite}x{hoehe} = {breite * hoehe} passt nicht zu {n} Werten."
            )
        ergebnis, n_randflaechen = _verwirf_randflaechen(ergebnis, breite, hoehe)
        unsicherheit.append(
            "Zusaetzlich verworfen: alle zusammenhaengenden Flaechen, die den Bildrand "
            "beruehren. Das trennt die vom Schaetzer in den leeren Grund gelegte "
            "Bodenebene vom freistehenden Baukoerper — gemessen an einem perfekten Bild "
            "hebt es den Anteil echter Bauwerkspunkte von 40.7 % auf 99.2 % "
            "(auf-20260818-12). DIE ANNAHME DAHINTER: Das Bauwerk beruehrt den Bildrand "
            "nicht. Bei einem angeschnittenen Bau — Innenraum, Detailaufnahme, zu nahe "
            "Kamera — verwirft die Regel das Bauwerk selbst und laesst NICHTS uebrig. "
            "Das ist sichtbar (n_hintergrund = alle) und nicht still."
        )

    n_hintergrund = sum(1 for w in ergebnis if not math.isfinite(w))
    if n_hintergrund == n:
        warnungen.append(
            "Die gesamte Ist-Karte gilt jetzt als Hintergrund. Es bleibt kein Punkt, an "
            "dem Geometrie gemessen werden koennte."
        )

    return {
        "tiefen": ergebnis,
        "strategie": strategie,
        "polaritaet": polaritaet,
        "n_punkte": n,
        "n_hintergrund": n_hintergrund,
        "anteil_hintergrund": n_hintergrund / n,
        "n_bereits_nicht_endlich": len(bereits),
        "n_randflaechen_verworfen": n_randflaechen,
        "unsicherheit": tuple(unsicherheit),
        "warnungen": tuple(warnungen),
    }


# --------------------------------------------------------------------------------------
# Die Naht zum Modell
# --------------------------------------------------------------------------------------

def standard_modell_wurzel(schaetzer_name: str) -> Path:
    """Wo die Gewichte auf der HomeStation liegen — eine Konvention, keine Prüfung.

    ``$AIIMAGING_MODELLE/<schaetzer-name>``, ersatzweise ``/ai/<schaetzer-name>`` — genau
    dieselbe Rechnung wie :func:`aiimaging.render.standard_modell_wurzel`, und darum von
    dort geholt statt hier nachgebaut.

    Der Grund, warum das hier steht: Bis zum 18.08.2026 rechnete diese Funktion fest mit
    ``/ai/modelle`` und las die Umgebungsvariable **nicht** — obwohl der Docstring
    „dieselbe Konvention" behauptete. Auf einer Maschine, deren Gewichte woanders liegen,
    lief damit der Render durch und die Geometrie-QA scheiterte erst danach mit einem
    ``OSError`` über eine Repo-Kennung: also ausgerechnet der Teil, der das Ergebnis
    bewerten soll, und erst dann, wenn der teure Teil schon gelaufen war (belegt auf der
    HomeStation, `auf-20260818-09`). Zwei Konventionen, die sich „dieselbe" nennen, sind
    schlimmer als zwei, die es offen nicht sind.

    Reine Pfadrechnung: Es wird nichts geladen und nichts geprüft.
    """
    from aiimaging import render          # nur für die Pfadrechnung, zieht keinen GPU-Stack
    return render.standard_modell_wurzel(hole(schaetzer_name).name)


def lade_modell(schaetzer_name: str, modell_wurzel=None):
    """Einen Tiefenschätzer laden — die einzige Stelle, die ``torch`` und ``transformers`` kennt.

    Args:
        schaetzer_name: Name aus der Registry.
        modell_wurzel: Verzeichnis der Gewichte. ``None`` heisst
            :func:`standard_modell_wurzel`.

    Returns:
        Ein **Aufrufbares** ``modell(parameter: dict) -> Sequence[float] | dict``. Der
        Vertrag der Naht ist absichtlich schmal: ein Wörterbuch hinein, eine Zahlenfolge
        heraus (oder ein Wörterbuch mit ``tiefen`` und optional ``breite``/``hoehe``).
        Alles, was Tensoren, Bildobjekte oder CUDA-Geräte kennt, bleibt hinter dieser
        Funktion — deshalb kommt :func:`schaetze_tiefe` ohne ``torch`` aus, und deshalb
        genügt im Test eine Funktion von drei Zeilen als Modell.

    Raises:
        TiefenschaetzerError: Schätzer unbekannt, unter Regel 1 ausgeschlossen, oder
            ``torch``/``transformers`` nicht vorhanden.

    Die Prüfreihenfolge ist bindend: **Lizenz zuerst.** Ein ausgeschlossenes Modell soll
    nicht daran scheitern, dass seine Gewichte fehlen — es soll an Regel 1 scheitern,
    auch dann, wenn jemand die Gewichte bereits heruntergeladen hat. Dieselbe Reihenfolge
    wie in ``render.lade_modell``.

    Warum der Import hier drin steht
    --------------------------------
    ``import torch`` auf Modulebene machte ``import aiimaging.tiefenschaetzer`` auf jedem
    Rechner ohne GPU-Stack unmöglich — und damit auch die Registry, die
    Hintergrundmarkierung und jeden Test darüber. Der Import gehört in die Funktion, die
    das Modell wirklich lädt. ``tests/test_tiefenschaetzer.py`` hält das fest, samt
    Gegenprobe, dass er in einer Funktion sehr wohl vorkommt.
    """
    eintrag = fordere_zulaessigen(schaetzer_name)
    wurzel = (Path(modell_wurzel) if modell_wurzel is not None
              else standard_modell_wurzel(eintrag.name))

    try:
        # NUR HIER. Siehe Docstring — und tests/test_tiefenschaetzer.py, das prüft, dass
        # diese beiden Namen nach dem Import des Moduls nicht in sys.modules liegen.
        import torch
        from transformers import pipeline
    except ImportError as fehler:
        raise TiefenschaetzerError(
            f"torch/transformers nicht verfuegbar ({fehler}). Die Tiefenschaetzung laeuft "
            f"nur dort, wo der GPU-Stack installiert ist — im Entwicklungscontainer gibt "
            f"es ihn nicht. Fuer Tests und Trockenlaeufe 'modell=' oder '_lader=' "
            f"uebergeben."
        ) from fehler

    pipe = pipeline(
        task="depth-estimation",
        model=str(wurzel),
        device=0 if torch.cuda.is_available() else -1,
    )
    return _pipeline_adapter(pipe, eintrag)


def _pipeline_adapter(pipe, eintrag):
    """Aus einer ``transformers``-Pipeline ein Modell im Sinne dieses Moduls machen.

    **Ungeprüft.** Diese Funktion ist die einzige Stelle des Moduls, die hier nie
    ausgeführt werden kann: Es gibt weder ``torch`` noch Gewichte. Sie ist bewusst so kurz
    wie möglich gehalten, damit die ungeprüfte Fläche klein bleibt — alles Entscheidbare
    (Lizenz, Registry, Hintergrundmarkierung, Längenprüfung, Ergebnisaufbau) liegt
    ausserhalb und ist geprüft. Dieselbe Bauform wie ``render._pipeline_adapter``.

    Die Pipeline liefert unter ``predicted_depth`` eine *relative inverse* Tiefe
    (Disparität) — nah = gross. Sie wird **nicht** umgerechnet und **nicht** normalisiert:
    Die Metrik ist rangbasiert, jede Umrechnung wäre wirkungslos oder irreführend.
    """
    def modell(parameter: dict):
        from PIL import Image                       # Pillow (MIT-CMU) — ebenfalls nur hier

        bild = Image.open(parameter["bild_png"]).convert("RGB")
        antwort = pipe(bild)
        karte = antwort["predicted_depth"]
        # squeeze(): die Pipeline liefert (1, H, W) oder (H, W).
        werte = karte.squeeze().tolist()
        hoehe = len(werte)
        breite = len(werte[0])
        flach = [float(x) for zeile in werte for x in zeile]
        return {"tiefen": flach, "breite": breite, "hoehe": hoehe}

    modell.schaetzer = eintrag.name          # zur Fehlersuche: welches Modell steckt drin
    return modell


# --------------------------------------------------------------------------------------
# Schätzen
# --------------------------------------------------------------------------------------

def _lies_antwort(antwort, breite_erwartet, hoehe_erwartet) -> tuple[list[float], int | None, int | None]:
    """Was die Naht zurückgab, in ``(tiefen, breite, hoehe)`` übersetzen — oder abbrechen.

    Der Vertrag lässt zwei Formen zu: eine reine Zahlenfolge, oder ein Wörterbuch mit
    ``tiefen`` und optional ``breite``/``hoehe``. Mehr Formen wären Bequemlichkeit ohne
    Nutzen; weniger machte den Test mit einer dreizeiligen Attrappe umständlich.
    """
    if isinstance(antwort, dict):
        if "tiefen" not in antwort:
            raise TiefenschaetzerError(
                f"Die Naht lieferte ein Woerterbuch ohne Schluessel 'tiefen': "
                f"{sorted(antwort)}. Der Vertrag ist: eine Zahlenfolge, oder ein "
                f"Woerterbuch mit 'tiefen'."
            )
        werte = _als_zahlen(antwort["tiefen"], "tiefen")
        breite = antwort.get("breite", breite_erwartet)
        hoehe = antwort.get("hoehe", hoehe_erwartet)
    else:
        werte = _als_zahlen(antwort, "tiefen")
        breite, hoehe = breite_erwartet, hoehe_erwartet

    if not werte:
        raise TiefenschaetzerError(
            "Die Naht lieferte eine leere Tiefenkarte. Eine leere Karte ist kein "
            "Messergebnis, sondern ein fehlgeschlagener Lauf."
        )
    for name, wert in (("breite", breite), ("hoehe", hoehe)):
        if wert is not None and (isinstance(wert, bool) or not isinstance(wert, int) or wert <= 0):
            raise TiefenschaetzerError(f"{name}: positive ganze Zahl oder None erwartet, war {wert!r}.")
    if breite is not None and hoehe is not None and breite * hoehe != len(werte):
        raise TiefenschaetzerError(
            f"Die Naht meldet {breite}x{hoehe} = {breite * hoehe} Punkte, lieferte aber "
            f"{len(werte)}. Ohne verlaessliche Bildgroesse ist die Indexgleichheit mit "
            f"der Soll-Karte nicht mehr zu behaupten (geometrie_qa, Vorbehalt 5)."
        )
    return werte, breite, hoehe


def _ist_ergebnis(status: str, *, bild_png, eintrag, tiefen=None, breite=None, hoehe=None,
                  markierung=None, dauer_s: float = 0.0, error=None,
                  warnungen=(), unsicherheit=()) -> dict:
    """Der Ergebnissatz der Schätzung — eine Form für alle Ausgänge.

    Auch ein Fehlschlag trägt Schätzer, Modell-Id und Lizenz. Sonst stünde im Protokoll
    „fehlgeschlagen" ohne die Angabe, womit es fehlschlug — dieselbe Überlegung wie in
    ``render._ergebnis``.
    """
    return {
        "status": status,
        "bild_png": str(bild_png),
        "schaetzer": eintrag.name,
        "modell_id": eintrag.modell_id,
        "lizenz": eintrag.lizenz,
        "polaritaet": eintrag.polaritaet,
        "tiefen": tiefen,
        "breite": breite,
        "hoehe": hoehe,
        "n_punkte": 0 if tiefen is None else len(tiefen),
        "hintergrund_strategie": None if markierung is None else markierung["strategie"],
        "n_hintergrund": None if markierung is None else markierung["n_hintergrund"],
        "anteil_hintergrund": None if markierung is None else markierung["anteil_hintergrund"],
        "methode": METHODE_IST,
        "dauer_s": round(float(dauer_s), 3),
        "error": error,
        "warnungen": tuple(warnungen),
        "unsicherheit": tuple(unsicherheit),
    }


def schaetze_tiefe(bild_png, *, schaetzer: str = VORGABE_TIEFENSCHAETZER, modell=None,
                   _lader=None, hintergrund_strategie: str = HG_KEINE,
                   hintergrund_anteil: float | None = None,
                   breite: int | None = None, hoehe: int | None = None) -> dict:
    """Aus einem erzeugten Bild eine Ist-Tiefenkarte schätzen — die eigentliche Naht.

    Args:
        bild_png: Pfad des erzeugten Bildes. Muss existieren; ein fehlendes Bild wird
            **vor** jedem Ladeversuch gemeldet, damit nicht erst Gewichte auf die GPU
            wandern, um dann an einem Dateinamen zu scheitern.
        schaetzer: Name aus :data:`TIEFENSCHAETZER`. Vorgabe
            :data:`VORGABE_TIEFENSCHAETZER`.
        modell: Ein fertiges Modell ``modell(parameter: dict) -> Sequence[float] | dict``.
            Übergeben heisst: nichts wird geladen. **Das ist die Test-Naht** — mit einer
            Attrappe läuft diese Funktion ohne GPU, ohne ``torch`` und ohne ein einziges
            Gewicht vollständig durch. Dieselbe Bauform wie ``modell=`` in
            ``render.rendere`` und ``_starte`` in ``seams.py``.
        _lader: Ersatz für :func:`lade_modell`, Signatur
            ``(schaetzer_name, modell_wurzel) -> modell``. Unterstrich, weil es eine Naht
            ist und keine Einstellung.
        hintergrund_strategie: :data:`HG_KEINE` (Vorgabe) oder :data:`HG_QUANTIL`.
            :data:`HG_WIE_SOLL` ist hier **nicht** möglich — die Strategie braucht eine
            Soll-Karte, und die kennt nur :func:`qa_gegen_soll`.
        hintergrund_anteil: nur bei :data:`HG_QUANTIL`, siehe :func:`markiere_hintergrund`.
        breite, hoehe: erwartete Bildgrösse. Meldet die Naht eine eigene, muss sie
            übereinstimmen; sonst ist die Indexgleichheit mit dem Soll dahin.

    Returns:
        ``{status, bild_png, schaetzer, modell_id, lizenz, polaritaet, tiefen, breite,
        hoehe, n_punkte, hintergrund_strategie, n_hintergrund, anteil_hintergrund,
        methode, dauer_s, error, warnungen, unsicherheit}``

        * ``status='ok'`` — ``tiefen`` trägt die geschätzte Karte, roh und **nicht** in
          Meter umgerechnet (siehe Modul-Docstring).
        * ``status='abgelehnt'`` — das Bild fehlt. Es wurde nichts geladen und nichts
          gerechnet.
        * ``status='fehler'`` — es wurde versucht, und es ging schief. ``error`` trägt
          die Meldung; ``tiefen`` bleibt ``None``.

        ``tiefen`` ist die einzige nicht-skalare Angabe. Für den Rückweg zur HomeStation
        (``auftrag.baue_ergebnis``: nur Zahlen, keine Bilddaten) ist nicht dieses
        Wörterbuch gedacht, sondern das von :func:`qa_gegen_soll` — es enthält die Karte
        bewusst nicht mehr.

    Raises:
        TiefenschaetzerError: Schätzer unbekannt oder unter Regel 1 ausgeschlossen, oder
            :data:`HG_WIE_SOLL` ohne Soll. Diese Fälle sind Aufrufefehler und keine
            Laufergebnisse — anders als in ``render.rendere``, wo eine Ablehnung
            protokolliert wird, gibt es hier keinen Parametersatz, dessen Protokoll etwas
            wert wäre. Die volle Begründung aus der Registry steht in der Meldung.
    """
    eintrag = fordere_zulaessigen(schaetzer)

    if hintergrund_strategie in (HG_WIE_SOLL, HG_OHNE_RANDBERUEHRUNG, HG_VORGABE):
        raise TiefenschaetzerError(
            f"Strategie {hintergrund_strategie!r} ist hier nicht moeglich: Sie entnimmt "
            f"die Anzahl der Geometriepunkte der SOLL-Karte, und die kennt nur "
            f"qa_gegen_soll(). Hier stehen {HG_KEINE!r} und {HG_QUANTIL!r} zur Wahl."
        )

    pfad = Path(bild_png)
    if not pfad.is_file():
        return _ist_ergebnis(
            STATUS_ABGELEHNT, bild_png=pfad, eintrag=eintrag,
            error=(f"Es gibt keine Datei {str(pfad)!r}. Ohne Bild gibt es nichts zu "
                   f"schaetzen — geprueft wird das vor dem Laden, nicht danach."),
        )

    parameter = {
        "bild_png": str(pfad),
        "schaetzer": eintrag.name,
        "modell_id": eintrag.modell_id,
        "polaritaet": eintrag.polaritaet,
    }

    beginn = time.perf_counter()
    try:
        if modell is None:
            lader = _lader or lade_modell
            modell = lader(eintrag.name, None)
        antwort = modell(parameter)
        werte, b, h = _lies_antwort(antwort, breite, hoehe)
    except Exception as fehler:                       # noqa: BLE001 — bewusst breit
        # Bewusst jede Ausnahme: Was ein fremdes Modell wirft, ist nicht vorhersagbar
        # (CUDA-OOM, kaputte Gewichte, ein Fehler im eigenen Adapter). Ein Stapelabbruch
        # mitten in einer Serie kostet die ganze Serie; ein 'status=fehler' mit Meldung
        # kostet ein Bild und bleibt protokolliert. Dieselbe Abwaegung wie in
        # ``render.rendere``.
        return _ist_ergebnis(
            STATUS_FEHLER, bild_png=pfad, eintrag=eintrag,
            dauer_s=time.perf_counter() - beginn,
            error=f"{type(fehler).__name__}: {fehler}",
        )
    dauer = time.perf_counter() - beginn

    markierung = markiere_hintergrund(
        werte, polaritaet=eintrag.polaritaet, strategie=hintergrund_strategie,
        anteil=hintergrund_anteil, breite=b, hoehe=h,
    )
    return _ist_ergebnis(
        STATUS_OK, bild_png=pfad, eintrag=eintrag, tiefen=markierung["tiefen"],
        breite=b, hoehe=h, markierung=markierung, dauer_s=dauer,
        warnungen=markierung["warnungen"], unsicherheit=markierung["unsicherheit"],
    )


# --------------------------------------------------------------------------------------
# Der Bogen zum Schluss: Ist schätzen und gegen das Soll messen
# --------------------------------------------------------------------------------------

#: Übersetzung der beiden Polaritäts-Schreibweisen dieses Projekts.
#:
#: :mod:`aiimaging.tiefenschaetzer` führt sie als **Zeichenkette** (``"disparitaet"``),
#: :mod:`aiimaging.geometrie_qa` als **Vorzeichen** (``−1``). Beide beschreiben dieselbe
#: Sache, aber **sie behaupten nicht dasselbe**, und darum steht die Übersetzung hier als
#: benannte Tabelle statt als beiläufiger Vergleich:
#:
#: * Die Zeichenkette gehört zum **Schätzer** und stammt aus seiner Beschreibung.
#: * Das Vorzeichen in ``geometrie_qa.GEMESSENE_POLARITAET`` gehört zum **Paar** aus
#:   Schätzer und *unserer* Soll-Konvention und ist an 24 Läufen gemessen
#:   (`auf-20260820-23`).
#:
#: Für ``depth-anything-v2-small`` stimmen beide überein. Dass sie das tun, ist ein
#: Befund und keine Selbstverständlichkeit — eine gedrehte Soll-Karte würde das Vorzeichen
#: kippen, ohne dass sich am Schätzer etwas ändert.
POLARITAETSZEICHEN = {
    POLARITAET_DISPARITAET: geometrie_qa.POLARITAET_DISPARITAET,
    POLARITAET_TIEFE: geometrie_qa.POLARITAET_TIEFE,
    POLARITAET_UNBEKANNT: None,
}


def gemessenes_zeichen(schaetzer_name: str) -> int | None:
    """Das **gemessene** Vorzeichen für dieses Schätzer/Soll-Paar — oder ``None``.

    **Warum das eine eigene Funktion ist und nicht dieselbe Auflösung wie im Maskenweg.**
    :func:`_maskenweg` fällt auf die **deklarierte** Polarität zurück
    (``POLARITAETSZEICHEN``), wenn nichts gemessen ist. Das ist dort richtig: Die
    Maskenmasse sind Diagnosewerte, und ein Wert aus einer Modellkarte ist besser als
    keiner.

    **Am Tor ist es das nicht.** ``geometrie_gate`` schneidet den Score bei einem
    Vorzeichenfehler auf **null** ab — aus einer falsch deklarierten Polarität würde damit
    ein durchgefallenes Bild, ohne dass irgendetwas am Bild falsch wäre. Eine Zeichenkette
    aus einer Modellkarte gilt für den Schätzer; das Vorzeichen, das hier zählt, gehört
    dem **Paar** aus Schätzer und unserer Soll-Konvention, und das ist eine Messung.

    Ist nichts gemessen, kommt ``None`` zurück, und das Tor rechnet weiter mit
    ``abs(spearman)`` — samt dem Vorbehalt, den ``geometrie_gate`` dann selbst meldet.
    **Das ist kein Versehen, sondern die mildere Regel für den ungemessenen Fall:** Lieber
    ein Score, der die Richtung nicht kennt, als ein Freispruch oder ein Urteil aus einer
    Modellkarte. Dieselbe Haltung wie ``MIN_POLARITAETSLAEUFE`` in ``geometrie_qa`` — wer
    die Polarität aus zu wenig Läufen bestimmt, bestimmt sie womöglich aus genau dem
    Fehler, den er später fangen will.
    """
    return geometrie_qa.GEMESSENE_POLARITAET.get(schaetzer_name)


def _maskenweg(soll: Sequence[float], roh: Sequence[float], maske, breite,
               schaetzer_name: str, polaritaet_wort: str) -> dict:
    """Die beiden Maskenmasse und ihr Paarurteil — oder lauter ehrliche ``None``.

    **Warum das hier steht und nicht beim Aufrufer.** Beide Masse brauchen die
    *geschätzte* Karte, und die entsteht in dieser Funktion. Sie herauszureichen hiesse,
    ein Bild voller Zahlen an jede Aufrufstelle mitzuschleppen, die es nicht braucht — die
    Maske hereinzureichen kostet dagegen nichts.

    **Und warum die ROHE Karte, nicht die hintergrundmarkierte.** Die Markierung setzt
    den Hintergrund auf eine Marke. Innerhalb der Maske wäre das gleichgültig — aber
    :func:`~aiimaging.geometrie_qa.kante_an_maskengrenze` liest ausdrücklich auch
    **ausserhalb**, und dort verdürbe die Marke den Median. Die Kante misst den Sprung
    zwischen Fassade und dem, was dahinter liegt; sie braucht das, was der Schätzer dort
    wirklich gesehen hat.

    Ohne Maske bleibt alles ``None``. Das heisst **nicht gemessen** und nicht *in
    Ordnung*: Wer den Maskenweg nicht gefahren ist, hat über Existenz und Richtigkeit des
    Bauwerks nichts erfahren — der Score über das ganze Bild beantwortet beides nicht
    (`auf-20260821-26`: ein leeres Grundstück erreicht dort 0.9530 und besteht das Tor).
    """
    leer = {"rho_maske": None, "kante": None, "kantenanteil": None,
            "himmel": None, "paarurteil": None}
    if maske is None or breite is None:
        return leer

    # Gemessen schlägt deklariert: Das Vorzeichen aus `GEMESSENE_POLARITAET` gilt für das
    # PAAR aus Schätzer und unserer Soll-Karte, die Zeichenkette nur für den Schätzer.
    zeichen = geometrie_qa.GEMESSENE_POLARITAET.get(schaetzer_name)
    if zeichen is None:
        zeichen = POLARITAETSZEICHEN.get(polaritaet_wort)

    rho = geometrie_qa.rho_ueber_maske(list(soll), list(roh), maske, polaritaet=zeichen)
    kante = geometrie_qa.kante_an_maskengrenze(list(roh), maske, breite=breite,
                                               polaritaet=zeichen)
    # Das zweite Bein des Paartests seit dem 22.08.: der ANTEIL der Grenze mit Kante.
    # Die Median-Kante bleibt daneben stehen, weil sie gemessen ist — aber sie kippt,
    # statt zu trennen, und taugt darum nicht als Tor (`auf-20260822-30`).
    anteil = geometrie_qa.anteil_grenze_mit_kante(list(roh), maske, breite=breite)
    # Zuständigkeit des zweiten Beins — aus dem SOLL, nicht aus der Schätzung, und darum
    # vor dem Urteil beantwortbar. Wo kein Himmel hinter dem Umriss steht, misst die
    # Tiefenkante nichts (`auf-vis-20260823-07`), und der Paartest schweigt.
    himmel = geometrie_qa.himmel_hinter_umriss(list(soll), maske, breite=breite)
    # HIER STAND BIS ZUM 24.08.2026 EIN DRITTES BEIN (R2, Rang statt Betrag). Es ist
    # wieder heraus, auf ausdrueckliche Bitte der HomeStation und mit ihrem Beleg:
    # An ERZEUGTEN Bildern sortiert R2 verkehrt. Sieben von zehn liegen ueber dem
    # perfekten Blender-Bild derselben Szene, sechs davon mit |rho| < 0.32. Der Grund
    # ist gemessen: Eine in Y verschobene Maske bekommt denselben Wert (0.8405 gegen
    # 0.8405) — R2 misst am Produktpfad nicht «steht da ein Bauwerk», sondern ob die
    # Maske im unteren Bilddrittel liegt (`auf-vis-20260824-09`).
    #
    # Mein Gegenargument von gestern war, der Anschluss sei streng additiv: Kein Bild
    # besteht durch R2, das ohne R2 durchgefallen waere. Das stimmt und genuegt nicht.
    # Eine ANGEZEIGTE Zahl, die bei schlechteren Bildern hoeher ausfaellt, fuehrt den
    # Menschen in die Irre, der das Urteil liest — und der gehoert zum Tor.
    #
    # Die Funktion bleibt in `geometrie_qa`, mit dem Befund im Docstring. Wer sie wieder
    # anschliessen will, liest ihn zuerst.
    return {"rho_maske": rho, "kante": kante, "kantenanteil": anteil, "himmel": himmel,
            "paarurteil": geometrie_qa.paarurteil(rho, kante, anteil_ergebnis=anteil,
                                                  himmel_ergebnis=himmel)}


def qa_gegen_soll(bild_png, soll_tiefen: Sequence[float], *,
                  schaetzer: str = VORGABE_TIEFENSCHAETZER, modell=None, _lader=None,
                  schwelle: float = geometrie_qa.SCHWELLE_GEOMETRIE,
                  hintergrund: float | None = None,
                  hintergrund_strategie: str = HG_VORGABE,
                  hintergrund_anteil: float | None = None,
                  breite: int | None = None, hoehe: int | None = None,
                  maske: Sequence[bool] | None = None) -> dict:
    """Die Funktion, die die Geometrie-Metrik endlich **anwendbar** macht.

    Sie schliesst den Bogen: Aus dem erzeugten Bild wird eine Ist-Tiefenkarte geschätzt,
    ihr Hintergrund wird markiert, und dann urteilt ``geometrie_qa.geometrie_gate`` über
    Soll und Ist. Bis hierher konnte die Metrik nur Soll gegen Soll messen — belegt, aber
    ohne Aussage über ein einziges erzeugtes Bild.

    Args:
        bild_png: das erzeugte Bild (Ausgabe von ``render.rendere``).
        soll_tiefen: die Soll-Tiefenkarte in Metern, zeilenweise von oben — so, wie
            ``bildlesen.tiefen_aus_report`` sie liefert. Hintergrund als ``inf`` oder als
            sehr grosser Wert.
        schaetzer: Name aus :data:`TIEFENSCHAETZER`.
        modell, _lader: die Nähte, siehe :func:`schaetze_tiefe`.
        schwelle: Bestehensgrenze, wird an ``geometrie_gate`` durchgereicht. Vorgabe
            ``geometrie_qa.SCHWELLE_GEOMETRIE`` (0.65) — empirisch an wenigen Fällen
            gesetzt und auf **dieser** Naht noch gar nicht kalibriert.
        hintergrund: Hintergrundmarke für die Metrik, siehe ``geometrie_qa.silhouette``.
            Betrifft im Wesentlichen die Soll-Karte; die Ist-Karte trägt nach der
            Markierung ``inf`` und ist damit von der Marke unabhängig.
        hintergrund_strategie: :data:`HG_WIE_SOLL` (Vorgabe), :data:`HG_QUANTIL` oder
            :data:`HG_KEINE`. Die Wahl und ihr Preis stehen im Modul-Docstring und in
            jedem Ergebnis unter ``unsicherheit``.
        hintergrund_anteil: nur bei :data:`HG_QUANTIL`.
        breite, hoehe: erwartete Bildgrösse, siehe :func:`schaetze_tiefe`.

    Returns:
        Ein Wörterbuch aus **nur Zahlen, Wahrheitswerten und Text** — keine Tiefenkarte,
        kein Bild. Damit passt es unverändert in ``auftrag.baue_ergebnis(messwerte=…)``
        und darf nach Regel 3 über das Repo reisen::

            {status, bestanden, score, spearman, geom_iou, n_gemeinsam, n_soll, n_ist,
             schwelle, methode, methode_ist, begruendung, warnungen, unsicherheit,
             schaetzer, modell_id, lizenz, polaritaet, hintergrund_strategie,
             n_hintergrund_ist, anteil_hintergrund_ist, geom_iou_obergrenze, n_punkte,
             breite, hoehe, bild_png, dauer_s, error}

        * ``status='ok'`` — es wurde gemessen. ``bestanden`` trägt das Urteil.
        * ``status='abgelehnt'`` — Bild fehlt, oder die Karten sind ungleich lang.
        * ``status='fehler'`` — die Schätzung oder die Metrik ging schief.

        ``bestanden`` ist bei jedem Status ausser ``ok`` **False**. Das ist dieselbe
        fail-closed-Haltung wie in ``geometrie_gate``: Was nicht gemessen wurde, ist nicht
        freigesprochen. Ein Freispruch aus Mangel an Messung wäre die teuerste Sorte
        Fehler, denn niemand sucht danach.

        ``geom_iou_obergrenze`` ist der **Anteil der Soll-Geometrie am Bild**. Bei
        :data:`HG_KEINE` ist er zugleich die obere Schranke für ``geom_iou`` — die Zahl,
        die erklärt, warum ein treues Bild dort trotzdem durchfällt.

        **Bei jeder anderen Strategie ist er KEINE Schranke, und der Name behauptet mehr,
        als die Zahl hält** (HomeStation, 24.08.2026: *«geom_iou_obergrenze ist keine
        Obergrenze — das gemessene geom_iou liegt bei drei Stufen darüber»*).

        Der Grund liegt in der Rechnung und nicht im Zufall: Die Schranke folgt daraus,
        dass die geschätzte Silhouette unter :data:`HG_KEINE` das **ganze Bild** ist —
        dann ist die Vereinigung so gross wie das Bild und die Überdeckung höchstens so
        gross wie der Soll-Anteil. Markiert eine andere Strategie den Hintergrund weg, ist
        die Vereinigung kleiner, und ``geom_iou`` darf darüber liegen. **Das ist richtig
        so und kein Fehler der Messung.**

        Der Name bleibt, weil ältere Berichte und Messprotokolle auf ihn zeigen; daneben
        steht seit dem 24.08.2026 ``geom_iou_obergrenze_gilt``. Ist es ``False``, ist die
        Zahl eine **Auskunft über die Szene** (wieviel Bild das Bauwerk füllt) und keine
        Schranke — und genau diese Auskunft ist die nützlichere, siehe
        :func:`aiimaging.geometrie_qa.torchance`.

    Raises:
        TiefenschaetzerError: Schätzer unbekannt oder unter Regel 1 ausgeschlossen, oder
            ``soll_tiefen`` ist keine brauchbare Zahlenfolge.

    Was hier NICHT belegt ist
    -------------------------
    Ohne echte Gewichte läuft dieser Bogen nur mit einer Attrappe. Geprüft ist damit die
    **Verdrahtung**: Reihenfolge, Formen, Längen, Lizenzentscheid, Hintergrundmarkierung,
    Weitergabe an die Metrik. **Nicht** geprüft ist, ob ein echter Schätzer auf einem
    Architekturrender eine brauchbare Staffelung liefert, welche Scores dabei entstehen
    und ob 0.65 hier trennt. Das gehört auf die HomeStation und in die Schwellenstudie
    (``docs/PLAN.md``, Phase 4).
    """
    eintrag = fordere_zulaessigen(schaetzer)
    soll = _als_zahlen(soll_tiefen, "soll_tiefen")
    if not soll:
        raise TiefenschaetzerError(
            "soll_tiefen ist leer. Ohne Soll gibt es nichts, wogegen gemessen werden "
            "koennte — und ein Urteil ohne Vergleich waere erfunden."
        )

    beginn = time.perf_counter()
    # Immer erst roh schätzen: HG_WIE_SOLL braucht die Soll-Silhouette, die es in
    # schaetze_tiefe nicht gibt. Markiert wird darum hier, in einem zweiten Schritt.
    ist_ergebnis = schaetze_tiefe(
        bild_png, schaetzer=eintrag.name, modell=modell, _lader=_lader,
        hintergrund_strategie=HG_KEINE, breite=breite, hoehe=hoehe,
    )

    sil_soll = geometrie_qa.silhouette(soll, hintergrund)
    n_soll_geometrie = sum(sil_soll)
    obergrenze = n_soll_geometrie / len(soll)

    grund = {
        "schaetzer": eintrag.name,
        "modell_id": eintrag.modell_id,
        "lizenz": eintrag.lizenz,
        "polaritaet": eintrag.polaritaet,
        "bild_png": ist_ergebnis["bild_png"],
        "breite": ist_ergebnis["breite"],
        "hoehe": ist_ergebnis["hoehe"],
        "methode_ist": METHODE_IST,
        "geom_iou_obergrenze": obergrenze,
        # Ob die Zahl daneben ueberhaupt eine Schranke IST. Nur unter HG_KEINE ist die
        # geschaetzte Silhouette das ganze Bild, und nur dann folgt die Schranke aus der
        # Rechnung. Sonst ist es der Anteil des Bauwerks am Bild — nuetzlich, aber etwas
        # anderes, und das gemessene geom_iou liegt dann zu Recht darueber (24.08.2026).
        "geom_iou_obergrenze_gilt": (hintergrund_strategie == HG_KEINE),
        "schwelle": float(schwelle),
    }

    if ist_ergebnis["status"] != STATUS_OK:
        return _qa_ohne_messung(
            ist_ergebnis["status"], grund, error=ist_ergebnis["error"],
            dauer_s=time.perf_counter() - beginn,
            warnungen=ist_ergebnis["warnungen"],
            n_punkte=ist_ergebnis["n_punkte"],
        )

    roh = ist_ergebnis["tiefen"]
    if len(roh) != len(soll):
        return _qa_ohne_messung(
            STATUS_ABGELEHNT, grund, dauer_s=time.perf_counter() - beginn,
            n_punkte=len(roh),
            error=(
                f"Soll- und Ist-Karte sind unterschiedlich lang ({len(soll)} vs. "
                f"{len(roh)}). Die Metrik setzt Indexgleichheit voraus — dieselbe "
                f"Aufloesung, dieselbe Kamera, dieselbe Punktreihenfolge (geometrie_qa, "
                f"Vorbehalt 5). Abschneiden waere eine stille Reparatur mit falschem "
                f"Ergebnis; skaliert werden muss das Bild vor der Schaetzung."
            ),
        )

    strategie, aufloesungs_warnungen = loese_strategie(
        hintergrund_strategie, breite=ist_ergebnis["breite"], hoehe=ist_ergebnis["hoehe"])
    try:
        markierung = markiere_hintergrund(
            roh, polaritaet=eintrag.polaritaet, strategie=strategie,
            anteil=hintergrund_anteil, n_geometrie=n_soll_geometrie,
            breite=ist_ergebnis["breite"], hoehe=ist_ergebnis["hoehe"],
        )
        # Die gemessene Polarität gehört an das Tor, und bis zum 26.08.2026 kam sie hier
        # nicht an: `geometrie_gate` lief ohne sie, das Vorzeichen benutzte allein der
        # Maskenweg. Folge war ein Dauervorbehalt in JEDEM Produktionslauf («KEINE
        # POLARITÄT ÜBERGEBEN») und eine Rechnung, die im geometrischen Fehler nicht
        # monoton ist — beides, obwohl das Vorzeichen seit dem 20.08.2026 gemessen war.
        #
        # Was der Wechsel kostet, ist gemessen und nicht geschätzt: Die gerichtete
        # Rechnung kann einen Score nur SENKEN (max(0, p*rho) <= abs(rho)), sie ist also
        # fail-closed. Und sie unterscheidet sich von der alten nur bei POSITIVEM rho. In
        # den 14 Läufen mit Vorzeichen aus `docs/GEOM_IOU_HALLUZINATION_2026-08-21.md`
        # haben zwei ein positives (+0.127 bei Score 0.1842, +0.337 bei 0.2301), beide
        # weit unter der Schwelle — kein bekanntes Urteil ändert sich.
        urteil = geometrie_qa.geometrie_gate(
            soll, markierung["tiefen"], schwelle=schwelle, hintergrund=hintergrund,
            polaritaet=gemessenes_zeichen(eintrag.name),
        )
    except (TiefenschaetzerError, geometrie_qa.QaError) as fehler:
        return _qa_ohne_messung(
            STATUS_FEHLER, grund, dauer_s=time.perf_counter() - beginn,
            n_punkte=len(roh), error=f"{type(fehler).__name__}: {fehler}",
        )

    warnungen = tuple(ist_ergebnis["warnungen"]) + tuple(aufloesungs_warnungen) \
        + tuple(markierung["warnungen"]) + tuple(urteil["warnungen"])

    # OHNE MASKE FEHLT DAS EINZIGE MASS, DAS DIE ABWESENHEIT FAENGT — und bis zum
    # 26.08.2026 sagte das an dieser Stelle niemand.
    #
    # `_maskenweg` gibt dann lauter `None` zurueck, und der Docstring dort haelt fest,
    # dass das "nicht gemessen" heisst und nicht "in Ordnung". Gesagt wurde es aber nur
    # dort: Der Abholer hat eine eigene Zeile dafuer (`befund_kurz`), die Kette hat keine
    # — und sie reicht gar keine Maske herein. Ein Urteil aus einem Kettenlauf sah damit
    # aus wie jedes andere.
    #
    # Die Zeile ist SELBSTLOESCHEND: Mit Maske steht sie nicht da. Eine Warnung, die
    # immer feuert, verdeckt die echten.
    if maske is None:
        warnungen = warnungen + (
            "OHNE MASKENWEG gemessen: rho_maske, Kante und Paarurteil bleiben ungemessen "
            "— und das sind die Masse, die die ABWESENHEIT eines Bauwerks fangen. Der "
            "Score ueber das ganze Bild fangt sie nicht: Ein leeres Grundstueck erreichte "
            "dort 0.9530 und bestand das Tor (auf-20260821-26). Ein bestandenes Urteil "
            "ohne Maskenweg sagt darum nichts darueber, ob ueberhaupt gebaut wurde.",
        )
    unsicherheit = tuple(markierung["unsicherheit"]) + (
        "Die Ist-Karte ist eine Schaetzung, keine Messung: Ein Fehler des Schaetzers ist "
        "von einer Halluzination des Bildmodells hier nicht unterscheidbar "
        "(geometrie_qa, Vorbehalt 6).",
    )

    # DER MASKENWEG IST EIN ZWEITES TOR, NICHT EINE ZUSATZMESSUNG (Owner-Entscheid
    # 26.08.2026). Lief er nicht, gibt es KEIN Urteil — `bestanden` ist dann `None`.
    #
    # `None` heisst hier wie ueberall in diesem Projekt *nicht beurteilbar* und nicht
    # *durchgefallen*: Der Score steht daneben und bleibt lesbar. Der Grund fuer den
    # Entscheid ist gemessen: Ohne Maskenweg fehlen rho_maske, Kante und Paarurteil, also
    # die einzigen Masse, die die ABWESENHEIT eines Bauwerks fangen — ein leeres
    # Grundstueck erreichte auf dem Score ueber das ganze Bild 0.9530 und bestand das Tor
    # (auf-20260821-26).
    #
    # WARUM EIN DURCHGEFALLENER SCORE TROTZDEM `False` BLEIBT. Zwei Tore stehen im UND,
    # und ein UND ueber drei Werten ist entschieden, sobald ein Teil `False` ist:
    # False UND unbekannt ist False, True UND unbekannt ist unbekannt. Ein Bild, dessen
    # Score die Schwelle reisst, ist durchgefallen — daran aendert eine fehlende zweite
    # Messung nichts, und es als "nicht beurteilbar" zu melden verloere eine Auskunft,
    # die wir haben.
    bestanden = bool(urteil["bestanden"])
    if maske is None and bestanden:
        bestanden = None

    return {
        "status": STATUS_OK,
        "bestanden": bestanden,
        "score": urteil["score"],
        "spearman": urteil["spearman"],
        "geom_iou": urteil["geom_iou"],
        # Derselbe Wert ohne den Anteil, den die Szene ohnehin schenkt (Owner-Entscheid
        # 28.08.2026). NICHT im Score — 0.65 behaelt seine Bedeutung. 0 heisst hier: so
        # gut wie ein konstantes Bild; negativ heisst: schlechter als das.
        "geom_iou_norm": urteil.get("geom_iou_norm"),
        "n_gemeinsam": urteil["n_gemeinsam"],
        "n_soll": urteil["n_soll"],
        "n_ist": urteil["n_ist"],
        "methode": urteil["methode"],
        # ACHTUNG, zwei verschiedene Dinge mit fast demselben Namen — und seit dem
        # 26.08.2026 haengt eine Zahl daran:
        #
        #   `polaritaet`         das DEKLARIERTE Wort des Schaetzereintrags
        #                        ("disparitaet"), aus der Modellkarte. Steht weiter unten
        #                        ueber **grund im Ergebnis und bleibt, weil aeltere
        #                        Berichte darauf zeigen.
        #   `polaritaet_zeichen` das VORZEICHEN, mit dem wirklich gerechnet wurde
        #                        (-1, +1 oder None). `None` heisst ungemessen, dann lief
        #                        `abs(spearman)`.
        #
        # Solange das Tor die Polaritaet gar nicht bekam, war der Unterschied folgenlos.
        # Jetzt entscheidet das Zeichen ueber den Score, und wer einen alten Wert deutet,
        # muss ihm ansehen, welche Rechnung dahinterstand. `methode` sagt dasselbe in
        # Worten; die Zahl steht daneben, weil sich eine Zeichenkette schlecht vergleichen
        # laesst.
        "polaritaet_zeichen": urteil["polaritaet"],
        "begruendung": urteil["begruendung"],
        "n_punkte": len(roh),
        "hintergrund_strategie": markierung["strategie"],
        "n_hintergrund_ist": markierung["n_hintergrund"],
        # Der Maskenweg. `None`, wenn keine Maske hereingereicht wurde — NICHT gemessen
        # und nicht in Ordnung. Warum die Maske hier hinein und die Schätzkarte nicht
        # heraus geht: Die Karte ist gross und wird nach diesem Aufruf nicht mehr
        # gebraucht; sie herauszureichen hiesse, sie an jeder Aufrufstelle mitzuschleppen.
        **_maskenweg(soll, roh, maske, ist_ergebnis["breite"], schaetzer,
                     eintrag.polaritaet),
        "anteil_hintergrund_ist": markierung["anteil_hintergrund"],
        "dauer_s": round(time.perf_counter() - beginn, 3),
        "error": None,
        "warnungen": warnungen,
        "unsicherheit": unsicherheit,
        **grund,
    }


def _qa_ohne_messung(status: str, grund: dict, *, error, dauer_s: float,
                     n_punkte: int = 0, warnungen=()) -> dict:
    """Ein Ergebnis ohne Messung — gleiche Felder, damit der Aufrufer nicht verzweigen muss.

    Alle Messfelder stehen auf ``None``, nicht auf 0. ``None`` heisst „kein Wert"; 0 hiesse
    „gemessen und schlecht". Diese Unterscheidung ist der Grund, warum ``geometrie_score``
    denselben Weg geht.
    """
    return {
        "status": status,
        "bestanden": False,
        "score": None,
        "spearman": None,
        "geom_iou": None,
        "geom_iou_norm": None,
        "n_gemeinsam": None,
        "n_soll": None,
        "n_ist": None,
        "methode": geometrie_qa.METHODE,
        # Kein Zeichen, weil nichts gerechnet wurde — `None` heisst hier wie ueberall
        # „kein Wert" und nicht „ungerichtet gerechnet". Das Feld steht trotzdem da: Der
        # Aufrufer soll nicht danach verzweigen muessen, ob eine Messung stattfand.
        "polaritaet_zeichen": None,
        "begruendung": (
            f"Nicht gemessen ({status}), damit nicht bestanden — was nicht geprueft "
            f"wurde, wird nicht durchgelassen. {error}"
        ),
        "n_punkte": n_punkte,
        "hintergrund_strategie": None,
        "n_hintergrund_ist": None,
        "anteil_hintergrund_ist": None,
        "dauer_s": round(float(dauer_s), 3),
        "error": error,
        "warnungen": tuple(warnungen),
        "unsicherheit": (),
        **grund,
    }


__all__ = [
    "HG_KEINE", "HG_QUANTIL", "HG_QUANTIL_VORGABE", "HG_STRATEGIEN", "HG_WIE_SOLL",
    "METHODE_IST", "POLARITAETEN", "POLARITAET_DISPARITAET", "POLARITAET_TIEFE",
    "POLARITAET_UNBEKANNT", "STATUSSE", "STATUS_ABGELEHNT", "STATUS_FEHLER", "STATUS_OK",
    "TIEFENSCHAETZER", "VORGABE_TIEFENSCHAETZER", "ZUGELASSENE_LIZENZEN",
    "Tiefenschaetzer", "TiefenschaetzerError",
    "fordere_zulaessigen", "hole", "lade_modell", "markiere_hintergrund",
    "pruefe_lizenz", "qa_gegen_soll", "schaetze_tiefe", "standard_modell_wurzel", "waehle",
]
