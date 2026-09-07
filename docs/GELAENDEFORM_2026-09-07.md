# Gelände an der Form — was sie trennt, und was sie kostet

**07.09.2026** · gemessen in dieser Umgebung, **ohne GPU**, an im Repo erzeugter Geometrie

---

## Warum es diese Regel gibt, und warum kein weiteres Wort

Die Geländeregel dieses Projekts liest **Namen**. Auf echtem Bestand versagt sie messbar:

| | |
|---|---|
| Knoten der Bestandsdatei | 4771 |
| Schrumpfung der Bauwerksbox | **2,32 %** |
| grösster verbliebener «Bauwerks»-Knoten | `IfcCovering_Sub-Division:…`, **90,78 m = 47 % der Szenenspannweite** |

*Eine Box, die 2 % bringt, sieht aus wie die Lösung.* Und der Ausweg «ein Wort mehr» ist
verschlossen — der Kommentar an `maske.WOERTER_AUSDRUECKLICH_NICHT` hält es fest:

> *«Damit ist der Befund nicht, welches Wort noch fehlt, sondern dass es keines gibt.»*

Belegt an zwei Zahlen aus demselben Bestand: `decke` wäre **nötig** (an einem
Geländemodell heissen 111 von 112 Knoten so) und ist zugleich **unmöglich** (in einer
Gebäudedatei desselben Projekts tragen 418 von 2742 Knoten dieselbe Vokabel für
Geschossdecken).

Das «von aussen» war als Feld im Szenenvertrag gedacht (`auf-20260901-67`) und liegt dort
seit dem 01.09.2026 unbeantwortet. **Dies ist das zweite «von aussen» — das, für das
niemand gefragt werden muss.**

---

## Was gemessen wird

Drei Merkmale je Körper, alle **relativ zur Szene**, alle aus den Hüllboxen, die
`glbbox.knotenboxen` ohnehin liefert — keine Dreiecke, kein Blender:

1. **Grundrissanteil** — Grundfläche des Körpers ÷ Grundfläche der Szene
2. **Flachheit** — Höhe ÷ **kleinere** Grundriss-Kante
3. **Tieflage** — Oberkante im Höhenbereich der Szene, `0` unten, `1` oben

Die Flachheit misst gegen die kleinere Kante, weil ein langer schmaler Steg sonst «flach»
wäre, obwohl er aufragt.

---

## Die Schwellen — und ihr Preis in beiden Richtungen

| Schwelle | Wert | Woher |
|---|---|---|
| `GRUNDRISSANTEIL_MIN` | **0,25** | Der Prüfstein liegt bei 47 %. Nicht höher, weil ein Vorplatz reicht; nicht tiefer, weil die Bodenplatte des Bauwerks drinbleiben soll. |
| `FLACHHEIT_MAX` | **0,15** | Ein Geländekörper ist eine Platte. Darüber ragt etwas auf. |
| `TIEFLAGE_MAX` | **0,35** | Gelände liegt unten. |
| `TIEFLAGE_UNKLAR_MAX` | **0,60** | Darüber: **nicht entscheidbar**, nicht Bauwerk. |

### Das Ergebnis über sechs Bestände

```
BAUWERK FAELSCHLICH AUSGESCHLOSSEN: 0   (die TEURE Richtung)
GELAENDE UEBERSEHEN:                0   (die billigere)
NICHT ENTSCHEIDBAR:                 1   (kein Fehler, sondern die dritte Antwort)
```

**Die beiden Richtungen sind nicht gleich teuer, und das entscheidet die Schwellenwahl.**

* *Gelände in der Maske* macht sie stumpf — auf einer Bodenszene erreichte weisses
  Rauschen dort den Score **0,72**.
* *Bauwerk fälschlich ausgeschlossen* macht die Box zu klein; die Kamera steht zu nah und
  schneidet das Bauwerk an.

Der erste ist teurer. Die Schwellen sind darum streng: **im Zweifel Bauwerk.**

### Die volle Tabelle

```
Bestand              Knoten                       soll      ist                  Anteil   Flach   Tief  Lage
quader_auf_platte    IfcCovering_Toposolid_1      gelaende  gelaende            100.0%    0.01    3%  
quader_auf_platte    Wand-01                      bauwerk   bauwerk               4.0%    1.50  100%  
sub_division         IfcCovering_Sub-Division:1   gelaende  gelaende             54.8%    0.01    1%  
sub_division         Stuetze-01                   bauwerk   bauwerk               1.6%    2.25  100%  
sub_division         IfcCivilElement_Nachbar_1    bauwerk   bauwerk               2.5%    1.00   56%  
riegel               Gelaende-Platte              gelaende  gelaende            100.0%    0.03    4%  
riegel               Riegel                       bauwerk   bauwerk              33.3%    1.38  100%  
decke_im_bauwerk     IfcCovering_Toposolid_1      gelaende  gelaende            100.0%    0.01    3%  
decke_im_bauwerk     Decke-025                    bauwerk   nicht entscheidbar   36.0%    0.01   50%  nicht entscheidbar
decke_im_bauwerk     Wand-01                      bauwerk   bauwerk              36.0%    0.50  100%  
zwei_ebenen          IfcCovering_Toposolid_1      gelaende  gelaende            100.0%    0.01    4%  
zwei_ebenen          Terrasse                     gelaende  gelaende             28.0%    0.01   16%  
zwei_ebenen          Wand-01                      bauwerk   bauwerk              16.0%    0.65  100%  
ohne_gelaende        Wand-01                      bauwerk   bauwerk              82.6%    0.75   97%  
ohne_gelaende        Dach                         bauwerk   bauwerk             100.0%    0.02  100%  
```

---

## Was die Form **nicht** trennt

Ein Fall bleibt offen, und er bleibt es mit Absicht: **`Decke-025`** — eine grosse flache
Geschossdecke auf halber Höhe. Grundrissanteil 36 %, Flachheit 0,01, Oberkante bei 50 %
der Szenenhöhe.

Nach Form sieht sie aus wie ein Geländesockel. Sie ist keiner. **Und die Form kann das
nicht wissen** — ein Geländesockel auf halber Höhe hätte dieselben drei Zahlen.

> *Nicht messbar ist weder Gelände noch Bauwerk.*

Sie zählt in der Rahmung als Bauwerk, weil Gelände in der Maske teurer ist — aber der
Befund sagt es, statt zu raten. Wer die Zahl `NICHT ENTSCHEIDBAR: 1` liest, weiss, dass
die Regel hier bei fünf von sechs Beständen sicher ist und bei einem nicht.

---

## Wie sie eingebaut ist: eine Zweitmeinung, keine zweite Regel

Der Unterschied ist der ganze Bau:

* Eine **zweite Regel** widerspricht der ersten. Dann sind zwei im Spiel, und eine davon
  ist falsch — genau davor warnt `bauwerksbox` beim Parameter `regel`.
* Eine **Zweitmeinung** spricht nur, wenn die erste schweigt. Sie überstimmt nichts.

Deshalb wird die Form erst gefragt, wenn die Namensregel unter `GERINGE_SCHRUMPFUNG`
(5 %) geblieben ist — am echten Bestand mit 2,32 % also sehr wohl. Und der Befund sagt
danach, **welche Regel entschieden hat** (`entschieden_durch`): *eine Box, der man nicht
ansieht, woher sie kommt, ist die Box, die um 2,32 % schrumpfte und wie eine Lösung aussah.*

### Am Prüfstein, an der wirklichen Kette

Eine erzeugte glb, deren Gelände `IfcCovering_Sub-Division:1` heisst und 47 % der
Spannweite einnimmt:

| | vorher | jetzt |
|---|---|---|
| `entschieden_durch` | — | **`form`** |
| Schrumpfung | **0 %** (die Regel fand nichts) | **83 %** |

---

## Was offen bleibt

**Diese Zahlen sind an selbstgebauten Körpern gerechnet — und genau daran ist die
Namensregel gescheitert.** Die Messung, die zählt, läuft an der echten 4771-Knoten-Datei
und liegt als Auftrag bei der HomeStation. Erwartet wird: Schrumpfung deutlich über
2,32 %, `Sub-Division` als Gelände erkannt, die drei Merkmale je erkanntem Knoten zur
Nachprüfung.

*Bis diese Zahlen da sind, ist die Formregel gebaut und nicht bestätigt.*

---

## Anhang · Woher die Zahlen kommen

```
python tools/studie_gelaendeform.py
python tools/studie_gelaendeform.py --json
```

`src/aiimaging/gelaendeform.py` · `tests/test_gelaendeform.py` ·
`auftraege/ergebnisse/auf-20260826-51.json` (die Bestandsmessung)
