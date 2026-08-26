# Woran `geom_iou` deckelt — und woran nicht

**26.08.2026** · gemessen in dieser Umgebung, **ohne GPU**, an im Repo erzeugter Geometrie
· Modul `src/aiimaging/deckelstudie.py`, Tests `tests/test_deckelstudie.py`

---

## Die Frage, und warum sie falsch gestellt war

`geometrie_qa.IOU_DECKEL` hält seit dem 18.08. fest: `geom_iou` deckelt an einer echten
Szene bei **0.256** (`wie_soll`) bzw. **0.406** (`ohne_randberuehrung`). Für die Schwelle
0.65 wären **0.4225** nötig — *selbst ein perfektes Bild kommt auf höchstens 0.634.*

Daraus wurde in `PLAN.md` eine offene Aufgabe:

> *«Den Rest des Deckels — trägt eine Kombination (`ohne_randberuehrung` plus `rand_10`)?»*

**Sie zielt auf die Silhouettenregel.** Diese Studie zeigt: dort liegt der Deckel nicht.

---

## 1 · Die Regel erreicht 0.9999

Ein **perfekter Schätzer** lässt sich nachstellen: Blenders eigene Tiefenkarte aus dem
normalisierten PNG. Sie trägt die richtigen Werte und — wie jede Schätzerkarte — **keine
Hintergrundmarke**. Genau das ist der Unterschied zur EXR.

| Szene | Geometrieanteil | `wie_soll` | `ohne_randberuehrung` |
|---|---|---|---|
| Quader (6 Bauteile) | 0.1111 | **0.9999** | 0.9999 |
| Hochbau (141 Bauteile) | 0.1730 | **0.9998** | 0.9999 |
| Hochbau mit Gelände | 0.0822 | **0.9977** | 0.9989 |

Alle drei bei 400 × 400, Kamera `sSE`, Blender 4.2.1 LTS.

**Die Regel erreicht 0.9999, wo die Produktion bei 0.406 deckelt.** Der Verlust liegt
vollständig im Schätzer.

---

## 2 · Und woran im Schätzer — zwei Fehlerquellen, einzeln aufgebracht

Die naheliegende Erklärung wäre **Ordnungsrauschen**: Der Schätzer ordnet die Tiefen
ungenauer. Sie trägt nicht.

### Fall A — Rauschen nur auf der Geometrie, Hintergrund bleibt perfekt

| \|rho\| über die Geometrie | 1.000 | 0.974 | 0.825 | 0.583 | **0.393** |
|---|---|---|---|---|---|
| IoU | 0.9998 | 0.9995 | 0.9846 | 0.9016 | **0.7653** |

*Selbst bei einer fast zerstörten Ordnung bleibt IoU bei 0.765.* Die Regel ist gegen
Ordnungsfehler **innerhalb** der Geometrie robust.

### Fall B — der Hintergrund rückt in den Wertebereich des Bauwerks

Die Geometriepunkte bleiben **unangetastet**.

| Hintergrund bei … des Bauwerksbereichs | 0 % | 25 % | 50 % | 75 % | 100 % |
|---|---|---|---|---|---|
| \|rho\| über die Geometrie | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| IoU | 0.9998 | 0.9036 | **0.4983** | 0.1849 | 0.0000 |

**Die Rangkorrelation bleibt bei exakt 1.0, und IoU fällt auf null.**

---

## 3 · Die Erklärung, und sie passt auf die Zahl

Gemessen wurde in der Produktion **|spearman| 0.990 bei geom_iou 0.406**
(`auf-20260819-15`).

* Nach **Fall A** gehörte zu |rho| 0.99 ein IoU von rund 0.99. Ordnungsrauschen erklärt
  0.406 also **nicht** — dafür müsste |rho| auf etwa 0.36 fallen.
* Nach **Fall B** gehört zu IoU 0.406 ein Hintergrund bei rund **0.56** des
  Bauwerksbereichs. Fein aufgelöst: 0.50 → 0.4983, **0.55 → 0.4298**, 0.60 → 0.3636.

> **Der Schätzer legt den Himmel mitten in die Tiefenspanne des Bauwerks.**

Das ist keine Ungenauigkeit, sondern eine Eigenschaft **relativer** Tiefenschätzer: Sie
bilden auf einen beschränkten Bereich ab und haben für *unendlich weit* keinen Wert.

---

## 4 · Was daraus folgt

**Keine Silhouettenregel, die allein die Werte des Schätzers liest, kann das beheben.**
`ohne_randberuehrung` hebt 0.256 auf 0.406, weil sie randberührende Flächen verwirft —
ein Teilausweg, und er erklärt genau die Grössenordnung des Gewinns.

Damit ist die offene Aufgabe *«trägt eine Kombination?»* beantwortet, und zwar mit **nein,
nicht nennenswert** — sie ist auf die falsche Komponente gerichtet.

### Drei Wege, und die Wahl gehört dem Owner

Sie berührt die Forschungsfrage selbst, darum steht hier keine Empfehlung als Entscheid:

1. **Eine Hintergrundtrennung, die nicht aus den Schätzerwerten kommt** — eine
   Segmentierung des erzeugten Bildes. Ein zusätzliches Modell, mit Lizenzfrage (Regel 1).
2. **`geom_iou` gegen den je Szene erreichbaren Deckel normalisieren.**
   `geometrie_qa.erreichbarkeit` rechnet ihn bereits. Billig — aber es macht die Zahl
   szenenabhängig, und Szenen sind dann untereinander nicht mehr vergleichbar.
3. **`geom_iou` aus dem Score nehmen** und auf die maskierte Rangkorrelation `rho_maske`
   stützen. *Fall B zeigt, dass sie von diesem Fehler gar nicht betroffen ist* — sie bleibt
   bei 1.0, während IoU zusammenbricht.

*Was gegen 1 spricht:* ein zweites Modell im Pfad, das selbst geprüft werden müsste.
*Was gegen 2 spricht:* eine Schwelle, die je Szene etwas anderes bedeutet.
*Was gegen 3 spricht:* `geom_iou` fängt heute den Fall, den `rho_maske` nicht sieht — ein
Bauwerk an der **falschen Stelle** mit richtiger Tiefenordnung. Wer es streicht, verliert
diesen Riegel.

---

## 5 · Die Prüfgrösse — diese Studie ist widerlegbar

`deckelstudie.wo_liegt_der_himmel(soll, karte)` gibt genau die eine Zahl, aus der alles
folgt: wo der Hintergrund im Wertebereich des Bauwerks liegt.

**Vorhersage: bei einem echten Schätzerlauf liegt sie bei rund 0,55 bis 0,60.**

Fällt sie deutlich anders aus, ist diese Erklärung falsch — und dann gehört sie
zurückgenommen und nicht nachjustiert. Beauftragt als `auf-20260826-55`.

---

## 6 · Was diese Studie NICHT ist

* **Kein Ersatz für eine Messung am Gerät.** Der perfekte Schätzer ist *nachgestellt*,
  nicht gelaufen. Was ein echter Schätzer auf einem **erzeugten** Bild tut, ist hier nicht
  gemessen — nur, was die Regel zuliesse.
* **Keine Aussage über die Schwelle 0.65.** Sie bleibt unkalibriert; diese Studie sagt nur,
  wo der Deckel *nicht* herkommt.
* **Drei Szenen sind nicht viele.** Zwei Baukörper und eine Geländevariante. Dass der
  Befund über verschiedene Kubaturen trägt, ist damit angedeutet, nicht gezeigt.
