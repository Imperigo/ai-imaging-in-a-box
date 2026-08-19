# Der Rauschboden — und warum er die Frage noch nicht beantwortet

**`auf-20260820-20`, gemessen auf der HomeStation · und eine Einschränkung, die von mir
selbst stammt**

---

## Was gefragt war

Wir haben mehrfach zwei Renderläufe verglichen und aus dem Unterschied etwas gefolgert.
Der wichtigste dieser Schlüsse: *„ControlNet-Stärke 0.80 schneidet besser ab als 1.00"*
(`auf-20260818-13`, 0.2649 gegen 0.2421).

**Nie gemessen wurde, wie weit zwei Läufe mit völlig gleichen Parametern auseinanderliegen,
wenn nur der Seed anders ist.** Ohne diese Zahl ist jeder solche Schluss unbelegt.

---

## Was gemessen wurde

Fünf Läufe, `seed` 1000 … 1004, alles andere identisch. Szene: der synthetische Testbau
**ohne Boden**, wie in `auf-13`. Prüfsummen aller fünf Bilder verschieden — es sind
wirklich fünf verschiedene Bilder.

| Seed | Score | `n_gemeinsam` |
|---|---|---|
| 1000 | **ungemessen** | 2 |
| 1001 | 0.0803 | 1925 |
| 1002 | **ungemessen** | 0 |
| 1003 | 0.0641 | 1005 |
| 1004 | 0.0034 | 137 |

| | |
|---|---|
| Mittel (3 messbare) | 0.0493 |
| Standardabweichung | **0.0331** |
| Spanne | **0.0770** |
| Variationskoeffizient | **67 %** |

**Zwei von fünf Läufen sind gar nicht messbar** — und sind ausdrücklich als *ungemessen*
und nicht als *null* gemeldet, wie der Auftrag es verlangte. Bei Seed 1002 gibt es
**keinen einzigen** gemeinsamen Bildpunkt zwischen Soll- und Ist-Silhouette.

Dass jeder zweite bis dritte Lauf aus der Messbarkeit fällt, ist selbst ein Befund.

---

## Die Folgerung der HomeStation — und wo sie eine Lücke hat

Sie schliesst: **Der `auf-13`-Vergleich war Rauschen.** Der dortige Unterschied von 0.0228
liegt deutlich unter der hier gemessenen Standardabweichung von 0.0331, erst recht unter
der Spanne von 0.0770.

Das ist plausibel und wahrscheinlich richtig. **Belegt ist es damit noch nicht**, und der
Grund liegt bei mir:

> Zwischen `auf-13` und dieser Messung habe ich die **Hintergrundstrategie** geändert.

Am 20.08. habe ich die Vorgabe von `ohne_randberuehrung` auf `wie_soll` zurückgenommen —
weil `auf-20260819-15` gezeigt hatte, dass die erste Regel in jeder Szene **mit** Boden
null Punkte wählt. Der Auftrag sagte „nach `git pull` mit der Vorgabe messen", und genau
das hat die HomeStation getan. Sie konnte es nicht wissen.

**Die Szene dieser Messung hat aber keinen Boden.** Und das ist genau der eine Fall, für
den die zurückgenommene Regel gebaut war und in dem sie gewinnt.

Die Zahlen bestätigen es. Bei einem Bild *ohne* Boden legt der Tiefenschätzer eine
Bodenebene hinein (`auf-10`); mit `wie_soll` wandert diese Scheingeometrie in die
Ist-Silhouette und zerstört die Überdeckung:

| | `geom_iou` | `n_gemeinsam` |
|---|---|---|
| `auf-13` (mit `ohne_randberuehrung`) | 0.082 | 3670 |
| heute (mit `wie_soll`) | ≈ 0.006 | 0 … 1925 |

Das ist rund ein **Dreizehntel**. Die beiden Messungen stehen damit an **zwei
verschiedenen Betriebspunkten**, und eine Standardabweichung, die bei einem Mittel von
0.049 erhoben wurde, lässt sich nicht ohne Weiteres gegen einen Unterschied halten, der
bei einem Mittel von 0.25 gemessen wurde.

**Der Rauschboden ist an der einen Szenenart gemessen, für die die zurückgenommene Regel
gebaut war. Ein Gebäude steht auf dem Boden.**

Das ist — an einem Tag — das **dritte** Mal derselbe Satz:

> **Eine Messung gilt so weit, wie gemessen wurde.**

---

## Was trotzdem feststeht, und es ist unangenehm genug

**1 · Die Streuung über den Seed ist real und gross.** Innerhalb dieser fünf Läufe, an
diesem Betriebspunkt: 67 % Variationskoeffizient. Ein Einzellauf als Vergleichsgrundlage
ist damit wertlos, und das gilt unabhängig vom Betriebspunkt.

**2 · Jeder zweite bis dritte Lauf ist nicht messbar.** `n_gemeinsam` schwankt von 0 bis
1925. Das ist keine Frage der Genauigkeit, sondern der Existenz einer Messung.

**3 · Die Kette hat noch nie ein erzeugtes Bild geliefert, das das Geometrie-Gate
besteht.** `auf-13` bestes: 0.265. Heute bestes: 0.080. Die Schwelle ist **0.65**. Das
steht so seit dem 18.08. in den Zahlen und ist nie als eigener Satz aufgeschrieben worden.

---

## Nachtrag am selben Tag: Ein Teil davon ist Arithmetik

Beim Zusammenrechnen der bisherigen Läufe zeigt sich, dass Punkt 3 nicht ganz das heisst,
wonach er klingt.

Der Score ist ``sqrt(|spearman| × geom_iou)``. Umgestellt: Für ``score ≥ 0.65`` braucht es
bei einer Rangkorrelation von 1.0 — dem bestmöglichen Wert — ein ``geom_iou`` von
mindestens **0.4225**.

Und die gemessenen Deckel:

| Szene · Strategie | `geom_iou`-Deckel | höchstmöglicher Score | 0.65 erreichbar? |
|---|---|---|---|
| ohne Boden · `wie_soll` | 0.256 | 0.505 | **nein** |
| ohne Boden · `ohne_randberuehrung` | 0.406 | 0.636 | **nein** |
| Platte endlich · `wie_soll` | 0.967 | 0.982 | ja |
| Ebene bis Rand · `wie_soll` | 0.974 | 0.986 | ja |

Die Deckel stammen aus `auf-12` und `auf-15` und sind an **gerenderten** Bildern gemessen
— also am bestmöglichen Fall, den diese Kette auf dieser Szene überhaupt hergibt.

> **Alle unsere Renderläufe liefen auf der Szene ohne Boden. Dort war die Schwelle 0.65
> arithmetisch unerreichbar.**

Ein durchgefallenes Bild belegte dort **nichts** über seine Geometrietreue — der Lauf
misst dann nicht das Bild, sondern die Szene.

### Und trotzdem ist das nicht die ganze Erklärung

Der Deckel lag bei 0.636, die erzeugten Bilder bei **0.265**. Zwischen „bestmöglich" und
„erreicht" klafft noch einmal derselbe Abstand. **Beides ist wahr, und keines erklärt das
andere weg:**

* Das Gate war unerreichbar — deshalb *bedeutet* „nie bestanden" weniger, als es klingt.
* Die Bilder blieben weit unter dem Erreichbaren — das ist ein echter Rückstand und bleibt
  einer.

`geometrie_qa.erreichbarkeit()` beantwortet die Frage jetzt **vor** dem Rechnen. Sie
kostet nichts und hätte den Unterschied gemerkt, bevor er drei Aufträge gekostet hat.

**4 · Die HomeStation meldet eine Lücke, die sie nicht erklären kann**, statt sie zu
glätten: Der `auf-13`-Lauf erreichte 0.2649, der beste heute 0.0803 — bei angeblich
identischen Einstellungen. Sie nennt es ausdrücklich als offene Frage. Die
Hintergrundstrategie erklärt das plausibel; **geprüft ist es nicht.**

---

## Was daraus folgt

**Als Frage, nicht als Empfehlung** — so hat es die HomeStation formuliert, und so bleibt
es:

- Der Rauschboden muss **an der Szenenart gemessen werden, die zählt**: mit Boden. Erst
  dort gilt die zurückgenommene Vorgabe, und erst dort steht ein Gebäude wie ein Gebäude.
- Beide Hintergrundstrategien gehören in denselben Lauf, sonst bleibt die Erklärung für
  den Faktor 13 eine Vermutung.
- Und erst danach lässt sich sagen, ob `auf-13` Rauschen war. **Bis dahin gilt die
  Empfehlung „0.80 schlägt 1.00" als unbelegt** — nicht als widerlegt, sondern als
  unbelegt. Der Unterschied ist wichtig.

Das ist der Auftrag `auf-20260820-21`.

---

## Eine Notiz zur Arbeitsweise

Der Auftrag sagte wörtlich: *„Beide Ergebnisse sind wertvoll; das zweite wäre unangenehm
und müsste trotzdem gemeldet werden."* Die HomeStation hat geantwortet: *„Hier ist es."*

Dass ich die Folgerung jetzt einschränke, ist **keine** Zurückweisung dieser Meldung. Die
Einschränkung stammt aus einer Änderung, die ich am selben Tag gemacht habe und die im
Auftrag nicht erwähnt war. Der Befund selbst — dass die Streuung gross ist und dass jeder
zweite bis dritte Lauf ausfällt — steht.


---

# Teil 2 · Mit Boden — und der Befund ist schwerer als der erste

**`auf-20260820-21`**, fünf Läufe auf `platte_endlich` (59,8 % Geometrieanteil), **feste
Kamera**, jedes Bild **zweimal** ausgewertet.

## Die beiden gestellten Fragen

**Wie gross ist die Streuung mit Boden?**

| | ohne Boden (`auf-20`) | mit Boden (`auf-21`) |
|---|---|---|
| Mittel | 0.0493 | **0.5356** |
| Standardabweichung | 0.0331 | **0.0758** |
| Variationskoeffizient | **67 %** | **14,2 %** |
| Ausfälle | 2 von 5 | **0 von 5** |

Absolut **grösser** (Faktor 2,29), relativ **deutlich kleiner**. Und keine Ausfälle mehr:
Die Messbarkeit war ein Problem der Szene, nicht des Verfahrens.

**Wie weit liegen die Strategien auseinander?** `ohne_randberuehrung` liefert **fünfmal
`n_ist = 0`** und keinen einzigen Score. Damit ist die Erklärung für den Faktor 13 auch am
**erzeugten** Bild belegt, nicht nur an Blenders Beauty-Pass. Die Rücknahme der Vorgabe war
richtig.

## Und dann die Nullprobe, die niemand verlangt hatte

Die HomeStation hat aus eigenem Antrieb vier Kontrollbilder durch dieselbe Kette geschickt
— Bilder, die **nicht** aus dem Modell stammen. Das kostet keinen Renderlauf und ist der
eigentliche Ertrag des Auftrags:

| Kontrollbild | Score | `geom_iou` | \|rho\| | Gate 0.65 |
|---|---|---|---|---|
| Beauty (perfekte Geometrie) | 0.9839 | 0.970 | 0.998 | ✓ |
| **weisses Rauschen** | **0.7217** | 0.568 | 0.917 | **✓** |
| leeres Graubild | 0.5188 | 0.303 | 0.889 | ✗ |
| strukturloser Verlauf | 0.3483 | 0.291 | 0.417 | ✗ |

**Unsere fünf Läufe: 0.4708 … 0.6568.**

> **Weisses Rauschen besteht das Gate — und schlägt jeden unserer fünf Läufe.**

Der eine Lauf über der Schwelle (0.6568, Seed 1004) liegt **24,8 % unter dem
Rauschanker**. Er hat das Gate bestanden und belegt nichts.

### Warum, und es liegt nicht am Rauschen

Ein monokularer Schätzer legt in **jedes** Bild eine zum Horizont laufende Bodenebene
(`auf-20260818-10`). Eine Szene, die zu 60 % aus Boden besteht, **ist** im Wesentlichen so
eine Rampe. Die Rangkorrelation misst dann die Übereinstimmung zweier Bodenrampen — und
die ist hoch, egal was im Bild steht.

> **Auf einer Szene mit viel Boden misst die Kette nicht mehr das Bauwerk, sondern die
> Bodenrampe.**

## Die Zange, in der wir stecken

| Szenenart | Fehler |
|---|---|
| **wenig Boden** (17 %) | Der Deckel liegt bei 0.64 — das Gate ist **unerreichbar** |
| **viel Boden** (60 %) | Rauschen erreicht 0.72 — das Gate **trennt nicht** |

Beides ist gemessen. Was **dazwischen** liegt, ist es nicht — und ausgerechnet dort liegt
die Geometrie, die wir am selben Tag gebaut haben: Testbau mit Gelände, Kamera aufs
Bauwerk, **24,7 %**.

## Was gebaut wurde

`geometrie_qa.NULLANKER` und `einordnung()`. Ein Score wird ab jetzt nicht mehr nur gegen
die Schwelle gehalten, sondern gegen das, was **nichts** auf derselben Soll-Karte erreicht
— genau wie `stil_qa` seit dem 18.08. gegen den gemessenen Boden von SigLIP 2 hält.

**Ohne Nullprobe gibt es keine Einordnung, sondern die Feststellung, dass keine vorliegt.**
Eine geschätzte wäre schlimmer als keine: Sie sähe aus wie ein Urteil.

## Der zweite Befund, den ich nicht überlesen will

Unsere Renders erreichen \|rho\| von **0.23 bis 0.45**. Weisses Rauschen erreicht **0.92**.

Das ist keine Aussage über die Metrik, sondern über die Bilder: **Die erzeugten Bilder
haben eine Tiefenstruktur, die schlechter zur Vorgabe passt als Rauschen.** Ein
naheliegender Verdacht ist die Polarität der Tiefenkarte, die in diese Läufe als
`invertiert` einging. Geprüft ist er nicht — er steht als eigener Planpunkt.
