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

**Warum der Betrag — und warum er ab dem 21.08.2026 nur noch die Notlösung ist.** Manche
Verfahren liefern Disparität (invertierte Tiefe): nah = gross. Dann ist die Reihenfolge
exakt umgekehrt und die Korrelation −1, obwohl die Geometrie perfekt stimmt. Gewertet
wurde darum ``abs(spearman)``.

**Diese Entscheidung ist am 20.08.2026 gemessen worden, und sie kostet mehr als gedacht**
(`auf-20260820-23`, 24 Blender-Läufe, `docs/EMPFINDLICHKEIT_2026-08-20.md`). Der bekannte
Preis war: Eine echte Vorne-Hinten-Vertauschung ist von einer Vorzeichenkonvention nicht
zu unterscheiden. Der unbekannte Preis ist grösser:

    Versatz 2 m → Score 0.1191   (ρ = −0.073)
    Versatz 4 m → Score 0.2301   (ρ = +0.337)

**Mehr Fehler, besserer Score.** ``abs()`` faltet die Skala in der Mitte: Der schlechteste
Wert liegt bei ρ = 0, mitten im Fehlerbereich, und beide Enden sind gleich gut. Eine
Grösse mit einem Minimum in der Mitte kann nicht monoton im Fehler sein — und was nicht
monoton ist, misst keinen Abstand. Nebenbei war das ein **Loch im Tor**: Eine vollständig
invertierte Tiefenkarte erreichte 1.0, also denselben Wert wie eine perfekte.

Der Ausweg steht in ``polaritaet``: Die Umkehrung gehört zum **Schätzer**, nicht zum Bild.
Wer sie einmal an Läufen bekannt guter Geometrie bestimmt (:func:`polaritaet_aus_messungen`),
darf danach das vorzeichenbehaftete ρ werten; dann liegt der schlechteste Wert am Ende der
Skala, und die invertierte Karte fällt auf 0. Ohne gemessene Polarität bleibt es beim
Betrag — **und das Ergebnis sagt dann in ``warnungen``, dass sein Score nicht monoton ist**.

Was das **nicht** löst, damit es niemand für mehr hält, als es ist: Die Metrik bleibt
stumpf. In der Szene mit 59.8 % Geometrieanteil liegt auch ein um vier Meter versetztes
Gebäude noch weit über dem Rauschanker, und dort ist ρ durchweg negativ — die Richtung
ändert an diesen Zahlen nichts. Nachgerechnet in ``docs/POLARITAET_2026-08-21.md``.

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

Der Maskenweg (21.08.2026) — ein zweiter Weg, kein Ersatz
---------------------------------------------------------
Der Score oben rechnet über das **ganze Bild**. Am 21.08.2026 ist gemessen worden, was
das in einer bodenlastigen Szene bedeutet (`auf-20260821-24`,
``docs/MASKE_2026-08-21.md``): Es werden im Wesentlichen zwei **Bodenrampen**
gegeneinander gehalten. Weisses Rauschen erreichte auf der Szene mit 59.8 % Bodenanteil
den Score 0.7217 — der Rauschanker jener Szene, gemessen in `auf-20260820-21/22` und
hier als ``NULLANKER['platte_endlich']`` hinterlegt —, und die Reihe war nicht monoton.

Rechnet man ρ **nur über die Punkte, an denen das Bauwerk steht** (dort 17.02 % des
Bildes), ist die Reihe in beiden gemessenen Szenen **streng monoton**, und die Kurven
zweier ganz verschiedener Szenen liegen mit höchstens 0.005 aufeinander — ohne jede
Normierung. Genau das sollte die frühere Normierung ``anteil_der_spanne`` leisten; sie
ist am 20.08.2026 widerlegt worden.

:func:`rho_ueber_maske` ist dieser Weg. Er ist **additiv**: ``geometrie_score`` bleibt
unverändert, weil alle bisher gemessenen Zahlen des Projekts mit ihm entstanden sind und
reproduzierbar bleiben müssen. Und er liefert bewusst **keinen Score und kein
``geom_iou``**:

* ``geom_iou`` **über der Maske** ist bedeutungslos — innerhalb der Maske trägt die
  Soll-Karte überall Geometrie, die Überdeckung ist dort konstruktionsbedingt 1.
* ``geom_iou`` **darf trotzdem nicht wegfallen**: Es war der Halluzinationsfänger. ρ
  fragt nur, ob die Tiefen *innerhalb* der Maske richtig gestaffelt sind — nicht, ob dort
  überhaupt ein Gebäude steht. Ob ρ über der Maske Halluzination fängt, ist als Auftrag
  ``auf-20260821-25`` unterwegs und **ungemessen**. Dieses Modul nimmt die Antwort nicht
  vorweg; darum steht der Maskenweg neben dem Score und nicht an seiner Stelle.

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

#: Wie weit das **Minimum** von N Ziehungen unter dem Mittel liegt, in Streuungen.
#:
#: Der Eintrag zu ``N`` steht an Position ``N-1``. ``N=1`` ist null (ein Wert ist sein
#: eigenes Minimum), ``N=3`` sind 0,845 Streuungen.
#:
#: **Wozu diese Tabelle da ist.** Das Urteil eines Auftrags ist das seiner **schwächsten**
#: Kamera — richtig so, denn ein Auftrag ist so gut wie sein schlechtestes Bild. Aber ein
#: Minimum fällt mit der Zahl der Ziehungen, ganz ohne dass sich an der Sache etwas
#: ändert. Als die automatischen Richtungen am 23.08.2026 von **einer auf drei** gingen,
#: wurde das Gate damit strenger — und niemand hatte das entschieden.
#:
#: **Die Grössenordnung:** 0,845 Streuungen. Die einzige Streuung, die dieses Projekt
#: gemessen hat, ist die über Startwerte (0,2269, siehe
#: ``varianten.GEMESSENE_SEED_STREUUNG``). Wäre die Streuung zwischen Kameras ähnlich
#: gross, kostete der Wechsel rund **0,19** — mehr als jeder Parametereffekt, den die
#: Kette je gezeigt hat (0,10-0,14).
#:
#: **Was daran ungemessen ist, und zwar ausdrücklich:** Die Streuung zwischen KAMERAS ist
#: nicht die zwischen Startwerten. Sie könnte grösser sein (verschiedene Blickrichtungen
#: zeigen verschieden viel Geometrie) oder kleiner. Die Zahl 0,19 ist darum eine
#: Grössenordnung und keine Vorhersage. Seit drei Kameras je Auftrag gefahren werden, ist
#: sie erstmals nebenbei messbar.
#:
#: Simuliert mit 600 000 Ziehungen je N; die Werte für N <= 5 stimmen mit der Tabelle der
#: Extremwertstatistik auf drei Stellen überein (0; 0,5642; 0,8463; 1,0294; 1,1630).
MINIMUM_ABSCHLAG = (0.0, 0.5626, 0.8453, 1.0286, 1.1627, 1.2679,
                    1.3523, 1.4244, 1.4856, 1.5391, 1.5861, 1.6295)


def minimum_abschlag(n):
    """Wie viele Streuungen unter dem Mittel das Minimum von ``n`` Werten liegt.

    ``None`` jenseits der Tabelle - extrapoliert wird nicht. Eine erfundene Zahl sähe
    hier genau wie eine gerechnete aus.
    """
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        return None
    return MINIMUM_ABSCHLAG[n - 1] if n <= len(MINIMUM_ABSCHLAG) else None

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

# --------------------------------------------------------------------------------------
# Polarität — die Antwort auf den Befund vom 20.08.2026
# --------------------------------------------------------------------------------------
#
# `auf-20260820-23` hat gemessen, was der Betrag kostet: **Der Score ist nicht monoton.**
# In Szene A gab ein Versatz von 2 m den Score 0.1191 und einer von 4 m den Score 0.2301
# — mehr Fehler, besserer Score. Die Ursache steht in derselben Zeile: ρ kippte von
# −0.073 auf +0.337, und gewertet wurde der Betrag.
#
# Der Grund ist geometrisch und nicht zufällig: `abs()` **faltet die Skala in der Mitte**.
# Der schlechteste Wert liegt dann bei ρ = 0, also mitten im Fehlerbereich, und beide
# Enden (+1 und −1) sind gleich gut. Eine Grösse mit einem Minimum in der Mitte kann
# nicht monoton in den Fehler sein — und was nicht monoton ist, misst keinen Abstand.
#
# Der Ausweg: Die Umkehrung ist eine Eigenschaft **des Schätzers**, nicht des Bildes. Ein
# Schätzer, der Disparität liefert, liefert sie bei jedem Bild. Wer sie **einmal**
# bestimmt, darf danach das vorzeichenbehaftete ρ werten — und dann liegt der schlechteste
# Wert am Ende der Skala, wo er hingehört, und eine echte Vorne-Hinten-Vertauschung fällt
# auf 0 statt auf „so gut wie perfekt".

#: Die Ist-Karte ordnet wie die Soll-Karte: grosser Wert = weit weg (metrische Tiefe).
POLARITAET_TIEFE = +1
#: Die Ist-Karte ordnet umgekehrt: grosser Wert = nah (Disparität, invertierte Tiefe).
POLARITAET_DISPARITAET = -1

#: Gemessene Polarität je Schätzer — gegen **unsere** Soll-Karte (Blender, Meter).
#:
#: `depth-anything-v2-small`: **Disparität**, an 24 Läufen auf zwei Szenen
#: (`auf-20260820-23`). Jeder Lauf mit kleinem geometrischem Fehler liefert ρ zwischen
#: −0.96 und −0.998; kein einziger liefert dort ein positives ρ. Das ist keine Annahme
#: aus der Modellkarte, sondern eine Messung an unserer eigenen Naht — und nur die zählt,
#: denn die Polarität ist eine Eigenschaft des **Paars** aus Schätzer und Soll-Konvention.
GEMESSENE_POLARITAET = {
    "depth-anything-v2-small": POLARITAET_DISPARITAET,
}

#: Um wie viele Zufallsstreuungen ``polaritaet * rho`` von null entfernt liegen muss, bevor
#: eine Richtung gemeldet wird: darunter «vorne und hinten sind vertauscht», darüber —
#: seit dem 23.09.2026 mit derselben Grenze — «erwartete Richtung». Dazwischen steht
#: «Richtung nicht bestimmbar» (:func:`_richtungshinweis`).
#:
#: **Der Befund vom 22.09.2026 (auf-20260922-137):** Die Meldung löste bis dahin schon bei
#: ``polaritaet * rho < 0`` aus, ganz ohne Mindestbetrag. Am Gerät gemessen: ρ = +0,037
#: über 848 Punkte bei Polarität −1 — und die Kette meldete «vertauscht». Die
#: Zufallsstreuung einer Rangkorrelation ohne jeden Zusammenhang liegt bei etwa
#: ``1/sqrt(n-1)``, dort also bei 0,034. +0,037 ist von null nicht zu unterscheiden; das
#: heisst «kein Zusammenhang», nicht «umgekehrt».
#:
#: **Warum 2 Streuungen:** Unter «kein Zusammenhang» liegt ρ in rund 2,3 % der Fälle
#: zufällig mehr als zwei Streuungen unter null (einseitig). Erst darunter ist eine
#: Umkehrung eine Feststellung und keine Rauschlesung. Die Grenze wächst mit kleinem
#: ``n`` — bei 848 Punkten liegt sie bei 0,069, bei 32 Punkten bei 0,36; unter fünf Punkten
#: übersteigt sie 1, und dann ist die Richtung gar nicht bestimmbar. Das ist gewollt.
#:
#: **Was diese Zahl NICHT tut:** Sie ändert kein Urteil. Der Score schneidet jeden Wert
#: unter null ohnehin auf 0 ab (``max(0, ·)``), nimmt jeden Wert darüber unverändert, ob
#: er die Grenze erreicht oder nicht, und ``gerichtet`` im Maskenweg bleibt unverändert.
#: Sie entscheidet allein, welcher Hinweis in ``warnungen`` steht.
RICHTUNG_MIN_STREUUNGEN = 2.0


def richtungsgrenze(n: int) -> float:
    """Ab welchem Betrag ein gerichtetes ρ über ``n`` Punkte eine Richtung trägt.

    ``RICHTUNG_MIN_STREUUNGEN / sqrt(n-1)`` — die Zufallsstreuung einer Rangkorrelation
    ohne Zusammenhang, mal die Zahl der verlangten Streuungen. Warum, steht bei
    :data:`RICHTUNG_MIN_STREUUNGEN` (Befund 22.09.2026).

    Unter zwei Punkten gibt es keine Rangkorrelation; dann ist die Grenze unendlich, und
    keine Richtung gilt als bestimmt.
    """
    if n < 2:
        return math.inf
    return RICHTUNG_MIN_STREUUNGEN / math.sqrt(n - 1)


# DIE GRENZE GILT IN BEIDE RICHTUNGEN — Befund 23.09.2026 (Runde 7).
#
# Runde 6 hat nur die NEGATIVE Seite an :func:`richtungsgrenze` gebunden. Die positive
# Seite blieb ohne Schwelle: Score-Weg und Maskenweg meldeten jedes ``rho < 0`` bei
# Polarität −1 als «den ERWARTETEN Fall» — auch ``rho = −0,01`` über 848 Punkte, wo die
# Grenze bei 0,069 liegt. Das war eine Richtung aus Rauschen, dieselbe Falle wie am
# 22.09.2026, nur mit dem angenehmeren Vorzeichen. Und bei Polarität +1 mit kleinem
# positivem ``rho`` schrieb keiner der Zweige etwas.
#
# Seither fällt die Antwort an EINER Stelle, die beide Wege rufen, und sie ist
# symmetrisch: Betrag unter der Grenze → «Richtung nicht bestimmbar»; darüber in der
# erwarteten Richtung → die Bestätigung; darüber in der falschen → «vertauscht». Die
# Wächter stehen in ``tests/test_runde7_richtung.py``: Polarität −1 über
# ``tiefenschaetzer.qa_gegen_soll`` (so ruft ihn der Homeworker), Polarität +1 — die der
# Produktschätzer nicht hat — über ``geometrie_gate`` und ``rho_ueber_maske`` direkt.
# (Hier stand bis zum 23.09.2026, alle Wächter führen über ``qa_gegen_soll``; das galt
# nur für −1.)
#
# WAS DAS NICHT TUT: Es ändert weder ``score`` noch ``bestanden`` noch ``gerichtet``. Es
# entscheidet allein, welcher Satz in ``warnungen`` steht. Der Wächter prüft die drei
# Werte über eine Reihe von rho gegen die ausgeschriebene Rechnung; die Probe alte gegen
# neue Fassung (23.09.2026, 1680 synthetische Fälle, beide Polaritäten und None) ergab
# keine einzige Abweichung darin. Geändert hat sich dabei eine Begründung: Wo kein Score
# entsteht, nennt ``geometrie_gate`` jetzt den Grund statt des Richtungssatzes (dort).

_RICHTUNG_ERWARTET = "erwartet"
_RICHTUNG_UNBESTIMMT = "unbestimmt"
_RICHTUNG_VERTAUSCHT = "vertauscht"


def _richtungsfall(gerichtet: float, n: int) -> str:
    """Welche der drei Antworten ``gerichtet = polaritaet * rho`` über ``n`` Punkte trägt.

    Die Grenze ist in beide Richtungen dieselbe (:func:`richtungsgrenze`). Unter zwei
    Punkten ist sie unendlich, und dann ist die Richtung nie bestimmt.
    """
    grenze = richtungsgrenze(n)
    if gerichtet <= -grenze:
        return _RICHTUNG_VERTAUSCHT
    if gerichtet >= grenze:
        return _RICHTUNG_ERWARTET
    return _RICHTUNG_UNBESTIMMT


#: Was die beiden Wege an der Meldung unterscheidet — Wortwahl und Nachsatz, nicht die
#: Regel. Der Score-Weg schneidet unter null ab, der Maskenweg nicht; das muss im Satz
#: stehen, weil es wahr ist, und nur das.
#:
#: Der Nachsatz ``"ohne_score"`` gilt im Score-Weg, wenn KEIN Score entsteht (gemeinsame
#: Silhouette unter :data:`MIN_GEMEINSAME_PUNKTE`). Bis zum 23.09.2026 stand dort der
#: gewöhnliche Nachsatz, und der sagte «gerechnet wird wie immer mit max(0, polaritaet *
#: spearman)» bzw. «Der Score ist auf 0 abgeschnitten» — über einen Score, der ``None``
#: ist. Es wurde nicht gerechnet, und ``None`` ist nicht 0.
_RICHTUNG_WEGE = {
    "score": {
        "wort": "spearman", "stellen": 3, "punkte": "Punkte", "ort": "",
        _RICHTUNG_VERTAUSCHT: "Der Score ist auf 0 abgeschnitten.",
        _RICHTUNG_UNBESTIMMT: (
            "Am Score und am Urteil ändert dieser Hinweis nichts: gerechnet wird wie "
            "immer mit max(0, polaritaet * spearman)."),
        _RICHTUNG_ERWARTET: (
            "Das ist eine Feststellung über die Richtung, kein Urteil — ob das Bild "
            "besteht, entscheidet allein der Score."),
        "ohne_score": (
            "Ein Score ist hier NICHT gerechnet (None, nicht 0) — der Satz beschreibt "
            "nur, wie die vorhandenen Punkte die Tiefe ordnen, und trägt kein Urteil."),
    },
    "maske": {
        "wort": "rho", "stellen": 4, "punkte": "Maskenpunkte",
        "ort": " innerhalb der Maske",
        _RICHTUNG_VERTAUSCHT: (
            "Der gerichtete Wert ist NICHT bei 0 abgeschnitten: 'genau umgekehrt' ist "
            "etwas anderes als 'kein Zusammenhang'."),
        _RICHTUNG_UNBESTIMMT: "'gerichtet' bleibt, wie gemessen.",
        _RICHTUNG_ERWARTET: "'gerichtet' bleibt, wie gemessen.",
    },
}


def _richtungshinweis(rho: float | None, polaritaet: int | None, n: int, *,
                      weg: str, gewertet: bool = True) -> str | None:
    """Der eine Satz zur Richtung, den Score-Weg und Maskenweg gleichermassen melden.

    ``gewertet=False`` heisst: Im Score-Weg ist kein Score entstanden. Dann steht statt
    des Nachsatzes über die Rechnung der Satz ``"ohne_score"`` (23.09.2026).

    ``None`` heisst: Hier gibt es keine Richtung zu beurteilen — weil ``rho`` nicht
    gemessen ist oder die Polarität nicht übergeben wurde. Für den zweiten Fall haben
    beide Wege ihre eigene, ausführliche Warnung; eine Richtung ohne Polarität gibt es
    nicht.
    """
    if rho is None or polaritaet is None:
        return None
    w = _RICHTUNG_WEGE[weg]
    st = w["stellen"]
    gerichtet = polaritaet * rho
    grenze = richtungsgrenze(n)
    fall = _richtungsfall(gerichtet, n)
    kopf = (f"{w['wort']} = {rho:+.{st}f} bei Polarität {polaritaet:+d}, über {n} "
            f"{w['punkte']}; gewertet {polaritaet:+d} * {w['wort']} = {gerichtet:+.{st}f}")

    if fall == _RICHTUNG_VERTAUSCHT:
        text = (
            f"Rangkorrelation zeigt in die falsche Richtung ({kopf}): Die Ist-Karte "
            f"ordnet die Tiefe{w['ort']} umgekehrt, und zwar deutlicher, als der Zufall "
            f"es erklärt (Grenze {-grenze:+.{st}f}). Weil die Polarität GEMESSEN ist, "
            f"ist das kein Konventionsbefund mehr, sondern ein Geometriebefund — vorne "
            f"und hinten sind vertauscht."
        )
    elif fall == _RICHTUNG_ERWARTET:
        text = (
            f"Rangkorrelation zeigt in die erwartete Richtung ({kopf}): Die Ist-Karte "
            f"ordnet die Tiefe{w['ort']} wie die Soll-Karte, und zwar deutlicher, als der "
            f"Zufall es erklärt (Grenze {grenze:+.{st}f})."
        )
        if rho < 0.0:
            text += (
                f" Das negative Vorzeichen von {w['wort']} gehört zur gemessenen "
                f"Polarität: Dieser Schätzer liefert Disparität (nah = grosser Wert)."
            )
    else:
        streuung = grenze / RICHTUNG_MIN_STREUUNGEN
        text = (
            f"Kein messbarer Zusammenhang ({w['wort']} von null nicht zu "
            f"unterscheiden), die Richtung ist nicht bestimmbar: {kopf}. Die "
            f"Zufallsstreuung einer Rangkorrelation ohne jeden Zusammenhang liegt dort "
            f"bei 1/sqrt(n-1) = {streuung:.{st}f}; eine Richtung wird erst ab dem Betrag "
            f"{grenze:.{st}f} festgestellt, in der erwarteten wie in der umgekehrten. "
            f"Das ist kein Freispruch und kein Befund über die Richtung, sondern: eine "
            f"Ordnung der Tiefe{w['ort']} ist nicht nachweisbar."
        )
    nachsatz = w[fall] if gewertet or "ohne_score" not in w else w["ohne_score"]
    return f"{text} {nachsatz}"


#: Kurzform des Rechenwegs, wandert in jedes Ergebnis. Wer später eine Zahl in der Arbeit
#: wiederfindet, soll ihr ansehen, wie sie entstanden ist — und an welcher Fassung.
METHODE = "sqrt(abs(spearman) * geom_iou), Rangkorrelation über die gemeinsame Silhouette, v1"

#: Dieselbe Kurzform für den Fall, dass die Polarität bekannt ist. Sie steht als eigene
#: Zeichenkette da, weil die beiden Fassungen **verschiedene Zahlen** liefern: Wer später
#: einen Score in der Arbeit wiederfindet, muss ihm ansehen, welche Rechnung dahinterstand.
METHODE_GERICHTET = ("sqrt(max(0, polaritaet * spearman) * geom_iou), Rangkorrelation "
                     "über die gemeinsame Silhouette, v2 (gerichtet)")

#: Und dieselbe Kurzform für den **Maskenweg** (:func:`rho_ueber_maske`). Sie gehört
#: dazu, weil dort eine dritte, wieder andere Zahl entsteht: keine Wurzel, kein
#: ``geom_iou``, keine Silhouettenauswahl — nur ρ über die übergebenen Punkte. Ein Wert
#: ohne diese Angabe wäre später nicht mehr einzuordnen; drei Rechenwege im selben Modul
#: liefern drei verschiedene Zahlen zum selben Bild.
METHODE_MASKE = ("polaritaet * spearman über die ÜBERGEBENEN Maskenpunkte, ohne "
                 "geom_iou und ohne Wurzel — kein Score, v3 (Maskenweg)")

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

def _iou_ohne_boden(geom_iou: float | None, anteil_soll: float | None) -> float | None:
    """``geom_iou`` ohne den Anteil, den die Szene ohnehin schenkt.

        (geom_iou − anteil_soll) / (1 − anteil_soll)

    **0 heisst hier: so gut wie ein konstantes Bild. 1 heisst: deckungsgleich.** Damit
    bedeutet die Zahl über verschiedene Szenen dasselbe — was der rohe ``geom_iou`` nicht
    tut, weil sein Boden mit der Szene wandert.

    **Negative Werte werden nicht abgeschnitten.** Ein Bild, das schlechter trifft als ein
    konstantes, ist ein Befund und kein Fehler — gemessen: eine um 90° gedrehte Karte kam
    auf −0,3068. Bei 0 abzuschneiden hiesse, «schlechter als nichts» und «so gut wie
    nichts» zu einer Zahl zu machen; dieselbe Begründung wie beim gerichteten ρ.

    Returns:
        ``None``, wenn ``geom_iou`` fehlt **oder** die Soll-Silhouette das ganze Bild
        füllt. Im zweiten Fall ist der Nenner null: Eine Szene ohne Hintergrund hat keinen
        Boden, gegen den sich normieren liesse — *nicht beurteilbar*, und ausdrücklich
        nicht 1.
    """
    if geom_iou is None or anteil_soll is None or anteil_soll >= 1.0:
        return None
    return (geom_iou - anteil_soll) / (1.0 - anteil_soll)


def geometrie_score(soll: Sequence[float], ist: Sequence[float],
                    hintergrund: float | None = None, *,
                    polaritaet: int | None = None) -> dict:
    """Geometrie-Treue zweier indexgleicher Tiefenkarten.

    Args:
        soll: Tiefenkarte aus der echten Geometrie (Blender, Meter).
        ist: Tiefenkarte, aus dem erzeugten Bild zurückgerechnet. Massstab und Nullpunkt
            dürfen beliebig anders sein — genau dafür ist das Verfahren rangbasiert.
        hintergrund: Hintergrundmarke für **beide** Karten, siehe ``silhouette()``.
        polaritaet: :data:`POLARITAET_TIEFE` (+1) oder :data:`POLARITAET_DISPARITAET`
            (−1), wenn für den verwendeten Schätzer **gemessen** — siehe
            :data:`GEMESSENE_POLARITAET` und :func:`polaritaet_aus_messungen`.

            ``None`` heisst **ungemessen** und nicht „egal": Dann fällt die Rechnung auf
            ``abs(spearman)`` zurück, und das Ergebnis sagt in ``warnungen`` ausdrücklich,
            dass der Score in diesem Modus **nicht monoton** im geometrischen Fehler ist.
            Zwei verschiedene Fehler können denselben Score ergeben, und der grössere von
            beiden kann der bessere sein (`auf-20260820-23`, gemessen).

    Returns:
        ``{score, spearman, geom_iou, n_gemeinsam, n_soll, n_ist, methode, polaritaet,
        warnungen}``

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
    if polaritaet is not None and polaritaet not in (POLARITAET_TIEFE, POLARITAET_DISPARITAET):
        raise QaError(
            f"polaritaet muss {POLARITAET_TIEFE:+d} (Tiefe), {POLARITAET_DISPARITAET:+d} "
            f"(Disparität) oder None (ungemessen) sein, war {polaritaet!r}. Ein anderer "
            f"Wert würde den Score skalieren statt ihn zu richten — und eine Skalierung "
            f"ist genau das, wogegen ein rangbasiertes Verfahren gebaut ist."
        )
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
            "beide Karten Geometrie sehen. Ohne gemeinsame Punkte gibt es keine "
            "Tiefenordnung zu vergleichen; Score bleibt None, und das ist eine fehlende "
            "Messung und kein Nullwert. "
            "ZWEI LESARTEN, UND DIESE ZAHL TRENNT SIE NICHT: eine erfundene Kubatur im "
            "Bild — oder eine SOLL-KARTE, DER DIE FLAECHE FEHLT, die das Bild zeigt "
            "(Szene ohne Gelaende: der Schaetzer legt in den leeren Vordergrund eine "
            "Bodenebene, und die trifft auf nichts). "
            "Bis zum 02.09.2026 stand hier nur die erste Lesart, als 'Extremfall einer "
            "erfundenen Kubatur'. Gemessen wurde an dem Tag das Gegenteil: An drei "
            "Kameras einer gelaendelosen Szene ergaben das erzeugte Bild UND drei "
            "wertlose Nullproben (Grau, Rauschen, Verlauf) denselben geom_iou 0.0 und "
            "denselben geom_iou_norm auf die Stelle genau. Eine Zahl, die fuer weisses "
            "Rauschen dasselbe sagt wie fuer das Bild, sagt ueber das Bild nichts. "
            "Wer wissen will, welche Lesart zutrifft, sieht im Maskenbefund nach, ob "
            "die Szene ueberhaupt Gelaende traegt."
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
        if polaritaet is None:
            # Ungemessene Polarität: Betrag, wie bisher — und der Preis steht unten.
            score = math.sqrt(abs(rho) * geom_iou)
        else:
            # Gerichtet: negativ heisst jetzt wirklich falsch herum und nicht bloss
            # „andere Konvention". Abgeschnitten bei 0, weil es unter „vollständig
            # verkehrt" nichts Schlechteres gibt.
            score = math.sqrt(max(0.0, polaritaet * rho) * geom_iou)

    if polaritaet is None:
        warnungen.append(
            "KEINE POLARITÄT ÜBERGEBEN — gewertet wird abs(spearman). *Das heisst NICHT, "
            "dass sie ungemessen wäre:* Für die üblichen Schätzer steht sie in "
            "GEMESSENE_POLARITAET (depth-anything-v2-small an 24 Läufen auf zwei Szenen, "
            "auf-20260820-23), und `tiefenschaetzer.qa_gegen_soll` reicht sie seit dem "
            "26.08.2026 durch — unabhängig davon, ob der Maskenweg läuft. Läuft dieser "
            "Satz aus einem Kettenlauf auf, ist die Frage darum «welcher Schätzer war "
            "das, und warum steht er nicht in GEMESSENE_POLARITAET». Aus einer STUDIE "
            "(`schwellenstudie`) läuft er zu Recht auf: Dort sind Soll und Ist beide "
            "metrische Tiefe, und eine gemessene Schätzerpolarität gibt es gar nicht. "
            "(Dieser Satz ist am 26.08.2026 zweimal berichtigt worden: erst zeigte er "
            "auf «ungemessen», dann auf den Maskenweg — beide Male schickte er in die "
            "falsche Richtung.) In diesem "
            "Modus ist der Score NICHT MONOTON im geometrischen Fehler: abs() faltet die "
            "Skala in der Mitte, der schlechteste Wert liegt bei spearman = 0 und beide "
            "Enden sind gleich gut. Am 20.08.2026 gemessen (auf-20260820-23): 2 m Versatz "
            "gaben 0.1191, 4 m Versatz 0.2301 — mehr Fehler, besserer Score. Wer den "
            "Score als Abstand vom Richtigen liest, liest ihn hier falsch. Abhilfe: die "
            "Polarität einmal bestimmen (polaritaet_aus_messungen) und mitgeben."
        )
        if rho is not None and rho < 0.0:
            warnungen.append(
                f"Rangkorrelation ist negativ ({rho:+.3f}): Die Ist-Karte ordnet die "
                f"Tiefe genau umgekehrt. Üblichster Grund ist Disparität (nah = grosser "
                f"Wert); gewertet wird deshalb der Betrag. Falls die Ist-Karte metrische "
                f"Tiefe sein soll, ist das kein Konventions-, sondern ein Geometriebefund "
                f"— vorne und hinten sind vertauscht. Ohne gemessene Polarität kann die "
                f"Metrik diese beiden Fälle nicht trennen."
            )
    # «Vertauscht» erst DEUTLICH unter null — Befund 22.09.2026 (auf-20260922-137): ρ =
    # +0,037 über 848 Punkte bei Polarität −1 ergab bis dahin «vertauscht», obwohl es von
    # null nicht zu unterscheiden war. Und seit dem 23.09.2026 «bestätigt» ebenso erst
    # DEUTLICH über null: Bis dahin hiess hier jedes negative rho bei Polarität −1 «der
    # erwartete Fall», auch −0,01 über 848 Punkte. Die Regel steht in _richtungshinweis,
    # dieselbe wie im Maskenweg. Am Score ändert sie nichts.
    else:
        richtung = _richtungshinweis(rho, polaritaet, n_gemeinsam, weg="score",
                                     gewertet=score is not None)
        if richtung is not None:
            warnungen.append(richtung)

    anteil_soll = n_soll / len(s) if s else 0.0
    if 0 < n_soll < ANTEIL_GEMESSEN_NIEDRIG * len(s):
        warnungen.append(
            f"Geringer Geometrieanteil: nur {anteil_soll:.1%} der Bildpunkte tragen "
            f"Geometrie. Am 19.08.2026 gemessen (auf-20260819-15): Bei 17 % deckelt "
            f"'geom_iou' bei 0.256 — die Schwelle {SCHWELLE_GEOMETRIE} ist dann "
            f"ARITHMETISCH UNERREICHBAR, und ein durchgefallenes Bild belegt nichts über "
            f"seine Geometrietreue. Ab 60 % lag der Deckel bei 0.967. Der Grund: Ein "
            f"monokularer Schätzer legt in eine leere Fläche eine Bodenebene hinein "
            f"(auf-20260818-10), und je mehr leere Fläche, desto mehr erfundene Geometrie "
            f"in der Ist-Silhouette. Was zwischen 20 % und 60 % geschieht, ist ungemessen."
        )

    if n_soll == len(s) or n_ist == len(i):
        # Am 19.08.2026 an einer Szene mit Bodenebene bis zum Horizont gemessen
        # (`auf-20260819-15`): geom_iou war **exakt 1.0000**, weil n_soll gleich der
        # Bildpunktzahl war — 262 144 von 262 144. Es gab keinen Hintergrund mehr.
        #
        # Eine Silhouette, die das ganze Bild ist, überdeckt jede andere Silhouette, die
        # das ganze Bild ist. Der Wert 1.0 sieht dort nach perfekt getroffener Kontur aus
        # und misst in Wahrheit gar nichts — der Score ruht dann allein auf `spearman`.
        #
        # Das ist genau die Sorte Zahl, gegen die dieses Projekt antritt: eine, die gut
        # aussieht und leer ist. Sie wird darum gemeldet und **nicht** verworfen — welche
        # der beiden Karten randlos ist, weiss der Aufrufer besser als diese Funktion.
        welche = []
        if n_soll == len(s):
            welche.append(f"Soll ({n_soll} von {len(s)})")
        if n_ist == len(i):
            welche.append(f"Ist ({n_ist} von {len(i)})")
        warnungen.append(
            f"Randlose Silhouette: {' und '.join(welche)} umfasst ALLE Bildpunkte — es "
            f"gibt keinen Hintergrund. 'geom_iou' misst dann nichts mehr, denn eine "
            f"Silhouette, die das ganze Bild ist, überdeckt jede andere, die das ganze "
            f"Bild ist. Ein Wert nahe 1.0 ist hier KEIN Beleg für eine getroffene Kontur; "
            f"der Score ruht allein auf der Rangkorrelation. Gemessen an einer Szene mit "
            f"Bodenebene bis zum Horizont (auf-20260819-15): geom_iou exakt 1.0000."
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

    # DER BODEN VON `geom_iou` GEHOERT DER SZENE, NICHT DEM BILD — und seit dem
    # 27.08.2026 ist das keine Beobachtung mehr, sondern eine Rechenidentitaet:
    #
    #     Ein KONSTANTES Bild traegt nirgends die Hintergrundmarke.
    #     -> seine Silhouette ist das GANZE Bild
    #     -> geom_iou = |soll ∩ ist| / |soll ∪ ist| = |soll| / |Bild| = anteil_soll
    #
    # Auf drei Szenen auf volle Gleitkommagenauigkeit belegt: 0.1104, 0.1729, 0.5297.
    # Eine Szene, deren Geometrie die halbe Bildflaeche fuellt, gibt JEDEM wertlosen Bild
    # 0.53 — und 0.53 liest sich wie «zur Haelfte richtig».
    #
    # OWNER-ENTSCHEID 28.08.2026: Der Score bleibt unangetastet — 0.65 behaelt seine
    # Bedeutung und die Schwellenstudie vom 18.08. ihre Gueltigkeit. Der normierte Wert
    # steht DANEBEN.
    geom_iou_norm = _iou_ohne_boden(geom_iou, anteil_soll)
    return {
        "score": score,
        "spearman": rho,
        "geom_iou": geom_iou,
        # Derselbe Wert ohne den Anteil, den die Szene ohnehin schenkt. NICHT im Score.
        "geom_iou_norm": geom_iou_norm,
        "n_gemeinsam": n_gemeinsam,
        "n_soll": n_soll,
        "n_ist": n_ist,
        # Aus der Soll-Karte ABGELESEN, nicht aus der Szene geraten — und der beste
        # Vorhersager des Deckels, den wir haben.
        "anteil_soll": anteil_soll,
        # Welche Rechnung dahinterstand — die beiden Fassungen liefern verschiedene
        # Zahlen, und ein Score ohne diese Angabe wäre später nicht mehr einzuordnen.
        "methode": METHODE if polaritaet is None else METHODE_GERICHTET,
        "polaritaet": polaritaet,
        "warnungen": warnungen,
    }


#: Wie viele Läufe eine Polaritätsbestimmung mindestens braucht.
#:
#: Einer genügt nicht: Ein einzelner Lauf könnte ein echter Vorne-Hinten-Fehler sein, und
#: dann bestimmte man die Polarität aus genau dem Fehler, den man später fangen will.
MIN_POLARITAETSLAEUFE = 3

#: Ab welchem Betrag ein ρ als Richtungszeuge zählt. Ein ρ nahe 0 hat keine Richtung —
#: es aus Trotz einer Seite zuzuschlagen wäre geraten und nicht gemessen.
POLARITAET_MIN_BETRAG = 0.5


def polaritaet_aus_messungen(spearman_werte: Sequence[float]) -> dict:
    """Die Polarität eines Schätzers aus Läufen bekannt guter Geometrie bestimmen.

    **Das ist der Kern des Auswegs aus dem Befund vom 20.08.2026.** Die Umkehrung ist eine
    Eigenschaft des Schätzers und nicht des einzelnen Bildes; wer sie einmal bestimmt,
    darf danach das vorzeichenbehaftete ρ werten.

    Die Läufe müssen **bekannt gute Geometrie** zeigen — Blender-Renders derselben Szene,
    aus der die Soll-Karte stammt, oder etwas gleichwertig Sicheres. Aus einem Lauf, dessen
    Geometrie fraglich ist, liesse sich die Polarität nicht bestimmen, ohne genau den
    Fehler mitzubestimmen, den sie später aufdecken soll.

    Args:
        spearman_werte: die gemessenen ρ dieser Läufe, **mit Vorzeichen**.

    Returns:
        ``{polaritaet, gemessen, einig, n, n_gewertet, begruendung}``. ``polaritaet`` ist
        ``None``, solange die Sache nicht eindeutig ist — und ``None`` heisst hier wie
        überall in diesem Projekt *nicht gemessen* und nicht *egal*.
    """
    werte = [float(w) for w in (spearman_werte or []) if w is not None]
    deutlich = [w for w in werte if abs(w) >= POLARITAET_MIN_BETRAG]
    antwort = {"polaritaet": None, "gemessen": False, "einig": False,
               "n": len(werte), "n_gewertet": len(deutlich), "begruendung": ""}

    if len(deutlich) < MIN_POLARITAETSLAEUFE:
        antwort["begruendung"] = (
            f"Nur {len(deutlich)} von {len(werte)} Läufen zeigen eine deutliche Richtung "
            f"(|ρ| ≥ {POLARITAET_MIN_BETRAG}); nötig sind {MIN_POLARITAETSLAEUFE}. Ein "
            f"einzelner Lauf könnte selbst ein Vorne-Hinten-Fehler sein — dann bestimmte "
            f"man die Polarität aus genau dem Fehler, den man später fangen will."
        )
        return antwort

    negativ = sum(1 for w in deutlich if w < 0)
    positiv = len(deutlich) - negativ
    if negativ and positiv:
        antwort["begruendung"] = (
            f"Die Läufe sind sich nicht einig: {negativ} mit negativem, {positiv} mit "
            f"positivem ρ. Eine Polarität, die von Lauf zu Lauf kippt, ist keine "
            f"Eigenschaft des Schätzers — dann stimmt eine Annahme weiter oben nicht, "
            f"etwa dass alle diese Läufe wirklich gute Geometrie zeigen."
        )
        return antwort

    pol = POLARITAET_DISPARITAET if negativ else POLARITAET_TIEFE
    art = "Disparität (nah = grosser Wert)" if negativ else "metrische Tiefe"
    antwort.update(
        polaritaet=pol, gemessen=True, einig=True,
        begruendung=(f"{len(deutlich)} Läufe, alle mit demselben Vorzeichen: {art}. "
                     f"Gewertet wird künftig {pol:+d} * spearman."))
    return antwort


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
        # Der Richtungshinweis ist nie der Grund, warum kein Score da ist — er steht nur
        # zuletzt, weil er nach der Punktzählung geschrieben wird. Seit dem 23.09.2026
        # schreibt ihn jede gemessene Polarität (auch +1 mit kleinem rho, wo vorher nichts
        # stand); ohne diesen Filter hätte er bei zu kleiner gemeinsamer Silhouette die
        # eigentliche Begründung verdrängt, bei Polarität −1 tat er das schon vorher.
        richtung = _richtungshinweis(ergebnis["spearman"], ergebnis["polaritaet"],
                                     ergebnis["n_gemeinsam"], weg="score",
                                     gewertet=False)
        gruende = [w for w in ergebnis["warnungen"] if w != richtung]
        grund = gruende[-1] if gruende else "Grund unbekannt."
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


# ======================================================================================
# Der Maskenweg — ρ nur über die Punkte, an denen das Bauwerk steht
# ======================================================================================
#
# **Der Befund, aus dem dieser Weg entstanden ist** (`auf-20260821-24`, 21.08.2026,
# `docs/MASKE_2026-08-21.md`): Über das ganze Bild gerechnet misst die Metrik in einer
# bodenlastigen Szene im Wesentlichen **zwei Bodenrampen gegeneinander**. Ein monokularer
# Schätzer legt in jede strukturlose Fläche eine glatte Rampe von unten nach oben, und die
# Soll-Karte einer Bodenszene *ist* eine solche Rampe. Weisses Rauschen erreichte damit auf
# der Szene mit 59.8 % Bodenanteil den Score 0.7217 — das ist der Rauschanker jener Szene
# aus `auf-20260820-21/22`, hier als `NULLANKER['platte_endlich']` hinterlegt.
#
# ρ nur über die Bauwerkspunkte (dort 44 604 von 262 144 Punkten = 17.02 %):
#
#     Versatz      0 m      0.25     0.5      1 m      2 m      4 m     Rauschen
#     29   %    −0.9908  −0.9627  −0.9239  −0.8449  −0.7814  −0.7386   −0.5207
#     59.8 %    −0.9874  −0.9594  −0.9211  −0.8437  −0.7843  −0.7435   −0.5207
#
# **Streng monoton in beiden Szenen** — jeder Meter Versatz kostet, keiner bringt —, und
# die Kurven zweier ganz verschiedener Szenen liegen mit höchstens **0.005** aufeinander,
# **ohne jede Normierung**. Die Szenenabhängigkeit war nie eine Eigenschaft der Metrik,
# sie war der Boden. (Die Normierung `anteil_der_spanne`, die genau das leisten sollte,
# ist am 20.08.2026 widerlegt worden — siehe `einordnung`.)
#
# **Was hier NICHT gebaut wird, und warum jedes Mal:**
#
# 1. **Kein `geom_iou` über der Maske.** Es ist dort konstruktionsbedingt 1: Innerhalb der
#    Maske trägt die Soll-Karte überall Geometrie, es gibt keinen Hintergrund mehr, gegen
#    den sich eine Silhouette abheben könnte. Eine Überdeckungszahl über einer Menge, die
#    per Definition ganz Geometrie ist, misst nichts. Gemessen, nicht vermutet.
# 2. **Kein Weg über die Hintergrundschwelle.** Die Maske als Soll-Karte durch die übliche
#    Kette zu schicken bricht zusammen: Das *perfekte* Bild erreichte so **zwei** gemeinsame
#    Punkte, weil die Hintergrundstrategie die nächstgelegenen Punkte *irgendwo im Bild*
#    wählt — und die liegen auf dem Boden. Der Maskenweg wählt die Punkte darum **direkt**.
# 3. **Kein Score, und `geometrie_score` bleibt unangetastet.** `geom_iou` war der
#    Halluzinationsfänger; ρ fragt nur, ob die Tiefen *innerhalb* der Maske richtig
#    gestaffelt sind, nicht ob dort überhaupt ein Gebäude steht. Ob ρ über der Maske
#    Halluzination fängt, ist als `auf-20260821-25` unterwegs und **ungemessen**. Ein
#    Score aus ρ allein nähme diese Antwort vorweg — und wäre genau dann falsch, wenn sie
#    nein lautet.

#: Wie viele Punkte eine Maske mindestens tragen muss, damit ρ über ihr ausgegeben wird.
#:
#: **Ausdrücklich an :data:`MIN_GEMEINSAME_PUNKTE` gebunden und nicht daneben gesetzt**,
#: weil die Begründung dieselbe ist: 32 Punkte sind in einer 512×512-Karte 0.012 % des
#: Bildes, also ein paar Pixel entlang einer Kante. Dort dominieren Resampling- und
#: Kantenartefakte; ein ρ daraus wäre Rauschen mit Dezimalpunkt. Zwei Zahlen für dasselbe
#: Argument würden mit der Zeit auseinanderlaufen, und niemand wüsste, welche gilt.
#:
#: Auch hier absolut und nicht relativ zur Bildgrösse — eine relative Grenze wüchse mit
#: der Auflösung. Die gemessene Bauwerksmaske lag mit 44 604 Punkten weit darüber; wie
#: 0.65 ist auch diese Zahl bislang plausibel und nicht kalibriert.
MIN_MASKENPUNKTE = MIN_GEMEINSAME_PUNKTE

#: Das ρ, das **weisses Rauschen** über der Bauwerksmaske erreicht. **Gemessen**, nicht
#: gesetzt: `auf-20260821-24`, beide Szenen, auf vier Stellen derselbe Wert.
#:
#: **Es ist keine Null.** Ein Bild ohne jede Geometrie erreicht über der Maske ρ = −0.52,
#: nicht 0 — weil der Schätzer auch in Rauschen eine Rampe sieht und die Fassade in der
#: Soll-Karte ebenfalls von oben nach unten näher kommt. Wer ρ gegen 0 hält statt gegen
#: diesen Boden, hält es gegen die falsche Zahl.
#:
#: **Der Wert gehört zum PAAR aus Schätzer und Szenenart** (`depth-anything-v2-small`
#: gegen unsere Blender-Soll-Karte, bodenlastige Aussenszene, feste Kamera) — genau wie
#: die Polarität. Ein anderer Schätzer oder eine andere Szenenart hat einen anderen Boden,
#: und der ist dann **ungemessen**. Darum vergleicht dieses Modul nicht selbsttätig
#: dagegen: Welcher Boden gilt, weiss der Aufrufer und nicht diese Datei.
#:
#: .. danger::
#:    **Und diese Zahl ist gar keine Konstante — sie ist eine Zahl für EINE MASKENLAGE**
#:    (HomeStation, `auf-vis-20260824-10`, 24.08.2026). Der Schätzer hat ein **festes
#:    Ortsfeld**: Was `depth-anything-v2-small` auf einem leeren Bild ausgibt, ist zu
#:    **95,75 %** eine Funktion des **Ortes** — zirkelfrei gemessen, Feld aus 15
#:    Rauschbildern, geprüft an 15 anderen. Gestalt: eine Schüssel mit starkem
#:    Unterrand-Bonus (Mitte z −1,25, unterer Rand z +2,4).
#:
#:    **Dieselbe Rauschkarte, dieselbe Maske, nur verschoben:**
#:
#:        96 px hoch    ρ −0,6249
#:        Mitte         ρ +0,5207   ← genau der Betrag dieser Konstanten
#:        96 px runter  ρ +0,6387
#:        96 px rechts  ρ +0,6513
#:
#:    Ausschlag **1,28** auf einer Skala von −1 bis +1, **mit Vorzeichenwechsel**. Zwei
#:    Kontrollen schliessen aus, dass es am Mass liegt: Karte *und* Maske gemeinsam
#:    verschoben lässt beide Masse unverändert (das Mass ist ortsneutral), und das
#:    mittlere Feld allein sagt den Boden an allen 13 Lagen vorher (Korrelation 0,9993).
#:    **Der Rauschanker misst die Maskenlage.**
#:
#:    **Es trifft auch die ρ-Eichung vom 23.08.** — die HomeStation sagt es über ihre
#:    eigene Arbeit: In allen drei Szenen lag die Maske an *derselben Stelle*. Die schöne
#:    Übereinstimmung von 0,4 % zeigt nicht, dass ρ szenenfest ist, sondern dass ρ **bei
#:    gleicher Maskenlage** szenenfest ist. Über verschiedene Lagen schwankt der Abstand
#:    der Schwelle 0,80 zu diesem Boden zwischen **0,15 und 1,42**.
#:
#:    **Was daraus folgt:** Wer diese Zahl liest, liest eine Zahl für eine Lage. Der Boden
#:    gehört **je Lauf an der tatsächlichen Maskenlage gemessen** — die Nullprobe wird
#:    ohnehin gerendert, siehe :func:`einordnung` und `abholer._nullprobe`. Diese
#:    Konstante bleibt als **Bezugspunkt** stehen, für Protokolle und ältere Messungen.
#:
#: .. note::
#:    **Und der naheliegende Griff ist gemessen widerlegt: Das Feld HERAUSZURECHNEN macht
#:    es schlechter** (HomeStation, 24.08.2026, acht Bildlagen desselben Bauwerks bei
#:    gleichem Füllgrad, ein Startwert, eine Ansicht).
#:
#:    Zuerst die Bestätigung: Die Verunreinigung ist real und beziffert — **r = 0,9361**
#:    zwischen *«wie gut das Feld allein die Wahrheit trifft»* und *«wie gut das Mass
#:    aussieht»*. Dasselbe Bauwerk, nur anders im Bild platziert, wandert von 0,55 auf
#:    0,94.
#:
#:    Dann die Überraschung: **Alle drei Abzugsformen ERHÖHEN die Streuung** — von 0,1374
#:    ohne Abzug auf 0,2882 / 0,3090 / 0,4051 — und drehen bei 7, 6 bzw. 1 von 8 Lagen das
#:    **Vorzeichen** um. Das Feld legt sich also **nicht additiv** auf den Inhalt.
#:
#:    Die Gegenprobe zeigt, dass es nicht hoffnungslos ist: Eine Lage erreicht 0,9318 bei
#:    einem Feldbeitrag von 0,0240. **Die Bildlage entscheidet nicht, ob das Mass gut sein
#:    KANN, sondern ob die Zahl ehrlich ist.**
#:
#:    Darum bleibt der gemessene Boden ein **Anzeiger** und wird nicht abgezogen — siehe
#:    :func:`rho_gegen_gemessenen_boden`.
RAUSCHBODEN_UEBER_MASKE = -0.5207


def rho_ueber_maske(soll: Sequence[float], ist: Sequence[float],
                    maske: Sequence[bool], *, polaritaet: int | None = None) -> dict:
    """Rangkorrelation **nur über die übergebene Teilmenge** der Bildpunkte.

    Der zweite Weg neben :func:`geometrie_score`, nicht sein Ersatz. Warum es ihn gibt,
    was er bewusst **nicht** rechnet und woher die Zahlen stammen, steht im Abschnitt
    darüber und im Modul-Docstring.

    Args:
        soll: Tiefenkarte aus der echten Geometrie (Blender, Meter).
        ist: Tiefenkarte, aus dem erzeugten Bild zurückgerechnet. Massstab und Nullpunkt
            dürfen beliebig anders sein — dafür ist das Verfahren rangbasiert.
        maske: **Indexgleiche** Folge von Wahrheitswerten, ein Eintrag je Bildpunkt.
            ``True`` heisst: dieser Punkt wird gewertet. Woher die Maske stammt, ist
            dieser Funktion gleichgültig und bleibt es mit Absicht — sie kann aus einem
            Material-ID-Pass kommen, aus einer zweiten Aufnahme oder von Hand. Was sie
            auswählt, verantwortet, wer sie erzeugt.
        polaritaet: :data:`POLARITAET_TIEFE` (+1) oder :data:`POLARITAET_DISPARITAET`
            (−1), wenn für den verwendeten Schätzer **gemessen**. ``None`` heisst
            *ungemessen* und nicht *egal*: Dann bleibt ``gerichtet`` ``None``, und das
            Ergebnis sagt in ``warnungen``, dass ρ ohne Richtung **nicht monoton** im
            geometrischen Fehler ist — ``abs()`` faltet die Skala in der Mitte.

    Returns:
        ``{rho, gerichtet, n_maske, n_bild, anteil_maske, methode, polaritaet, warnungen}``

        * ``rho`` — Spearman über die Maskenpunkte, **mit Vorzeichen**, unverändert wie
          gemessen. ``None`` heisst *nicht gemessen* — nicht 0 und nicht 1.
        * ``gerichtet`` — ``polaritaet * rho`` in ``[−1, 1]``: ``+1`` perfekt geordnet,
          ``−1`` vollständig verkehrt herum. **Nicht** bei 0 abgeschnitten, weil hier
          kein Score entsteht, in den ein negativer Wert einginge; die Unterscheidung
          zwischen „kein Zusammenhang“ (0) und „genau umgekehrt“ (−1) ist ein Befund und
          gehört nicht weggeschnitten. ``None``, solange die Polarität ungemessen ist.
        * ``n_maske``/``n_bild`` — Punkte in der Maske und im Bild. ``anteil_maske`` ist
          ihr Verhältnis; die gemessene Bauwerksmaske lag bei 0.1702.
        * ``methode`` — :data:`METHODE_MASKE`. Drei Rechenwege im selben Modul liefern
          drei verschiedene Zahlen zum selben Bild; ohne diese Angabe wäre eine Zahl
          später nicht mehr einzuordnen.
        * ``warnungen`` — Klartextsätze. Leer heisst: nichts aufgefallen.

    Raises:
        QaError: ``maske`` fehlt (``None``), trägt keine Wahrheitswerte, oder ihre Länge
            passt nicht zu den Karten; ebenso ungleich lange oder leere Karten, oder eine
            erfundene Polarität.

    **Die drei Fälle, die nicht dasselbe sind**, und die dieses Modul auseinanderhält:

    1. **Maske fehlt** (``None``) — ein *Aufrufefehler*. Wer keine Maske hat, ruft diesen
       Weg nicht auf; ``None`` stillschweigend als „alle Punkte“ zu deuten wäre genau die
       Reparatur, gegen die dieses Modul gebaut ist, und ergäbe wieder den ganzen Boden.
    2. **Maske leer** (kein ``True``) — eine gefahrene Messung ohne Punkte, also **nicht
       gemessen**: ``rho`` bleibt ``None``. Weder 0 (Verurteilung ohne Grundlage) noch 1
       (Freispruch ohne Grundlage). ``None`` heisst in diesem Projekt durchgehend *kein
       Wert*, niemals *in Ordnung*.
    3. **Maske zu klein** (unter :data:`MIN_MASKENPUNKTE`) — ein **Befund** und kein
       Score: So wenige Punkte liegen an Kanten, wo Resampling und Schätzrauschen
       dominieren. ``rho`` bleibt ``None``, und die Warnung nennt die Zahl.

    **Was dieser Weg nicht tut.** Er prüft nicht nach, ob die Maske sinnvoll ist. Zeigt sie
    auf Punkte, an denen die Soll-Karte gar keine Geometrie trägt, dann gehen deren
    Hintergrundmarken als gewöhnliche Zahlen in die Rangfolge ein — eine Hintergrund*marke*
    ist eine endliche Zahl und von einer sehr grossen Tiefe hier nicht zu unterscheiden.
    Das ist Absicht: Eine Schwellenprüfung an dieser Stelle wäre wieder die
    Hintergrundstrategie, an der der Weg über die übliche Kette zerbrochen ist (zwei
    gemeinsame Punkte beim perfekten Bild). Die Maske entscheidet, und wer sie erzeugt,
    verantwortet sie.
    """
    if polaritaet is not None and polaritaet not in (POLARITAET_TIEFE, POLARITAET_DISPARITAET):
        raise QaError(
            f"polaritaet muss {POLARITAET_TIEFE:+d} (Tiefe), {POLARITAET_DISPARITAET:+d} "
            f"(Disparität) oder None (ungemessen) sein, war {polaritaet!r}. Ein anderer "
            f"Wert würde ρ skalieren statt es zu richten."
        )
    if maske is None:
        raise QaError(
            "maske fehlt (None). Eine fehlende Maske ist ein AUFRUFEFEHLER und keine "
            "leere Messung: Ohne Maske gibt es diesen Rechenweg nicht, und sie als "
            "'alle Punkte' zu deuten ergäbe wieder die Rechnung über das ganze Bild — "
            "also genau den Boden, dessentwegen dieser Weg existiert. Wer eine leere "
            "Auswahl übergeben will, übergibt eine Maske aus lauter False; das ist dann "
            "eine gefahrene Messung ohne Punkte und liefert rho=None mit Begründung."
        )

    s = _als_zahlen(soll, "soll")
    i = _als_zahlen(ist, "ist")
    m = _als_wahrheitswerte(maske, "maske")
    if len(s) != len(i):
        raise QaError(
            f"soll und ist sind unterschiedlich lang ({len(s)} vs. {len(i)}). Beide "
            f"Karten müssen denselben Bildausschnitt in derselben Punktreihenfolge "
            f"zeigen. Abschneiden wäre eine stillschweigende Reparatur mit falschem "
            f"Ergebnis."
        )
    if len(m) != len(s):
        raise QaError(
            f"maske und Karten sind unterschiedlich lang ({len(m)} vs. {len(s)}). Eine "
            f"Maske ist eine indexgleiche Folge zu Soll und Ist — ein Eintrag je "
            f"Bildpunkt. Wird sie abgeschnitten oder aufgefüllt, verschiebt sich die "
            f"Zuordnung aller Punkte danach, und gemessen würde eine andere Stelle des "
            f"Bildes als die gemeinte."
        )
    if not s:
        raise QaError("soll und ist sind leer — es gibt nichts zu vergleichen.")

    punkte = [k for k, an in enumerate(m) if an]
    n_maske = len(punkte)
    n_bild = len(s)
    warnungen: list[str] = []

    # NaN und inf müssen VOR spearman abgefangen werden, und zwar hier: spearman kennt
    # nur die Position innerhalb der Auswahl und meldete darum einen Index, den es im
    # Bild nicht gibt. Eine Fehlermeldung, die auf die falsche Stelle zeigt, kostet mehr
    # als keine.
    unbrauchbar = [k for k in punkte
                   if not (math.isfinite(s[k]) and math.isfinite(i[k]))]

    rho: float | None = None
    if n_maske == 0:
        warnungen.append(
            "Leere Maske: kein einziger Punkt ausgewählt. Das ist eine gefahrene Messung "
            "ohne Punkte, also NICHT GEMESSEN — rho bleibt None. Weder 0 noch 1 wäre "
            "hier eine Feststellung: Das eine verurteilte, das andere spräche frei, und "
            "belegt ist keines von beidem."
        )
    elif n_maske < MIN_MASKENPUNKTE:
        warnungen.append(
            f"Maske zu klein: {n_maske} Punkte, nötig sind {MIN_MASKENPUNKTE}. So wenige "
            f"Punkte liegen an Kanten, wo Resampling und Schätzrauschen dominieren; ein "
            f"rho daraus wäre Rauschen mit Dezimalpunkt. rho bleibt None — dass die Maske "
            f"so klein ist, ist für sich schon ein Befund: Entweder trifft sie das "
            f"Bauwerk nicht, oder das Bauwerk füllt im Bild kaum Fläche."
        )
    elif unbrauchbar:
        warnungen.append(
            f"{len(unbrauchbar)} von {n_maske} Maskenpunkten tragen NaN oder inf, der "
            f"erste an Bildindex {unbrauchbar[0]}. In einer Rangfolge haben sie keinen "
            f"Platz, und sie stillschweigend zu übergehen änderte die gemessene "
            f"Punktmenge — dann stünde ein rho da, das über etwas anderes gerechnet ist "
            f"als über die übergebene Maske. rho bleibt None; die Maske gehört auf die "
            f"Punkte gelegt, an denen beide Karten Werte haben."
        )
    else:
        try:
            rho = spearman([s[k] for k in punkte], [i[k] for k in punkte])
        except QaError as fehler:
            warnungen.append(f"Rangkorrelation nicht berechenbar: {fehler}")

    gerichtet = None if (rho is None or polaritaet is None) else polaritaet * rho

    if polaritaet is None:
        warnungen.append(
            "KEINE POLARITÄT ÜBERGEBEN — es gibt darum keinen gerichteten Wert. *Nicht "
            "zu verwechseln mit «ungemessen»:* Sie steht für die üblichen Schätzer in "
            "GEMESSENE_POLARITAET und wird im Maskenweg angewandt. "
            "Ohne Richtung bliebe nur abs(rho), und in diesem Modus ist die Grösse NICHT "
            "MONOTON im geometrischen Fehler: abs() faltet die Skala in der Mitte, der "
            "schlechteste Wert liegt bei rho = 0 und beide Enden sind gleich gut. Am "
            "20.08.2026 gemessen (auf-20260820-23): 2 m Versatz gaben 0.1191, 4 m Versatz "
            "0.2301 — mehr Fehler, besserer Score. Genau diese Monotonie ist der Grund, "
            "aus dem der Maskenweg gebaut wurde; ohne gemessene Polarität ist sie dahin. "
            "Abhilfe: die Polarität einmal bestimmen (polaritaet_aus_messungen) und "
            "mitgeben."
        )
    # Dieselbe Regel wie im Score-Weg, und zwar DIESELBE FUNKTION: Die Gerätemessung
    # des 22.09.2026 lief dort auf (auf-20260922-137: +0,037 über 848 gemeinsame
    # Punkte), die schwellenlose Bestätigung des 23.09.2026 in beiden Wegen. Zwei
    # Abschriften einer Regel waren genau das, was die positive Seite hat liegen lassen.
    # ``gerichtet`` bleibt unverändert; nur der Hinweis unterscheidet die drei Antworten.
    else:
        richtung = _richtungshinweis(rho, polaritaet, n_maske, weg="maske")
        if richtung is not None:
            warnungen.append(richtung)

    if n_maske == n_bild:
        # Eine Maske über das ganze Bild ist keine Maske, sondern der alte Weg unter neuem
        # Namen — und der ist am 21.08.2026 gerade daran gescheitert, dass er in einer
        # bodenlastigen Szene zwei Bodenrampen gegeneinander misst (weisses Rauschen: 0.72).
        warnungen.append(
            "Randlose Maske: ALLE Bildpunkte sind ausgewählt. Dann rechnet dieser Weg "
            "über dasselbe wie die Fassung über das ganze Bild, und der Sinn der Maske "
            "ist dahin: In einer bodenlastigen Szene misst er dann wieder im Wesentlichen "
            "zwei Bodenrampen gegeneinander — dort erreichte weisses Rauschen den Score "
            "0.7217 (Rauschanker der Szene mit 59.8 % Bodenanteil, NULLANKER"
            "['platte_endlich'], gemessen in auf-20260820-21/22). Eine Maske, die alles "
            "auswählt, wählt nichts aus."
        )

    return {
        "rho": rho,
        "gerichtet": gerichtet,
        "n_maske": n_maske,
        "n_bild": n_bild,
        "anteil_maske": n_maske / n_bild,
        "methode": METHODE_MASKE,
        "polaritaet": polaritaet,
        "warnungen": warnungen,
    }


# ======================================================================================
# Erreichbarkeit — die Frage VOR dem Rechnen
# ======================================================================================

#: Gemessene Obergrenzen von ``geom_iou`` je Szenenart und Hintergrundstrategie.
#:
#: **Warum diese Tabelle der wichtigste Teil dieses Moduls sein könnte.** Am 20.08.2026
#: fiel beim Zusammenrechnen der bisherigen Läufe etwas auf, das seit dem 18.08. in den
#: Zahlen stand und nie jemand ausgesprochen hatte:
#:
#:     Auf der Szene **ohne Boden** — der einzigen, auf der wir je gerendert haben — war
#:     die Schwelle 0.65 **arithmetisch unerreichbar.**
#:
#: Der Score ist ``sqrt(|spearman| * geom_iou)``. Bei einer Rangkorrelation von 1.0, dem
#: bestmöglichen Wert, braucht ``score >= 0.65`` ein ``geom_iou`` von mindestens
#: **0.4225**. Der gemessene Deckel jener Szene liegt bei 0.256 (``wie_soll``) bzw. 0.406
#: (``ohne_randberuehrung``). Selbst ein *perfektes* Bild kommt dort auf höchstens 0.634.
#:
#: Die Werte stammen aus `auf-20260818-12` und `auf-20260819-15`; sie messen den Deckel
#: an einem **gerenderten** Bild durch den Tiefenschätzer — also die beste Silhouette, die
#: diese Kette auf dieser Szene überhaupt hergibt.
IOU_DECKEL = {
    # 29,1 % Geometrieanteil, gemessen am perfekten Bild (`auf-20260820-22`).
    ("platte_11m", "wie_soll"): 0.1792,
    ("ohne_boden", "wie_soll"): 0.2556,
    ("ohne_boden", "ohne_randberuehrung"): 0.4057,
    ("platte_endlich", "wie_soll"): 0.9666,
    ("ebene_bis_rand", "wie_soll"): 0.9737,
    ("ebene_mit_horizont", "wie_soll"): 1.0000,
}

#: Bestes je gemessenes ``|spearman|`` an einem gerenderten Bild (`auf-20260819-15`).
#: Es ist nahe an 1.0 — die Tiefen*ordnung* war nie das Problem, die Silhouette schon.
SPEARMAN_BESTENFALLS = 0.998

#: Was `auf-20260819-15` über den Zusammenhang von **Geometrieanteil** und Deckel sagt.
#:
#: Der Geometrieanteil — wieviel Prozent der Bildpunkte überhaupt Geometrie tragen — lässt
#: sich aus der Soll-Karte **ablesen**, ohne die Szene zu kennen. Und er sagt fast alles:
#:
#: =================  ===============  ==================
#: Szene              Geometrieanteil  ``geom_iou``-Deckel
#: =================  ===============  ==================
#: ohne Boden         17,0 %           0,256
#: Platte, endlich    59,8 %           0,967
#: Ebene bis Rand     93,9 %           0,974
#: Ebene mit Horizont 100 %            1,000
#: =================  ===============  ==================
#:
#: **Der Grund ist bekannt:** Ein monokularer Schätzer legt in eine leere Fläche eine
#: Bodenebene hinein (`auf-20260818-10`). Je mehr leere Fläche, desto mehr erfundene
#: Geometrie in der Ist-Silhouette — und desto kleiner die Überdeckung.
#:
#: **Vier Punkte sind keine Kurve.** Was hier steht, ist die untere und die obere Marke,
#: nicht eine Formel dazwischen: Unterhalb von 20 % war der Deckel unerreichbar, ab 60 %
#: war er hoch. Was zwischen 20 % und 60 % geschieht, ist **ungemessen**.
ANTEIL_GEMESSEN_NIEDRIG = 0.20
ANTEIL_GEMESSEN_HOCH = 0.60


# ======================================================================================
# Die Tiefenkante an der Maskengrenze — die zweite Frage
# ======================================================================================
#
# ρ über der Maske fragt: **Stimmt die Tiefenstaffelung dort, wo das Bauwerk stehen
# müsste?** Es fragt nicht, ob dort überhaupt etwas steht. Gemessen (`auf-20260821-27`):
#
#     H1 · Bauwerk ganz weg    ρ −0.6861  — von ρ NICHT gefangen
#     H2 · 20 m versetzt       ρ −0.6854  — von ρ NICHT gefangen
#
# Beide liegen über dem Rauschboden (−0.5207) und sähen an ρ allein brauchbar aus. Und
# `geom_iou`, das diese Frage einmal beantworten sollte, **belohnt** die Abwesenheit:
# Das leere Grundstück erreichte 0.9848 gegen 0.9703 beim perfekten Bild
# (`auf-20260821-26`) — weil das Bauwerk die einzige Stelle war, an der Soll und Ist sich
# überhaupt unterscheiden konnten.
#
# Die Kante fragt die andere Hälfte: **Steht an der Silhouettengrenze ein Tiefensprung?**
# Ein Bauwerk erzeugt dort einen — vorne die Fassade, dahinter der ferne Hintergrund. Ein
# leeres Grundstück nicht, weil Boden und Himmel stetig ineinander übergehen.
#
#     perfekt +0.1615 | H1 +0.0006 | H2 +0.0007 | H3 +0.0066 | H4 +0.0021
#
# **H3 und H4 zeigen ebenfalls keine Kante, und das ist kein Mangel, sondern die
# Definition:** Die Maske ist die Silhouette des RICHTIGEN Bauwerks. Ein gedrehtes oder
# anders geformtes hat seine Kanten woanders; an dieser Grenze steht dann Grund, genau wie
# bei Abwesenheit. Die Kante fragt nicht „steht dort etwas", sondern „steht dort DAS
# RICHTIGE" — und genau die Fälle, die sie verfehlt, fängt ρ.
#
# > **Existenz und Richtigkeit sind zwei Fragen und brauchen zwei Messungen.**
#
# Das ist der Ertrag der ganzen Kette `auf-25` bis `auf-27`, und es ist zugleich die
# Diagnose für den Konstruktionsfehler von ``sqrt(|ρ| · geom_iou)``: Ein einzelner Score
# verschmolz zwei Fragen, die getrennt gehören.

#: Wie viele Randpunkte es mindestens braucht. **Deutlich weniger als Maskenpunkte** —
#: der Rand einer Fläche wächst mit ihrem Umfang und nicht mit ihrem Inhalt. Bei der
#: gemessenen Bauwerksmaske (44 604 Punkte) liegt der Rand in der Grössenordnung von
#: tausend. Die Zahl ist **gesetzt, nicht kalibriert**, und sie steht aus demselben Grund
#: da wie ``MIN_GEMEINSAME_PUNKTE``: Ein Median über eine Handvoll Punkte ist Rauschen
#: mit Dezimalpunkt.
MIN_RANDPUNKTE = 16

#: Kurzform des Rechenwegs. Vierter Weg im selben Modul — ohne diese Angabe wäre eine
#: Zahl später nicht mehr einzuordnen.
METHODE_KANTE = ("(Median innen − Median aussen) an der Maskengrenze, geteilt durch die "
                 "Spanne der ganzen Schätzkarte, gerichtet über die Polarität")


def kante_an_maskengrenze(ist: Sequence[float], maske: Sequence[bool], *,
                          breite: int, polaritaet: int | None = None) -> dict:
    """Steht an der Silhouettengrenze ein Tiefensprung?

    Args:
        ist: die **geschätzte** Tiefenkarte. Die Soll-Karte wird hier nicht gebraucht —
            sie steckt bereits in der Maske. Gefragt wird allein, ob das Bild an dieser
            Grenze eine Kante zeigt.
        maske: indexgleiche Wahrheitswerte, ``True`` = Bauwerk.
        breite: Bildbreite in Punkten. **Pflichtangabe**: Die Karten kommen flach herein,
            und ohne Breite gibt es keine Nachbarschaft und damit keinen Rand.
        polaritaet: :data:`POLARITAET_TIEFE` oder :data:`POLARITAET_DISPARITAET`, wenn
            gemessen. ``None`` heisst *ungemessen*; dann bleibt ``gerichtet`` ``None``.

    Returns:
        ``{roh, gerichtet, n_innen, n_aussen, spanne, methode, polaritaet, warnungen}``

        * ``roh`` — ``(Median innen − Median aussen) / Spanne(ist)``, ohne Richtung.
        * ``gerichtet`` — ``−polaritaet · roh``. **Positiv heisst: dort steht etwas.**

    **Warum das Vorzeichen so herum steht.** Das Bauwerk ist *näher* als das, was hinter
    seiner Silhouette liegt. Was „näher" für die Zahl heisst, hängt an der Polarität:

    * Disparität (−1, nah = gross): innen **grösser** → ``roh`` positiv
    * Tiefe (+1, nah = klein): innen **kleiner** → ``roh`` negativ

    In beiden Fällen soll ``gerichtet`` positiv sein, also ``gerichtet = −polaritaet · roh``.
    Gegenprobe an der Messung: Der Schätzer ist Disparität, das perfekte Bild lieferte
    **+0.1615 roh** — positiv, wie es sein muss.

    **Warum durch die Spanne geteilt wird.** Ohne das misst man die Skala des Schätzers
    statt der Kante: Ein Modell, das seine Ausgabe auf 0–1000 legt, bekäme das
    Tausendfache eines Modells mit 0–1, bei identischer Geometrie.

    Raises:
        QaError: ``breite`` passt nicht zur Länge, ``maske`` fehlt oder ist ungleich lang.

    **Nicht gemessen ist nicht null.** Zu wenige Randpunkte, eine Maske ohne Grenze (leer
    oder das ganze Bild) und eine Schätzkarte ohne Spanne liefern ``roh = None`` mit
    Begründung — nicht 0, was „keine Kante" hiesse und damit ein Urteil wäre.
    """
    werte = _als_zahlen(ist, "ist")
    if maske is None:
        raise QaError(
            "maske fehlt. Ohne Maske gibt es keine Grenze, an der sich eine Kante messen "
            "liesse — und 'alle Punkte' wäre keine Grenze, sondern das ganze Bild."
        )
    m = _als_wahrheitswerte(maske, "maske")
    if len(m) != len(werte):
        raise QaError(
            f"maske und ist sind unterschiedlich lang ({len(m)} vs. {len(werte)}). "
            f"Abschneiden wäre eine stillschweigende Reparatur mit falschem Ergebnis."
        )
    if isinstance(breite, bool) or not isinstance(breite, int) or breite <= 0:
        raise QaError(f"breite muss eine positive ganze Zahl sein, war {breite!r}.")
    if len(werte) % breite != 0:
        raise QaError(
            f"Die Karte hat {len(werte)} Punkte, das ist kein Vielfaches der Breite "
            f"{breite}. Eine der beiden Angaben stimmt nicht — geraten wird hier nicht."
        )

    hoehe = len(werte) // breite
    antwort = {"roh": None, "gerichtet": None, "n_innen": 0, "n_aussen": 0,
               "spanne": None, "methode": METHODE_KANTE, "polaritaet": polaritaet,
               "warnungen": []}

    innen, aussen = _randpunkte(m, breite, hoehe)
    antwort["n_innen"], antwort["n_aussen"] = len(innen), len(aussen)

    if not innen or not aussen:
        antwort["warnungen"].append(
            f"Die Maske hat keine Grenze: {len(innen)} Randpunkte innen, {len(aussen)} "
            f"aussen. Eine leere Maske und eine, die das ganze Bild füllt, haben beide "
            f"keinen Rand — und ohne Rand gibt es nichts zu messen. NICHT GEMESSEN, "
            f"weder 0 noch 1.")
        return antwort
    if len(innen) < MIN_RANDPUNKTE or len(aussen) < MIN_RANDPUNKTE:
        antwort["warnungen"].append(
            f"Zu wenige Randpunkte: {len(innen)} innen, {len(aussen)} aussen, nötig sind "
            f"je {MIN_RANDPUNKTE}. Ein Median über eine Handvoll Punkte ist Rauschen mit "
            f"Dezimalpunkt. NICHT GEMESSEN.")
        return antwort

    spanne = max(werte) - min(werte)
    antwort["spanne"] = spanne

    # EINE KARTE MIT HINTERGRUNDMARKE IST HIER DIE FALSCHE KARTE — und das Ergebnis sieht
    # trotzdem gut aus. Am 26.08.2026 nachgemessen, an derselben Szene:
    #
    #   Soll-Karte, Hintergrund als 1e10 :  roh = -1.0000, Spanne 1e10
    #   dieselbe Karte ohne Marke        :  roh = -0.7700, Spanne 11.66
    #
    # Der Grund: `roh` teilt den Mediansprung durch die Spanne der GANZEN Karte. Traegt
    # sie eine Marke, ist die Spanne die Marke, und der Sprung zwischen innen und aussen
    # ist selbst die Marke — das Mass saettigt bei genau ±1.0. Es meldet also eine
    # perfekte Kante und misst in Wahrheit den Abstand zwischen Bauwerk und Himmelsmarke.
    #
    # Der Aufrufer in `tiefenschaetzer._maskenweg` gibt darum ausdruecklich die ROHE
    # Schaetzkarte. Das stand bisher nur dort, und wer die Funktion sonst rief, konnte es
    # nicht wissen — gefunden beim Nachbauen der Halluzinationsfaelle, wo ich ihr selbst
    # die markierte Karte gegeben habe.
    if max(werte) >= HINTERGRUND_SCHWELLE_M:
        antwort["warnungen"].append(
            f"Diese Karte traegt eine HINTERGRUNDMARKE (groesster Wert "
            f"{max(werte):.3g} ≥ {HINTERGRUND_SCHWELLE_M:.3g}). Erwartet wird die ROHE "
            f"Schaetzkarte: Ein Schaetzer schreibt dort keinen Marker, sondern eine "
            f"gewoehnliche Zahl. Mit Marke ist die Spanne der Karte die Marke selbst, und "
            f"das Mass saettigt bei ±1.0 — es meldet dann eine perfekte Kante und misst "
            f"in Wahrheit den Abstand zwischen Bauwerk und Himmelsmarke. Der Wert steht "
            f"trotzdem da, weil das Verwerfen einer Zahl schlimmer waere als ihre "
            f"Erklaerung; brauchbar ist er nicht.")

    if spanne <= 0.0:
        antwort["warnungen"].append(
            "Die Schätzkarte hat keine Spanne — alle Punkte tragen denselben Wert. Ein "
            "massstabsfreies Mass liesse sich daraus nur durch Division durch null "
            "gewinnen. NICHT GEMESSEN. (Ein Bild ohne jede Tiefenstaffelung ist für sich "
            "schon ein Befund.)")
        return antwort

    roh = (_median([werte[i] for i in innen]) - _median([werte[i] for i in aussen])) / spanne
    antwort["roh"] = roh

    if polaritaet is None:
        antwort["warnungen"].append(
            "Polarität ungemessen — 'roh' steht da, 'gerichtet' nicht. Ohne Richtung ist "
            "nicht entscheidbar, ob ein positives Vorzeichen 'dort steht etwas' oder "
            "'dort ist ein Loch' bedeutet: Bei Disparität liegt das Bauwerk oben, bei "
            "metrischer Tiefe unten. Abhilfe: polaritaet_aus_messungen.")
        return antwort
    if polaritaet not in (POLARITAET_TIEFE, POLARITAET_DISPARITAET):
        raise QaError(
            f"polaritaet muss {POLARITAET_TIEFE:+d}, {POLARITAET_DISPARITAET:+d} oder "
            f"None sein, war {polaritaet!r}.")

    antwort["gerichtet"] = -polaritaet * roh
    return antwort


def _randpunkte(maske: list[bool], breite: int, hoehe: int) -> tuple[list[int], list[int]]:
    """Die Punkte beiderseits der Maskengrenze, als Indizes in die flache Karte.

    **Innen** ist ein Maskenpunkt mit mindestens einem 4-Nachbarn ausserhalb, **aussen**
    umgekehrt. Vier Nachbarn und nicht acht: Die Diagonalen machen den Rand dicker, ohne
    ihn schärfer zu machen, und ein dickerer Rand mischt Fassade und Hintergrund in
    beide Mediane.

    Der Bildrand zählt **nicht** als Maskengrenze. Berührt das Bauwerk die Bildkante, ist
    dort keine Silhouette, sondern ein Anschnitt — die Tiefe dahinter ist nicht im Bild,
    und ein Sprung liesse sich dort nicht messen, sondern nur erfinden.
    """
    innen: list[int] = []
    aussen: list[int] = []
    for y in range(hoehe):
        for x in range(breite):
            i = y * breite + x
            # Am Bildrand fehlt mindestens ein Nachbar — siehe Docstring.
            if x == 0 or y == 0 or x == breite - 1 or y == hoehe - 1:
                continue
            hier = maske[i]
            nachbarn = (maske[i - 1], maske[i + 1], maske[i - breite], maske[i + breite])
            if hier and not all(nachbarn):
                innen.append(i)
            elif not hier and any(nachbarn):
                aussen.append(i)
    return innen, aussen


def _median(werte: list[float]) -> float:
    """Median statt Mittelwert — ein einzelner Ausreisser am Rand darf nicht durchschlagen.

    Randpunkte liegen dort, wo Resampling und Schätzrauschen am stärksten sind; genau
    dort ist ein Mittelwert am wenigsten belastbar.
    """
    s = sorted(werte)
    n = len(s)
    mitte = n // 2
    return s[mitte] if n % 2 else (s[mitte - 1] + s[mitte]) / 2.0


#: Welcher Anteil der Bildpunkte als „trägt eine Kante" gilt.
#:
#: Die stärksten 5 % des Bildes. **Die Zahl hat eine Eigenschaft, die keine Schwelle
#: dieses Projekts bisher hatte: Sie erzeugt ihren eigenen Nullwert.** Wenn 5 % aller
#: Bildpunkte über der Schranke liegen, trägt eine Maskengrenze **ohne jeden Bezug zum
#: Bild** ebenfalls rund 5 %. Alles darüber ist Signal, alles darunter ist schlechter als
#: Zufall — und das ist gemessen vorgekommen (`auf-20260822-30`: 2.8 %).
KANTENANTEIL_STAERKSTE = 0.05

#: Um wieviel der **tatsächliche** Nullwert den verlangten übersteigen darf, bevor das
#: Mass als *nicht messbar* gilt.
#:
#: **Der Anlass ist eine fremde Eichung, die meinen eigenen Vorschlag erledigt hat**
#: (`docs/EICHUNG_2026-08-23.md`, HomeStation). Sie prüfte dieselbe Idee in zwei
#: Fassungen und zog sie zurück: In der relativen Fassung erreichen **grau und ein
#: Verlauf 100 %** — bei einem strukturlosen Bild ist der Gradient überall gleich, und
#: „über dem 95. Perzentil von lauter Gleichständen" ist für jeden Punkt wahr. Das Mass
#: belohnt dann Strukturlosigkeit, also genau die Krankheit von ``geom_iou``, gegen die
#: es antreten sollte.
#:
#: **Meine Fassung hatte denselben Defekt, nur halb verdeckt.** Nachgemessen an den drei
#: Nullankern: grau meldete 100 % gegen einen Nullwert von 100 % (und fiel damit richtig
#: durch), ein **Verlauf** aber 100 % gegen 93,9 % — und galt als „über Zufall".
#: Rechnerisch stimmt das und bedeutet nichts: Wo 94 % aller Bildpunkte als „stärkste
#: 5 %" gelten, sagt ein Anteil von 100 % an der Grenze nichts über den Umriss.
#:
#: Die Antwort ist nicht ein strengerer Vergleich, sondern die **richtige Kategorie**:
#: Trennt die Schranke nicht, ist das Mass auf diesem Bild **nicht anwendbar**. Es
#: liefert dann ``anteil = None`` statt einer Zahl mit Fussnote — dieselbe Regel wie
#: überall hier: *ungemessen* ist nicht *schlecht*, und eine Zahl mit Vorbehalt wird
#: ohne den Vorbehalt weitergereicht.
MAX_ZUFALL_FAKTOR = 2.0

#: Wie viele Streuungen der Anteil über dem Zufall liegen muss, um als Signal zu gelten.
#:
#: **Zwei** — dieselbe Zahl wie ``varianten.K_STREUUNGEN`` und ``stil_qa.K_STREUUNGEN``,
#: damit dieses Projekt nicht drei Begriffe von „deutlich mehr als Zufall" führt.
#:
#: Vorher stand hier ein striktes ``>``. Ein Anteil von 5,43 % gegen einen Nullwert von
#: 5,06 % galt damit als „über Zufall" — bei 92 Grenzpunkten ist das nichts. Die Streuung
#: einer Binomialverteilung ist ``sqrt(p·(1−p)/n)``, hier rund 2,3 Prozentpunkte; der
#: Vorsprung betrug 0,4. Ein strikter Vergleich auf einer verrauschten Grösse prüft nicht,
#: er würfelt.
#:
#: Die Folge ist sichtbar und erwünscht: **Weisses Rauschen gilt seither nicht mehr als
#: „über Zufall".** Es lag mit 6,9 % gegen 5,0 % knapp darüber und ist damit genau der
#: Fall, für den der Abstand gedacht ist.
K_STREUUNGEN_ANTEIL = 2.0

#: Kurzform des Rechenwegs. Fünfter Weg im selben Modul.
METHODE_KANTENANTEIL = ("Anteil der Maskengrenze, der eine Kante aus den stärksten 5 % "
                        "des Bildes trägt")


def anteil_grenze_mit_kante(ist: Sequence[float], maske: Sequence[bool], *,
                            breite: int,
                            staerkste: float = KANTENANTEIL_STAERKSTE) -> dict:
    """Wieviel vom Umriss das Bild **wirklich zeichnet**.

    **Warum es dieses zweite Mass gibt, obwohl es schon eines gibt.**
    :func:`kante_an_maskengrenze` bildet den **Median** über das ganze Randband. Das ist
    gegen Ausreisser robust und hat einen Preis, den erst die Messung gezeigt hat: Zeichnet
    ein Bild nur ein Viertel seines Umrisses, sieht der Median **nichts** — er bricht
    zusammen, statt allmählich zu fallen (`auf-20260822-30`).

    Gemessen an denselben Bildern, ganz **ohne Tiefenschätzer**:

    ==========================  =========  ====================
    Bild                        Anteil     Median-Kante
    ==========================  =========  ====================
    perfektes Blender-Bild      87.4 %     0.1615
    weichgezeichnet (Radius 8)  43.8 %     ~0.03
    z-image-turbo mit Führung   24.3 %     0.0058
    z-image-turbo ohne Führung    6.4 %    0.0037
    qwen                          2.8 %    0.0048
    ==========================  =========  ====================

    Der Anteil trennt, was der Median zu einer Zahl zusammenschiebt: 24.3 % gegen 6.4 %
    ist ein Faktor 4, die zugehörigen Mediane liegen 0.0021 auseinander.

    .. warning::
       **Die letzte Zeile ist die eigentliche Warnung.** Qwen erreicht ρ = −0.7406 —
       ordentlich — und zeichnet den Umriss an **2.8 %** der Grenze, also **unter
       Zufall**. Ein anständiges ρ ist ohne jede Umrisstreue erreichbar. Wer ρ allein
       wertet, wertet ein Bild, das die Tiefen richtig staffelt und das Gebäude nicht
       zeichnet.

    Args:
        ist: die geschätzte Tiefenkarte. Der Vergleich läuft **innerhalb** dieser Karte —
            gefragt ist nicht, ob sie zur Soll-Karte passt, sondern ob sie an der
            Silhouettengrenze überhaupt eine Kante hat.
        staerkste: Anteil der Bildpunkte, der als Kante gilt. Ändert man ihn, ändert man
            **auch den Nullwert** — bei 10 % läge Zufall bei 10 %.

    Returns:
        ``{anteil, n_grenze, n_mit_kante, schranke, zufall, ueber_zufall, methode,
        warnungen}``. ``zufall`` ist ``staerkste`` — die Zahl, gegen die der Anteil zu
        lesen ist. ``anteil`` ist ``None``, wenn es keine Grenze gibt.
    """
    werte = _als_zahlen(ist, "ist")
    if maske is None:
        raise QaError("maske fehlt — ohne Maske gibt es keine Grenze.")
    m = _als_wahrheitswerte(maske, "maske")
    if len(m) != len(werte):
        raise QaError(
            f"maske und ist sind unterschiedlich lang ({len(m)} vs. {len(werte)}).")
    if isinstance(breite, bool) or not isinstance(breite, int) or breite <= 0:
        raise QaError(f"breite muss eine positive ganze Zahl sein, war {breite!r}.")
    if len(werte) % breite != 0:
        raise QaError(f"{len(werte)} Punkte sind kein Vielfaches der Breite {breite}.")
    if not (0.0 < staerkste < 1.0):
        raise QaError(
            f"staerkste muss zwischen 0 und 1 liegen, war {staerkste}. Bei 0 trüge kein "
            f"Punkt je eine Kante, bei 1 jeder — beides misst nichts.")

    hoehe = len(werte) // breite
    antwort = {"anteil": None, "n_grenze": 0, "n_mit_kante": 0, "schranke": None,
               "zufall": staerkste, "zufall_verlangt": staerkste, "ueber_zufall": None,
               "messbar": False, "grund": "",
               "zufall_streuung": None, "zufall_grenze": None,
               "methode": METHODE_KANTENANTEIL, "warnungen": []}

    staerken = _kantenstaerken(werte, breite, hoehe)
    innen, _aussen = _randpunkte(m, breite, hoehe)
    antwort["n_grenze"] = len(innen)
    if not innen:
        antwort["warnungen"].append(
            "Die Maske hat keine Grenze — leer oder das ganze Bild. NICHT GEMESSEN.")
        return antwort
    if len(innen) < MIN_RANDPUNKTE:
        antwort["warnungen"].append(
            f"Nur {len(innen)} Randpunkte, nötig sind {MIN_RANDPUNKTE}. Ein Anteil aus "
            f"einer Handvoll Punkten springt in groben Stufen. NICHT GEMESSEN.")
        return antwort

    sortiert = sorted(staerken, reverse=True)
    schranke = sortiert[max(0, int(len(sortiert) * staerkste) - 1)]
    antwort["schranke"] = schranke

    # **Der Nullwert ist der TATSÄCHLICHE Anteil und nicht der verlangte.** Bei vielen
    # gleichen Werten — eine Karte mit zwei Stufen, ein Bild mit grossen einfarbigen
    # Flächen — liegen weit mehr als `staerkste` Punkte auf oder über der Schranke, weil
    # sich Gleichstände nicht trennen lassen. Dann trifft auch eine bezugslose Grenze
    # entsprechend öfter, und gegen die verlangten 5 % zu prüfen behauptete ein Signal, wo
    # Gleichstand ist. Aufgefallen an einem Testbild aus Streifen: nominal 5 %, tatsächlich
    # weit mehr — und der Anteil an der Grenze stieg folgerichtig mit.
    ueber_schranke = sum(1 for s in staerken if s >= schranke)
    zufall = ueber_schranke / len(staerken)
    antwort["zufall"] = zufall
    antwort["zufall_verlangt"] = staerkste
    mit_kante = sum(1 for i in innen if staerken[i] >= schranke)
    antwort["n_mit_kante"] = mit_kante

    if zufall > MAX_ZUFALL_FAKTOR * staerkste:
        # NICHT MESSBAR — und das ist etwas anderes als ein schlechter Wert.
        #
        # Hier stand bis zum 23.08.2026 eine Warnung und trotzdem eine Zahl. Eine Zahl
        # mit Fussnote wird ohne die Fussnote weitergereicht: `paarurteil` las sie, die
        # Schwelle 0.20 verglich sie, und ein reiner Verlauf bestand mit 100 %.
        antwort["grund"] = (
            f"Nicht messbar: Die Schranke trennt nicht. Verlangt waren die stärksten "
            f"{staerkste:.0%}, tatsächlich liegen {zufall:.0%} der Bildpunkte darüber — "
            f"Gleichstände, also eine Karte mit wenigen verschiedenen Werten. Wo fast "
            f"jeder Punkt als 'starke Kante' gilt, sagt ein Anteil an der Grenze nichts "
            f"über den Umriss. (Fremd geeicht, EICHUNG_2026-08-23.md: grau und ein "
            f"Verlauf erreichen in dieser Bauart 100 %.)")
        antwort["warnungen"].append(antwort["grund"])
        return antwort

    antwort["messbar"] = True
    antwort["anteil"] = mit_kante / len(innen)

    # Der Abstand zum Zufall, an der Streuung gemessen und nicht am blossen Vorzeichen.
    #
    # Ob eine Maskengrenze mit `n` Punkten `k` Treffer zeigt, ist ein Münzwurf je Punkt:
    # binomialverteilt mit der Trefferwahrscheinlichkeit `zufall`. Ihre Streuung ist
    # `sqrt(p·(1-p)/n)`. Alles innerhalb von zwei davon ist Zufall — dieselbe Regel wie
    # bei den Variantenreihen und der Stil-QA.
    streuung = math.sqrt(max(zufall * (1.0 - zufall), 0.0) / len(innen))
    antwort["zufall_streuung"] = streuung
    antwort["zufall_grenze"] = zufall + K_STREUUNGEN_ANTEIL * streuung
    antwort["ueber_zufall"] = antwort["anteil"] > antwort["zufall_grenze"]
    if not antwort["ueber_zufall"]:
        antwort["warnungen"].append(
            f"Der Umriss ist an {antwort['anteil']:.1%} der Grenze gezeichnet — das ist "
            f"NICHT MEHR als Zufall. Erwartet wären {zufall:.1%} ± {streuung:.1%}; "
            f"belegt wäre erst ab {antwort['zufall_grenze']:.1%}. Eine Maskengrenze ohne "
            f"jeden Bezug zum Bild träfe bei {len(innen)} Punkten genauso oft. Gemessen "
            f"vorgekommen (auf-20260822-30: 2.8 % bei einem Bild, dessen ρ mit −0.7406 "
            f"ordentlich aussah).")
    return antwort


# --------------------------------------------------------------------------------------
# Die Anwesenheitsfrage über den RANG statt über den Betrag — das dritte Bein
# --------------------------------------------------------------------------------------

#: Halbe Fensterbreite in Bildpunkten, in der je Grenzabschnitt innen gegen aussen
#: verglichen wird. **Gesetzt, nicht gemessen** (HomeStation, `auf-vis-20260823-08`).
R2_FENSTERRADIUS = 6

#: Jeder wievielte innere Randpunkt einen Abschnitt bildet. Ebenfalls **gesetzt**.
#:
#: Benachbarte Randpunkte teilen fast dasselbe Fenster; jeden zu werten hiesse, dieselbe
#: Beobachtung mehrfach zu zählen. Drei ist die Zahl, mit der die Eichung lief.
R2_JEDER_NTE = 3

#: So viele Abschnitte muss ein Umriss hergeben, sonst ist der Anteil **nicht gemessen**.
#:
#: Ein Anteil aus fünf Abschnitten hat fünf mögliche Werte. Die Eichung lief auf 276 und
#: 515 Abschnitten; hier steht bewusst eine viel kleinere Zahl, weil ein kleines Bauwerk
#: im Bild ein kurzer Umriss ist und deswegen nicht unmessbar sein soll.
R2_MIN_ABSCHNITTE = 24

#: Das Zufallsniveau dieses Masses — **es folgt aus der Konstruktion und ist nicht gemessen.**
#:
#: Hat die Schätzkarte **gar keinen Bezug** zur Maske, sind der Median innen und der Median
#: aussen zwei unabhängige Ziehungen aus derselben Verteilung. Welcher grösser ausfällt,
#: ist dann ein Münzwurf: **50 %**. Für eine symmetrische Werteverteilung gilt das exakt,
#: sonst annähernd.
#:
#: **Nachgemessen, weil «folgt aus der Konstruktion» schon einmal falsch war:** weisses
#: Rauschen über 200 Startwerte auf einer synthetischen Szene ergibt einen Median von
#: **0,5063** (Spanne 0,228 bis 0,772).
#:
#: Das ist die zweite Grösse in diesem Modul, die ihren eigenen Nullwert mitbringt — nach
#: :data:`KANTENANTEIL_STAERKSTE`. Der Vorteil ist derselbe und er ist gross: Er kostet
#: keine Nullprobe je Szene und **hängt nicht an der Szene**.
R2_ZUFALLSNIVEAU = 0.50

#: **ZURÜCKGEZOGEN am 24.08.2026 — von ihrem Urheber.** Steht nur noch als Zahl da, auf
#: die sich Messungen und Protokolle beziehen; sie entscheidet nichts und soll es nie.
#:
#: Die HomeStation hat sie selbst zurückgenommen, und mit einer Begründung, die schwerer
#: wiegt als der Anker: *«Das Zufallsniveau folgt aus der Konstruktion und beträgt 0,50.
#: Eine Schwelle darunter ist grundsätzlich unhaltbar. Eine Schwelle muss über 0,50
#: liegen. Die echten Fälle lagen zwischen 52,6 und 82,5 % — das lässt ein Fenster von
#: rund ZWEI Punkten, und das ist keine Schwelle, sondern eine Zufallsgrenze.»*
#:
#: **Beide Rauschanker waren richtig, sie massen Verschiedenes** — die Frage, die ich von
#: hier aus nicht trennen konnte, hat sie am Gerät getrennt:
#:
#:     Rauschen ALS Tiefenkarte, 200 Ziehungen   Median 0,4942, über 0,45 in 160/200
#:     SCHÄTZER auf Rauschbildern, 30 Ziehungen  Median 0,1440, über 0,45 in   0/30
#:
#: Ihre 33,7 % waren also keine glücklich gezogene Zahl, sondern eine **Eigenschaft des
#: Schätzers** — und das ist der Faden, an dem :data:`RAUSCHBODEN_UEBER_MASKE` hängt.
#:
#: Vorgeschlagene Schwelle für den Anteil — **abgelesen, sie torschliesst NICHT, und sie
#: liegt UNTER dem Zufallsniveau.**
#:
#: **Gemessen** (`auf-vis-20260823-08`, fünf Szenen, drei Gebäude, nur Blender-Renders):
#:
#:     g0 flach 68,1 % · g1 geneigt 70,3 % · g2 Nachbargebäude 67,0 %
#:     s60 75,5 % · s29 82,5 %
#:     Anker: Rauschen 33,7 / 16,1 % · grau 0,0–0,4 % · Verlauf 0,2–0,4 %
#:
#: Jeder echte Fall liegt zwischen 52,6 und 82,5 %, jeder Anker bei höchstens 33,7 %.
#: 45 % hat damit 7 Punkte Abstand nach unten und 11 nach oben. **Der Rauschwert hängt an
#: der Szene** (33,7 gegen 16,1 %), die Schwelle braucht darum Luft; 40 % wäre schon knapp.
#:
#: **Sie entscheidet aus zwei Gründen nichts — Entscheid vom 23.08.2026.**
#:
#: **Erstens, und das ist der schwerere: 0,45 liegt unter dem Zufallsniveau von 0,50**
#: (:data:`R2_ZUFALLSNIVEAU`). Nachgemessen auf einer synthetischen Szene besteht weisses
#: Rauschen diese Schwelle in **138 von 200** Startwerten. Der eine gemessene Rauschanker
#: von 33,7 % ist **eine Ziehung** aus einer Verteilung, deren Median bei 0,50 liegt und
#: die von 0,23 bis 0,77 streut — und aus einer Ziehung eine Schwelle abzulesen ist
#: derselbe Fehler wie eine Spanne aus einer Stichprobe für die Wahrheit zu nehmen.
#:
#: Möglich ist, dass ihr Anker etwas anderes ist als meiner: Sie messen den *Schätzer auf
#: einem Rauschbild*, ich das Rauschen selbst als Karte. Dann ist ihre 33,7 % kein
#: Münzwurf, sondern eine Eigenschaft des Schätzers — und **auch dann braucht der Anker
#: mehrere Startwerte**, statt einen.
#:
#: **Zweitens:** Kein einziger der fünf Werte stammt von einem **erzeugten** Bild. Alle
#: kommen aus Blender-Renders und den Nullankern; die Versatzreihe ist der *Ersatz* für
#: schlechter werdende Geometrie. Eine Schwelle, die über erzeugte Bilder entscheidet, an
#: keinem erzeugten Bild geeicht — das ist die Reihenfolge, die dieses Projekt am selben
#: Tag zweimal zurückgenommen hat.
R2_SCHWELLE = 0.45

METHODE_R2 = ("Anteil der Grenzabschnitte, an denen der Median INNEN näher liegt als der "
              "Median AUSSEN im selben Fenster — Rang statt Betrag, v1")


def anteil_naeher_am_rand(ist: Sequence[float], maske: Sequence[bool], *, breite: int,
                          polaritaet: int | None = None,
                          fensterradius: int = R2_FENSTERRADIUS,
                          jeder_nte: int = R2_JEDER_NTE) -> dict:
    """An wieviel Prozent des Umrisses liegt das Bauwerk **lokal näher** als sein Hintergrund.

    .. danger::
       **NICHT AM PRODUKTPFAD VERWENDEN. Diese Funktion sortiert an erzeugten Bildern
       verkehrt.** Sie ist am 23.08.2026 angeschlossen und am 24.08.2026 wieder
       herausgenommen worden — auf Bitte der HomeStation und mit ihrem Beleg
       (`auf-vis-20260824-09`), der erstmals an **erzeugten** Bildern gemessen wurde:

       * **Sieben von zehn** erzeugten Bildern liegen **über** dem perfekten Blender-Bild
         derselben Szene. Sechs davon haben ``|rho| < 0.32``, also praktisch keine
         Tiefenordnung. Das einzige Bild *unter* dem Band hat das zweitbeste ρ.
       * Der Mechanismus ist gemessen und lässt keine Rettung zu: Eine **in Y verschobene**
         Maske bekommt denselben Wert — 0,8405 gegen 0,8405, identisch. In X sehr wohl.
         Der Schätzer sieht im unteren Bildteil eine grosse Nah-Region; jede Maske dort
         bekommt denselben Wert. **Das Mass beantwortet am Produktpfad nicht «steht da ein
         Bauwerk», sondern «liegt die Maske im unteren Bilddrittel».**

       *«Eine Zahl, die bei schlechteren Bildern höher ausfällt, ist schlimmer als keine.»*

       **Und mein Gegenargument von gestern genügt nicht.** Ich hatte den Anschluss damit
       gerechtfertigt, er sei streng additiv: Kein Bild besteht durch R2, das ohne R2
       durchgefallen wäre. Das stimmt — und es übersieht, dass eine **angezeigte** Zahl den
       Menschen in die Irre führt, der das Urteil liest. Der gehört zum Tor.

       Die Funktion bleibt erhalten, weil der Befund an ihr hängt und weil die Tests
       festhalten, *warum* sie nicht taugt. Wer sie wieder anschliessen will, misst zuerst
       an erzeugten Bildern und prüft die Y-Verschiebung.

    Je Grenzabschnitt der Median der Maskenpunkte gegen den Median der Aussenpunkte
    **im selben Fenster**. Gezählt wird nur, *welcher* der beiden näher liegt — kein
    Betrag, keine Normierung über die Karte.

    **Warum das ein anderes Mass ist und nicht ein besseres.** Ein monokularer Schätzer
    liefert *relative* Tiefe: Die Reihenfolge stimmt, die absolute Skala ist willkürlich.
    An derselben Stelle desselben Bildes gemessen (`auf-vis-20260823-08`): Bauwerk 1,7124,
    Nachbar 1,6112 — die Ordnung ist richtig, der Betrag beträgt aber nur 3 % der
    Kartenspanne, obwohl 15 m dazwischenliegen. :func:`kante_an_maskengrenze` und
    :func:`anteil_grenze_mit_kante` fragen nach dem Betrag und messen dort nichts mehr;
    dieses Mass fragt nach dem Rang und trägt weiter.

    Der Preis ist mitgemessen und gehört in denselben Satz: **Es ist kein Gütemass.** Die
    Versatzreihe fällt nicht monoton — auf einer Szene ging sie 75,5 → 71,7 → **73,8** →
    71,1 → 63,1 → 59,4, also zwischendurch wieder hinauf. Es beantwortet *«steht da ein
    Bauwerk»*, nicht *«wie gut ist es gezeichnet»*.

    **Gleiches gegen Gleiches, und das ist keine Feinheit.** Die HomeStation hat einen
    ersten Anlauf dokumentiert, der das **Maximum** über das Innenfenster gegen einen
    **einzelnen** Aussenpunkt verglich. Das ist strukturell nach oben verzerrt: Weisses
    Rauschen erreichte damit 71,3 % — mehr als jedes perfekte Bild. Median gegen Median
    behebt es. Dieser Irrweg steht als Test in `tests/test_r2_anwesenheit.py`, damit ihn
    niemand ein zweites Mal geht.

    Args:
        polaritaet: ``+1`` metrische Tiefe (nah = klein), ``-1`` Disparität (nah = gross),
            ``None`` ungemessen. Ohne sie steht ``anteil`` nicht da: Ob „grösser" näher
            oder ferner heisst, entscheidet die Polarität, und raten hiesse, in der Hälfte
            der Fälle das Gegenteil zu melden.

    Returns:
        ``{anteil, n_abschnitte, n_naeher, n_unentschieden, schwelle, ueber_schwelle,
        methode, polaritaet, fensterradius, jeder_nte, warnungen}``.

        ``anteil`` ist ``None``, wenn nicht gemessen werden konnte — **nicht** 0, was
        „nirgends näher" hiesse und damit ein Urteil wäre.

        ``ueber_schwelle`` ist eine **Auskunft und kein Tor**: Diese Funktion entscheidet
        über nichts (siehe :data:`R2_SCHWELLE`).

    Raises:
        QaError: Masse fehlen, sind ungleich lang, ``breite`` passt nicht, oder
            ``fensterradius``/``jeder_nte`` sind nicht positiv.
    """
    werte = _als_zahlen(ist, "ist")
    if maske is None:
        raise QaError(
            "maske fehlt. Ohne Maske gibt es keinen Umriss, an dem sich innen von aussen "
            "unterscheiden liesse.")
    m = _als_wahrheitswerte(maske, "maske")
    if len(m) != len(werte):
        raise QaError(
            f"maske und ist sind unterschiedlich lang ({len(m)} vs. {len(werte)}). "
            f"Abschneiden wäre eine stillschweigende Reparatur mit falschem Ergebnis.")
    if isinstance(breite, bool) or not isinstance(breite, int) or breite <= 0:
        raise QaError(f"breite muss eine positive ganze Zahl sein, war {breite!r}.")
    if len(werte) % breite != 0:
        raise QaError(
            f"Die Karte hat {len(werte)} Punkte, das ist kein Vielfaches der Breite "
            f"{breite}. Eine der beiden Angaben stimmt nicht — geraten wird hier nicht.")
    if isinstance(fensterradius, bool) or not isinstance(fensterradius, int) or fensterradius <= 0:
        raise QaError(f"fensterradius muss eine positive ganze Zahl sein, war {fensterradius!r}.")
    if isinstance(jeder_nte, bool) or not isinstance(jeder_nte, int) or jeder_nte <= 0:
        raise QaError(f"jeder_nte muss eine positive ganze Zahl sein, war {jeder_nte!r}.")

    hoehe = len(werte) // breite
    antwort = {"anteil": None, "n_abschnitte": 0, "n_naeher": 0, "n_unentschieden": 0,
               "schwelle": R2_SCHWELLE, "ueber_schwelle": None,
               "zufallsniveau": R2_ZUFALLSNIVEAU, "ueber_zufall": None,
               "methode": METHODE_R2,
               "polaritaet": polaritaet, "fensterradius": fensterradius,
               "jeder_nte": jeder_nte, "warnungen": []}

    if polaritaet is None:
        antwort["warnungen"].append(
            "Polarität ungemessen. Ohne Richtung ist nicht entscheidbar, ob der GRÖSSERE "
            "Median den näheren Körper meint: Bei Disparität liegt das Bauwerk oben, bei "
            "metrischer Tiefe unten. NICHT GEMESSEN. Abhilfe: polaritaet_aus_messungen.")
        return antwort
    if polaritaet not in (POLARITAET_TIEFE, POLARITAET_DISPARITAET):
        raise QaError(
            f"polaritaet muss {POLARITAET_TIEFE:+d}, {POLARITAET_DISPARITAET:+d} oder "
            f"None sein, war {polaritaet!r}.")

    innen, _aussen = _randpunkte(m, breite, hoehe)
    abschnitte = innen[::jeder_nte]

    naeher = 0
    unentschieden = 0
    gewertet = 0
    for i in abschnitte:
        x0, y0 = i % breite, i // breite
        drin: list[float] = []
        draussen: list[float] = []
        for y in range(max(0, y0 - fensterradius), min(hoehe, y0 + fensterradius + 1)):
            for x in range(max(0, x0 - fensterradius), min(breite, x0 + fensterradius + 1)):
                k = y * breite + x
                (drin if m[k] else draussen).append(werte[k])
        # Ein Fenster ohne beide Seiten trägt keinen Vergleich. Es wird NICHT als
        # „nicht näher" gezählt — das wäre eine Aussage über etwas Ungesehenes.
        if not drin or not draussen:
            continue
        gewertet += 1
        # Gleiches gegen Gleiches: Median gegen Median. Siehe Docstring — die Fassung
        # mit Maximum gegen Einzelpunkt liess weisses Rauschen auf 71,3 % steigen.
        gerichtet = -polaritaet * (_median(drin) - _median(draussen))
        if gerichtet > 0.0:
            naeher += 1
        elif gerichtet == 0.0:
            unentschieden += 1

    antwort["n_abschnitte"] = gewertet
    antwort["n_naeher"] = naeher
    antwort["n_unentschieden"] = unentschieden

    if gewertet < R2_MIN_ABSCHNITTE:
        antwort["warnungen"].append(
            f"Nur {gewertet} Abschnitte, nötig sind {R2_MIN_ABSCHNITTE}. Ein Anteil aus so "
            f"wenigen hat so wenige mögliche Werte — das ist Rauschen mit Dezimalpunkt. "
            f"NICHT GEMESSEN, weder 0 noch 1.")
        return antwort

    antwort["anteil"] = naeher / gewertet
    antwort["ueber_schwelle"] = antwort["anteil"] >= R2_SCHWELLE
    if antwort["anteil"] > R2_ZUFALLSNIVEAU:
        # Ueber dem Muenzwurf — aber um WIEVIEL es dafuer sein muss, steht nicht fest.
        # Die Fenster benachbarter Abschnitte ueberlappen (Radius 6, jeder 3. Punkt), also
        # sind die Abschnitte nicht unabhaengig und die binomiale Streuung zu klein.
        # Gemessen betraegt der Faktor auf einer synthetischen Szene 1.93 bei jeder_nte=3
        # und 1.34 bei 7 — auf EINER Szene, also keine Zahl, auf die sich etwas stuetzen
        # laesst. Darum bleibt `ueber_zufall` None statt True: Das waere eine Behauptung
        # ueber einen Abstand, den niemand kennt.
        antwort["warnungen"].append(
            f"Anteil {antwort['anteil']:.4f} liegt über dem Zufallsniveau "
            f"{R2_ZUFALLSNIVEAU:.2f} — um wieviel er darüberliegen MUSS, ist offen: Die "
            f"Fenster benachbarter Abschnitte überlappen, die Abschnitte sind also nicht "
            f"unabhängig und die binomiale Streuung zu klein. NICHT als 'über Zufall' "
            f"gemeldet, solange die Zahl fehlt.")
    else:
        antwort["ueber_zufall"] = False
    if antwort["ueber_schwelle"] and antwort["anteil"] < R2_ZUFALLSNIVEAU:
        antwort["warnungen"].append(
            f"Die vorgeschlagene Schwelle {R2_SCHWELLE:.2f} liegt UNTER dem Zufallsniveau "
            f"{R2_ZUFALLSNIVEAU:.2f}. Dieser Wert besteht sie und ist trotzdem schlechter "
            f"als ein Münzwurf. Die Schwelle ist an EINEM Rauschanker abgelesen (33,7 %) — "
            f"weisses Rauschen besteht sie in 138 von 200 Startwerten.")
    return antwort


#: Ab welchem Anteil Himmel hinter dem Umriss die Tiefenkante überhaupt etwas messen kann.
#:
#: **Am Gerät gemessen und schwer erkauft** (HomeStation, `auf-vis-20260823-07`,
#: 23.08.2026): Dieselbe Kamera, dasselbe Bauwerk, nur der Hintergrund verschieden.
#:
#:     g0 flaches Gelände      63,3 % Himmel hinter dem Umriss    Kante +0,4227
#:     g1 geneigtes Gelände     0,0 %                             Kante +0,1442
#:     g2 Nachbargebäude        0,0 %                             Kante +0,0016
#:
#: In g2 trennt die Kante ein **perfektes** Bild nicht mehr von weissem Rauschen
#: (+0,0016 gegen −0,0024; der Abstand ist kleiner als die Streuung der Nullanker
#: untereinander). Ein grünes Abzeichen wäre dort in die **gefährliche** Richtung falsch.
#:
#: **Der Mechanismus liegt nicht im Mass.** Der Nachbar steht im Soll 15,05 m weiter
#: hinten; der Schätzer legt beide nur 3,0 % der Kartenspanne auseinander. Ein
#: monokularer Schätzer trennt zwei ähnliche Betonkörper in 34 und 49 m praktisch nicht —
#: er hat dafür keinen Bildhinweis. Die Gegenprobe macht es endgültig: Der **wahre**
#: Sprung ist in g2 am grössten und der **gemessene** dort am kleinsten. Die Beziehung
#: ist umgekehrt.
#:
#: Daraus folgt keine bessere Normierung, sondern eine Zuständigkeitsgrenze: Wo kein
#: Himmel hinter dem Umriss steht, misst die Tiefenkante nichts, und sie soll dann
#: **schweigen statt bestehen**. Ob ein grösserer Schätzer die 15 m auflöst, ist
#: ungemessen — dann wäre der ganze Befund eine Frage der Modellgrösse.
#:
#: Der Wert ist eine **Setzung**: 10 % gemessene Himmelabschnitte. Zwischen 0 % (nichts)
#: und 63 % (trägt) liegt nichts Gemessenes; wer die Lücke füllt, ändert die Zahl.
#:
#: .. important::
#:    **Diese Grenze gehört zum BETRAGSMASS, nicht zur Frage.** Sie ist die Antwort
#:    darauf, dass unser zweites Bein den *Betrag* des Tiefensprungs benutzt — und der
#:    wird gestaucht, wo kein Himmel dahintersteht.
#:
#:    Der Schätzer selbst **ordnet dort richtig**: an derselben Szene Bauwerk 1.7124,
#:    Nachbar 1.6112, der Nachbar liegt also hinten (`auf-vis-20260823-08`). Ein
#:    monokularer Schätzer liefert *relative* Tiefe; die absolute Skala ist willkürlich.
#:    Ein **rangbasiertes** Mass trägt dort darum weiter — die HomeStation misst mit einer
#:    solchen Variante in derselben Szene 67,0 % gegen einen Rauschanker von 33,7 %.
#:
#:    Wer das zweite Bein einmal auf ein Rangmass umstellt, muss diese Grenze also
#:    **mitprüfen und vermutlich abschalten**. Sie hier stehenzulassen wäre dann derselbe
#:    Fehler in der anderen Richtung: ein Mass zum Schweigen bringen, das antworten kann.
MIN_HIMMELANTEIL = 0.10


def himmel_hinter_umriss(soll, maske, *, breite: int,
                         grenze_m: float = HINTERGRUND_SCHWELLE_M) -> dict:
    """Wieviel des Umrisses hat **Himmel** dahinter — aus dem SOLL, nicht aus der Schätzung.

    Der Anteil der äusseren Randpunkte, deren Soll-Tiefe Hintergrund ist (nicht endlich
    oder jenseits von ``grenze_m``). Das ist genau die Grösse, an der die Tiefenkante
    hängt: Wo Himmel dahintersteht, ist der Sprung unendlich; wo ein Nachbargebäude
    dahintersteht, ist er im Soll gross und in der Schätzung praktisch null.

    **Aus dem Soll und nicht aus dem Bild** — das ist der Punkt. Die Frage *«kann hier
    überhaupt gemessen werden»* muss beantwortbar sein, **bevor** gemessen wird, und die
    Soll-Karte liegt in dieser Kette immer vor. Eine Zuständigkeitsprüfung, die das
    Ergebnis der Messung braucht, ist keine.

    Returns:
        ``{anteil, n_aussen, n_himmel, traegt, methode}``. ``traegt`` ist ``False``,
        wenn der Anteil unter :data:`MIN_HIMMELANTEIL` liegt — dann misst die Tiefenkante
        nichts, und das ist etwas anderes als ein schlechter Wert.
    """
    werte = _als_zahlen(soll, "soll")
    m = _als_wahrheitswerte(maske, "maske")
    if len(werte) != len(m):
        raise QaError(
            f"soll und maske sind verschieden lang ({len(werte)} gegen {len(m)}). "
            f"Zwei Karten verschiedener Grösse zu vergleichen ergäbe eine Zahl ohne Sinn.")
    hoehe = len(werte) // breite
    _innen, aussen = _randpunkte(m, breite, hoehe)

    n_himmel = sum(1 for i in aussen
                   if not math.isfinite(werte[i]) or werte[i] >= grenze_m)
    anteil = (n_himmel / len(aussen)) if aussen else 0.0
    return {
        "anteil": anteil,
        "n_aussen": len(aussen),
        "n_himmel": n_himmel,
        "traegt": bool(aussen) and anteil >= MIN_HIMMELANTEIL,
        "methode": "himmelanteil_am_aussenrand",
    }


#: Ab welchem Anteil durchsichtiger Maskenpunkte die Soll-Karte als **durchsichtig** gilt.
#:
#: **ABGELESEN AN ZWEI LÄUFEN, NICHT KALIBRIERT** — und das ist hier keine Verlegenheit,
#: sondern die ganze Datenlage. Demolauf 16 (dieselbe Kette, dieselbe Kamera, ein Modell
#: ohne Scheibe) hat **0 von 714818** Maskenpunkten ohne endliche Soll-Tiefe; Demolauf 17
#: (dasselbe, nur mit 750 Glas-Primitiven) hat **2106 von 729938**, also 0.29 %. Zwischen
#: «gar keiner» und «einer von 350» liegt keine Grauzone, die zu teilen wäre.
#:
#: Ein Promille steht darum nicht als gemessene Trennlinie da, sondern als **Nachsicht
#: gegenüber dem Bildrand**: Material-ID und Tiefe entstehen in zwei getrennten
#: Render-Durchgängen mit verschiedenem Rekonstruktionsfilter, und ein einzelnes Pixel
#: Versatz an einer Silhouettenkante wäre kein Befund. Dass Lauf 16 exakt null erreicht,
#: sagt: im gesunden Fall wird diese Nachsicht gar nicht gebraucht.
MAX_DURCHSICHT_ANTEIL = 0.001


def tiefenstruktur(karte: Sequence[float], *, breite: int,
                   hintergrund_grenze: float = HINTERGRUND_SCHWELLE_M) -> dict:
    """Hat diese Tiefenkarte **Kanten** — oder ist sie ein reiner Verlauf?

    **Der Anlass** (HomeStation, 12.09.2026, erster Lauf von der Szene bis zum fertigen
    Bild): Der Rahmungsriegel misst den **Füllgrad** und entschied damit falsch herum. Er
    wies die brauchbare Übersichtskamera ab — *«Das Bauwerk füllt 59.9 % der Bildbreite,
    gemessen nötig sind 65 %»* — und liess die **nutzlose Nahaufnahme durch**, die mit
    100 % Füllgrad 5,1 m vor einer fensterlosen Wand stand. Dort war *«die Tiefenkarte ein
    reiner Verlauf ohne jede Kante, und das Bildmodell hat frei erfunden»*.

    **Warum es zwei Zahlen sind, und warum die erste allein nicht reicht.** Der Vorschlag
    von dort war die *mittlere Abweichung zum Nachbarpunkt*. Beim Nachrechnen an zwei
    synthetischen Karten fiel auf: massstabsfrei gemacht — also durch die Spanne geteilt —
    liefert sie für einen reinen Verlauf und für eine harte Kante **dieselbe Zahl** —
    an einem 16×16-Feld beide Male 0,0333, auf vier Stellen gleich. Der Grund ist
    einfach: Ein Verlauf hat an *jedem* Paar eine kleine Differenz, eine Kante an
    *einem* Paar eine grosse, und Mittelwert geteilt durch Spanne hebt das gegeneinander
    auf.

    *Eine Kennzahl, die stimmt, während das Bild schlechter wird, ist die falsche
    Kennzahl* — derselbe Satz, den die HomeStation aus ihrem Renderprojekt mitgeschickt
    hat, hier auf ihren eigenen Vorschlag angewandt.

    Was trennt, ist die **zweite Differenz** (Krümmung): Ein linearer Verlauf hat sie
    **null**, eine Kante nicht. Gemessen an denselben Karten, 16×16:

    ===================  ============  ==================
    Karte (16×16)        ``glaette``   ``struktur``
    ===================  ============  ==================
    reiner Verlauf          0,0333       **0,0000**
    harte Kante             0,0333       **0,0714**
    Raum mit Boden          0,0479       **0,0402**
    ===================  ============  ==================

    Die mittlere Zeile ist der Prüfstein: Dieselbe ``glaette``, und die eine Karte trägt
    alles, was ein ControlNet braucht, die andere nichts.

    ``struktur`` ist die tragende Zahl, ``glaette`` steht daneben, weil sie der
    ursprüngliche Vorschlag war und ihr Versagen dokumentiert gehört.

    **Das ist eine Messung und kein Riegel.** Sie entscheidet nichts. Eine Schwelle aus
    zwei Fällen wäre an zwei Fällen geeicht — dieselbe Zurückhaltung wie bei den
    Paarschwellen. Ob daraus ein zweites Tor neben dem Füllgrad wird, entscheidet eine
    Messreihe.

    Hintergrundpunkte (≥ ``hintergrund_grenze``) werden **ausgelassen**, und jedes Paar
    mit einem: Der Sprung von einer Fassade auf die Himmelsmarke ist keine Struktur des
    Bauwerks, sondern der Abstand zu einer Konstanten — er liesse jede Aussenansicht
    strukturreich aussehen, auch eine leere.

    Returns:
        ``{struktur, glaette, n_stellen, n_paare, n_hintergrund, spanne, warnungen}``.
        ``struktur`` ist ``None``, wenn zu wenig zu vergleichen war oder die Karte keine
        Spanne hat — *nicht* 0: Eine Karte ohne Spanne ist **nicht gemessen** und nicht
        *strukturlos*.
    """
    if breite is None or int(breite) <= 0:
        raise QaError(f"breite muss eine positive ganze Zahl sein, war {breite!r}")
    breite = int(breite)
    if len(karte) % breite:
        raise QaError(f"Karte mit {len(karte)} Punkten passt nicht zu Breite {breite}.")

    hoehe = len(karte) // breite
    grenze = float(hintergrund_grenze)
    echt = [float(w) for w in karte]
    innen = [w < grenze for w in echt]

    antwort = {"struktur": None, "glaette": None, "n_stellen": 0, "n_paare": 0,
               "n_hintergrund": sum(1 for d in innen if not d), "spanne": None,
               "warnungen": []}

    werte = [w for w, d in zip(echt, innen) if d]
    if len(werte) < 2:
        antwort["warnungen"].append(
            "Weniger als zwei Punkte ohne Hintergrundmarke — NICHT GEMESSEN.")
        return antwort
    spanne = max(werte) - min(werte)
    antwort["spanne"] = spanne
    if spanne <= 0.0:
        antwort["warnungen"].append(
            "Die Karte hat keine Spanne — alle Punkte tragen denselben Wert. NICHT "
            "GEMESSEN; eine massstabsfreie Zahl entstuende hier nur durch Division durch "
            "null. (Eine Tiefenkarte ohne jede Staffelung ist fuer sich schon ein Befund.)")
        return antwort

    # Erste Differenz — der urspruengliche Vorschlag. Steht da, trennt aber nicht.
    summe1 = 0.0
    paare = 0
    for y in range(hoehe):
        for x in range(breite):
            i = y * breite + x
            if not innen[i]:
                continue
            if x + 1 < breite and innen[i + 1]:
                summe1 += abs(echt[i] - echt[i + 1])
                paare += 1
            if y + 1 < hoehe and innen[i + breite]:
                summe1 += abs(echt[i] - echt[i + breite])
                paare += 1

    # Zweite Differenz — die Zahl, die traegt.
    summe2 = 0.0
    stellen = 0
    for y in range(hoehe):
        for x in range(1, breite - 1):
            i = y * breite + x
            if innen[i - 1] and innen[i] and innen[i + 1]:
                summe2 += abs(echt[i - 1] - 2 * echt[i] + echt[i + 1])
                stellen += 1
    for y in range(1, hoehe - 1):
        for x in range(breite):
            i = y * breite + x
            if innen[i - breite] and innen[i] and innen[i + breite]:
                summe2 += abs(echt[i - breite] - 2 * echt[i] + echt[i + breite])
                stellen += 1

    antwort["n_paare"] = paare
    antwort["n_stellen"] = stellen
    if paare:
        antwort["glaette"] = (summe1 / paare) / spanne
    if stellen == 0:
        antwort["warnungen"].append(
            "Keine Stelle mit drei benachbarten Punkten ohne Hintergrundmarke — die "
            "zweite Differenz ist NICHT GEMESSEN.")
        return antwort
    antwort["struktur"] = (summe2 / stellen) / spanne
    return antwort


#: Ab welchem Anteil markierter Maskenpunkte gewarnt wird.
#:
#: **Gemessen, nicht gesetzt:** Die HomeStation hat am 08.09.2026 (`auf-20260907-81`) den
#: Mechanismus aufgeklärt, an dem der Paartest frontal zerbricht — bei
#: ``quader-w-versatz_20px`` holten **1220 von 5635 Maskenpunkten (21,7 %)** ihren Wert
#: von ausserhalb des Umrisses. Ein Zehntel ist damit deutlich unter dem beobachteten
#: Fall und immer noch weit über dem, was eine saubere Maske hat.
MASKE_HINTERGRUND_WARNSCHWELLE = 0.10


def maske_auf_hintergrund(soll, maske, *,
                          grenze_m: float = HINTERGRUND_SCHWELLE_M,
                          warnschwelle: float = MASKE_HINTERGRUND_WARNSCHWELLE) -> dict:
    """Wie viele Maskenpunkte stehen in der **Soll**-Karte auf der Hintergrundmarke?

    **Eine Messung, kein Eingriff.** :func:`rho_ueber_maske` rechnet solche Punkte
    ausdrücklich mit, und der Grund dort ist gut: Eine Schwellenprüfung *im Mass* wäre
    wieder die Hintergrundstrategie, an der der Weg über die übliche Kette zerbrochen ist.
    *Die Maske entscheidet, und wer sie erzeugt, verantwortet sie.* Diese Funktion ändert
    daran nichts — sie macht nur sichtbar, **wie viel** dort mitgerechnet wird.

    **Warum das sichtbar sein muss** (`auf-20260907-81`, HomeStation, 08.09.2026). Unter
    dem echten Schätzer trennt der Paartest frontal nicht mehr: Der höchste schlechte Fall
    liegt mit 0,9957 über dem niedrigsten guten mit 0,1426. Der Mechanismus ist gemessen
    und liegt genau hier:

    * 1220 von 5635 Maskenpunkten (**21,7 %**) holen ihren Wert von **ausserhalb** des
      Umrisses.
    * In der **Soll**-Karte steht dort 1220-mal die Hintergrundmarke — *eine Konstante
      ohne Rangfolge*, über die ρ nicht einmal definiert ist.
    * In der **Schätzung** stehen dort gewöhnliche Werte, die den Maskenbereich
      überlappen; über diese 1220 Punkte allein korreliert der verrutschte Streifen mit
      **+0,9873**.

    *Was die perfekte Karte an einer unendlichen Kante fängt, glättet der Schätzer weg.*

    Eine hohe Zahl heisst **nicht**, dass die Messung falsch ist — sie heisst, dass ein
    Teil von ρ aus Punkten stammt, an denen die Referenz gar keine Geometrie trägt. Wer
    die Zahl kennt, kann das einordnen; wer sie nicht kennt, liest ρ als Aussage über das
    Bauwerk.

    Returns:
        ``{n_maske, n_hintergrund, anteil, grenze_m, warnungen}``. ``anteil`` ist ``None``,
        wenn die Maske leer ist — nicht 0: *Kein Punkt* ist etwas anderes als *kein
        markierter Punkt*.
    """
    if maske is None:
        raise QaError("maske fehlt (None) — diese Prüfung braucht eine Auswahl.")
    if len(soll) != len(maske):
        raise QaError(f"soll ({len(soll)}) und maske ({len(maske)}) sind ungleich lang.")

    grenze = float(grenze_m)
    n_maske = 0
    n_hintergrund = 0
    for wert, drin in zip(soll, maske):
        if not drin:
            continue
        n_maske += 1
        if float(wert) >= grenze:
            n_hintergrund += 1

    antwort = {"n_maske": n_maske, "n_hintergrund": n_hintergrund, "anteil": None,
               "grenze_m": grenze, "warnungen": []}
    if n_maske == 0:
        antwort["warnungen"].append(
            "Leere Maske — kein Punkt zu prüfen. Das heisst NICHT GEMESSEN und nicht "
            "'keine Hintergrundpunkte'.")
        return antwort

    anteil = n_hintergrund / n_maske
    antwort["anteil"] = anteil
    if anteil >= warnschwelle:
        antwort["warnungen"].append(
            f"{n_hintergrund} von {n_maske} Maskenpunkten ({anteil:.1%}) stehen in der "
            f"SOLL-Karte auf der Hintergrundmarke (≥ {grenze:.3g} m). Dort trägt die "
            f"Referenz keine Geometrie: eine Konstante ohne Rangfolge. Sie gehen in "
            f"rho_maske als gewöhnliche Zahlen mit ein — in der SCHAETZUNG stehen an "
            f"denselben Stellen gewöhnliche Werte, und über genau solche Punkte "
            f"korrelierte ein verrutschter Streifen am 08.09.2026 mit +0,9873. "
            f"Die Maske passt nicht zum Umriss dieses Renders.")
    return antwort


def durchsichtiges_soll(soll, maske, *,
                        grenze_m: float = HINTERGRUND_SCHWELLE_M) -> dict:
    """Sieht die **Soll**-Karte durch das eigene Bauwerk hindurch? Ein Riegel, kein Mass.

    Die Maske kommt aus dem Material-ID-Pass, die Tiefe aus dem Z-Pass — **zwei
    Durchgänge desselben Renders derselben Szene**. Wo die Maske sagt «hier steht ein
    Bauteil» und die Tiefe sagt «hier ist Himmel», widersprechen sich die beiden. Das ist
    kein schlechter Messwert, sondern ein **Widerspruch in der Referenz**, gegen die
    danach alles andere gemessen wird.

    **Warum das eine eigene Prüfung braucht und nicht am Score abzulesen ist.** Am
    03.09.2026 kam in Demolauf 17 erstmals Glas im Modell an — 750 Primitive mit
    ``alphaMode: BLEND``. Der Z-Pass lief mit den Cycles-Vorgaben, also mit
    Transparenz-Bounces, und schrieb hinter jeder Scheibe *das, was dahinter liegt*: im
    Median 4.49 m tiefer als der eigene undurchsichtige Rand, im 95. Perzentil 26.6 m,
    und an 2106 Punkten den Hintergrundwert — dort verliess der Strahl das Gebäude auf
    der anderen Seite wieder. Der Material-ID-Pass war nicht betroffen; er läuft seit
    jeher mit ``transparent_max_bounces = 0``.

    Die Folge war ein Rückschritt, der wie ein schlechteres Bild aussah und keiner war.
    Nachgerechnet mit derselben Ist-Schätzung, nur mit im Soll undurchsichtig gemachtem
    Glas (Zeilenfüllung aus den undurchsichtigen Rändern):

    ==========================  =========  ===========  =========
    Demolauf 17 «Eingang»        wie gef.   Glas dicht   Lauf 16
    ==========================  =========  ===========  =========
    ``score``                      0.0000       0.2001     0.2015
    ``rho_maske`` (gerichtet)     +0.6480      +0.8057    +0.7995
    ``spearman``                  +0.2501      −0.2377    −0.2393
    ==========================  =========  ===========  =========

    Der Score war auf null abgeschnitten, weil das **Vorzeichen** der Rangkorrelation
    kippte — vorne und hinten vertauscht, von der Kette als Geometriebefund gemeldet.
    Vertauscht hatte sie nicht das Bild, sondern die Soll-Karte. **Ein Mass, das ein
    besseres Modell schlechter bewertet, misst nicht das, was gemeint war**, und die Kette
    konnte das von sich aus nicht sagen.

    **Was diese Prüfung sieht und was nicht.** Sie zählt nur die Punkte, an denen die
    Durchsicht bis zum Hintergrund durchschlägt — 2106 von 85069 Glaspunkten, also die
    Spitze. Der Schaden am Score entsteht an den **übrigen** Glaspunkten, deren Tiefe
    bloss ein paar Meter zu weit hinten liegt und darum endlich bleibt. Die Zahl hier ist
    ein **Anzeiger, kein Schadensmass**: Sie sagt zuverlässig, *dass* die Soll-Karte
    durchsichtig ist, und nichts darüber, *wieviel* das den Score gekostet hat. Wer sie
    als Schadensmass liest, liest sie falsch.

    **Warum ein Widerspruch hier immer ein Defekt ist.** Die Maske enthält nur Punkte, an
    denen der Material-ID-Pass eine Fläche getroffen hat. Wo etwas getroffen wurde, hat es
    eine endliche Entfernung. Ein Durchblick durch ein Tor oder unter einem Vordach fällt
    nicht darunter: Dort trifft schon die Material-ID nichts, und der Punkt liegt gar
    nicht erst in der Maske. Es gibt darum keinen gesunden Fall, in dem diese Zahl gross
    wird.

    Args:
        soll: die Soll-Tiefenkarte in Metern, zeilenweise von oben.
        maske: die Bauwerksmaske aus dem Material-ID-Pass, gleich lang.
        grenze_m: ab hier gilt ein Wert als Hintergrund. Vorgabe
            :data:`HINTERGRUND_SCHWELLE_M`.

    Returns:
        ``{n_maske, n_durchsicht, anteil, durchsichtig, methode, warnungen}``.
        ``durchsichtig`` ist ``True``, sobald der Anteil
        :data:`MAX_DURCHSICHT_ANTEIL` überschreitet.

    Raises:
        QaError: ``soll`` und ``maske`` sind verschieden lang. Zwei Karten verschiedener
            Grösse gegeneinanderzuhalten ergäbe eine Zahl ohne Sinn — dieselbe Regel wie
            in :func:`himmel_hinter_umriss`.
    """
    werte = _als_zahlen(soll, "soll")
    m = _als_wahrheitswerte(maske, "maske")
    if len(werte) != len(m):
        raise QaError(
            f"soll und maske sind verschieden lang ({len(werte)} gegen {len(m)}). "
            f"Zwei Karten verschiedener Grösse zu vergleichen ergäbe eine Zahl ohne Sinn.")

    n_maske = sum(1 for treffer in m if treffer)
    n_durch = sum(1 for i, treffer in enumerate(m)
                  if treffer and (not math.isfinite(werte[i]) or werte[i] >= grenze_m))
    anteil = (n_durch / n_maske) if n_maske else 0.0
    durchsichtig = anteil > MAX_DURCHSICHT_ANTEIL

    warnungen = []
    if durchsichtig:
        warnungen.append(
            f"Die SOLL-Karte ist durchsichtig: An {n_durch} von {n_maske} Maskenpunkten "
            f"({anteil:.2%}) meldet der Material-ID-Pass ein Bauteil und der Tiefenpass "
            f"Hintergrund. Beide stammen aus demselben Render derselben Szene; sie können "
            f"nicht beide recht haben. Der wahrscheinliche Grund ist ein Tiefenpass MIT "
            f"Transparenz-Bounces über einem Material mit Alpha < 1 — der Strahl geht "
            f"durch die Scheibe und schreibt, was dahinter liegt. FOLGE FUER JEDE ZAHL "
            f"DIESES LAUFS: Score, Rangkorrelation und geom_iou messen dann gegen eine "
            f"Referenz, die das Bauwerk stellenweise nicht zeigt, und fallen dadurch ZU "
            f"NIEDRIG aus. Um wieviel, sagt diese Pruefung NICHT — sie zaehlt nur, wo die "
            f"Durchsicht bis zum Hintergrund durchschlaegt, nicht die vielen Punkte, die "
            f"bloss ein paar Meter zu weit hinten liegen. An dem einen nachgerechneten "
            f"Fall waren es Score 0.0000 statt 0.2001 (Demolauf 17, 03.09.2026).")
    return {
        "n_maske": n_maske,
        "n_durchsicht": n_durch,
        "anteil": anteil,
        "durchsichtig": durchsichtig,
        "methode": "maskenpunkte_ohne_endliche_solltiefe",
        "warnungen": warnungen,
    }


def _kantenstaerken(werte: list[float], breite: int, hoehe: int) -> list[float]:
    """Je Bildpunkt: wie stark sich die Tiefe zu den Nachbarn ändert.

    Grösster Betrag der Differenz zu den vier Nachbarn — nicht die Summe und nicht der
    Mittelwert. Eine Kante ist eine Richtung: Ein Punkt auf einer senkrechten Silhouette
    hat links-rechts einen Sprung und oben-unten keinen, und ein Mittelwert halbierte ihn
    genau deshalb.

    Am Bildrand fehlen Nachbarn; dort steht 0.0. Das ist kein Messwert, sondern die
    Feststellung, dass die Nachbarschaft nicht vollständig ist — und der Bildrand zählt
    ohnehin nicht als Maskengrenze (siehe :func:`_randpunkte`).
    """
    staerken = [0.0] * len(werte)
    for y in range(1, hoehe - 1):
        for x in range(1, breite - 1):
            i = y * breite + x
            hier = werte[i]
            staerken[i] = max(abs(hier - werte[i - 1]), abs(hier - werte[i + 1]),
                              abs(hier - werte[i - breite]), abs(hier - werte[i + breite]))
    return staerken


# ======================================================================================
# Das Paarurteil — beide Zahlen führen, keine verrechnen
# ======================================================================================

#: Schwelle für die gerichtete Rangkorrelation über der Maske.
#:
#: Die HomeStation schlug ``ρ ≤ −0.80`` vor (`auf-20260821-27`). Hier steht sie als
#: **gerichteter** Wert ``≥ +0.80``: Das ist dieselbe Aussage für diesen Schätzer, gilt
#: aber auch für einen mit umgekehrter Polarität. Eine Schwelle auf dem rohen ρ wäre an
#: die Konvention *eines* Schätzers gebunden, ohne das irgendwo zu sagen.
#:
#: **ABGELESEN, NICHT KALIBRIERT.** Sieben Fälle aus einer Szene. Die HomeStation sagt
#: das selbst dazu, und der Unterschied ist der, an dem dieses Projekt seit Phase 0
#: arbeitet.
#:
#: **UND SEIT DEM 08.09.2026 IST GEMESSEN, WAS SIE AUF FRONTALEN ANSICHTEN ANRICHTET —
#: nachgetragen am 19.09.2026, weil es bis dahin nur im Ergebnis stand und nicht hier.**
#: `auf-20260907-81` hat dieselbe Falltabelle mit einem echten Schätzer
#: (`depth-anything-v2-small`) statt mit der Soll-Karte gerechnet. Unter dessen Rauschen
#: gibt es **auf frontalen Ansichten kein fehlerfreies Fenster mehr**::
#:
#:     hoechster Wert eines SCHLECHTEN frontalen Falls   0,9957
#:     niedrigster Wert eines GUTEN frontalen Falls      0,1426
#:
#: Die beiden Mengen überlappen also fast vollständig; diagonal trennt das Mass weiter.
#: Mit 0.80 sperrt es **11 von 40 guten frontalen Fällen** — darunter das treue
#: Blender-Render selbst — und lässt erstmals zwei schlechte durch.
#:
#: **Was das heisst, und was es NICHT heisst.** Das Paarurteil ist kein Tor: Es sperrt
#: nichts, es schreibt einen Satz in ``verdict.reason``
#: (:func:`aiimaging.kosmo_szene`). Dieser Satz — «SCORE BESTEHT, MASKENWEG
#: WIDERSPRICHT» — ist auf frontalen Ansichten damit **zu gut einem Viertel falsch**.
#: Eine Warnung, die jedes vierte Mal grundlos kommt, wird nach der dritten nicht mehr
#: gelesen; sie ist dann schlimmer als keine.
#:
#: **Geändert wird hier trotzdem nichts, und das ist der Punkt.** `auf-20260907-81` sagt
#: über alle acht Kurven ``genuegt_als_kalibrierung: false`` — nicht wegen des Umfangs,
#: sondern wegen der Herkunft: Die Bilder kommen aus **Blender**, nicht aus dem
#: Bildmodell. Eine Schwelle an Blender-Bildern zu eichen und auf erzeugte anzuwenden
#: wäre genau der Fehler, der bei der Stil-Schwelle schon einmal gemacht wurde. Die
#: Messung an erzeugten Bildern steht als `auf-20260909-98` bei `local`.
PAAR_RHO_SCHWELLE = 0.80

#: Schwelle für die gerichtete Tiefenkante. Abgelesen (`auf-20260821-27`).
#:
#: **Sie ist am 22.08. als Tor ausgemustert worden** und steht nur noch für die Zahl, die
#: weiter mitgemessen wird. Grund (`auf-20260822-30`): Das Mass ist ein **Median** über das
#: Randband und **bricht zusammen, statt allmählich zu fallen** — zeichnet ein Bild ein
#: Viertel seines Umrisses, sieht der Median nichts. Ein Ja-Nein-Tor auf einer Grösse mit
#: dieser Eigenschaft trennt nicht, es kippt.
PAAR_KANTE_SCHWELLE = 0.05

#: Schwelle für den **Anteil der Grenze mit Kante** — das zweite Bein des Paartests.
#:
#: **Abgelesen, provisorisch, und die Zahl ist unbequem.** Gemessen (`auf-20260822-30`):
#:
#:     Zufall 5 % · qwen 2.8 % · ohne Führung 6.4 % · mit Führung 24.3 %
#:     · weichgezeichnet 43.8 % · perfektes Bild 87.4 %
#:
#: 0.20 liegt beim **Vierfachen des Zufalls** und bei **einem knappen Viertel** des
#: perfekten Bildes. Es lässt unser bestes erzeugtes Bild durch und weist das ungeführte
#: ab — aber es liegt damit sehr viel näher am Zufall als am Richtigen.
#:
#: **Das ist ausdrücklich keine Kalibrierung.** Welche Umrisstreue ein Bild haben *muss*,
#: hat niemand entschieden; die Zahl markiert nur die Lücke zwischen dem, was wir heute
#: erreichen, und dem, was gut wäre. Wer sie später senkt, weil sonst nichts besteht, hat
#: aufgegeben — wer sie hebt, verlangt bessere Bilder. Beides ist eine Entscheidung und
#: keine Messung.
PAAR_KANTENANTEIL_SCHWELLE = 0.20


def rho_gegen_gemessenen_boden(rho_gerichtet: float | None, maskenanker: dict | None, *,
                               schwelle: float = PAAR_RHO_SCHWELLE) -> dict:
    """ρ gegen den Rauschboden **dieser** Maskenlage — nicht gegen die Konstante.

    **Der Anlass ist ein Befund über unseren Schätzer** (HomeStation,
    `auf-vis-20260824-10`, 24.08.2026): `depth-anything-v2-small` hat ein **festes
    Ortsfeld**, das 95,75 % der Varianz seiner Ausgabe auf einem leeren Bild erklärt.
    Dieselbe Rauschkarte mit derselben, nur **verschobenen** Maske ergibt ρ von −0,6249
    bis +0,6513 — ein Ausschlag von 1,28 **mit Vorzeichenwechsel**.

    :data:`RAUSCHBODEN_UEBER_MASKE` ist damit keine Konstante, sondern eine Zahl für eine
    Lage. Der Abstand der Schwelle 0,80 zum Boden schwankt über verschiedene Lagen
    zwischen **0,15 und 1,42**.

    **Gemessen wird der Boden ohnehin schon** — die Nullprobe läuft je Kamera und je
    Soll-Karte (`abholer._nullprobe`). Sie wurde nur nie **gelesen**. Diese Funktion liest
    sie.

    **Der Abstand ist ein ANZEIGER und kein besseres ρ.** Am 24.08.2026 ist gemessen
    worden, dass das Ortsfeld sich **nicht additiv** auf den Inhalt legt: Alle drei
    Formen, es herauszurechnen, erhöhten die Streuung (0,1374 → 0,2882 / 0,3090 / 0,4051)
    und drehten bei bis zu 7 von 8 Bildlagen das Vorzeichen um. Wer ``abstand`` für das
    *richtigere* ρ hält, wiederholt diesen Fehler.

    Wozu er dann taugt: Eine Lage erreichte ρ 0,9318 bei einem Feldbeitrag von 0,0240,
    eine andere sah nur deshalb gut aus, weil das Feld zufällig mit der Geometrie
    übereinstimmte (r = 0,9361 über sieben Lagen). **Die Bildlage entscheidet nicht, ob
    das Mass gut sein kann, sondern ob die Zahl ehrlich ist** — und genau das sagt der
    Abstand.

    Args:
        maskenanker: ``{art: {rho, kante}}`` aus der Nullprobe **dieses** Laufs.

    Returns:
        ``{abstand, boden, boden_art, schwelle, schwelle_traegt, warnungen}``.

        * ``boden`` — der **höchste** Wert unter den Nullankern. Ein echtes Bild muss den
          besten Nullanker schlagen und nicht den bequemsten; sonst schlüge man den
          Boden, indem man sich den Anker aussucht.
        * ``schwelle_traegt`` — ``False``, wenn der gemessene Boden die Schwelle
          **erreicht oder übersteigt**. Dann lässt das Tor an dieser Maskenlage Rauschen
          durch, und das ist ein Befund über den Lauf und nicht über das Bild.
        * ``abstand`` — ``ρ − boden``. ``None``, wenn eines von beidem fehlt: **nicht
          gemessen ist nicht null.**
    """
    antwort = {"abstand": None, "boden": None, "boden_art": None, "schwelle": schwelle,
               "schwelle_traegt": None, "warnungen": []}
    boeden = {art: e.get("rho") for art, e in (maskenanker or {}).items()
              if isinstance(e, dict) and e.get("rho") is not None}
    if not boeden:
        antwort["warnungen"].append(
            "Keine Nullprobe für diese Maskenlage. ρ steht damit gegen NICHTS — und die "
            "Konstante RAUSCHBODEN_UEBER_MASKE hilft nicht, sie gilt für eine andere "
            "Lage (Ausschlag 1,28 mit Vorzeichenwechsel, auf-vis-20260824-10).")
        return antwort

    art = max(boeden, key=lambda a: boeden[a])
    boden = boeden[art]
    antwort["boden"], antwort["boden_art"] = boden, art
    antwort["schwelle_traegt"] = boden < schwelle
    if not antwort["schwelle_traegt"]:
        antwort["warnungen"].append(
            f"Der gemessene Rauschboden dieser Maskenlage liegt bei {boden:+.4f} "
            f"({art}) und damit NICHT unter der Schwelle {schwelle:.2f}. Das Tor lässt "
            f"hier Rauschen durch — ein Befund über die Kameralage, nicht über das Bild. "
            f"Abhilfe ist eine andere Maskenlage, keine andere Schwelle.")
    if rho_gerichtet is None:
        antwort["warnungen"].append(
            "ρ liegt nicht vor; der Abstand zum Boden ist damit NICHT GEMESSEN, nicht 0.")
        return antwort

    antwort["abstand"] = rho_gerichtet - boden
    # Wieviel von rho koennte allein die BILDLAGE erklaeren? Kein Tor und keine Korrektur
    # — eine Auskunft. Zwei gleich hohe rho sind verschieden viel wert, je nachdem, ob der
    # Boden an dieser Lage bei 0.02 oder bei 0.7 liegt.
    if rho_gerichtet > 0 and boden > 0:
        antwort["boden_erklaert_anteil"] = min(1.0, boden / rho_gerichtet)
        if antwort["boden_erklaert_anteil"] >= 0.5:
            antwort["warnungen"].append(
                f"Der Rauschboden dieser Maskenlage ({boden:+.4f}) erklärt bereits "
                f"{antwort['boden_erklaert_anteil']:.0%} von ρ ({rho_gerichtet:+.4f}). "
                f"Die Zahl ist damit zu einem grossen Teil eine Aussage über die BILDLAGE "
                f"und nicht über das Bild. Herausrechnen hilft nicht — das ist gemessen "
                f"und macht die Streuung grösser (24.08.2026).")
    return antwort


def paarurteil(rho_ergebnis: dict | None, kante_ergebnis: dict | None, *,
               anteil_ergebnis: dict | None = None,
               himmel_ergebnis: dict | None = None,
               rho_schwelle: float = PAAR_RHO_SCHWELLE,
               kante_schwelle: float = PAAR_KANTE_SCHWELLE,
               anteil_schwelle: float = PAAR_KANTENANTEIL_SCHWELLE) -> dict:
    """Beide Messungen zusammen — **ohne sie zu verrechnen**.

    Args:
        rho_ergebnis: Antwort von :func:`rho_ueber_maske`, oder ``None``.
        kante_ergebnis: Antwort von :func:`kante_an_maskengrenze`, oder ``None``.
        himmel_ergebnis: Antwort von :func:`himmel_hinter_umriss`, oder ``None``. Wird
            sie übergeben und trägt sie **nicht**, fällt das zweite Bein aus — nicht
            durch. Ohne sie urteilt der Paartest wie bisher; das ist die alte Form und
            keine bessere.

    Returns:
        ``{bestanden, gemessen, zustaendig, rho, kante, anteil, himmel, zweites_bein,
        traeger, schwellen, begruendung}``

        * ``bestanden`` — ``None``, solange auch nur eine der beiden Zahlen fehlt.
          **Nicht** „bestanden aufgrund der anderen": Ein Urteil aus der halben Messung
          wäre eine Behauptung über die Hälfte, die niemand angesehen hat.
        * ``zustaendig`` — ``False``, wenn hinter dem Umriss kein Himmel steht. Dann misst
          das zweite Bein nichts (siehe :data:`MIN_HIMMELANTEIL`), und der Paartest
          **schweigt statt zu bestehen**. ``rho`` steht trotzdem im Ergebnis: Das erste
          Bein ist von der Frage nicht betroffen.
        * ``traeger`` — welches Mass ein „durchgefallen" trägt: ``"rho"``, ``"kante"``,
          ``"beide"`` oder ``None``. *„ρ in Ordnung, Kante fehlt"* ist eine andere
          Diagnose als umgekehrt, und der Aufrufer soll sie unterscheiden können.

    **Kein Score, und das ist der ganze Punkt.** Kein Produkt, kein geometrisches Mittel,
    keine Verrechnung. ``sqrt(|ρ| · geom_iou)`` ist genau daran gescheitert: Es
    verschmolz **Existenz** und **Richtigkeit** zu einer Zahl, und der Faktor, der die
    Existenz beantworten sollte, belohnte am Ende die Abwesenheit — ein leeres Grundstück
    erreichte `geom_iou` 0.9848 gegen 0.9703 beim perfekten Bild (`auf-20260821-26`).

    Die beiden Masse decken **zusammen** alle vier gemessenen Halluzinationsfälle ab und
    **einzeln keiner von beiden** — gemessen gegen den jeweiligen **Rauschboden**, nicht
    gegen die Schwellen unten:

    ==========================  ========  =======  ================
    Fall                        ρ         Kante    trennt vom Boden
    ==========================  ========  =======  ================
    Bauwerk ganz weg            −0.6861   +0.0006  **Kante**
    20 m versetzt               −0.6854   +0.0007  **Kante**
    andere Kubatur              +0.3842   +0.0066  **ρ**
    90° gedreht                 −0.4546   +0.0021  **ρ**
    ==========================  ========  =======  ================

    **Diese Spalte ist genau zu lesen, sonst führt sie in die Irre.** Sie sagt, welches
    Mass den Fall vom Rauschboden (:data:`RAUSCHBODEN_UEBER_MASKE`, −0.5207) trennt: ρ
    liegt bei „Bauwerk weg" mit −0.686 zwar über dem Boden, aber so knapp, dass es nichts
    belegt — die Kante dagegen fällt von +0.1615 auf +0.0006, um mehr als zwei
    Zehnerpotenzen. Gegen die **Schwellen** dieser Funktion fallen H1 und H2 auch an ρ
    durch, weil ``0.80`` strenger ist als der Rauschboden. Beides ist wahr und meint
    Verschiedenes: Die Spalte beschreibt, was ein Mass **unterscheiden kann**, die
    Schwelle, was es **durchlässt**.

    **Und beide Spalten gelten nur, wo Himmel hinter dem Umriss steht.** Alle vier Fälle
    oben sind an einer freistehenden Szene gemessen. Steht dort ein Nachbargebäude, fällt
    das zweite Bein von +0,4227 auf +0,0016 und trennt das perfekte Bild nicht mehr von
    weissem Rauschen — nicht weil das Bild schlechter wäre, sondern weil ein monokularer
    Schätzer zwei Betonkörper in 34 und 49 m nicht auseinanderlegt (`auf-vis-20260823-07`,
    siehe :data:`MIN_HIMMELANTEIL`). Darum fragt ``himmel_ergebnis`` **vor** dem Urteil,
    ob hier überhaupt gemessen werden kann. Nicht messbar ist nicht dasselbe wie schlecht
    — und ein grünes Abzeichen wäre dort in die gefährliche Richtung falsch.

    **Und die Grenze hängt am Mass, nicht an der Szene.** Der Schätzer ordnet auch dort
    richtig; nur der *Betrag* wird gestaucht. Ein rangbasiertes zweites Bein bräuchte
    ``himmel_ergebnis`` darum nicht — wer eines einbaut, prüft diese Grenze mit
    (`auf-vis-20260823-08`).

    .. warning::
       **Bis zum 22.08.2026 stand hier: „Dieser Paartest würde jedes Bild abweisen, das
       dieses Projekt je erzeugt hat." Das ist gemessen widerlegt, und zwar am selben
       Tag.**

       Der Satz stützte sich auf fünf erzeugte Bilder, die über der Maske alle schlechter
       lagen als weisses Rauschen (:data:`RAUSCHBODEN_UEBER_MASKE`, −0.5207). Die
       Seed-Messung (`docs/SEEDAUSWAHL_2026-08-22.md`) zeigt: Derselbe Aufbau liefert je
       nach Startwert **0.4152 bis 0.9139** — und 0.9139 liegt **über**
       :data:`PAAR_RHO_SCHWELLE`. Erreichbar ist die Schwelle also; nur nicht
       zuverlässig.

       **Damit hat sich die Frage verschoben, nicht erledigt.** Die Seed-Streuung
       (0.2269) ist grösser als jeder gemessene Parametereffekt (0.10–0.14). Die Frage
       lautet nicht mehr *„ist die Schwelle erreichbar"*, sondern *„warum liefert derselbe
       Aufbau einmal 0.91 und einmal 0.42"* — und die ist offen.

       Was unverändert gilt: Wer die Schwelle senkt, weil sonst nichts besteht, hat nicht
       kalibriert, sondern aufgegeben. Eine Auswahl unter mehreren Startwerten ist etwas
       anderes als eine gesenkte Schwelle — sie macht keine besseren Bilder, sondern
       findet das bessere unter denselben.
    """
    rho = (rho_ergebnis or {}).get("gerichtet")
    kante = (kante_ergebnis or {}).get("gerichtet")
    anteil = (anteil_ergebnis or {}).get("anteil")
    # Das zweite Bein ist seit dem 22.08. der ANTEIL und nicht mehr die Median-Kante.
    # Liegt kein Anteil vor, fällt der Test auf die alte Form zurück — mit einem Satz
    # dazu, denn die alte Form kippt statt zu trennen.
    zweites_bein = "anteil" if anteil is not None else "kante"
    # Zuständigkeit VOR Messung: Steht hinter dem Umriss kein Himmel, misst das zweite
    # Bein nichts — dann darf hier kein Urteil stehen, auch kein schlechtes.
    himmel_anteil = (himmel_ergebnis or {}).get("anteil")
    zustaendig = True if himmel_ergebnis is None else bool(himmel_ergebnis.get("traegt"))
    antwort = {
        "bestanden": None, "gemessen": False, "zustaendig": zustaendig,
        "rho": rho, "kante": kante,
        "anteil": anteil, "himmel": himmel_anteil,
        "zweites_bein": zweites_bein, "traeger": None,
        "schwellen": {"rho": rho_schwelle, "kante": kante_schwelle,
                      "anteil": anteil_schwelle, "himmel": MIN_HIMMELANTEIL},
        "begruendung": "",
    }

    if not zustaendig:
        rho_wort = "liegt nicht vor" if rho is None else f"steht bei {rho:+.4f}"
        antwort["begruendung"] = (
            f"NICHT ZUSTÄNDIG: Hinter dem Umriss steht zu wenig Himmel "
            f"({himmel_anteil:.1%} der äusseren Randpunkte, verlangt sind "
            f"{MIN_HIMMELANTEIL:.0%}). Das zweite Bein misst dort den Sprung zwischen "
            f"Fassade und Nachbargebäude — und ein monokularer Schätzer legt zwei "
            f"Betonkörper in 34 und 49 m praktisch nicht auseinander "
            f"(auf-vis-20260823-07: +0.0016 gegen einen Rauschanker von −0.0024). "
            f"Ein Urteil aus dieser Zahl wäre in die gefährliche Richtung falsch. "
            f"ρ über der Maske ist davon nicht betroffen und {rho_wort}; es beantwortet "
            f"aber die Existenzfrage nicht und ersetzt das zweite Bein nicht.")
        return antwort

    zweiter_wert = anteil if zweites_bein == "anteil" else kante
    zweiter_name = ("Anteil der Grenze mit Kante" if zweites_bein == "anteil"
                    else "Tiefenkante (Median)")
    fehlt = [n for n, w in (("ρ über der Maske", rho), (zweiter_name, zweiter_wert))
             if w is None]
    if fehlt:
        antwort["begruendung"] = (
            f"NICHT GEMESSEN: {' und '.join(fehlt)} liegt nicht vor. Ein Urteil aus der "
            f"halben Messung wäre eine Behauptung über die Hälfte, die niemand angesehen "
            f"hat — und die beiden Masse beantworten verschiedene Fragen: ρ die "
            f"Richtigkeit, die Kante die Existenz. Für die fehlende gibt es keinen "
            f"Ersatz.")
        return antwort

    schwelle_zwei = anteil_schwelle if zweites_bein == "anteil" else kante_schwelle
    rho_ok = rho >= rho_schwelle
    zwei_ok = zweiter_wert >= schwelle_zwei
    antwort["gemessen"] = True
    antwort["bestanden"] = rho_ok and zwei_ok
    if not rho_ok and not zwei_ok:
        antwort["traeger"] = "beide"
    elif not rho_ok:
        antwort["traeger"] = "rho"
    elif not zwei_ok:
        antwort["traeger"] = zweites_bein

    teile = [f"ρ (gerichtet) {rho:+.4f} gegen {rho_schwelle:.2f} — "
             f"{'in Ordnung' if rho_ok else 'ZU NIEDRIG'}",
             f"{zweiter_name} {zweiter_wert:+.4f} gegen {schwelle_zwei:.2f} — "
             f"{'in Ordnung' if zwei_ok else 'ZU NIEDRIG'}"]
    if zweites_bein == "kante":
        teile.append("ACHTUNG: Als zweites Bein dient die Median-Kante, weil kein Anteil "
                     "vorliegt. Sie KIPPT, statt zu trennen (auf-20260822-30) — dieses "
                     "Urteil ist schwächer als eines mit Anteil")
    if antwort["bestanden"]:
        schluss = "Beide Masse tragen."
    elif antwort["traeger"] in ("kante", "anteil"):
        schluss = ("Die Tiefenstaffelung stimmt, aber an der Silhouettengrenze steht kein "
                   "Sprung — das Muster eines Bildes, in dem das Bauwerk FEHLT oder "
                   "anderswo steht.")
    elif antwort["traeger"] == "rho":
        schluss = ("An der Grenze steht ein Sprung, aber die Tiefen dahinter stimmen "
                   "nicht — das Muster einer FALSCHEN Kubatur am richtigen Ort.")
    else:
        schluss = "Beide Masse fallen durch."
    antwort["begruendung"] = " · ".join(teile) + " · " + schluss + (
        "  [Schwellen ABGELESEN an sieben Fällen aus einer Szene (auf-20260821-27), "
        "nicht kalibriert.]")
    return antwort


#: Was an **gemessenen** Punkten aus dem Maskenanteil wird — die Rahmungsmessung.
#:
#: **Gemessen** (HomeStation, 24.08.2026): ein Quader 15,36 × 10,36 × 6,0 m auf einer
#: Platte mit **zehnfacher** Grundfläche, ein Startwert, eine Ansicht, vier Abstände:
#:
#:     anteil_maske 0.0193  →  geom_iou 0.000183   (`cameras: auto`, 90,6 m)
#:     anteil_maske 0.0565  →  geom_iou 0.0        (55,0 m)
#:     anteil_maske 0.1565  →  geom_iou 0.00144    (35,1 m)
#:     anteil_maske 0.3051  →  geom_iou 0.9323     (26,6 m) — Score 0.9599, **bestanden**
#:
#: **Der Sprung zwischen den letzten beiden ist Faktor 647** — aber *«eine Schwelle, keine
#: Rampe»* war zu grob, und zwar von beiden Seiten korrigiert.
#:
#: **Feiner nachgemessen** (HomeStation, Nachtrag vom 24.08.2026) ist es eine **Rampe mit
#: Knie**: Der Score steigt ab rund 0,50 Bildbreite, überschreitet die Schwelle zwischen
#: **0,5991 und 0,6488** und liegt linear bei 0,61. Der Faktor 647 war eine Folge der
#: groben Abstufung — vier Punkte über einen weiten Bereich sehen wie ein Sprung aus, wenn
#: das Knie zwischen zwei von ihnen liegt.
#:
#: **Warum trotzdem nicht interpoliert wird:** Eine Rampe mit Knie ist keine Gerade, und
#: die vier Punkte hier liegen beidseits des Knies. Die feinen Zahlen oben stehen in
#: *Bildbreite*, die Tabelle hier in *Maskenanteil* — die beiden ineinander umzurechnen
#: verlangt die Szene, und dann wäre es keine Tabelle mehr, sondern ein Modell.
#:
#: Damit ist die Behauptung widerlegt, :data:`SCHWELLE_GEOMETRIE` sei arithmetisch
#: unerreichbar. Sie ist es **bei der Rahmung, die `cameras: auto` erzeugt** — und das ist
#: etwas ganz anderes, weil es sich beheben lässt, ohne eine Schwelle zu senken.
#:
#: **Die Tabelle ist eine Stichprobe: eine Szene, ein Startwert, eine Ansicht.** Sie sagt,
#: was dort herauskam, und nicht, was allgemein gilt. :func:`torchance` gibt darum
#: ausserhalb der gemessenen Punkte ``None`` zurück, statt zu interpolieren.
RAHMUNG_GEMESSEN = (
    (0.0193, 0.000183),
    (0.0565, 0.0),
    (0.1565, 0.00144),
    (0.3051, 0.9323),
)

#: Unterhalb dieses Maskenanteils ist **gemessen**, dass das Tor nicht besteht.
#: Der grösste gemessene Punkt ohne Bestehen — nicht ein Wert dazwischen.
ANTEIL_MASKE_GEMESSEN_ZU_KLEIN = 0.1565

#: Ab diesem Maskenanteil ist **gemessen**, dass das Tor bestehen kann.
ANTEIL_MASKE_GEMESSEN_REICHT = 0.3051


def torchance(anteil_maske: float | None) -> dict:
    """Kann das Geometrie-Tor bei diesem Maskenanteil überhaupt bestehen? — **vor** dem Lauf.

    **Warum das eine eigene Frage ist.** Ein Renderlauf, der nicht bestehen *kann*, ist
    keine schlechte Nachricht über das Bildmodell — er ist verlorene Rechenzeit und ein
    irreführendes Urteil obendrein. Die Frage ist aus der Kameraaufstellung allein
    beantwortbar, also **bevor** eine GPU anläuft.

    Returns:
        ``{lage, anteil_maske, gemessen_zu_klein, gemessen_reicht, begruendung}``.

        ``lage`` ist ``"zu_klein"``, ``"reicht"`` oder ``None``. **``None`` heisst: liegt
        zwischen den gemessenen Punkten oder darüber** — dort steht nichts Gemessenes, und
        zu interpolieren hiesse, eine Kurve durch vier Punkte einer einzigen Szene zu
        legen. Der Sprung dazwischen beträgt Faktor 647; eine Gerade dadurch wäre keine
        Schätzung, sondern eine Erfindung.
    """
    antwort = {"lage": None, "anteil_maske": anteil_maske,
               "gemessen_zu_klein": ANTEIL_MASKE_GEMESSEN_ZU_KLEIN,
               "gemessen_reicht": ANTEIL_MASKE_GEMESSEN_REICHT, "begruendung": ""}
    if anteil_maske is None:
        antwort["begruendung"] = (
            "Kein Maskenanteil bekannt — die Frage ist NICHT BEANTWORTET und nicht "
            "verneint.")
        return antwort

    wert = float(anteil_maske)
    if wert <= ANTEIL_MASKE_GEMESSEN_ZU_KLEIN:
        antwort["lage"] = "zu_klein"
        antwort["begruendung"] = (
            f"Maskenanteil {wert:.4f} liegt bei oder unter {ANTEIL_MASKE_GEMESSEN_ZU_KLEIN}, "
            f"wo GEMESSEN kein Tor besteht (geom_iou 0.00144 und darunter). Das ist kein "
            f"Urteil über das Bild: Bei dieser Rahmung KANN es nicht bestehen. Abhilfe ist "
            f"eine nähere Kamera, keine gesenkte Schwelle — bei 0.3051 entstand ein Score "
            f"von 0.9599. Der Anstieg dazwischen ist eine Rampe mit Knie, kein "
            f"gleichmässiges Steigen: Bestellempfehlung ist 0.70 Bildbreite, nicht 0.65.")
        return antwort
    if wert >= ANTEIL_MASKE_GEMESSEN_REICHT:
        antwort["lage"] = "reicht"
        antwort["begruendung"] = (
            f"Maskenanteil {wert:.4f} liegt bei oder über {ANTEIL_MASKE_GEMESSEN_REICHT}, "
            f"wo GEMESSEN ein Tor bestanden hat (geom_iou 0.9323). Die Rahmung steht der "
            f"Messung nicht im Weg; über das Bild sagt das nichts.")
        return antwort

    antwort["begruendung"] = (
        f"Maskenanteil {wert:.4f} liegt ZWISCHEN den gemessenen Punkten "
        f"({ANTEIL_MASKE_GEMESSEN_ZU_KLEIN} und {ANTEIL_MASKE_GEMESSEN_REICHT}). Dort "
        f"steht nichts Gemessenes. Der Anstieg dazwischen ist eine RAMPE MIT KNIE, und "
        f"die vier Punkte liegen beidseits davon — eine Gerade hindurchzulegen wäre keine "
        f"Schätzung, sondern eine Erfindung. NICHT BEANTWORTET.")
    return antwort


def noetiges_iou(schwelle: float = SCHWELLE_GEOMETRIE,
                 spearman: float = SPEARMAN_BESTENFALLS) -> float:
    """Welches ``geom_iou`` eine Schwelle bei gegebener Rangkorrelation verlangt.

    Reine Umstellung von ``score = sqrt(|rho| * iou)`` nach ``iou``. Der Nutzen liegt
    nicht in der Formel, sondern darin, sie **vor** dem Rechnen anzuwenden: Eine Schwelle,
    die mehr Überdeckung verlangt, als die Szene hergibt, ist kein strenges Gate — sie ist
    gar keines.

    Raises:
        QaError: Schwelle ausserhalb ``[0, 1]`` oder Rangkorrelation nicht positiv.
    """
    if not (0.0 <= schwelle <= 1.0):
        raise QaError(f"Schwelle muss in [0,1] liegen, war {schwelle}.")
    if not (0.0 < abs(spearman) <= 1.0):
        raise QaError(
            f"|spearman| muss in (0,1] liegen, war {spearman}. Bei 0 wäre der Score "
            f"immer 0, und die Frage nach dem nötigen iou hätte keine Antwort."
        )
    return schwelle ** 2 / abs(spearman)


def erreichbarkeit(*, iou_deckel: float, schwelle: float = SCHWELLE_GEOMETRIE,
                   spearman: float = SPEARMAN_BESTENFALLS, name: str = "diese Szene") -> dict:
    """Kann eine Szene die Schwelle **überhaupt** erreichen? — vor dem ersten Renderlauf.

    Args:
        iou_deckel: das beste ``geom_iou``, das diese Szene mit dieser
            Hintergrundstrategie an einem *gerenderten* Bild erreicht. Aus
            :data:`IOU_DECKEL` oder selbst gemessen.
        spearman: das bestenfalls erreichbare ``|spearman|``.

    Returns:
        ``{erreichbar, hoechster_score, noetiges_iou, luecke, begruendung}``.

    **Wozu das gut ist.** Eine GPU-Stunde, die ein Bild erzeugt, das die Schwelle gar
    nicht erreichen *kann*, misst nicht das Bild, sondern die Szene. Diese Prüfung kostet
    nichts und hätte den Unterschied gemerkt, bevor er drei Aufträge gekostet hat.
    """
    if not (0.0 <= iou_deckel <= 1.0):
        raise QaError(f"iou_deckel muss in [0,1] liegen, war {iou_deckel}.")
    noetig = noetiges_iou(schwelle, spearman)
    hoechster = math.sqrt(abs(spearman) * iou_deckel)
    erreichbar = hoechster >= schwelle

    if erreichbar:
        grund = (
            f"{name}: Deckel geom_iou {iou_deckel:.4f} bei |spearman| {abs(spearman):.3f} "
            f"ergibt höchstens {hoechster:.4f} — die Schwelle {schwelle:.2f} ist "
            f"erreichbar. Ob ein erzeugtes Bild sie erreicht, sagt das NICHT; es sagt "
            f"nur, dass die Frage sinnvoll ist."
        )
    else:
        grund = (
            f"{name}: Deckel geom_iou {iou_deckel:.4f} bei |spearman| {abs(spearman):.3f} "
            f"ergibt höchstens {hoechster:.4f} — die Schwelle {schwelle:.2f} ist auf "
            f"dieser Szene UNERREICHBAR. Nötig wären {noetig:.4f}, es fehlen "
            f"{noetig - iou_deckel:.4f}.\n"
            f"Ein Lauf gegen diese Schwelle misst dann nicht das Bild, sondern die Szene. "
            f"Ein durchgefallenes Bild belegt hier NICHTS über seine Geometrietreue."
        )
    return {
        "erreichbar": erreichbar,
        "hoechster_score": hoechster,
        "noetiges_iou": noetig,
        "luecke": max(0.0, noetig - iou_deckel),
        "begruendung": grund,
    }


def erreichbarkeit_fuer(szene: str, strategie: str, **kw) -> dict | None:
    """:func:`erreichbarkeit` für eine Szenenart aus :data:`IOU_DECKEL`.

    Gibt **``None``** für eine Kombination, die nicht gemessen ist — und **nicht** eine
    Schätzung aus einer benachbarten Zeile. Ein geratener Deckel wäre genau die Sorte
    Zahl, gegen die dieses Modul antritt: eine, die eine Frage beantwortet, die sie nicht
    beantworten kann.
    """
    deckel = IOU_DECKEL.get((szene, strategie))
    if deckel is None:
        return None
    return erreichbarkeit(iou_deckel=deckel, name=f"{szene}/{strategie}", **kw)



# ======================================================================================
# Nullanker — was ein Score wert ist, hängt davon ab, was NICHTS erreicht
# ======================================================================================

#: Was Bilder **ohne jede Geometrie** auf derselben Soll-Karte erreichen.
#:
#: **Der wichtigste Befund dieses Moduls, und er kam von einer Nullprobe, die niemand
#: verlangt hatte** (`auf-20260820-21`, 20.08.2026). Szene ``platte_endlich``,
#: 59,8 % Geometrieanteil, dieselbe Soll-Karte, dieselbe Kette — vier Bilder, die **nicht**
#: aus dem Modell stammen:
#:
#: ===========================  =======  ==========  ============
#: Kontrollbild                 Score    ``iou``     ``|rho|``
#: ===========================  =======  ==========  ============
#: Beauty (perfekte Geometrie)  0.9839   0.970       0.998
#: **weisses Rauschen**         **0.7217**  0.568    0.917
#: leeres Graubild              0.5188   0.303       0.889
#: strukturloser Verlauf        0.3483   0.291       0.417
#: ===========================  =======  ==========  ============
#:
#: **Weisses Rauschen besteht das Gate von 0.65.** Und es schlägt jeden der fünf echten
#: Läufe derselben Messung (0.471 … 0.657).
#:
#: Der Grund ist bekannt und liegt nicht am Rauschen: Ein monokularer Schätzer legt in
#: **jedes** Bild eine zum Horizont laufende Bodenebene (`auf-20260818-10`). Eine Szene,
#: die zu 60 % aus Boden besteht, **ist** im Wesentlichen so eine Rampe — die
#: Rangkorrelation misst dann die Übereinstimmung zweier Bodenrampen und nicht die des
#: Bauwerks.
#:
#:     Auf einer Szene mit viel Boden misst die Kette nicht mehr das Bauwerk, sondern die
#:     Bodenrampe.
#:
#: Das ist dieselbe Lage wie bei der Stil-Schwelle vom 18.08.: Dort liess 0.30 jedes
#: beliebige Bildpaar durch, bis der Boden von SigLIP 2 bei 0.526 gemessen war. Ein Gate
#: ohne Nullprobe ist kein Gate.
#: **Nachtrag 20.08.2026 abends** (`auf-20260820-22`): Bei **29,1 %** Geometrieanteil
#: besteht weisses Rauschen das Gate **nicht** mehr (0.2546) — aber das perfekte Bild auch
#: nicht (0.4149). Und der Zusammenhang ist **nicht monoton**:
#:
#: ================  =========  ==========  ===================
#: Geometrieanteil   perfekt    Rauschen    Verhältnis
#: ================  =========  ==========  ===================
#: 17 %              0.504      —           —
#: **29,1 %**        **0.415**  **0.255**   **1.63**
#: 59,8 %            0.984      0.722       1.36
#: ================  =========  ==========  ===================
#:
#: Die Mitte hat die **niedrigste Decke von dreien** und trotzdem die **beste Trennung**.
#: „Zwischen den beiden Fehlerbereichen liegt der gute Bereich" war damit zu einfach
#: gedacht — es gibt keinen Anteil, bei dem beides zugleich stimmt.
#:
#: **Was daraus folgt, ist die eigentliche Konsequenz dieses Moduls:** Eine *feste*
#: Schwelle kann es nicht geben. Decke und Boden schwanken je Szene um mehr als das
#: Doppelte. Die szenenunabhängige Grösse ist der **Anteil der Spanne** —
#: ``(score − rauschen) / (perfekt − rauschen)`` — und den rechnet :func:`einordnung`.
NULLANKER = {
    "platte_endlich": {
        "beauty": 0.9839,
        "rauschen": 0.7217,
        "grau": 0.5188,
        "verlauf": 0.3483,
    },
    # 11-m-Platte, 29,1 % Geometrieanteil. `grau` und `verlauf` sind dort gar nicht
    # messbar (n_gemeinsam 0) — auch das trennt, und es fehlt hier darum, statt als Null
    # zu erscheinen.
    "platte_11m": {
        "beauty": 0.4149,
        "rauschen": 0.2546,
    },
}

#: Der Name des Ankers, gegen den ein Score sich behaupten muss.
#: Weisses Rauschen ist der härteste der drei geometriefreien — und der einzige, der das
#: Gate besteht.
ANKER_RAUSCHEN = "rauschen"


def einordnung(score: float | None, anker: dict | None, *,
               schwelle: float = SCHWELLE_GEOMETRIE) -> dict:
    """Wo liegt ein Score zwischen **nichts** und **perfekt**?

    Ein Score allein sagt wenig. Er sagt erst etwas, wenn danebensteht, was ein Bild
    **ohne jede Geometrie** auf derselben Soll-Karte erreicht — und was ein perfektes
    erreicht.

    Args:
        anker: Ein Eintrag aus :data:`NULLANKER` oder ein eigener mit denselben
            Schlüsseln. ``None`` heisst: Für diese Szene ist keine Nullprobe gefahren.

    Returns:
        ``{ueber_rauschen, ueber_gate, anteil_der_spanne, anteil_gilt, begruendung}``.

        ``ueber_rauschen`` ist die Aussage, die **trägt**: Erreicht dieses Bild auf dieser
        Soll-Karte mehr als eines ganz ohne Geometrie? Ein Vergleich innerhalb einer
        Szene, kein Abstand — und darum von der Nicht-Monotonie des Scores nicht
        betroffen.

        ``anteil_der_spanne`` ist ``(score − rauschen) / (beauty − rauschen)``.

        .. warning::
           **Diese Grösse ist am 20.08.2026 widerlegt worden** (`auf-20260820-23`,
           `docs/EMPFINDLICHKEIT_2026-08-20.md`), und zwar in beiden Behauptungen, die
           sie einmal trug:

           * *Sie sei szenenunabhängig.* Ist sie nicht. Dieselbe Verschiebung von 1 m
             ergibt bei 29 % Geometrieanteil rund 0.40, bei 59.8 % rund 0.92 — Faktor 2,3.
           * *Sie messe den Abstand vom Richtigen.* Tut sie nicht. Der zugrunde liegende
             Score ist nicht monoton im geometrischen Fehler; eine lineare Umrechnung
             erbt den Knick unverändert. Zwei verschiedene Fehler ergeben denselben
             Anteil, und der grössere von beiden kann der bessere sein.

           Sie wird weiter **gerechnet**, weil sie eine nachvollziehbare Ableitung aus
           zwei gemessenen Ankern ist und in älteren Ergebnissen steht. Sie wird nicht
           mehr **gedeutet**. ``anteil_gilt`` ist deshalb immer ``False``: Das Feld sagt
           dem Aufrufer, dass er die Zahl nicht als Güte lesen darf, statt darauf zu
           hoffen, dass er den Docstring liest.

    **Ohne Anker gibt es keine Einordnung, sondern die Feststellung, dass keine vorliegt.**
    Eine geschätzte Einordnung wäre schlimmer als keine — sie sähe aus wie ein Urteil.
    """
    if score is None:
        return {"ueber_rauschen": None, "ueber_gate": None, "anteil_der_spanne": None,
                "anteil_gilt": False,
                "begruendung": "Kein Score — es gibt nichts einzuordnen."}
    if not anker or ANKER_RAUSCHEN not in anker:
        return {"ueber_rauschen": None, "ueber_gate": score >= schwelle,
                "anteil_der_spanne": None, "anteil_gilt": False, "begruendung": (
                    f"Score {score:.4f} gegen Schwelle {schwelle:.2f} — aber für diese "
                    f"Szene ist KEINE Nullprobe gefahren. Ohne sie ist nicht bekannt, was "
                    f"ein Bild ohne jede Geometrie hier erreicht; auf einer anderen Szene "
                    f"waren das {NULLANKER['platte_endlich'][ANKER_RAUSCHEN]:.4f}, also "
                    f"mehr als das Gate. Der Score ist damit nicht eingeordnet.")}

    rauschen = float(anker[ANKER_RAUSCHEN])
    beauty = float(anker.get("beauty", 1.0))
    spanne = beauty - rauschen
    anteil = (score - rauschen) / spanne if abs(spanne) > 1e-12 else None
    ueber = score > rauschen

    if ueber:
        grund = (f"Score {score:.4f} liegt über dem Rauschanker {rauschen:.4f} — er trägt "
                 f"also mehr als ein Bild ohne jede Geometrie auf derselben Soll-Karte. "
                 f"DAS ist die Aussage, und weiter reicht sie nicht.\n"
                 f"Zum perfekten Bild dieser Szene ({beauty:.4f}) verhält er sich wie "
                 f"{anteil:.1%} der Spanne. Diese Zahl ist am 20.08.2026 widerlegt worden "
                 f"(auf-20260820-23) und steht hier nur noch als Ableitung, nicht als "
                 f"Urteil: Sie ist weder szenenunabhängig (dieselbe Verschiebung ergab in "
                 f"zwei Szenen 0.40 gegen 0.92) noch ein Abstand vom Richtigen (der Score "
                 f"darunter ist nicht monoton im Fehler). Wer sie als Güte liest, liest "
                 f"sie falsch.")
    else:
        grund = (
            f"Score {score:.4f} liegt UNTER dem Rauschanker {rauschen:.4f}. Auf derselben "
            f"Soll-Karte erreicht weisses Rauschen mehr. Ein Wert, den Rauschen "
            f"übertrifft, belegt keine Geometrietreue — auch dann nicht, wenn er die "
            f"Schwelle {schwelle:.2f} überschreitet.\n"
            f"Der Grund liegt an der Szene und nicht am Bild: Ein monokularer Schätzer "
            f"legt in jedes Bild eine Bodenrampe, und eine Szene mit viel Boden ist im "
            f"Wesentlichen so eine Rampe. Gemessen am 20.08.2026 (auf-20260820-21)."
        )
    return {"ueber_rauschen": ueber, "ueber_gate": score >= schwelle,
            "anteil_der_spanne": anteil, "anteil_gilt": False, "begruendung": grund}


def anker_fuer(szene: str) -> dict | None:
    """Die Nullprobe einer Szene, oder ``None``. **Keine Schätzung aus einer anderen.**"""
    return NULLANKER.get(szene)


# ======================================================================================
# Lücken-Trennung — wo die Ferne aufhört, weiss nur das Bild
# ======================================================================================
#
# **Der Anlass** (HomeStation, 11.09.2026, an einem echten Innenraum gemessen): Um aus
# einer Tiefenkarte die Ferne abzutrennen, wurde über das 99er-Perzentil normiert. Das
# Ergebnis war flach — Mittel 0.9869, 98.7 % der Punkte über 0.99 —, weil die
# Fernsichtebene 1.13 % der Fläche einnahm, also MEHR als das eine Prozent, das ein
# 99er-Perzentil wegschneidet. Ein festes Perzentil setzt voraus, dass man vorher weiss,
# wie viel Ferne im Bild steht.
#
#     „Wie viel Himmel im Bild steht, weiss nur das Bild."
#
# Was stattdessen trägt, steht in derselben Messung: Die Verteilung ist **zweigipflig**.
# 98.6 % der Punkte lagen zwischen 1.75 m und 10 m, 1.13 % bei 1600 m — und zwischen
# 146 m und 1000 m lag KEIN EINZIGER Punkt. Diese Lücke ist im Bild selbst vorhanden,
# unabhängig davon, wie gross die Ferne ausfällt.

#: Ab welchem VERHÄLTNIS zweier benachbarter Tiefenwerte eine Lücke als Trennung gilt.
#:
#: **Warum ein Verhältnis und kein Abstand in Metern.** Absolut gemessen wäre ein Sprung
#: bei 1600 m immer grösser als einer bei 5 m; der Wächter fände dann in jeder
#: Aussenansicht dieselbe Lücke ganz hinten und nie die, die das Bild teilt. Ein
#: Verhältnis ist zudem massstabsfrei: dieselbe Szene in Zentimetern ergibt dieselbe
#: Trennung.
#:
#: **Warum der Wert 3.0 ist.** Er muss zwei gemessene Zahlen trennen: Die echten Lücken
#: des Innenraums vom 11.09.2026 lagen bei Faktor 14.5 (10 m → 145 m) und Faktor 11
#: (145.5 m → 1600 m). Eine GLEICHMÄSSIGE Verteilung ohne Loch bleibt weit darunter —
#: bei 200 Punkten zwischen 1.75 m und 10 m beträgt der grösste Nachbarsprung 1.024,
#: denn der Abstand ist dort konstant (0.041 m) und das Verhältnis damit höchstens
#: 1 + 0.041/1.75. Faktor 3 liegt zwischen beidem, und zwar nicht knapp: Er verlangt,
#: dass hinter einem Punkt ein Bereich doppelt so breit wie dessen eigener Abstand
#: vollständig leer ist. Das ist keine kalibrierte Schwelle, sondern eine begründete —
#: eine Messreihe über mehrere Räume steht aus.
MINDEST_LUECKEN_VERHAELTNIS = 3.0

#: Welcher Anteil der betrachteten Punkte mindestens UNTERHALB einer Lücke liegen muss,
#: damit sie als Trennung in Frage kommt.
#:
#: Ohne diesen Riegel entschiede ein einziger Ausreisser nach vorn: Ein Punkt bei 0.001 m
#: vor einem Raum ab 1.75 m ergäbe das Verhältnis 1750 — den grössten Sprung der ganzen
#: Karte — und die Obergrenze läge bei 0.001 m. Die Ferne wird hinten abgetrennt, nicht
#: vorne; der Kern ist die Mehrheit. Der Riegel wirft die Lücke aus der AUSWAHL, er
#: verwirft nicht die Karte: Eine echte Trennung weiter hinten wird weiterhin gefunden.
MINDEST_KERN_ANTEIL = 0.5


def ferne_abtrennen(karte: Sequence[float], *, stufen: int = 1,
                    mindest_verhaeltnis: float = MINDEST_LUECKEN_VERHAELTNIS,
                    hintergrund_grenze: float = HINTERGRUND_SCHWELLE_M) -> dict:
    """Die Obergrenze einer Tiefenkarte aus ihrer eigenen **Lücke**, nicht aus einem Perzentil.

    Gesucht wird der grösste **Verhältnis**-Sprung zwischen zwei benachbarten Werten der
    sortierten Verteilung. Er trennt dort, wo das Bild selbst nichts hat.

    **Warum die zweite Stufe nicht von selbst läuft** (gemessen 16.09.2026, und die
    Messung hat den ursprünglichen Entwurf umgeworfen). Der Gedanke war: Eine Lücke trennt
    eine Ferne ab, nicht jede — nach der Fernsichtebene blieben am 11.09.2026 noch die
    Nachbarhäuser bis 145 m übrig, und die kosteten fast den ganzen Wertebereich. Eine
    zweite Stufe sollte darum immer die nächste Lücke darunter suchen.

    Nachgerechnet trägt das nicht, aus zwei Gründen:

    1. **Die erste Stufe findet den Fall vom 11.09.2026 schon selbst.** Gewählt wird der
       GRÖSSTE Verhältnis-Sprung, nicht der hinterste. Innenraum → Nachbarhäuser ist
       Faktor 14.5, Nachbarhäuser → Fernsichtebene nur Faktor 11 — die erste Stufe landet
       also direkt bei 10 m, und der Kern nutzt 100 % des Wertebereichs. Die zweite Stufe
       ändert an diesem Fall **nichts**.
    2. **Wo sie etwas ändert, nimmt sie Bauwerk weg.** Nachgestellte Aussenansicht
       (Bauwerk 5–15 m, echte Nachbarzeile 60–64 m, Himmel)::

           stufen=1 → Obergrenze 63.95 m, geklemmt  4.4 %   (die Nachbarzeile bleibt)
           stufen=2 → Obergrenze 14.99 m, geklemmt 11.5 %   (die Nachbarzeile ist weg)

       Beide Male ist die Lücke echt. Ob der Klumpen bei 60 m eine Fernsichtebene ist oder
       ein Nachbargebäude, steht **nicht in der Tiefenkarte** — es ist ein Entscheid über
       den Bildinhalt, und dieses Modul hat ihn nicht zu treffen.

    Darum ist ``stufen=1`` die Voreinstellung. Wer mehr will, bekommt mit ``kanten`` alle
    gefundenen Trennungen und in ``warnungen`` den Satz, wie viel die späteren Stufen
    zusätzlich wegnehmen — die Wahl bleibt beim Aufrufer und wird nicht hier versteckt.

    Hintergrundmarken (``≥ hintergrund_grenze``) werden **vorher ausgelassen**: Sie sind
    eine Konstante des Renderers und keine Tiefe. Nähme man sie mit, wäre die grösste
    Lücke der Karte immer der Sprung auf diese Marke — der Wächter fände also stets
    dasselbe und nie das Bild. Aus demselben Grund fliegen Werte ``≤ 0`` heraus: Ein
    Verhältnis gegen null ist keine Zahl.

    Args:
        karte: Tiefenwerte in beliebiger, aber einheitlicher Längeneinheit.
        stufen: Wie viele Lücken nacheinander gesucht werden, jede unterhalb der
            vorigen. Mindestens 1.
        mindest_verhaeltnis: Ab welchem Sprung eine Lücke als Trennung gilt
            (:data:`MINDEST_LUECKEN_VERHAELTNIS`).
        hintergrund_grenze: Ab hier gilt ein Wert als Marke, nicht als Tiefe.

    Returns:
        ``{obergrenze, stufen_gefunden, kanten, anteil_geklemmt, anteil_wertebereich,
        verhaeltnis, n_gemessen, n_ausgelassen, warnungen}``.

        ``kanten`` sind alle gefundenen Trennungen in der Reihenfolge ihrer Stufen, von
        aussen nach innen. Mit ``stufen=1`` steht dort genau ein Wert.

        ``obergrenze`` ist ``None``, wenn KEINE taugliche Lücke gefunden wurde. Das heisst
        **NICHT GEMESSEN** — weder „keine Ferne“ noch „alles Ferne“. Eine Karte ohne Lücke
        kann ein durchgehender Verlauf sein oder eine, in der die Ferne fliessend anfängt;
        beides ist ein Befund für den Aufrufer und keine Zahl, die dieses Modul erfinden
        darf. In diesem Fall sind auch ``anteil_geklemmt`` und ``anteil_wertebereich``
        ``None``, und in ``warnungen`` steht der grösste tatsächlich gefundene Sprung.

        ``anteil_wertebereich`` sagt, welchen Anteil des Bereichs ``[kleinster Wert,
        obergrenze]`` der **Kern** nutzt — die Punkte unterhalb der tiefsten tauglichen
        Lücke. Das ist die Zahl zur Tabelle oben: dieselbe Aussenansicht nutzt mit einer
        Stufe **17.0 %** des Wertebereichs und mit zwei Stufen 100 %. Ist die Obergrenze
        gleich dem kleinsten Wert, hat der Bereich keine Breite — dann ist der Anteil
        ``None``, also NICHT GEMESSEN, und ausdrücklich nicht 0.

        ``anteil_geklemmt`` zählt gegen ``n_gemessen`` und nicht gegen die Länge der
        Karte: Hintergrundmarken sind keine Tiefe, also können sie auch nicht geklemmt
        werden. ``verhaeltnis`` ist der Sprung der **zuletzt** gefundenen Stufe, also der
        Sprung an ``obergrenze`` — bei ``stufen=1`` der einzige.

    Raises:
        QaError: leere Karte, ``stufen < 1``, ``mindest_verhaeltnis < 1`` (ein Sprung
            unter Faktor 1 ist keiner) oder unbrauchbare Werte.
    """
    stufen = int(stufen)
    if stufen < 1:
        raise QaError(f"stufen muss mindestens 1 sein, war {stufen!r}.")
    mindest = float(mindest_verhaeltnis)
    if not math.isfinite(mindest) or mindest < 1.0:
        raise QaError(
            f"mindest_verhaeltnis muss endlich und ≥ 1 sein, war {mindest_verhaeltnis!r}. "
            f"Ein Sprung um weniger als das Einfache ist kein Sprung."
        )
    grenze = _hintergrund_grenze(hintergrund_grenze)
    roh = _als_zahlen(karte, "karte")
    if not roh:
        raise QaError("karte ist leer — es gibt nichts abzutrennen.")

    werte = sorted(w for w in roh if math.isfinite(w) and 0.0 < w < grenze)
    antwort = {"obergrenze": None, "stufen_gefunden": 0, "kanten": (),
               "anteil_geklemmt": None, "anteil_wertebereich": None, "verhaeltnis": None,
               "n_gemessen": len(werte), "n_ausgelassen": len(roh) - len(werte),
               "warnungen": []}

    if len(werte) < 2:
        antwort["warnungen"].append(
            f"Weniger als zwei verwertbare Tiefen ({len(werte)} von {len(roh)} Punkten; "
            f"der Rest ist Hintergrundmarke, nicht endlich oder ≤ 0) — NICHT GEMESSEN. "
            f"Eine Obergrenze aus einem einzigen Wert wäre dieser Wert selbst.")
        return antwort

    # Die Lücken liegen zwischen VERSCHIEDENEN Werten; gleiche Werte haben Verhältnis 1.
    # Zu jedem Wert wird mitgezählt, wie viele Punkte auf ihm oder darunter liegen — das
    # entscheidet über MINDEST_KERN_ANTEIL.
    stufen_werte: list[float] = []
    kleinster = werte[0]
    n_gesamt = len(werte)

    def _luecke(betrachtet: list[float]) -> tuple[float, float] | tuple[None, float]:
        """Grösste taugliche Lücke in ``betrachtet`` als ``(untere Kante, Verhältnis)``.

        Zurück kommt auch der grösste ÜBERHAUPT gefundene Sprung, damit die Warnung im
        Fall ohne Lücke eine Zahl nennen kann statt nur ein Nein.
        """
        bester_wert: float | None = None
        bestes_v = 0.0
        groesster_sprung = 1.0
        n = len(betrachtet)
        for i in range(n - 1):
            unten, oben = betrachtet[i], betrachtet[i + 1]
            if oben <= unten:
                continue
            v = oben / unten
            groesster_sprung = max(groesster_sprung, v)
            # i+1 Punkte liegen auf `unten` oder darunter.
            if (i + 1) < MINDEST_KERN_ANTEIL * n:
                continue
            if v >= mindest and v > bestes_v:
                bester_wert, bestes_v = unten, v
        return (bester_wert, bestes_v if bester_wert is not None else groesster_sprung)

    betrachtet = werte
    verhaeltnis = None
    letzter_sprung = 1.0
    for _ in range(stufen):
        kante, v = _luecke(betrachtet)
        if kante is None:
            letzter_sprung = v
            break
        stufen_werte.append(kante)
        verhaeltnis = v
        betrachtet = [w for w in betrachtet if w <= kante]
        if len(betrachtet) < 2:
            break

    if not stufen_werte:
        antwort["warnungen"].append(
            f"KEINE taugliche Lücke gefunden — NICHT GEMESSEN, und das heisst weder "
            f"„keine Ferne“ noch „alles Ferne“. Der grösste Nachbarsprung war Faktor "
            f"{letzter_sprung:.4g}, verlangt sind {mindest:.4g}. Eine Verteilung ohne Loch "
            f"lässt sich nicht an einem Loch trennen; wer hier trotzdem klemmt, wählt eine "
            f"Grenze, die im Bild nicht steht (Perzentil-Befund vom 11.09.2026).")
        return antwort

    obergrenze = stufen_werte[-1]
    # Der Kern endet an der TIEFSTEN tauglichen Lücke unterhalb der Obergrenze. Fand die
    # letzte Stufe keine mehr, ist die Obergrenze selbst das Ende des Kerns — dann nutzt
    # der Kern den Wertebereich vollständig, und genau das ist die Aussage.
    kern_kante, _ = _luecke([w for w in werte if w <= obergrenze])
    kern_max = kern_kante if kern_kante is not None else obergrenze

    antwort["obergrenze"] = obergrenze
    antwort["stufen_gefunden"] = len(stufen_werte)
    antwort["kanten"] = tuple(stufen_werte)
    antwort["verhaeltnis"] = verhaeltnis
    antwort["anteil_geklemmt"] = sum(1 for w in werte if w > obergrenze) / n_gesamt

    # Jede Stufe nach der ersten ist ein Entscheid über den BILDINHALT und keine Messung:
    # Ob der Klumpen hinter der ersten Lücke Fernsicht ist oder ein Nachbargebäude, steht
    # in der Tiefenkarte nicht. Was sie zusätzlich wegnimmt, wird darum beziffert — still
    # geschieht das nicht.
    if len(stufen_werte) > 1:
        erste = stufen_werte[0]
        zusatz = sum(1 for w in werte if obergrenze < w <= erste) / n_gesamt
        antwort["warnungen"].append(
            f"{len(stufen_werte)} Stufen: Die erste Lücke lag bei {erste:.4g}, geklemmt "
            f"wird erst ab {obergrenze:.4g} — {zusatz:.1%} der Punkte fallen allein durch "
            f"die späteren Stufen weg. Diese Punkte sind ENTWEDER Ferne ODER Bauwerk; "
            f"welches von beidem, steht nicht in der Tiefenkarte. Wer ihnen nicht traut, "
            f"nimmt stufen=1.")
    spanne = obergrenze - kleinster
    if spanne > 0.0:
        antwort["anteil_wertebereich"] = (kern_max - kleinster) / spanne
    else:
        antwort["warnungen"].append(
            "Obergrenze gleich kleinstem Wert — der Wertebereich hat keine Breite, der "
            "genutzte Anteil ist NICHT GEMESSEN und nicht 0.")
    return antwort


# ======================================================================================
# Die zwei Tore — zwei Fragen, zwei Zahlen, verbunden mit UND
# ======================================================================================
#
# **Der Anlass ist der schwerste Befund dieses Projekts** (R3, nachgerechnet am
# 18.09.2026 an den Zahlen von `auf-20260909-92`, ausgeschrieben in
# `docs/R3_WELCHES_MASS_TRENNT_2026-09-18.md`):
#
# Zwölf erzeugte Bilder bestanden die Schwelle 0.65. **Dieselben zwölf bestanden sie auch
# gegen die Tiefenkarte eines völlig anderen Gebäudes.** Und bei einer ControlNet-Stärke
# von 0.30, wo das Bild dem Modell nachweislich nicht mehr folgt, bestanden immer noch
# elf von zwölf.
#
# Nachgerechnet an denselben zwölf Bildern, dreimal gemessen:
#
#     Kennzahl     folgt dem Modell   folgt NICHT (0.30)   trennt richtig/falsch
#     score            0.966          0.766  besteht noch   ja  (paarweise 12/12)
#     geom_iou         0.961          0.722  besteht noch   ja  (Lücke +0.149)
#     rho_maske        0.798         -0.009  EXAKT NULL     NEIN (nur 10/12)
#
# **Es sind zwei Fragen, und eine einzige Zahl kann beide nicht beantworten:**
#
#   A  Folgt das Bild dem Modell überhaupt?      → `rho_maske`, und nur sie.
#   B  Folgt es DIESEM Modell und keinem andern? → `geom_iou`, mit der grössten Lücke.
#
# Der zusammengesetzte `score` multipliziert A (über `spearman`) mit B (`geom_iou`) und
# zieht die Wurzel. Damit gleicht ein guter Wert der einen einen schlechten der anderen
# aus — und genau das lässt Müllbilder durch.
#
#     Eine Kennzahl, die zwei Fragen zu einer verrechnet, beantwortet keine von beiden.
#
# `geometrie_gate` bleibt unverändert daneben stehen: Alle bisher gemessenen Zahlen des
# Projekts sind mit ihm entstanden und müssen reproduzierbar bleiben. Die zwei Tore sind
# der Weg nach vorn, nicht eine Berichtigung nach hinten.

#: Ab welchem ``rho_maske`` gilt **Tor A** als bestanden: folgt das Bild dem Modell?
#:
#: **Woher die Zahl kommt, und woher nicht.** Gemessen ist das *Rauschband*: Bei
#: ControlNet-Stärke 0.30, wo das Bild dem Modell nachweislich nicht mehr folgt, lag
#: ``rho_maske`` über zwölf Bilder zwischen **−0.0473 und +0.0554**. 0.10 liegt darüber,
#: und darauf allein ruht die Zahl. Sie ist **gesetzt, nicht kalibriert.**
#:
#: **BERICHTIGUNG 18.09.2026 — hier stand eine Behauptung zu viel.** Der Satz lautete:
#: «Gemessen ist auch der niedrigste Wert eines Bildes, das dem Modell folgt: +0.144»,
#: und daraus wurde eine Lücke 0.055…0.144 abgeleitet, in deren Mitte 0.10 liege. Das
#: gilt **nur für Stärke 1.00**. Nachgerechnet über alle drei Reihen desselben Laufs
#: (``auf-20260909-92-tabelle.json``)::
#:
#:     Stärke 1.00   rho_maske  +0.1437 … +0.9931     iou 0.9257 … 0.9784
#:     Stärke 0.75   rho_maske  −0.1549 … +0.9961     iou 0.9119 … 0.9845
#:     Stärke 0.30   rho_maske  −0.0473 … +0.0554     iou 0.6037 … 0.8579
#:
#: Ein Bild bei Stärke 0.75 (Fall C, Szene ``gebaeude``, Seed 2) hat ``rho_maske``
#: **−0.1549** — **unterhalb des ganzen Rauschbandes** — und zugleich ``geom_iou``
#: **0.9119**, also eine Silhouette, die sauber sitzt. Die Lücke, aus der 0.10 stammt,
#: existiert an dieser Stelle des eigenen Datensatzes **nicht**.
#:
#: **Was das kostet, gezählt statt geschätzt.** Mit 0.10 fällt genau dieses eine Bild
#: durch Tor A::
#:
#:     Stärke 1.00   Tor A 12/12   Tor B 12/12   UND 12/12
#:     Stärke 0.75   Tor A 11/12   Tor B 12/12   UND 11/12
#:     Stärke 0.30   Tor A  0/12   Tor B  1/12   UND  0/12
#:
#: Das ist ein **Fehlalarm**, kein Durchlasser: Ein brauchbares Bild wird abgewiesen.
#: Das ist die richtige Richtung für einen Riegel — aber es heisst auch, dass
#: ``rho_maske`` bei 0.75 mindestens einmal **etwas anderes misst als bei 1.00**.
#:
#: **ENTSCHIEDEN am 21.09.2026 — die Gegenprobe ist gefahren** (``auf-20260918-115``,
#: HomeStation, 36 Bilder, jedes gegen die richtige **und** die falsche Tiefenkarte).
#: Die Frage lautete: folgt das Bild bei 0.75 wirklich weniger, oder versagt dort
#: ``rho_maske``? Die Antwort ist die erste, und sie ist deutlich::
#:
#:     Fall C, gebaeude, Seed 2, Stärke 0.75
#:         rho_maske gegen die RICHTIGE Karte   −0.1549
#:         rho_maske gegen die FALSCHE  Karte   +0.3001
#:
#: **Das Bild folgt der fremden Geometrie besser als der eigenen.** Eine blinde Zahl kann
#: das nicht — sie sieht dort etwas, und es ist das falsche Gebäude. *Das Modell hat aus
#: dem gegliederten Bauwerk einen Block gemacht, und der ist der Schachtel ähnlicher.*
#:
#: **Die Schwelle 0.10 bleibt damit, wo sie ist.** Dieses Bild fällt durch Tor A, und es
#: soll durchfallen. Was oben als möglicher Fehlalarm stand, ist keiner.
#:
#: **Und es liegt nicht an der Stärke.** Dieselbe Zelle steht bei Stärke 1.00 auf
#: richtig +0.1437 gegen falsch +0.4122 — ebenfalls falschherum, nur weniger deutlich.
#: Es ist eine Eigenschaft **dieser Zelle**, nicht der Führungsstärke.
#:
#: **BERICHTIGUNG 21.09.2026 — es ist nicht EINE Zelle, es sind ZWEI.** Hier stand, die
#: Gegenprobe habe «den einen zweifelhaften Fall des eigenen Datensatzes» aufgelöst.
#: Nachgezählt an ``auf-20260909-92-tabelle.json``, Reihe Stärke 1.00, alle zwölf Paare::
#:
#:     C2  gebaeude  richtig +0.1437   falsch +0.4122   Abstand −0.2685
#:     D2  gebaeude  richtig +0.4877   falsch +0.6324   Abstand −0.1447
#:
#: Beide folgen der **fremden** Geometrie besser als der eigenen, und beide bestehen
#: Tor A heute (0.1437 und 0.4877 liegen über 0.10). Die Zahl war nie falsch — die
#: **Anzahl** war es, und sie stand seit dem 21.09.2026 als «eine» da. *Eine Aussage
#: über die eigenen Daten, die nicht nachgezählt ist, veraltet nicht, sie war von
#: Anfang an falsch.*
#:
#: Was daran NICHT wackelt: ``geom_iou`` ordnet **alle zwölf** Paare richtig, D2 mit
#: +0.2020 Abstand. Die Zuordnung leistet Tor B, und genau darum steht sie dort
#: (siehe :func:`zuordnung`).
#:
#: **ENTSCHIEDEN 21.09.2026 — der Vorschlag 0.88 wird NICHT übernommen**
#: (``auf-20260909-98``, HomeStation, 44 Fälle an vier neuen Szenen). Die Werkstatt hat
#: sauber kalibriert und ein fehlerfreies Fenster gefunden: höchster schlechter Fall
#: +0.8651, niedrigster guter +0.9031, Vorschlag 0.88 in der Mitte. An **ihrem**
#: Datensatz stimmt das.
#:
#: **An unserem nicht, und das ist gezählt statt geschätzt.** Dieselbe Schwelle auf die
#: tragende Reihe von ``auf-20260909-92`` (Stärke 1.00) angewandt::
#:
#:     Tor A mit 0.10    12 von 12 bestanden
#:     Tor A mit 0.88     7 von 12 bestanden
#:
#: Fünf Bilder fielen. **Drei davon folgen ihrer eigenen Geometrie nachweislich besser
#: als einer fremden** — C1 (+0.2276), D0 (+0.1974), D1 (+0.3348). Das wären drei
#: **Fehlalarme** auf zwölf Bilder, an der Reihe, die diese Arbeit trägt.
#:
#: **Der Grund ist keine schlechte Messung, sondern eine andere Population**, und die
#: Werkstatt hat ihn selbst benannt: Sie stört die **Referenz** und misst gegen die
#: geschätzte Karte eines erzeugten Bildes. Im Betrieb ist das **Bild** das Schlechte und
#: die Referenz richtig.
#:
#:     *Eine Schwelle, die an einer gestörten Referenz kalibriert ist, misst die
#:     Störung — nicht das Bild.*
#:
#: Das Fenster 0.8651…0.9031 ist in unseren Daten kein Fenster: Fünf von zwölf guten
#: Bildern liegen darunter oder darin.
#:
#: **Was die Messung trotzdem beiträgt**, und es ist nicht wenig: Sie zeigt, dass 0.10
#: **nur** die Fälle mit verschwindendem oder negativem Wert fängt — gedreht, verrauscht,
#: innen vertauscht. ``versatz_20px``, also dasselbe Bauwerk an der falschen Stelle,
#: liegt bei 0.78…0.87 und kommt durch. *Ein Riegel, der die grobe Hälfte fängt, ist
#: kein Riegel gegen die feine.*
#:
#: *Genau diese Sorte Zahl war die alte 0.65, und sie hat elf von zwölf Müllbildern
#: durchgelassen.* Der Unterschied ist, dass hier dransteht, worauf sie ruht — und dass
#: die Gegenprobe in :func:`zwei_tore` sie bei jedem Lauf prüft, statt ihr zu glauben.
SCHWELLE_FOLGT = 0.10

#: Ab welchem ``geom_iou`` gilt **Tor B** als bestanden: folgt es DIESEM Modell?
#:
#: **Gemessen** an zwölf Paaren, jedes Bild gegen die richtige und gegen eine falsche
#: Tiefenkarte::
#:
#:     gegen die richtige Karte    0.9257 … 0.9784
#:     gegen die falsche Karte     0.7350 … 0.7766
#:     Lücke                       +0.1491
#:
#: 0.85 liegt in der Mitte dieser Lücke. **Ebenfalls gesetzt und nicht kalibriert**, aber
#: mit siebenfach mehr Luft als bei Tor A — und die Lücke ist an echten Gegenproben
#: gemessen, nicht an Störungen.
#:
#: **Warum Tor B allein nicht genügt:** In der 0.30-Reihe erreicht ein Müllbild gegen
#: seine *richtige* Karte ``geom_iou`` **0.8579** und damit Tor B. Erst das UND mit Tor A
#: (dort 0.0008) weist es ab. Ein Tor ist kein Riegel.
#:
#: **Woran sie kippt:** Die falsche Karte war immer die jeweils *andere von zweien* — eine
#: Schachtel und ein fünfgeschossiger Bau. Zwei **ähnliche** Gebäude sind nicht geprüft,
#: und dort wird es schwer. Die Messung dazu ist bestellt.
SCHWELLE_DIESES = 0.85


def _tor(wert, schwelle: float, frage: str, name: str) -> dict:
    """Ein einzelnes Tor. ``wert is None`` heisst NICHT GEMESSEN — und damit nicht bestanden.

    **Fail-closed, wie der Torwächter und wie** :func:`geometrie_gate`: Was ungeprüft ist,
    wird nicht durchgelassen. Ein Freispruch aus Mangel an Messung wäre die teuerste Sorte
    Fehler, denn niemand sucht danach.

    Unterschieden bleibt es trotzdem: ``gemessen`` sagt, ob überhaupt eine Zahl vorlag.
    *Nicht gemessen und durchgefallen sind beides «nicht bestanden» — aber nur eines davon
    ist ein Befund über das Bild.*
    """
    if wert is None:
        return {"name": name, "frage": frage, "wert": None, "schwelle": schwelle,
                "gemessen": False, "bestanden": False,
                "begruendung": f"{name}: NICHT GEMESSEN, damit nicht bestanden. "
                               f"Das ist kein Urteil über das Bild, sondern über die Messung."}
    bestanden = wert >= schwelle
    return {"name": name, "frage": frage, "wert": float(wert), "schwelle": schwelle,
            "gemessen": True, "bestanden": bestanden,
            "begruendung": f"{name}: {wert:.4f} {'≥' if bestanden else '<'} {schwelle:.2f}"}


def zuordnung(geom_iou, geom_iou_fremd) -> dict:
    """**Folgt das Bild DIESEM Modell?** — beantwortet durch Vergleich, nicht durch Schwelle.

    Args:
        geom_iou: Silhouetten-Überdeckung gegen die **richtige** Soll-Karte.
        geom_iou_fremd: dieselbe Zahl gegen eine **fremde** Geometrie.
            Beide ``None`` = nicht gemessen.

    Returns:
        ``{ordnet, abstand, gemessen, begruendung}``. ``ordnet`` ist ``True``, wenn die
        eigene Karte besser passt als die fremde, ``False``, wenn die fremde besser passt,
        und ``None``, wenn eine der beiden Zahlen fehlt.

    **Woher diese Funktion kommt** (HomeStation, ``auf-20260918-115``, 21.09.2026, an 36
    Bildern gemessen). Die Werkstatt hat eine Unterscheidung nachgemessen, die hier zwei
    Fragen in einem Tor vermischt hatte:

    ================================  =========================  =====================
    Frage                             Werkzeug                   Form
    ================================  =========================  =====================
    Folgt das Bild **überhaupt** etwas?   ``rho_maske``          Schwelle
    Folgt es **DIESEM** Modell?           ``geom_iou``           **Vergleich**
    ================================  =========================  =====================

    Gemessen, und beide Hälften sind unbequem:

    * Als **Schwelle** ist ``geom_iou`` schwach — es lässt bei 56 % Geometrieanteil auch
      das falsche Gebäude durch.
    * Als **Vergleich** ist es das schärfere Werkzeug: **24 von 24** Paaren richtig
      geordnet (Führung 1,00 und 0,75), gegen 19 von 24 bei ``rho_maske``.

    **Warum hier kein Mindestabstand steht, obwohl er naheliegt.** Aus den Rohdaten
    derselben Messung nachgerechnet (nicht aus der Zusammenfassung übernommen):

    ==================  ===================  ==================
    Führung             richtig geordnet     Abstand
    ==================  ===================  ==================
    1,00                12 von 12            +0,1876 … +0,2243
    0,75                12 von 12            +0,1541 … +0,2254
    0,30 (ohne Führung)  6 von 12            −0,1586 … +0,1570
    ==================  ===================  ==================

    Der kleinste **echte** Abstand ist +0,1541. Der grösste Betrag im **Rauschen** ist
    0,1586 — er ist **grösser**. Zwischen Signal und Rauschen liegt hier also *keine
    Lücke*, und damit ist kein Mindestabstand setzbar, der die beiden trennte.

        *Eine Schwelle, die es in den Daten nicht gibt, wird durch Setzen nicht wahr.*

    Gewertet wird darum allein das **Vorzeichen**. Das genügt, weil diese Frage erst
    gestellt wird, wenn die erste schon mit Ja beantwortet ist: Bei Führung 0,30 fällt
    ``rho_maske`` auf null, Tor A hält an, und diese Ordnung wird nie befragt. *Die
    Ordnung ist nur dort etwas wert, wo überhaupt etwas geordnet wird.*
    """
    for name, wert in (("geom_iou", geom_iou), ("geom_iou_fremd", geom_iou_fremd)):
        if wert is None or isinstance(wert, (int, float)) and not isinstance(wert, bool):
            continue
        raise QaError(f"{name}: Zahl oder None erwartet, war {wert!r} "
                      f"({type(wert).__name__}).")

    if geom_iou is None or geom_iou_fremd is None:
        fehlt = "geom_iou" if geom_iou is None else "geom_iou_fremd"
        return {"ordnet": None, "abstand": None, "gemessen": False,
                "begruendung": (f"NICHT GEMESSEN: {fehlt} fehlt. Ohne beide Zahlen gibt es "
                                f"keinen Vergleich — und eine fehlende Zahl ist hier "
                                f"weder ein Ja noch ein Nein.")}

    abstand = float(geom_iou) - float(geom_iou_fremd)
    ordnet = abstand > 0.0
    if ordnet:
        satz = (f"Die eigene Geometrie passt besser als die fremde "
                f"({geom_iou:.4f} gegen {geom_iou_fremd:.4f}, Abstand {abstand:+.4f}).")
    else:
        satz = (f"DIE FREMDE GEOMETRIE PASST BESSER ODER GLEICH GUT "
                f"({geom_iou:.4f} gegen {geom_iou_fremd:.4f}, Abstand {abstand:+.4f}). "
                f"Das Bild stellt dann nicht dieses Modell dar.")
    return {"ordnet": ordnet, "abstand": abstand, "gemessen": True, "begruendung": satz}


def zwei_tore(rho_maske, geom_iou, *,
              rho_maske_fremd=None, geom_iou_fremd=None,
              schwelle_folgt: float = SCHWELLE_FOLGT,
              schwelle_dieses: float = SCHWELLE_DIESES) -> dict:
    """Das Urteil aus **zwei** Toren — und aus der Gegenprobe, die es erst gültig macht.

    Args:
        rho_maske: Rangkorrelation über der Bauwerksmaske, gegen die **richtige**
            Soll-Karte. Aus :func:`rho_ueber_maske`. ``None`` = nicht gemessen.
        geom_iou: Silhouetten-Überdeckung gegen die **richtige** Soll-Karte. Aus
            :func:`geometrie_score`. ``None`` = nicht gemessen.
        rho_maske_fremd, geom_iou_fremd: dieselben zwei Zahlen gegen eine **fremde**
            Geometrie — die Gegenprobe. Ohne sie ist das Urteil vorläufig, und das Ergebnis
            sagt es (siehe unten).
        schwelle_folgt, schwelle_dieses: siehe :data:`SCHWELLE_FOLGT` und
            :data:`SCHWELLE_DIESES`. Beide sind **gesetzt und nicht kalibriert**.

    Returns:
        ``{bestanden, trennt, tor_folgt, tor_dieses, gegenprobe, begruendung, warnungen}``

        ``bestanden`` ist ``True`` nur, wenn **beide** Tore bestehen — ein UND, kein
        Mittelwert. Es ist ``None``, wenn die Gegenprobe zeigt, dass diese Messung gar
        nicht trennt (siehe unten). Sonst ``False``.

    **Warum ein UND und kein Mittelwert.** Der bisherige ``score`` verrechnet beide Fragen
    miteinander; ein guter Wert der einen hebt einen schlechten der anderen über die
    Schwelle. An zwölf Bildern gemessen liess das elf Müllbilder durch.

    **Die Gegenprobe, und sie ist der eigentliche Gehalt dieser Funktion.**
    Besteht das Bild auch gegen eine **fremde** Geometrie, dann hat diese Messung nichts
    gezeigt. Das Ergebnis ist dann **nicht «bestanden»**, sondern ``bestanden = None`` —
    *nicht entscheidbar*. Das ist die dritte Antwort an der Stelle, an der sie am meisten
    wert ist:

        Ein Prüfverfahren, das auch die falsche Antwort durchlässt, hat nicht die richtige
        bestätigt — es hat gar nichts gemessen.

    Ohne Gegenprobe (``…_fremd is None``) urteilt die Funktion trotzdem, setzt aber
    ``trennt = None`` und schreibt eine Warnung: *Das Urteil ist dann so viel wert wie das
    alte, und das alte war nichts wert.*
    """
    for name, wert in (("rho_maske", rho_maske), ("geom_iou", geom_iou),
                       ("rho_maske_fremd", rho_maske_fremd),
                       ("geom_iou_fremd", geom_iou_fremd)):
        if wert is None or isinstance(wert, (int, float)) and not isinstance(wert, bool):
            continue
        raise QaError(f"{name}: Zahl oder None erwartet, war {wert!r} "
                      f"({type(wert).__name__}).")

    a = _tor(rho_maske, float(schwelle_folgt),
             "Folgt das Bild dem Modell ueberhaupt?", "rho_maske")
    b = _tor(geom_iou, float(schwelle_dieses),
             "Folgt es DIESEM Modell und keinem anderen?", "geom_iou")

    warnungen: list[str] = []
    bestanden = a["bestanden"] and b["bestanden"]

    # ── Die Gegenprobe ────────────────────────────────────────────────────────────────
    gegenprobe = None
    trennt = None
    if rho_maske_fremd is not None or geom_iou_fremd is not None:
        a_f = _tor(rho_maske_fremd, float(schwelle_folgt), a["frage"], "rho_maske (fremd)")
        b_f = _tor(geom_iou_fremd, float(schwelle_dieses), b["frage"], "geom_iou (fremd)")
        fremd_bestanden = a_f["bestanden"] and b_f["bestanden"]
        vollstaendig = a_f["gemessen"] and b_f["gemessen"]
        gegenprobe = {"tor_folgt": a_f, "tor_dieses": b_f,
                      "bestanden": fremd_bestanden, "vollstaendig": vollstaendig}

        # EINE HALBE GEGENPROBE IST KEINE TRENNUNG — und das war hier ein echter Fehler,
        # gefunden von der Gegenpruefung am 18.09.2026 und selbst nachgestellt:
        #
        #     zwei_tore(0.80, 0.96, geom_iou_fremd=0.99)
        #       -> bestanden True, trennt True, keine Warnung,
        #          Begruendung: "Gegen fremde Geometrie faellt sie durch, wie sie soll."
        #
        # Die EINZIGE gemessene fremde Zahl (0.99) BESTAND Tor B — die fremde Geometrie
        # sah der richtigen messbar aehnlich. Und die Funktion meldete Trennung.
        #
        # Die Ursache ist eine Verwechslung von zwei Richtungen: `_tor` ist fail-closed,
        # ein nicht gemessenes Tor gilt als nicht bestanden. Fuer das URTEIL ist das
        # richtig. Fuer die GEGENPROBE ist es die Umkehrung: Dort wuerde daraus
        # "die fremde Karte ist durchgefallen", also "es trennt" — aus einer fehlenden
        # Messung eine positive Behauptung.
        #
        # Genau der Fehler, gegen den diese ganze Funktion geschrieben ist, und er stand
        # in ihrem Herzstueck.
        if not vollstaendig:
            trennt = None
            fehlt = [n for n, t in (("rho_maske", a_f), ("geom_iou", b_f))
                     if not t["gemessen"]]
            warnungen.append(
                f"HALBE GEGENPROBE: Von der fremden Geometrie fehlt {', '.join(fehlt)}. "
                f"Ob diese Messung trennt, ist damit NICHT GEMESSEN — weder ja noch nein. "
                f"Eine fehlende Zahl darf hier nicht als «die fremde Karte ist "
                f"durchgefallen» gelesen werden; genau so entstuende aus einer Luecke eine "
                f"Zusage.")
        else:
            trennt = not fremd_bestanden
        if fremd_bestanden and vollstaendig:
            # HIER IST DIE DRITTE ANTWORT AM MEISTEN WERT. Ein Urteil «bestanden» waere
            # jetzt nachweislich wertlos — dieselbe Messung sagt dasselbe ueber ein
            # Gebaeude, das es nicht ist.
            bestanden = None
            warnungen.append(
                "DIESE MESSUNG TRENNT NICHT: Das Bild besteht auch gegen eine FREMDE "
                "Geometrie. Damit ist nichts gezeigt — weder dass es geometrietreu ist "
                "noch dass es das nicht ist. Das Urteil ist NICHT ENTSCHEIDBAR, nicht "
                "«bestanden». Genau dieser Fall lag am 08.09.2026 zwoelfmal vor und wurde "
                "als Erfolg gelesen.")
    else:
        warnungen.append(
            "OHNE GEGENPROBE. Es wurde nicht geprueft, ob dieselbe Messung auch gegen eine "
            "fremde Geometrie besteht. Das Urteil ist damit so viel wert wie das alte — "
            "und das alte liess elf von zwoelf Muellbildern durch.")

    if not a["gemessen"] or not b["gemessen"]:
        warnungen.append(
            "Mindestens ein Tor ist NICHT GEMESSEN und gilt darum als nicht bestanden. "
            "Fail-closed wie der Torwaechter: Was ungeprueft ist, wird nicht durchgelassen.")

    if bestanden is None:
        kopf = "NICHT ENTSCHEIDBAR"
    elif bestanden:
        kopf = "BESTANDEN"
    else:
        kopf = "NICHT BESTANDEN"
    begruendung = f"{kopf} — {a['begruendung']}; {b['begruendung']}."
    if trennt is False:
        begruendung += " Die Gegenprobe gegen fremde Geometrie besteht ebenfalls."
    elif trennt is True:
        begruendung += " Gegen fremde Geometrie faellt sie durch, wie sie soll."
    elif gegenprobe is not None:
        # Der Satz oben waere hier eine Behauptung ueber eine Messung, die es nicht gibt.
        begruendung += " Die Gegenprobe ist unvollstaendig; ob sie trennt, ist offen."

    # DIE ZUORDNUNG — dieselben zwei Zahlen, aber als VERGLEICH statt als Schwelle.
    #
    # Sie urteilt hier bewusst NICHT mit. `bestanden` bleibt, was die zwei Tore sagen.
    # Der Grund ist der Zustand der Belege: Die Ordnung ist an 24 Paaren gemessen und
    # traegt dort 24 von 24; die Schwelle 0.85 steht seit dem 18.09.2026 in einer
    # gemessenen Luecke. Beide gegeneinander auszuspielen, bevor ein Fall bekannt ist,
    # in dem sie sich widersprechen, hiesse raten.
    #
    # Was sie tut, ist mehr wert: Sie MELDET den Widerspruch, wenn es ihn gibt. Ein Bild,
    # das Tor B ueber die Schwelle bringt und zugleich der fremden Geometrie aehnlicher
    # ist, ist genau der Fall, den diese Funktion finden soll — und genau der Fall, den
    # eine Schwelle allein nie sieht.
    ordnung = zuordnung(geom_iou, geom_iou_fremd)
    if ordnung["gemessen"] and ordnung["ordnet"] is False and b["bestanden"]:
        warnungen.append(
            f"WIDERSPRUCH ZWISCHEN SCHWELLE UND ORDNUNG: Tor B besteht "
            f"({geom_iou:.4f} >= {float(schwelle_dieses):.2f}), aber die FREMDE Geometrie "
            f"passt besser ({geom_iou_fremd:.4f}). Eine Schwelle sagt, wie gut es passt; "
            f"sie sagt nicht, ob es zu DIESEM Modell gehoert. Dieser Fall ist am "
            f"21.09.2026 an einem echten Bild gemessen worden.")

    return {"bestanden": bestanden, "trennt": trennt,
            "tor_folgt": a, "tor_dieses": b, "gegenprobe": gegenprobe,
            "zuordnung": ordnung,
            "begruendung": begruendung, "warnungen": warnungen}
