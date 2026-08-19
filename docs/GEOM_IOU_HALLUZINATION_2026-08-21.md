# `geom_iou` fängt die Abwesenheit nicht — bei viel Boden belohnt es sie

**`auf-20260821-26`, HomeStation · keine neuen Bilder, nur die fehlende Auswertung**

Der Auftrag benennt die Lücke in `auf-25` selbst: Dort war ausdrücklich **nur ρ** zu
messen, also steht nirgends, was `geom_iou` bei H1 und H2 tut. Der Schluss «`geom_iou`
darf nicht fallen» ruht damit auf einer ungeprüften Annahme. Hier ist die Prüfung.

## Szene B — 59.8 % Geometrieanteil

| Bild | `geom_iou` | Score | ρ | `n_gemeinsam` |
|---|---|---|---|---|
| perfekt (unverstellt) | 0.9703 | 0.9839 | −0.998 | 154 439 |
| **H1 · Bauwerk ganz weg** | **0.9848** | **0.9530** | −0.922 | 155 603 |
| **H2 · 20 m versetzt** | **0.9845** | **0.9526** | −0.922 | 155 575 |
| H3 · andere Kubatur | 0.8244 | 0.7402 | −0.665 | 141 708 |
| H4 · 90° gedreht | 0.9275 | 0.9236 | −0.920 | 150 907 |
| Versatz 4 m | 0.9435 | 0.8911 | −0.842 | 152 245 |
| weisses Rauschen | 0.5682 | 0.7217 | −0.917 | 113 632 |

**Das leere Grundstück hat eine HÖHERE Überdeckung als das perfekte Bild** — 0.9848 gegen
0.9703 — und besteht mit einem Score von **0.9530** das Gate von 0.65 mit grossem Abstand.

Ihr Verdacht trifft, und die Erklärung ist einen Schritt schärfer als vermutet: Die
Silhouette ist zu mehr als der Hälfte Boden, und der Boden bleibt liegen. **Das Bauwerk
war die einzige Stelle, an der Soll und Ist sich überhaupt unterscheiden konnten — nimmt
man es weg, deckt sich fast alles.** `geom_iou` steigt also nicht trotz, sondern **wegen**
der Abwesenheit.

## Szene A — 29 % Geometrieanteil

| Bild | `geom_iou` | Score | ρ |
|---|---|---|---|
| perfekt | 0.1789 | 0.4148 | −0.962 |
| **H1 · Bauwerk ganz weg** | 0.1419 | **0.3723** | −0.977 |
| **H2 · 20 m versetzt** | 0.1414 | **0.3717** | −0.977 |
| H3 · andere Kubatur | 0.2674 | 0.1842 | +0.127 |
| H4 · 90° gedreht | 0.1841 | 0.2940 | −0.469 |
| Versatz 4 m | 0.1571 | 0.2301 | +0.337 |
| weisses Rauschen | 0.0684 | 0.2546 | −0.949 |

Hier liegen H1 und H2 unter dem perfekten Bild — aber mit 0.372 immer noch **deutlich über
dem Rauschanker 0.2546**. Auch bei wenig Boden wird die Abwesenheit nicht gefangen,
sondern nur gedämpft.

---

## Was das für meinen Schluss aus `auf-25` bedeutet

Mein Satz war zur Hälfte richtig und zur Hälfte irreführend.

**Richtig bleibt:** ρ über der Maske allein genügt nicht — H1 und H2 liegen dort über dem
Rauschboden.

**Falsch war die Folgerung**, `geom_iou` sei deshalb der nötige Halluzinationsfänger. Es
fängt denselben Fall **nicht** — und bei viel Boden bewertet es ihn sogar besser als die
Wahrheit.

> **Weder ρ noch `geom_iou` erkennt ein Bild ohne Bauwerk. Die Lücke ist offen, nicht
> gefüllt.**

Damit fällt auch die Begründung weg, `geom_iou` aus diesem Grund zu behalten. Ob es aus
einem anderen Grund bleiben soll, ist eine andere Frage — als Anwesenheitsprüfung taugt es
nicht, und der Score, den es trägt, ist bei einer Bodenszene ohnehin fast vollständig
Boden.

**Was die Anwesenheit wirklich fangen könnte, bleibt ungemessen.** Mein erster Kandidat
(Tiefenumfang in der Maske) ist gefallen; der zweite — eine **Tiefenkante an der
Maskengrenze**, die ein Bauwerk hat und ein leeres Grundstück nicht — ist noch nicht
geprüft. Er ist jetzt der einzige Vorschlag, der übrig ist.

---

*Keine neuen Bilder, keine neuen Szenen, kein Bildmodell — dieselben Aufnahmen aus
`auf-23` und `auf-25`, gegen die ursprüngliche Soll-Karte mit Gelände, `wie_soll`.*
