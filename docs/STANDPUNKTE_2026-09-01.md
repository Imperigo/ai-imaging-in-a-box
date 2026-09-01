# Was `guete_standpunkt` wirklich unterscheidet — acht Standpunkte, zwei Werte

**01.09.2026 · gerechnet in dieser Umgebung, ohne GPU und ohne Blender**

---

## Der Anlass: ein Folgeposten ohne Adressaten

Die HomeStation hat am 01.09.2026 den Kameraabstand berichtigt — er war 24 bis 25 % zu
gross, weil `+ tiefe/2` die seitlichen Silhouettenkanten auf die Vorderkante setzte. In
derselben Meldung stand ein Satz, den niemand aufgegriffen hätte:

> *«Die Streuung von `flaechenanteil` über die zwölf Richtungen fällt am gedrungenen Bau
> von 2.3 auf 1.17 — ein grosser Teil der alten Spanne WAR der Abstandsfehler. Das
> schwächt `guete_standpunkt` bei kompakten Bauten, und das ist ein Folgeposten, kein
> Nebensatz.»*

*Ein Posten ohne Adressaten wird nie eingebaut, und es fällt keinem auf.* Diese Messung
ist die Antwort darauf. Sie kostet nichts: `kamerasatz` rechnet aus einer Hüllbox, es
braucht weder Bild noch Gerät.

**Werkzeug:** `tools/studie_standpunkte.py` · **Rohdaten:** `build/standpunkte.json`

---

## Der Aufbau

Sechs Formen, von würfelig bis langgestreckt. Die Kantenlängen sind **gesetzt** und
beschreiben Verhältnisse, keine Gebäude — was hier gemessen wird, hängt am
Grundriss-Verhältnis und nicht am Massstab.

| Form | Masse (m) | Grundriss-Verhältnis |
|---|---|---|
| `wuerfel` | 20 × 20 × 20 | 1,00 |
| `turm` | 20 × 18 × 45 | 1,11 |
| `gedrungen` | 30 × 25 × 18 | 1,20 |
| `flachbau` | 40 × 30 × 6 | 1,33 |
| `langriegel` | 103,84 × 57,15 × 27,10 | 1,82 |
| `riegel` | 60 × 12 × 15 | 5,00 |

---

## 1 · Der Befund, den die HomeStation vermutet hat — bestätigt

| Form | Spanne des Flächenanteils |
|---|---|
| `wuerfel` | **1,07 ×** |
| `langriegel` | 1,17 × |
| `gedrungen` | 1,20 × |
| `turm` / `flachbau` | 1,33 × |
| `riegel` | 2,25 × |

Der Docstring von `guete_standpunkt` behauptete bis heute *«Faktor 2,3 bis 1,9 — sie
**kann** also unterscheiden»*. **Beide Zahlen waren mit dem falschen Abstand gemessen.**
Der ehrliche Bereich ist 1,07 bis 2,25, und er hängt fast vollständig am
Grundriss-Verhältnis: Je würfeliger der Bau, desto weniger unterscheidet das Mass.

---

## 2 · Und der härtere Befund, der dabei herausfiel

**Über acht taugliche Standpunkte kennt die Güte höchstens ZWEI verschiedene Werte.**
Auf dem Würfel einen einzigen.

| Form | taugliche Standpunkte | verschiedene Gütewerte |
|---|---|---|
| `wuerfel` | 8 | **1** |
| alle übrigen | 8 | **2** |

Am `langriegel` sieht das so aus:

```
wWN  eEN  wWS  eES   guete 0.783896   (flaeche_norm 0.9973, zweite_fassade 0.7860)
nNW  nNE  sSE  sSW   guete 0.359276   (flaeche_norm 0.9323, zweite_fassade 0.3854)
n  e  s  w           guete 0.000000   — keine zweite Fassade, ausgeschlossen
```

Vier und vier, auf sechs Nachkommastellen identisch. **Die Funktion ordnet nicht acht
Dinge, sie teilt sie in zwei Haufen.** Und das ist kein Rechenfehler: Eine Hüllbox ist
symmetrisch, spiegelbildliche Standpunkte *sind* gleich gut. Nur liest sich eine
Rangfolge, als gäbe es einen besten.

### Was das für die Auswahl heisst

`standpunkte()` zählt alle 56 Dreierkombinationen aus und nimmt die beste. Gezählt, wie
viele denselben Wert erreichen:

| Form | Gleichstand an der Spitze |
|---|---|
| `wuerfel` | **16 von 56** |
| `gedrungen`, `turm`, `flachbau`, `riegel` | 8 von 56 |
| `langriegel` | 4 von 56 |

Die gewählte Dreiergruppe ist also eine von vier bis sechzehn gleichwertigen. Aufgelöst
wird der Gleichstand deterministisch nach `RICHTUNGSFOLGE` — *gemeldet heisst nicht
gewürfelt* —, aber bis heute stand darüber kein Wort.

> **Genau diesen Vorwurf macht `guete_standpunkt` dem Füllgrad:** *«Er ist die Vorgabe,
> die `kamerasatz` einhält, und eine eingehaltene Vorgabe kann nichts unterscheiden. Wer
> nach ihm auswählt, wählt in Wahrheit die Reihenfolge der Liste.»*
>
> Eine Ebene höher galt derselbe Satz für die Auswahl selbst, und niemand sagte es.

Seit heute meldet `standpunkte()` `n_gleichstand`, `n_kombinationen` und eine Warnung im
Klartext.

---

## 3 · Trägt der Flächenanteil die Auswahl überhaupt?

Die Gegenprobe: Ersetzt man ihn bei allen zwölf Richtungen durch **dieselbe Zahl**, so
dass nur noch `zweite_fassade` entscheidet — ändert sich dann der beste Standpunkt?

| Form | bester Standpunkt | ohne Flächenanteil | ändert sich? |
|---|---|---|---|
| `wuerfel` | nNW | nNW | nein |
| `gedrungen` | wWS | wWS | nein |
| `turm` | wWS | wWS | nein |
| `flachbau` | eES | wWS | **ja** |
| `riegel` | wWN | wWN | nein |
| `langriegel` | wWN | wWN | nein |

**In einer von sechs Formen.** Und beim `riegel` — der Form mit der grössten Spanne —
zeigt er sogar in die **andere** Richtung:

```
Sieger      wWN   flaeche_norm 0.9239   zweite_fassade 0.2856   guete 0.263892
Unterlegen  nNW   flaeche_norm 1.0000   zweite_fassade 0.1400   guete 0.140042
```

Der Sieger trägt **weniger** Bildfläche als der Unterlegene; `zweite_fassade` überstimmt
ihn. *Ein Mass, das man überstimmen muss, trägt die Auswahl nicht.*

---

## 4 · Was daraus folgt — und was ausdrücklich nicht

**Was folgt:**

1. Die Zahlen im Docstring sind berichtigt. Sie waren nicht falsch gerechnet, sondern an
   einer falschen Kamera gemessen — *dieselbe Sorte Fehler wie eine Schwelle, die auf
   einem Bild geeicht wurde, das inzwischen anders entsteht.*
2. `standpunkte()` meldet den Gleichstand. Wer drei Standpunkte bestellt, bekommt drei
   und weiss jetzt, dass es zwölf andere genauso gute gibt.
3. Die Auswahl ruht **im Wesentlichen auf `zweite_fassade`** — also auf der Frage «steht
   ein Körper im Bild oder ein Aufriss». Das ist eine vernünftige Frage und es war die
   erklärte Absicht; neu ist nur, dass die zweite Grösse fast nichts beiträgt.

**Was nicht folgt:**

* **Kein Ausbau von `flaechenanteil`.** Er ist nicht schädlich, er ist auf würfeligen
  Grundrissen nur beinahe konstant. Ihn zu entfernen hiesse, den einen Fall aufzugeben,
  in dem er entscheidet.
* **Keine neue Grösse.** Welche dritte Zahl einen Standpunkt besser macht, ist eine
  gestalterische Frage und keine geometrische — sie gehört an den Owner und nicht in
  einen Commit. Die Messung sagt nur, dass Platz dafür wäre.
* **Kein Urteil über echte Bauten.** Sechs Quader sind sechs Quader. Ein echtes Gebäude
  hat Vor- und Rücksprünge, und ob die Güte dort mehr als zwei Werte kennt, ist hier
  nicht messbar. *Was an einer Hüllbox gemessen ist, gilt für Hüllboxen.*

---

## Anhang · Nachrechnen

```
python tools/studie_standpunkte.py
```

Geprüft in `tests/test_studie_standpunkte.py` und `tests/test_standpunkte.py`; drei
Mutationsproben an der Gleichstandsmeldung fallen.
