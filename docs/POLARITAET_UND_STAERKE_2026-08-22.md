# Die Polarität ist entschieden, die Stärke ist es nicht — und der Seed ist jetzt der Hebel

**HomeStation, 22.08.2026 · `auf-13` und `auf-22` neu gefahren, mit echter Tiefenkarte**

---

## Warum das neu zu fahren war

`auf-20260818-13` und `auf-20260820-22` haben Polarität und ControlNet-Stärke vermessen —
**beide an einer Schablone.** Bis heute Morgen wurde unsere 16-Bit-Tiefenkarte beim Wandeln
nach RGB geklippt: 235 Stufen wurden zu zwei. Beide Reihen bestimmen aber, wie KosmoVis
heute rendert.

Neu gefahren, mit echter Karte, gemessen mit **ρ über der Bauwerksmaske** (dem Mass, das
trägt), **n = 3 Seeds** gegen die Streuung. Szene, Kamera, Prompt, Schrittzahl unverändert.

---

## Ergebnis

| Polarität | Stärke 0.65 | Stärke 0.80 | Stärke 1.00 |
|---|---|---|---|
| **invertiert** (nah = dunkel, Vorgabe) | −0.6443 | **−0.7445** | −0.6043 |
| nicht invertiert (wie Blender schreibt) | −0.2910 | −0.2015 | −0.3379 |

*(je negativer, desto besser; perfektes Bild −0.9874, weisses Rauschen −0.5207)*

### Die Polarität: entschieden

    invertiert       Mittel -0.6644   stdabw 0.2269   (9 Läufe)
    nicht invertiert Mittel -0.2768   stdabw 0.1091   (9 Läufe)
    Abstand                  0.3876

**Der Abstand ist grösser als jede Streuung im Versuch.** `POL_NAH_DUNKEL` ist damit
bestätigt — diesmal wirklich.

**Das ist neu.** `auf-22` konnte es nicht entscheiden: Dort lag die nicht invertierte Karte
sogar **0.0418 besser**, was innerhalb der Seed-Streuung lag und darum als «nicht messbar»
gemeldet wurde. **An einer Schablone gibt es keine Polarität** — ein Negativ einer
Schwarzweissfläche ist wieder eine Schwarzweissfläche. Erst mit echten Grauwerten hat die
Richtung eine Bedeutung, und dann ist sie eindeutig.

### Die Stärke: nicht entschieden

| Vergleich | Abstand | grössere Streuung | trägt? |
|---|---|---|---|
| 0.80 gegen 0.65 | 0.1002 | 0.2565 | **nein** |
| 0.80 gegen 1.00 | 0.1402 | 0.3128 | **nein** |

0.80 führt, aber beide Abstände liegen **unter** einer einzigen Standardabweichung. Die
alte Aussage aus `auf-13` — *«0.80 schneidet besser ab als 1.00»* — bleibt damit unbelegt,
jetzt zum zweiten Mal und mit dem besseren Messgerät. `auf-20` hatte sie schon als Rauschen
entlarvt; das gilt unverändert.

---

## Was jetzt der Hebel ist: die Seed-Streuung

Über alle neun Läufe mit richtiger Polarität:

    bester Lauf   -0.9085     (nahe am perfekten Bild)
    schlechtester -0.2683     (schlechter als weisses Rauschen)
    unter der Schwelle -0.80:  3 von 9

**Ein Drittel der Läufe besteht, zwei Drittel nicht — bei identischen Einstellungen.**
Die Streuung über den Seed (0.2269) ist inzwischen **grösser als jeder Effekt, den die
Parameter noch hergeben** (0.10 bis 0.14).

**Damit hat sich die Frage verschoben.** Sie lautet nicht mehr «welche Stärke», sondern:

* **Kurzfristig, und heute schon machbar:** mehrere Seeds rendern und den besten
  **auswählen** — das Messgerät dafür steht seit gestern (ρ über der Maske ist monoton,
  szenenunabhängig und trägt ein Vorzeichen). Drei Bilder kosten rund vier Sekunden; eines
  davon besteht im Mittel.
* **Grundsätzlich:** herausfinden, warum derselbe Aufbau einmal −0.91 und einmal −0.27
  liefert. Das ist die nächste echte Frage — und sie ist mit dem alten Messgerät nie
  stellbar gewesen, weil dort alles bei −0.14 lag.

*Auffällig am Rand:* Die falsch gepolte Reihe streut **halb so stark** (0.1091 gegen
0.2269). Eine Karte, die nichts Brauchbares sagt, sagt es zuverlässig; erst die richtige
Konditionierung macht das Ergebnis vom Seed abhängig.

---

## Was daraus für KosmoVis folgt

1. **Vorgabe bleibt: invertiert, Stärke 0.80.** Die Polarität ist jetzt belegt, die Stärke
   ist die beste unbelegte Wahl — und es gibt keinen Grund, sie zu ändern.
2. **Keine weitere Stärkereihe**, bevor die Seed-Streuung verstanden ist. Sie würde wieder
   nur Rauschen messen; das ist jetzt dreimal passiert.
3. **Die Auswahl über mehrere Seeds ist der billigste Qualitätssprung**, den die Kette
   heute hergibt — vom Mittel −0.66 auf den besten von dreien.

---

*18 Renderläufe, 18 Tiefenschätzungen, eine Szene, drei Seeds je Zelle. Nichts am Code
geändert.*
