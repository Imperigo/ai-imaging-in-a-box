# HomeStation, 18.08.2026: die zwei Schwellen, gemessen

**Home-PC-Worker.** `auf-20260818-11` (Boden des Einbetters) und `auf-20260818-10`
(Schwellenstudie, zweite Hälfte). Beide Schwellen des Projekts standen zur Prüfung, und
beide fallen — aber aus entgegengesetzten Gründen.

| Schwelle | Stand | Befund |
|---|---|---|
| Stil, 0.30 | zu niedrig | **wirkungslos** — jedes beliebige Bildpaar besteht sie |
| Geometrie, 0.65/0.90 | zu hoch | **unerreichbar** — auch ein perfektes Bild kommt nur auf 0.51 |

---

## 0 · Ein Befund vorweg: der Auftrag war so nicht ausführbar

Der befohlene Aufruf `homeworker.py --auftrag auf-20260818-11` hätte **nichts gemessen**.
Für `art: "qa"` läuft in `tools/homeworker.py` nur der Blender-Multipass; die Wörter
`einbetter`, `stoerungen` und `boden` kommen in der Datei nicht vor. Beide Aufträge wären
mit `status: ok, urteil: {multipass: ok}` zurückgekommen — grün, ohne eine einzige der
verlangten Zahlen.

Das ist dieselbe Fehlerbauart, vor der ein Kommentar in derselben Datei warnt
(«unauffindbar, weil als erledigt abgehakt») — nur eine Ebene höher: Dort fehlte ein
Artefakt, hier ein Auswerter. Beide Male ist die stille Variante die schlimme. Ein
Auftrag, der abbricht, kostet einen Lauf; einer, der grün und leer zurückkommt, kostet das
Vertrauen in alle anderen.

**Behoben:** `_unverstandene_params` lehnt einen Auftrag ab, dessen `params` dieses Skript
nicht verbraucht. Die Grenze läuft zwischen *hier ungenutzt* (ein `prompt` an einem
Multipass — harmlos, bestehende Tests stellen solche Aufträge) und *hier unbekannt*
(`stoerungen`, `einbetter` — sie verlangen einen anderen Auswerter). Geprüft an allen vier
offenen Aufträgen: `-08`, `-10`, `-11` werden abgelehnt, `-09` läuft unverändert durch.

---

## 1 · Der Boden von SigLIP 2 liegt über der Stil-Schwelle

```
Boden      +0.5259 ± 0.0698      Median 0.5232
Spanne     +0.3097 … +0.8448     4950 Paare aus 100 Bildern, 768 Dimensionen
Perzentile p90 0.617 · p99 0.698 · p99.9 0.752
```

**Alle 4950 Paare erreichen die Schwelle 0.30.** Nicht ein paar, nicht die meisten — alle.
Auch das *unähnlichste* Paar des ganzen Korpus liegt mit 0.3097 darüber. Die Schwelle
liegt **3,24 Streuungen unter** dem Boden.

Der Auftrag hatte vorgerechnet: bei isotroper Streuung läge der Boden bei 0.000 ± 0.036,
bei einem Kegelanteil von 0,6 bei 0.36 — und dort wäre er bereits über der Schwelle.
Gemessen sind 0.526. SigLIP 2 besetzt einen **engeren Kegel als der ungünstigste
vorausberechnete Fall**.

Damit bestätigt sich auch der Verdacht, der die alte Zahl entwertet: Der überlieferte
Fehlbereich 0.06–0.13 aus den DINOv3-Läufen liegt nicht einmal in der Nähe des
SigLIP-2-Bodens. Er war der Boden *jenes* Einbetters und ist beim Modellwechsel in
Sitzung 06 stillschweigend mitgewandert.

### Hängt das am Korpus?

Nein, und das ist geprüft statt behauptet. Der Korpus hat bekannte stilistische Häufungen
— rund neun Studiofreisteller vor neutralem Grund, acht Reproduktionen flacher
Papierwerke. Sie **heben** den Boden, wirken also gegen die Aussage.

| | Mittelwert | Streuung | Maximum |
|---|---|---|---|
| alle 4950 Paare | 0.5259 | 0.0698 | 0.8448 |
| ohne die 5 % ähnlichsten (4703 Paare) | 0.5180 | 0.0618 | 0.6472 |

Auch das Maximum der verbleibenden Paare liegt bei mehr als dem Doppelten der Schwelle.
Es gibt keinen Zuschnitt dieses Korpus, unter dem 0.30 wieder Sinn ergäbe.

### Zum Korpus selbst

100 Bilder aus Wikimedia Commons, Lizenz je Datei aus `extmetadata.License` der API
gelesen — nicht vermutet: 34 Public Domain, 14 CC0, 52 CC-BY in vier Fassungen.
**Kein Share-Alike, kein unklarer Status.** 65 Motivbereiche, kurze Bildkante 443–960 px
(nichts hochskaliert), keine Dubletten (dHash-Distanz aller 4950 Paare > 12 Bit), keine
Architekturserie, keine gerenderten 3D-Modelle.

### Was folgt

Die Schwelle braucht keinen besseren **Wert**, sondern ein **Verfahren** — genau wie
vermutet. Ein fester Wert ist an den Einbetter gebunden und stirbt mit ihm. Auf Basis
dieser Zahlen: Boden je Einbetter messen, Schwelle als «Boden + k Streuungen» setzen. Für
SigLIP 2 base ergäbe k=2 eine Schwelle von 0.666, k=2.5 eine von 0.701 (das p99 des Bodens
liegt bei 0.698).

**Welches k richtig ist, sagt diese Messung nicht.** Dafür braucht es Paare, die
stilistisch ähnlich sein *sollen*. Der Boden ist die eine Hälfte der Kalibrierung, nicht
die ganze.

Und eine Warnung zur Übertragung: Diese Zahlen gelten für `siglip2-base-patch16-224` und
den **`pooler_output`**. Ein anderer Ausleseort desselben Modells — etwa gemittelte
Kachel-Vektoren aus `last_hidden_state` — hat einen anderen Boden. Wer die Schwelle
übernimmt, muss den Ausleseort mitübernehmen, sonst wiederholt sich genau der Fehler, der
0.30 hierher gebracht hat. (Der Ausleseort ist hier nicht theoretisch: Ein erster
Messversuch griff `[0]` des Rückgabeobjekts ab und bekam den `last_hidden_state` mit
196×768 Werten statt der Bildeinbettung. Das fiel nur auf, weil die Dimension als 1
gemeldet wurde.)

---

## 2 · Die Geometrie-Schwelle ist unerreichbar, und der Grund ist nicht der Schätzer

Die Nullprobe des Auftrags — ungestörte Geometrie durch die ganze Kette — ergibt
**0.033**. Das ist so niedrig, dass es zunächst wie ein Kettenfehler aussieht. Es ist
keiner, aber die Zahl vermischt **zwei** Fehler: den des Tiefenschätzers und die Untreue
des Bildmodells. Der Auftrag fragt nach dem ersten.

Darum eine zusätzliche Messung, die der Auftrag nicht verlangt hat und ohne die seine
Frage nicht beantwortbar ist: **derselbe Schätzer auf Blenders eigenen Beauty-Pass** —
gleiche Szene, gleiche Kamera, gleiche Auflösung, kein Bildmodell dazwischen. Ein Bild
also, das die Geometrie **exakt** zeigt.

```
spearman             -0.9904     Betrag 0.990
geom_iou              0.2612
score                 0.5086     = sqrt(0.990 × 0.261)
polaritaet            disparitaet
n_soll = n_ist        44 604      n_gemeinsam  18 476
```

**Der Schätzer ist nicht das Problem.** Seine Tiefenordnung ist mit |ρ| = 0.990 nahezu
fehlerfrei; das negative Vorzeichen ist die Disparitätskonvention, die die Metrik korrekt
über den Betrag abfängt und die sie selbst als `polaritaet: disparitaet` erkennt.

Das Problem ist `geom_iou` = 0.261 — **bei einem Bild, das die Geometrie exakt zeigt.**
Und weil der Score das geometrische Mittel beider Grössen ist, deckelt das die ganze Kette
bei 0.509.

### Warum die Silhouette nicht trifft

Nachgesehen statt vermutet. Die Auswahlregel `wie_soll` nimmt aus der Ist-Karte so viele
Punkte als «Geometrie», wie das Soll hat — die mit der grössten Disparität, also die
nächsten. Eine Maske dieser Auswahl, gegen die Soll-Silhouette gehalten, zeigt:

- **34 %** der ausgewählten Punkte liegen auf dem Bauwerk,
- der grosse Rest bildet einen **Keil in der oberen rechten Bildecke** — also im leeren
  Hintergrund,
- und entsprechend fällt rund ein Drittel des echten Baukörpers aus der Auswahl heraus.

Das ist das Verhalten eines monokularen Schätzers, der auf Naturfotos trainiert wurde: In
eine flache, gleichmässige Fläche legt er eine Bodenebene hinein, die zur Bildecke hin auf
die Kamera zuläuft. Der Beauty-Pass zeigt einen Körper vor gleichmässigem Grund — genau
die Situation, in der dieser Vorgriff greift.

### Was das für die Schwellen heisst

Die erste Hälfte der Studie hatte 0.90 als beste Schwelle ermittelt und festgehalten, dass
bis 0.85 kein treuer Fall gesperrt wird. **Beides gilt für die Metrik, nicht für die
Kette.** In der Kette ist 0.90 nicht erreichbar, und 0.65 ebenfalls nicht: Die Obergrenze
liegt bei 0.509, und die wird nur von einem Bild erreicht, das gar nicht erst durch ein
Bildmodell gelaufen ist.

Ein Gate mit diesen Zahlen sperrt **alles**, auch das Treue. Das ist genau die Falle, die
der Auftrag befürchtet hat — nur schlimmer als angenommen: Sie liegt nicht im Schätzer,
sondern in der Silhouettenauswahl davor.

**Der Hebel liegt darum nicht bei der Schwelle.** Solange ein perfektes Bild 0.26 an
`geom_iou` bekommt, ist jede Schwelle über 0.5 eine Ablehnung aller Fälle und jede
darunter eine Aussage über die Rangkorrelation allein. Die Auswahlregel gehört repariert,
bevor die Schwelle wieder verhandelt wird. `qa_gegen_soll` kennt dafür bereits
`hintergrund`, `hintergrund_strategie` und `hintergrund_anteil` — welche Kombination
trägt, ist eine eigene Messung und nicht Teil dieses Auftrags.
