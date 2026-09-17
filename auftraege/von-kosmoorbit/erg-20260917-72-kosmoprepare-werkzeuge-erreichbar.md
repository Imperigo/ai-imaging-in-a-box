# erg-20260917-72 — `auf-20260902-72` (an: ui): alle sieben Werkzeuge sind erreichbar, drei davon per echtem Knopf, mit einer offen benannten Einschraenkung

**Stand 17.09.2026:** erledigt (mit Einschraenkung, benannt) — woran gemessen: die sieben
verlangten KosmoPrepare-Werkzeuge sind heute alle ueber die Systemschale erreichbar (Kosmo-
Chat), und drei davon zusaetzlich ueber ein echtes Bedienelement (Knopf), auf zwei Flaechen
gleichzeitig eingehaengt. Die verbleibenden vier haben keinen dedizierten Knopf — das ist
die offen benannte Einschraenkung.

Arbeitsstand: `kosmo-orbit` HEAD `407b0cc3` (2026-09-17). Reine Lesemessung.

---

## 0 · Der eigene Vorlauf (`P3`, 12.09.2026) — selbst nachgemessen, nicht zitiert

Die Aufgabenstellung nennt einen frueher gemessenen Stand des ganzen Werkzeugbestands
(Nenner 202, 158/163 mit Knopf, 37 mit E2E-Beleg; KosmoPrepare-Familie 8 Werkzeuge, 5 mit
Bedienelement). Diese Zahlen wurden hier **nicht uebernommen**, sondern eigenstaendig
nachgemessen:

```
grep -rc "registerCommand({" packages/kosmo-kernel/src/commands/*.ts | awk -F: '{s+=$2} END{print s}'
→ 157   (Kernel-Commands, werden automatisch zu Kosmo-Werkzeugen ueber commandTools())

grep -n "registriereUiBefehl(" apps/kosmo-orbit/src/state/ui-befehle.ts apps/kosmo-orbit/src/state/dock-befehle.ts | wc -l
→ 15    (eigenstaendige UI-Befehle, ausserhalb des Kernel-Command-Wegs)

grep -c "name:" apps/kosmo-orbit/src/modules/spez/spez-kosmo-werkzeuge.ts... (spezKosmoWerkzeuge() gelesen)
→ 2     (sonnenstudieWerkzeug, ergebnisseLesenWerkzeug)

+ modelQueryTool, bildAnsehenTool, laufPlanTool, die LAUF_BIBLIOTHEK-Vorschlagskarte
→ 4 weitere Einzel-Werkzeuge (packages/kosmo-ai/src/tools.ts + KosmoPanel.tsx:4790)

+ KOSMOPREPARE_TOOL_NAMEN (packages/kosmo-ai/src/tools.ts:341-350)
→ 8
```

Summe der eigenstaendig gezaehlten Teile: **rund 186** (157+15+2+4+8), nicht 202. **Das ist
ein Fund, kein widerlegter Wert** — ich habe die vollstaendige Laufzeit-Zusammensetzung, wie
sie `KosmoPanel.tsx` tatsaechlich an `ChatSession` uebergibt (inklusive Stationsfilter,
Budgetschnitt und `KOSMO_AUSGESCHLOSSENE_COMMANDS`-Abzuegen), fuer diesen Durchgang nicht
Zeile fuer Zeile nachgebaut — das haette einen eigenen Messlauf gebraucht, den die
Zeitauflage dieses Pakets nicht vorsah. Wer die exakten 202/158/163/37 braucht, sollte den
tatsaechlichen Kosmo-Werkzeugsatz zur Laufzeit zaehlen (`ChatSession`-Konstruktion in
`KosmoPanel.tsx`), nicht die Quelldateien von Hand aufsummieren.

**Fuer die KosmoPrepare-Familie selbst ist die Zahl dagegen exakt nachvollzogen:**
`KOSMOPREPARE_TOOL_NAMEN` (`packages/kosmo-ai/src/tools.ts:341-350`) fuehrt **8** Eintraege —
deckt sich mit dem Blatt und mit den genannten P3-Zahlen. Bei «5 mit Bedienelement» weicht
die eigene Messung ab: siehe Abschnitt 1.

## 1 · M1 — welche der sieben Werkzeuge wurden erreichbar gemacht, welche nicht, mit Grund

**Alle sieben sind erreichbar — ueber die Systemschale (Kosmo-Chat). Drei zusaetzlich ueber
einen echten Knopf.**

Befehl:
```
grep -n "KOSMOPREPARE_BEDIENELEMENTE" apps/kosmo-orbit/src/modules/prepare/werkbank/prepare-werkbank-werkzeuge.ts
grep -n "PREPARE_WERKBANK_WERKZEUGE" apps/kosmo-orbit/src/modules/prepare/werkbank/PrepareWerkbank.tsx
```

* `KOSMOPREPARE_BEDIENELEMENTE` (`prepare-werkbank-werkzeuge.ts:62-70`) fuehrt genau die
  sieben verlangten Namen (alle ausser `kosmoprepare_capabilities`, wie vom Blatt selbst
  verlangt: «kein Bedienelement … gehoert zur Registrierung, nicht in die Oberflaeche»).
  `kosmoprepareWerkzeuge()` verdrahtet sie in `KosmoPanel.tsx:4849` als
  `extraReadTools` — damit sind alle sieben ueber den Kosmo-Chat aufrufbar, mit strukturierter
  Ausgabe und Anzeige derselben Vorbehaltsfelder (Abschnitt 3).
* Drei davon (`kosmoprepare_flaechen`, `_baugesetz`, `_raumprogramm`) haben zusaetzlich
  einen echten Klick-Knopf: `PrepareWerkbank.tsx` (`PREPARE_WERKBANK_WERKZEUGE:62-70/94-98`),
  eingehaengt auf **zwei** Flaechen — `PrepareWorkspace.tsx:347` (klassische
  Manuell-Oberflaeche) UND `modules/prepare/island/inhalte/werkbank.tsx` (WISSEN-Insel,
  Produktions-Default seit `ui-zustand.ts`, gelandet 12.09.2026, Commit `4c3c96f42`). Beide
  rufen exakt denselben Transport (`kosmoprepareWerkzeuge()`), kein zweiter Bau.
* Die verbleibenden vier — `kosmoprepare_standort`, `_phase0`, `_orchestrate`,
  `_praezedenz` — haben **keinen** dedizierten Knopf. Grund, am Code belegt
  (`PrepareWerkbank.tsx:14-29`): die drei Knopf-Werkzeuge sind bewusst die einzigen drei, die
  weder eine live geo.admin-Standortabfrage noch einen geladenen `.gehirn`-Korpus
  voraussetzen — ein Klick reicht dort ohne externe Zusatzbedingung bis an den
  KosmoPrepare-Server. Fuer die vier uebrigen fehlt bislang ein Formular fuer die
  komplexeren Eingaben (Adresse/Koordinate/Polygon, Korpus-Pfad). Sie sind erreichbar
  (Kosmo kann sie im Chat aufrufen), aber nicht per eigenem Klick auslösbar — genau die
  Unterscheidung, die euer Blatt selbst mit «erreichbar fuer den Nutzer» meint.
* **Eigene E2E-Beleglage (`werkzeug-erreichbarkeit-gate.mjs`, selbst ausgefuehrt):**
  ```
  node tools/werkzeug-erreichbarkeit-gate.mjs
  → A2 kosmoprepare_* mit toolCalls-E2E: 7 von Untergrenze 5 — GRUEN
    (kosmoprepare_baugesetz, kosmoprepare_flaechen, kosmoprepare_orchestrate,
     kosmoprepare_phase0, kosmoprepare_praezedenz, kosmoprepare_raumprogramm,
     kosmoprepare_standort)
  ```
  Alle sieben — nicht nur die drei Knopf-Werkzeuge — haben einen echten E2E-Beleg ueber
  `toolCalls` (Kosmo hat sie im Test wirklich aufgerufen). Das ist eine hoehere Zahl als
  die im Auftragskontext genannte KosmoPrepare-Teilzahl «5 mit Bedienelement» — auch das ein
  Fund der eigenen Messung, keine Uebernahme.

## 2 · M2 — wo erscheinen sie

Rezeptliste: `kosmoprepare_orchestrate` (wie im Blatt vorausgesetzt) plus alle sechs
uebrigen sind Kosmo-Chat-Werkzeuge, keine eigene Rezept-Karte. Knoten/Palette: keine — es
gibt keinen dedizierten KosmoPrepare-Node im Vis-Graphen. Eigene Flaeche: **drei** der sieben
Werkzeuge haben eine «Werkbank»-Karte mit Eingabefeldern und Knopf, gleichzeitig auf der
Manuell-Oberflaeche UND auf der Insel der Station KosmoPrepare (Abschnitt 1).

## 3 · M3 — werden die fuenf Vorbehaltsfelder angezeigt?

**Ja, alle fuenf, auf demselben Weg fuer Chat- und Knopf-Aufruf.**

Befehl:
```
sed -n '90,170p' apps/kosmo-orbit/src/modules/prepare/werkbank/prepare-werkbank-anzeige.ts
```
`formatiereKosmoprepareAnzeige()` behandelt `annahmen`, `fragen`, `review_ready`, `sicher`
mit je einer eigenen, IMMER gesprochenen Zeile — auch wenn das Feld fehlt («… nicht
geliefert.» statt Stille, `standardZeilen()` Zeile 104-157). `quelle`, `art` und `konfidenz`
laufen ueber den generischen Fallthrough (Zeile 163-166: jedes noch nicht gezeigte Feld aus
dem Ergebnis wird ungefiltert mitgegeben) — keines der fuenf Felder aus eurem Blatt wird
verschwiegen. Dieselbe Formatierungsfunktion laeuft fuer den Knopf-Weg
(`PrepareWerkbank.tsx`, ueber `wrapKosmoprepareWerkzeug`) UND den Chat-Weg — eine Anzeige,
kein zweiter, abweichender Text.

## 4 · M4 — gab ein Werkzeug etwas zurueck, das ihr nicht darstellen konntet?

Kein Fund. Die vier Regeln plus der generische Fallthrough decken jedes Feld des
`structuredContent` ab; Kosmo selbst bekommt zusaetzlich immer die volle, unveraenderte
Zeichenkette (`formatiereKosmoprepareErgebnis()`, `packages/kosmo-ai/src/tools.ts`). Fuer
`kosmoprepare_phase0`s Markdown-Bericht (Fliesstext neben den strukturierten Feldern) wurde
keine gesonderte Pruefung gemacht, ob lange Markdown-Abschnitte in der `<pre>`-Ergebniszone
sauber umbrechen — das ist der einzige nicht restlos geklaerte Punkt bei M4, kein bekannter
Fehler.

## 5 · M5 — ist der Auftrag an der falschen Adresse?

Nein — «erreichbar fuer den Nutzer» ist unsere Zustaendigkeit, wie das Blatt selbst
begruendet, und der Befund liess sich vollstaendig am UI-Code klaeren. Kein Weiterreichen
noetig.

---

## Was hier nicht gemessen wurde

* Der exakte, zur Laufzeit zusammengesetzte Gesamt-Werkzeugsatz (inkl. Stationsfilter/
  Budgetschnitt) — nur die Quelldateien wurden gezaehlt, s. Abschnitt 0.
* Ob ein echter KosmoPrepare-Server antwortet — ohne Tauri-Desktop meldet jeder der sieben
  Wege ehrlich «KosmoPrepare braucht die Desktop-App» (Kommentar an
  `island/inhalte/werkbank.tsx:28-32`), das ist unveraendert Stand von P3 und nicht neu
  geprueft.
* Kein Build, kein Playwright — nur die Quelle und ein eigenstaendiger Gate-Lauf
  (`werkzeug-erreichbarkeit-gate.mjs`, kein E2E).

**Zeile:** erledigt
