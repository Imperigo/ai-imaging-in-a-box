# Die Neigung stört den Schätzer nicht — und der erste Anlauf war der lehrreichere

**`auf-20260822-29`, HomeStation · sechs Blender-Läufe, kein Bildmodell**

---

## Die Antwort

**Nein. Die Kameraausrichtung ist dem Tiefenschätzer praktisch gleichgültig.**

Eckansicht, zwei Fassaden sichtbar — dieselbe Szene, derselbe Standort, nur die
Ausrichtung ändert sich:

| Ausrichtung | ρ über der Maske | Tiefenkante | Maske |
|---|---|---|---|
| **A** · gekippt 9,4623° (wie heute) | **−0.9835** | +0.2034 | 17.3 % |
| **B** · waagrecht, höheres Bildformat | **−0.9650** | +0.1101 | 24.7 % |
| **C** · waagrecht, gleiches Format | **−0.9650** | +0.1397 | 16.4 % |

**Alle drei innerhalb von 0.019.** Die falsifizierbare Behauptung verlangte, B und C
müssten *deutlich besser* sein als A. Sie sind marginal **schlechter**, und der Abstand
liegt im Rauschen.

**Folge, und sie steht so im Auftrag:** Der Umbau von `kameras.py` bleibt richtig, weil
die Fachnorm ihn verlangt — aber er ist **kein Beitrag zur Bildqualität**. Genau das war
zu wissen, bevor er gebaut wird.

*Zur Kante:* A 0.2034, C 0.1397, B 0.1101 — das Kippen hilft ihr sogar leicht. Alle drei
liegen weit über dem Abwesenheitswert (~0.005) und dem Rauschen (−0.0044).

*Zum Shift:* Mein Aufbau kann keinen. B ist darum waagrecht mit höherem Bildformat
(512 × 768) gefahren, wie der Auftrag es erlaubt.

---

## Der Nebenbefund, und er ist der wertvollere

**Mein erster Anlauf stand frontal vor der Langseite.** Dieselben drei Ausrichtungen
ergaben dort:

| Ausrichtung | ρ frontal | ρ über Eck |
|---|---|---|
| A · gekippt | −0.8305 | −0.9835 |
| B · waagrecht + Format | **+0.6509** | −0.9650 |
| C · waagrecht | **+0.8159** | −0.9650 |

**Frontal kippt das Vorzeichen.** Nicht ein bisschen — vollständig, von −0.83 auf +0.82.

Der Grund steht im Bild: Von vorn zeigt das Bauwerk **eine flache Wand**, fast parallel
zur Bildebene. Innerhalb der Maske gibt es dann **keine Tiefenstaffelung, die sich ordnen
liesse**. Der Schätzer trägt seine eigene Annahme ein — «oben im Bild ist ferner» —, und
die kann jedes Vorzeichen haben. Bei A rettet die perspektivische Konvergenz der
gekippten Kamera gerade noch ein echtes Gefälle; bei B und C fehlt auch das.

**Für jede künftige Messung mit dieser Grösse gilt damit:** Die Blickrichtung muss so
gewählt sein, dass **mehr als eine Fläche** sichtbar ist. Sonst misst ρ über der Maske
nicht die Geometrie, sondern den Schätzer.

*Ich hätte den frontalen Lauf melden und dabei belassen können — die Zahlen sahen nach
einem klaren Befund aus («Kippen hilft, Waagrechte schadet»). Es wäre der falsche gewesen.
Er steht hier, weil die Gegenüberstellung mehr wert ist als das Ergebnis allein.*

---

## Zur Korrektur des Auftraggebers

Die berichtigten 9,1 bis 11,7 Prozent Konvergenz sind übernommen; gerechnet wurde ohnehin
mit den 9,4623 Grad Neigung, und die standen nicht in Frage. Die Messung hier hängt an der
Neigung, nicht an der Konvergenzzahl.

---

*Sechs Blender-Läufe (zwei Standorte × drei Ausrichtungen), je Ausrichtung Soll-Karte und
Maske aus derselben Aufnahme, Maske aus dem Material-ID-Pass. Kein Bildmodell, keine
Seeds, nichts am Code geändert.*
