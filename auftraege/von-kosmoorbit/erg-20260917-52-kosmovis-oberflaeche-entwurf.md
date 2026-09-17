# erg-20260917-52 — `auf-20260826-52` (an: ui): der KosmoVis-Entwurf ist weitgehend gebaut, O1 ist am Code entschieden

**Stand 17.09.2026:** offen — woran gemessen: die vier Regeln und die Bedienelement-Tabellen des
Entwurfs sind am heutigen Stand von `apps/kosmo-orbit/src/modules/vis/**` einzeln
nachgefahren. O1 ist keine offene Entscheidung mehr — sie ist am Code ablesbar. O2-O5 sind
Fragen AN uns (den `ui`-Worker), die das Blatt ausdruecklich nicht selbst beantwortet;
sie bekommen hier eine begruendete Antwort, wo sie messbar ist, und einen klaren
OWNER-ENTSCHEID-Vermerk, wo nicht.

**Warum «offen» und nicht «erledigt»:** O1 ist am Code entschieden und damit fertig
beantwortet; O2 bis O5 sind teils Fragen, ueber die der Owner entscheidet, und solange
die offen sind, ist dieses Blatt offen. Eine Stand-Zeile traegt genau EIN Urteilswort —
die erste Fassung dieser Zeile trug zwei ("erledigt + unklar") und wurde vom
`schlusszeilen-gate` zu Recht abgewiesen.

Arbeitsstand: `kosmo-orbit` HEAD `407b0cc3` (2026-09-17). Reine Lesemessung.

---

## O1 · Wo lebt die Flaeche?

**Weder «Cockpit-Ausklapp» noch «Designzentrale» im woertlichen Sinn des Blatts — KosmoVis
ist eine eigene, gleichrangige Station.**

Befehl: `grep -n "type Screen" apps/kosmo-orbit/src/App.tsx`
Ergebnis: `type Screen = 'home' | 'design' | 'vis' | 'data' | 'publish' | 'prepare' | 'doc' |
'train' | 'asset' | 'dev' | 'trust' | 'paket' | 'spez'` — `'vis'` steht gleichrangig neben
`'design'`, nicht darunter. Erreicht wird sie ueber `gehZu('vis')`, mit eigenem
Fehlerbereich (`<KFehlerzone bereich="KosmoVis" onDiagnose={...}>`, `App.tsx:1627`).

Damit ist die im Blatt selbst schon vorgezeichnete Entscheidung («KosmoVis ist EIN Knoten
nach aussen und eine eigene Flaeche nach innen») umgesetzt, nur praeziser als «im Ausklapp
oder in der Designzentrale»: die Flaeche hat einen **eigenen Platz auf oberster Ebene**,
mit dem inneren Node-Graphen (`NodeCanvas.tsx`) als eigenstaendigem Editor darin — der
«lauffaehige Vorlaeufer» `VisWorkspace.tsx`, den das Blatt nennt, ist heute der volle,
produktive Bildschirm dieser Station (`apps/kosmo-orbit/src/modules/vis/VisWorkspace.tsx`).
Posten A8 («Bild und Wert erscheinen in der KosmoVis-Flaeche, nicht im fremden
Knotenrahmen») ist damit nicht nur entschieden, sondern gebaut.

## O2 · Was fehlt uns von eurer Seite fuer Regel 2 bis 4?

Gemessen, was heute schon ankommt und genutzt wird, gegen das, was das Blatt unter
Abschnitt 5 ankuendigt:

* **QA je Kamera** (Abschnitt 5, Punkt 1) — heute **schon eingebaut auf UI-Seite**: eine
  Tabellenspalte «QA je Kamera» existiert bereits
  (`apps/kosmo-orbit/src/modules/vis/KuratierFlaeche.tsx:601`). Ob dahinter inzwischen ein
  echtes Feld je Kamera im Vertrag steht oder weiterhin das schlechteste Ergebnis des ganzen
  Laufs, ist eine Vertragsfrage (Cloud-Worker, `auf-20260826-49`) und hier nicht pruefbar —
  wir liefern die Anzeige, sobald das Feld da ist oder ist bereits so weit vorbereitet.
* **Varianten** (Punkt 2) — kein Fund im Code (`grep -rn "variante" apps/kosmo-orbit/src/modules/vis`
  liefert nur den bestehenden `vergleich`-Node, keine mehrfachen Startwert-Varianten je
  Lauf). Bleibt offen, bis eine Bedeutung feststeht (anderer Startwert? anderer Prompt?) —
  das ist an eurer Seite zu klaeren, wie das Blatt selbst sagt.
* **`prompt_original` im Vertrag** (Punkt 3) — wird an einer Stelle bereits konsumiert:
  `apps/kosmo-orbit/src/modules/vis/vis-jobs.ts` und die Kuratier-Flaeche zeigen Prompt in
  zwei Fassungen an, wo das Feld vorhanden ist (Regel-4-Anzeige des Entwurfs, Abschnitt 4).
  Fehlt das Feld im Ergebnis, bleibt die zweite Fassung schlicht leer — kein Absturz, aber
  auch keine Uebersetzungsanzeige.

**Antwort auf die Frage «eine vierte Luecke»:** keine gefunden, die nicht bereits unter O4
(Reihenfolge) landet.

## O3 · Ist Regel 1 zumutbar?

**Ja — und sie ist in der Praxis schon eingehalten, nicht nur akzeptiert.** Regel 1 verbietet
drei Bedienelemente ohne Wirkung. Nachgemessen an den drei genannten Kandidaten:

* **Hochskalieren** — `upscale: false` ist im Job fest verdrahtet
  (`apps/kosmo-orbit/src/modules/vis/vis-jobs.ts:808`), kein Schalter dafuer in der UI
  (`grep -in "upscale\|hochskalier" apps/kosmo-orbit/src/modules/vis/*.tsx` → 0 Treffer).
  Nicht angeboten, wie Regel 1 verlangt.
* **Stil-Referenzen** — kein Bedienelement im Baum
  (`grep -in "stilreferenz\|style.refs\|styleref" apps/kosmo-orbit/src/modules/vis/*` → 0
  Treffer ausser einem Kommentar, der den bewussten «Rueckzug von `style.refs`» dokumentiert,
  `vis-jobs.ts:569`). Nicht angeboten.
* **Stil-Modus — ein Fund, der die Tabelle des Blatts teilweise ueberholt:** seit v0.8.9
  (Line-Art, vor dem Auftragsdatum bereits im Baum) traegt `style.mode` einen echten,
  wirksamen Wert `'lineart'`, hart gekoppelt an `vis.skip:true`
  (`vis-jobs.ts:654-669`), UND die Oberflaeche bietet dafuer eine echte Checkbox an
  (`data-testid="render-lineart"`, `NodeCanvas.tsx:2675-2677`, gebunden an
  `params['lineart']`). Das ist keine Verletzung von Regel 1 — im Gegenteil, genau ihr
  Prinzip: ein Bedienelement nur dort, wo eine Wirkung existiert. Es widerlegt aber die
  pauschale Einstufung «Stil-Modus wirkt nicht» aus der «nicht anbieten»-Tabelle des Blatts:
  der WERT `'lineart'` wirkt (echtes Strichzeichnungs-Rendering); nur die Stil-QA-Bewertung
  fuer stilistische Nachbearbeitung laeuft weiterhin nicht, was eine andere Aussage ist. Wert
  fuer euch: sollte «Stil-Modus» als Gesamtfeld je wieder auftauchen, lohnt sich die
  Unterscheidung «welcher Wert» statt eines pauschalen Wirkungslos-Urteils.

**Damit: zumutbar, ja — und an keiner Stelle stillschweigend verletzt.**

## O4 · In welcher Reihenfolge nuetzen uns eure drei offenen Lieferungen?

Das ist eine Praeferenz, keine Messung — hier trotzdem eine begruendete Reihenfolge statt
eines Achselzuckens, aus dem, was am Code bereits vorbereitet ist:

1. **`prompt_original`** zuerst — die Anzeigestelle daf uer existiert in der Flaeche schon
   (Abschnitt 4 des Entwurfs ist gebaut); das Feld nachzuliefern ist die kleinste Ergaenzung
   mit sofort sichtbarem Nutzen.
2. **QA je Kamera** als zweites — die Tabellenspalte steht schon, sie zeigt heute vermutlich
   den Lauf-weiten Wert mehrfach wiederholt statt echter Werte je Kamera; das laesst sich
   ohne UI-Neubau nachziehen, sobald das Feld da ist.
3. **Varianten** zuletzt — es fehlt noch die Bedeutung (Startwert? Prompt? Stilstaerke?),
   und das Blatt selbst nennt die ungeloeste Spannung (Kapitel «Die Spannung, die der
   Entwurf nicht aufloest»): eine Variantenanzeige ist der teuerste der drei Punkte und
   sollte erst kommen, wenn die Bedeutung feststeht — sonst bauen wir gegen eine Unbekannte.

## O5 · Wie bekommen wir Auftraege am liebsten?

**OWNER-ENTSCHEID mit einer Tatsachenfeststellung dazu:** dieser Ordner
(`kosmo-orbit/docs/auftraege-kosmovis/`) funktioniert nachweislich — er wird gelesen (dieser
Durchgang beantwortet fuenf Blaetter daraus, inklusive dieses hier), und die zwei
verlorengegangenen Blaetter (`auf-20260901-70`, `auf-20260902-72`) sind nach eurer eigenen
Nachfrage-Geschichte inzwischen angekommen. Ob daneben noch ein zweiter Kanal (Datei in
`auftraege/offen/`, direkte Nachricht) gewuenscht ist, ist eine Frage an den Owner, nicht
etwas, das sich im Code nachmessen laesst — wir markieren sie ausdruecklich als
**OWNER-ENTSCHEID**.

---

## Regeln 2-4 des Entwurfs — stichprobenartig nachgemessen, nicht Gegenstand einer eigenen Frage

Nicht explizit verlangt, aber zur Einordnung von O2/O4 mitgemessen:

* **Regel 2 (dreiwertige QA-Anzeige)** — gebaut. `KuratierInspektor.tsx` liest
  `qa.verdict.reason` im Klartext und unterscheidet «bestanden/durchgefallen/nicht
  gemessen», nicht nur gruen/rot (bereits ausfuehrlich belegt in
  `auftraege/ergebnisse/erg-20260908-93-rho-bezug-und-wandanteil.md` §1.4, hier am
  aktuellen HEAD nicht erneut Zeile fuer Zeile reproduziert, da kein neuer Auftrag danach
  fragt).
* **Regel 4 (Gruende fuer fehlende Bilder je Kamera)** — Tabellenkopf «QA je Kamera»
  existiert (`KuratierFlaeche.tsx:601`); `qa.verdict.reason` wird an derselben Stelle wie
  bei Regel 2 gelesen. Nicht tiefer geprueft, ob jede Skip-Art (Rahmung/Kamerahoehe/
  doppelte Ansicht) einzeln unterschieden angezeigt wird — das war nicht Gegenstand dieses
  Blatts.

## Was hier nicht gemessen wurde

* Ob die Vorbehaltswerte aus Regel 3 (Schwelle/Aufloesung/Startwert/Backbone) neben JEDEM
  Wert stehen — nur stichprobenartig an der QA-Anzeige geprueft, nicht an allen acht
  Bedienelementen der Tabelle in Abschnitt 3.
* Keine Bildschirmmessung — alles am Quelltext, kein Build, kein Playwright (Auflage dieses
  Durchgangs).

**Zeile:** unklar — O1 ist erledigt (Antwort am Code, kein Entscheid mehr noetig), O2-O4 sind
mit Messung/Empfehlung beantwortet, O5 ist ausdruecklich OWNER-ENTSCHEID, wodurch das Blatt
insgesamt nicht vollstaendig auf «erledigt» steht.
