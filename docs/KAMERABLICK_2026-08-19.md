# Die zwölf Bilder angesehen — was zwölf grüne Zahlen nicht zeigten

**19.08.2026.** `docs/PLAN.md` führte den Punkt *„Die zwölf Bilder ansehen"* mit dem
Zusatz: **braucht ein Augenpaar, keine Zahl.** Das ist hier eingelöst — zwölf echte
Blender-Läufe an einem synthetischen Wohnhaus (40 × 26 × 15 m, Sockel + Hauptkörper +
zurückgesetzte Attika + Anbau; Regel 3: kein echtes Projekt), quadratischer Rahmen,
256 px, 8 Samples.

Alle zwölf Kameras bestehen den Eckentest, alle zwölf melden `vollstaendig: True`, und
der Füllgrad liegt bei allen zwölf zwischen 0.548 und 0.550. **Trotzdem taugen die Bilder
nicht.** Drei Gründe, in der Reihenfolge ihrer Tragweite.

---

## 1 · Der Füllgrad ist konstant, die Bildfläche schwankt um den Faktor drei

```
                 gemeldet      Breite     Höhe     FLÄCHE im Bild
n                  0.549        0.512     0.176        6.5 %
e                  0.548        0.391     0.289        9.6 %
s                  0.549        0.496     0.199        8.0 %
w                  0.548        0.473     0.238        7.6 %
nNE                0.550        0.418     0.145        4.2 %
eEN                0.550        0.402     0.160        4.5 %
eES                0.550        0.297     0.172        4.5 %
sSE                0.550        0.320     0.164        4.6 %
sSW                0.550        0.418     0.152        4.4 %
wWS                0.550        0.402     0.156        4.1 %
wWN                0.550        0.254     0.148        3.3 %
nNW                0.550        0.297     0.141        3.4 %
```

Der Füllgrad ist **nicht falsch**: Er beantwortet die Frage „wurde der Deckungsgrad
eingehalten", und die Antwort ist zwölfmal ja — die *Breite* trifft 0.51 bei
angeforderten 0.55. Er beantwortet nur nicht die Frage, die ein Mensch stellt.

**Und die Ursache ist keine Fehlfunktion, sondern Geometrie.** Ein 40 m breiter, 15 m
hoher Bau kann einen quadratischen Rahmen nicht füllen: Erfüllt er die Breite, ist die
Höhe zwangsläufig leer. Das ist eine Frage des **Formats** oder des **Vordergrunds** —
nicht des Abstands. Näher heranzugehen würde den Bau anschneiden, nicht das Bild füllen.

*Behoben:* `kameras.flaechenanteil` rechnet die konvexe Hülle der acht projizierten
Hüllbox-Ecken. Gegen alle zwölf Messungen geprüft — sie liegt für jede Kamera darüber
(die Hüllbox ist voller als der Bau) und ordnet die zwölf Ansichten richtig.

---

## 2 · Die Szene hat keinen Boden — und das ist vermutlich die Hälfte des `geom_iou`-Deckels

Auf jedem der zwölf Bilder **schwebt der Baukörper in gleichmässigem Grau.** Es gibt keine
Bodenplatte, kein Gelände, keinen Horizont.

`auf-20260818-10` hat gemessen, warum `geom_iou` schon beim perfekten Bild bei 0.261
deckelt: Der monokulare Tiefenschätzer *legt in eine flache, gleichmässige Fläche eine
Bodenebene hinein*, die zur Bildecke hin auf die Kamera zuläuft. Nur 34 % der gewählten
Punkte lagen auf dem Bauwerk.

> Wir haben ihm ein Bild ohne Boden gegeben — und uns dann darüber gewundert, dass er
> einen erfindet.

Ein Schätzer, der an Naturfotos trainiert wurde, hat noch nie ein schwebendes Gebäude
gesehen. **Die Frage ist damit offen und war es bisher nicht:** Verhält er sich anders,
wenn die Szene einen echten Boden hat? Ein realer Architekturrender hat immer einen.

Das ist **nicht** hier zu entscheiden, sondern zu messen — `auf-20260819-15`. Und es ist
kein kleiner Eingriff: Ein Boden reicht bis zum Horizont, verändert damit die Tiefenspanne
und über die Normalisierung jeden Grauwert der Karte. Er könnte den Deckel heben oder
verschieben. Ihn einzubauen, weil er „offensichtlich richtig" ist, wäre genau der Fehler,
den `groesste_flaeche` in `auf-20260818-12` vorgeführt hat: Der naheliegendste Griff traf
null Prozent.

---

## 3 · Der Beauty-Pass trennt Bauwerk und Hintergrund kaum

Gebäudegrau und Weltgrau liegen dicht beieinander; der Baukörper hebt sich nur über seine
Kanten ab. Für die Tiefenkarte ist das gleichgültig — sie trennt sauber —, für ein
Bildmodell nicht: Es bekommt ein Ausgangsbild mit sehr wenig Zeichnung.

Das ist kein Fehler der Kamera und keiner des Renderers, sondern eine Folge davon, dass
die Beleuchtung bewusst schlicht gehalten ist („die Lichtstimmung ist nicht Gegenstand
dieser Phase, die Reproduzierbarkeit schon", `blender_depth_stage.py`). Es gehört
trotzdem notiert: Sobald die Bildstufe ernsthaft bewertet wird, ist ein kontrastarmes
Ausgangsbild eine Störgrösse, die niemand angemeldet hat.

---

## Was das für die Stilfrage bedeutet

Der Hausstil `kosmo_standard` verlangt *„something in the near foreground giving depth"*
und ein **quadratisches** Format — beides aus den Referenzbildern des Owners abgeleitet.
Die Referenzen sind in ihren Quadraten nicht leer: Sie sind voll Wiese, Bäume, Strasse,
Menschen. **Unsere Szene hat nichts davon**, und darum wirkt dasselbe Format bei uns wie
ein Fehler.

Der Stil und die Szene widersprechen sich also — und der Widerspruch liegt nicht im Stil.
Entweder bekommt die Szene einen Vordergrund, oder das Format folgt dem Baukörper statt
dem Stil. Das ist eine Entscheidung des Owners und keine Rechenfrage.

---

## Was hier NICHT getan wurde

* **Kein Boden eingebaut.** Siehe oben — das gehört gemessen (`auf-20260819-15`).
* **Kein Format geändert.** Der Hausstil sagt quadratisch, und ein Bildbefund an einem
  synthetischen Haus reicht nicht, um eine Stilentscheidung des Owners zu überstimmen.
* **Nichts an der Beleuchtung.** Sie ist bewusst schlicht; sie zu ändern verschöbe jede
  bisher gemessene Zahl.
