"""GEOMETRIE-QA — die Frage „folgt der Render der entworfenen Kubatur?“, messbar gemacht.

Warum dieses Modul existiert
----------------------------
Generative Bildmodelle erzeugen Gebäude, die plausibel *aussehen*. Plausibel ist nicht
dasselbe wie entworfen: Das Modell erfindet Geschosse, verschiebt Baukörper, füllt eine
leere Parzelle. Für Architekt:innen ist ein solches Bild nicht bloss wertlos, sondern
schädlich — es zeigt einen Entwurf, den es nicht gibt, und sieht dabei aus wie eine
Visualisierung des echten.

Der belegte Anlass stammt aus dem Vorläuferprojekt: Ein reines **Stil**-Gate meldete
``bestanden`` (0.42) auf eine **halluzinierte** Kubatur. Das Gate hatte recht — der Stil
stimmte. Es hatte nur nie nach der Geometrie gefragt. Genau diese Blindstelle schliesst
dieses Modul.

Das Verfahren
-------------
Zwei Tiefenkarten desselben Bildausschnitts, Punkt für Punkt indexgleich:

* **Soll** — von Blender aus der echten Geometrie gerendert, in Metern.
* **Ist**  — aus dem erzeugten Bild zurückgerechnet (monokulare Tiefenschätzung).

Daraus::

    score = sqrt(abs(spearman) * geom_iou)

**Warum Rangkorrelation und nicht der Tiefenfehler in Metern.** Die zurückgerechnete
Tiefe hat einen anderen Massstab und einen anderen Nullpunkt als die echten Meter; viele
Schätzer liefern überhaupt keine Meter, sondern eine affin unbestimmte Grösse. Ein
Absolutvergleich misst dann den Massstab des Schätzers, nicht die Treue des Bildes.
Vergleichbar ist allein die **Reihenfolge**: was vorne ist, muss vorne bleiben. Die
Rangkorrelation ist gegen jede streng monoton steigende Umrechnung unempfindlich —
``ist = 3 * soll + 7`` ändert an ihr nichts. Das ist keine Bequemlichkeit, sondern die
einzige Grösse, die über die Naht zwischen zwei Verfahren hinweg dasselbe bedeutet.

**Warum der Betrag.** Manche Verfahren liefern Disparität (invertierte Tiefe): nah = gross.
Dann ist die Reihenfolge exakt umgekehrt und die Korrelation −1, obwohl die Geometrie
perfekt stimmt. Gewertet wird darum ``abs(spearman)``. Der Preis dieser Entscheidung ist
benannt: Eine echte Vorne-Hinten-Vertauschung ist von einer Vorzeichenkonvention hier
nicht zu unterscheiden. Ein negatives Vorzeichen erscheint deshalb immer als Warnung.

**Warum zusätzlich die Silhouette.** Die Rangkorrelation allein ist erpressbar: Ein
erfundenes Vollgebäude in einer leeren Szene hat eine völlig eigene, in sich stimmige
Tiefenstaffelung — hohe Rangkorrelation auf dem wenigen, was sich überlappt. ``geom_iou``
fragt darum nicht, *wie tief* die Punkte liegen, sondern *welche Punkte überhaupt
Geometrie tragen* (Intersection over Union der Silhouetten). Steht das erfundene Gebäude
anderswo, geht dieser Anteil gegen null. Das ist der Teil, der die Halluzination fängt.

**Warum das geometrische Mittel.** ``sqrt(a * b)`` verlangt, dass **beide** Anteile gut
sind: Fällt einer gegen null, fällt der Score mit, egal wie gut der andere ist. Ein
arithmetisches Mittel liesse sich genau umgekehrt missbrauchen — perfekte Tiefenordnung
im überlappenden Rest kompensierte dort eine fast verfehlte Silhouette. Genau diese
Kompensation ist der Fehler, gegen den das Modul gebaut ist.

Vorbehalt zur Schwelle
----------------------
``SCHWELLE_GEOMETRIE = 0.65`` ist **empirisch an wenigen Fällen** gesetzt: treue Renders
lagen bei 0.81–0.93, eine halluzinierte Kubatur bei 0.11. Zwischen 0.11 und 0.81 liegt
eine breite, unbesetzte Lücke — die Schwelle darin ist plausibel, aber nicht kalibriert.
Eine systematische Schwellenstudie steht aus (``docs/PLAN.md``, Phase 4). Bis dahin gilt:
Die Zahl trennt die geprüften Fälle, sie ist kein Messnormal. Dasselbe gilt für
``MIN_GEMEINSAME_PUNKTE``.

Was dieses Modul bewusst *nicht* tut
------------------------------------
Es liest keine Dateien. EXR-Lesen, Tiefenschätzung und Bildverarbeitung liegen jenseits
einer Prozessgrenze und kommen später; hierher gehören sie nicht, weil sie schwere
Pakete nachziehen und die Metrik damit an eine Umgebung binden würden. Diese Funktionen
nehmen **Zahlenlisten** entgegen — nichts sonst.

Und was die Metrik *nicht kann* (bitte in jeder Auswertung mitlesen)
--------------------------------------------------------------------
1. **Sie misst Übereinstimmung, nicht Richtigkeit.** Ist schon die Soll-Tiefenkarte aus
   der falschen Geometrie oder der falschen Kamera gerendert, bestätigt die Metrik treu
   den falschen Entwurf.
2. **Massstabsblind — beabsichtigt, aber mit Preis.** Rangbasiert heisst: eine entlang
   der Sichtachse gestauchte oder gedehnte Kubatur, deren Tiefen*reihenfolge* stimmt,
   wird nicht bestraft. Proportionsfehler in Blickrichtung sind hier unsichtbar.
3. **Silhouette ist eine 2D-Deckung.** Was innerhalb der Silhouette geschieht — Fenster,
   Rücksprünge, Attika, Fassadengliederung — geht nur über die Tiefenordnung ein, nicht
   über die Umrisslogik. Ein richtiger Umriss mit erfundener Fassade fällt kaum auf.
4. **Keine räumliche Nachbarschaft.** Die Punkte werden als Menge behandelt; die Metrik
   kennt keine Kanten, keine Zusammenhangskomponenten, keine Glattheit.
5. **Indexgleichheit wird vorausgesetzt.** Beide Karten müssen dieselbe Auflösung, dieselbe
   Kamera und dieselbe Punktreihenfolge haben. Ein Versatz wird nicht erkannt, sondern
   nur bestraft — als niedrigerer Score ohne Hinweis auf die Ursache.
6. **Die Ist-Karte ist nur so gut wie ihr Schätzer.** Ein Fehler der Tiefenschätzung ist
   von einer Halluzination des Bildmodells hier nicht unterscheidbar. Die Metrik misst
   die Differenz, nicht ihre Ursache.
7. **Die Hintergrundkennung ist eine Vereinbarung, keine Messung.** Liefert der Schätzer
   für den Himmel irgendeine endliche Zahl statt einer Hintergrundmarke, trägt die
   Ist-Silhouette das ganze Bild und ``geom_iou`` wird strukturell zu klein. Die
   Hintergrundmarke gehört vor dem Aufruf gesetzt — an der Prozessgrenze, wo das Bild
   gelesen wird.
8. **Kein Urteil über Stil, Material oder Licht.** Das ist das zweite Gate; erst beide
   zusammen ergeben ein Urteil über ein Bild.

Abhängigkeiten: keine. Reine stdlib, kein numpy, kein scipy, kein ``bpy``, kein
``ifcopenshell``. Die Metrik ist reine Mathematik und muss überall laufen — auch dort,
wo weder GPU noch schwere Pakete existieren (Regel 4).
"""
from __future__ import annotations

import math
from collections.abc import Sequence

# Ab hier gilt ein Render als geometrietreu.
#
# Ursprünglich an wenigen Fällen gesetzt (treu 0.81–0.93, halluziniert 0.11) — siehe
# Vorbehalt im Modul-Docstring.
#
# STAND NACH DER ERSTEN SCHWELLENSTUDIE (18.08.2026, `docs/SCHWELLENSTUDIE_2026-08-18.md`):
# Diese Zahl ist **zu mild**, und das ist jetzt gemessen statt vermutet. Über acht
# Störungsarten × sieben Stärken lässt 0.65 **18 von 32** auswertbaren gestörten Fällen
# durch (Trefferquote 0.44); die beste Schwelle auf der Studienszene ist **0.90**, und sie ist
# über drei Auflösungen dieselbe. Bis 0.85 wird dabei **kein einziger treuer Fall**
# gesperrt — anheben kostete dort also nichts.
#
# Warum sie trotzdem steht: Die Studie kalibriert die **Metrik**, nicht die Kette. Im
# Betrieb liegt zwischen Soll und Ist ein monokularer Tiefenschätzer, dessen Fehler in
# keiner dieser Zahlen enthalten ist. Er senkt jeden Score, und wie weit, weiss niemand.
# Eine Schwelle von 0.90 könnte im Betrieb jeden Render sperren, auch den treuen — genau
# die Falle, in die der `geom_iou`-Deckel in Sitzung 06 schon einmal geführt hat.
#
# Sie zu erhöhen, bevor der Schätzer in der Messung steckt, hiesse eine unbegründete Zahl
# durch eine schwächer unbegründete zu ersetzen. **0.65 ist nicht verteidigt, sondern
# beibehalten** — der Unterschied gehört in die Arbeit und darum auch hierher.
#
# STAND NACH DER ZWEITEN HÄLFTE (18.08.2026, `auf-20260818-10`, `docs/HOMESTATION-
# 2026-08-18-SCHWELLEN.md`) — der Schätzer steckt jetzt in der Messung, und die
# befürchtete Falle ist eingetreten, nur an anderer Stelle als vermutet:
#
#   * **Der Schätzer ist es nicht.** An Blenders eigenem Beauty-Pass gemessen — gleiche
#     Szene, gleiche Kamera, kein Bildmodell dazwischen — liegt seine Tiefenordnung bei
#     |ρ| = 0.990. Nahezu fehlerfrei.
#   * **`geom_iou` deckelt bei 0.261**, und zwar bei genau diesem perfekten Bild. Damit
#     liegt der höchstmögliche Score der ganzen Kette bei **0.509**. 0.65 ist im Betrieb
#     also **unerreichbar** — das Gate sperrt derzeit ALLES, auch das Treue.
#   * **Die Nullprobe durch die ganze Kette liefert 0.033** (|ρ| = 0.005). Von der
#     Tiefenordnung bleibt nach dem Bildmodell nichts übrig; 22 von 24 GESTÖRTEN Zeilen
#     schneiden besser ab als die ungestörte Geometrie.
#
# **Die Zahl wird trotzdem nicht gesenkt.** Eine Schwelle an eine kaputte Kette
# anzupassen hiesse, das Gate an das anzupassen, wogegen es schützen soll. Solange bei
# ungestörter Geometrie 0.033 herauskommt, misst kein Wert etwas — die Schwelle ist
# derzeit weder das Problem noch die Lösung. Zwei Dinge müssen vorher stimmen: die
# Silhouettenauswahl (siehe DIAGNOSE_* unten) und ein Backbone, das die Geometrie
# überhaupt hält (`qwen-image-edit-2511` ist kein ControlNet, `auf-20260818-09`).
SCHWELLE_GEOMETRIE = 0.65

# Wie viele Punkte die gemeinsame Silhouette mindestens tragen muss, damit ein Score
# überhaupt ausgegeben wird.
#
# Statistisch ist die Grenze grosszügig: Eine perfekte Rangkorrelation entsteht rein
# zufällig mit Wahrscheinlichkeit 2/n! — bei n = 8 sind das bereits 5e-5. Die bindende
# Begründung ist praktisch: In einer 512×512-Tiefenkarte sind 32 Punkte 0.012 % des
# Bildes, also ein paar Pixel entlang einer Kante. Dort dominieren Resampling- und
# Kantenartefakte; ein Score daraus wäre Rauschen mit Dezimalpunkt.
#
# Bewusst absolut und nicht relativ zur Bildgrösse: Eine relative Grenze wüchse mit der
# Auflösung und machte damit auch SCHWELLE_GEOMETRIE auflösungsabhängig. Wie 0.65 ist
# auch diese Zahl bislang nur plausibel, nicht kalibriert (Phase 4).
MIN_GEMEINSAME_PUNKTE = 32

# Ab welchem Tiefenwert ein Bildpunkt als Hintergrund gilt, wenn der Aufrufer keine
# eigene Marke nennt.
#
# 1e6 m sind 1000 km. Der Torwächter lässt Bauwerke bis 1000 m Kantenlänge durch, und
# Kameraabstände liegen in derselben Grössenordnung; alles darüber ist keine Messung,
# sondern eine Marke. Renderer schreiben für „nichts getroffen“ typischerweise 1e10 oder
# den float-Maximalwert — beide liegen weit über dieser Grenze, ohne dass man den
# konkreten Wert kennen muss.
HINTERGRUND_SCHWELLE_M = 1.0e6

#: Kurzform des Rechenwegs, wandert in jedes Ergebnis. Wer später eine Zahl in der Arbeit
#: wiederfindet, soll ihr ansehen, wie sie entstanden ist — und an welcher Fassung.
METHODE = "sqrt(abs(spearman) * geom_iou), Rangkorrelation über die gemeinsame Silhouette, v1"

# Reine Diagnose-Schwellen. Sie gehen NICHT in den Score ein; sie benennen ein Muster:
# hohe Rangkorrelation bei kaum überlappenden Silhouetten.
#
# ACHTUNG, GEÄNDERTE DEUTUNG (18.08.2026): Bis hierher galt dieses Muster als Signatur
# einer **erfundenen Kubatur** — „innen stimmig, aber am falschen Ort". Diese Deutung war
# zu sicher. `auf-20260818-10` hat genau dieses Muster an einem Bild gemessen, das die
# Geometrie **exakt zeigt** (Blenders eigener Beauty-Pass): |ρ| = 0.990 bei
# geom_iou = 0.261. Da war nichts erfunden.
#
# Die Ursache lag in der **Silhouettenauswahl**: Ein monokularer Schätzer, auf Naturfotos
# trainiert, legt in eine flache gleichmässige Fläche eine Bodenebene hinein, die zur
# Bildecke hin auf die Kamera zuläuft. Ein Körper vor gleichmässigem Grund ist genau die
# Situation, in der dieser Vorgriff greift. Nachgemessen: nur **34 %** der ausgewählten
# Punkte lagen auf dem Bauwerk, der Rest bildete einen Keil in der oberen rechten Bildecke
# — im leeren Hintergrund —, und entsprechend fiel rund ein Drittel des echten Baukörpers
# aus der Auswahl heraus.
#
# Die Warnung nennt darum jetzt BEIDE Ursachen und sagt, woran sie zu unterscheiden sind.
# Eine Warnung, die eine von zwei möglichen Ursachen als die einzige ausgibt, schickt
# jemanden an die falsche Stelle — und das kostet mehr als gar keine Warnung.
DIAGNOSE_RHO_HOCH = 0.80
DIAGNOSE_IOU_NIEDRIG = 0.30


class QaError(ValueError):
    """Die Eingabe lässt keine belastbare Messung zu.

    Bewusst ein Fehler und kein stiller Ersatzwert: Ungleich lange Karten, Text statt
    Zahlen oder eine nicht definierte Korrelation sind Aufrufefehler. Sie hier auf 0.0
    abzurunden hiesse, ein Urteil zu fällen, für das keine Grundlage vorliegt — und
    genau das ist die Fehlerklasse, gegen die dieses Modul gebaut ist.

    Erbt von ``ValueError``, damit bestehendes ``except ValueError`` weiter greift.
    """


# --------------------------------------------------------------------------------------
# Eingaben lesen — streng, weil die Zahlen aus fremden Prozessen kommen
# --------------------------------------------------------------------------------------

def _als_zahlen(werte, name: str) -> list[float]:
    """Eingabefolge → Liste von ``float``. Nicht-endliche Werte bleiben **erhalten**.

    NaN und inf sind hier keine Fehler, sondern Daten: Ein Renderer markiert leeren
    Himmel gern mit ``inf``, eine gescheiterte Schätzung mit ``NaN``. Die Silhouette
    liest daraus „kein Geometriepunkt“. Erst die Rangkorrelation verlangt endliche
    Werte und prüft das selbst.

    Abgewiesen wird dagegen:

    * **Generatoren und andere Einweg-Iterables** — sie wären nach dem ersten Durchlauf
      leer, und ein Teil der Prüfungen liefe dann still auf einer leeren Folge.
    * **``str``/``bytes``** — eine Zeichenkette ist zwar eine Sequenz, aber nie eine
      Tiefenkarte.
    * **``bool``** — in Python ein ``int``, als Tiefenwert immer ein Irrtum. Der Fall
      fängt zugleich den häufigen Vertauscher: eine Silhouette dort, wo Tiefen erwartet
      werden.
    * **Zahlen in Textform** (``"27.3"``) — sie stillschweigend zu deuten wäre die Art
      Reparatur, gegen die dieses Projekt durchgehend antritt.
    """
    if isinstance(werte, (str, bytes, bytearray)) or not isinstance(werte, Sequence):
        raise QaError(
            f"{name}: Sequenz von Zahlen erwartet (Liste oder Tupel), war "
            f"{type(werte).__name__}. Generatoren sind nicht zulässig — sie wären nach "
            f"dem ersten Durchlauf leer."
        )
    zahlen: list[float] = []
    for i, wert in enumerate(werte):
        if isinstance(wert, bool) or not isinstance(wert, (int, float)):
            raise QaError(
                f"{name}[{i}]: Zahl erwartet, war {wert!r} ({type(wert).__name__}). "
                f"Es wird nichts umgedeutet."
            )
        zahlen.append(float(wert))
    return zahlen


def _als_wahrheitswerte(werte, name: str) -> list[bool]:
    """Eingabefolge → Liste von ``bool``. Zahlen werden **nicht** als 0/1 gedeutet.

    Die Strenge hat einen konkreten Zweck: ``iou(soll, ist)`` mit zwei *Tiefenkarten*
    statt zweier Silhouetten ist der wahrscheinlichste Fehlgriff an dieser Stelle. Würde
    hier auf Wahrheitswert geprüft, käme dabei eine Zahl heraus, die aussieht wie ein
    Messwert und keiner ist — der einzige Tiefenwert, der als ``False`` gälte, wäre die
    exakte 0.0.
    """
    if isinstance(werte, (str, bytes, bytearray)) or not isinstance(werte, Sequence):
        raise QaError(
            f"{name}: Sequenz von Wahrheitswerten erwartet, war {type(werte).__name__}."
        )
    for i, wert in enumerate(werte):
        if not isinstance(wert, bool):
            raise QaError(
                f"{name}[{i}]: Wahrheitswert erwartet, war {wert!r} "
                f"({type(wert).__name__}). Eine Tiefenkarte ist keine Silhouette — "
                f"``silhouette()`` erzeugt sie."
            )
    return list(werte)


def _hintergrund_grenze(hintergrund) -> float:
    """Prüft die Hintergrundmarke und gibt sie als ``float`` zurück."""
    if isinstance(hintergrund, bool) or not isinstance(hintergrund, (int, float)):
        raise QaError(
            f"hintergrund: Zahl oder None erwartet, war {hintergrund!r} "
            f"({type(hintergrund).__name__})."
        )
    grenze = float(hintergrund)
    if math.isnan(grenze):
        raise QaError("hintergrund ist NaN — damit ist kein Vergleich möglich.")
    if grenze <= 0.0:
        raise QaError(
            f"hintergrund muss positiv sein, war {grenze!r}. Eine Marke bei 0 oder "
            f"darunter erklärte die ganze Karte zum Hintergrund."
        )
    return grenze


# --------------------------------------------------------------------------------------
# Rangkorrelation
# --------------------------------------------------------------------------------------

def _mittlere_raenge(werte: list[float]) -> list[float]:
    """Ränge 1..n, bei gleichen Werten der **mittlere** Rang der Bindungsgruppe.

    Beispiel: ``[5, 5, 9]`` → ``[1.5, 1.5, 3.0]``.

    Bindungen sind in Tiefenkarten der Normalfall, nicht die Ausnahme: eine Wand parallel
    zur Bildebene liefert über hunderte Punkte denselben Wert. Sie einfach in
    Auftauchreihenfolge durchzunummerieren erzeugte eine Ordnung, die in den Daten nicht
    steht — und damit eine Korrelation, die es nicht gibt. Der mittlere Rang ist die
    einzige Vergabe, die keine der gleichwertigen Punkte bevorzugt.
    """
    n = len(werte)
    ordnung = sorted(range(n), key=lambda i: werte[i])
    raenge = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and werte[ordnung[j + 1]] == werte[ordnung[i]]:
            j += 1
        # Ränge sind 1-basiert; die Gruppe belegt die Plätze i+1 .. j+1.
        mittel = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            raenge[ordnung[k]] = mittel
        i = j + 1
    return raenge


def spearman(a: Sequence[float], b: Sequence[float]) -> float:
    """Rangkorrelation nach Spearman, in ``[-1, 1]``.

    Gerechnet wird als Pearson-Korrelation über die **mittleren Ränge**. Die verbreitete
    Kurzformel ``1 - 6*Σd²/(n*(n²-1))`` gilt nur ohne Bindungen und liefert bei
    Tiefenkarten — wo Bindungen der Normalfall sind — systematisch falsche Werte. Der
    Umweg über Pearson ist die bindungskorrekte Fassung, nicht eine schönere.

    Bedeutung des Vorzeichens: ``+1`` gleiche Reihenfolge, ``-1`` exakt umgekehrte
    Reihenfolge (invertierte Tiefe/Disparität), ``0`` kein monotoner Zusammenhang. Diese
    Funktion gibt das Vorzeichen **unverändert** zurück; die Betragsbildung ist eine
    Entscheidung des Scores und gehört dorthin, wo sie begründet ist.

    Raises:
        QaError: unterschiedlich lang, weniger als zwei Punkte, nicht-endliche Werte,
            oder eine der beiden Folgen ist konstant. Konstanz ist kein Sonderfall zum
            Wegdefinieren: Ohne Streuung gibt es keine Reihenfolge, die korrelieren
            könnte — jeder Rückgabewert wäre erfunden.
    """
    x = _als_zahlen(a, "a")
    y = _als_zahlen(b, "b")
    if len(x) != len(y):
        raise QaError(
            f"a und b sind unterschiedlich lang ({len(x)} vs. {len(y)}). Punktweise "
            f"Vergleiche setzen dieselbe Punktmenge in derselben Reihenfolge voraus."
        )
    if len(x) < 2:
        raise QaError(
            f"Rangkorrelation braucht mindestens 2 Punkte, bekam {len(x)}. Aus einem "
            f"Punkt lässt sich keine Reihenfolge lesen."
        )
    for name, werte in (("a", x), ("b", y)):
        for i, wert in enumerate(werte):
            if not math.isfinite(wert):
                raise QaError(
                    f"{name}[{i}] ist {wert!r}. NaN und inf haben in einer Rangfolge "
                    f"keinen Platz — Hintergrundpunkte gehören vorher aussortiert "
                    f"(siehe silhouette())."
                )

    rx = _mittlere_raenge(x)
    ry = _mittlere_raenge(y)
    n = len(rx)
    mx = sum(rx) / n
    my = sum(ry) / n
    sxy = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    sxx = sum((r - mx) ** 2 for r in rx)
    syy = sum((r - my) ** 2 for r in ry)
    if sxx == 0.0 or syy == 0.0:
        leer = "a" if sxx == 0.0 else "b"
        raise QaError(
            f"{leer} ist über alle Punkte konstant — die Rangkorrelation ist dann nicht "
            f"definiert (Division durch 0). In einer Tiefenkarte heisst das: eine Fläche "
            f"exakt parallel zur Bildebene, oder eine entartete Schätzung."
        )
    # Rundungsfehler können bei perfekter Korrelation minimal über 1 hinauslaufen.
    return max(-1.0, min(1.0, sxy / math.sqrt(sxx * syy)))


# --------------------------------------------------------------------------------------
# Silhouette und Überdeckung
# --------------------------------------------------------------------------------------

def silhouette(tiefen: Sequence[float], hintergrund: float | None = None) -> list[bool]:
    """Welche Bildpunkte tragen Geometrie? → ``True`` je Punkt mit Geometrie.

    Hintergrund ist, was **nicht endlich** ist (``NaN``, ``inf`` — der Strahl hat nichts
    getroffen) oder **sehr gross** (die Marke, mit der ein Renderer „nichts getroffen“
    schreibt, üblich sind 1e10 oder der float-Maximalwert).

    Args:
        tiefen: Tiefenwerte, ein Eintrag je Bildpunkt.
        hintergrund: Marke, ab der ein Wert als Hintergrund gilt. ``None`` nimmt
            ``HINTERGRUND_SCHWELLE_M`` (1e6 m). Verglichen wird ``wert < grenze``, also
            **einschliesslich** der Marke selbst — ein Renderer, der exakt 1e10 schreibt,
            soll auch dann Hintergrund liefern, wenn genau 1e10 übergeben wurde. Wer nur
            nicht-endliche Werte als Hintergrund werten will, übergibt ``math.inf``.

    Negative Werte gelten als Geometrie. Das ist Absicht: Manche Verfahren zählen Tiefe
    mit umgekehrtem Vorzeichen oder liefern eine Disparität mit Offset. Ein Nullpunkt
    lässt sich hier nicht annehmen, und eine falsche Annahme darüber schnitte stumm halbe
    Baukörper aus der Silhouette.
    """
    werte = _als_zahlen(tiefen, "tiefen")
    grenze = HINTERGRUND_SCHWELLE_M if hintergrund is None else _hintergrund_grenze(hintergrund)
    return [math.isfinite(wert) and wert < grenze for wert in werte]


def iou(a: Sequence[bool], b: Sequence[bool]) -> float:
    """Intersection over Union zweier Silhouetten, in ``[0, 1]``.

    ``|A ∩ B| / |A ∪ B|`` — der Anteil der Punkte, über den beide Karten einig sind,
    gemessen an allem, wo mindestens eine von beiden Geometrie sieht. Ein erfundenes
    Gebäude an anderer Stelle senkt den Wert doppelt: Es fehlt, wo es sein sollte, und es
    steht, wo nichts ist.

    Raises:
        QaError: unterschiedlich lang, keine Wahrheitswerte, oder **beide** Silhouetten
            leer. Der letzte Fall ist 0/0. Weder 0.0 („kein Bezug“) noch 1.0 („perfekt“)
            wäre eine Feststellung — beides erfände ein Urteil über zwei leere Bilder.
    """
    x = _als_wahrheitswerte(a, "a")
    y = _als_wahrheitswerte(b, "b")
    if len(x) != len(y):
        raise QaError(
            f"a und b sind unterschiedlich lang ({len(x)} vs. {len(y)}). Silhouetten "
            f"lassen sich nur punktweise vergleichen."
        )
    schnitt = sum(1 for i in range(len(x)) if x[i] and y[i])
    vereinigung = sum(1 for i in range(len(x)) if x[i] or y[i])
    if vereinigung == 0:
        raise QaError(
            "Beide Silhouetten sind leer — IoU ist 0/0 und damit nicht definiert. Zwei "
            "leere Bilder sind nicht 'perfekt gleich', sondern ungeprüft."
        )
    return schnitt / vereinigung


# --------------------------------------------------------------------------------------
# Der Score
# --------------------------------------------------------------------------------------

def geometrie_score(soll: Sequence[float], ist: Sequence[float],
                    hintergrund: float | None = None) -> dict:
    """Geometrie-Treue zweier indexgleicher Tiefenkarten.

    Args:
        soll: Tiefenkarte aus der echten Geometrie (Blender, Meter).
        ist: Tiefenkarte, aus dem erzeugten Bild zurückgerechnet. Massstab und Nullpunkt
            dürfen beliebig anders sein — genau dafür ist das Verfahren rangbasiert.
        hintergrund: Hintergrundmarke für **beide** Karten, siehe ``silhouette()``.

    Returns:
        ``{score, spearman, geom_iou, n_gemeinsam, n_soll, n_ist, methode, warnungen}``

        * ``score`` — ``sqrt(abs(spearman) * geom_iou)`` in ``[0, 1]``, oder ``None``,
          wenn nicht messbar. **``None`` ist kein schlechter Wert, sondern kein Wert.**
          Ein nicht messbarer Fall darf weder als 0 (Verurteilung ohne Grundlage) noch
          als 1 (Freispruch ohne Grundlage) durchgehen; warum, steht in ``warnungen``.
        * ``spearman`` — mit Vorzeichen, unverändert wie gemessen. In den Score geht der
          Betrag ein; das Vorzeichen bleibt sichtbar, weil es etwas bedeutet.
        * ``geom_iou`` — Silhouetten-Überdeckung.
        * ``n_gemeinsam`` — Punkte, die in **beiden** Karten Geometrie tragen. Nur über
          ihnen wird die Rangkorrelation gerechnet.
        * ``n_soll``/``n_ist`` — Punkte je Silhouette.
        * ``methode`` — Rechenweg als Text, für die Nachvollziehbarkeit in der Arbeit.
        * ``warnungen`` — Liste von Klartextsätzen. Leer heisst: nichts aufgefallen.

    Raises:
        QaError: unterschiedlich lange oder leere Eingaben. Ungleiche Längen sind ein
            Fehler und keine Gelegenheit zum Abschneiden — wer kürzt, verschiebt
            stillschweigend die Zuordnung aller Punkte danach.

    **Warum die Rangkorrelation nur über die gemeinsame Silhouette läuft.** Über alle
    Punkte gerechnet verglichen sich Tiefenwerte mit Hintergrundmarken. Das Ergebnis wäre
    grossenteils die Korrelation zweier Himmel — beliebig hoch, sobald beide Karten
    denselben leeren Bereich haben, und ohne jede Aussage über den Bau. Die Deckung der
    Silhouetten wird separat und ehrlich von ``geom_iou`` gemessen; sie zusätzlich in die
    Rangkorrelation zu mischen zählte sie doppelt und verwässerte beide Anteile.
    """
    s = _als_zahlen(soll, "soll")
    i = _als_zahlen(ist, "ist")
    if len(s) != len(i):
        raise QaError(
            f"soll und ist sind unterschiedlich lang ({len(s)} vs. {len(i)}). Beide "
            f"Karten müssen denselben Bildausschnitt in derselben Punktreihenfolge "
            f"zeigen. Abschneiden wäre eine stillschweigende Reparatur mit falschem "
            f"Ergebnis."
        )
    if not s:
        raise QaError("soll und ist sind leer — es gibt nichts zu vergleichen.")

    sil_soll = silhouette(s, hintergrund)
    sil_ist = silhouette(i, hintergrund)
    n_soll = sum(sil_soll)
    n_ist = sum(sil_ist)
    gemeinsam = [k for k in range(len(s)) if sil_soll[k] and sil_ist[k]]
    n_gemeinsam = len(gemeinsam)

    warnungen: list[str] = []
    if n_soll == 0:
        warnungen.append(
            "Soll-Tiefenkarte trägt keine Geometrie. Entweder ist die Hintergrundmarke "
            "falsch gesetzt, oder es wurde eine leere Szene gerendert — in beiden Fällen "
            "ist nicht das Bild das Problem."
        )
    if n_ist == 0:
        warnungen.append(
            "Ist-Tiefenkarte trägt keine Geometrie. Entweder hat die Tiefenschätzung "
            "nichts gefunden, oder ihre Hintergrundmarke passt nicht zur Soll-Karte."
        )

    try:
        geom_iou: float | None = iou(sil_soll, sil_ist)
    except QaError:
        # Beide Silhouetten leer. Kein Score, aber auch kein Absturz: Der Aufrufer soll
        # die Zähler sehen und daraus erkennen, dass hier nichts gemessen wurde.
        geom_iou = None
        warnungen.append(
            "Weder Soll- noch Ist-Karte trägt Geometrie — die Überdeckung ist 0/0 und "
            "nicht definiert. Es liegt kein Urteil vor."
        )

    rho: float | None = None
    if n_gemeinsam >= 2:
        try:
            rho = spearman([s[k] for k in gemeinsam], [i[k] for k in gemeinsam])
        except QaError as fehler:
            warnungen.append(
                f"Rangkorrelation nicht berechenbar: {fehler}"
            )

    score: float | None = None
    if n_gemeinsam == 0:
        warnungen.append(
            "Keine gemeinsame Silhouette: Es gibt keinen einzigen Bildpunkt, an dem "
            "beide Karten Geometrie sehen. Das ist der Extremfall einer erfundenen "
            "Kubatur — messbar ist er trotzdem nicht, denn ohne gemeinsame Punkte gibt "
            "es keine Tiefenordnung zu vergleichen. Score bleibt None; das ist eine "
            "fehlende Messung, kein Nullwert."
        )
    elif n_gemeinsam < MIN_GEMEINSAME_PUNKTE:
        warnungen.append(
            f"Gemeinsame Silhouette zu klein: {n_gemeinsam} Punkte, nötig sind "
            f"{MIN_GEMEINSAME_PUNKTE}. So wenige Punkte liegen an Kanten, wo Resampling "
            f"und Schätzrauschen dominieren; ein Score daraus wäre Rauschen mit "
            f"Dezimalpunkt. Score bleibt None — die Silhouetten decken sich aber ohnehin "
            f"kaum, was für sich schon ein Befund ist."
        )
    elif rho is not None and geom_iou is not None:
        # Betrag: invertierte Tiefe (Disparität) ist eine Konvention, kein Geometriefehler.
        score = math.sqrt(abs(rho) * geom_iou)

    if rho is not None and rho < 0.0:
        warnungen.append(
            f"Rangkorrelation ist negativ ({rho:+.3f}): Die Ist-Karte ordnet die Tiefe "
            f"genau umgekehrt. Üblichster Grund ist Disparität (nah = grosser Wert); "
            f"gewertet wird deshalb der Betrag. Falls die Ist-Karte metrische Tiefe sein "
            f"soll, ist das kein Konventions-, sondern ein Geometriebefund — vorne und "
            f"hinten sind vertauscht. Diese beiden Fälle kann die Metrik nicht trennen."
        )

    if score is not None and abs(rho) >= DIAGNOSE_RHO_HOCH and geom_iou <= DIAGNOSE_IOU_NIEDRIG:
        warnungen.append(
            f"Innen stimmig, aussen daneben: Die Tiefenordnung stimmt im Überlappungs"
            f"bereich gut (|spearman| {abs(rho):.3f}), die Silhouetten decken sich aber "
            f"kaum (geom_iou {geom_iou:.3f}). Dafür gibt es ZWEI Ursachen, und diese "
            f"Metrik kann sie nicht trennen:\n"
            f"  (a) Eine erfundene Kubatur — ein in sich stimmiges Gebäude an der "
            f"falschen Stelle sieht genau so aus.\n"
            f"  (b) Die Silhouettenauswahl der IST-Karte. Ein monokularer Schätzer legt "
            f"in eine leere, gleichmässige Fläche eine Bodenebene hinein, die zur "
            f"Bildecke hin auf die Kamera zuläuft; diese Scheingeometrie verdrängt "
            f"echten Baukörper aus der Auswahl. Am 18.08.2026 an einem Bild gemessen, "
            f"das die Geometrie EXAKT zeigte: |spearman| 0.990 bei geom_iou 0.261, nur "
            f"34 % der ausgewählten Punkte auf dem Bauwerk.\n"
            f"Unterscheiden lässt sich das nur am Bild: Liegt der überzählige Teil der "
            f"Ist-Silhouette als zusammenhängender Keil in einer Bildecke, ist es (b). "
            f"Ein Mittelwert liesse den guten Wert den schlechten ausgleichen — das "
            f"geometrische Mittel tut es nicht."
        )

    return {
        "score": score,
        "spearman": rho,
        "geom_iou": geom_iou,
        "n_gemeinsam": n_gemeinsam,
        "n_soll": n_soll,
        "n_ist": n_ist,
        "methode": METHODE,
        "warnungen": warnungen,
    }


def geometrie_gate(soll, ist, *, schwelle: float = SCHWELLE_GEOMETRIE, **kw) -> dict:
    """Das Urteil: Ist der Render geometrietreu genug?

    Args:
        soll: Soll-Tiefenkarte, siehe ``geometrie_score``.
        ist: Ist-Tiefenkarte, siehe ``geometrie_score``.
        schwelle: Bestehensgrenze in ``[0, 1]``. Vorgabe ``SCHWELLE_GEOMETRIE`` (0.65),
            empirisch an wenigen Fällen gesetzt — der Vorbehalt im Modul-Docstring gilt
            auch hier. Der Parameter existiert, damit die Schwellenstudie in Phase 4 die
            Grenze verschieben kann, ohne den Rechenweg anzufassen.
        **kw: wird an ``geometrie_score`` weitergereicht (``hintergrund``).

    Returns:
        Alle Felder von ``geometrie_score``, ergänzt um ``bestanden``, ``schwelle`` und
        ``begruendung``.

    **Ein nicht messbarer Fall gilt als nicht bestanden.** Ist ``score is None``, ist
    ``bestanden`` ``False`` — nicht, weil der Render als schlecht gilt, sondern weil
    nichts belegt ist. Der Torwächter hält es genauso: Was ungeprüft ist, wird nicht
    durchgelassen. Ein Freispruch aus Mangel an Messung wäre die teuerste Sorte Fehler,
    denn niemand sucht danach.

    Das ist **ein** Gate von zweien. Über Stil, Material und Licht sagt es nichts; erst
    beide Gates zusammen ergeben ein Urteil über ein Bild (``docs/PLAN.md``, Phase 3).
    """
    if isinstance(schwelle, bool) or not isinstance(schwelle, (int, float)):
        raise QaError(
            f"schwelle: Zahl erwartet, war {schwelle!r} ({type(schwelle).__name__})."
        )
    schwelle = float(schwelle)
    if not math.isfinite(schwelle) or not 0.0 <= schwelle <= 1.0:
        raise QaError(
            f"schwelle muss in [0, 1] liegen, war {schwelle!r}. Der Score kann diesen "
            f"Bereich nicht verlassen; eine Schwelle ausserhalb wäre immer oder nie "
            f"erfüllt."
        )

    ergebnis = geometrie_score(soll, ist, **kw)
    score = ergebnis["score"]
    bestanden = score is not None and score >= schwelle

    if score is None:
        grund = ergebnis["warnungen"][-1] if ergebnis["warnungen"] else "Grund unbekannt."
        begruendung = (
            f"Nicht messbar, damit nicht bestanden — ein Score, den es nicht gibt, ist "
            f"kein bestandener Score. {grund}"
        )
    else:
        vergleich = "≥" if bestanden else "<"
        begruendung = (
            f"Score {score:.3f} {vergleich} Schwelle {schwelle:.2f} "
            f"(|spearman| {abs(ergebnis['spearman']):.3f} über {ergebnis['n_gemeinsam']} "
            f"gemeinsame Punkte, geom_iou {ergebnis['geom_iou']:.3f})."
        )

    urteil = {"bestanden": bestanden, "schwelle": schwelle, "begruendung": begruendung}
    urteil.update(ergebnis)
    return urteil
