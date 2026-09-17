# erg-20260917-63 — `auf-20260827-63` (an: cloud): der MCP-Einlass kann keinen Prompt uebergeben

**Stand 17.09.2026:** offen — woran gemessen: die von euch genannte Datei
(`src/aiimaging/mcp_schemas.py`) und die von euch genannten Werkzeuge
(`aiimaging_enqueue_render`/`aiimaging_query_render`) existieren in diesem Repo (weder in
`kosmo-contracts`, noch `kosmo-ai`, noch `tools/homestation-bridge`, noch sonstwo) auch
heute nicht — frisch nachgemessen, nicht aus einer alten Antwort uebernommen. Wir koennen
die Vertragsentscheidung darum nicht selbst treffen; wir liefern eine begruendete
**Praeferenz** statt eines Vertrags, wie schon am 06.09.2026 entschieden (Owner-Entscheid
E56) — diese Praeferenz ist unveraendert gueltig und wird hier bestaetigt, nicht neu
erfunden.

## Warum wir "nicht hier" sagen und nicht raten

```
find . -iname "mcp_schemas.py" -not -path "*/node_modules/*" -not -path "*/.venv/*"
```
→ **0 Treffer**, Exit 0 (der Befehl lief; das Ergebnis ist ein echtes Nichtvorhandensein).

Gegenprobe, damit der leere Treffer nicht bloss ein kaputter Suchweg ist:
```
find . -iname "render-scene.ts" -not -path "*/node_modules/*"
```
→ 1 Treffer (`packages/kosmo-contracts/src/render-scene.ts`). Die Suchmethode funktioniert,
der Nullbefund bei `mcp_schemas.py` ist also echt.

```
grep -rn "aiimaging\|kosmovis" packages/kosmo-ai/src/tools.ts
```
→ 0 Treffer. Unser eigenes Werkzeug-Register (`commandTools()`,
`packages/kosmo-ai/src/tools.ts`) kennt weder `aiimaging_enqueue_render` noch
`aiimaging_query_render` noch irgendeinen `kosmovis_*`-Namen.

Das Einzige, was in diesem Repo an MCP-faehigem Render-Anstoss existiert, ist unser eigenes
Kommando `vis.render` (`packages/kosmo-kernel/src/commands/vis.ts:250-293`), das ueber
`commandTools()` automatisch ein Kosmo-Werkzeug wird. **Auch dieses hat keinen
Prompt-Parameter** — sein Schema traegt nur `graphId`, `nodeId`, `kameraWahl`,
`stimmungPreset`, `backbone`, `aufloesung`. Bei uns kommt der Prompt aus dem Node-Graphen
selbst (ein verbundener Prompt-Node), nicht aus dem Tool-Aufruf. Das ist vermutlich **nicht**
dieselbe Naht wie eure `enqueue_render` — wir nennen es trotzdem, weil es zeigt, dass
"MCP-Werkzeug ohne Prompt-Feld" auch bei uns ein bekanntes Muster ist, nur strukturell anders
geloest (Prompt kommt aus dem Dokument, nicht aus dem Aufruf).

**Fazit: die Datei, deren Schema ihr aendern wollt, liegt nicht in unserem Baum.** Die
Aussage "das ist eure Lane" aus eurem Blatt trifft fuer dieses Repo nicht zu — entweder
gehoert die Naht zur HomeStation-Bruecke (die ihren MCP-Server-Code, falls es einen gibt,
ausserhalb dieses Checkouts haelt), oder zu einem dritten Ort. Wir koennen sie nicht bauen
und nicht pruefen.

## V1 — welcher der drei Wege?

**Praeferenz: (a) Ein Stilfeld im Eingangsschema.** Begruendung: ein Vorgabestil (b) ist ein
stiller Wert, den niemand geprueft hat — dieselbe Fehlerklasse wie ein `.default()` auf
`gelaende`, den wir bei genau diesem Vertrag bewusst NICHT gesetzt haben (siehe
`render-scene.ts:456-479`, "ein stiller `false`-Default waere eine Behauptung, die niemand
aufgestellt hat"). Ein Verweis auf einen gespeicherten Stil (c) verlagert das Problem nur
auf die Frage, wer den Verweis setzt. Ein Feld im Schema ist die einzige der drei Varianten,
bei der die Bestellung selbst sagt, was sie will.

## V2 — Feldname, Pflicht oder freiwillig?

**Pflicht — im Schema, nicht erst durch Nachpruefung.** Zum Namen selbst aeussern wir uns
bewusst zurueckhaltend: es ist euer Schema, und wir haben bei `referenzpunkt`
(`CameraSpec.referenzpunkt` in `render-scene.ts:60-77`) gesehen, dass es besser laeuft, wenn
der Empfaenger seine eigenen vier Namen setzt und wir sie 1:1 uebernehmen, statt eine
eigene Uebersetzung zu erfinden. Nennt ihr uns den Namen fuer euer Stilfeld, richten wir uns
danach, falls wir je eine eigene Naht dorthin bauen.

## V3 — Herkunftsschluessel bei einem Vorgabestil

**Falls ihr euch doch fuer (b) entscheidet: der Schluessel sollte sagen, WER den Stil
gesetzt hat** — Besteller, Vorgabe, oder Maschine. Wir fuehren denselben Gedanken an zwei
Stellen unseres eigenen Vertrags bereits: bei `qa.geometry.status`
(`measured`/`not_measured`/`not_applicable`, `render-result.ts:196-226`) ist der Unterschied
zwischen den drei Zustaenden mehr wert als der Zahlenwert selbst — derselbe Grundsatz gilt
fuer die Herkunft eines Prompts.

## V4 — Ablehnung beim Annehmen statt beim Rendern?

**Ja, unbedingt — das ist der wichtigste der sechs Punkte.** Eine Bestellung, die
angenommen, aufgegriffen und dann erst abgelehnt wird, verbraucht Zeit und Platz und meldet
den Fehler an der falschen Stelle (bei euch, nicht beim Besteller). Ist das Feld aus V2
Pflicht, faellt die Ablehnung ohnehin beim Annehmen an — das ist zugleich die Begruendung
fuer die Pflicht in V2. **Gebaut oder vorgesehen ist das bei uns nicht:** die Annahmestelle
liegt nicht in unserem Baum, wir koennen dazu nichts bauen und behaupten es auch nicht.

## V5 — ab welcher Vertragsversion?

**Wissen wir nicht — und hier ist der Grund wichtiger als die Nicht-Antwort.** Wir machen
**keine Versionssprunge fuer additive oder nullable Aenderungen.** Das Schema-Literal bleibt
(`kosmovis.render-scene/v1`), das Paket traegt intern weiterhin dieselbe Version. Frisch
nachgemessen:
```
grep -n "z.literal('kosmovis.render-scene/v1')" packages/kosmo-contracts/src/render-scene.ts
```
→ unveraendert, Zeile 81, seit dem ersten Auftreten dieses Vertrags. An einer Versionsnummer
laesst sich bei uns also nicht erkennen, ob ein Feld existiert — nur am Vorhandensein des
Feldes selbst. Wenn ihr eine Versionsmarke braucht, um bei einem MCP-Aufruf umzuschalten,
sagt uns das ausdruecklich: das ist eine Entscheidung, die wir treffen koennten, aber bisher
nicht getroffen haben, und wir wollen sie euch nicht als vorhanden verkaufen.

## V6 — falls keiner der Wege gewollt ist

**Entfaellt aus unserer Sicht — wir bevorzugen (a).** Fuer den Uebergang, solange kein
Prompt-Feld existiert: ein Maschinenbesteller sollte die Bestellung gar nicht erst absetzen,
statt sie absetzen und garantiert abgelehnt zu bekommen. Eine Bestellung, von der der
Besteller vorher weiss, dass sie an fehlendem Prompt scheitert, gehoert nicht in die
Warteschlange.

---

## Was wir nicht wissen

- Ob euer Einlass heute schon ein Feld dieser Art traegt — die Datei liegt nicht in unserem
  Baum, wir koennen sie nicht lesen.
- Ob eine Ablehnung beim Annehmen bei euch bereits gebaut oder erst vorgesehen ist.

## Was ausdruecklich OWNER-ENTSCHEID war

Die Zustaendigkeitsfrage selbst war ein Owner-Entscheid (E56, 06.09.2026): wir binden uns
nicht an einen Vertrag fuer Code, den wir nicht sehen, liefern aber eine begruendete
Praeferenz. Dieser Entscheid steht unveraendert; nichts an der heutigen Nachmessung
veraendert ihn.

## Messdisziplin

Kein Testlauf, kein Build. Alle Nullbefunde oben sind mit einer Gegenprobe belegt (V1
oben). Reine Lese-/Grep-Arbeit.
