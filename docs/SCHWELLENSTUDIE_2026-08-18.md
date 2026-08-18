# Schwellenstudie I · Kalibrierung der Geometrie-Metrik

**18.08.2026 · Sitzung 07 · Modul `aiimaging.schwellenstudie`, Tabellen aus `studienlauf`**

Dies ist die erste Hälfte der in `docs/PLAN.md` unter Phase 4 geforderten
Schwellenstudie. Sie kalibriert **die Metrik**, nicht die Kette — was das ausschliesst,
steht in Kapitel 5, und dieses Kapitel ist das wichtigste des Dokuments.

---

## 0 · Das Ergebnis in drei Sätzen

1. Die Metrik ist **nachweislich rangbasiert**: streng monotone Umrechnungen der Tiefe
   (Massstab, Nullpunkt, Potenz) lassen den Score bei **exakt 1,000**. Das ist die einzige
   Prüfung hier, die die Metrik hätte widerlegen können, und sie ist bestanden.
2. Die Schwelle **0,65 ist zu milde**. Von 36 gestörten Fällen lässt sie **22 durch**;
   die Trefferquote liegt bei **0,39**. Die beste Schwelle auf dieser Szene ist **0,90**
   (Trefferquote 0,75–0,83), und sie ist über drei Auflösungen hinweg dieselbe.
3. Zwei Abweichungsarten sieht die Metrik **fast gar nicht**: verlorene Gliederung
   (Score 0,996 bei stärkster Glättung) und eine **vertauschte Tiefenordnung**
   (Score 1,000 bei Spearman −1,000). Die zweite ist bekannt und gewollt, die erste
   nicht.

**Trotzdem bleibt `SCHWELLE_GEOMETRIE` vorläufig bei 0,65.** Begründung in Kapitel 6 —
kurz: 0,90 gegen 0,65 zu tauschen hiesse, eine unbegründete Zahl durch eine schwächer
unbegründete zu ersetzen, solange der Tiefenschätzer nicht in der Messung steckt.

---

## 1 · Wie gemessen wurde

Eine synthetische Soll-Tiefenkarte wird **gezielt verfälscht**, in acht Störungsarten
über je sieben Stärken. Jede Störung bildet eine reale Fehlerart eines Bildmodells nach
und trägt eine **Erwartung**, welchen Anteil des Scores sie treffen soll. Ob die
Erwartung eintrifft, ist damit prüfbar und nicht Auslegungssache.

Der Score ist `sqrt(|spearman| × geom_iou)` — Rangkorrelation über die gemeinsame
Silhouette, mal Silhouetten-Überdeckung.

| Störung | entspricht | erwartet: Spearman | erwartet: IoU |
|---|---|---|---|
| `rauschen` | Messrauschen des Tiefenschätzers | fällt | bleibt |
| `silhouette_wachsen` | das Modell baut an | bleibt | fällt |
| `silhouette_schrumpfen` | das Modell lässt weg | bleibt | fällt |
| `verschiebung` | verrutschte Kamera | fällt | fällt |
| `glaettung` | verlorenes Detail | fällt | bleibt |
| `zusatzkoerper` | Halluzination: Bau, wo Himmel sein müsste | bleibt | fällt |
| `tiefenumkehr` | **Kontrolle** — falsche Polarität | bleibt | bleibt |
| `monoton` | **Kontrolle** — Massstab/Nullpunkt/Potenz | bleibt | bleibt |

**Alle 48 auswertbaren Zeilen erfüllen ihre Erwartung.** Die Störungen treffen also das,
was sie treffen sollen — die Messinstrumente sind in Ordnung.

---

## 2 · Die Szene musste zweimal gebaut werden, und das ist ein Befund

Der erste Lauf lieferte zwei unbrauchbare Zeilen. Beide lagen an der **Testszene**, nicht
an der Metrik — und beide wären als Aussage über die Metrik durchgegangen, hätte man
nicht nachgesehen.

**`glaettung` war völlig wirkungslos** (Score 1,000 bei jeder Stärke). Die erste Szene war
eine reine Rampe, und der Mittelwert einer linearen Folge ist wieder dieselbe Folge — die
Störung hatte schlicht nichts zu zerstören. Erst ein **Tiefensprung** (ein vorspringender
Flügel) gibt ihr eine Kante.

**Die Monotonie-Kontrolle scheiterte scheinbar** — Score 0,999997 statt 1,0. Die Diagnose:
Die erste Szene hatte **1837 gleiche Werte auf 1936 Punkte**, weil das Gefälle aus der
Summe zweier gleichgewichteter Achsenanteile entstand. Über so einer Karte ist die
Rangkorrelation grösstenteils eine Rechnung über Bindungsgruppen, und die
Fliesskomma-Umrechnung zerlegte sie anders. Mit einem **inkommensurablen** Achsenverhältnis
(√2) fällt die Bindungszahl auf **0**, und die Kontrolle steht bei exakt 1,000.

> **Die Lehre:** Ein Messinstrument kann saubere Zahlen über nichts liefern. Beide Fehler
> sahen wie Aussagen über die Metrik aus („Glättung schadet nicht", „das Verfahren ist
> nicht ganz rangbasiert") und waren Aussagen über die Szene.

---

## 3 · Die Kurven

Score bei Störungsstärke 0,0 bis 1,0 (Szene 64×64, `seed=0`). **Fett** = fällt unter 0,65.

| Störung | 0,0 | 0,1 | 0,2 | 0,3 | 0,5 | 0,7 | 1,0 |
|---|---|---|---|---|---|---|---|
| `rauschen` | 1,000 | 0,989 | 0,962 | 0,926 | 0,841 | 0,763 | 0,672 |
| `silhouette_wachsen` | 1,000 | 0,957 | 0,919 | 0,919 | 0,852 | 0,796 | 0,748 |
| `silhouette_schrumpfen` | 1,000 | 0,955 | 0,909 | 0,909 | 0,818 | 0,727 | **0,636** |
| `verschiebung` | 1,000 | 0,947 | 0,896 | 0,896 | 0,801 | 0,712 | **0,627** |
| `glaettung` | 1,000 | 0,999 | 0,998 | 0,998 | 0,997 | 0,997 | 0,996 |
| `zusatzkoerper` | 1,000 | 0,961 | 0,935 | 0,914 | 0,888 | 0,870 | 0,844 |
| `tiefenumkehr` | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 |
| `monoton` | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 |

*(Die Stärkeachse ist bei den räumlichen Störungen grob gerastert — sie rechnet in ganzen
Bildpunkten. Darum sind 0,2 und 0,3 dort mehrfach gleich. Vergleichbar sind die Kurven,
nicht die Stärken untereinander.)*

### Was daran auffällt

**Die Metrik bestraft verlorene Gliederung praktisch nicht.** Acht Mittelungsdurchgänge —
genug, um jede Fassadengliederung auszulöschen — kosten **vier Tausendstel**. Für eine
Architekturarbeit ist das keine Fussnote: Ein Render, der die Kubatur hält und alles
Detail verschmiert, gilt der Metrik als treu. Das ist nicht falsch (die Metrik misst
Geometrietreue, nicht Detailtreue), aber es begrenzt, was ein bestandenes Gate aussagt.

**Ein halluzinierter Baukörper von der Fläche des Baus selbst besteht mit 0,844.** Das
steht in Spannung zu der bisherigen Projektangabe „halluziniert 0,24". Der Unterschied
ist real und wichtig: Der frühere Fall **ersetzte** die Geometrie (der Bau stand woanders),
dieser hier **ergänzt** sie. Ein hinzugefügter Körper senkt nur den IoU, und auch den nur
so weit, wie er Fläche hinzufügt. **Anbauen wird deutlich milder bestraft als versetzen.**

**Die Rangkorrelation ist robuster als erwartet.** Selbst bei stärkstem Rauschen
(σ = eine halbe Bautiefe) bleibt Spearman bei 0,45.

---

## 4 · Die Trennschärfe

Eine Zeile gilt als *treu*, solange ihre Störungsstärke ≤ 0,2 ist. **Das ist eine
Setzung, keine Messung** — sie steht als `grenzstaerke` in jedem Ergebnis, damit niemand
sie für ein Naturgesetz hält. Kontrollen und nicht messbare Zeilen zählen nicht mit.

| Schwelle | Trefferquote | falsch frei | falsch gesperrt |
|---|---|---|---|
| 0,05 – 0,60 | 0,333 | 24 | 0 |
| **0,65** *(heute)* | **0,389** | **22** | **0** |
| 0,70 | 0,417 | 21 | 0 |
| 0,75 | 0,500 | 18 | 0 |
| 0,80 | 0,556 | 16 | 0 |
| 0,85 | 0,667 | 12 | 0 |
| **0,90** *(bestes)* | **0,750** | **8** | **1** |
| 0,95 | 0,750 | 4 | 5 |

**Der auffälligste Wert steht in der letzten Spalte:** Bis einschliesslich 0,85 wird
**kein einziger treuer Fall gesperrt**. Die Schwelle von 0,65 auf 0,85 anzuheben kostet
auf dieser Szene also *nichts* und fängt zehn zusätzliche untreue Fälle.

Über drei Auflösungen geprüft (48², 64², 96²): Die beste Schwelle ist jedes Mal **0,90**,
und 0,65 lässt jedes Mal **22 von 36** durch. Das Ergebnis hängt also nicht an der
Bildgrösse.

---

## 5 · Was diese Studie NICHT zeigt

Dieses Kapitel wiegt schwerer als Kapitel 4.

**Sie kalibriert die Metrik, nicht die Kette.** Im Betrieb liegt zwischen Soll und Ist ein
monokularer Tiefenschätzer (Depth-Anything-V2-Small). Sein Fehler ist hier **nicht
enthalten** — die Ist-Karte entsteht durch direkte Verfälschung der Soll-Karte, nicht
durch Schätzung aus einem Bild. Der Schätzer wird die Zahlen nach unten ziehen, und zwar
unbekannt weit. Eine hier gewonnene Schwelle ist eine Schwelle **für die Metrik**.

**„Treu" ist durch die Störungsstärke definiert, nicht durch ein Urteil.** Dass Stärke 0,2
noch annehmbar sei, ist gesetzt. Ein Architekt könnte einen um vier Bildpunkte versetzten
Bau für völlig in Ordnung halten und einen halluzinierten Anbau für untragbar — die Studie
gewichtet beide gleich.

**Eine synthetische Szene ist kein Haus.** Zwei Quader mit einem Sprung. Fassadentiefe,
Fenster, Vor- und Rücksprünge, Umgebung — nichts davon ist da.

**Die Störungen sind unabhängig, die Wirklichkeit nicht.** Ein Bildmodell rauscht,
verschiebt und halluziniert gleichzeitig. Kombinationen sind nicht gemessen.

**Die Metrik ist blind für die Polarität.** Bestätigt: Score 1,000 bei Spearman −1,000.
Das ist kein Fehler, sondern eine bekannte Grenze des `abs()` im Score — aber sie heisst,
dass die Polarität **ausserhalb** der Metrik festgestellt werden muss. In der Kette tut
das `tiefenschaetzer`, indem er sie nie aus den Daten rät.

---

## 6 · Warum die Schwelle trotzdem bei 0,65 bleibt

0,65 ist unbegründet. 0,90 wäre auf dieser Szene besser begründet — aber „besser
begründet auf einer synthetischen Szene ohne Tiefenschätzer" reicht nicht, um die
Bestehensgrenze eines Verfahrens zu setzen, das auf echte Renders angewandt werden soll.

Der Schätzer fehlt in der Messung, und er ist der grösste unbekannte Anteil: Er senkt jeden
Score, und wie weit, weiss niemand. Eine Schwelle von 0,90 könnte im Betrieb **jeden**
Render sperren, auch den treuen. Genau diese Falle hat das Projekt schon einmal erwischt —
der `geom_iou`-Deckel in Sitzung 06, an dem jeder treue Render durchgefallen wäre.

**Was daraus folgt, ist die zweite Hälfte der Studie:** Dieselben acht Störungen, aber die
Ist-Karte nicht direkt verfälscht, sondern durch den Schätzer aus einem gerenderten Bild
gewonnen. Das braucht GPU und läuft über `auftraege/`. Erst danach lässt sich die Schwelle
mit Grund verschieben.

Bis dahin gilt: **0,65 ist nicht verteidigt, sondern beibehalten.** Der Unterschied gehört
in die Arbeit.
