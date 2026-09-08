# auf-20260907-82 — Die Formregel am echten Bestand

Datei: <die 4771-Knoten-Bestandsdatei, 25 063 384 Byte .glb>, 4771 Knoten, 0 ohne min/max.
Messweg durchweg: `PYTHONPATH=src .venv-render/bin/python`, reine Kopfauswertung der
glb (glTF min/max). Kein Blender, kein Render, keine GPU.

## M1 — Die zwei Zahlen

```
PYTHONPATH=src .venv-render/bin/python -c "from aiimaging import glbbox;
 aus=glbbox.bauwerksbox(<die 4771-Knoten-Bestandsdatei, 25 063 384 Byte .glb>, up_axis='Y');
 print(aus['entschieden_durch'], aus['schrumpfung'])"
-> 'name' 0.023201149398744514   (exit 0)
```

    entschieden_durch  'name'   (erwartet war 'form')
    schrumpfung        2.32 %   (erwartet war deutlich mehr als 2,32 %)
    n_gelaende         10
    n_bauwerk          4761

**Die Formregel hat nicht gesprochen.** Die Zahl ist unveraendert dieselbe wie am
06.09.2026 — Bit fuer Bit: 0.023201149398744514.

## M5 — Woran es lag: ZWEI voneinander unabhaengige Gruende

### Grund 1 — der `hatte_namen`-Riegel in `glbbox._zweitmeinung`

Die Zweitmeinung wird zwar befragt (2,32 % < GERINGE_SCHRUMPFUNG 5 %), gibt aber
sofort zurueck, weil die Namensregel etwas gefunden hat — 10 Knoten. Der Riegel steht
bei `if hatte_namen: return aus` und ist im Quelltext begruendet: *«Die Namensregel
hat etwas gefunden, nur zu wenig. Dann bleibt sie zustaendig.»* Der Auftragstext
beschreibt die Bedingung als «nur, wenn die Namensregel unter 5 % Schrumpfung
geblieben ist». Gemessen ist die Bedingung enger: Sie verlangt zusaetzlich, dass die
Namensregel **gar nichts** gefunden hat. **Das ist eine Abweichung zwischen Auftrag
und Quelltext, und der Quelltext hat recht behalten.**

Gegenprobe (kann widersprechen, weil sie beide Zweige faehrt):

```
glbbox._zweitmeinung(alle, up_axis='Y', hatte_namen=True)
  -> entschieden_durch None, gelaende_namen None
glbbox._zweitmeinung(alle, up_axis='Y', hatte_namen=False)
  -> entschieden_durch 'form', gelaende_namen 1 Knoten
```

### Grund 2 — auch OHNE den Riegel aendert die Form nichts

Und das ist der wichtigere Befund. Ohne Riegel faende die Form genau **einen** Knoten:
`IfcCovering_Toposolid:Toposolid_1:95_338BGF1wzCwupEkmd7sW7…` — und den hat die Namensregel bereits.
Die Bauwerksbox waere danach nicht enger, sondern **weiter**:

```
Szenen-Grundrissdiagonale                       192.511 m
Namensregel, 10 Knoten ausgeschlossen  -> Schrumpfung  2.320 %
Formregel  ,  1 Knoten ausgeschlossen  -> Schrumpfung  0.000 %
```

**Der Riegel hat hier nicht gebremst, er hat geschuetzt.** Haette die Form uebernommen,
waere die Rahmung von 2,32 % auf 0,00 % zurueckgefallen.

## M2 — Was die Form als Gelaende erkannt hat

1 von 4771 Knoten:

    IfcCovering_Toposolid:Toposolid_1:95_338BGF1wzCwupEkmd7sW7R
      Grundrissanteil 0.9515 · Flachheit 0.0373 · Tieflage 0.2576
      Grundrissanteil 95.2%, Flachheit 0.04, Oberkante bei 26% der Szenenhoehe — gross, flach und unten.

**`Sub-Division` ist NICHT darunter.** Kein einziger der 20 `Sub-Division`-Knoten wird
von der Form als Gelaende erkannt — siehe M4.

## M3 — Was die Form NICHT entschieden hat

    form_befund.unklar   0 Knoten
    form_befund.gelaende 1 Knoten
    bauwerk              4770 Knoten

Die Null ist hier **kein gutes Zeichen**, sondern die Folge davon, dass der Trichter
schon an der ersten Schwelle zufaellt — `unklar` kann nur entstehen, wenn ein Knoten
die ersten beiden Schwellen passiert:

```
alle Knoten                                   4771
  Grundrissanteil >= 0.25                         1
    davon Flachheit <= 0.15                      1
      davon Tieflage <= 0.35  -> GELAENDE         1
      davon Tieflage <= 0.6   -> UNKLAR           0
```

Gegenprobe zur Null (sie kann widersprechen, denn sie faehrt denselben Code auf
selbstgebauten Koerpern): eine Szene 100x100x50 mit vier Koerpern liefert
gelaende=('platte_unten',), unklar=('platte_mitte',), bauwerk=('hochhaus',
'platte_oben'). **Der unklar-Pfad lebt.** Die Null ist eine Aussage ueber die Datei,
nicht ueber toten Code.

## M4 — Die drei Merkmale

### Der eine erkannte Knoten

    Grundrissanteil 0.951541
    Flachheit       0.037347
    Tieflage        0.257641

### Die 20 `Sub-Division`-Knoten, absteigend nach Grundrissanteil

```
  Grundrissanteil  Flachheit  Tieflage   scheitert an
       0.221467   0.025718  0.217255   Grundrissanteil
       0.052238   0.126879  0.186105   Grundrissanteil
       0.027456   0.127862  0.258031   Grundrissanteil
       0.018440   0.013221  0.186927   Grundrissanteil
       0.014526   0.018505  0.186293   Grundrissanteil
       0.013762   0.072984  0.119523   Grundrissanteil
       0.013387   0.054470  0.185246   Grundrissanteil
       0.012473   0.153845  0.175600   Grundrissanteil
       0.010564   0.016691  0.179794   Grundrissanteil
       0.010473   0.083759  0.214333   Grundrissanteil
       0.009938   0.113715  0.109298   Grundrissanteil
       0.007933   0.003446  0.180381   Grundrissanteil
       0.007319   0.072087  0.181677   Grundrissanteil
       0.006375   0.025703  0.116542   Grundrissanteil
       0.005670   0.003561  0.180224   Grundrissanteil
       0.005255   0.096040  0.212992   Grundrissanteil
       0.003181   0.202166  0.158731   Grundrissanteil
       0.000745   0.068716  0.186970   Grundrissanteil
       0.000661   0.039917  0.180461   Grundrissanteil
       0.000648   0.038818  0.181668   Grundrissanteil
```

**Alle zwanzig scheitern an der ersten Schwelle.** Der groesste kommt auf
0.221467 und braucht 0.25 — es fehlen 0.028533.

## Zusatzbefund A — die Schwelle 0,25 ist an einer LAENGE geeicht, nicht an einer FLAECHE

Der Docstring zu `GRUNDRISSANTEIL_MIN` begruendet die 0,25 mit den 47 % aus
`auf-20260826-51`. Diese 47 % sind aber ein **Anteil an der Szenen-SPANNWEITE**, das
Merkmal `grundrissanteil` ist ein **Anteil an der Szenen-FLAECHE**. Gemessen an
demselben Knoten:

```
Grundriss-Spannweite des Knotens           90.78 m
  Anteil an der Szenenspannweite          0.4715   <- die zitierten 47 %
Grundriss-ANTEIL (Flaeche/Flaeche)      0.221467
Quadrat des Laengenanteils              0.222355   <- deckt sich damit
Schwelle GRUNDRISSANTEIL_MIN                0.25
```

Eine Schwelle, die diesen Knoten fangen sollte, muesste unter 0,2215 liegen, nicht
unter 0,47. **Wir aendern nichts** — die Schwelle gehoert dem Auftraggeber, und eine an
dieser Datei nachgezogene Schwelle waere an ihr geeicht. Der Befund ist die Zahl.

## Zusatzbefund B — die 2,32 % sind gar keine Gelaende-Schrumpfung

Jeder der 10 Namensknoten einzeln entfernt, Schrumpfung gemessen:

```
   0.000 %   IfcCovering_Toposolid:Toposolid_1:95_338BGF1wzCwupEkmd7sW7
   0.000 %   IfcSlab_Toposolid:Toposolid_Stra_0SrMHRZpD1q81lpFZfqxSA
   0.000 %   IfcSite_Floor:Aussen_-_Gras:9405_1$v3RpjEPC3BiKuxPyrDAh
   0.000 %   IfcSite_Model_Text:400mm_Arial_3_2x1yR2RNvCX9jHsiBhxRKR
   0.000 %   IfcSite_Generic_Models_37:Generi_0Dp7Bi4VP7whCdqGmnFnh_
   0.000 %   IfcSite_Generic_Pyramid:Generic__3VBOyvgTHECwW9dsjcA$y6
   0.000 %   IfcSite_Specialty_Equipment_12:S_1Y_y5wxUb2muKDmrYdUC_g
   0.000 %   IfcSite_Model_Text:125mm_Arial:1_1Y_y5wxUb2muKDmrYdUC_A
   0.000 %   IfcSite_Model_Text:140mm_Arial:1_1Y_y5wxUb2muKDmrYdUCzk
   2.320 %   IfcSite_Model_Text:600mm_Arial:1_2ZN3ABakb3awk17kN64BEq
```

**Die ganzen 2,32 % haengen an einem einzigen Knoten, und der ist eine
Textbeschriftung**: `IfcSite_Model_Text:600mm_Arial:…`, 49,75 x 19,75 x 0,15 m, flach
am Suedrand liegend und ueber die Szenengrenze hinausragend. Das eigentliche Gelaende
(`Toposolid_1`, 135,50 x 130,12 m, 95 % der Grundflaeche) traegt **0,000 %**, weil es
ganz innerhalb der uebrigen Szene liegt.

Die Bezugszahl der ganzen Untersuchung misst also nicht «wie viel Gelaende die Regel
herausnimmt», sondern «wie weit eine Planbeschriftung ueber das Modell hinausragt».
Eine Formregel, die perfekt jedes Gelaende faende, koennte diese Zahl nicht
verbessern — das Gelaende liegt nicht aussen.

## Zusatzbefund C — die Form urteilt je Knoten, das Gelaende ist in 20 Stuecke zerlegt

Rein hypothetisch, ohne Aenderung am Modul: die Huellbox ueber alle 20
`Sub-Division`-Knoten zusammen ergibt

    Grundrissanteil 0.918184 · Flachheit 0.037016 · Tieflage 0.258031
    Urteil der Form darauf: gelaende

Die Merkmale sind richtig gewaehlt — sie treffen die Platte, sobald sie EINE Platte
ist. Der Bestand liefert sie aber als Familie, und `gelaende_knoten` urteilt je
Knoten. Das ist kein Schwellenproblem, sondern ein Korngroessenproblem.

## Was NICHT geaendert wurde

`gelaendeform.py` und die vier Schwellen sind unberuehrt. `git status` im Repo ist
sauber. Die bestehenden Tests zu Form und Box laufen gruen:
`PYTHONPATH=src .venv-render/bin/python -m pytest tests -k 'gelaendeform or glbbox' -q`
-> 43 passed, 5437 deselected, exit 0.
