# Die Richtung repariert einen der drei Knicke — und die Stumpfheit gar nicht

**Nachgerechnet an den Messwerten aus `auf-20260820-23`. Keine neue Messung.**

---

## Worum es geht

Die HomeStation hat am 20.08. zwei Dinge gemessen und ein drittes vorgeschlagen:

1. Die Normierung `(score − rauschen) / (perfekt − rauschen)` **trägt nicht** — dieselbe
   Verschiebung ergibt in zwei Szenen Anteile, die um Faktor 2,3 auseinanderliegen.
2. Der Score ist **nicht monoton** — mehr geometrischer Fehler kann einen besseren Score
   geben.
3. Vorschlag: die **Polarität** des Schätzers einmal bestimmen und danach das
   vorzeichenbehaftete ρ werten statt seinen Betrag.

Der Vorschlag ist richtig und ist umgesetzt. Diese Notiz rechnet nach, **wie viel er
repariert** — denn er repariert deutlich weniger, als der Name nahelegt.

---

## Die Rechnung

Alt: `sqrt(|ρ| · geom_iou)` · Neu: `sqrt(max(0, −ρ) · geom_iou)`, Polarität −1
(Disparität, an sechs Läufen aus zwei Szenen gemessen).

| Reihe | alt | monoton | neu | monoton |
|---|---|---|---|---|
| A Versatz | 0.4149 0.3991 0.3730 0.3184 0.1192 **0.2301** | **nein** | 0.4149 0.3991 0.3730 0.3184 0.1192 **0.0000** | **ja** |
| A Drehung | 0.4149 0.4093 0.3917 0.3723 0.3400 0.3267 | ja | unverändert | ja |
| B Versatz | 0.9841 0.9677 **0.9583 0.9619** 0.9407 0.8913 | **nein** | unverändert | **nein** |
| B Drehung | 0.9841 0.9795 **0.9715 0.9768** 0.9642 0.9582 | **nein** | unverändert | **nein** |

---

## Drei Befunde

### 1 · Von drei Knicken verschwindet einer

Der Knick in **A Versatz** verschwindet, und zwar vollständig: Aus 0.2301 wird 0.0000, die
Reihe fällt streng. Das ist genau der Fall, für den die Richtung gebaut ist — bei 4 m
Versatz kippt ρ auf **+0.337**, die Tiefenstaffelung läuft dem Soll entgegen, und das ist
kein „fast richtig", sondern verkehrt herum.

**Die beiden Knicke in Szene B bleiben unberührt.** Dort ist ρ in jedem einzelnen Lauf
negativ (−0.998 bis −0.842); das Vorzeichen ist nie strittig, und eine Vorzeichenregel
kann dort nichts richten. Der Knick sitzt woanders:

| Szene B | ρ | `geom_iou` |
|---|---|---|
| Versatz 0.5 m | −0.985 | 0.9324 |
| Versatz 1 m | −0.966 | **0.9579** ← *grösser* |

**ρ fällt sauber, `geom_iou` steigt.** Der zweite Faktor der Metrik ist selbst nicht
monoton im geometrischen Fehler. Dasselbe Muster bei der Drehung (5° → 10°: 0.9515 →
0.9676). Die Richtung repariert den ρ-Anteil und lässt den `geom_iou`-Anteil, wie er war.

### 2 · Die Stumpfheit bleibt vollständig

Kein einziger Lauf der Szene B fällt unter den Rauschanker 0.7217 — vorher nicht und
nachher nicht. Auch 4 m Versatz und 45° Drehung nicht. In Szene A ändert sich die Grenze
ebenfalls nicht: 2 m und 4 m liegen darunter, 1 m darüber, vorher wie nachher.

**Die Richtung ist keine Antwort auf die Stumpfheit.** Wer sie dafür hält, hält ein
Vorzeichen für eine Empfindlichkeit.

### 3 · Ein Loch im Tor ist zu

Das ist der Gewinn, den niemand gesucht hat. Eine **vollständig invertierte** Tiefenkarte
— vorne und hinten vertauscht, der grösstmögliche Geometriefehler — erreichte mit `abs()`
den Score **1.0**, denselben Wert wie eine perfekte Karte. Sie bestand das Tor. Mit
gemessener Polarität fällt sie auf **0.0**.

Das ist kein Genauigkeitsproblem gewesen, sondern ein Sicherheitsloch, und es war seit dem
ersten Tag im Modul dokumentiert — als *benannter Preis*, nicht als Fehler. Der Preis war
höher als der Text vermuten liess.

---

## Was das für die nächste Messung heisst

Der `geom_iou`-Anteil ist jetzt der Verdächtige, und es gibt eine Vermutung, die zu ihm
passt: **Beide Faktoren werden vom Boden beherrscht.** Bei 59.8 % Geometrieanteil ist
mehr als die Hälfte aller Punkte Bodenebene. Verschiebt man das Gebäude, ändert sich an
den Bodenpunkten fast nichts — die Silhouetten decken sich weiter, weil sie sich im Boden
decken. Dass die Überdeckung dabei sogar *steigen* kann, ist dann kein Widerspruch,
sondern Zufall auf einem Untergrund, der nichts misst.

Das passt zum Nullprobenbefund vom 20.08.: Weisses Rauschen erreichte auf derselben Szene
0.7217. Eine Metrik, die Rauschen so gut bewertet, misst dort zwei Bodenrampen
gegeneinander und nicht zwei Gebäude.

**Vermutung, nicht Messung:** Die Metrik muss dort messen, wo das Gebäude ist, und nicht
über das ganze Bild. Ein früherer Anlauf in diese Richtung (`ohne_randberuehrung`, am
20.08. zurückgenommen) war richtig gedacht und falsch gebaut — er wählte in Szenen mit
Boden **null** Punkte aus. Die Frage ist damit nicht erledigt, sondern offen.

---

*Keine neue Messung. Alle Zahlen stammen aus `docs/EMPFINDLICHKEIT_2026-08-20.md`; die
Nachrechnung steht als Test in `tests/test_geometrie_qa.py`
(`test_die_gemessene_nicht_monotonie_verschwindet_mit_der_polaritaet`).*
