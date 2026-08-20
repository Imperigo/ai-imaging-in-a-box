# Das ControlNet hat nie eine Tiefenkarte gesehen

**HomeStation, 20.08.2026 · und es erklärt ein halbes Dutzend Messungen rückwirkend**

---

## Der Fund

`auf-20260820-22` hat gemessen und benannt, aber nicht erklärt:

> *«Die Konditionierung bewegt die Silhouette, nicht die Tiefenordnung.»*
> |ρ| lag über **alle vier** Varianten bei 0.45–0.49 — **auch mit abgeschalteter
> Konditionierung**.

Der Grund steht in einer Zeile, die seit Beginn unverändert dastand:

    tiefe = Image.open(parameter["depth_png"]).convert("RGB")

Unser Multipass schreibt `tiefe_norm.png` als **16-Bit-PNG** (PIL-Modus `I;16`). PIL
**klippt** beim Wandeln nach RGB bei 255, statt den Wertebereich zu skalieren. An unserer
eigenen Karte gemessen:

| | verschiedene Werte |
|---|---|
| roh (`I;16`) | **235** — sauberer Tiefenverlauf |
| nach `convert("RGB")` | **2** — 40 % schwarz, 60 % weiss |

**Das ControlNet hat nie eine Tiefenkarte gesehen. Es hat eine Schwarzweiss-Schablone
gesehen.**

Damit ist alles erklärt: Eine Schablone trägt die **Silhouette** exakt und **keine
Ordnung**. Dass |ρ| auch ohne Konditionierung gleich blieb, war kein Rätsel, sondern die
Feststellung, dass nichts zu übertragen war.

---

## Der Beleg

Gleiche Szene, gleicher Prompt, gleiche Stärke, **eine Änderung**: die Karte auf 8 Bit
skaliert statt geklippt. Gemessen mit ρ über der Bauwerksmaske — je negativer, desto besser.

| Seed | 16 Bit, geklippt | 8 Bit, skaliert |
|---|---|---|
| 1000 | −0.0958 | **−0.7486** |
| 1002 | −0.0680 | **−0.5790** |
| 1004 | −0.2540 | **−0.9059** |
| **Mittel** | **−0.1393** | **−0.7445** |
| Standardabweichung | 0.1004 | 0.1635 |

**Der Unterschied beträgt 0.605 — das 3,7-Fache der grösseren Streuung.** Jeder skalierte
Lauf schlägt jeden geklippten; die beiden Wertebereiche überschneiden sich nicht.

Zur Einordnung, dieselbe Szene und dasselbe Mass:

| | ρ über der Maske |
|---|---|
| perfektes Blenderbild | −0.9874 |
| **bester skalierter Lauf** | **−0.9059** |
| **Mittel skaliert** | **−0.7445** |
| weisses Rauschen | −0.5207 |
| Mittel geklippt (bisheriger Stand) | −0.1393 |

Der beste Lauf liegt jetzt **nahe am perfekten Bild**. Vorher lagen alle Läufe
**schlechter als weisses Rauschen**.

**Und der Augenschein stimmt zu:** Das alte Bild zeigte einen massiven Betonblock mit
Himmel darüber. Das neue zeigt den **offenen Kasten von oben** — Wände, Innenecke,
Öffnung —, also die Kubatur, die in der Soll-Karte steht.

---

## Warum es so lange unentdeckt blieb

**Die eine Zahl, die wir hatten, war blind für genau diesen Verlust.** Eine Schablone
trägt die Silhouette exakt, und `geom_iou` misst die Silhouette. Der Wert lag bei **0.95**,
während die Tiefe verschwunden war.

Das ist dieselbe Lehre wie gestern, nur von der anderen Seite: Eine Metrik, die das Falsche
misst, verbirgt nicht nur schlechte Ergebnisse — **sie verbirgt auch die Ursache.**

*Und eine unbequeme Nebenwirkung, die hierher gehört:* Der **alte** Score fällt durch die
Korrektur von 0.6568 auf 0.2197, weil sein ρ das Vorzeichen wechselt. Wer nur auf ihn
geschaut hätte, hätte diese Verbesserung für einen Rückschritt gehalten und
zurückgebaut.

---

## Was geändert wurde

`render._tiefe_als_rgb` skaliert 16-Bit-Karten auf ihren **tatsächlichen** Höchstwert statt
auf die formale Obergrenze 65535 — die Karte ist bereits je Bild normiert, und eine zweite
Normierung auf 65535 verschenkte Kontrast. Acht-Bit-Karten bleiben unangetastet.

Vier Tests dazu, darunter eine **Gegenprobe**, die festhält, dass der alte Weg wirklich nur
zwei Stufen liefert — sollte PIL das eines Tages selbst richtig machen, fällt unser Umweg
auf und wird geprüft statt blind mitgeschleppt. Suite **2738 grün**.

**Gegenprobe am Produktweg:** Nach dem Einbau erzeugt `render.rendere` für alle drei Seeds
Bilder, die **byte-identisch** zu denen mit der von Hand vorbereiteten Karte sind
(`0d343f18…`, `bb4830f3…`, `ffeedb53…`). Der Fix ist exakt der gemessene Eingriff.

---

## Was das für die Messungen von gestern heisst

**Sie bleiben gültig — sie haben eine Kette mit einer Schablone gemessen.** Die Aussagen
über die *Metrik* (Normierung trägt nicht, `geom_iou` belohnt die Abwesenheit, ρ über der
Maske ist monoton und szenenunabhängig) sind davon unberührt: Sie wurden an Blenders
perfekten Bildern erhoben, die diesen Weg nie nahmen.

**Neu zu bewerten ist alles, was die *Kette* beurteilt hat:**

* «Alle fünf erzeugten Bilder liegen schlechter als weisses Rauschen» — galt für die
  Schablone. **Mit skalierter Karte liegen alle drei darüber**, der beste nahe am perfekten Bild.
* Die Reihen über ControlNet-Stärke und Polarität (`auf-13`, `auf-22`) sind an einer
  Schablone gefahren. **Sie gehören wiederholt**, und diesmal misst ρ über der Maske
  wirklich etwas.

---

*Vier Renderläufe für den Beleg, drei für die Gegenprobe, kein neuer Messaufbau. Die
Ursache stand in einer Zeile, die niemand angesehen hat, weil die Zahl daneben gut aussah.*
