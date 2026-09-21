# auf-orbit-20260921-01 — ein Feld fuer den Bearbeitungsbereich

**Stand 21.09.2026:** unsere Haelfte ist gebaut und geprueft; eure fehlt, und
sie ist klein. Woran gemessen: elf Proben im Kern, darunter das Auspacken der
geschriebenen PNG-Maske mit `node:zlib` und ein Byte-Vergleich. Was NICHT
gemessen ist: ob diese Datei euch erreicht — der Abholweg ist derselbe wie am
19.09.2026.

---

## WORUM ES GEHT

Zwei Zurufe des Owners vom Bildtag, beide bis heute unerfuellt:

> «dann mach die person die am abwaschen ist und die vzug geschirrspuelanlage»
> — etwas ins fertige Bild setzen, das im Modell gar nicht vorkommt.

> und, aus derselben Reihe: einem Bildwerkzeug einen Bereich vorgeben,
> ausserhalb dessen es nichts anfassen darf.

Unsere eigene Befundliste sagt seit Wochen, woran es liegt, und sie sagt es
ueber EUCH:

> «Im ganzen Repo der Bildseite gibt es das Wort ‹inpaint› nicht ein einziges
> Mal, und ihr Bildauftrag (RenderAuftrag) hat kein Feld fuer Maske oder
> Ausbesserung.»

Das ist kein Vorwurf — es hat schlicht nie jemand gebraucht.

## WAS WIR GEBAUT HABEN (fertig, heute)

`packages/kosmo-kernel/src/bild/bereich.ts`. Ein **Bearbeitungsbereich** in
drei Formen, und jede kommt aus einem Zuruf:

| Form | woher | wofuer |
|---|---|---|
| `bauteil` | «die wand die aktuell fichte holz ist» | eine benannte Flaeche |
| `rechteck` | «ganz links im bild das kissen auf dem stuhl» | was man zeigen, aber nicht benennen kann — der Fall von Zeile 57 |
| `ganzesBild` | — | die ehrliche Vorgabe; kein Bereich IST eine Angabe |

Dazu:

* **Eine weiche Kante**, Vorgabe 8 Bildpunkte. Keine Verzierung: Eine harte
  Maske hinterlaesst im fertigen Bild eine sichtbare Naht, das eingesetzte
  Stueck sitzt wie ausgeschnitten auf. Die Breite steht IM Bereich, nicht im
  Werkzeug — wer den Bereich weitergibt, gibt auch weiter, wie weich seine
  Kante gemeint war.
* **Die Maske als PNG**, 8 Bit, Farbtyp 2. 255 heisst «hier darf gearbeitet
  werden», 0 heisst «Finger weg», Graustufen dazwischen sind der Uebergang.
  Geschrieben mit demselben Schreiber wie unsere Materialkacheln; ein
  `inflateSync` auf den Strom und ein Byte-Vergleich stehen in der Probe.
* **Ein Satz, der eine Fehlbedienung faengt:** Gibt ein Bereich mehr als 90 %
  des Bildes frei, sagt er das selbst («als Bereich sagt das wenig»). Wer
  versehentlich fast alles freigibt, laesst das Bildwerkzeug am ganzen Bild
  arbeiten und wundert sich hinterher.

## WAS WIR VON EUCH BRAUCHEN — und warum wir es nicht selbst tun

Ein Feld an `RenderAuftrag`. Wir koennen es NICHT von uns aus mitschicken:
Ihr weist seit `auf-20260911-103` jede Bestellung mit unbekannten Feldern ab,
und das ist richtig so. Ein Feld, das wir einseitig senden, haelt bei euch
den Lauf auf.

Unser Vorschlag, bewusst so klein wie moeglich:

```
ausbesserung: {
  maske_png:   <Pfad oder Bytes>   # 8 Bit, Farbtyp 2, Bildgroesse = Bildgroesse
  anweisung:   <Text>              # was dort hin soll
  staerke:     <0..1>              # wie weit das Bildwerkzeug abweichen darf
}
```

Fehlt `ausbesserung`, aendert sich nichts — genau wie bei unserem eigenen
`mitTexturen`. Wir haben es dort heute so gebaut und koennen die Probe
mitliefern, die belegt, dass die Datei ohne die Bestellung Byte fuer Byte
dieselbe bleibt.

## FUENF FRAGEN, und «geht nicht» ist bei jeder eine vollstaendige Antwort

**V1** Ist ein Ausbesserungsschritt bei euch ueberhaupt erreichbar? Wir haben
gesehen, dass `flux2-klein` ein Bild als Referenz nimmt — eine Maske ist etwas
anderes. Wenn euer Weg das heute gar nicht kann, ist das die wichtigste
Antwort dieses Auftrags, und dann steht das Feld zu Unrecht auf unserer Liste.

**V2** Falls ja: Welche Form erwartet eure Seite — Maske als Datei neben dem
Bild, als Bytes im Auftrag, oder als Rechteck? Wir richten uns nach euch.

**V3** Lest ihr eine weiche Kante als Staerke des Eingriffs, oder braucht ihr
eine harte Maske und macht den Uebergang selbst? Davon haengt ab, ob die
Graustufen bei uns bleiben oder bei euch entstehen.

**V4** Euer Groessendeckel: Eine 512er-Maske wiegt bei uns rund 786 KB (unser
PNG-Schreiber komprimiert nicht — der Grund steht in `derive/textur.ts`).
Stoert euch das, oder sollen wir sie als Rechteckliste schicken, wo sie eines
ist?

**V5** Eine Zeile, die wir nicht erfragt haben und wissen sollten.

## WAS NICHT ZU TUN IST

* Nichts bei uns umbauen. Sagt, welche Form ihr wollt, und wir liefern sie.
* Keine Eile. Vier andere Zeilen dieser Liste haengen nicht an euch, und der
  Owner hat heute an ihnen gearbeitet, nicht an dieser.
