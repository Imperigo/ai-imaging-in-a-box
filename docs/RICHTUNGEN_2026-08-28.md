# Hängt die Messbarkeit am Standpunkt? — acht Richtungen, dieselbe Szene

**28.08.2026 · ohne GPU, 58 Sekunden · `tools/studie_richtungen.py`**

---

## Die Vermutung, die dazu führte

Beim Umstellen der Kamera von *gekippt* auf *shift* wurde ein Test rot: Dieselbe Szene,
dieselbe frontale Kamera, nur der Modus getauscht — **341 gegen 18** verschiedene
Tiefenwerte im Bild.

Daraus wurde die Vermutung: *Frontale Ansichten tragen zu wenig Tiefensignal, und die
Rangkorrelation hat dort wenig zu ordnen.* Sie ging als offene Frage an die HomeStation.

**Sie ist falsch.** Und die Messung zeigt, woran das liegt.

---

## Der Aufbau

Hochbau (141 Bauteile), 192 px, vier **frontale** Richtungen (`n`, `e`, `s`, `w`) gegen
vier **diagonale** (`nNE`, `eES`, `sSE`, `wWN`). Je Richtung dieselben elf Fälle wie in der
Obergrenzen-Studie — fünf gute und sechs schlechte, **von Hand etikettiert**.

Die Zufallszahl wird je Richtung zurückgesetzt: Sonst bekäme die zweite Kamera anderes
Rauschen als die erste, und ein Unterschied zwischen zwei Richtungen wäre nicht mehr von
einem Unterschied zwischen zwei Würfen zu trennen.

| Richtung | Gruppe | Tiefenspanne in der Maske | verschiedene Tiefenwerte |
|---|---|---:|---:|
| `n` | frontal | 9,647 m | 357 |
| `e` | frontal | 8,904 m | 158 |
| **`s`** | frontal | **0,421 m** | 241 |
| `w` | frontal | 11,291 m | 196 |
| `nNE` | diagonal | 7,986 m | 540 |
| `eES` | diagonal | 9,546 m | 339 |
| `sSE` | diagonal | 7,779 m | 339 |
| `wWN` | diagonal | 10,615 m | 543 |

---

## Befund 1 · ρ trennt auf **jeder** Richtung

    frontal    Lücken +0,515 bis +0,763
    diagonal   Lücken +0,563 bis +0,822

Es gibt keinen frontalen Zusammenbruch. Die Vermutung ist widerlegt.

**Und die Richtung `s` ist der Beleg dafür, warum.** Sie sieht ihre Fassade mit einer
Tiefenspanne von **0,42 m** — dem Zwanzigstel der übrigen — und liefert trotzdem die
**besten** guten Werte der frontalen Gruppe: 0,880 bis 0,999.

> **Rangbasiert heisst massstabsfrei.** Eine Spanne von 0,42 m trägt so viel Rangordnung
> wie eine von 11 m. Das steht seit dem ersten Tag als Begründung im Modul; hier ist es
> zum ersten Mal gemessen statt behauptet.

**Die Zahl «verschiedene Tiefenwerte» sagt über die Messbarkeit nichts.** Sie ist ein
Artefakt der 16-Bit-Normalisierung: `s` hat 241 davon über 0,42 m, `e` nur 158 über 8,9 m.
*Wer sie als Signalmass liest, misst die Skalierung und nicht die Szene.*

---

## Befund 2 · Was stattdessen dasteht, ist schärfer — und es trifft die Schwelle

Die **guten** Fälle liegen auf frontalen Richtungen systematisch tiefer:

| | schlechtester guter Fall |
|---|---:|
| frontal | 0,664 … 0,880 |
| diagonal | **0,932 … 0,951** |

Gemessen gegen `PAAR_RHO_SCHWELLE = 0.80`:

| Gruppe | gute Fälle unter der Schwelle |
|---|---:|
| **frontal** | **5 von 20** |
| **diagonal** | **0 von 20** |

Namentlich: `n`/geglättet 0,769 · `e`/verrauscht 0,692 · `w`/verrauscht 0,664 ·
`w`/geglättet 0,739 · `w`/1 px versetzt 0,790.

> **Die Schwelle ist richtungsabhängig.** Eine an diagonalen Ansichten kalibrierte Zahl
> sperrt auf frontalen gute Bilder — und niemand sähe, dass der Standpunkt es war.

Das geht als Auflage in `auf-20260827-61`: **Die Richtung gehört in jede Zeile der
Kalibriertabelle**, und beide Gruppen müssen aufgenommen werden. Nur diagonale zu messen
ergäbe eine Schwelle, die im Betrieb frontale Bilder sperrt; nur frontale eine, die zu
mild ist.

---

## Befund 3 · Und darum ist die Vorgabe des Homeworkers diagonal

`homeworker.VORGABE_KAMERA = "sSE"` steht seit dem 28.08.2026 — **gemessen, nicht
gewählt.** Frontale Ansichten sind nicht unmessbar; sie sind die schlechtere Vorgabe.

*Wer eine frontale Richtung ausdrücklich bestellt, bekommt sie — `params.kamera`.*

---

## Was diese Messung NICHT sagt

**Die Karten sind gebaut, nicht geschätzt** — dieselbe Einschränkung wie bei der
Obergrenzen-Studie. Der Schätzerfehler kommt nicht vor.

**Eine Szene, ein Gebäude.** Ob der Unterschied zwischen frontal und diagonal an der
*Fassadengliederung* dieses Baus hängt oder allgemein ist, sagt diese Messung nicht. Der
Hochbau hat Fassadentafeln mit Fugen, ein Stützenraster und eine Auskragung — ein glatter
Kubus verhielte sich womöglich anders.

**Vier von zwölf Richtungen.** Die diagonalen sind je eine aus einem Quadranten, aber acht
weitere Richtungen der Standardfolge sind ungemessen.

---

## Nachbau

    python tools/studie_paarmasse.py build/studie     # erzeugt die Szene
    python tools/studie_richtungen.py build/frontal

*Diese Studie lief zuerst aus einem Skript unter `build/` — also **ausserhalb** des Repos,
und es wurde danach gelöscht. Ihre Zahlen standen bereits in zwei Aufträgen, die andere
ausführen sollen, als das auffiel. Sie ist deshalb ein Werkzeug geworden, mit zehn Tests;
die Zahlen oben reproduzieren exakt.*
