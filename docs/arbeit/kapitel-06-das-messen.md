# 6 · Das Messen: der Kern der Arbeit

> **Stand 21.09.2026 — Entwurf.** Viertes geschriebenes Kapitel, und das tragende.
> **Alle Zahlen sind am 19.09.2026 neu gerechnet**, gegen die Rohdaten in
> `auftraege/ergebnisse/auf-20260909-92-tabelle.json` und den heutigen Quelltext.
> **Nachgetragen am 21.09.2026:** zwei bestellte Messungen sind zurück. Die eine löst den
> Grenzfall aus 6.5 auf — *und zwar zugunsten der Schwelle*. Die andere ist für eine ganz
> andere Frage gefahren worden und liefert die erste Bestätigung des Ergebnisses an
> **fremden Daten** (6.6).
> **Die Strukturnotiz zu diesem Kapitel ist überholt.** Sie nennt als Kernbehauptung einen
> zusammengesetzten Wert — und genau der ist am 18.09.2026 widerlegt worden. Das Kapitel
> ist um das neue Ergebnis herum geschrieben, nicht um das alte.

---

## 6.1 Die Frage, und warum sie schwer ist

Ein Bildmodell erzeugt aus einer Tiefenkarte und einem Satz ein Bild. Die Frage dieser
Arbeit lautet: **Folgt dieses Bild dem Gebäudemodell, aus dem die Tiefenkarte stammt?**

Sie ist aus zwei Gründen schwer.

**Erstens fehlt der Massstab.** Ein Bildmodell erzeugt kein Bild in Metern. Was es liefert,
ist eine Helligkeitsverteilung; ob der Vorsprung vorn zwei Meter oder zwanzig tief ist,
steht nirgends. Ein Mass, das Meter gegen Meter hält, misst darum nichts.

**Zweitens sieht ein falsches Bild nicht falsch aus.** Ein Bildmodell, das ein Geschoss
dazu erfindet, erfindet es *plausibel*. Genau darin besteht seine Leistung. Die Abweichung
ist nicht als Fehler erkennbar, sondern nur als Abweichung — und nur, wenn man etwas hat,
wogegen man hält.

---

## 6.2 Massstabsblind messen: die Rangkorrelation

Der Ausweg aus der ersten Schwierigkeit ist, **nicht die Werte zu vergleichen, sondern
ihre Reihenfolge**. Wenn Punkt A im Modell näher liegt als Punkt B, soll er auch im Bild
näher wirken — wie *viel* näher, ist gleichgültig.

Das leistet eine Rangkorrelation. Sie ist **unempfindlich gegen jede streng monotone
Umrechnung**, und das ist keine Behauptung, sondern geprüft: Rechnet man die Tiefenkarte
mit Potenz 2 um, multipliziert mit 10 und verschiebt den Nullpunkt um −50 m — sodass
**kein einziger Meterwert mehr stimmt** —, bleibt das Mass bei **1,000**.

*Ein Mass, das den Massstab nicht kennt, kann von ihm auch nicht getäuscht werden.*

---

## 6.3 Warum die Rangkorrelation allein nicht genügt

Hier beginnt der eigentliche Gegenstand dieser Arbeit, und er ist eine Reihe von
Fehlschlägen.

### Der Boden rettet die Korrelation

Ein Bild, in dem das **Bauwerk in der Tiefe gespiegelt** ist — vorn und hinten vertauscht —,
während der Boden stimmt, erreicht über das ganze Bild eine Korrelation von **0,962**.
Über die Bauwerksmaske allein: **−1,000**, also die perfekte Umkehrung.

Bei einem Versatz von 16 Bildpunkten dasselbe Muster: **0,993** über das ganze Bild,
**−0,607** über die Maske.

**Der Grund ist geometrisch und nicht statistisch.** Ein Architekturbild ist zum grossen
Teil Boden und Himmel. Beide sind in jeder Version gleich, und sie ziehen die Korrelation
nach oben, ganz gleich, was das Bauwerk tut.

> *Eine Kennzahl über das ganze Bild misst zum grossen Teil den Boden.*

Daraus folgt die Bauwerksmaske: gemessen wird **nur dort, wo das Bauwerk steht.**

### Die Abwesenheit besteht die Prüfung

Der zweite Fehlschlag ist der lehrreichere. Ein Mass, das die Flächenüberschneidung der
Silhouette bewertet, schien geeignet — bis es an einem **leeren Grundstück** gemessen
wurde:

| | |
|---|---|
| leeres Grundstück, kein Gebäude | **0,9848** |
| das perfekte Bild derselben Szene | 0,9703 |

*Die Abwesenheit war besser als die Anwesenheit.* Und drei Nullanker — weisses Rauschen,
eine graue Fläche, ein Verlauf — erreichten **alle drei denselben Wert: 0,6016.** Die
Silhouette allein trägt also 60 % des Masses, bevor irgendetwas gezeigt wird.

### Und der zusammengesetzte Wert vererbt beide Fehler

Die naheliegende Antwort war, beide Masse zu verrechnen und die Wurzel zu ziehen. Sie hat
bis zum 18.09.2026 gegolten, und sie ist **an denselben Daten widerlegt worden, die sie
bestätigen sollten**.

---

## 6.4 Das tragende Ergebnis: es sind zwei Fragen

**Gemessen am 19.09.2026** an zwölf erzeugten Bildern, jedes gegen die richtige **und**
gegen die Tiefenkarte eines **anderen** Gebäudes:

| Der alte, zusammengesetzte Riegel | |
|---|---|
| echte Bilder bestehen | 12 von 12 |
| **absichtlich unbrauchbare Bilder bestehen** | **11 von 12** |
| **echte Bilder gegen eine FREMDE Geometrie** | **12 von 12 bestehen** |

Die zweite Zeile allein wäre eine schlechte Schwelle. **Die dritte ist vernichtend:** Ein
Riegel, der auch gegen das falsche Gebäude durchlässt, prüft nicht die Geometrie. Er prüft
irgendetwas.

**Die Ursache ist keine falsche Schwelle, sondern eine falsche Frage.** Es sind zwei:

| | Frage | Kennzahl |
|---|---|---|
| **A** | Folgt das Bild dem Modell **überhaupt**? | die Rangkorrelation über die Maske |
| **B** | Folgt es **diesem** Modell und keinem anderen? | die Flächenüberschneidung |

Der zusammengesetzte Wert multipliziert A mit B und zieht die Wurzel. **Damit gleicht ein
guter Wert der einen einen schlechten der anderen aus** — und genau das lässt die
unbrauchbaren Bilder durch.

> **Eine Kennzahl, die zwei Fragen zu einer verrechnet, beantwortet keine von beiden.**

### Zwei Tore, mit UND verbunden

Beide Fragen werden getrennt gestellt, und **beide** müssen bestanden sein. Gemessen an
denselben Daten:

| | |
|---|---|
| echte Bilder bestehen | **12 von 12** |
| unbrauchbare Bilder bestehen | **0 von 12** |
| Gegenprobe gegen fremde Geometrie trennt | **12 von 12** |

Die Lücke, auf der Tor B steht, ist gemessen und nicht gesetzt:

    gegen die richtige Karte    0,9257 … 0,9784
    gegen die falsche Karte     0,7350 … 0,7766
    Lücke                       +0,1491      Schwelle 0,85

### Und die Gegenprobe ist eingebaut, nicht angehängt

Das ist der zweite Teil des Ergebnisses und der allgemeinere:

> **Ohne Gegenprobe gegen eine fremde Geometrie ist keine Geometriekennzahl etwas wert.**

Der alte Riegel war nicht deshalb schlecht, weil seine Schwelle falsch lag. Er war
schlecht, weil **niemand ihn je gegen das falsche Gebäude gehalten hatte.** Hätte man es
getan, wäre er am ersten Tag gefallen.

Die Gegenprobe ist darum ein Argument der Prüffunktion selbst. Fehlt sie, gibt es kein
Urteil, sondern eine Warnung. Besteht dieselbe Messung **auch** gegen die fremde Geometrie,
lautet das Urteil **nicht entscheidbar** — nicht «bestanden».

---

## 6.5 Ein Befund gegen die eigene Schwelle

Die Schwelle von Tor A wurde aus einer Lücke abgeleitet: Bei Bildern ohne Führung durch
die Geometrie streut das Mass zwischen **−0,047 und +0,055**; das niedrigste Bild *mit*
Führung lag bei **+0,144**.

**Diese Begründung trägt nicht ganz**, und das steht im Quelltext neben der Zahl. Sie ist
über zwei von drei Messreihen gerechnet; die mittlere war nicht ausgewertet. Dort liegt
ein Bild mit sauber sitzender Silhouette (Flächenüberschneidung 0,9119) bei **−0,155** —
unter dem gesamten Streubereich der unbrauchbaren Bilder.

Paarweise über dieselben Zellen gerechnet:

| Vergleich | Ordnung erhalten |
|---|---|
| volle gegen keine Führung | **12 von 12** |
| volle gegen mittlere Führung | **7 von 12** |

**An den Rändern ist die Ordnung sauber. In der Mitte gibt es keine Ordnung, nur
Streuung** — und für eine Schwelle ist die Mitte genau der Bereich, der zählt.

Der Preis schien gezählt: Bei mittlerer Führung wird **ein Bild von zwölf** abgewiesen —
ein Fehlalarm und kein Durchlasser, also die verzeihliche Richtung.

### Nachtrag vom 21.09.2026: Es war kein Fehlalarm

Die Gegenprobe, die diesen Fall entscheiden würde, war als Messauftrag offen. Sie ist
gefahren — 36 Bilder, jedes gegen die richtige **und** gegen eine falsche Tiefenkarte —
und sie beantwortet die Frage in eine Richtung, die man nicht erwartet:

| Dasselbe Bild, gemessen gegen | Rangkorrelation |
|---|---|
| die **richtige** Geometrie | **−0,155** |
| die **falsche** Geometrie | **+0,300** |

**Das Bild folgt dem fremden Gebäude besser als dem eigenen.** Eine blinde Kennzahl kann
das nicht: Sie sieht dort etwas, und es ist die falsche Form. Das Bildmodell hat aus dem
gegliederten Bau einen Block gemacht — und ein Block ist der Schachtel ähnlicher als dem
Haus, das er darstellen soll.

Das ändert das Urteil über diesen Abschnitt vollständig:

> Die Schwelle hatte recht. Das abgewiesene Bild war **kein brauchbares**, und der
> vermeintliche Fehlalarm war eine richtige Absage.

**Und es liegt nicht an der Führungsstärke**, wie hier zuerst vermutet: Dieselbe Zelle
steht auch bei voller Führung falschherum (+0,144 eigen gegen +0,412 fremd), nur weniger
deutlich. Es ist eine Eigenschaft **dieses einen Falls**, nicht der Einstellung.

*Dieser Abschnitt steht hier und nicht im Anhang, weil ein Kapitel über das Messen, das
den eigenen Grenzfall verschweigt, seine eigene These widerlegt. Er bleibt stehen,
obwohl er aufgelöst ist — denn dass die Auflösung erst eine bestellte Messung brachte,
ist selbst das Ergebnis.*

### Was dieselbe Messung sonst noch umwirft

Ein zweiter Befund aus demselben Lauf verschiebt die Arbeitsteilung der beiden Masse:

| Frage | Werkzeug | Form | gemessen |
|---|---|---|---|
| Folgt das Bild **überhaupt** etwas? | Rangkorrelation | Schwelle | fällt ohne Führung exakt auf null |
| Folgt es **diesem** Modell? | Flächenüberschneidung | **Vergleich** | **24 von 24** richtig geordnet |

Die Rangkorrelation ordnet paarweise nur **19 von 24** richtig. Als *Schwelle* ist sie
das bessere Werkzeug, als *Vergleich* das schlechtere — und umgekehrt.

**Die zweite Frage braucht also gar keine Schwelle, sondern eine zweite Karte.** Das ist
billiger als jede Kalibrierung.

Aber auch hier hält die Messung eine unbequeme Hälfte bereit, die erst beim Nachrechnen
der Rohdaten auffiel: Der kleinste **echte** Abstand zwischen eigener und fremder Karte
beträgt +0,154 — der grösste Abstand im **Rauschen** 0,159. Er ist *grösser*. Zwischen
Signal und Rauschen liegt keine Lücke.

> *Eine Schwelle, die es in den Daten nicht gibt, wird durch Setzen nicht wahr.*

Gewertet wird darum allein das Vorzeichen. Das genügt, weil diese Frage erst gestellt
wird, wenn die erste mit Ja beantwortet ist — *die Ordnung ist nur dort etwas wert, wo
überhaupt etwas geordnet wird.*

---

## 6.6 Die Gegenprobe von aussen — ein Regler, der die Geometrie herausdreht

Bis zum 21.09.2026 ruhte alles in diesem Kapitel auf **einem** Datensatz: zwölf Bilder,
ein Bildmodell, eine Maschine.

> *Ein Ergebnis, das nur an den Daten belegt ist, aus denen es gewonnen wurde, ist eine
> Beschreibung und kein Befund.*

Am 21.09.2026 kam eine zweite Messreihe zurück, die für eine **ganz andere Frage**
bestellt war — ob ein kleines, für einen Laptop taugliches Bildmodell der Geometrie
folgen kann. 78 Bilder, anderes Modell, andere Anbindung, andere Maschine. Sie liefert
nebenbei den stärksten Beleg, den dieses Kapitel hat.

Das Modell hat einen Regler, der bestimmt, wie streng es dem Textbefehl folgt. Man dreht
ihn von 1,0 auf 4,0 und misst mit:

| Regler | zusammengesetzter Wert | Flächenüberschneidung | Rangkorrelation |
|---|---|---|---|
| 1,0 | 0,775 | 0,700 | **0,299** |
| 2,5 | 0,848 | 0,925 | 0,050 |
| 4,0 | **0,876** | **0,975** | **0,030** |

Alles, was der alte Riegel misst, **steigt**. Das eine, worum es geht, **fällt auf null**.

> **Wer nach dem zusammengesetzten Wert optimiert, optimiert die Geometrie weg.**

Und die Flächenüberschneidung gegen die **falsche** Geometrie rührt sich über alle drei
Zeilen kaum: sie bleibt zwischen 0,638 und 0,724. *Eine Zahl, die sich nicht ändert, wenn
man ihr ein anderes Gebäude vorlegt, beantwortet die Frage nach dem Gebäude nicht.* Sie
misst, **wie viel** Bild ein Bauwerk füllt — nicht **welches**.

**Der alte Riegel besteht alle drei Zeilen** — gegen die richtige Karte *und* gegen die
falsche (0,740 / 0,765 / 0,778, alle über 0,65). Zum zweiten Mal, an fremden Daten.

**Die zwei Tore halten alle drei an, und jede aus einem anderen Grund:**

| Regler | was durchfällt | warum |
|---|---|---|
| 1,0 | Tor B | die Silhouette sitzt nicht |
| 2,5 und 4,0 | Tor A | die Bindung an die Tiefe ist weg |

Ein einzelnes Mass könnte das nicht. Bei 4,0 sieht die Flächenüberschneidung mit 0,975
tadellos aus — und genau dort ist die Geometrie verschwunden.

**Was diese Reihe nicht zeigt, und es ist die härtere Hälfte:** Kein einziges dieser 78
Bilder besteht beide Tore. Das ist die richtige Auskunft über diese Bilder — und es heisst
zugleich, dass für das laptoptaugliche Modell **noch kein Weg** gefunden ist, auf dem die
Geometrie ankommt.

---

## 6.7 Grenzen dieses Kapitels

**Erstens, und es ist die schwerste: Die tragende Messung fehlt.** Alle Zahlen dieses
Kapitels sind an **Soll-Karten** gerechnet — an der Tiefenkarte, die das Modell selbst
geliefert hat. Im Betrieb steht dort aber eine **geschätzte** Tiefenkarte, die eine
zweite KI aus dem erzeugten Bild ableitet, und deren Rauschen ist in keiner dieser Zahlen
enthalten.

Nach der Hausregel dieses Projekts dürfen solche Messungen **ausschliessen, aber nichts
zusagen**. Was dieses Kapitel zeigt, ist also: *Der alte Riegel ist widerlegt.* Was es
**nicht** zeigt: dass der neue unter Schätzerrauschen trägt.

Eine erste Messung dazu liegt vor, und sie ist unangenehm: Unter dem Rauschen eines
echten Schätzers gibt es auf **frontalen** Ansichten kein fehlerfreies Fenster mehr — die
Werte guter und schlechter Fälle überlappen fast vollständig. Diagonale Ansichten trennen
weiter. Auch diese Messung stammt aus gerenderten Bildern, nicht aus erzeugten, und
beantwortet die Frage darum **nicht**.

**Zweitens: Zwölf Bilder sind zwölf Bilder.** Ein Bildmodell, eine Maschine, zwei Szenen —
eine Schachtel und ein fünfgeschossiger Bau. Dass die Gegenprobe trennt, ist an **zwei
offensichtlich verschiedenen** Gebäuden gezeigt. Zwei **ähnliche** Gebäude sind nicht
geprüft, und dort wird es schwer. Die Messung dazu ist bestellt.

**Drittens: Beide Schwellen sind gesetzt, nicht kalibriert.** Sie liegen in gemessenen
Lücken, aber *wo* in der Lücke, sagt keine Messung. Bei Tor B ist die Lücke gross genug,
dass es wenig ausmacht; bei Tor A ist sie es nicht — siehe 6.5.

**Viertens, und es gehört dazu:** Der alte Riegel bleibt unverändert neben dem neuen
stehen. Alle bisher veröffentlichten Zahlen dieses Projekts sind mit ihm entstanden und
müssen nachbaubar bleiben. *Die zwei Tore sind der Weg nach vorn, nicht eine Berichtigung
nach hinten.*

---

## Belegstellen

| Abschnitt | Im Repo |
|---|---|
| Alle Zahlen | `auftraege/ergebnisse/auf-20260909-92-tabelle.json`, neu gerechnet 19.09.2026 |
| 6.2 Massstabsblindheit | `docs/POLARITAET_2026-08-21.md` |
| 6.3 Maske und Nullanker | `docs/MASKE_2026-08-21.md`, `docs/BRAUCHT_ES_GEOM_IOU_2026-08-26.md` |
| 6.4 Das tragende Ergebnis | `src/aiimaging.geometrie_qa.zwei_tore`, `docs/R3_WELCHES_MASS_TRENNT_2026-09-18.md` |
| 6.6 Der Regler, der die Geometrie herausdreht | `auftraege/ergebnisse/auf-20260918-114.json` |
| 6.5 Der Befund gegen die eigene Schwelle | Kommentar an `SCHWELLE_FOLGT` in `src/aiimaging/geometrie_qa.py` |
| 6.5 Die Auflösung des Grenzfalls | `auftraege/ergebnisse/auf-20260918-115.json` |
| 6.7 Die Messung unter Schätzerrauschen | `auftraege/ergebnisse/auf-20260907-81.json` |
