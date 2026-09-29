# 5 · Die Kamera: was die Software selbst entscheidet

> **Stand 29.09.2026 — Entwurf** (geschrieben 19.09.2026, nachgezogen 29.09.2026).
> Drittes geschriebenes Kapitel.
> **Alle Zahlen dieses Kapitels sind für das Kapitel gerechnet worden**, am 19.09.2026,
> gegen den Quelltext in `src/aiimaging/kameras.py`. Wo eine ältere Notiz eine andere Zahl
> nannte, steht die neu gerechnete — und der Unterschied ist vermerkt.
> **Nachtrag 29.09.2026:** `kameras.py` hat sich am 24.09.2026 geändert (Wandabstand 10 m →
> 3 m, Rücknahme bei zu steilem Shift). Die Zahlen vom 19.09.2026 gelten für den dort
> gerechneten Baukörper (12 × 15 × 9 m) weiter; **für kleine Bauten waren zwei Aussagen zu
> allgemein** — siehe 5.3 und 5.4. Dazu die Zwillinge (5.6) und die Innenansicht (5.7).

---

## 5.1 Die Frage, die eine Software beantworten muss, wenn niemand danach gefragt wird

Ein Bildmodell braucht eine Kamera. Wo sie steht, wohin sie blickt, welche Brennweite sie
hat — das steht in keinem Gebäudemodell, und es steht in keiner Bestellung, die eine
Architektin absetzt. Sie sagt «zeig mir das Haus», nicht «Augpunkt bei 27,08 / 37,60 /
1,70, Brennweite 35 mm».

**Die Software muss also entscheiden.** Die Frage dieses Kapitels ist, *wie weit* sie das
darf und woran man erkennt, dass sie es gut getan hat.

Die Antwort dieser Arbeit besteht aus drei Teilen:

* **Rechnen, wo gerechnet werden kann.** Standpunkt, Abstand und Rahmung folgen aus der
  Hüllbox des Bauwerks. Das ist Geometrie, keine Gestaltung.
* **Nicht entscheiden, wo es eine Entscheidung wäre.** Wo zwei Antworten gleich gut sind,
  werden beide geliefert. Die Software soll nicht so tun, als wüsste sie mehr, als in der
  Geometrie steht.
* **Sagen, was sie getan hat.** Jeder Standpunkt trägt seine Begründung mit — nicht als
  Kommentar im Quelltext, sondern als Feld im Ergebnis.

---

## 5.2 Zwölf Richtungen, und warum genau zwölf

Die Software kennt **zwölf** Blickrichtungen: die vier Himmelsrichtungen und je zwei
Überecksichten daneben. Aus ihnen werden für einen Auftrag **drei** ausgewählt.

Warum nicht acht, warum nicht sechzehn? Die Zwölf folgen aus der Sache: Vier Fassaden,
und zwischen je zwei Fassaden liegt eine Ecke, von der man beide sieht. Zwölf ist die
kleinste Zahl, die jede Fassade frontal **und** jede Ecke zweiseitig abdeckt.

**Gemessen am 19.09.2026** an einem Baukörper von 12 × 15 × 9 m:

| | |
|---|---|
| Richtungen im Satz | **12** |
| geprüfte Dreierkombinationen bei der Auswahl | **56** |
| Winkelabstand der gewählten drei | **90°** (Ideal wäre 120°) |
| Begründung jedes Standpunkts | *«Alle acht Ecken im Bild.»* |

Die 56 ist keine Schätzung: Sie ist die Zahl der Dreierkombinationen aus acht tauglichen
Kandidaten, und sie steht im Ergebnis. **Die Software rechnet sie alle durch** und wählt
nach einem Gütemass, das den Flächenanteil des Bauwerks im Bild gegen die Sichtbarkeit
einer zweiten Fassade abwägt.

**Und die Streuung von 90° gegen das Ideal von 120° wird gemeldet, nicht versteckt.** Bei
einem rechteckigen Grundriss lassen sich drei Standpunkte nicht gleichmässig um 120°
verteilen, ohne einen schlechten Blickwinkel in Kauf zu nehmen. Die Software nimmt den
kleineren Abstand und **sagt es dazu**.

---

## 5.3 Shift statt Kippen — die Entscheidung, an der man Architektur erkennt

Ein Gebäude, das höher ist als der Augpunkt, passt nicht ins Bild, wenn die Kamera
waagrecht steht. Es gibt zwei Auswege, und sie unterscheiden sich fundamental:

**Kippen.** Die Kamera wird nach oben geneigt. Das ist, was ein Mobiltelefon tut. Die
Folge: **stürzende Linien** — die senkrechten Gebäudekanten laufen im Bild nach oben
zusammen.

**Shiften.** Die Kamera bleibt waagrecht, und die Bildebene wird verschoben. Das ist, was
ein Architekturfotograf mit einem Shift-Objektiv tut. Die Folge: **die Senkrechten bleiben
senkrecht.**

Für eine Architektur-Visualisierung ist das kein Geschmack. Stürzende Linien lesen sich
als Schnappschuss; parallele Senkrechten lesen sich als Darstellung eines Bauwerks. Die
Software shiftet darum immer.

**Gemessen am 19.09.2026** über **216 Fälle** — Gebäudehöhen von 3 bis 100 m, vier
Grundrisse von 8 × 8 m bis 60 × 40 m, je drei Standpunkte:

| | |
|---|---|
| Lotabweichung (Neigung der Kamera) | **0,000°** in allen 216 Fällen |
| grösster nötiger Shift | **2,01 mm** |
| Objektivgrenze | 12 mm |
| Fälle über der Grenze | **0 von 216** |

**Eine Berichtigung gegenüber der Vorarbeit**, und sie gehört hierher: Eine frühere Notiz
nannte «unter 2 mm». Über die hier gerechnete, weitere Spanne liegt der grösste Wert bei
**2,01 mm** — knapp darüber. Die Aussage, auf die es ankommt, ändert sich dadurch nicht
(zwei Millimeter gegen eine Grenze von zwölf sind sechsfache Reserve), aber *eine Zahl,
die «unter 2» sagt, wo 2,01 gemessen wird, ist falsch, und sie wäre bei der nächsten
Messung noch falscher geworden.*

**Was diese Zahlen bedeuten, in einem Satz:** Die Software erreicht für jedes praktisch
vorkommende Gebäude eine korrekte Architekturdarstellung mit einem gewöhnlichen
35-mm-Objektiv — und sie muss dafür nie kippen.

> **Nachtrag 29.09.2026 — die Spanne hatte eine Untergrenze, die niemand gerechnet hatte.**
> Die 216 Fälle beginnen bei 3 m Höhe. Am 24.09.2026 zeigte sich, dass Körper **deutlich
> unter Augenhöhe** (Kante 0,1 bis 1,2 m) die Rechnung mit einem Absturz (`TypeError`)
> abbrechen liessen. Die Physik dahinter ist einfach: Die Kamera steht auf 1,70 m, der
> Körper ist 1 m hoch und nur 3 m entfernt; der Blick müsste steil nach unten, und der
> nötige Shift (−12 bis −17 mm) übersteigt die halbe Sensorhöhe, die im Bildformat 16:9 nur
> 10,1 mm beträgt.
>
> Behoben, ohne zu kippen: Die Kamera wird in diesem Fall **waagrecht zurückgenommen**, bis
> der Shift wieder in den Rahmen passt, und eine Warnung sagt es (`kameras._shift_zu_steil`).
> Alle Fälle, die vorher nicht abbrachen, bleiben bitgleich. *Der Satz «sie muss dafür nie
> kippen» gilt weiter — aber «für jedes praktisch vorkommende Gebäude» war am 19.09.2026
> nicht gerechnet, sondern angenommen.* Ein Sockel, eine Mauer oder ein Möbelstück als
> Modell lag ausserhalb der gerechneten Spanne.

---

## 5.4 Die Rahmung, und ein Befund, der eine Annahme umgeworfen hat

Ein Bild, in dem das Gebäude die ganze Fläche füllt, ist unbrauchbar: Es fehlt der
Zusammenhang. Ein Bild, in dem es als Fleck in der Mitte sitzt, ebenso. Die Software zielt
auf einen **Deckungsgrad von 0,70** — das Bauwerk füllt 70 % der Bildhöhe.

Gemessen: Der bestellte Wert wird **exakt** erreicht (0,7000 in allen gerechneten Fällen).

**Und dann der Befund, der eine Annahme umgeworfen hat.** Der Deckungsgrad wurde gegen die
**Szenenbox** gerechnet — also gegen alles, was in der Datei steht, Gelände eingeschlossen.
Bei einem Modell mit Geländeplatte füllt darum *die Platte* 70 % des Bildes, und das
Bauwerk schrumpft auf **0,2795**.

Das Bild war formal richtig und praktisch unbrauchbar. Die Software rahmt seither gegen
die **Bauwerksbox**, die aus der Szene herausgerechnet wird — und dieser Befund ist der
Grund, warum es die Trennung von Gelände und Bauwerk überhaupt gibt.

*Eine Rahmung, die das Gelände rahmt, ist keine falsche Rechnung. Sie ist die richtige
Rechnung auf den falschen Gegenstand.*

> **Berichtigt 29.09.2026 — «exakt erreicht, in allen gerechneten Fällen» galt nur für die
> gerechneten Fälle.** Am 24.09.2026 wurden von drei automatischen Kameras am Testbau
> (8 × 5 × 3 m) nur eine gerendert. Die zwei Über-Eck-Ansichten füllten 63,9 % des Bildes,
> und der eigene Rahmungsriegel (`BILDBREITE_ABBRUCH`, 0,65) sperrte sie — zu Recht, denn
> unter rund 0,65 trägt die Geometrieprüfung nicht.
>
> **Die Ursache war eine gesetzte Zahl.** Der Abstand wird aus drei Kandidaten gewählt; einer
> davon ist eine Untergrenze aus halber Tiefe plus `WANDABSTAND_M`, und der stand auf
> **10 m — gesetzt, nie gemessen.** Bei kleinen Bauten war diese Untergrenze massgebend und
> stellte die Kamera zu weit weg:
>
> | Körper | Füllgrad bei 10 m | bei 3 m |
> |---|---|---|
> | Kiosk (klein) | 0,432 | 0,699 |
> | Pavillon | 0,518 | 0,699 |
> | Testbau 8 × 5 × 3 m, alle zwölf Richtungen | 0,517 – 0,699 | 0,697 – 0,700 |
> | Bauten ab 12 m Kante | — | bitgleich |
>
> Seit dem 24.09.2026 gilt `WANDABSTAND_M = 3.0`. Der Baukörper dieses Kapitels (12 × 15 ×
> 9 m) ist davon nicht betroffen; die Zahlen oben bleiben für ihn richtig. **Der Riegel ist
> nicht gesenkt worden** — *die Schwelle zu senken hätte das Symptom zugedeckt und die
> Ursache stehen lassen.* Am Gerät bestätigt am 24.09.2026 (`auf-20260924-169`: drei Bilder,
> Füllgrad 0,699 / 0,70 / 0,70).

---

## 5.5 Wo die Software bewusst **nicht** entscheidet

Für Innenräume rechnet die Software je Raum zwei Standpunkte: **frontal** auf eine Wand
und **über Eck**. Sie liefert beide und wählt nicht aus.

Das ist keine Unfertigkeit, sondern ein Entscheid. Welche der beiden Ansichten die bessere
ist, hängt davon ab, ob die Stirnwand ein Motiv trägt — einen Kamin, eine Küchenzeile, ein
Fenster mit Aussicht. **Das steht in keinem Gebäudemodell.** Eine Software, die hier
wählte, ersetzte eine Information durch eine Vermutung.

Beide Ansichten zu rechnen kostet nichts; beide zu rendern kostet. Die Software rechnet
darum immer beide und rendert **nur auf Bestellung** — bei zwanzig Räumen wären es sonst
vierzig Läufe.

Die Kamera steht dabei auf halber Raumhöhe, damit Boden und Decke gleich viel Bild
bekommen, und **waagrecht**, aus demselben Grund wie aussen.

---

## 5.6 Was die Software über ihre eigene Entscheidung sagt

Jeder gerechnete Standpunkt trägt seine Begründung mit. Nicht «Kamera nNE», sondern:

> *«80 % des besten Flächenanteils dieses Satzes (0,2460), zweite Fassade 88 % der ersten
> — Güte 0,7021. Kleinster Winkelabstand im Satz: 90° (ideal 120°). **EINE VON 8
> GLEICHWERTIGEN.»***

Der letzte Satz ist der wichtigste. Bei einem symmetrischen Baukörper gibt es **acht**
gleich gute Dreierkombinationen; die Software nimmt eine und **sagt, dass es acht gab**.

*Eine Software, die aus acht gleichwertigen Möglichkeiten eine nimmt und sie als die
richtige ausgibt, hat eine Willkür in eine Aussage verwandelt.*

### Nachtrag 29.09.2026: gleichwertig heisst manchmal gleich — die Zwillinge

Symmetrie hat eine zweite Folge, die im Entwurf fehlt: Zwei gewählte Standpunkte können
**dasselbe Bild** ergeben. Seit dem 26.08.2026 gibt es dafür eine Zwillingserkennung — eine
Kamera mit derselben Soll-Tiefenkarte wie eine andere wird nicht noch einmal gerechnet.

**Sie hat im Betrieb nie gegriffen.** Am 24.09.2026 lieferte die Messmaschine für den
punktsymmetrischen Testbau zwei byte-gleiche Bilder (`sSE` und `nNW`), beide gerechnet —
468 s für nichts (`auf-20260924-169`). Nachgestellt mit echtem Blender, zwei Ursachen:

1. Der Betrieb liefert die Tiefenkarte **flach**, die Erkennung erwartete **Zeilen**. Sie
   stolperte an der ersten Zahl und meldete still «nicht vergleichbar». Die Proben fütterten
   Zeilen und blieben grün.
2. Selbst richtig gelesen, unterscheiden sich die beiden Karten um bis zu 9,5·10⁻⁶ m
   (Rechenrauschen bei rund 10 m Abstand); ein Abgleich auf sechs Nachkommastellen kippte
   daran.

Behoben mit einer Toleranz von 1 mm, zwei Grössenordnungen über dem gemessenen Rauschen,
und Proben in der Datenform des Betriebs. *Eine Probe, die die Datenform selbst erfindet,
prüft die Erfindung.* Am Gerät steht die Bestätigung aus (`auf-20260924-173`, Einbau-Stand
C22 *gebaut, am Gerät unbestätigt*).

**Und am 29.09.2026 hatte die Erkennung recht, wo es zuerst nach einem Fehler aussah:** Zwei
von Hand gesetzte Standpunkte lagen punktgespiegelt um die Gebäudemitte, und der Testbau ist
ein Rechteck — beide Tiefenkarten waren wirklich gleich (nächster Punkt 6,030965 gegen
6,030963 m). Nebenbefund: `tools/make_test_ifc.py` nennt den Testbau «asymmetrisch»; das
gilt für eine Spiegelung, nicht für eine Drehung um 180 Grad.

---

## 5.7 Grenzen dieses Kapitels

**Erstens, und es ist die wichtigste: Die Innenansichten erreichen den Betriebsweg
nicht.** Nicht wegen einer fehlenden Zeile, sondern aus einem strukturellen Grund: Räume
sind ein Begriff des Gebäudemodells (`IfcSpace`). Der Renderweg bekommt aber eine
**Dreiecksdatei** — dort sind Wände und Böden Dreiecke ohne Raumbegriff. *Der einzige
Moment, in dem sich die Frage «welche Räume gibt es?» beantworten lässt, liegt vor der
Umwandlung.*

Die Zuständigkeit dafür liegt bei der Gegenseite und ist als Auftrag gestellt. **Die
Antwort fehlt**, und sie gehört in dieses Kapitel und nicht in den Ausblick: Es ist eine
offene Frage der Arbeit, keine Idee für später.

*Nachtrag 19.09.2026:* Die Gegenseite hat gemeldet, dass ihre Brücke das Dateiformat bis
zum 11.09.2026 unbedingt auf die Dreiecksdatei zurückgebogen hat. **Der Weg war also nicht
ungenutzt, sondern blockiert** — und seit dem 11.09. ist er es nicht mehr, ohne dass es
jemand wusste. Die Frage ist damit neu gefasst und erneut gestellt.

**Zweitens: Die Standpunkte sind gerechnet, nicht beurteilt.** Dass alle acht Ecken im
Bild sind und der Deckungsgrad stimmt, ist geometrisch nachgewiesen. Ob das Bild *gut
aussieht*, ist damit nicht gezeigt und wird in dieser Arbeit auch nicht behauptet.

**Drittens: Das Gütemass ist gesetzt.** Die Abwägung zwischen Flächenanteil und zweiter
Fassade folgt keiner Messung, sondern einer Setzung darüber, was eine brauchbare
Architekturansicht ausmacht. Sie ist begründet und im Ergebnis sichtbar — aber sie ist
nicht kalibriert, und eine andere Gewichtung ergäbe andere Standpunkte.

---

## Belegstellen

| Abschnitt | Im Repo |
|---|---|
| Alle Zahlen dieses Kapitels | `src/aiimaging/kameras.py`, gerechnet am 19.09.2026 |
| 5.2 Zwölf Richtungen, Auswahl | `kameras.RICHTUNGEN`, `kameras.standpunkte`, `docs/RICHTUNGEN_2026-08-28.md` |
| 5.3 Shift statt Kippen | `kameras.MAX_SHIFT_MM`, `docs/KAMERANEIGUNG_2026-08-22.md` |
| 5.4 Rahmung und Bauwerksbox | `src/aiimaging/glbbox.py`, `docs/BODENANTEIL_2026-08-26.md` |
| 5.5 Innenansichten | `src/aiimaging/raumkamera.py`, `docs/INNENANSICHT_2026-09-09.md` |
| 5.7 Die offene Zuständigkeit | `auftraege/offen/auf-20260909-91.json` |
