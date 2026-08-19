# Die Normierung trägt nicht — und die Metrik ist zu stumpf

**`auf-20260820-23`, HomeStation · 24 Blender-Läufe, kein Bildmodell**

---

## Der eine Satz

**Die beiden Anteilskurven liegen NICHT aufeinander.**

Dieselbe Verschiebung von 1 m ergibt bei 29 % Geometrieanteil einen Anteil von rund
**0.40** der Spanne, bei 59.8 % einen von rund **0.92**. Das ist Faktor 2,3, nicht
«ungefähr dasselbe». Die Normierung `(score − rauschen) / (perfekt − rauschen)` ist damit
**widerlegt**.

*Den Anteil sollte ich nicht ausrechnen — ich habe es nur getan, um genau diese Frage
beantworten zu können, und nenne die zwei Zahlen, damit der Satz nachprüfbar ist. Im
Ergebnis stehen wie verlangt nur die rohen Messwerte.*

---

## Die Gegenprobe zuerst

Bevor irgendetwas gefolgert wird: **Verschiebung 0 muss den perfekt-Anker treffen.**

| Szene | gemessen heute | Anker aus `auf-21`/`auf-22` |
|---|---|---|
| 29.11 % | 0.41484 | 0.4149 |
| 59.81 % | 0.98386 | 0.9839 |

Beide Szenen sind wiederverwendet und nicht neu gebaut, die Anker gelten also weiter.

---

## Szene A — Bodenplatte 11 m, 29.11 % Geometrieanteil

*Anker: perfekt 0.4149 · weisses Rauschen 0.2546 (grau und Verlauf sind hier ungemessen,
`n_gemeinsam` 0)*

| Verschiebung | Score | ρ | `geom_iou` | `n_gemeinsam` |
|---|---|---|---|---|
| 0 m | 0.4148 | −0.962 | 0.1789 | 23 166 |
| 0.25 m | 0.3991 | −0.895 | 0.1780 | 23 062 |
| 0.5 m | 0.3730 | −0.782 | 0.1779 | 23 058 |
| 1 m | 0.3184 | −0.549 | 0.1847 | 23 796 |
| **2 m** | **0.1191** | −0.073 | 0.1946 | 24 868 |
| 4 m | 0.2301 | **+0.337** | 0.1571 | 20 726 |

| Drehung | Score | ρ | `geom_iou` | `n_gemeinsam` |
|---|---|---|---|---|
| 0° | 0.4148 | −0.962 | 0.1789 | 23 166 |
| 2° | 0.4094 | −0.961 | 0.1743 | 22 660 |
| 5° | 0.3916 | −0.902 | 0.1701 | 22 186 |
| 10° | 0.3724 | −0.822 | 0.1686 | 22 023 |
| 20° | 0.3401 | −0.714 | 0.1619 | 21 268 |
| 45° | 0.3268 | −0.641 | 0.1665 | 21 793 |

## Szene B — Bodenplatte 20 m, 59.81 % Geometrieanteil

*Anker: perfekt 0.9839 · Rauschen 0.7217 · grau 0.5188 · Verlauf 0.3483*

| Verschiebung | Score | ρ | `geom_iou` | `n_gemeinsam` |
|---|---|---|---|---|
| 0 m | 0.9839 | −0.998 | 0.9703 | 154 439 |
| 0.25 m | 0.9678 | −0.992 | 0.9439 | 152 277 |
| **0.5 m** | **0.9585** | −0.985 | 0.9324 | 151 312 |
| **1 m** | **0.9617** | −0.966 | 0.9579 | 153 431 |
| 2 m | 0.9409 | −0.924 | 0.9578 | 153 423 |
| 4 m | 0.8911 | −0.842 | 0.9435 | 152 245 |

| Drehung | Score | ρ | `geom_iou` | `n_gemeinsam` |
|---|---|---|---|---|
| 0° | 0.9839 | −0.998 | 0.9703 | 154 439 |
| 2° | 0.9793 | −0.997 | 0.9623 | 153 792 |
| 5° | 0.9717 | −0.992 | 0.9515 | 152 906 |
| 10° | 0.9769 | −0.986 | 0.9676 | 154 219 |
| 20° | 0.9642 | −0.974 | 0.9545 | 153 151 |
| 45° | 0.9585 | −0.944 | 0.9727 | 154 635 |

---

## Die Auflösungsgrenze

**Szene A (29 %):** Der Score fällt zwischen **1 m** (0.3184) und **2 m** (0.1191) unter
den Rauschanker 0.2546.

**Szene B (59.8 %):** **Gar nicht.** Selbst 4 m Versatz liefert 0.8911 und liegt damit
weit über dem Rauschanker 0.7217.

**Drehung, beide Szenen:** **Gar nicht.** 45° — ein um eine Achtelumdrehung verdrehtes
Gebäude — liefert 0.3268 beziehungsweise 0.9585, beide über ihrem Rauschanker.

Nach dem eigenen Massstab des Auftrags — *«Fällt schon 0.25 m darunter, ist sie zu grob;
erst bei 4 m, ist sie zu stumpf»* — lautet die Antwort: **zu stumpf.** In der realistischen
Szene mit viel Boden erkennt die Metrik ein um vier Meter versetztes oder um 45 Grad
verdrehtes Gebäude **nicht als schlechter als weisses Rauschen**.

---

## Und der Befund, den ich nicht gesucht habe: der Score ist nicht monoton

**Szene A, Versatz:** 2 m ergibt **0.1191**, 4 m ergibt **0.2301** — mehr Fehler, besserer
Score. Die Ursache steht in derselben Zeile: ρ kippt von −0.073 auf **+0.337**, und
gewertet wird der Betrag. Bei 2 m steht die verschobene Tiefenstaffelung fast senkrecht
auf der richtigen (ρ ≈ 0, der schlechtestmögliche Wert); bei 4 m wird sie wieder
korreliert, nur mit umgekehrtem Vorzeichen.

**Szene B, Versatz:** 0.5 m ergibt 0.9585, 1 m ergibt **0.9617** — ebenfalls höher trotz
grösserem Fehler.

**Das trifft die Normierung ein zweites Mal, und härter als der Szenenvergleich.** Eine
nicht-monotone Grösse lässt sich durch keine Normierung in ein Mass für «Abstand vom
Richtigen» verwandeln — der Anteil der Spanne erbt die Nicht-Monotonie unverändert. Zwei
verschiedene geometrische Fehler ergeben denselben Anteil, und der grössere von beiden
kann der bessere sein.

---

## Was daraus folgt

1. **Die Normierung ist widerlegt**, und zwar aus zwei unabhängigen Richtungen: die
   Kurven liegen nicht aufeinander, und die zugrunde liegende Grösse ist nicht monoton.
2. **`|spearman|` ist der Kern des Problems.** Der Betrag war eine bewusste Entscheidung
   mit dokumentiertem Grund (Disparität), aber er faltet die Skala in der Mitte: Der
   schlechteste Wert liegt bei ρ = 0, nicht an einem Ende. Eine Metrik mit einem Minimum
   in der Mitte ihres Fehlerbereichs kann nicht monoton sein.
3. **Ein Ausweg wäre, die Polarität EINMAL zu bestimmen** — sie ist eine Eigenschaft des
   Schätzers, nicht des Bildes — und danach das **vorzeichenbehaftete** ρ zu werten.
   Dann liegt der schlechteste Wert am Ende der Skala, wo er hingehört.
   Das ist ein Vorschlag, keine Messung.
4. **Der Vorbehalt des Auftrags gilt und ist wichtiger geworden:** Dies ist die
   **Obergrenze**. Bei perfekten Bildern trennt die Metrik einen 4-m-Versatz nicht vom
   Rauschen. Bei erzeugten Bildern kann sie es nicht besser.

---

*24 Blender-Läufe à rund 6 s, vier Auswertungsreihen, kein Bildmodell und keine Seeds.
Zwei der vier Reihen von Hilfsagenten gefahren, mit demselben unveränderten Skript.
Nichts am Code des Projekts geändert; Messstand und Bilder ausserhalb des Repos.*
