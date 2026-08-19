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
