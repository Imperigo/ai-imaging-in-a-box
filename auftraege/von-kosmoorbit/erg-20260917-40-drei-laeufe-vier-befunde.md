# erg-20260917-40 — `auf-20260824-40` (an: ui): F1 bis F4, alle vier an der echten Oberflaeche nachgemessen

**Stand 17.09.2026:** erledigt — woran gemessen: alle vier Befunde (F1, F2, F3, F4a/b/c/d)
sind im heutigen Quelltext von `apps/kosmo-orbit/src` behoben, mit Datum/Kommentar an der
Fundstelle selbst, nicht nur behauptet. F5 ist laut dem Blatt selbst nicht an uns gerichtet
(an `cloud` unter `auf-20260827-64`) und wird hier bewusst nicht beantwortet.

Arbeitsstand: `kosmo-orbit` HEAD `407b0cc3` (2026-09-17 02:55 +0200), Uhr dieser Maschine
`2026-09-17T07:16Z`. Reine Lesemessung — nichts am Auftragsblatt, am Code oder an
ROADMAP/CLAUDE.md geaendert.

Ein Vorlauf war vorhanden und wurde als Ausgangspunkt genutzt, nicht als Quelle
uebernommen: `kosmo-orbit/docs/INVENTAR-KOSMOVIS-UI.md` (Stand 03.09.2026) fuehrt dieselben
vier Punkte bereits als erledigt. Jede Zeile unten ist an der heutigen (17.09.) Fassung des
Codes selbst nachgefahren, mit eigenem Befehl.

---

## F1 · Raeumt «Zur Zentrale» ab, oder legt es die Startseite darueber?

**Es raeumt ab — kein Overlay, kein vergessenes Abraeumen.** Ursache der beobachteten
Taubheit war `document.startViewTransition`, nicht das Abraeumen selbst.

Befehl und Beleg:
```
grep -n "uebergaengeAktiv\|startViewTransition\|gehZu" apps/kosmo-orbit/src/App.tsx
```
`gehZu()` (`App.tsx:325-332`) ruft bei jedem Stationswechsel `setScreen(s)` — ein reiner
React-Zustandswechsel, keine zweite Ebene bleibt liegen. Die Blende laeuft nur, wenn
`uebergaengeAktiv()` wahr ist; seit dem Fund (B62-Nachtrag, im Kopfkommentar von
`apps/kosmo-orbit/src/shell/sicherer-modus.ts` dokumentiert und mit einer Retro-Leiter A/B
belegt: `kosmo.sicher.uebergaenge=0` → 10/10 Laeufe mit echter Maus erfolgreich, `=1` → 0/10,
exakt der im Blatt beschriebene Befund) liefert `uebergaengeAktiv()` ohne gespeicherten Wert
auf **beiden** Plattformen `false` (`sicherer-modus.ts`, Funktion `uebergaengeAktiv()`).
`gehZu()` laeuft damit im Regelfall den synchronen Pfad, nie `document.startViewTransition` —
die Ursache der Taubheit tritt strukturell nicht mehr ein. Ein Owner, der Uebergaenge
ausdruecklich einschaltet, bekaeme das Risiko wieder — das ist eine bewusste Ruecknahme
durch den Nutzer, kein stiller Rueckfall.

## F2 · Kommt das Beispielprojekt in der Vis-Station an?

**Ja, auf zwei Wegen, beide gebaut.**

Befehl und Beleg:
```
grep -n "versucheAktivesProjektNachzuladen\|data-vis-aktives-projekt" apps/kosmo-orbit/src/App.tsx apps/kosmo-orbit/src/state/project-vault.ts
grep -rn "Beispielprojekt laden\|Beispielprojekt Demohaus" apps/kosmo-orbit/src/App.tsx apps/kosmo-orbit/src/modules/vis/vis-jobs.ts
```
1. **Uebernahme des aktiven Projekts:** `gehZu()` stoesst bei `s === 'vis'`
   `versucheAktivesProjektNachzuladen()` an (`App.tsx:326`, `state/project-vault.ts:443`) —
   Owner-Entscheid vom 03.09.2026, referenziert wortwoertlich `auf-20260824-40` F2 im
   Kopfkommentar von `App.tsx:311-324`. Findet sich nichts (kein Tresor-Eintrag oder 0
   Entities), passiert nichts — kein erfundenes Projekt. Ob Geometrie da ist, zeigt der
   `data-vis-aktives-projekt`-Marker an der Vis-Stationshuelle (`App.tsx:1637`).
2. **«Beispielprojekt Demohaus laden» ist app-weit per Befehlspalette erreichbar**
   (`App.tsx:875-883`, Kommando-Id `demohaus`), nicht mehr nur auf der Startseite — die
   Palette (`Kurzbefehle.tsx`) ist immer gemountet, unabhaengig von der Station.
3. Die Leerlauf-Wache selbst ist ebenfalls gebaut: `KEINE_GEOMETRIE_HINWEIS`
   (`apps/kosmo-orbit/src/modules/vis/vis-jobs.ts:326-333`) benennt Ursache und Weg
   («Befehlspalette (⌘K/Ctrl+K) → «Beispielprojekt Demohaus laden»») statt eine leere
   Huellbox durchzureichen, und sperrt den Render-Knopf
   (`szeneBauteileAnzahl(doc) === 0`, `NodeCanvas.tsx:2462/2508`) — genau der Schutz vor
   der «Unsinn mit Dezimalpunkt»-Folge, die das Blatt beschreibt.

## F3 · Geht die zweite Kante in Folge verloren?

**War ein echter Fehler, ist behoben und mit einem eigenen Test abgesichert.**

Befehl und Beleg:
```
grep -n "vis-node-port-hit\|onPointerCancel\|P-ZWEITKANTE" apps/kosmo-orbit/src/modules/vis/NodeCanvas.tsx
ls apps/kosmo-orbit/test/ | grep -i zweitkante
```
Ursache war `setPointerCapture` am Quell-Port: das `pointerup` landete dann dort und
erreichte den Zielport nie (Kommentar bei `NodeCanvas.tsx:1729-1741`, «P-ZWEITKANTE Posten 5,
28.08.2026»). Der Riegel gegen `setPointerCapture` bleibt ausdruecklich bestehen; die
verlorene Kante wird stattdessen im `onPointerCancel` des SVG-Canvas geheilt (Rettung ueber
die letzte Zeigerposition, `NodeCanvas.tsx:1386`). Zwei eigene Tests fahren genau diesen
Fall: `apps/kosmo-orbit/test/p-zweitkante-zwei-kanten-ein-durchgang.test.tsx` (zwei Kanten in
einem Durchgang, wie im Blatt beschrieben — Zug unmittelbar nach einem anderen Zug) und
`apps/kosmo-orbit/test/p-knotenfeld-zweitkante-meldung.test.tsx`.

## F4 · Die drei Kleineren plus der leere Graph

**a) Knoten stapeln sich** — behoben. `nodeHinzufuegen()`
(`apps/kosmo-orbit/src/modules/vis/vis-graph-aktionen.ts:200-284`) sucht per Spiral-Suche
(`findeSpiralPlatz`, Zeile 243-260) einen ueberlappungsfreien Platz, ausgehend vom
Sicht-Mittelpunkt der Leinwand, mit Randklemme. Kommentar an derselben Stelle nennt
sogar den Grund einer frueheren Teilreparatur («P-KNOTENPLATZ-KLEMME», 27.08.2026, an acht
gleichartigen Knoten gemessen: «Node 4 und 6 ueberlappen»). Befehl:
`grep -n "findeSpiralPlatz\|passtHier" apps/kosmo-orbit/src/modules/vis/vis-graph-aktionen.ts`.

**b) «Kamera vorschlagen» ohne Abbruch/Escape** — im heutigen Code nicht mehr reproduzierbar.
`kameraVorschlagenAktion()` (`vis-graph-aktionen.ts:136-193`) ist eine synchrone,
sofort abgeschlossene Aktion innerhalb EINER Undo-Gruppe (`history.beginGroup()` /
`endGroup()`) — es gibt keinen anhaltenden Modus mehr, den man mit Escape verlassen
muesste. Die im Blatt zitierte Textzeile «KAMERA VORSCHLAGEN AKTIV» existiert nirgends mehr
im Baum (`grep -rni "vorschlagen aktiv" apps/kosmo-orbit/src` → 0 Treffer, Gegenprobe: derselbe
Befehl findet `verdict.reason`-Zeilen anderswo problemlos, der Suchweg funktioniert). Statt
eines Modus meldet die Aktion sofort per Toast («Kein Kamera-Node im Graph — einer wurde
gesetzt und angeschlossen (1 Undo-Schritt).», Zeile 181-183) und ist mit einem Griff
rueckgaengig zu machen.

**c) Inseln erst nach Hover treffbar** — im heutigen Code nicht reproduzierbar. Die
geschlossene Insel-Pille ist ein natives `<button onClick={oeffneLeiste}>`
(`apps/kosmo-orbit/src/modules/design/island/IslandShell.tsx:1272-1279`, von den
Vis-Inseln mitgenutzt, `modules/vis/island/index.ts`), ohne `pointer-events:none` im
geschlossenen Zustand (`grep -n "\.isl-pill" apps/kosmo-orbit/src/modules/design/island/island.css`
zeigt nur `:hover`/`:focus-visible`-Regeln, keine Sperre am Grundzustand). Ein Klick ohne
vorheriges Hover loest den Handler strukturell direkt aus; ein Hover-Zwang besteht nicht.
Mit dem Zusatz aus dem Kopfkommentar von `IslandShell.tsx:1040`: «Hover/Tap oeffnet die
Leiste (§4.1 Stufe 1)» — das ist die dokumentierte erste Ebene (Pille → Leiste → Werkzeug),
kein Fehlzustand.

**d) «+ Graph erstellen» liefert einen leeren statt des vorverdrahteten Graphen** — war ein
Missverstaendnis, nicht ein Rueckfall, bereits im eigenen ROADMAP aufgeklaert
(`ROADMAP.md:3630-3632`, Eintrag 1095, «P-GRAPHSTART»): `vis.graphErstellen`
(`packages/kosmo-kernel/src/commands/vis.ts:28-38`) legt seit dem **allerersten**
KosmoVis-Commit (`62da55300`) einen leeren Graphen an — im Fenster zwischen den beiden im
Blatt genannten Terminen (v0.9.41 → v0.9.47, 92 Commits) hat keiner der drei zustaendigen
Dateien angefasst. Befehl:
`git log --oneline --all -- packages/kosmo-kernel/src/commands/vis.ts`. Ein vorverdrahteter
Graph existierte separat nie unter diesem Knopf — «Drei Stimmungen»
(`dreiStimmungenEinfuegen()`, `vis-graph-aktionen.ts:76-127`) ist der Knopf, der eine fertige
Kette liefert, und ist unveraendert ein eigener, zweiter Knopf.

---

## Was hier nicht gemessen wurde

* **F5** — bewusst nicht beantwortet; das Blatt selbst weist sie an `cloud`/`auf-20260827-64`.
* **Bildschirm-/Browser-Nachmessung.** Alle vier Befunde sind am Quelltext und an
  bestehenden Unit-/Komponententests belegt, nicht an einem laufenden Build. Kein
  Playwright, kein `npm run build` — Auflage dieses Durchgangs.
* Ob F4b/F4c je in genau der beschriebenen Form existiert haben, laesst sich rueckwirkend
  nicht mehr pruefen (kein Fund im heutigen Baum ist kein Beweis fuer «nie passiert») — nur,
  dass sie **heute** nicht reproduzierbar sind.

**Zeile:** erledigt
