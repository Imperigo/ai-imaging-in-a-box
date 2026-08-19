# Der Prüfstein fällt — und der Kandidat lebt trotzdem

**`auf-20260821-27`, HomeStation · keine neuen Bilder, keine Renderläufe**

---

## Die Zahlen

**Mass:** Median der Randpunkte knapp *innerhalb* der Maskengrenze minus Median knapp
*ausserhalb*, geteilt durch die Spanne der ganzen Schätzkarte. Randband je zwei Bildpunkte
(innen 2295, aussen 2334). Der Schätzer liefert Disparität — nah = gross —, ein Bauwerk vor
fernem Grund gibt also einen **positiven** Wert.

| Bild | Kante bei 59.8 % | Kante bei 29 % |
|---|---|---|
| **perfekt (unverstellt)** | **+0.1615** | **+0.2474** |
| Versatz 1 m | +0.0655 | +0.1071 |
| **H3 · andere Kubatur** | **+0.0066** | **+0.0094** |
| **H4 · 90° gedreht** | **+0.0021** | **+0.0051** |
| **H1 · Bauwerk ganz weg** | **+0.0006** | −0.0003 |
| **H2 · 20 m versetzt** | **+0.0007** | −0.0002 |
| weisses Rauschen | −0.0044 | −0.0044 |

## Der Prüfstein, wörtlich genommen: **nicht erfüllt**

> *«Perfekt, H3 und H4 müssen eine DEUTLICHE Kante zeigen — dort steht etwas, wenn auch
> das Falsche. H1 und H2 dürfen keine zeigen.»*

H1 und H2 zeigen keine — richtig. **Aber H3 und H4 auch nicht.** Sie liegen um Faktor 25
bis 75 unter dem perfekten Bild und praktisch auf der Höhe der Abwesenden.

**Warum, und es ist im Nachhinein zwingend:** Die Maske ist die Silhouette des **richtigen**
Bauwerks. Ein gedrehtes oder anders geformtes Bauwerk hat seine Kanten woanders — an der
Maskengrenze steht dann Grund, genau wie bei Abwesenheit. **Das Mass fragt nicht «steht
dort etwas», sondern «steht dort das Richtige».**

Nach der wörtlichen Lesart ist der Kandidat damit tot, und ich sage das so klar, wie
verlangt.

---

## Aber er ist es nicht — weil ρ genau die Fälle fängt, die er verfehlt

Nebeneinandergelegt mit den ρ-Werten aus `auf-25` (Rauschboden **−0.5207**):

| Fall | ρ über der Maske | von ρ gefangen? | Kante | von der Kante gefangen? |
|---|---|---|---|---|
| **H1** · Bauwerk weg | −0.6861 | **nein** | +0.0006 | **ja** |
| **H2** · 20 m versetzt | −0.6854 | **nein** | +0.0007 | **ja** |
| **H3** · andere Kubatur | **+0.3842** | **ja** | +0.0066 | **nein** |
| **H4** · 90° gedreht | **−0.4546** | **ja** | +0.0021 | **nein** |
| perfekt | −0.9874 | — | +0.1615 | — |
| Versatz 1 m | −0.8437 | — | +0.0655 | — |
| Versatz 4 m | −0.7386 | **ja** | — | — |
| weisses Rauschen | −0.5207 | — | −0.0044 | **ja** |

**Die beiden fangen genau die jeweils anderen Fälle. Zusammen decken sie alle vier ab —
einzeln keiner von beiden.**

* ρ misst, ob die Tiefen **innerhalb** der Maske richtig gestaffelt sind → fängt die
  falsche Kubatur, ist blind für die leere Fläche.
* Die Kante misst, ob **an der Maskengrenze** ein Tiefensprung sitzt → fängt die leere
  Fläche, ist blind für die falsche Kubatur.

Das ist keine Notlösung, sondern die saubere Aufteilung: **Existenz** und **Richtigkeit**
sind zwei Fragen, und sie brauchen zwei Messungen.

## Der Abstand, um den gefragt war — in beiden Lesarten

* **Wörtliche Lesart** (H3/H4 zählen als anwesend): kleinste Kante der Anwesenden
  +0.0021, grösste der Abwesenden +0.0007 → **Abstand 0.0014**. Daraus wird keine
  Schwelle, nicht einmal eine Tendenz.
* **Lesart «richtige Silhouette besetzt»**: kleinste +0.0655 (Versatz 1 m), grösste der
  übrigen +0.0066 (H3) → **Abstand 0.0589, Faktor 10**. Daraus wird eine Schwelle.

Beide Zahlen stehen hier, damit die Wahl der Lesart sichtbar bleibt und nicht in einer
günstigen verschwindet.

---

## Ein Vorschlag, ausdrücklich ungemessen

Ein **Paartest** — `ρ ≤ −0.80` **und** `Kante ≥ 0.05` — lässt von allen hier gemessenen
Bildern nur das perfekte und den 1-m-Versatz durch, und weist alles andere ab: H1, H2, H3,
H4, den 4-m-Versatz und das Rauschen.

**Das ist eine Ablesung aus diesen Zahlen, keine Kalibrierung.** Die beiden Schwellen sind
an *einer* Szene, *einem* Baukörper und ausschliesslich an **perfekten Bildern** abgelesen.
Wie sich die Kante an einem *erzeugten* Bild verhält, ist nicht gemessen — und nach den
ρ-Werten von gestern (erzeugte Bilder bei −0.07 bis −0.25, schlechter als Rauschen) ist die
Erwartung gedämpft: Der Paartest würde die heutige Kette vermutlich vollständig abweisen.
**Das wäre allerdings die richtige Antwort**, nicht die Schuld des Masses.

---

*Elf Messungen über zwei Szenen, alle Bilder aus `auf-23` und `auf-25`. Kein Bildmodell,
keine neuen Renderläufe, keine Normierung, kein Score. Nichts am Code geändert.*
