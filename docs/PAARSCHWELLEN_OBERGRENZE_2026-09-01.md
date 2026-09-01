# Die Ersatzkalibrierung der Paarschwellen — vier Szenen, vier Richtungen, und was `0.80` kostet

**01.09.2026 · gemessen in dieser Umgebung, ohne GPU, an im Repo erzeugter Geometrie**

---

## Was das hier ist — und was es ausdrücklich nicht ist

`auf-20260827-61` liegt seit dem 27.08. bei der HomeStation und **bleibt offen**. Die
Kalibrierung, die dort ansteht, braucht einen echten Tiefenschätzer und GPU-Zeit; beides
gibt es hier nicht. Der Owner hat am 01.09. entschieden, die Tabelle **bis dahin** hier zu
rechnen — mit gebauten statt geschätzten Ist-Karten.

> **Das Ergebnis ist eine Obergrenze und keine Kalibrierung.** Der Fehler des Schätzers
> kommt nicht vor. Er trägt ein festes Ortsfeld, das allein 95,75 % der Varianz auf einem
> leeren Bild erklärt (`docs/SCHWELLENSTUDIE_ECHT_2026-08-26.md`). Was hier scheitert,
> scheitert mit einem echten Schätzer erst recht; was hier gelingt, ist damit **nicht**
> bestätigt.

**Dieser Vorbehalt steht nicht nur in diesem Text.** Er wird als
`zusatz_vorbehalte` an `paarschwellen.trennkurve` übergeben und setzt dort
`genuegt_als_kalibrierung` auf **falsch** — in allen acht Kurven, auch in denen, deren
Umfang reicht und deren Trennung sauber ist. Der Weg kann eine Kurve nur strenger machen,
nie milder; ein Schalter, der eine Einschränkung *abstellt*, ist mit Absicht nicht
vorgesehen. *Eine Messung, die ihren eigenen Vorbehalt aufweichen kann, ist keine.*

---

## Der Aufbau

Vier Szenen × vier Richtungen × elf Fälle = **176 Zeilen**, 192 × 192 Punkte, 6 Samples.
Werkzeug: `tools/studie_ersatzkalibrierung.py`; Rohdaten `build/ersatz/roh.json`,
Kurven `build/ersatz/kurven.json`.

Die elf Fälle und ihre **von Hand vergebenen** Etiketten sind unverändert die vom 27.08.
(`tools/studie_paarmasse.faelle`) — fünf gute (`treu`, `skala`, `rausch_leicht`,
`glatt_leicht`, `versatz_1px`) und sechs schlechte (`bauwerk_weg`, `versatz_20px`,
`gedreht_90`, `rauschen`, `flach`, `innen_vertauscht`).

**Die Richtung ist die Auswertungseinheit**, nicht eine Spalte unter anderen. Am 28.08.
fielen auf frontalen Richtungen 5 von 20 guten Fällen unter `PAAR_RHO_SCHWELLE` und auf
diagonalen keiner (`docs/RICHTUNGEN_2026-08-28.md`). Darum zwei frontale Richtungen
(`s`, `w`) und zwei diagonale (`sSE`, `nNE`), und darum wird **je Gruppe getrennt**
gerechnet.

| Szene | `s` | `w` | `sSE` | `nNE` |
|---|---|---|---|---|
| `quader` | 0.1981 | 0.1529 | 0.1108 | 0.1108 |
| `hochbau` | 0.2019 | 0.1405 | 0.1785 | 0.1737 |
| `gelaende` | 0.1981 | 0.1529 | 0.1108 | 0.1108 |
| `raeume` | 0.1981 | 0.1529 | 0.1108 | 0.1108 |

*(Geometrieanteil — der Anteil des Bildes, den die Bauwerksmaske deckt.)*

---

## 1 · Die vierte Szene ist keine

**`raeume` liefert in allen 44 Zeilen exakt dieselben Zahlen wie `quader`** — nicht auf
vier Stellen, sondern auf allen. Die beiden `IfcSpace`, die `--raeume` ins Wandinnere
legt, sind von aussen nicht zu sehen; weder die Tiefenkarte noch die Maske kennen sie.
Die Studie ist mit vier Szenen geplant und mit **drei** gemessen worden.

Das ist kein Rechenfehler und wäre ohne die Dublettenprüfung **nicht aufgefallen**: Die
Fallzahl hätte gestimmt, die Tabelle hätte plausibel ausgesehen, und ein Viertel des
Belegs wäre eine Kopie gewesen. *Die vierte Szene war der Sicherheitsabstand — dass genau
sie ausfällt, ist der Grund, warum es sie gab.*

**`gelaende` ist dagegen eine echte vierte Sicht:** nur 8 der 44 Zeilen sind mit `quader`
identisch. Die Platte ändert nichts an der Maske, aber alles an dem, was **hinter** dem
Umriss steht — und daran hängen zwei Dinge:

* `bauwerk_weg` wird überhaupt erst **messbar**. Ohne Gelände steht hinter dem Bauwerk
  die Hintergrundmarke, der Ersatz ist wieder Hintergrund, und ρ ist `None`.
* Der **Kantenanteil bricht ein**: `treu` fällt von 1.0000 (Quader) auf 0.6408 (Gelände).
  Der Umriss ist derselbe; nur steht dahinter jetzt eine Fläche in ähnlicher Tiefe statt
  eines unendlichen Sprungs. **Der Kantenanteil misst nicht das Bauwerk, sondern den
  Kontrast zu seiner Umgebung** — und für ein Bauwerk auf Gelände heisst das: das perfekte
  Bild erreicht 0.64, nicht 1.00.

---

## 2 · Die Dubletten kommen aus zwei ganz verschiedenen Quellen

**88 der 176 Zeilen wiederholen ein Wertepaar ihrer Gruppe** — genau die Hälfte. Sie
zerfallen sauber in zwei Hälften mit verschiedenen Ursachen:

**44 Zeilen: die Szene ist eine Kopie.** Das sind die `raeume`-Zeilen aus Kapitel 1.

**44 Zeilen: das Mass hat Fixpunkte.** Vier der elf Fallarten liefern über **alle** vier
Szenen und beide Richtungen einer Gruppe **einen einzigen** ρ-Wert, und das ist keine
Symmetrie des Bauwerks, sondern eine Eigenschaft der Rechnung:

| Fallart | ρ auf allen 8 Zeilen einer Gruppe | warum |
|---|---|---|
| `treu` | 1.0000 | die Rangfolge ist dieselbe Rangfolge |
| `skala` | 1.0000 | ρ ist rangbasiert, also massstabsfrei |
| `innen_vertauscht` | −1.0000 | die Rangfolge ist exakt umgekehrt |
| `flach` | `None` | ein konstantes Bild hat keine Rangfolge |

Dazu `bauwerk_weg` als halber Fall: `None` auf den drei Szenen ohne Gelände, ein echter
Wert auf `gelaende`. **Diese Zahlen kann man ohne Blender hinschreiben** — sie sind
Eigenschaften der Definition von ρ und nicht Messungen an einem Bauwerk.

Am 27.08. wurde derselbe Befund noch als *«symmetrische Kamerapaare»* gelesen — 23 von 33
Fallarten punktgleich über zwei Kameras. **Das war die falsche Erklärung für die richtige
Beobachtung.** Quader und Gelände sehen von zwei Seiten tatsächlich gleich aus, aber die
Punktgleichheit hängt nicht daran: Sie tritt bei `hochbau` genauso auf, und der ist
asymmetrisch. Was hier doppelt zählt, sind die **analytischen** Fälle.

**Was das für die Fallzahl heisst, in einer Zeile:**

| Gruppe | gute Zeilen | verschiedene ρ | schlechte Zeilen | verschiedene ρ |
|---|---|---|---|---|
| frontal | 40 | **18** | 48 | **22** |
| diagonal | 40 | **16** | 48 | **22** |

Entdoppelt bleiben frontal 23 gute und 23 schlechte, diagonal 19 und 23 — und damit fällt
die diagonale Gruppe unter `MINDEST_GUT = 20`. Der Wächter meldet das von selbst. *Die
Studie hat 176 Zeilen und deutlich weniger Belege, als die Zeilenzahl verspricht.*

---

## 3 · ρ trennt in beiden Gruppen sauber — aber nicht an derselben Stelle

| Gruppe | höchster **schlechter** | niedrigster **guter** | fehlerfreies Fenster |
|---|---|---|---|
| frontal | 0.2568 | 0.3790 | **0.2568 < t ≤ 0.3790** |
| diagonal | 0.5311 | 0.9065 | **0.5311 < t ≤ 0.9065** |

Jede Gruppe für sich lässt sich fehlerfrei trennen. Entdoppelt ändern sich beide Fenster
**nicht um eine Stelle** — die Randfälle sind keine Dubletten.

**Und die beiden Fenster überschneiden sich nicht.**

> **Es gibt keine einzelne ρ-Schwelle, die beide Richtungsgruppen fehlerfrei trennt.**
> Das frontale Fenster endet bei 0.3790, das diagonale beginnt bei 0.5311. Dazwischen
> liegt kein gemeinsamer Wert, sondern eine Lücke von 0,15.

Das ist die schärfste Aussage dieser Studie, und sie ist **nicht** eine Frage der Fallzahl
oder des Schätzers: Sie folgt aus vier Zahlen, die alle mit perfekten Karten gemessen sind.
Ein echter Schätzer kann diese Lücke nur vergrössern.

### Was `PAAR_RHO_SCHWELLE = 0.80` heute kostet

| Gruppe | falsch bestanden | falsch gesperrt | von |
|---|---|---|---|
| frontal | **0** | **5** | 40 guten |
| diagonal | **0** | **0** | 40 guten |

`0.80` liegt oberhalb beider schlechter Gruppen — **kein einziger schlechter Fall kommt
durch**, in keiner Richtung. Der ganze Preis steht in einer Zelle: fünf gute frontale
Fälle werden gesperrt. Es sind diese:

| Fall | ρ |
|---|---|
| `gelaende-w-rausch_leicht` | 0.3790 |
| `gelaende-s-rausch_leicht` | 0.5540 |
| `hochbau-w-rausch_leicht` | 0.6615 |
| `hochbau-w-glatt_leicht` | 0.7391 |
| `hochbau-w-versatz_1px` | **0.7904** |

Vier von fünf sind `rausch_leicht` oder `glatt_leicht` — genau die beiden Störungen, die
eine **frontale** Ansicht am härtesten trifft, weil dort die ganze Tiefenspanne einer
Fassade wenige Dezimeter beträgt und ein Rauschen von 1 % der Spanne die Rangfolge
umwirft. Der fünfte, `hochbau-w-versatz_1px` bei 0.7904, verfehlt die Schwelle um
**0.0096**.

**Der Befund vom 28.08. ist damit bestätigt und geschärft:** damals 5 von 20 guten Fällen
auf einer Szene, jetzt 5 von 40 auf dreien — die Zahl der Sperrungen bleibt gleich, während
sich die Grundmenge verdoppelt hat. Es sind nicht *anteilig* 25 %, sondern **immer
dieselben fünf Konstellationen**: frontale Ansicht, leichte Störung, kleine Tiefenspanne.

---

## 4 · Der Kantenanteil trennt in keiner Gruppe

| Gruppe | höchster **schlechter** | niedrigster **guter** | Trennung |
|---|---|---|---|
| frontal | 1.0000 | 0.4967 | **überlappend** |
| diagonal | 1.0000 | 0.5224 | **überlappend** |

Der beste schlechte Fall erreicht in beiden Gruppen den **Höchstwert 1.0000**. Es ist
`innen_vertauscht`: der Umriss vollkommen, die Tiefen innen gespiegelt, ρ bei −1.0000.
**Es gibt keine Schwelle**, die diesen Fall sperrt, ohne jeden guten mitzusperren.

### Was `PAAR_KANTENANTEIL_SCHWELLE = 0.20` heute tut

| Gruppe | falsch bestanden | falsch gesperrt |
|---|---|---|
| frontal | **18** von 34 messbaren schlechten | 0 von 40 guten |
| diagonal | **12** von 34 | 0 von 40 |

Bei 0.20 sperrt der Kantenanteil **keinen einzigen guten Fall** und lässt **mehr als die
Hälfte der schlechten durch**. Als Tor allein ist er bei diesem Wert nahezu wirkungslos.

**Das ist kein Argument, ihn zu entfernen** — es ist dasselbe Bild wie am 27.08., nur auf
mehr Zeilen: Die beiden Masse versagen in **entgegengesetzte** Richtungen. ρ hält
`innen_vertauscht` (−1.0000) mühelos, wo der Kantenanteil bei 1.0000 blind ist; der
Kantenanteil hält einen Umriss, den ρ über 2,8 % Maske noch ordentlich findet. Ein Paar
aus zwei Massen, die dieselben Fehler machen, wäre eines zu viel. **Dieses Paar macht
verschiedene.**

Was der Kantenanteil dagegen **nicht** ist: eine Grösse mit einem festen Massstab. Sein
Wert für das perfekte Bild schwankt szenenabhängig zwischen 0.64 (Gelände) und 1.00
(Quader) — dieselbe Beobachtung wie beim Boden von `geom_iou`
(`docs/GEOM_IOU_BODEN_UND_DECKE_2026-08-27.md`). Eine Schwelle darauf ist eine Schwelle
auf einer Grösse, deren Nullpunkt die Szene bestimmt.

---

## 5 · Was daraus folgt — und was ausdrücklich nicht

**Was diese Studie trägt:**

1. `PAAR_RHO_SCHWELLE = 0.80` ist als **richtungsblinde** Schwelle vertretbar: null falsch
   bestandene Fälle in beiden Gruppen, der ganze Preis sind fünf gesperrte gute frontale.
2. Eine **bessere einzelne** Zahl gibt es nicht. Wer die fünf retten will, muss unter
   0.7904 gehen — und dann beginnt bei 0.5311 der diagonale Bereich, in dem schlechte
   Fälle durchkommen. Der Gewinn ist nicht in einer Zahl zu haben.
3. Die Verbesserung, die es gäbe, ist eine **richtungsabhängige** Schwelle. Das ist genau
   die Auflage, die `auf-20260827-61` seit dem 28.08. trägt.
4. `PAAR_KANTENANTEIL_SCHWELLE = 0.20` ist **keine Schwelle, sondern eine Formalität** —
   sie sperrt nichts. Ihre Rechtfertigung liegt allein darin, dass sie in der anderen
   Richtung versagt als ρ. Das ist ein Argument für das *Paar*, keines für die *0.20*.

**Was diese Studie nicht trägt:**

* **Keinen Entscheid.** Welcher der beiden Fehler schwerer wiegt — ein durchgelassenes
  falsches Bild oder ein gesperrtes richtiges — ist eine Frage an den Owner und keine
  Messung. `paarschwellen.bericht` schreibt darum unter jede Tabelle *«KEINE EMPFEHLUNG»*.
* **Keine Bestätigung.** Alle acht Kurven melden `genuegt_als_kalibrierung: false`. Fünf
  von acht melden zusätzlich einen zweiten Vorbehalt aus eigener Rechnung.
* **Kein Ersatz für `auf-61`.** Der Auftrag bleibt offen. Was hier gemessen ist, ist die
  Decke des Machbaren; wo der echte Schätzer darunter landet, weiss nur er.

---

## Anhang · Wo die Zahlen herkommen

```
python tools/studie_ersatzkalibrierung.py build/ersatz
```

16 Multipass-Läufe (4 Szenen × 4 Richtungen), daraus 176 Zeilen und acht Trennkurven
(2 Gruppen × 2 Zustände × 2 Grössen). Die Saat wird **je Richtung** zurückgesetzt, damit
ein Unterschied zwischen zwei Richtungen nicht von einem Unterschied zwischen zwei Würfen
kommt — die Lehre aus `tools/studie_richtungen.py`.

Geprüft in `tests/test_studie_ersatzkalibrierung.py`; der Vorbehaltsweg in
`tests/test_paarschwellen.py`.
