# Die frontale Innenansicht zeigt eine Fläche — und der Rückfall macht sie unmessbar

**Stand:** 2026-09-09 · **Nachbaubar:** `python tools/studie_innenansicht.py` ·
**Braucht:** Blender und `.venv-ifc`, **keine GPU**

---

## Die Frage, und warum sie seit dem 22.08. offen lag

`docs/PLAN.md` trägt sie im Wortlaut, und sie trägt ihr eigenes Gegenargument mit:

> **Verdacht gegen die frontale INNENANSICHT — ungemessen, und deshalb nicht
> abgeschaltet.** `auf-29` fand: Für ρ über der Maske muss der Blick **mehr als eine
> Fläche** zeigen, sonst misst man den Schätzer statt der Geometrie. […] Eine frontale
> Innenaufnahme zeigt genau das: eine Wand senkrecht zur Blickachse. **Aber innen ist die
> Lage nicht dieselbe** — Boden, Decke und die anschneidenden Seitenwände liegen schräg im
> Bild und tragen Tiefe. Die Ansicht wird darum weiter geliefert; sie wegzulassen wäre ein
> Schluss von einer Messung auf einen Fall, den sie nicht enthält.

Das war die richtige Entscheidung — und sie hat achtzehn Tage gehalten, weil daneben
stand: *«Die Messung ist billig.»* Sie war es. Sie wurde nur nicht gemacht.

**Warum sie hier geht, obwohl ρ den Schätzer braucht.** ρ ist die Frage; *ob überhaupt
etwas zu ordnen ist*, ist die Vorfrage — und die steht in der **Soll-Karte**, die aus
Blender kommt. Kein `torch`, kein Gewicht, keine GPU.

---

## Was gemessen wurde

Die Testgeometrie aus `tools/make_test_ifc.py --raeume`: zwei `IfcSpace` im Wandinneren,
26,62 m² (L-förmig) und 5,94 m² (rechteckig). Je Raum beide Blickarten aus
`raumkamera.standpunkte`, je Blickart **zwei Brennweiten** — die, die `raumkamera`
rechnet, und der Rückfall, den der Blender-Runner stellt, wenn ihm niemand eine nennt.

800 × 496 (dasselbe Seitenverhältnis wie 1600 × 992 in der Produktion), 8 Samples,
Blender 4.2, acht Läufe.

Vier Zahlen je Fall. Die vierte ist die, um die es geht:

| Zahl | was sie sagt |
|---|---|
| **Geometrieanteil** | wieviel des Bildes überhaupt Geometrie trägt |
| **Spanne** | grösste minus kleinste Tiefe |
| **Tiefenstufen** | verschiedene Werte, auf 1 cm gerundet |
| **grösste Ebene** | der Anteil des **ganzen Bildes**, der auf *einem* Wert liegt |

*Die Spanne allein genügt nicht.* Ein Bild kann fünf Meter Spanne haben und trotzdem zu
vier Fünfteln auf einer Ebene liegen — dann trägt es kaum Rangordnung, und ρ misst dort
im Wesentlichen den Schätzer.

---

## Das Ergebnis

```
Raum         Blick      Brennweite         Geometrie  Spanne m  Stufen  groesste Ebene
Raum-Nord    frontal    24 mm (raumkamera)     93.3%     1.191      73           78.8%
Raum-Nord    frontal    50 mm (Rueckfall)     100.0%     0.000       1          100.0%
Raum-Nord    ueber_eck  24 mm (raumkamera)     84.2%     4.998     489            0.6%
Raum-Nord    ueber_eck  50 mm (Rueckfall)      99.7%     3.650     366            0.5%
Raum-Sued    frontal    24 mm (raumkamera)     96.2%     2.288     207           56.9%
Raum-Sued    frontal    50 mm (Rueckfall)     100.0%     0.335      34           95.9%
Raum-Sued    ueber_eck  24 mm (raumkamera)     85.1%     5.106     497            0.5%
Raum-Sued    ueber_eck  50 mm (Rueckfall)      99.9%     3.650     366            0.5%
```

### Befund 1 · Der Verdacht trägt, das Gegenargument nur zum Teil

Frontal liegen **56,9 %** und **78,8 %** des Bildes auf *einer* Ebene. Über Eck sind es
**0,5 %** und **0,6 %** — Faktor **über hundert**, und die beiden Räume sind sich darin
einig, obwohl sie sich in Fläche und Zuschnitt um mehr als das Vierfache unterscheiden.

Das Gegenargument ist nicht falsch: Boden und Seitenwände tragen sehr wohl etwas bei —
1,19 m und 2,29 m Spanne statt der 0,000 m, die eine reine Wandaufnahme ergibt. Es reicht
nur nicht. **Der Blick bleibt von einer Fläche beherrscht.**

### Befund 2 · Der Rückfall auf 50 mm macht die Aufnahme unmessbar

Das ist der schwerere Fund, und er stand nicht in der Frage.

Bei 50 mm trägt die Tiefenkarte des grösseren Raums **einen einzigen Wert**: Spanne
0,000 m, **eine** Stufe, 100 % des Bildes. Das ist nicht «etwas ungenauer» — eine
Rangkorrelation über eine Karte ohne jede Ordnung misst **nichts**, und die ganze
Geometrie-QA dieses Projekts ruht auf Tiefenrängen.

**Woher die 50 mm kommen.** `raumkamera` rechnet je Standpunkt ein Sichtfeld: 24 mm
(`BRENNWEITE_INNEN_MM`), die sichtbare Breite an der Zielwand, und die *nötige*
Brennweite, wenn die Wand nicht ins Bild passt — geprüft gegen die belegte Grenze von
16 mm. Über die Prozessgrenze ging davon **nichts**: `kette._fuehre_multipass` reichte
Auge und Blickziel hinüber und liess die Brennweite fallen. Der Runner stellt dann seinen
Rückfall.

> **Zum vierten Mal dieselbe Sache.** Brennweite und Geländestand am 23.08.,
> `gelaende_erwartet` am 24.08., drei Kameraparameter am 26.08. — im Modul längst
> gerechnet, auf dem Weg nicht durchgereicht. *«Einstellbar» ist eine Zusage, die man an
> der Naht prüfen muss und nicht am Modul.*

**Behoben am selben Tag**, mit drei Mutationsproben (`tests/test_innenansicht.py`): Der
Durchgriff entfernt, die Zahl aus einer Konstanten statt aus dem Standpunkt geholt, und
die Innenbrennweite auch dem Aussenweg untergeschoben — jede fällt beim richtigen Test.

### Befund 3 · Über Eck ist stabil, frontal ist es nicht

Über Eck liefern beide Räume und **beide** Brennweiten dasselbe Bild der Lage: 0,5 bis
0,6 % auf der grössten Ebene, 366 bis 497 Stufen. Frontal schwankt derselbe Wert zwischen
56,9 % und 100 %.

*Eine Ansicht, deren Messbarkeit an der Brennweite hängt, ist die unangenehmere von
beiden* — sie sieht in jedem Fall wie ein Bild aus.

---

## Die Grenzen, und sie sind hart

**Die Testräume haben keine Decke.** `make_test_ifc.py` baut vier Wände und eine
Bodenplatte; die zwei `IfcSpace` liegen im Wandinneren. Das Gegenargument im Plan nennt
die Decke ausdrücklich — dieser Teil ist damit **nicht** widerlegt, sondern ungeprüft. Und
er ist mit dieser Geometrie auch nicht prüfbar: `--hochbau` und `--raeume` schliessen
einander aus, mit Begründung (*«Die beiden Räume aus RAEUME sind an die Wandflucht des
Quaders gerechnet und lägen im Hochbau mitten im Kern»*).

**Es sind zwei Räume, kein Bestand.** Beide sind rechteckig oder L-förmig, beide klein,
beide ohne Öffnungen mit Tiefe dahinter. Ein Raum mit Fenster in eine Landschaft hätte
eine andere Tiefenordnung.

**Und es ist eine Vorprüfung.** Die Hausregel vom 24.08.2026 gilt: *Renders und Nullanker
können ein Mass widerlegen, aber nicht tragen.* Dass frontal kaum Ordnung trägt, ist ein
Ausschluss und gilt. Dass über Eck welche trägt, sagt über ein **erzeugtes** Bild nichts —
drei Vorschläge dieses Projekts sind genau an dieser Stelle gefallen.

---

## Was daraus folgt

**Nicht abgeschaltet.** Die frontale Innenansicht wird weiter geliefert. Der Grund ist
derselbe wie am 22.08., nur jetzt mit einer Zahl: Sie ist eine fotografisch übliche
Ansicht, und *die Metrik nicht messen zu können ist kein Grund, das Bild nicht zu machen* —
es ist ein Grund, das **Urteil** darüber zurückzuhalten.

**Gebaut ist der Durchgriff, nicht die Regel.** Was fehlt, ist die Entscheidung, ob eine
flächenbeherrschte Aufnahme ihr Geometrie-Urteil überhaupt tragen darf. Das ist dieselbe
Frage wie bei `himmel_hinter_umriss` am 23.08. — dort lautete die Antwort *«nicht
zuständig»* statt *«durchgefallen»*. Sie hier genauso zu beantworten, wäre naheliegend und
darum verdächtig: Es fehlt die Messung an einem erzeugten Bild.

**`auf-20260909-87` fragt sie am Gerät:** dieselben vier Fälle, aber mit dem echten
Schätzer und ρ über der Maske. Erst dann steht fest, ob «von einer Fläche beherrscht» eine
Zuständigkeitsgrenze verdient oder bloss eine Zeile im Befund.

---

## Nachbauen

```
python tools/studie_innenansicht.py
python tools/studie_innenansicht.py --breite 1600 --hoehe 992      # Produktionsmass
python tools/studie_innenansicht.py --json
```

Die Zahlen oben stammen aus dem Lauf mit den Vorgabewerten. *Eine Zahl, die in einem
Dokument steht und nicht nachgebaut werden kann, ist eine Behauptung.*
