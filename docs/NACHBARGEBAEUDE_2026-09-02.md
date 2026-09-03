# Der Nachbarvorbehalt — hier nicht reproduzierbar, und das ist die Eingrenzung

**02.09.2026 · gerechnet in dieser Umgebung, ohne GPU und ohne Bildmodell**

---

## Warum nachgemessen wurde

Seit dem 01.09.2026 trägt die Bauwerksmaske einen Vorbehalt: Steht ein `IfcCivilElement`
in der Szene, sei der Kantenanteil an der Maskengrenze nur eingeschränkt aussagekräftig.

Die Zahlen dazu — **+0.0016 gegen −0.0024** — stammen aus `auf-20260823-37`, also **von
der HomeStation und nicht von hier.** *Einen fremden Vorbehalt weiterzutragen ist bequem
und wird mit jeder Weitergabe unschärfer.*

**Werkzeug:** `tools/studie_nachbargebaeude.py` · **Rohdaten:** `build/nachbar/roh.json`

---

## Der Mechanismus, der geprüft werden sollte

Der Kantenanteil zählt, wie viel der Maskengrenze im Bild wirklich als **Tiefensprung**
dasteht. Hinter dem Bauwerk Himmel heisst: unendlicher Sprung, jede Grenzstelle zählt.
Hinter dem Bauwerk ein Nachbar in ähnlicher Tiefe heisst: kleiner Sprung — und dann,
so die Vermutung, sieht ein perfektes Bild dort aus wie irgendeines.

---

## Der Aufbau — und zwei verfehlte Anläufe, die dazugehören

Ein Zielbau (12 × 8 × 12 m) und ein Nachbar dahinter, in drei Abständen. Kamera frontal,
Auflösung 192, gebaute Karten.

**Zwei Anläufe haben die Bedingung gar nicht hergestellt**, und beide stehen hier, weil
sie die häufigste Art sind, eine Messung zu verfehlen:

| Anlauf | Nachbar deckt vom Hintergrund | warum das nichts misst |
|---|---|---|
| 1 · Nachbar 28 × 16 m | **9,8 %** | zu klein — der Hintergrund blieb Himmel |
| 2 · Nachbar 120 × 40 m, ohne Rahmung | **14,1 %** | Der Runner rahmte die **ganze Szene**: Das Ziel wurde winzig, über dem Nachbarn stand Himmel |
| 3 · dasselbe, Rahmung auf das **Ziel** | **51,7 %** | jetzt herrscht die Bedingung |

> *Eine Szene, die die Bedingung nicht herstellt, widerlegt keinen Vorbehalt — sie misst
> etwas anderes und sieht dabei aus wie eine Messung.*

---

## Das Ergebnis

| Szene | Hintergrund endlich | perfekt | geglättet | weisses Rauschen | Abstand perfekt | Abstand geglättet |
|---|---|---|---|---|---|---|
| `himmel` | 0.0000 | 1.0000 | 1.0000 | 0.0520 | **0.9480** | 0.9480 |
| `nachbar_1m` | 0.5199 | 1.0000 | 0.9950 | 0.0520 | **0.9480** | 0.9431 |
| `nachbar_5m` | 0.5154 | 1.0000 | 0.9950 | 0.0520 | **0.9480** | 0.9431 |
| `nachbar_20m` | 0.5066 | 1.0000 | 0.9950 | 0.0520 | **0.9480** | 0.9431 |

**Der Kantenanteil trennt mit Nachbarn genauso gut wie mit Himmel.** Ein perfektes Bild
erreicht 1.0000, weisses Rauschen 0.0520 — in jeder Szene. Auch eine geglättete Karte
(3 × 3-Mittel, der grobe Ersatz für die Unschärfe eines Schätzers) ändert daran fast
nichts: 0.9431 statt 0.9480.

---

## Was das heisst — und was es ausdrücklich nicht heisst

**Es ist kein Widerspruch zur HomeStation.** Es ist eine **Eingrenzung**:

> Der Vorbehalt ist eine Aussage über den **Tiefenschätzer**, nicht über die **Szene**.

Die Rechnung dahinter ist einfach: Bei rund 170 m Kameraabstand ist ein Nachbar 1 m
dahinter ein relativer Tiefenunterschied von **0,6 %**. Eine gebaute Karte trägt diesen
Sprung exakt und der Kantenanteil findet ihn. Ein echter Schätzer hat diese Schärfe nicht
— und **genau dort**, nicht in der Geometrie, entsteht der Befund.

Die 3 × 3-Glättung ist als Ersatz dafür **zu schwach**, und dass sie es ist, sagt diese
Studie damit auch: *Wer Schätzerrauschen nachbilden will, braucht einen Schätzer.*

### Was daraufhin geändert wurde

Die Warnung in der Maske sagt seit heute:

* **wessen** Messung sie trägt (die der HomeStation, mit Auftragsnummer),
* dass sie **mit einem echten Schätzer** gilt und hier nicht reproduzierbar ist,
* die Gegenzahl dazu (0.9431 gegen 0.9480),
* und dass der Satz *«dann ruht das Paarurteil allein auf ρ»* eine **Folgerung** ist und
  keine Messung.

*Ein Vorbehalt, der mehr behauptet als er belegt, ist derselbe Fehler wie eine Zahl ohne
Anker — nur in die vorsichtige Richtung.*

---

## Die Frage, die daraus folgt und nur drüben zu messen ist

**Ab welchem relativen Tiefenunterschied verliert euer Schätzer die Kante?** 0,6 % ist
der Fall, den wir gebaut haben; ob die Grenze bei 1 %, 5 % oder 20 % liegt, entscheidet,
wie oft der Vorbehalt überhaupt greift — und ob ein Nachbar in 50 m Abstand noch einer ist.

Sie steht als Rückgabepunkt in `auf-20260826-60` (Rang 7), wo der echte Schätzer ohnehin
läuft. **Kein neuer Auftrag** — `local` trägt 22.

---

## Anhang · Nachrechnen

```
python tools/studie_nachbargebaeude.py
```

Vier Blender-Läufe bei 192 Punkten. Geprüft in `tests/test_studie_nachbargebaeude.py`.
