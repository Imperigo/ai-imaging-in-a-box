# Die fehlende Randkante ist ein echter Mangel — und das Mass lässt sich schärfen

**HomeStation, 22.08.2026 · Nachtrag zu `auf-20260822-28`, kein neuer Renderlauf**

---

## Die Frage

`auf-28` hat sie offengelassen: Alle drei erzeugten Bilder haben eine Tiefenkante von
**0.004 bis 0.006** — auf dem Niveau der **Abwesenheit** (H1/H2: 0.0006/0.0007), nicht des
perfekten Bildes (0.1615). Der Paartest `ρ ≤ −0.80 UND Kante ≥ 0.05` würde Lauf B damit
**abweisen**, obwohl sein ρ mit −0.9059 sehr gut ist.

> *Ist die fehlende Randkante ein echter geometrischer Mangel — oder ein Artefakt des
> Schätzers, der an weichen, texturarmen Übergängen keine harte Kante findet?*

**Die Prüfung:** das perfekte Blenderbild schrittweise weichzeichnen. Die Geometrie bleibt
dabei exakt richtig; nur die Schärfe des Übergangs fällt. Bricht die Kante schon dadurch
ein, misst sie Bildschärfe statt Anwesenheit.

---

## Das Ergebnis

| Bild | ρ über der Maske | Kante | Bildkontrast am Rand |
|---|---|---|---|
| perfekt, scharf | −0.9874 | **0.1615** | 7.0 |
| perfekt, weich r = 1 | −0.9886 | 0.1556 | 5.0 |
| perfekt, weich r = 2 | −0.9830 | 0.1338 | 3.5 |
| perfekt, weich r = 4 | −0.9657 | **0.0628** | 2.0 |
| perfekt, weich r = 8 | −0.8875 | **0.0277** | 1.0 |
| **erzeugt B** (z-image + Führung) | −0.9059 | **0.0058** | 3.0 |
| erzeugt A (qwen) | −0.7406 | 0.0048 | 1.0 |

**Beides ist wahr, und die Reihenfolge zählt:**

**1 · Die Kante misst tatsächlich auch Schärfe.** Ein bloss weichgezeichnetes, geometrisch
**perfektes** Bild fällt von 0.1615 auf 0.0277 — unter die Schwelle 0.05 —, während sein ρ
bei −0.8875 bleibt und die Schwelle −0.80 weiter besteht. **Der Paartest würde ein
perfektes, leicht weiches Bild abweisen.** Das ist eine echte Schwäche.

**2 · Aber Bs Ausfall erklärt sich dadurch nicht.** B hat am Rand einen Bildkontrast von
**3.0** — das entspricht dem perfekten Bild bei r = 2 (Kontrast 3.5), und **das erreicht
0.1338**. B liegt bei 0.0058, also **dreiundzwanzigmal niedriger bei vergleichbarer
Randschärfe.**

> **Die fehlende Randkante von B ist ein echter Mangel.** Das erzeugte Bauwerk ordnet seine
> Tiefen innen nahezu perfekt und setzt an seinem Rand **keinen Sprung** — es steht nicht
> vor dem Hintergrund, es geht in ihn über.

Die Abweisung durch den Paartest ist damit **inhaltlich richtig**. Sie steht nur auf einem
Mass, das nebenbei die Schärfe mitmisst.

---

## Und daraus fällt ein besseres Mass ab

Teilt man die Kante durch den **Bildkontrast am Rand**, verschwindet die Schärfe-Empfindlichkeit:

| Bild | Kante / Kontrast |
|---|---|
| perfekt, scharf | 0.0231 |
| perfekt, r = 1 | 0.0311 |
| perfekt, r = 2 | 0.0382 |
| perfekt, r = 4 | 0.0314 |
| perfekt, r = 8 | 0.0277 |
| **erzeugt B** | **0.0019** |
| erzeugt A | 0.0048 |

**Über vier Weichzeichnungsstufen bleibt das perfekte Bild zwischen 0.023 und 0.038** —
praktisch flach, während die rohe Kante um das Sechsfache fällt. Die erzeugten Bilder
liegen bei **0.0019 und 0.0048**, also **fünf- bis zwanzigfach darunter**, sauber getrennt.

**Als Vorschlag, ausdrücklich keine Kalibrierung:** Die Kante durch den Randkontrast
teilen und bei etwa **0.010** trennen. Dann weist der Paartest ein weiches, geometrisch
richtiges Bild **nicht** mehr ab und Bs echten Mangel weiter schon.

**Die ehrlichen Grenzen davon:** Der Randkontrast ist der Abstand zweier Mediane aus
8-Bit-Werten und wird bei sehr weichen Bildern grob (1.0 bei r = 8). Sieben Bilder, eine
Szene, ein Bauwerk. Das ist ein Hinweis auf ein besseres Mass, keine fertige Schwelle.

---

*Kein neuer Renderlauf — vier Weichzeichnungen des vorhandenen Beauty-Passes und sieben
Tiefenschätzungen. Nichts am Code geändert; das normierte Mass ist ein Vorschlag und
nirgends eingebaut.*
