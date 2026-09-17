# erg-20260917-49 — `auf-20260826-49` (an: cloud): Produktweg, QA je Kamera, Varianten, KosmoPublish-Feldnamen

**Stand 17.09.2026:** offen — woran gemessen: V2 und V4 sind am Code beantwortbar und
beantwortet, V3 ist ein bereits getroffener Owner-Entscheid (NEIN, unveraendert seit
03.09.2026), aber **V1 (welcher Weg der Produktweg ist) ist weiterhin ein unentschiedener
Owner-Entscheid** — im Code oder in den Owner-Dokumenten dieses Repos findet sich dazu keine
Festlegung. V5 bleibt teilweise ungeklaert, weil das referenzierte "Uebergabeblatt" mit den
Fragen 5/9/15/16 in diesem Repo nicht auffindbar ist.

Hinweis zur Vorgeschichte: eine erste Antwort liegt bereits vor
(`auftraege/ergebnisse/auf-20260826-49.json`, 03.09.2026, laut `docs/AUFTRAG-B118-...md`
seit 08./09.09.2026 in eurem Repo mit `status: ok`). Diese Datei hier misst denselben
Vertrag am heutigen Stand erneut nach — V2 hat sich seither veraendert (jetzt gebaut).

---

## V1 — Welcher Weg ist der Produktweg: Szenenvertrag oder Werkzeugnaht (MCP)?

**OWNER-ENTSCHEID — wir entscheiden das nicht, genau wie ihr verlangt habt.**

Was wir **wissen**, am Code:
- **Weg A (Szenenvertrag)**: `RenderScene`/`RenderResult` in `kosmo-contracts`, ausgeliefert
  ueber die Datei-Warteschlange der HomeStation-Bruecke
  (`tools/homestation-bridge/kosmo_bridge/main.py`, `POST /jobs`). Dieser Weg ist in diesem
  Repo vollstaendig vorhanden und wird von der App selbst genutzt
  (`apps/kosmo-orbit/src/modules/vis/vis-jobs.ts`, `postRenderJob`).
- **Weg B (Werkzeugnaht/MCP)**: in KosmoOrbit selbst gibt es EIN Kosmo-Kommando, das zu
  einem MCP-/Kosmo-Werkzeug wird — `vis.render` in
  `packages/kosmo-kernel/src/commands/vis.ts:250-293`. Ueber `commandTools()`
  (`packages/kosmo-ai/src/tools.ts:129`) wird jeder registrierte Command automatisch ein
  Werkzeug, das Kosmo (die Buero-KI) aufrufen kann. `vis.render` setzt aber nur einen
  Render-**Auftrag** ins Dokument (`VisRenderWunsch`); ausgefuehrt wird er ueber genau
  denselben `sendeGraphRenderAuftrag()` → `postRenderJob()` → `POST /jobs`-Weg wie Weg A.
  Es gibt also **in diesem Repo keine zwei getrennten Ausfuehrer** — nur einen, mit zwei
  Anstoss-Wegen (Button/UI, oder Kosmo-Tool-Aufruf).
- Ob das identisch mit **eurem** "Weg B" ist (eure `aiimaging_enqueue_render`/
  `aiimaging_query_render`), koennen wir nicht sagen: diese Namen kommen in diesem Repo
  nicht vor (`grep -rn "aiimaging" packages/kosmo-ai/src/tools.ts` → 0 Treffer). Vermutlich
  beschreibt euer Blatt eine andere, separate MCP-Naht (siehe unsere Antwort zu
  `auf-20260827-63`), nicht `vis.render`.

Was **entschieden werden muss**: ob KosmoOrbit fuer Renderauftraege an euch langfristig
(a) ausschliesslich den Datei-Weg (`kosmo-contracts`/`POST /jobs`), (b) ausschliesslich
einen reinen MCP-Weg, oder (c) beide parallel pflegt. Das ist eine Architektur-/
Pflegeaufwand-Frage, keine, die sich aus dem heutigen Code ablesen laesst — beide Wege
existieren und funktionieren, keiner ist im Code als "veraltet" markiert.

## V2 — QA je Kamera

**Antwort: Ja, gebaut — neu seit unserer letzten Antwort vom 03.09.2026 (damals "noch
nicht gebaut").** Feldname `qa_je_kamera`, additiv neben dem bestehenden `qa`-Block:

```
sed -n '366,393p' packages/kosmo-contracts/src/render-result.ts
```
```ts
qa_je_kamera: z
  .array(
    z.object({
      kamera: z.string(),
      geometry: GeometryQA.optional(),
      style: StyleQA.optional(),
    }),
  )
  .optional(),
```
`kamera` ist Pflichtfeld je Eintrag (ohne ihn waere ein durchgefallener Eintrag keinem
Blickwinkel zuzuordnen). `geometry`/`style` sind je Eintrag optional, wie im bestehenden
`qa`-Block auch. Der bestehende `qa`-Block bleibt **byte-identisch** unveraendert und traegt
weiterhin das schlechteste Urteil ueber alle Kameras — das neue Feld ist eine Ergaenzung,
kein Ersatz. **Kein Default**: ein Ergebnis ohne `qa_je_kamera` sagt nichts ueber einzelne
Kameras aus, der aggregierte `qa`-Block bleibt dann die einzige Auskunft.

Test:
```
grep -n "qa_je_kamera traegt je Kamera" packages/kosmo-contracts/test/contracts.test.ts
```
→ Zeile 1510 (`describe`-Block "V2 (auf-20260826-49, Owner-Entscheid 03.09.2026):
qa_je_kamera additiv neben qa" ab Zeile 1509).

## V3 — Varianten: bereits entschieden (NEIN)

**Antwort: Nein — Owner-Entscheid vom 03.09.2026, unveraendert.** Kein Variant-Feld gebaut,
`images` bleibt eine einfache Liste ohne Mehrfachbelegung eines Blickwinkels.

```
grep -n "variante\|Variante" packages/kosmo-contracts/src/render-scene.ts packages/kosmo-contracts/src/render-result.ts
```
→ 0 inhaltliche Treffer (nur unverwandte Textstellen wie das `'flux-krea'`-GGUF-"Variante").

Begruendung aus der bestehenden Antwort, am Code weiterhin zutreffend: Varianten je Kamera
verlangen zuerst eine Bedeutungs-Festlegung (was ist eine Variante, wie viele je Kamera,
wonach waehlt der Benutzer) — dafuer gibt es in der Oberflaeche heute keinen Ort, an dem ein
Benutzer zwischen Varianten waehlt, und jede Festlegung ohne diesen Ort waere geraten. Das
ist keine neue Pruefung, sondern die Bestaetigung, dass sich am Stand seit 03.09.2026 nichts
geaendert hat. **Solltet ihr diesen Vorbau bei euch fuer KosmoOrbit vorhalten: er wird nicht
gebraucht, bis sich das aendert.**

## V4 — Eingabefeldnamen des Knotens, der eure Bilder abnimmt (KosmoPublish)

**Antwort, unveraendert und frisch am Code bestaetigt:** Der Knoten heisst im Knotengraphen
`blatt` ("Aufs Blatt") und hat genau **ein** Eingabefeld: `bild` (Typ `bild`).

```
sed -n '132,146p;178,186p' packages/kosmo-kernel/src/derive/visgraph.ts
```
```ts
render: {
  ...
  outputs: [{ name: 'bild', typ: 'bild', label: 'Bild' }],
  ...
},
...
blatt: {
  typ: 'blatt',
  label: 'Aufs Blatt',
  hilfe: 'Legt das Bild als Blatt-Buerger in KosmoPublish ab (ein Undo-Schritt).',
  kategorie: 'ausgabe',
  inputs: [{ name: 'bild', typ: 'bild', label: 'Bild' }],
  outputs: [],
  defaults: { titel: 'Visualisierung' },
},
```
Die Kante entsteht ueber Feldnamen-Gleichheit `bild ↔ bild`, genau wie in eurem Blatt
beschrieben — der `render`-Knoten liefert exakt dieses eine Ausgabefeld.

## V5 — Fragen 5, 9 und 15/16 eines "Uebergabeblatts"

**Antwort: Wissen wir nicht — das referenzierte Dokument ist in diesem Repo nicht
auffindbar.**

```
grep -rli "uebergabeblatt" . --include="*.md" 2>/dev/null | grep -v node_modules
```
findet drei Treffer, keiner davon enthaelt nummerierte Fragen 5/9/15/16 im gefragten Sinn.
Eine gezielte Suche nach den Fragennummern selbst und nach `pruefe_kette` (Frage 5) in
`auftraege/von-homestation/` (21 Dateien) liefert ebenfalls 0 Treffer. Das ist keine
Vermutung, sondern eine vollstaendige, dokumentierte Nichtauffindbarkeit — dieselbe wie
in der Antwort vom 03.09.2026 bereits festgestellt, heute erneut geprueft.

Teilbefund zu **Frage 9** (aus dem Blatt-Text erschliessbar: "Nehmt ihr unseren Abholer? Er
bedient seit dem 26.08. beide Ablagen"): das ist eine **Betriebsfrage** (laeuft ein Prozess),
kein Vertragsthema — aus `kosmo-contracts` heraus nicht beantwortbar, dasselbe Muster wie die
Abholer-Frage aus `auf-20260822-31`.

**Rueckfrage an euch:** Wo genau liegt das "Uebergabeblatt" mit den Fragen 5/9/15/16 — in
eurem eigenen Repo, oder wurde der Name/Ort beim Uebertragen ungenau?

---

## Was ausdruecklich OWNER-ENTSCHEID ist (noch offen)

- **V1 — Produktweg.** Zwei funktionierende Wege existieren im Code, keiner ist markiert
  als bevorzugt. Kosten beider Wege dauerhaft parallel zu pflegen: nicht gemessen (ausserhalb
  dieses Dateikreises).

## Was ausdruecklich OWNER-ENTSCHEID war und bereits entschieden ist

- **V2** — `qa_je_kamera`, wie oben, gebaut seit 03.09.2026.
- **V3** — Varianten: NEIN, wie oben, entschieden 03.09.2026, unveraendert gueltig.

## Messdisziplin

Kein Testlauf, kein Build (Auflage der Sitzung, paralleles Paket im selben Baum). Alle
Aussagen aus Lesen + `grep`/`sed`. Wo ein Test zitiert wird, ist das ein Verweis auf
vorhandenen Testcode, keine Behauptung eines soeben gelaufenen gruenen Ergebnisses.
