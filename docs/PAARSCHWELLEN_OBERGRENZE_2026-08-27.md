# Können die Paarmasse überhaupt trennen? — die Obergrenze, ohne Schätzer

**27.08.2026 · gemessen in dieser Umgebung, ohne GPU, an im Repo erzeugter Geometrie**

---

## Was hier gefragt wird, und warum vor `auf-61`

`auf-20260827-61` schickt die HomeStation los, die beiden Paarschwellen zu kalibrieren —
GPU-Zeit, echter Schätzer, echte Bilder. Bevor jemand das ausgibt, ist eine billigere
Frage zu klären:

> **Können die beiden Masse überhaupt trennen — mit *perfekten* Karten?**

Denn die Antwort ist eine **Obergrenze**. Die Ist-Karten sind hier nicht geschätzt,
sondern aus der Soll-Karte **gebaut**; der Fehler des Tiefenschätzers kommt gar nicht
vor. *Was hier nicht trennt, trennt mit einem echten Schätzer erst recht nicht. Was hier
trennt, ist damit noch nicht bestätigt.*

Dieselbe Abgrenzung wie bei der Schwellenstudie: **Sie deckt das Mass ab, nicht den Weg
dorthin.**

---

## Der Aufbau

Drei Szenen × zwei Kameras × elf Fälle = **66 Zeilen**.

| Szene | Geometrieanteil | Bodenanteil |
|---|---|---|
| Quader | 0.1104 | 0.0000 |
| Hochbau, 141 Bauteile | 0.1729 / 0.1675 | 0.0000 |
| Quader auf vierfacher Geländeplatte | 0.1104 | 0.4194 |

Die Etiketten *gut* und *schlecht* sind **von Hand vergeben** und nicht aus einer
Störungsstärke abgeleitet — das ist der Unterschied zur Schwellenstudie und der Grund,
warum `paarschwellen.trennkurve` und nicht `schwellenstudie.trennschaerfe_kurve` gerechnet
wurde.

**Gut (5):** `treu` · `skala` (streng monotone Umrechnung) · `rausch_leicht` (σ = 1 % der
Spanne) · `glatt_leicht` (3×3-Mittel) · `versatz_1px`

**Schlecht (6):** `bauwerk_weg` · `versatz_20px` · `gedreht_90` · `rauschen` · `flach` ·
`innen_vertauscht` (die Tiefen **innerhalb** des Bauwerks gespiegelt, der Umriss bleibt)

---

## Befund 1 · ρ trennt sauber — und die abgelesene 0,80 liegt mitten in der Lücke

    Trennung: SAUBER. Jede Schwelle über 0.6169 und bis 0.9282 trennt fehlerfrei.
    30 gut (30 messbar) · 36 schlecht (26 messbar)

| Schwelle | falsch bestanden | falsch gesperrt |
|---:|---:|---:|
| 0.60 | 2 | 0 |
| **0.65** | **0** | **0** |
| **0.80** | **0** | **0** |
| 0.90 | 0 | 0 |
| 0.95 | 0 | 3 |

Der schlechteste gute Fall liegt bei **0,9282** (`glatt_leicht` am Quader), der beste
schlechte bei **0,6169** (`versatz_20px` am Gelände). Dazwischen liegen **0,31** — eine
breite Lücke, und **`PAAR_RHO_SCHWELLE = 0.80` liegt fast genau in ihrer Mitte.**

*Das ist ein Ergebnis über die abgelesene Zahl, nicht über die Kalibrierung: Sie war
kein schlechter Griff. Kalibriert ist sie damit nicht — auf perfekten Karten trennt fast
jede Zahl zwischen 0,62 und 0,93, und welche davon einen **geschätzten** Fall noch trägt,
sagt diese Messung ausdrücklich nicht.*

---

## Befund 2 · Der Kantenanteil trennt NICHT — und man sieht, woran

    Trennung: ÜBERLAPPEND. Der schlechteste gute Fall liegt bei 0.5503,
    der beste schlechte bei 1.0000 — es gibt keine fehlerfreie Schwelle.

| Schwelle | falsch bestanden | falsch gesperrt |
|---:|---:|---:|
| **0.20** (heute) | **12** | **0** |
| 0.45 | 6 | 0 |
| 0.60 | 6 | 2 |
| 0.70 | 6 | 10 |
| 0.90 | 6 | 10 |

**Zwei Zahlen erklären die ganze Tabelle.**

*Die sechs, die nie hängen bleiben,* sind die `innen_vertauscht`-Fälle: Ihr Kantenanteil
ist **1,0000** — der höchstmögliche. Das Bauwerk zeichnet seinen Umriss vollkommen, und
**innen sind die Tiefen gespiegelt**. Bei ihnen sagt ρ = **−1,0000**, also *vollständig
verkehrt herum*.

*Die zehn, die ab 0,70 fälschlich gesperrt werden,* sind die guten Fälle der
Geländeszene: Das **perfekte** Bild erreicht dort nur **0,6927**. Eine Schwelle über 0,55
fängt an, einwandfreie Renders abzuweisen.

**Damit versagen die beiden Masse in entgegengesetzte Richtungen.** Der Quelltext von
`anteil_grenze_mit_kante` warnt schon vor der einen Richtung — *ein anständiges ρ ist ohne
jede Umrisstreue erreichbar* (qwen: ρ −0,74 bei 2,8 % Umriss). Hier steht die **Umkehrung**
daneben: **perfekte Umrisstreue bei vollständig falschen Tiefen.**

*Das ist das stärkste Argument, das dieses Projekt bisher dafür hat, beide Zahlen zu
führen und keine aus ihnen zu rechnen. Ein Mittelwert aus 1,0000 und −1,0000 wäre 0 —
und 0 heisst hier weder das eine noch das andere.*

---

## Befund 3 · Der Fall, um den es geht, ist auf zwei von drei Szenen NICHT MESSBAR

**Zehn von 66 Zeilen sind nicht messbar**, und sie verteilen sich nicht zufällig:

| Fall | Quader | Hochbau | Gelände |
|---|---|---|---|
| `bauwerk_weg` | **nicht messbar** | **nicht messbar** | ρ = 0.0601 |
| `flach` | nicht messbar | nicht messbar | nicht messbar |

Der Grund ist einfach und einleuchtend: **Ohne Gelände gibt es nichts, womit sich die
Lücke füllen liesse.** Entfernt man das Bauwerk aus einer Szene ohne Boden, steht in der
Maske nur noch die Hintergrundmarke — eine Konstante, und eine Konstante hat keine
Rangfolge. ρ ist dann `None`: **weder bestanden noch durchgefallen.**

**Und das ist die richtige Antwort, nicht die bequeme.** Im dreiwertigen Tor wird daraus
`null` — *nicht beurteilbar* —, nicht *bestanden*. Der Fall rutscht also nicht durch; er
landet in der dritten Antwort, und dort gehört er hin.

**Wo Boden liegt, wird derselbe Fall messbar und fällt klar durch** (ρ = 0,0601 gegen die
Schwelle 0,80). Genau dort ist er auch gefährlich: Das ist die Lage, in der der Score bei
0,951 bleibt (`auf-20260826-60`). *Der Maskenweg greift also gerade da, wo der Score
blind ist — und schweigt da, wo der Score ohnehin fällt.*

---

## Was diese Studie NICHT trägt — und es ist mehr, als es aussieht

### Die zwei Kameras sind grösstenteils **eine** Messung

**23 von 33 Fallarten sind auf vier Nachkommastellen identisch** zwischen `sSE` und `nNW`:

| Szene | identisch |
|---|---|
| Quader | 10 von 11 |
| Gelände | 8 von 11 |
| Hochbau | 5 von 11 |

Zwei Ursachen, und beide sind bemerkenswert:

1. **Die Fälle sind angeschlagen.** `treu` und `skala` ergeben 1,0000, `innen_vertauscht`
   ergibt −1,0000, `flach` ergibt `None` — diese Werte sind durch die *Konstruktion*
   festgelegt und können sich mit der Kamera gar nicht ändern.
2. **Quader und Geländeszene sind symmetrisch.** `sSE` und `nNW` sehen denselben Körper.

**Das ist eine Rasterdublette**, dieselbe Falle wie in der Schwellenstudie vom 18.08. —
nur diesmal nicht über die Stärkeachse, sondern über die Kameraachse. Die Zeile «3 Szenen ·
2 Kameras» sieht nach Streuung aus und ist zu zwei Dritteln keine.

**Nur der Hochbau streut wirklich:** `versatz_20px` gibt dort 0,4706 gegen 0,4592,
`gedreht_90` 0,2999 gegen 0,2263, und der Kantenanteil schwankt von 0,3869 auf 0,1719 —
*über den Faktor zwei, allein durch den Standpunkt.*

### Und die Karten sind gebaut, nicht geschätzt

Der Kern der Einschränkung. Zwischen Soll und Ist liegt im Betrieb ein monokularer
Tiefenschätzer, dessen festes Ortsfeld allein **95,75 %** der Varianz auf einem leeren
Bild erklärt (HomeStation, `auf-vis-20260824-10`). Nichts davon ist hier enthalten.

**Die Lücke von 0,31 zwischen gut und schlecht ist deshalb ein Bestwert und keine
Erwartung.** Sie wird schmaler, sobald geschätzt wird — die Frage ist nur, um wieviel.

---

## Was daraus für `auf-61` folgt

1. **Die Kalibrierung von ρ lohnt sich.** Das Mass trennt im Prinzip, und zwar deutlich.
   Was fehlt, ist die Zahl unter Schätzerrauschen.
2. **Die Kalibrierung des Kantenanteils lohnt sich in dieser Form nicht.** Er trennt auch
   unter Bestbedingungen nicht: Sechs schlechte Fälle gehen bei **jeder** Schwelle durch,
   und ab 0,55 fängt er an, perfekte Bilder zu sperren. *Er ist damit kein Torkandidat,
   sondern eine Anzeige — was er seit dem 22.08. für das Median-Mass ohnehin schon ist.*
3. **Symmetrische Szenen zählen nicht doppelt.** Wer zwei Kameras verlangt, muss
   asymmetrische Geometrie nehmen, sonst misst er zweimal dasselbe. Der Auftrag sagt das
   jetzt.

---

## Nachbau

    python tools/studie_paarmasse.py build/studie
    python tools/paarschwellen.py build/studie/f_rho.json
    python tools/paarschwellen.py build/studie/f_kante.json --groesse kantenanteil

Auflösung 256, 8 Samples, Zufallszahl 20260827. Gesamtlaufzeit 36 Sekunden, ohne GPU.
