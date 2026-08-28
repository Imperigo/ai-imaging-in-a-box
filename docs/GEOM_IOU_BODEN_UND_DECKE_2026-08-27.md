# Der Boden von `geom_iou` gehört der Szene, die Decke sieht nicht hinein

**27.08.2026 · gemessen ohne GPU, an im Repo erzeugter Geometrie · 66 Fälle, drei Szenen**

---

## Warum diese Messung

`docs/BRAUCHT_ES_GEOM_IOU_2026-08-26.md` hat gezeigt, dass ein **vollständig
verschwundenes Bauwerk** `geom_iou = 1,000` und Score 0,951 bekommt. Es nennt selbst die
Grenze dieses Befundes:

> *«Sie ist an einer Szene mit viel Boden gemessen (0,790). Aber die Aussage gilt für
> **diese** Lage, nicht für jede.»*

Genau diese Lücke schliesst diese Messung. Dieselbe Methode wie bei den Paarschwellen
(`tools/studie_paarmasse.py`): **perfekte Karten, von Hand etikettierte Fälle**, drei
Szenen mit Bodenanteilen von **0,00 bis 0,42**, dazu der Messpunkt von gestern bei 0,79.

**Es ist eine Obergrenze.** Die Ist-Karten sind gebaut, nicht geschätzt. *Was hier
scheitert, scheitert mit einem echten Schätzer erst recht.*

---

## Befund 1 · Der Boden ist eine Rechenidentität — und er gehört der Szene

Ein **konstantes** Bild — eine Zahl auf jedem Punkt, das wertloseste denkbare Ergebnis —
bekommt:

| Szene | Vordergrundanteil | `geom_iou` (flaches Bild) |
|---|---|---|
| Quader | 0,1103668213 | **0,1103668213** |
| Hochbau | 0,1729431152 | **0,1729431152** |
| Quader auf Geländeplatte | 0,5297393799 | **0,5297393799** |

**Gleich auf volle Gleitkommagenauigkeit, auf allen drei Szenen.** Das ist kein Messwert,
sondern Arithmetik:

    Ein konstantes Bild trägt nirgends die Hintergrundmarke.
    → seine Silhouette ist das GANZE Bild
    → geom_iou = |soll ∩ ist| / |soll ∪ ist| = |soll| / |Bild| = Vordergrundanteil

**Damit hat `geom_iou` einen Boden, den die Szene setzt und nicht das Bild.** Eine Szene,
deren Geometrie die halbe Bildfläche füllt, gibt **jedem** wertlosen Bild 0,53.

*0,53 liest sich wie «zur Hälfte richtig». Es heisst «die Szene ist gross».*

Dasselbe gilt für reines Rauschen: 0,1104 · 0,1729 · 0,5297 — dieselben drei Zahlen.

---

## Befund 2 · Die Decke sieht nicht hinein

Der Fall `innen_vertauscht` — die Tiefen **innerhalb** des Bauwerks gespiegelt, der Umriss
unberührt:

| Szene | Bodenanteil | `geom_iou` | ρ über der Maske |
|---|---|---|---|
| Quader | 0,00 | **1,0000** | −1,0000 |
| Hochbau | 0,00 | **1,0000** | −1,0000 |
| Gelände | 0,42 | **1,0000** | −1,0000 |

**Ein Bauwerk mit vollständig verkehrter Tiefenordnung bekommt die volle Punktzahl.**
Unabhängig vom Bodenanteil, weil der Umriss unberührt ist.

*Zusammen mit Befund 1: `geom_iou` misst den Umriss. Mehr behauptet es nicht — und mehr
darf man ihm nicht entnehmen. Beides steht seit heute unter je einem Test.*

---

## Befund 3 · Das verschwundene Bauwerk — jetzt mit der ganzen Kurve

| Bodenanteil | `geom_iou` bei fehlendem Bauwerk | Score |
|---:|---:|---:|
| 0,00 (Quader, Hochbau) | **0,0000** | nicht messbar |
| 0,42 (Gelände) | **0,8501** | 0,9211 |
| 0,79 (Messung vom 26.08.) | **1,0000** | 0,9507 |

**Der Befund vom 26.08. steht, und jetzt kennt man seine Form.** Ohne Boden fällt
`geom_iou` korrekt auf null — die Silhouette verschwindet mit dem Bauwerk. Mit Boden
steigt es steil, und **bei 0,79 ist es blind**.

*Das ist keine Entwarnung, sondern das Gegenteil: 0,00 ist die Laborszene, 0,79 ist das
Haus auf dem Grundstück. Der Fehler wächst genau in die Richtung, in die jede wirkliche
Szene liegt.*

---

## Befund 4 · Der Ganzbild-Score trennt nicht — mit perfekten Karten

    Trennung: ÜBERLAPPEND.
    Schlechtester GUTER Fall  0,9381
    Bester SCHLECHTER Fall    0,9384
    → drei Zehntausendstel dazwischen, und sie liegen falsch herum.

Bei der heutigen Schwelle **0,65 bestehen vier schlechte Fälle** — beide Geländeläufe mit
verschwundenem Bauwerk (0,9211) und beide mit 20 px Versatz (0,9384). Erst bei 0,95 fällt
`falsch bestanden` auf null, und dann sperrt die Schwelle bereits zwei einwandfreie Bilder.

**Zum Vergleich, an denselben 66 Fällen gemessen:**

| Mass | Trennung | Lücke |
|---|---|---|
| **ρ über der Maske** | **sauber** | 0,6169 … 0,9282 |
| Ganzbild-Score | überlappend | −0,0003 |
| Ganzbild-Spearman (Score ohne `geom_iou`) | überlappend | −0,0698 |
| `geom_iou` | überlappend | −0,0519 |
| Kantenanteil | überlappend | −0,4497 |

**Genau ein Mass von vieren trennt, und es ist nicht das, auf dem das Tor heute steht.**

---

## Befund 5 · `geom_iou` wegzunehmen macht es **schlechter** — und das war die Vermutung wert

Weg 3 des Entscheids lautet: *`geom_iou` aus dem Score nehmen.* Dann bliebe
`abs(spearman)` über das ganze Bild. An denselben 66 Fällen gemessen:

    Trennung: ÜBERLAPPEND.
    Schlechtester GUTER Fall  0,9282
    Bester SCHLECHTER Fall    0,9980
    → die Lücke wächst von −0,0003 auf −0,0698, also um das Zweihundertfache.

**Und der beste schlechte Fall ist ausgerechnet der, um den alles geht:**

| Fall | `spearman` (ganzes Bild) | `geom_iou` | Score heute |
|---|---:|---:|---:|
| **Gelände, Bauwerk verschwunden** | **0,9980** | 0,8501 | 0,9211 |
| Gelände, 20 px versetzt | 0,9933 | 0,8865 | 0,9384 |

Der Grund ist derselbe wie überall in dieser Messung: **Der Boden bleibt liegen.** Nimmt
man das Bauwerk weg und füllt die Lücke mit dem, was daneben steht, ist die
Tiefenstaffelung über das *ganze* Bild fast unverändert — 0,998. `geom_iou` zieht diesen
Fall auf 0,921 herunter, und das ist mehr, als der Spearman allein täte.

**`geom_iou` ist also nicht der Fehler — es ist die einzige Bremse, die der heutige Score
hat.** Sie reicht nicht (0,921 besteht die Schwelle 0,65 mühelos), aber sie wegzunehmen
verschlimmert genau den Fall, für den sie einmal eingebaut wurde.

*Weg 3 ist damit gemessen und nicht mehr offen: Er kostet, statt zu nützen.*

---

## Was diese Messung NICHT sagt

**Die Karten sind gebaut, nicht geschätzt.** Der Fehler des Tiefenschätzers kommt nicht
vor; sein festes Ortsfeld erklärt allein 95,75 % der Varianz auf einem leeren Bild
(HomeStation, `auf-vis-20260824-10`). Die saubere ρ-Trennung ist ein **Bestwert**, kein
Versprechen — sie wird schmaler, sobald geschätzt wird.

**Umgekehrt gilt für die drei überlappenden Masse mehr, nicht weniger:** Sie versagen
schon unter Bestbedingungen. Ein Schätzerfehler macht das nicht besser.

**Zwei der drei Szenen sind symmetrisch**, ihre beiden Kameras sehen dasselbe — 23 von 33
Fallarten waren auf vier Nachkommastellen identisch. Die Zeile «3 Szenen · 2 Kameras» ist
zu zwei Dritteln keine Streuung (siehe `docs/PAARSCHWELLEN_OBERGRENZE_2026-08-27.md`).

**Der Bodenanteil 0,79 stammt aus der Messung vom 26.08. und nicht aus dieser Reihe.**
Drei Punkte einer Kurve sind eine Form, keine Funktion.

---

## Nachbau

    python tools/studie_paarmasse.py build/studie
    python tools/paarschwellen.py build/studie/f_score.json --groesse score
    python tools/paarschwellen.py build/studie/f_iou.json   --groesse geom_iou
    python tools/paarschwellen.py build/studie/f_spearman.json --groesse spearman

Die beiden Rechenidentitäten stehen als Tests in `tests/test_geometrie_qa.py` — sie
brauchen weder Blender noch die Studie.
