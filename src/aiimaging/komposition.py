"""KOMPOSITION — das fotografische Regelwissen als rechnende, prüfbare Bibliothek.

Warum dieses Modul existiert
----------------------------
``kameras.py`` rechnet, wo eine Kamera stehen muss, damit das Bauwerk im Bild ist. Es
rechnet das richtig — und es hält die Kamera dabei **falsch**. Dieses Modul liefert die
Gegenrechnung: dieselbe Geometrie, aber mit der einen Regel, die das Fach wirklich kennt.

Der Befund, um den herum dieses Modul gebaut ist
------------------------------------------------
``kameras.py`` legt das Blickziel über die Augenhöhe (``ZIEL_ANTEIL_HOEHE = 0.20``) und
kippt die Kamera damit systematisch nach oben. Bei einem Abstand von 1,2 × Gebäudehöhe
sind das ``atan(0.20 / 1.2)`` = **9,4623°** — und zwar **unabhängig von der Gebäudehöhe**,
weil sich das Gebäudemass in Zähler und Nenner wegkürzt. Der Kommentar dort nennt das
„der übliche Griff der Architekturfotografie".

**Das ist genau verkehrt herum.** Die Recherche (``docs/recherche/KOMPOSITION_AUSSEN.md``
1.1) findet dazu die einzige institutionell verbindliche Regel des ganzen Fachs:

    „positioning the camera's focal plane perpendicular to the ground, **regardless of the
    photographer's eye level**" — en.wikipedia.org/wiki/Architectural_photography

und HABS/NPS schreibt die Perspektivkorrektur **bei der Aufnahme** zwingend vor („must be
used", „perspective corrected in the field at the time of capture"). Der übliche Griff ist
also: Kamera waagrecht halten und **shiften**, nicht kippen. Die Konvention bindet die
*Neigung* auf 0°; über die *Höhe* sagt sie nichts.

Dieses Modul korrigiert ``kameras.py`` nicht — es macht den Unterschied messbar. Die
Umstellung ist ein eigener Schritt.

Was die Nachrechnung des Auftrags bestätigt hat und was nicht
--------------------------------------------------------------
* **Bestätigt:** die 9,4623° und ihre Unabhängigkeit von der Gebäudehöhe. Auf zehn
  Nachkommastellen, für 6 / 8 / 15 / 40 m. :func:`neigung_grad` hält das fest.
* **Nicht bestätigt: die Spanne „12 bis 22 %" Konvergenz.** Unter der einzigen Definition,
  die ich sauber aufschreiben konnte — Verhältnis der Bildbreiten an Gebäudeoberkante und
  Gebäudefuss, siehe :func:`konvergenz` — ergibt derselbe Aufbau **12,6 % bei 6 m und
  12,3 % bei 40 m**. Die Konvergenz ist damit fast **konstant**, nicht wachsend, und der
  Grund ist derselbe wie bei der Neigung: Wenn der Abstand mit der Höhe mitwächst, bleibt
  der Winkel, unter dem das Bauwerk erscheint, gleich. Nur die Aufteilung dieses Winkels
  ober- und unterhalb der optischen Achse verschiebt sich, und das ist ein Effekt zweiter
  Ordnung. **Eine Konvergenzzahl ohne Angabe ihrer Definition und ihres Bezugsabstands ist
  keine Zahl.** Welche Definition zu 21,8 % bei 40 m führt, habe ich nicht rekonstruieren
  können; sie steht hier deshalb nicht.

Die Dreiteilung ist die Hauptsache dieses Moduls
-------------------------------------------------
Jede Zahl hier trägt, woher sie kommt. Drei Stufen, und sie werden nicht vermischt:

``belegt``
    Norm (HABS/NPS), Fachnorm (DIN 33402-2), begutachtete Studie (Amirshahi et al. 2014),
    Herstellerangabe (Shift-Beträge) oder nachrechenbare Geometrie. Registriert in
    :data:`BELEGT`, jeder Eintrag mit ``quelle`` und ``art``.

``gesetzt``
    Entscheid dieses Projekts. Kein Fund. Registriert in :data:`SETZUNGEN`, jeder Eintrag
    mit ``gesetzt_von`` und ``gesetzt_am``. **Eine Setzung als Fachwissen auszugeben wäre
    die Art Fehler, gegen die dieses Projekt seit Phase 0 antritt.**

``ungemessen``
    Die Recherche hat ausdrücklich nichts gefunden, und niemand hat entschieden.
    Registriert in :data:`UNGEMESSEN`, ``wert`` ist dort immer ``None``. Wo ein Ratgeber
    trotzdem eine Zahl nennt, steht sie unter ``behauptet`` — als Zitat, nicht als Wert.

Ratgeberliteratur begründet in diesem Modul **keinen** Wert. Sie ist zahlenmässig in der
Überzahl und schreibt voneinander ab; das ist kein Beleg. Die **Drittelregel** ist als
Beschreibung der Praxis widerlegt (Amirshahi et al., *Art & Perception* 2, 2014: ρ = 0,17
über grosse Bildkorpora, „only a minor, if any, role"). Sie kommt hier nur so vor.

Wo ich der Recherche widersprechen muss
----------------------------------------
**„Die Praxis kennt keinen Weg, über 50 % Bodenanteil zu kommen, ohne die Kamera zu
kippen."** Das ist als Aussage über die *Praxis* richtig und als Aussage über die
*Geometrie* falsch. Shift geht in beide Richtungen — die belegte Angabe lautet ±11 mm, in
jede Richtung. Ein Shift **nach unten** vergrössert den Bodenanteil über 50 %, bei
lotrechter Sensorebene und damit ohne jede Konvergenz. Die 59,8 %, an denen die
Geometrie-QA am 20./21.08. hing, verlangen rechnerisch −2,35 mm Shift am Querformat —
ein Zwölftel des verfügbaren Wegs. :func:`bodenanteil_erreichbar` rechnet das aus.

Was daran bleibt: **Kein einziger fotografischer Text beschreibt diesen Griff.** Shift
wird ausschliesslich nach oben beschrieben, um den Bau ins Bild zu holen und den Boden
loszuwerden. Ein Bild mit 59,8 % Boden ist also nicht geometrisch unmöglich, sondern
fotografisch unbeschrieben — und wenn dieser Boden leer ist, wird er in jeder gefundenen
Quelle als Fehler benannt. Das ist der Brückenschlag zwischen der Fotografie und unserer
Messreihe, und er ist schmaler, als er zuerst aussah.

Was dieses Modul bewusst *nicht* tut
------------------------------------
Es setzt keine Kamera, es fasst ``kameras.py`` nicht an, und es entscheidet nichts, was
die Recherche offen lässt. Es rechnet und sagt dazu, mit welcher Belegstufe.

Abhängigkeiten: reine stdlib, kein ``bpy`` (Regel 2), ohne Oberfläche aufrufbar (Regel 4).
Die Richtungstabelle kommt aus :mod:`aiimaging.kameras` — es gibt genau eine, und dieses
Modul bildet den HABS-Ansichtenkatalog auf sie ab, statt eine zweite zu erfinden.
"""
from __future__ import annotations

import math

from .kameras import BIAS_GRAD, RICHTUNGEN, RICHTUNGSFOLGE, richtungen


class KompositionError(ValueError):
    """Aus dieser Eingabe lässt sich keine Komposition rechnen — und ein Ersatzwert wäre
    schlimmer.

    Erbt von ``ValueError``, dieselbe Wahl wie ``geometrie_qa.QaError`` und
    ``maske.MaskeError``: Bestehendes ``except ValueError`` greift weiter, und die
    getrennte Klasse sagt trotzdem, *welche* Naht gerissen ist.

    Bewusst ein Fehler und kein stiller Ersatzwert. Der Anlass steht in
    :func:`mindestabstand`: Bei ``shift ≥ halbe Sensorhöhe`` ist der Mindestabstand nicht
    definiert. Eine Division, die dort still ``inf`` liefert, sähe aus wie „sehr weit weg"
    und wäre in Wahrheit „diese Aufnahme gibt es nicht".
    """


#: Die drei Belegstufen dieses Moduls, in der Reihenfolge ihrer Belastbarkeit.
BELEGSTUFEN = ("belegt", "gesetzt", "ungemessen")

#: Die zulässigen Herkunftsarten eines **belegten** Werts.
#:
#: ``ratgeber`` steht hier absichtlich **nicht** drin. Ein Ratgeberwert ist in diesem
#: Modul kein belegter Wert; er gehört als Zitat unter ``behauptet`` in :data:`UNGEMESSEN`.
BELEG_ARTEN = ("norm", "studie", "geometrie", "hersteller", "messung")


# ======================================================================================
# A · BELEGTE ZAHLEN
#
# Norm, begutachtete Studie, Herstellerangabe, nachrechenbare Geometrie, eigene Messreihe.
# Jede dieser Konstanten hat unten einen Eintrag in BELEGT mit Quelle und Art.
# ======================================================================================

#: Kamera-Neigung (pitch) in Grad. **Exakt 0** — die einzige institutionell verbindliche
#: Regel des Fachs. HABS/NPS schreibt die Perspektivkorrektur bei der Aufnahme vor.
#: Der Preis: Der Bau kommt nur noch über Abstand und Shift ins Bild, nicht über Kippen.
NEIGUNG_WAAGRECHT_GRAD = 0.0

#: Kamera-Rollwinkel in Grad. Exakt 0, damit die Vertikalen parallel zum Bildrand stehen.
ROLLWINKEL_WAAGRECHT_GRAD = 0.0

#: Höchster Shift-Betrag in Millimetern, Canon TS-E / Nikon PC am Kleinbild.
#:
#: **In jede Richtung**, nicht nur nach oben — das ist die Angabe, an der die Aussage
#: „über 50 % Boden geht nur mit Kippen" scheitert (siehe Modulkopf).
SHIFT_HOECHSTWERT_MM = 11.0

#: Neuere Perspective-Control-Objektive erreichen 12 mm. Getrennt geführt, weil die
#: Recherche-Tabellen mit 12 rechnen und die Gerätemehrheit 11 kann.
SHIFT_HOECHSTWERT_NEUERE_MM = 12.0

#: Sensorhöhe Kleinbild in Aufnahmelage **quer**, in Millimetern.
SENSOR_HOEHE_QUER_MM = 24.0

#: Sensorhöhe Kleinbild in Aufnahmelage **hoch**, in Millimetern. Die 36 mm sind hier die
#: Höhe, nicht die Breite — im Hochformat steht der Sensor auf der langen Kante.
SENSOR_HOEHE_HOCH_MM = 36.0

#: Arbeitsbrennweite aussen, Kleinbild, in Millimetern.
#:
#: Zwei unabhängige Wege, ein Ergebnis: Der HABS-Objektivsatz von 1933 (90 mm auf 4×5)
#: entspricht 25,3 mm Kleinbild; die heutige Ratgeber- und Herstellerliteratur nennt
#: übereinstimmend 24 mm. Das ist die belastbarste Brennweitenaussage der Recherche.
#:
#: **``kameras.BRENNWEITE_MM`` steht auf 35 mm** — eine Setzung des Owners vom
#: 23.08.2026, ausdrücklich als eigene Vorliebe benannt. Die Abweichung von der Recherche
#: ist damit grösser geworden, und sie bleibt hier stehen, statt geglättet zu werden:
#: Dieses Modul führt, was das Fach sagt, nicht was das Projekt entscheidet. Genau dafür
#: gibt es die Dreiteilung ``belegt`` / ``gesetzt`` / ``ungemessen``. Ein Modul, das seine
#: Belege an die Vorgaben anpasst, ist kein Beleg mehr.
ARBEITSBRENNWEITE_AUSSEN_MM = 24.0

#: Arbeitsbereich innen, Kleinbild, in Millimetern: ``(untere, obere)``.
BRENNWEITE_INNEN_ARBEIT_MM = (24.0, 35.0)

#: Harte Untergrenze innen, in Millimetern. Airbnb schreibt seinen Fotografen „never
#: capture wider than 16mm" vor — die einzige gefundene **verbindliche** Brennweitengrenze.
#: Sie ist eine Geschäftsentscheidung, keine optische Erkenntnis, aber sie ist verbindlich.
BRENNWEITE_INNEN_UNTERGRENZE_MM = 16.0

#: Umrechnungsfaktor Grossformat 4×5 → Kleinbild: Verhältnis der Bilddiagonalen
#: (43,27 mm / 153,7 mm). Damit wird der HABS-Objektivsatz vergleichbar.
GROSSFORMAT_FAKTOR_4X5 = 0.2815

#: Augenhöhe Erwachsener im Stehen, ``(5. Perzentil Frauen, 95. Perzentil Männer)``,
#: in Metern, nach DIN 33402-2 über die Datensammlung der BAuA.
#:
#: **Das ist eine Spanne von 30 cm, keine Zahl.** Wer 1,70 gegen 1,60 verteidigt,
#: verteidigt einen Geschmack.
AUGENHOEHE_SPANNE_M = (1.43, 1.735)

#: 95. Perzentil der Männer, in Metern. Die projektgesetzten 1,70 m liegen **hier**,
#: nicht in der Mitte der Spanne. Das gehört zur Setzung dazu.
AUGENHOEHE_MAENNER_P95_M = 1.735

#: Anteil der Bildhöhe unterhalb des Horizonts bei waagrechter Kamera **ohne** Shift.
#: Geometrisch zwingend, für jede Brennweite, jeden Abstand und jedes Format.
BODENANTEIL_OHNE_SHIFT = 0.5

#: Spearman-Rangkorrelation zwischen ästhetischer Bewertung und Drittelregel-Treue,
#: Amirshahi et al., *Art & Perception* 2 (2014) 163–182. ρ = 0,17 — „only a minor, if
#: any, role in large sets of high-quality photographs and paintings".
#:
#: Diese Zahl steht hier, damit niemand die Drittelregel als Praxisbeschreibung benutzt.
DRITTELREGEL_KORRELATION = 0.17

#: Der in diesem Repo gemessene Bodenanteil der Szene, an der die Geometrie-QA am
#: 20./21.08.2026 versagte. Eigene Messreihe, kein fremder Wert.
BODENANTEIL_MESSREIHE_2026_08_20 = 0.598

#: Winkel der Über-Eck-Ansicht gegen die Fassadennormale, in Grad. Mehrfach und
#: konsistent genannt — aber ausschliesslich in Ratgeber- und Visualisierungsquellen.
#: Steht darum **nicht** in :data:`BELEGT`, sondern in :data:`UNGEMESSEN`.
UEBER_ECK_WINKEL_BEHAUPTET_GRAD = 45.0

BELEGT = {
    "NEIGUNG_WAAGRECHT_GRAD": {
        "wert": NEIGUNG_WAAGRECHT_GRAD,
        "art": "norm",
        "quelle": "HABS/HAER/HALS Photography Guidelines (NPS): Perspektivkorrektur "
                  "bei der Aufnahme zwingend; Wikipedia: focal plane perpendicular to "
                  "the ground, regardless of the photographer's eye level",
        "bemerkung": "Die einzige verbindliche institutionelle Vorgabe der Recherche.",
    },
    "ROLLWINKEL_WAAGRECHT_GRAD": {
        "wert": ROLLWINKEL_WAAGRECHT_GRAD,
        "art": "geometrie",
        "quelle": "Vertikalen bleiben nur parallel zum Bildrand, wenn der Sensor nicht "
                  "verdreht ist",
        "bemerkung": "Folgt aus derselben Regel wie die Neigung.",
    },
    "SHIFT_HOECHSTWERT_MM": {
        "wert": SHIFT_HOECHSTWERT_MM,
        "art": "hersteller",
        "quelle": "Wikipedia, Perspective control lens; Cambridge in Colour, "
                  "Tilt-Shift Lenses — Canon/Nikon PC, 11 bzw. 11,5 mm in jede Richtung",
        "bemerkung": "In JEDE Richtung. Der Wert ist kein Naturgesetz, sondern der "
                     "Verstellweg heutiger Kleinbild-Shiftobjektive.",
    },
    "SHIFT_HOECHSTWERT_NEUERE_MM": {
        "wert": SHIFT_HOECHSTWERT_NEUERE_MM,
        "art": "hersteller",
        "quelle": "Wikipedia, Perspective control lens — neuere Modelle 12 mm",
        "bemerkung": "Die Recherche-Tabellen in KOMPOSITION_AUSSEN.md 4.3/4.4 rechnen "
                     "mit diesem Wert.",
    },
    "SENSOR_HOEHE_QUER_MM": {
        "wert": SENSOR_HOEHE_QUER_MM,
        "art": "norm",
        "quelle": "Kleinbild 24 × 36 mm (Barnack/Leica), Aufnahmelage quer",
        "bemerkung": "Die Bezugsgrösse, auf die sich jede Brennweitenangabe der "
                     "Architekturfotografie stillschweigend bezieht.",
    },
    "SENSOR_HOEHE_HOCH_MM": {
        "wert": SENSOR_HOEHE_HOCH_MM,
        "art": "norm",
        "quelle": "Kleinbild 24 × 36 mm, Aufnahmelage hoch",
        "bemerkung": "",
    },
    "ARBEITSBRENNWEITE_AUSSEN_MM": {
        "wert": ARBEITSBRENNWEITE_AUSSEN_MM,
        "art": "norm",
        "quelle": "HABS-Objektivsatz 65/90/150/210 mm auf 4×5 → 18,3/25,3/42,2/59,1 mm "
                  "Kleinbild; unabhängig davon 24 mm in der heutigen Ratgeber- und "
                  "Herstellerliteratur (Chaos/Enscape: 24 mm Tilt-Shift, 67° FOV)",
        "bemerkung": "Bundesstandard von 1933 und heutige Praxis treffen sich.",
    },
    "BRENNWEITE_INNEN_ARBEIT_MM": {
        "wert": BRENNWEITE_INNEN_ARBEIT_MM,
        "art": "norm",
        "quelle": "mehrere unabhängige Innenraumquellen nennen 24–35 mm; 35 mm gilt als "
                  "Vorgabewert der professionellen Innenraum-Visualisierung",
        "bemerkung": "",
    },
    "BRENNWEITE_INNEN_UNTERGRENZE_MM": {
        "wert": BRENNWEITE_INNEN_UNTERGRENZE_MM,
        "art": "norm",
        "quelle": "Airbnb, Photo Composition Tips: „Never capture wider than 16mm“",
        "bemerkung": "Verbindliche Plattformvorgabe — eine Geschäftsentscheidung, keine "
                     "optische Erkenntnis, aber verbindlich für ihre Fotografen.",
    },
    "GROSSFORMAT_FAKTOR_4X5": {
        "wert": GROSSFORMAT_FAKTOR_4X5,
        "art": "geometrie",
        "quelle": "Verhältnis der Bilddiagonalen 43,27 mm (Kleinbild) zu 153,7 mm "
                  "(4×5, Nutzfläche 96 × 120 mm)",
        "bemerkung": "",
    },
    "AUGENHOEHE_SPANNE_M": {
        "wert": AUGENHOEHE_SPANNE_M,
        "art": "norm",
        "quelle": "DIN 33402-2 über die Kleine ergonomische Datensammlung der BAuA "
                  "(Sekundärwiedergabe, Norm nicht im Original geprüft)",
        "bemerkung": "Frauen 1430–1605 mm, Männer 1530–1735 mm (5./95. Perzentil).",
    },
    "AUGENHOEHE_MAENNER_P95_M": {
        "wert": AUGENHOEHE_MAENNER_P95_M,
        "art": "norm",
        "quelle": "DIN 33402-2 über BAuA/iba.online",
        "bemerkung": "Die projektgesetzten 1,70 m liegen hier, nicht in der Mitte.",
    },
    "BODENANTEIL_OHNE_SHIFT": {
        "wert": BODENANTEIL_OHNE_SHIFT,
        "art": "geometrie",
        "quelle": "waagrechte Kamera ohne Shift: der Horizont liegt auf der optischen "
                  "Achse, also exakt in der Bildmitte",
        "bemerkung": "Gilt für jede Brennweite, jeden Abstand und jedes Format.",
    },
    "DRITTELREGEL_KORRELATION": {
        "wert": DRITTELREGEL_KORRELATION,
        "art": "studie",
        "quelle": "Amirshahi, Hayn-Leichsenring, Denzler, Redies: Evaluating the Rule of "
                  "Thirds in Photographs and Paintings, Art & Perception 2 (2014) 163–182",
        "bemerkung": "Spearman ρ = 0,17 zwischen Ästhetikurteil und Drittelregel-Treue; "
                     "mit berechneten Werten gar keine Korrelation. Die Drittelregel ist "
                     "als Beschreibung der Praxis widerlegt.",
    },
    "BODENANTEIL_MESSREIHE_2026_08_20": {
        "wert": BODENANTEIL_MESSREIHE_2026_08_20,
        "art": "messung",
        "quelle": "eigene Messreihe, docs/EMPFINDLICHKEIT_2026-08-20.md und "
                  "docs/POLARITAET_2026-08-21.md",
        "bemerkung": "Der Bodenanteil der Szene, an der die Geometrie-QA versagte.",
    },
}


# ======================================================================================
# ======================================================================================
#
#   B · P R O J E K T S E T Z U N G E N   —   K E I N E   F U N D E
#
#   Alles unterhalb dieser Schranke ist eine Entscheidung dieses Projekts. Die Recherche
#   hat dazu nichts gefunden, oder sie hat sich widersprochen und jemand musste wählen.
#
#   Jede Setzung trägt, wer sie gesetzt hat und wann. Keine Setzung trägt eine Quelle —
#   das ist keine Nachlässigkeit, sondern der Unterschied.
#
#   Wer hier eine Zahl in Teil A verschiebt, behauptet, jemand habe sie gemessen.
#
# ======================================================================================
# ======================================================================================

#: **GESETZT.** Augenhöhe aussen in Metern, über dem Bezugspunkt.
#:
#: 1,70 m ist keine Mitte, sondern ein hoher Wert: Er liegt nahe dem 95. Perzentil der
#: Männer (:data:`AUGENHOEHE_MAENNER_P95_M`). Vertretbar, aber gewählt.
SETZUNG_AUGENHOEHE_AUSSEN_M = 1.70

#: **GESETZT.** Der Bezugspunkt, auf den sich die Kamerahöhe aussen bezieht.
SETZUNG_BEZUGSPUNKT_AUSSEN = "terrain_an_kamera"

#: **GESETZT (vorgeschlagen, nicht entschieden).** Anteil der Bildbreite, auf dem eine
#: Stütze im Innenraumbild sitzen soll — 2/3 von links oder von rechts.
#:
#: Zur Bildposition einer Stütze findet die Recherche **keine einzige** Aussage. Weder in
#: der Architekturfotografie noch in den Immobilienratgebern. Diese Regel ist mit der
#: Drittelregel verträglich — aber die Drittelregel ist als Praxisbeschreibung widerlegt
#: (:data:`DRITTELREGEL_KORRELATION`), taugt also nicht als Begründung.
SETZUNG_STUETZE_BILDANTEIL = 2.0 / 3.0

SETZUNGEN = {
    "SETZUNG_AUGENHOEHE_AUSSEN_M": {
        "wert": SETZUNG_AUGENHOEHE_AUSSEN_M,
        "gesetzt_von": "Owner (Pflichtenheft)",
        "gesetzt_am": "2026-08-14",
        "stand": "entschieden",
        "begruendung": "Mehrheit der Fundstellen im Bestand und das ausgereifteste "
                       "Verfahren dort halten es so.",
        "recherche": "Keine institutionelle Vorgabe nennt eine Kamerahöhe. HABS und das "
                     "Bayerische Landesamt für Denkmalpflege regeln Format, Objektivsatz "
                     "und Ansichtenkatalog — keine Silbe zur Höhe "
                     "(KOMPOSITION_AUSSEN.md 1.2a).",
        "preis": "1,70 m liegt nahe dem 95. Perzentil der Männer. Die Wirkung des "
                 "Unterschieds zu 1,60 m ist mit 0,6–1,2 Prozentpunkten am Baukörper "
                 "unsichtbar — der Bezugspunkt entscheidet, nicht die 100 mm.",
    },
    "SETZUNG_BEZUGSPUNKT_AUSSEN": {
        "wert": SETZUNG_BEZUGSPUNKT_AUSSEN,
        "gesetzt_von": "Owner / Sitzung 07-08",
        "gesetzt_am": "2026-08-19",
        "stand": "entschieden",
        "begruendung": "Der Fotograf steht auf dem Gelände an seiner eigenen XY-Position. "
                       "SketchUp sagt dasselbe: „directly above the point you click“.",
        "recherche": "Fünf verschiedene Nullpunkte heissen alle „Augenhöhe“ "
                     "(KOMPOSITION_AUSSEN.md 1.2d). Die Recherche stützt diese Wahl, "
                     "belegt sie aber nicht — es gibt keine Norm dazu.",
        "preis": "Das Gelände muss die Zahl liefern. Aus der Gebäudegeometrie ist sie "
                 "nicht ableitbar; am Hang ist die Hüllbox-Unterkante die falsche Antwort.",
    },
    "SETZUNG_STUETZE_BILDANTEIL": {
        "wert": SETZUNG_STUETZE_BILDANTEIL,
        "gesetzt_von": "Owner (Vorschlag)",
        "gesetzt_am": "2026-08-19",
        "stand": "vorgeschlagen",
        "begruendung": "Vorschlag des Owners: „Wenn ein Innenraumfoto eine Stütze zeigt, "
                       "wird die Stütze auf 2/3 links oder rechts platziert.“",
        "recherche": "NICHTS GEFUNDEN. Gezielt gesucht (KOMPOSITION_INNEN.md 2.2): keine "
                     "Quelle formuliert eine Positionsregel für Stützen. Belegt ist nur "
                     "ihre Rolle als Vordergrund- und Rahmungselement, ohne Position.",
        "preis": "Zwei der fachlich stärksten Quellen lehnen Positionsregeln grundsätzlich "
                 "ab (Tjintjelaar, Freeman). Die Regel ist legitim zu setzen; sie als "
                 "„so machen es Architekturfotografen“ auszugeben, wäre falsch.",
    },
}


# ======================================================================================
# C · UNGEMESSEN — die Fragen, auf die es keine Zahl gibt
#
# Nicht „noch nicht recherchiert", sondern: gesucht und nicht gefunden. `wert` ist hier
# immer None. Wo ein Ratgeber trotzdem eine Zahl nennt, steht sie unter `behauptet` —
# als Zitat, nicht als Wert.
# ======================================================================================

UNGEMESSEN = {
    "bodenanteil_zielwert_aussen": {
        "wert": None,
        "frage": "Welchen Anteil des Bildes soll der Boden bei einer Aussenaufnahme "
                 "einnehmen?",
        "befund": "Keine gefundene Konvention nennt einen Prozentsatz für den Bodenanteil. "
                  "Der Himmel hat eine benannte Untergrenze (Negativraum ≥ 1/3), der "
                  "Boden hat keine (BILDPROPORTIONEN.md Teil 3 Nr. 10).",
        "behauptet": "„Horizont auf der unteren Drittellinie“ — entspricht 33,3 % "
                     "Boden und verlangt im Hochformat 6 mm Shift. Ratgeberliteratur, "
                     "allgemeine Fotografie, nicht Architektur.",
    },
    "fluchtpunkt_verschiebung": {
        "wert": None,
        "frage": "Wohin wird der Fluchtpunkt verschoben, wenn er nicht mittig bleibt?",
        "befund": "Das Verfahren ist belegt (Kelley verschiebt ihn per Shift), ein "
                  "Zielwert wird nirgends genannt (KOMPOSITION_INNEN.md 3.5).",
        "behauptet": "",
    },
    "anschnitt_schwelle": {
        "wert": None,
        "frage": "Wie stark darf ein Vordergrundobjekt angeschnitten sein?",
        "befund": "Belegt ist nur „deutlich ja, knapp nein“ — knapper Anschnitt wirkt "
                  "versehentlich. Die Schwelle wird nie beziffert "
                  "(KOMPOSITION_INNEN.md 3.6).",
        "behauptet": "",
    },
    "eingang_bildposition": {
        "wert": None,
        "frage": "Wo sitzt der Eingang im Bild?",
        "befund": "Keine Quelle nennt eine Bildposition für den Eingang bei "
                  "Aussenaufnahmen (KOMPOSITION_AUSSEN.md 2.1).",
        "behauptet": "Kamerahöhe „auf Höhe der Eingangstür“ — das ist eine "
                     "Höhenregel, keine Bildpositionsregel (Immobilienfotografie).",
    },
    "gebaeudeecke_bildposition": {
        "wert": None,
        "frage": "Wo sitzt die vertikale Hauptkante bei der Über-Eck-Aufnahme?",
        "befund": "Keine Positionsangabe gefunden (KOMPOSITION_AUSSEN.md 2.1).",
        "behauptet": "„vertical elements … should be positioned along the vertical grid "
                     "lines“ — ohne Angabe, welche. Ratgeber.",
    },
    "wandanzahl_innen": {
        "wert": None,
        "frage": "Sollen zwei oder drei Wände im Innenraumbild sichtbar sein?",
        "befund": "Kein Konsens, sondern zwei Ziele: drei Wände zeigen das Mass, zwei "
                  "lassen den Raum gross wirken. Der Streit ist unter Praktikern "
                  "dokumentiert (KOMPOSITION_INNEN.md 3.3). Einig sind sich alle nur "
                  "im Negativen: vier Wände (Kamera in der Raummitte) ist falsch.",
        "behauptet": "",
    },
    "neigung_bei_absichtlichem_regelbruch": {
        "wert": None,
        "frage": "Wie stark darf gekippt werden, wenn stürzende Linien gewollt sind?",
        "befund": "Es gibt keinen ableitbaren Neigungswinkel. Die einzige gefundene Zahl "
                  "(„ca. 50 % Korrektur“, Schörner) ist ein Einzelbeispiel, und der "
                  "Autor begründet ausdrücklich, warum es keine Formel geben kann "
                  "(KOMPOSITION_AUSSEN.md Teil 5.1).",
        "behauptet": "",
    },
    "ueber_eck_winkel": {
        "wert": None,
        "frage": "Unter welchem Winkel steht die Über-Eck-Ansicht?",
        "befund": "HABS verlangt die Über-Eck-Ansicht, nennt aber keinen Winkel. Die "
                  "45° stammen ausschliesslich aus Ratgeber- und "
                  "Visualisierungsquellen (KOMPOSITION_AUSSEN.md 1.3, 4.1).",
        "behauptet": "45° zur Fassadennormale, mehrfach und konsistent — siehe "
                     "UEBER_ECK_WINKEL_BEHAUPTET_GRAD. Für Autos gibt es eine Auszählung "
                     "(90 % der Titelbilder), für Architektur keine.",
    },
}


def belegstufe(name: str) -> str:
    """Die Belegstufe eines Namens: ``belegt``, ``gesetzt`` oder ``ungemessen``.

    Der Sinn dieser Funktion ist, dass man sie **nicht umgehen** kann: Wer eine Zahl aus
    diesem Modul benutzt, kann in einer Zeile erfahren, ob sie gemessen, entschieden oder
    schlicht unbekannt ist.

    Raises:
        KompositionError: Der Name steht in keiner der drei Ablagen. Bewusst ein Fehler
            und kein ``"unbekannt"`` — ein stiller Rückgabewert liesse einen Tippfehler
            wie eine Auskunft aussehen.
    """
    if name in BELEGT:
        return "belegt"
    if name in SETZUNGEN:
        return "gesetzt"
    if name in UNGEMESSEN:
        return "ungemessen"
    raise KompositionError(
        f"Unbekannter Name: {name!r}. Bekannt sind die Schlüssel von BELEGT, SETZUNGEN "
        "und UNGEMESSEN."
    )


def herkunft(name: str) -> dict:
    """Der vollständige Eintrag zu einem Namen, samt Belegstufe.

    Returns:
        dict — eine **Kopie** des Eintrags, ergänzt um ``belegstufe`` und ``name``. Kopie,
        damit ein Aufrufer die Registratur nicht versehentlich umschreibt.
    """
    stufe = belegstufe(name)
    ablage = {"belegt": BELEGT, "gesetzt": SETZUNGEN, "ungemessen": UNGEMESSEN}[stufe]
    eintrag = dict(ablage[name])
    eintrag["name"] = name
    eintrag["belegstufe"] = stufe
    return eintrag


# ======================================================================================
# Prüfhelfer
# ======================================================================================

def _zahl(wert, name: str) -> float:
    """Endliche Zahl, oder ``KompositionError``. ``bool`` gilt nicht als Zahl."""
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):
        raise KompositionError(f"{name} muss eine Zahl sein, war: {wert!r}")
    x = float(wert)
    if not math.isfinite(x):
        raise KompositionError(f"{name} muss endlich sein, war: {wert!r}")
    return x


def _positiv(wert, name: str) -> float:
    x = _zahl(wert, name)
    if x <= 0.0:
        raise KompositionError(f"{name} muss positiv sein, war: {wert!r}")
    return x


def _nicht_negativ(wert, name: str) -> float:
    x = _zahl(wert, name)
    if x < 0.0:
        raise KompositionError(f"{name} darf nicht negativ sein, war: {wert!r}")
    return x


# ======================================================================================
# 1 · Die waagrechte Kamera, der Shift und die Konvergenz
# ======================================================================================

def neigung_grad(*, hoehendifferenz_m: float, abstand_m: float) -> float:
    """Neigung in Grad, die nötig ist, um von der Kamera auf ein Blickziel zu schauen.

    Das ist die Rechnung, die ``kameras.py`` implizit anstellt, wenn es das Blickziel über
    die Augenhöhe legt. Sie ist hier explizit gemacht, damit die Zahl sichtbar wird.

    **Der Befund, den diese Funktion trägt:** Wächst der Abstand proportional zur
    Gebäudehöhe (und tut es die Zielanhebung auch), kürzt sich das Gebäudemass heraus und
    die Neigung ist **konstant**. Bei ``ZIEL_ANTEIL_HOEHE = 0.20`` und einem Abstand von
    1,2 × Gebäudehöhe sind das ``atan(0.20 / 1.2)`` = 9,4623° — für einen 6-m-Schuppen
    genauso wie für ein 40-m-Haus.

    Args:
        hoehendifferenz_m: Blickziel minus Kamerahöhe, in Metern. Negativ heisst: Die
            Kamera schaut nach unten.
        abstand_m: horizontaler Abstand Kamera ↔ Blickziel, in Metern.

    Returns:
        Neigung in Grad. Positiv = nach oben, negativ = nach unten, exakt 0 nur bei
        ``hoehendifferenz_m == 0``.
    """
    dz = _zahl(hoehendifferenz_m, "hoehendifferenz_m")
    d = _positiv(abstand_m, "abstand_m")
    return math.degrees(math.atan2(dz, d))


def konvergenz(*, neigung_grad: float, gebaeudehoehe_m: float,
               kamerahoehe_m: float, abstand_m: float) -> float:
    """Wie stark die Vertikalen im Bild aufeinander zulaufen. 0 bei waagrechter Kamera.

    **Die Definition, weil eine Konvergenzzahl ohne sie nichts bedeutet:** Verglichen
    werden die Bildbreiten, die ein und dieselbe waagrechte Strecke an der
    Gebäudeoberkante und am Gebäudefuss im Bild einnimmt. Der Rückgabewert ist

        ``1 − Breite(Oberkante) / Breite(Fuss)``

    also der Anteil, um den die Fassade oben schmaler erscheint als unten. Die Bildbreite
    ist umgekehrt proportional zur Tiefe entlang der optischen Achse; bei um ``θ`` nach
    oben geneigter Kamera ist die Tiefe eines Punktes auf Höhe ``z`` über der Kamera

        ``t(z) = abstand · cos θ + z · sin θ``

    Bei ``θ = 0`` ist ``t`` von ``z`` unabhängig, beide Breiten sind gleich, und der
    Rückgabewert ist **exakt 0** — die Vertikalen bleiben parallel. Das ist die Regel des
    Fachs, in eine Zahl gefasst.

    **Was diese Zahl nicht ist:** ein Winkel. Sie ist ein Verhältnis und hängt ausser von
    der Neigung auch davon ab, welchen Winkelbereich das Bauwerk einnimmt. Zwei Aufnahmen
    mit gleicher Neigung können verschiedene Konvergenz haben, wenn die eine näher steht.

    Args:
        neigung_grad: Kameraneigung in Grad, positiv nach oben.
        gebaeudehoehe_m: Höhe des Bauwerks über dem Gelände.
        kamerahoehe_m: Kamerahöhe über demselben Gelände.
        abstand_m: horizontaler Abstand zur Fassadenebene.

    Returns:
        Anteil zwischen −1 und 1. Positiv: Vertikalen laufen nach oben zusammen
        (stürzende Linien). Negativ: Sie laufen nach oben auseinander — das passiert bei
        nach unten geneigter Kamera und ist derselbe Fehler mit anderem Vorzeichen.

    Raises:
        KompositionError: Der Gebäudefuss oder die Oberkante liegt hinter der Kameraebene.
            Dann ist das Verhältnis nicht definiert, und ein Zahlenwert wäre eine Lüge.
    """
    theta = math.radians(_zahl(neigung_grad, "neigung_grad"))
    hoehe = _positiv(gebaeudehoehe_m, "gebaeudehoehe_m")
    kamera = _nicht_negativ(kamerahoehe_m, "kamerahoehe_m")
    abstand = _positiv(abstand_m, "abstand_m")

    c, s = math.cos(theta), math.sin(theta)
    tiefe_fuss = abstand * c + (-kamera) * s
    tiefe_oben = abstand * c + (hoehe - kamera) * s
    if tiefe_fuss <= 0.0 or tiefe_oben <= 0.0:
        raise KompositionError(
            "Konvergenz nicht definiert: Bei Neigung "
            f"{neigung_grad}° und Abstand {abstand_m} m liegt Fuss oder Oberkante des "
            "Bauwerks hinter der Kameraebene "
            f"(Tiefe Fuss {tiefe_fuss:.3f} m, Tiefe Oberkante {tiefe_oben:.3f} m)."
        )
    return 1.0 - tiefe_fuss / tiefe_oben


def horizontanteil(*, shift_mm: float = 0.0,
                   sensor_hoehe_mm: float = SENSOR_HOEHE_QUER_MM) -> float:
    """Anteil der Bildhöhe **unterhalb** des Horizonts: ``(s/2 − v) / s``.

    Der ganze Inhalt dieser Funktion ist, dass Kamerahöhe, Abstand und Brennweite darin
    **nicht vorkommen**. Bei waagrechter Kamera liegt der Horizont auf der optischen
    Achse; wo die Achse im Bild sitzt, entscheidet allein der Shift.

    Ohne Shift: exakt 0,5. Mit vollem Shift nach oben (11 mm, quer): 4,2 %. Mit Shift
    **nach unten** geht es über 0,5 hinaus — siehe :func:`bodenanteil_erreichbar`.

    Args:
        shift_mm: Versatz der Sensormitte gegen die optische Achse, in Millimetern.
            Positiv = nach oben geshiftet (mehr Himmel), negativ = nach unten.
        sensor_hoehe_mm: Sensorhöhe in Aufnahmelage.

    Returns:
        Anteil zwischen 0 und 1.

    Raises:
        KompositionError: ``|shift_mm| > sensor_hoehe_mm / 2``. Dann läge der Horizont
            ausserhalb des Bildes; ein Anteil unter 0 oder über 1 ist keine Antwort.
    """
    v = _zahl(shift_mm, "shift_mm")
    s = _positiv(sensor_hoehe_mm, "sensor_hoehe_mm")
    if abs(v) > s / 2.0:
        raise KompositionError(
            f"shift_mm = {v} liegt ausserhalb des Sensors (halbe Sensorhöhe {s / 2.0} mm). "
            "Der Horizont läge dann gar nicht mehr im Bild."
        )
    return (s / 2.0 - v) / s


def bodenanteil_erreichbar(anteil: float, *,
                           sensor_hoehe_mm: float = SENSOR_HOEHE_QUER_MM,
                           shift_hoechstwert_mm: float = SHIFT_HOECHSTWERT_MM) -> dict:
    """Ist dieser Bodenanteil mit **waagrechter** Kamera erreichbar, und mit welchem Shift?

    **Hier widerspreche ich der Recherche, und zwar begründet.** Der übliche Satz lautet:
    „Shift regelt von 50 % abwärts; über 50 % kommt man nur durch Kippen." Der zweite Teil
    ist als Aussage über die Praxis richtig und als Aussage über die Geometrie falsch. Der
    belegte Verstellweg ist ±11 mm — **in jede Richtung**. Ein Shift nach unten hebt den
    Bodenanteil über 50 %, ohne die Sensorebene aus dem Lot zu bringen, also ohne jede
    Konvergenz.

    Für die 59,8 % der Messreihe vom 20./21.08. sind das −2,35 mm am Querformat: ein
    Zwölftel des Wegs. Geometrisch also mühelos — und trotzdem fotografisch unbeschrieben.
    Keine der gesichteten Quellen beschreibt einen Shift nach unten; Shift wird
    ausschliesslich nach oben benutzt, um den Bau ins Bild zu holen und den Boden
    loszuwerden. **Das ist der ehrliche Stand: nicht unmöglich, sondern unüblich.**

    Args:
        anteil: gewünschter Bodenanteil, 0 bis 1.
        sensor_hoehe_mm: Sensorhöhe in Aufnahmelage.
        shift_hoechstwert_mm: verfügbarer Verstellweg in jede Richtung.

    Returns:
        dict mit ``erreichbar`` (bool), ``shift_mm`` (der nötige, vorzeichenbehaftete
        Shift), ``richtung`` (``"aufwaerts"``, ``"abwaerts"`` oder ``"kein_shift"``),
        ``ueber_der_haelfte`` (bool) und ``bemerkung``.
    """
    a = _zahl(anteil, "anteil")
    if not (0.0 <= a <= 1.0):
        raise KompositionError(f"anteil muss zwischen 0 und 1 liegen, war: {anteil!r}")
    s = _positiv(sensor_hoehe_mm, "sensor_hoehe_mm")
    grenze = _positiv(shift_hoechstwert_mm, "shift_hoechstwert_mm")

    # Aus (s/2 - v)/s = a folgt v = s * (0.5 - a).
    v = s * (0.5 - a)
    if v > 0.0:
        richtung = "aufwaerts"
    elif v < 0.0:
        richtung = "abwaerts"
    else:
        richtung = "kein_shift"
    erreichbar = abs(v) <= grenze and abs(v) <= s / 2.0

    if richtung == "abwaerts" and erreichbar:
        bemerkung = ("Erreichbar, aber durch Shift NACH UNTEN. Geometrisch einwandfrei "
                     "(Vertikalen bleiben parallel), fotografisch in keiner gefundenen "
                     "Quelle beschrieben.")
    elif not erreichbar:
        bemerkung = (f"Nicht erreichbar: nötig wären {v:.2f} mm Shift, verfügbar sind "
                     f"±{grenze:.2f} mm.")
    else:
        bemerkung = "Erreichbar mit dem üblichen Shift nach oben."

    return {
        "anteil": a,
        "erreichbar": bool(erreichbar),
        "shift_mm": v,
        "richtung": richtung,
        "ueber_der_haelfte": a > BODENANTEIL_OHNE_SHIFT,
        "bemerkung": bemerkung,
    }


# ======================================================================================
# 2 · Der nötige Abstand — hergeleitet, nicht geraten
# ======================================================================================

def mindestabstand(*, gebaeudehoehe_m: float, kamerahoehe_m: float,
                   brennweite_mm: float = ARBEITSBRENNWEITE_AUSSEN_MM,
                   sensor_hoehe_mm: float = SENSOR_HOEHE_HOCH_MM,
                   shift_mm: float = 0.0) -> dict:
    """Wie weit die Kamera weg muss, damit Dach **und** Fuss im Bild sind.

    Bei waagrechter Kamera gibt es dafür genau eine Rechnung, und sie hat zwei Terme::

        Dach im Bild   ⇔   d ≥ f · (H − h) / (s/2 + v)
        Fuss im Bild   ⇔   d ≥ f · h       / (s/2 − v)
        d_min = max(beide)

    **Der zweite Term ist der, den eine naive Umsetzung übersieht.** Je stärker nach oben
    geshiftet wird, desto weiter muss man weg, damit der **Gebäudefuss** überhaupt noch
    im Bild ist. Bei 8 m Höhe, 1,70 m Kamerahöhe, 24 mm im Hochformat und vollem Shift
    (12 mm) sind es 6,8 m — wegen des Sockels, nicht wegen der Traufe. Ohne Shift wären
    es 8,4 m, und dann bindet das Dach.

    **Dieselbe Formel gilt innen**, mit ``gebaeudehoehe_m`` = lichte Raumhöhe: Dann sagt
    der erste Term, ab wann die Deckenkante der Stirnwand im Bild liegt, und der zweite,
    ab wann die Bodenkante es tut. Das ist keine Analogie, sondern dieselbe Geometrie.

    Die Recherche merkt an, dass sie diese Herleitung in **keiner** Quelle so gefunden
    hat. Sie ist nachrechenbar, aber nirgends aufgeschrieben — vermutlich, weil sie sich
    zwingend aus der waagrechten Kamera ergibt und deshalb niemandem der Rede wert war.

    Args:
        gebaeudehoehe_m: Höhe über Gelände (aussen) bzw. lichte Raumhöhe (innen).
        kamerahoehe_m: Kamerahöhe über demselben Bezugspunkt.
        brennweite_mm: Brennweite, Kleinbild.
        sensor_hoehe_mm: Sensorhöhe in Aufnahmelage. Vorgabe ist das **Hochformat** —
            der Regelfall, wenn ein Bau ganz ins Bild soll.
        shift_mm: Shift nach oben in Millimetern.

    Returns:
        dict mit ``abstand_m``, ``dach_m``, ``fuss_m``, ``bindend``
        (``"dach"``, ``"fuss"`` oder ``"beide"``) und ``faktor_hoehe`` (``d/H``, die
        Zahl, die eine Faustregel gerne wäre — sie ist **nicht** konstant).

    Raises:
        KompositionError: ``s/2 − shift ≤ 0``. Dann ist der zweite Term nicht definiert:
            Der Shift hat den Horizont auf oder unter die Bildunterkante geschoben, und
            **kein** Abstand bringt den Gebäudefuss ins Bild. Das ist ein Fehler mit
            Erklärung, keine stille Division.
    """
    H = _positiv(gebaeudehoehe_m, "gebaeudehoehe_m")
    h = _nicht_negativ(kamerahoehe_m, "kamerahoehe_m")
    f = _positiv(brennweite_mm, "brennweite_mm")
    s = _positiv(sensor_hoehe_mm, "sensor_hoehe_mm")
    v = _zahl(shift_mm, "shift_mm")

    if h > H:
        raise KompositionError(
            f"kamerahoehe_m ({h}) liegt über gebaeudehoehe_m ({H}). Dann schaut die "
            "Kamera auf das Dach herab, und „Dach und Fuss im Bild“ ist die falsche "
            "Frage."
        )

    unten = s / 2.0 - v
    if unten <= 0.0:
        raise KompositionError(
            f"shift_mm = {v} erreicht oder überschreitet die halbe Sensorhöhe "
            f"({s / 2.0} mm). Der Horizont liegt damit auf oder unter der Bildunterkante — "
            "kein Abstand bringt den Gebäudefuss ins Bild. Der Ausdruck "
            "f·h/(s/2 − v) ist nicht definiert."
        )
    oben = s / 2.0 + v
    if oben <= 0.0:
        raise KompositionError(
            f"shift_mm = {v} liegt unterhalb der negativen halben Sensorhöhe "
            f"(−{s / 2.0} mm). Der Horizont läge über der Bildoberkante — kein Abstand "
            "bringt die Gebäudeoberkante ins Bild."
        )

    dach = f * (H - h) / oben
    fuss = f * h / unten
    if math.isclose(dach, fuss, rel_tol=1e-12, abs_tol=1e-12):
        bindend = "beide"
    else:
        bindend = "dach" if dach > fuss else "fuss"
    abstand = max(dach, fuss)
    return {
        "abstand_m": abstand,
        "dach_m": dach,
        "fuss_m": fuss,
        "bindend": bindend,
        "faktor_hoehe": abstand / H,
    }


def kleinbild_aequivalent(brennweite_grossformat_mm: float, *,
                          faktor: float = GROSSFORMAT_FAKTOR_4X5) -> float:
    """Brennweite am 4×5-Planfilm → Kleinbild-Äquivalent, in Millimetern.

    Damit wird der HABS-Objektivsatz von 1933 (65 / 90 / 150 / 210 mm) mit heutigen
    Angaben vergleichbar: 18,3 / 25,3 / 42,2 / 59,1 mm. Der Normalfall der Vorschrift,
    90 mm, liegt bei 25,3 mm — und damit auf demselben Wert, den die heutige
    Ratgeberliteratur unabhängig nennt.
    """
    f = _positiv(brennweite_grossformat_mm, "brennweite_grossformat_mm")
    k = _positiv(faktor, "faktor")
    return f * k


# ======================================================================================
# 3 · Die Kamerahöhe — und zwar mit Bezugspunkt
# ======================================================================================

#: Die Nullpunkte, die alle „Augenhöhe" heissen und verschiedene Orte meinen.
#:
#: Fünf Stück, und im Projekt ist an dieser Stelle schon zweimal etwas schiefgegangen.
#: Darum ist der Bezugspunkt in :func:`kamerahoehe` ein **Pflichtargument**: Es gibt
#: keine Vorgabe, weil jede Vorgabe irgendwo falsch wäre.
BEZUGSPUNKTE = {
    "terrain_an_kamera": {
        "beschreibung": "Gelände an der XY-Position der Kamera. Was der Fotograf meint; "
                        "SketchUp sagt „directly above the point you click“.",
        "kippt_wenn": "Am Hang ist das nicht die Erdgeschosshöhe. Der Nullpunkt gehört "
                      "zum Gelände, nicht zum Gebäude.",
        "verlaesslich": True,
    },
    "okff": {
        "beschreibung": "Oberkante Fertigfussboden des betretenen Raums. Der Bezug für "
                        "Innenaufnahmen.",
        "kippt_wenn": "Weicht am Hang und bei Sockelgeschossen vom Terrain ab. In IFC ist "
                      "das die begehbare Oberfläche, nicht IfcBuildingStorey.Elevation.",
        "verlaesslich": True,
    },
    "huellbox_unterkante": {
        "beschreibung": "Unterkante der achsparallelen Hüllbox. Was naive "
                        "Bounding-Box-Umsetzungen meinen.",
        "kippt_wenn": "Bei einem Untergeschoss liegt sie im Erdreich — die Kamera steht "
                      "im Keller.",
        "verlaesslich": False,
    },
    "weltnull": {
        "beschreibung": "z = 0 des Koordinatensystems.",
        "kippt_wenn": "Bei einem Landeskoordinatensystem (LV95, m ü. M.) sind das "
                      "mehrere hundert Meter Fehler, ohne jede Warnung. Genau dieser "
                      "Fall ist in kameras.py schon aufgetreten.",
        "verlaesslich": False,
    },
    "bauteil_oberkante": {
        "beschreibung": "Oberkante eines Bauteils (Eingangstür, Arbeitsplatte, Matratze). "
                        "Was die Immobilienfotografie meint, wenn sie Zahlen nennt.",
        "kippt_wenn": "Das ist gar keine Höhenangabe im Sinn des Renderers, sondern eine "
                      "Bezugnahme auf Geometrie. „Arbeitsplatte + 0,45 m“ sind "
                      "1,35–1,40 m über OKFF, nicht 0,45 m.",
        "verlaesslich": False,
    },
}


def kamerahoehe(hoehe_m: float, *, bezugspunkt: str) -> dict:
    """Eine Kamerahöhe mit ihrem Nullpunkt — und mit den Warnungen, die dazugehören.

    ``bezugspunkt`` ist ein Pflichtargument ohne Vorgabewert. Das ist der ganze Zweck
    dieser Funktion: **Die 100 mm sind gleichgültig, der Nullpunkt ist es nicht.**

    Die Zahlen dazu (:func:`horizont_am_baukoerper`): Der Unterschied zwischen 1,60 m und
    1,70 m verschiebt den Horizont am Baukörper um 0,6 bis 1,2 Prozentpunkte — das sieht
    niemand. Ein falscher Bezugspunkt, etwa ein Geschoss daneben, verschiebt ihn um 2,3
    bis 17,5 Prozentpunkte — und das sieht man.

    Die Recherche findet **keine** eindeutige Kamerahöhe: veröffentlichte Werte von 1,50
    bis 1,83 m mit fünf verschiedenen Nullpunkten, und keine institutionelle Vorgabe nennt
    überhaupt eine. Anthropometrisch spannt die Augenhöhe Erwachsener 1,43–1,74 m
    (DIN 33402-2). **1,70 m liegt nahe dem 95. Perzentil der Männer** — keine Mitte,
    sondern eine Setzung.

    Args:
        hoehe_m: Höhe in Metern über dem genannten Bezugspunkt.
        bezugspunkt: einer der Schlüssel von :data:`BEZUGSPUNKTE`.

    Returns:
        dict mit ``hoehe_m``, ``bezugspunkt``, ``beschreibung``, ``verlaesslich``,
        ``belegstufe`` (immer ``"gesetzt"`` — eine Kamerahöhe ist nirgends belegt) und
        ``warnungen``.

    Raises:
        KompositionError: unbekannter Bezugspunkt, oder eine unbrauchbare Höhe.
    """
    h = _positiv(hoehe_m, "hoehe_m")
    if not isinstance(bezugspunkt, str) or bezugspunkt not in BEZUGSPUNKTE:
        raise KompositionError(
            f"Unbekannter bezugspunkt: {bezugspunkt!r}. Bekannt sind: "
            f"{', '.join(sorted(BEZUGSPUNKTE))}. Es gibt hier bewusst keine Vorgabe — "
            "jede wäre irgendwo falsch."
        )

    eintrag = BEZUGSPUNKTE[bezugspunkt]
    warnungen = []
    if not eintrag["verlaesslich"]:
        warnungen.append(
            f"Bezugspunkt {bezugspunkt!r} ist im Projekt schon schiefgegangen: "
            f"{eintrag['kippt_wenn']}"
        )
    unten, oben = AUGENHOEHE_SPANNE_M
    if not (unten <= h <= oben):
        warnungen.append(
            f"{h:.2f} m liegt ausserhalb der anthropometrischen Augenhöhenspanne "
            f"{unten:.2f}–{oben:.2f} m (DIN 33402-2). Das ist erlaubt — die Konvention "
            "bindet die Neigung, nicht die Höhe —, aber es ist keine Augenhöhe mehr."
        )
    if h > AUGENHOEHE_MAENNER_P95_M:
        warnungen.append(
            f"{h:.2f} m liegt über dem 95. Perzentil der Männer "
            f"({AUGENHOEHE_MAENNER_P95_M:.3f} m)."
        )
    return {
        "hoehe_m": h,
        "bezugspunkt": bezugspunkt,
        "beschreibung": eintrag["beschreibung"],
        "verlaesslich": eintrag["verlaesslich"],
        "belegstufe": "gesetzt",
        "warnungen": warnungen,
    }


def horizont_am_baukoerper(*, kamerahoehe_m: float, gebaeudehoehe_m: float) -> float:
    """Wo der Horizont die Fassade schneidet, als Anteil der Gebäudehöhe: ``h / H``.

    Die Horizontlinie trifft die Fassade **genau auf Kamerahöhe**. Damit teilt sie die
    Bildhöhe des Gebäudes im Verhältnis ``h : (H − h)`` — und zwar **unabhängig von
    Abstand, Brennweite, Format und Shift**. Dass diese vier Grössen hier nicht als
    Argumente vorkommen, ist die Aussage der Funktion, nicht ihre Bequemlichkeit.

    Bei 8 m Höhe: 1,60 m → 20,0 %, 1,70 m → 21,3 %, 3,00 m (ein Geschoss daneben) →
    37,5 %.
    """
    h = _nicht_negativ(kamerahoehe_m, "kamerahoehe_m")
    H = _positiv(gebaeudehoehe_m, "gebaeudehoehe_m")
    if h > H:
        raise KompositionError(
            f"kamerahoehe_m ({h}) liegt über gebaeudehoehe_m ({H}); der Horizont "
            "schneidet die Fassade dann gar nicht."
        )
    return h / H


def horizont_verschiebung_pp(*, gebaeudehoehe_m: float,
                             hoehe_a_m: float, hoehe_b_m: float) -> float:
    """Um wie viele **Prozentpunkte** zwei Kamerahöhen den Horizont am Bau verschieben.

    Das ist die quantitative Fassung des Bezugspunkt-Problems dieses Projekts: Die
    Funktion beantwortet, ob ein Höhenunterschied eine Geschmacksfrage oder ein Fehler
    ist. 100 mm Unterschied sind Geschmack. Ein Geschoss Unterschied ist ein Fehler.
    """
    a = horizont_am_baukoerper(kamerahoehe_m=hoehe_a_m, gebaeudehoehe_m=gebaeudehoehe_m)
    b = horizont_am_baukoerper(kamerahoehe_m=hoehe_b_m, gebaeudehoehe_m=gebaeudehoehe_m)
    return abs(a - b) * 100.0


def hoehe_fuer_bild_gleichgewicht(raumhoehe_m: float, *, shift_mm: float = 0.0,
                                  abstand_m: float | None = None,
                                  brennweite_mm: float | None = None) -> float:
    """Die Kamerahöhe, bei der Boden und Decke **exakt gleich viel** Bildfläche bekommen.

    Ohne Shift ist die Antwort ``raumhoehe / 2`` — und das ist die einzige harte,
    geometrisch beweisbare Bildpositionsregel, die dieses Modul kennt. Sie ist
    **unabhängig von Brennweite und Abstand**. Beweis in einer Zeile: Boden- und
    Deckenanteil unterscheiden sich um ``f · (H_r − 2h) / (D · s) − 2v/s``; der Term wird
    für ``v = 0`` genau dann null, wenn ``h = H_r / 2``, ohne dass ``f`` oder ``D``
    darin vorkommen.

    Bei 2,55 m lichter Raumhöhe sind das **1,275 m** — mitten im fotografischen Band von
    1,22–1,52 m, das die Innenraumfotografie unabhängig davon nennt. Die projektübliche
    Augenhöhe von 1,70 m liegt darüber und erzeugt dort ein deutliches Übergewicht der
    Decke.

    **Mit Shift verschiebt sich die Antwort**, und dann kommen Abstand und Brennweite doch
    ins Spiel: ``h = H_r/2 − v · D / f``. Das ist kein Widerspruch zur Regel, sondern ihre
    Verallgemeinerung — der Shift verschiebt das Bildfenster, und diese Verschiebung ist
    in Metern am Motiv gemessen abstands- und brennweitenabhängig.

    Args:
        raumhoehe_m: lichte Raumhöhe, OKFF bis Unterkante Decke.
        shift_mm: Shift nach oben.
        abstand_m: nur nötig, wenn ``shift_mm != 0``.
        brennweite_mm: nur nötig, wenn ``shift_mm != 0``.

    Raises:
        KompositionError: ``shift_mm != 0`` ohne ``abstand_m`` und ``brennweite_mm``.
            Bewusst ein Fehler statt einer stillen Näherung: Mit Shift ist ``H_r/2``
            schlicht die falsche Antwort.
    """
    hr = _positiv(raumhoehe_m, "raumhoehe_m")
    v = _zahl(shift_mm, "shift_mm")
    if v == 0.0:
        return hr / 2.0
    if abstand_m is None or brennweite_mm is None:
        raise KompositionError(
            f"shift_mm = {v} ist nicht 0; dann hängt die Gleichgewichtshöhe von Abstand "
            "und Brennweite ab und braucht beide. Ohne Shift gilt raumhoehe/2 — mit "
            "Shift gilt es nicht."
        )
    d = _positiv(abstand_m, "abstand_m")
    f = _positiv(brennweite_mm, "brennweite_mm")
    return hr / 2.0 - v * d / f


# ======================================================================================
# 4 · Boden- und Deckenanteil
# ======================================================================================

def _roh_boden(h: float, d: float, f: float, s: float, v: float) -> float:
    """Bodenanteil **ohne** Begrenzung: ``(s/2 − v − f·h/D) / s``.

    Steht als eigene Funktion da, damit ``bodenanteil`` und ``bildanteile`` dieselbe
    Formel benutzen statt zweier Abschriften. Ein negativer Wert heisst: Die Bodenkante
    der Stirnwand liegt unterhalb des Bildes, der Boden ist gar nicht sichtbar.
    """
    return (s / 2.0 - v - f * h / d) / s


def _roh_decke(h: float, hr: float, d: float, f: float, s: float, v: float) -> float:
    """Deckenanteil ohne Begrenzung: ``(s/2 + v − f·(H_r − h)/D) / s``.

    Der einzige Unterschied zu :func:`_roh_boden` ist das Vorzeichen vor dem Shift. Genau
    daraus folgt die Gleichgewichtsregel: Ein Shift nach oben nimmt dem Boden, was er der
    Decke gibt, und ihre Summe bleibt gleich.
    """
    return (s / 2.0 + v - f * (hr - h) / d) / s


def bodenanteil(*, kamerahoehe_m: float, abstand_m: float | None = None,
                brennweite_mm: float = ARBEITSBRENNWEITE_AUSSEN_MM,
                sensor_hoehe_mm: float = SENSOR_HOEHE_QUER_MM,
                shift_mm: float = 0.0,
                raumhoehe_m: float | None = None) -> float:
    """Welchen Anteil der Bildhöhe der Boden einnimmt, bei waagrechter Kamera.

    **Der Befund, der in diesen Docstring gehört:** Eine waagrechte Kamera **ohne** Shift
    legt den Horizont exakt in die Bildmitte — also 50 %. Der Shift regelt von 50 %
    abwärts, im Grenzfall (11 mm, quer) bis auf 4,2 %. Genau dazu ist er da: „choose how
    much sky and foreground to include without tilting the camera". Wieviel Boden im Bild
    ist, ist in der Architekturfotografie **kein Nebenprodukt des Standorts, sondern eine
    eingestellte Grösse**.

    **Warum das dieses Projekt hart trifft:** Die Szene, an der die Geometrie-QA am
    20./21.08.2026 versagte, hatte 59,8 % Bodenanteil — mehr, als der fotografische
    Normalfall überhaupt erzeugt. Die Praxis bewegt sich in die Gegenrichtung. Ob 59,8 %
    geometrisch unmöglich sind, beantwortet :func:`bodenanteil_erreichbar`, und die
    Antwort ist differenzierter als „nein" (siehe dort und im Modulkopf).

    **Zwei Fälle, eine Funktion:**

    * ``raumhoehe_m is None`` — **aussen**. Der Boden läuft bis zum Horizont, also nimmt
      er alles unterhalb davon ein: ``(s/2 − v)/s``. Kamerahöhe, Abstand und Brennweite
      **gehen nicht ein**; sie sind trotzdem erlaubt, damit derselbe Aufruf beide Fälle
      bedient. Vorausgesetzt ist ebener, unverstellter Boden bis zum Horizont — ein
      Hügel oder eine Nachbarbebauung nimmt Bodenfläche weg, und das rechnet hier
      niemand.
    * ``raumhoehe_m`` gesetzt — **innen**. Der Boden endet an der Stirnwand:
      ``(s/2 − v − f·h/D)/s``. Hier gehen alle Grössen ein.

    Der Rückgabewert ist auf ``[0, 1]`` begrenzt. **Das ist eine bewusste Abweichung von
    der Formel in der Recherche** (KOMPOSITION_INNEN.md 4.4), die unbegrenzt rechnet: Bei
    1,70 m Kamerahöhe in einem 2,55-m-Raum aus 3,0 m Abstand liefert sie −6,7 % Boden. Ein
    Anteil kann nicht negativ sein; die Zahl bedeutet dort, dass die Bodenkante der
    Stirnwand aus dem Bild fällt und der Boden gar nicht sichtbar ist. Wer den rohen Wert
    braucht, findet ihn in :func:`bildanteile` unter ``roh``.

    Raises:
        KompositionError: ``raumhoehe_m`` gesetzt, aber kein ``abstand_m``; oder
            ``|shift_mm|`` grösser als die halbe Sensorhöhe.
    """
    h = _nicht_negativ(kamerahoehe_m, "kamerahoehe_m")
    s = _positiv(sensor_hoehe_mm, "sensor_hoehe_mm")
    v = _zahl(shift_mm, "shift_mm")
    if abs(v) > s / 2.0:
        raise KompositionError(
            f"shift_mm = {v} liegt ausserhalb des Sensors (halbe Sensorhöhe {s / 2.0} mm)."
        )
    if raumhoehe_m is None:
        return horizontanteil(shift_mm=v, sensor_hoehe_mm=s)

    hr = _positiv(raumhoehe_m, "raumhoehe_m")
    if h > hr:
        raise KompositionError(
            f"kamerahoehe_m ({h}) liegt über raumhoehe_m ({hr}) — die Kamera steckt in "
            "der Decke."
        )
    if abstand_m is None:
        raise KompositionError(
            "Für den Innenraum braucht der Bodenanteil den Abstand zur Stirnwand "
            "(abstand_m). Ohne ihn ist die Bodenkante nicht zu verorten."
        )
    d = _positiv(abstand_m, "abstand_m")
    f = _positiv(brennweite_mm, "brennweite_mm")
    return min(1.0, max(0.0, _roh_boden(h, d, f, s, v)))


def deckenanteil(*, kamerahoehe_m: float, raumhoehe_m: float, abstand_m: float,
                 brennweite_mm: float = ARBEITSBRENNWEITE_AUSSEN_MM,
                 sensor_hoehe_mm: float = SENSOR_HOEHE_QUER_MM,
                 shift_mm: float = 0.0) -> float:
    """Welchen Anteil der Bildhöhe die Decke einnimmt: ``(s/2 + v − f·(H_r − h)/D)/s``.

    Nur innen. Aussen gibt es keine Decke — dort steht über dem Horizont der Himmel, und
    der ist keine Fläche des Bauwerks, sondern das, was übrig bleibt.

    Spiegelbildlich zum Bodenanteil, mit einem einzigen Vorzeichenwechsel beim Shift: Ein
    Shift nach oben nimmt dem Boden, was er der Decke gibt. Genau daraus folgt die
    Gleichgewichtsregel in :func:`hoehe_fuer_bild_gleichgewicht`.
    """
    h = _nicht_negativ(kamerahoehe_m, "kamerahoehe_m")
    hr = _positiv(raumhoehe_m, "raumhoehe_m")
    d = _positiv(abstand_m, "abstand_m")
    f = _positiv(brennweite_mm, "brennweite_mm")
    s = _positiv(sensor_hoehe_mm, "sensor_hoehe_mm")
    v = _zahl(shift_mm, "shift_mm")
    if abs(v) > s / 2.0:
        raise KompositionError(
            f"shift_mm = {v} liegt ausserhalb des Sensors (halbe Sensorhöhe {s / 2.0} mm)."
        )
    if h > hr:
        raise KompositionError(
            f"kamerahoehe_m ({h}) liegt über raumhoehe_m ({hr}) — die Kamera steckt in "
            "der Decke."
        )
    return min(1.0, max(0.0, _roh_decke(h, hr, d, f, s, v)))


def bildanteile(*, kamerahoehe_m: float, abstand_m: float | None = None,
                brennweite_mm: float = ARBEITSBRENNWEITE_AUSSEN_MM,
                sensor_hoehe_mm: float = SENSOR_HOEHE_QUER_MM,
                shift_mm: float = 0.0,
                raumhoehe_m: float | None = None) -> dict:
    """Boden, Decke, Wand und Horizont in einem Zug — mit den rohen Werten daneben.

    Der Wandanteil ist ``1 − Boden − Decke``. Bemerkenswert an ihm: Er hängt **nicht von
    der Kamerahöhe ab**, sondern nur von ``H_r / (D · s / f)``. Die Kamerahöhe verteilt
    nur zwischen Boden und Decke um; sie verändert nicht, wieviel Wand zu sehen ist. Das
    ist eine Aussage, die man an einer Innenaufnahme nachprüfen kann.

    ``roh`` trägt die unbegrenzten Werte. Ein negativer Rohwert heisst: Diese Kante liegt
    ausserhalb des Bildes. Die zugehörigen Wahrheitswerte ``boden_kante_im_bild`` und
    ``decken_kante_im_bild`` sagen dasselbe kürzer — und die Abstände, ab denen sie wahr
    werden, liefert :func:`mindestabstand`.

    Aussen (``raumhoehe_m is None``) sind ``deckenanteil`` und ``wandanteil`` ``None``.
    Ein Zahlenwert dort wäre erfunden: Über dem Horizont steht der Himmel, und wieviel
    davon das Bauwerk verdeckt, weiss diese Funktion nicht.
    """
    boden = bodenanteil(kamerahoehe_m=kamerahoehe_m, abstand_m=abstand_m,
                        brennweite_mm=brennweite_mm, sensor_hoehe_mm=sensor_hoehe_mm,
                        shift_mm=shift_mm, raumhoehe_m=raumhoehe_m)
    horizont = horizontanteil(shift_mm=shift_mm, sensor_hoehe_mm=sensor_hoehe_mm)

    if raumhoehe_m is None:
        return {
            "bodenanteil": boden,
            "deckenanteil": None,
            "wandanteil": None,
            "horizontanteil": horizont,
            "roh": {"boden": boden, "decke": None},
            "boden_kante_im_bild": False,
            "decken_kante_im_bild": False,
            "lage": "aussen",
        }

    decke = deckenanteil(kamerahoehe_m=kamerahoehe_m, raumhoehe_m=raumhoehe_m,
                         abstand_m=abstand_m, brennweite_mm=brennweite_mm,
                         sensor_hoehe_mm=sensor_hoehe_mm, shift_mm=shift_mm)
    s = float(sensor_hoehe_mm)
    v = float(shift_mm)
    f = float(brennweite_mm)
    d = float(abstand_m)
    h = float(kamerahoehe_m)
    hr = float(raumhoehe_m)
    roh_boden = _roh_boden(h, d, f, s, v)
    roh_decke = _roh_decke(h, hr, d, f, s, v)
    return {
        "bodenanteil": boden,
        "deckenanteil": decke,
        "wandanteil": max(0.0, 1.0 - boden - decke),
        "horizontanteil": horizont,
        "roh": {"boden": roh_boden, "decke": roh_decke},
        "boden_kante_im_bild": roh_boden > 0.0,
        "decken_kante_im_bild": roh_decke > 0.0,
        "lage": "innen",
    }


# ======================================================================================
# 5 · Der Ansichtenkatalog nach HABS
# ======================================================================================

#: Die vier Ansichten, die HABS für ein Bauwerk verlangt — wörtlich.
#:
#: Das ist die härteste Fundstelle der ganzen Recherche für ein Kameraset: nicht erfunden,
#: sondern seit 1933 die Vorschrift des US-Bundesstandards für Baudokumentation. Die
#: **schräge** Ansicht ist dort der Regelfall (zweimal), die frontale die Ausnahme
#: (einmal).
HABS_ANSICHTEN = (
    ("umgebung",
     "General or environmental view(s) to illustrate setting, including landscaping, "
     "adjacent building(s), and roadways"),
    ("frontal",
     "Front façade, with and without a scale stick"),
    ("ueber_eck_vorn",
     "Perspective view, front and one side"),
    ("ueber_eck_hinten",
     "Perspective view, rear and opposing side"),
)


def _kuerzel_fuer(grundazimut: float, faktor: int) -> str:
    """Das Richtungskürzel aus ``kameras.RICHTUNGEN`` zu Grundazimut und Bias-Faktor."""
    for kuerzel in RICHTUNGSFOLGE:
        grund, f = RICHTUNGEN[kuerzel]
        if math.isclose(grund % 360.0, grundazimut % 360.0, abs_tol=1e-9) and f == faktor:
            return kuerzel
    raise KompositionError(
        f"Keine Richtung in kameras.RICHTUNGEN mit Grundazimut {grundazimut} und "
        f"Faktor {faktor}."
    )


def ansichtenkatalog(*, frontal: str = "s", seite: int = -1,
                     bias_grad: float = BIAS_GRAD) -> tuple:
    """Der HABS-Ansichtensatz, abgebildet auf die Richtungskürzel aus ``kameras``.

    Es gibt in diesem Projekt genau **eine** Richtungstabelle, und sie steht in
    ``kameras.RICHTUNGEN``. Diese Funktion erfindet keine zweite; sie sagt nur, welche
    ihrer Kürzel den vier HABS-Ansichten entsprechen.

    Die beiden Über-Eck-Ansichten liegen auf **gegenüberliegenden** Diagonalen: „front and
    one side" gegen „rear and opposing side". In der Tabelle heisst das gleicher
    Bias-Faktor, um 180° gedrehter Grundazimut — aus ``sSE`` (Süd- und Ostfassade) wird
    ``nNW`` (Nord- und Westfassade). Die Azimute unterscheiden sich dann für **jeden**
    Bias-Wert um exakt 180°; das prüft der Test nach, statt es zu glauben.

    Die **Umgebungsansicht** bekommt hier dieselbe Richtung wie die frontale, aber einen
    eigenen Ausschnitt. Das ist eine ehrliche Auskunft und keine Verlegenheit: HABS
    unterscheidet die beiden nicht über den Standort, sondern darüber, wieviel Umfeld im
    Bild ist. Eine Richtungstabelle kann das nicht beantworten.

    **Zum Stand des Projekts:** ``abholer.AUTO_RICHTUNGEN`` steht seit dem 23.08.2026 auf
    ``("s", "sSE", "nNW")`` — drei Richtungen; bis dahin war es eine einzige (``sSE``).
    Damit sind **beide** Über-Eck-Ansichten abgedeckt und eine der beiden Aufnahmen aus
    ``s``. Welche der beiden, ist aus der Richtung **nicht** zu sagen — sie unterscheiden
    sich im Ausschnitt. Das steht bei :func:`fehlende_ansichten`.

    Args:
        frontal: Kürzel einer der vier Frontalen (``"n"``, ``"e"``, ``"s"``, ``"w"``).
            ``"s"`` heisst: Kamera südlich, Blick auf die Südfassade.
        seite: ``-1`` oder ``+1`` — welche der beiden Diagonalen die vordere ist.
            ``-1`` bei ``frontal="s"`` ergibt ``sSE``, den heutigen Projektwert.
        bias_grad: wird an ``kameras.richtungen`` durchgereicht, um die Azimute
            mitzuliefern.

    Returns:
        Tuple aus vier dicts mit ``name``, ``habs`` (wörtliches Zitat), ``richtung``
        (Kürzel), ``azimut_grad`` und ``ausschnitt`` (``"weit"`` oder ``"normal"``).

    Raises:
        KompositionError: ``frontal`` ist keine der vier Frontalen, oder ``seite`` ist
            weder ``-1`` noch ``+1``.
    """
    if frontal not in RICHTUNGEN or RICHTUNGEN[frontal][1] != 0:
        raise KompositionError(
            f"frontal muss eine der vier Frontalen sein (n, e, s, w), war: {frontal!r}"
        )
    if seite not in (-1, 1):
        raise KompositionError(
            f"seite muss -1 oder +1 sein, war: {seite!r}. Beide Vorzeichen sind zulässig; "
            "sie wählen, welche Nebenfassade die vordere Über-Eck-Ansicht zeigt."
        )
    grund = RICHTUNGEN[frontal][0]
    vorn = _kuerzel_fuer(grund, seite)
    hinten = _kuerzel_fuer(grund + 180.0, seite)
    azimute = richtungen(bias_grad)

    zuordnung = {
        "umgebung": (frontal, "weit"),
        "frontal": (frontal, "normal"),
        "ueber_eck_vorn": (vorn, "normal"),
        "ueber_eck_hinten": (hinten, "normal"),
    }
    return tuple(
        {
            "name": name,
            "habs": zitat,
            "richtung": zuordnung[name][0],
            "azimut_grad": azimute[zuordnung[name][0]],
            "ausschnitt": zuordnung[name][1],
        }
        for name, zitat in HABS_ANSICHTEN
    )


def fehlende_ansichten(kuerzel, *, ausschnitte=None, **kwargs) -> dict:
    """Welche HABS-Ansichten ein gegebener Richtungssatz **nicht** abdeckt.

    Das ist keine Forderung, zwölf Kameras zu rendern. Wieviele Standpunkte ein Auftrag
    wert ist, ist eine Betriebsentscheidung. Es ist die Auskunft, **was dabei wegfällt**.

    Args:
        kuerzel: Die Richtungskürzel, die wirklich gerendert werden.
        ausschnitte: ``{kuerzel: "weit" | "normal"}``, soweit **bekannt**. Ohne diese
            Angabe bleibt bei jeder Richtung, auf der **mehr als eine** HABS-Ansicht
            liegt, offen, welche davon getroffen wurde.

    ``kwargs`` gehen an :func:`ansichtenkatalog` (``frontal``, ``seite``, ``bias_grad``).

    Returns:
        ``{fehlend, nicht_feststellbar, abgedeckt, grund}`` — Namen in der Reihenfolge
        von :data:`HABS_ANSICHTEN`.

    .. important::
       **Bis zum 26.08.2026 gab diese Funktion eine blosse Namensliste zurück, und die
       war zu optimistisch.** ``fehlende_ansichten(("s", "sSE", "nNW"))`` ergab ``()`` —
       «nichts fehlt». Das stimmt nicht: *Umgebungsansicht* und *Frontalansicht* liegen
       **beide** auf ``s`` und unterscheiden sich allein im **Ausschnitt**. Eine einzige
       Aufnahme aus ``s`` deckt genau eine von beiden ab, und aus der Richtung ist nicht
       zu sagen, welche.

       Ein Test hiess sogar ``test_der_volle_habs_satz_laesst_nichts_fehlen`` und hat die
       Fehlaussage festgeschrieben. Die dritte Antwort dieses Projekts gilt auch hier:
       *nicht feststellbar* ist weder abgedeckt noch fehlend.
    """
    katalog = ansichtenkatalog(**kwargs)
    vorhanden = set(kuerzel)
    bekannt = dict(ausschnitte or {})

    # Wie viele HABS-Ansichten liegen auf derselben Richtung? Nur dort ist der Ausschnitt
    # ueberhaupt die unterscheidende Groesse.
    je_richtung: dict[str, int] = {}
    for a in katalog:
        je_richtung[a["richtung"]] = je_richtung.get(a["richtung"], 0) + 1

    fehlend, offen, abgedeckt = [], [], []
    for a in katalog:
        if a["richtung"] not in vorhanden:
            fehlend.append(a["name"])
            continue
        gesehen = bekannt.get(a["richtung"])
        if gesehen is not None:
            (abgedeckt if gesehen == a["ausschnitt"] else fehlend).append(a["name"])
        elif je_richtung[a["richtung"]] > 1:
            offen.append(a["name"])
        else:
            abgedeckt.append(a["name"])

    teile = []
    if fehlend:
        teile.append(f"FEHLT: {', '.join(fehlend)} — keine Kamera in dieser Richtung")
    if offen:
        teile.append(
            f"NICHT FESTSTELLBAR: {', '.join(offen)} liegen auf derselben Richtung und "
            f"unterscheiden sich nur im Ausschnitt. Ohne die Angabe, wie weit gerahmt "
            f"wurde, ist nicht zu sagen, welche davon die Aufnahme zeigt — und 'beide' "
            f"waere die falsche Antwort")
    if not teile:
        teile.append("Alle vier HABS-Ansichten sind abgedeckt.")
    return {"fehlend": tuple(fehlend), "nicht_feststellbar": tuple(offen),
            "abgedeckt": tuple(abgedeckt), "grund": " | ".join(teile)}


# ======================================================================================
# 6 · Eine Aufnahme, in einem Zug beurteilt
# ======================================================================================

def aufnahme(*, kamerahoehe_m: float, bezugspunkt: str, gebaeudehoehe_m: float,
             abstand_m: float,
             brennweite_mm: float = ARBEITSBRENNWEITE_AUSSEN_MM,
             sensor_hoehe_mm: float = SENSOR_HOEHE_HOCH_MM,
             shift_mm: float = 0.0,
             neigung_grad: float = NEIGUNG_WAAGRECHT_GRAD) -> dict:
    """Eine Aussenaufnahme, vollständig durchgerechnet und mit ihren Warnungen.

    Das ist der Zusammenbau: Höhe mit Bezugspunkt, Neigung, Konvergenz, Bodenanteil,
    Mindestabstand und Horizontlage in einem dict. ``neigung_grad`` steht auf 0, weil das
    die Regel ist; wer davon abweicht, bekommt es in ``warnungen`` zurückgemeldet — die
    Abweichung ist ein **Wunsch**, kein Zustand, und ein Programm kann sie nicht aus der
    Geometrie ableiten.

    Returns:
        dict mit ``kamerahoehe`` (dem vollständigen Eintrag aus :func:`kamerahoehe`),
        ``neigung_grad``, ``rollwinkel_grad``, ``konvergenz``, ``bodenanteil``,
        ``horizont_am_baukoerper``, ``mindestabstand``, ``abstand_m``,
        ``abstand_genuegt`` und ``warnungen``.
    """
    hoehe = kamerahoehe(kamerahoehe_m, bezugspunkt=bezugspunkt)
    neigung = _zahl(neigung_grad, "neigung_grad")
    konv = konvergenz(neigung_grad=neigung, gebaeudehoehe_m=gebaeudehoehe_m,
                      kamerahoehe_m=kamerahoehe_m, abstand_m=abstand_m)
    noetig = mindestabstand(gebaeudehoehe_m=gebaeudehoehe_m, kamerahoehe_m=kamerahoehe_m,
                            brennweite_mm=brennweite_mm, sensor_hoehe_mm=sensor_hoehe_mm,
                            shift_mm=shift_mm)
    boden = bodenanteil(kamerahoehe_m=kamerahoehe_m, brennweite_mm=brennweite_mm,
                        sensor_hoehe_mm=sensor_hoehe_mm, shift_mm=shift_mm)

    warnungen = list(hoehe["warnungen"])
    if neigung != NEIGUNG_WAAGRECHT_GRAD:
        warnungen.append(
            f"Neigung {neigung:g}° statt 0°. Die einzige institutionell verbindliche "
            "Regel des Fachs (HABS/NPS) verlangt die lotrechte Sensorebene; die "
            f"Vertikalen laufen hier um {konv * 100:.1f} % aufeinander zu. Das ist "
            "zulässig als Absicht, nicht als Voreinstellung."
        )
    genuegt = float(abstand_m) >= noetig["abstand_m"]
    if not genuegt:
        warnungen.append(
            f"Abstand {float(abstand_m):.2f} m unterschreitet den Mindestabstand "
            f"{noetig['abstand_m']:.2f} m; bindend ist der {noetig['bindend']}. "
            "Das Bauwerk passt nicht vollständig ins Bild."
        )
    return {
        "kamerahoehe": hoehe,
        "neigung_grad": neigung,
        "rollwinkel_grad": ROLLWINKEL_WAAGRECHT_GRAD,
        "konvergenz": konv,
        "bodenanteil": boden,
        "horizont_am_baukoerper": horizont_am_baukoerper(
            kamerahoehe_m=kamerahoehe_m, gebaeudehoehe_m=gebaeudehoehe_m),
        "mindestabstand": noetig,
        "abstand_m": float(abstand_m),
        "abstand_genuegt": bool(genuegt),
        "warnungen": warnungen,
    }


# --------------------------------------------------------------------------------------
# Die Brücke zu den wirklichen Kameras
# --------------------------------------------------------------------------------------

def beurteile_kamera(kamera: dict, *, gebaeudehoehe_m: float, gelaende_z: float,
                     bezugspunkt: str) -> dict:
    """Eine Kamera aus :func:`aiimaging.kameras.kamerasatz` gegen das Regelwissen halten.

    Args:
        kamera: Ein Eintrag aus ``kamerasatz(...)["kameras"]``.
        gebaeudehoehe_m: Höhe des Bauwerks **über dem Geländestand**, nicht die Höhe der
            Hüllbox. Bei einem Untergeschoss sind das zwei verschiedene Zahlen.
        gelaende_z: Der Geländestand im Weltsystem, aus ``kamerasatz(...)["gelaende_z"]``.
        bezugspunkt: Woher dieser Stand kommt, aus ``["gelaende_bezug"]``. **Pflicht** —
            :func:`kamerahoehe` verlangt ihn aus demselben Grund: Eine Kamerahöhe ohne
            Bezugspunkt ist keine Höhe.

    Returns:
        Die Antwort von :func:`aufnahme`, plus ``kuerzel``. Ihre ``warnungen`` sind die
        eigentliche Ausbeute: Sie sagen, was an dieser Kamera gegen die Norm steht.

    Die Sensorhöhe wird aus dem **Seitenverhältnis dieser Kamera** gerechnet und nicht
    aus :data:`SENSOR_HOEHE_HOCH_MM` übernommen. Der Vorgabewert dort ist die Hochlage
    (36 mm); wer ihn für ein quadratisches Bild stehen liesse, bekäme einen zu grossen
    Bildwinkel und damit einen zu kleinen Mindestabstand — eine Prüfung, die zu milde
    urteilt, ist schlimmer als keine.
    """
    from .kameras import SENSOR_BREITE_MM

    seitenverhaeltnis = float(kamera.get("seitenverhaeltnis") or 1.0)
    return dict(
        aufnahme(
            kamerahoehe_m=float(kamera["auge"][2]) - float(gelaende_z),
            bezugspunkt=bezugspunkt,
            gebaeudehoehe_m=float(gebaeudehoehe_m),
            abstand_m=float(kamera["abstand_m"]),
            brennweite_mm=float(kamera["brennweite_mm"]),
            sensor_hoehe_mm=SENSOR_BREITE_MM / seitenverhaeltnis,
            shift_mm=float(kamera.get("shift_mm") or 0.0),
            neigung_grad=float(kamera.get("neigung_grad") or 0.0),
        ),
        kuerzel=kamera.get("kuerzel"),
    )


def beurteile_kamerasatz(satz: dict) -> dict:
    """Den ganzen Kamerasatz gegen das Regelwissen halten — und zusammenfassen.

    **Warum es diese Funktion gibt.** Dieses Modul war bis zum 23.08.2026 von *nichts*
    aufgerufen ausser seinen eigenen Tests: 1400 Zeilen gerechnetes Fachwissen, das kein
    Lauf je zu sehen bekam. Das ist die tote Kante dieses Projekts in ihrer bisher
    grössten Ausführung — und sie fällt nicht auf, weil ein ungenutztes Modul grün ist
    wie jedes andere. Ein Regelwerk, das nur seine Tests beurteilt, beurteilt nichts.

    Args:
        satz: die vollständige Antwort von :func:`aiimaging.kameras.kamerasatz`.

    Returns:
        ``{kameras, n_mit_warnung, warnungen, gebaeudehoehe_m, bezugspunkt,
        alle_waagrecht}``.

        ``alle_waagrecht`` ist die eine Zahl, auf die es normativ ankommt: ob **jede**
        Kamera dieses Satzes die lotrechte Sensorebene einhält (HABS/NPS). Sie steht
        getrennt, weil sie in den vielen Warnungen sonst untergeht.
    """
    kameras = satz.get("kameras") or []
    gelaende_z = float(satz.get("gelaende_z") or 0.0)
    bezugspunkt = satz.get("gelaende_bezug") or "huellbox_unterkante"
    mitte_z = float(satz["mitte"][2])
    hoehe_bbox = float(satz["masse_m"][2])
    # Höhe ÜBER GELÄNDE, nicht Höhe der Hüllbox. Liegt der Geländestand unter der
    # Hüllbox-Unterkante (Untergeschoss), ist das Bauwerk über Gelände niedriger.
    gebaeudehoehe = (mitte_z + hoehe_bbox / 2.0) - gelaende_z

    urteile = [beurteile_kamera(k, gebaeudehoehe_m=gebaeudehoehe,
                                gelaende_z=gelaende_z, bezugspunkt=bezugspunkt)
               for k in kameras]
    warnungen = [f"{u['kuerzel']}: {w}" for u in urteile for w in u["warnungen"]]

    return {
        "kameras": urteile,
        "n_mit_warnung": sum(1 for u in urteile if u["warnungen"]),
        "warnungen": tuple(warnungen),
        "gebaeudehoehe_m": gebaeudehoehe,
        "bezugspunkt": bezugspunkt,
        "alle_waagrecht": bool(urteile) and all(
            u["neigung_grad"] == NEIGUNG_WAAGRECHT_GRAD for u in urteile),
    }


#: Die Felder, die ein Kamerabericht des Runners tragen muss, damit er beurteilbar ist.
#:
#: Sie stehen hier als Liste und nicht als ``try/except``, weil das Fehlen eines Feldes
#: keine Ausnahme ist, sondern eine **Auskunft**: Der Rückfallweg des Runners (Kamera
#: diagonal von vorn-oben, ohne Rechnung) liefert sie gar nicht — und dann gibt es nichts
#: zu beurteilen, wohl aber etwas zu melden.
BERICHTSFELDER = ("auge", "abstand_m", "brennweite_mm", "gelaende_z",
                  "gelaende_bezug", "gebaeudehoehe_m")


def beurteile_bericht(kamera_bericht: dict) -> dict:
    """Den Kamerablock eines Multipass-Berichts beurteilen — oder sagen, warum nicht.

    Das ist die Fassung für den **Produktivweg**: Der Kamerasatz wird in Blender
    gerechnet, nicht hier; was zurückkommt, ist der ``kamera``-Block des Berichts. Die
    Beurteilung läuft trotzdem diesseits der Prozessgrenze — sie ist reine Arithmetik,
    und im Runner wäre sie eine Fähigkeit, die ohne Blender niemand hätte (Regel 4).

    Returns:
        ``{beurteilt, grund, ...}``. Bei ``beurteilt=False`` steht in ``grund``, was
        fehlt; die Felder von :func:`aufnahme` fehlen dann. **Kein Rückfall auf
        Ersatzwerte** — eine Beurteilung aus geratenen Zahlen sähe aus wie eine Prüfung
        und wäre keine.
    """
    if not isinstance(kamera_bericht, dict):
        return {"beurteilt": False,
                "grund": f"Kein Kamerablock: {type(kamera_bericht).__name__}."}

    fehlt = [f for f in BERICHTSFELDER if kamera_bericht.get(f) is None]
    if fehlt:
        return {"beurteilt": False, "grund": (
            f"Der Kamerablock trägt {', '.join(fehlt)} nicht — er stammt vermutlich vom "
            f"Rückfallweg des Runners ('weg': {kamera_bericht.get('weg')!r}), der die "
            f"Kamera ohne Rechnung setzt. Ohne diese Zahlen ist nichts zu beurteilen. "
            f"Geraten wird nicht.")}

    urteil = beurteile_kamera(
        kamera_bericht,
        gebaeudehoehe_m=float(kamera_bericht["gebaeudehoehe_m"]),
        gelaende_z=float(kamera_bericht["gelaende_z"]),
        bezugspunkt=str(kamera_bericht["gelaende_bezug"]),
    )
    return dict(urteil, beurteilt=True, grund="")
