# erg-20260917-70 — `auf-20260901-70` (an: ui): unsere Haelfte ist gebaut, `message` wird bei `queued` gelesen und angezeigt

**Stand 17.09.2026:** erledigt — woran gemessen: `j.message` wird bei jedem Job-Poll
uebernommen und die Beschriftung unterscheidet seit dem Fund zwischen «niemand holt ab» und
«abgeholt und zurueckgestellt», mit dem Wortlaut aus `message` unveraendert in der grossen
Platzhalter-Flaeche.

Arbeitsstand: `kosmo-orbit` HEAD `407b0cc3` (2026-09-17). Reine Lesemessung.

---

## Eure Haelfte — nachgemessen

Befehl:
```
grep -n "WARTET_ABHOLER_LABEL\|wartetAbholerLabel\|wartetAbholerText\|wartetGrund" apps/kosmo-orbit/src/modules/vis/vis-runtime.ts apps/kosmo-orbit/src/modules/vis/NodeCanvas.tsx
```
* `j.message` wird bei **jedem** Poll in `wartetGrund` uebernommen, nicht nur im
  `kein-render-worker`-Zweig, den das Blatt als Luecke benennt
  (`NodeCanvas.tsx:762`, `:984`, `:993`).
* `wartetAbholerLabel(grund)` (`vis-runtime.ts:200-202`) liefert **«wartet — abgeholt,
  zurueckgestellt»**, sobald ein Grund gesetzt ist, sonst unveraendert
  `WARTET_ABHOLER_LABEL` («wartet — nicht abgeholt (Grund unbekannt)») — exakt die zwei
  Faelle, die euer Blatt als «heute nicht unterscheidbar» benennt, sind jetzt getrennt.
* Der volle Wortlaut aus `message` erscheint unveraendert (keine Kuerzung/Umformulierung)
  in der grossen Platzhalter-Flaeche des Render-Knotens
  (`wartetAbholerText()`, `vis-runtime.ts:255ff`, Kopfkommentar Zeile 247-253 zitiert das
  Blatt woertlich: «mit gesetztem `RenderJob.message` ist die Frage ‹Laeuft auf der
  HomeStation ein Render-Abholer?› FALSCH»). Genau dieser Satz faellt weg, sobald ein Grund
  bekannt ist — wie im Blatt selbst verlangt.
* Eine Kurzform fuer die Companion-Karte kam als Nachtrag desselben Pakets dazu
  (`WARTET_ABHOLER_KURZ_ZURUECK`, `vis-runtime.ts:222-228`) — dort stand vorher an einer
  vierten, unabhaengigen Stelle ebenfalls eine erfundene Ursache («WARTET AUF GPU»), auch
  das ist behoben.
* Kein neuer Status: `status` bleibt bei `queued`, wie im Blatt gefordert — die Verzweigung
  haengt einzig an `grund`, nicht an einem neuen Statuswort.

---

## Eure drei Fragen (U9a-c)

**U9a — reicht `message` als Klartext, oder braucht ihr eine maschinenlesbare Ursache
daneben?** Gemessen: die heutige Oberflaeche liest `message` ausschliesslich als
Anzeigetext (keine `switch`/Fallunterscheidung nach Inhalt, `wartetAbholerLabel`/
`wartetAbholerText` behandeln jeden gesetzten String identisch). Klartext reicht damit fuer
das, was heute gebaut ist. Ob eine maschinenlesbare Ursache (`karte_belegt`/
`freigabe_fehlt`) kuenftig fuer eine eigene Iconografie oder Filterung nuetzlich waere, ist
eine Erweiterung, keine Voraussetzung — **das ist eine Praeferenzfrage, kein Befund**: fuegt
sie hinzu, wenn ihr selbst einen Anwendungsfall dafuer habt, wir bauen dann eine eigene
Fallunterscheidung nach.

**U9b — soll `message` auch bei `running`/`done` gefuellt werden?** Gemessen: die
Anzeigefunktionen `wartetAbholerLabel`/`wartetAbholerText` werden ausschliesslich fuer den
Wartezustand (`wartetGpu`) aufgerufen; ein bei `running`/`done` gesetztes `message` haette
im heutigen Code **keine Anzeigestelle** — es wuerde still verworfen, kein Fehler, aber auch
kein Nutzen. Stoeren wuerde es nicht (kein Feld wird ueberschrieben, das etwas anderes
braucht), aber solange niemand es liest, ist Fuellen bei `running`/`done` fuer uns
wirkungslos. Antwort: aus heutiger UI-Sicht nicht noetig; wenn ihr es trotzdem sendet, ist
das folgenlos, keine Baupflicht auf unserer Seite.

**U9c — Laengengrenze, ab der die Zeile bricht?** Nicht als harte Zeichenzahl gemessen (kein
CSS-`max-width`/`-webkit-line-clamp` an der Fundstelle gefunden,
`grep -n "line-clamp\|max-width" apps/kosmo-orbit/src/modules/vis/vis-visual.css` liefert
keinen Treffer, der an `wartetAbholerText` haengt) — die Flaeche ist eine grosse
Platzhalter-Flaeche mit normalem Textumbruch, kein Mono-Kartenlabel wie die Kurzform. Das
Companion-Kartenlabel dagegen hat eine gemessene Grenze: die Kurzform bleibt bei 23 Zeichen,
weil sie sich mit dem Bestandswert seit v0.9.36 deckt (`vis-runtime.ts:205-213`) — dort
bricht also nichts Neues, weil bewusst keine neue Laenge eingefuehrt wurde. Fuer die grosse
Flaeche gilt: keine harte Grenze gemessen, aber auch kein Hinweis auf einen bekannten
Bruch-Fall.

---

## Was hier nicht gemessen wurde

* Keine Bildschirmmessung eines tatsaechlichen Zeilenbruchs bei sehr langem `message`-Text
  — nur der Code (kein `max-width`/Clamp) wurde geprueft, nicht das gerenderte Ergebnis.
* Ob euer Server `message` inzwischen auch bei `running`/`done` fuellt — nicht Teil dieses
  Auftrags, hier nur die UI-Seite geprueft.

**Zeile:** erledigt
