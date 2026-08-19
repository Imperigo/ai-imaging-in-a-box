# Nein, `geom_iou` darf nicht fallen — ρ über der Maske ist gegen ein leeres Grundstück erpressbar

**`auf-20260821-25`, HomeStation · vier Halluzinationsfälle, nur ρ mit Vorzeichen**

---

## Die Antwort in einem Satz

**Die falsifizierbare Behauptung ist widerlegt.** H1 und H2 sollten auf oder unter dem
Rauschboden landen — sie landen **darüber**, und deutlich.

| Fall | ρ bei 59.8 % | ρ bei 29 % | gegen Rauschboden **−0.5207** |
|---|---|---|---|
| **H1** · Bauwerk ganz weg, nur Gelände | **−0.6861** | −0.6885 | **besser als Rauschen** ✗ |
| **H2** · Bauwerk 20 m versetzt, im Bild sichtbar | **−0.6854** | −0.6886 | **besser als Rauschen** ✗ |
| H3 · andere Kubatur am richtigen Ort | **+0.3842** | +0.3960 | weit schlechter ✓ |
| H4 · Bauwerk 90° gedreht am richtigen Ort | **−0.4546** | −0.4594 | schlechter ✓ |
| *Anker* weisses Rauschen | −0.5207 | −0.5207 | — |
| *Anker* leeres Graubild | +0.3174 | +0.3174 | — |
| *Anker* Verlauf quer | +0.5729 | +0.5729 | — |

**Ein leeres Grundstück schlägt weisses Rauschen.** Die Sorge war berechtigt: Der
monokulare Schätzer legt über Boden und Himmel eine glatte Rampe, und diese Rampe
korreliert mit der Tiefenstaffelung einer Fassade — bei −0.69, also besser als ein um
4 m versetztes echtes Gebäude (−0.739 liegt nahe daran, aber H1 ist nicht weit davon
entfernt).

**H1 und H2 unterscheiden sich um 0.0007.** Ob das Bauwerk fehlt oder zwanzig Meter
entfernt steht, macht an den Maskenpunkten keinen Unterschied — beide zeigen dort Boden
und Himmel. Genau der Fall, vor dem der Auftrag gewarnt hat.

---

## Was ρ über der Maske dagegen sehr gut kann

**H3 (+0.3842) und H4 (−0.4546) liegen beide schlechter als der Rauschboden**, H3 sogar
im Positiven. Eine falsche Kubatur am richtigen Ort und ein um 90° verdrehtes Gebäude
werden also sauber gefangen.

Damit ist die Rolle von ρ über der Maske genau umrissen:

> **ρ misst, ob die Tiefen innerhalb der Maske richtig gestaffelt sind. Es misst nicht,
> ob dort überhaupt gebaut wurde.**

Das ist keine Schwäche der Grösse, sondern ihre Definition — und exakt die Lücke, für
die `geom_iou` ursprünglich gebaut wurde. **Der Halluzinationsfänger muss bleiben.**

---

## Was von der Maske trotzdem bleibt

1. **Die Szenenunabhängigkeit hält auch hier.** Alle vier Fälle liegen über beide Szenen
   auf höchstens **0.012** beieinander — dieselbe Eigenschaft, die die Normierung nie
   erreicht hat, und sie überlebt den Halluzinationstest.
2. **Die Monotonie und das Vorzeichen bleiben gültig** (`auf-24`): streng monoton über
   Verschiebung und Drehung, Grau und Verlauf kippen ins Positive.
3. **Was fällt, ist nur die Hoffnung, ρ allein genüge.** Die Maske hat die
   Szenenabhängigkeit gelöst; sie löst nicht die Anwesenheit.

**Der Umbau, den ich daraus ableiten würde — als Vorschlag, nicht als Messung:** zwei
Zahlen statt einer. ρ über der Maske für die **Richtigkeit** der Tiefenordnung, und
daneben eine Anwesenheitsprüfung für die **Existenz** des Bauwerks. Ob letztere `geom_iou`
in seiner heutigen Form sein muss, ist damit **nicht** entschieden — nur, dass ohne sie
ein leeres Grundstück durchginge.

*Ein Kandidat, ausdrücklich ungemessen:* Der Tiefen**umfang** innerhalb der Maske. Ein
Baukörper spannt dort einen anderen Bereich auf als Boden-und-Himmel. Das wäre die
nächste billige Messung — dieselben acht Bilder liegen schon da.

---

*Acht Blender-Läufe, elf Auswertungen, kein Bildmodell. Maske, Soll-Karte und Kamera
unverändert aus `auf-24`; geändert wurde ausschliesslich das gerenderte Bild.*

---

# Nachtrag: Mein eigener Kandidat für die Anwesenheitsprüfung fällt durch

Ich habe oben den Tiefen**umfang** innerhalb der Maske als «nächste billige Messung»
vorgeschlagen. Sie war billig — dieselben Bilder, nur elf Schätzungen — und sie ist
**negativ ausgefallen**. Damit steht sie hier, bevor jemand Zeit hineinsteckt.

Gemessen als **Spannenanteil**: der Abstand vom 5.- zum 95.-Perzentil *innerhalb der
Maske*, geteilt durch denselben Abstand über das *ganze Bild*. Das Verhältnis ist
massstabsfrei, weil der Schätzer jedes Bild anders normiert.

| Bild | Spannenanteil |
|---|---|
| perfekt (unverstellt) | **0.4691** |
| **H1 · Bauwerk ganz weg** | **0.4443** |
| **H2 · 20 m versetzt** | **0.4492** |
| H3 · andere Kubatur | 0.6392 |
| H4 · 90° gedreht | 0.6709 |
| Versatz 1 m | 0.5184 |
| Versatz 4 m | 0.7158 |
| weisses Rauschen | 0.3344 |
| leeres Graubild | 0.1046 |
| erzeugt, `seed` 1000 | 0.2367 |
| erzeugt, `seed` 1004 | 0.1775 |

**H1 und H2 liegen innerhalb von 5 % des perfekten Bildes.** Genau die zwei Fälle, für die
die Prüfung gebaut wäre, unterscheidet sie nicht. Der Grund ist im Nachhinein
offensichtlich: An den Maskenpunkten spannt Boden-plus-Himmel einen ganz ähnlichen
Tiefenbereich auf wie eine Fassade davor — die Maske liegt ja genau dort, wo das Gebäude
den Blick auf beides verstellt.

**Und die Grösse zeigt sogar in die falsche Richtung:** H3, H4 und der 4-m-Versatz liegen
**über** dem perfekten Wert. Der Spannenanteil wächst mit dem geometrischen Fehler, statt
mit der Abwesenheit zu fallen. Als Anwesenheitsprüfung ist er damit nicht nur unbrauchbar,
sondern irreführend.

*Was die Zahlen nebenbei bestätigen:* Die erzeugten Bilder (0.18–0.24) liegen unter dem
Rauschen (0.33) und nahe beim leeren Graubild (0.10). Auch auf dieser Achse ist die Kette
näher an einem leeren Bild als an einem Bauwerk — dasselbe Bild wie bei ρ.

**Die Frage «was ersetzt `geom_iou`» bleibt damit offen**, und mein erster Vorschlag ist
vom Tisch. Der nächste, den ich nicht gemessen habe: eine Prüfung nicht auf Zahlen der
Tiefenkarte, sondern auf **Kanten** — ein Bauwerk hat an der Maskengrenze eine
Tiefenkante, ein leeres Grundstück nicht.
