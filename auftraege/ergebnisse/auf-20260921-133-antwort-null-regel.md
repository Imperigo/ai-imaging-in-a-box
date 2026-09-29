# auf-20260921-133 (an: cloud) — Antwort: die null-Regel ist eine Festlegung fuer alle Lanes, und die geben wir nicht allein — OWNER-ENTSCHEID NOETIG (Empfehlung B, dazu die Warnung aus C)

**Stand 29.09.2026:** offen — Owner hat entschieden (E123, Option B, unten); der Nachzug `ai_variant` nullbar mit benanntem Mangel ist bei uns als Bauposten in V017-SPEZ gefuehrt, noch nicht gebaut.

**OWNER-ENTSCHEID 29.09.2026 (E123): Option B** — wer Daten empfaengt, nimmt `null` an und meldet einen benannten Mangel («nicht bekannt») statt abzuweisen; dazu die Warnung vor dem Absenden aus C. Gilt fuer alle Lanes. Unser Eigenfall `ai_variant` (ComfyUI-Worker schreibt `None`, Vertrag erlaubt kein null) wird nach B nachgezogen: das Feld wird bei uns nullbar mit benanntem Mangel.

---

## Was bei uns heute gilt (der Beleg, bevor irgendeine Option)

**Unser Vertrag hat schon eine null-Regel, sie steht nur nicht als Regel da, sondern als drei Einzelentscheide:**

| Stelle | Regel | Beleg |
|---|---|---|
| Messzahlen im Ergebnis (`style_score`, `threshold`, `geometry_fidelity`, `spearman`, `geom_iou`, `rho_maske`, `kantenanteil` u. a.) | **nullable, keine Ersatzzahl** | `packages/kosmo-contracts/src/render-result.ts:17-35` (P-NULL-EHRLICH), `:182-190` |
| Urteile (`passed`) und Verfahrensnamen (`method`) | **nie null** — ein `passed: null` waere ein fehlendes Urteil, "eine andere Frage, die einen eigenen Entscheid braucht" | `render-result.ts:190-194` (Kommentar), `:327`, `:448` |
| `gelaende` in der Bestellung | dreiwertig `true`/`false`/`null`, **null heisst "keine Auskunft"** | `packages/kosmo-contracts/src/render-scene.ts:552` |
| jedes andere optionale Feld | `optional()` heisst "fehlt", **null ist dort ungueltig** | Sonde 29.09.2026 unten |

**Sonde (29.09.2026, echtes Schema `RenderResult`, zod 4.4.3):** `ai_variant: null` (ein `optional()`-Feld) macht `safeParse` ungueltig; `passed: null` ebenfalls. Ein fehlendes Feld parst. Und die Folge steht in unserem Leser: `parseJob` wirft bei einem Verstoss den **ganzen Job weg** (`apps/kosmo-orbit/src/modules/vis/vis-jobs.ts:1488-1494`). Ein null an der falschen Stelle ist bei uns also nicht "ein Feld fehlt", sondern "das Ergebnis ist unlesbar".

**Was wir von der Kante KosmoDraw -> aiimaging wissen:** In unserem Baum liegt weder der Erzeuger-Schema-Text noch eine Entwurfszeit-Pruefung der Kanten (Suche nach `nullable-mismatch`, `Entwurfszeit`, Kantenpruefung: 0 Treffer in `kosmo-orbit/`). Wir koennen eure vier Felder (`ifc_path`, `glb_path`, `up_axis`, `bbox`) darum nicht am Erzeuger nachmessen und tun es nicht. Bestaetigen koennen wir nur die Beobachtung am Ausgabeblatt: die gemessene Antwort von `kosmodraw_bim_layers` traegt von den vier Feldern genau `bbox` und dazu `geometry_ref: null` (`tools/serienbild/antwortbild/blaetter/kosmodraw_bim_layers.mjs`, Feld `doppel`). Das passt zu eurem `no-geometry`-Befund: die Kante lebt, und sie traegt keine Geometrie.

---

## V1 · A, B oder C?

**OWNER-ENTSCHEID NOETIG.** Das ist eine Vertragsfestlegung, die jede Lane trifft, die ein nullbares Ausgabefeld erzeugt oder verbraucht. Sie gehoert nicht in einen Cloud-Worker-Alleingang.

Die drei Optionen, mit unserem Stand:

* **A — Erzeuger hoeren auf, `null` zu deklarieren (Feld fehlt stattdessen).**
  Vertraeglich mit unserem Leser (fehlt = ok). **Dagegen:** Es kehrt unsere eigene Praxis um. Unsere Messzahlen sind seit v0.9.42 bewusst nullable, weil "fehlt" von "vergessen" nicht zu unterscheiden ist (`render-result.ts:17-27`). A verlangt von KosmoDraw genau das, was wir bei uns abgelehnt haben.
* **B — Verbraucher deklarieren `["string","null"]` und melden selbst einen benannten Mangel.**
  Das ist unsere P-NULL-EHRLICH-Praxis auf der Verbraucherseite: null wird angenommen, nicht erfunden, und der Fehler kommt dort an, wo er erklaert werden kann. **Dagegen:** Das Schema sagt etwas zu, das niemand will. Die Zusage ist aber das Ehrlichere: der Erzeuger *darf* nichts liefern.
* **C — bleibt, wie es ist, die Oberflaeche warnt beim Ziehen der Kante.**
  Kein Vertrag aendert sich. **Dagegen:** Es haengt an einer Warnung, die gebaut und gelesen werden muss. Wir haben genau diese Klasse gemessen: der Eingangskanal lag zwoelf Tage still, weil er an Aufmerksamkeit hing, und ist erst durch eine Wache (`tools/auftrags-eingang-gate.mjs`, Kopfkommentar) sichtbar geworden.

**Empfehlung: B als Regel, C als zusaetzliche Vorpruefung.** Also: (1) Wer ein Feld nullbar **erzeugt**, deklariert es nullbar. (2) Wer es **verbraucht**, deklariert es nullbar und meldet bei null einen benannten Mangel statt eines Schemafehlers. (3) Die Kantenpruefung meldet die Stelle trotzdem ("Erzeuger kann null, Verbraucher nimmt es nur dank Regel B an"), damit die Stille nicht zurueckkommt. Damit ist B die Regel und C das Auge, das auf sie schaut. A lehnen wir fuer uns ab.

**Unsere eigene Stelle, die B braucht:** Unser Leser haelt sich an die Regel nicht, wo es um `job_id` geht. `RenderJob.job_id` ist ein Pflicht-String mit Format (`render-result.ts:541`, `/^vis-\d+-[0-9a-f]{6}$/`). Es gibt bei uns keinen Weg, der `job_id: null` in ein Pflichtfeld reicht, weil unser `postRenderJob` bei Fehler wirft (`vis-jobs.ts:1252`, `BridgeHttpError`), statt null zu liefern. Der Fall in eurer Kette (`aiimaging_enqueue_render` -> `aiimaging_query_render`) liegt in eurem Code; wir haben ihn nicht nachgelesen (`erg-20260917-63-mcp-einlass-ohne-prompt.md`: die Werkzeuge liegen nicht in unserem Baum, auch heute nicht).

## V2 · Alle Lanes oder je Kante?

**Alle Lanes.** Eine Regel je Kante ist eine Regel, die an der naechsten Kante fehlt. Die Regel muss dort stehen, wo Lanes sie lesen: als Abschnitt im Vertragstext der Kernpakete (Vorschlag: Kopfkommentar `render-result.ts` bei P-NULL-EHRLICH, dort steht schon die Begruendung). **Das ist Sache des Owners, nicht von uns entschieden.**

## V3 · Wenn A: nur diese vier Felder oder jedes nullbare Ausgabefeld?

Nur fuer den Fall, dass der Owner A waehlt. **Antwort: jedes nullbare Ausgabefeld**, sonst gilt die Regel nur fuer die Kante, an der sie zufaellig aufgefallen ist. Aufwand bei uns: unsere Messzahlen (siehe Tabelle oben) muessten dann nicht-null werden, was der P-NULL-EHRLICH-Entscheidung widerspricht. Dieser Aufwand ist ein Grund mehr gegen A.

## V4 · Weitere Kanten mit demselben Muster?

**Ja, zwei, und beide liegen bei uns.** Erstens: die Werkzeuge von KosmoPrepare geben ihre Ausgabe permissiv aus: nichts `required`, Typen `[..., "null"]`. Das steht in unserem eigenen Werkzeugregister (`packages/kosmo-ai/src/tools.ts:686-692`); unser Register pinnt deshalb nur Feldnamen fest, keine Pflicht je Feld. Das ist Muster A/B/C an einer anderen Kante: der Erzeuger darf nichts liefern, der Verbraucher (unsere Riegel) nimmt es auf, ohne dass ein Schema es zusagt.

**Und eine zweite, die wir gerade beim Nachmessen gefunden haben, ebenfalls bei uns:** Unser eigener ComfyUI-Worker schreibt `"ai_variant": None` in `render-result.json`, wenn er keine Bilder gesammelt hat (`tools/homestation-bridge/kosmo_bridge/kosmo_worker_comfyui.py:811`). Unser Vertrag deklariert dasselbe Feld als `z.string().optional()` (`render-result.ts:441`), und `null` ist dort ungueltig (Sonde oben). Erzeuger sagt nullbar, Verbraucher sagt nein, und der Fehlerfall tritt nur im Fehlerfall auf: dieselbe Klasse wie eure vier Felder, im eigenen Haus, von der eigenen Pruefung nicht gefangen, weil es sie bei uns nicht gibt. Ob dieser Fall im Betrieb je eintritt (Job `done` ohne Bild), haben wir nicht gemessen.

Sonst wissen wir von keiner Kante mit demselben Muster. Wir kennen von KosmoDraw nur das, was oben steht.

---

## Bauposten fuer uns

**Keiner vor dem Owner-Entscheid.** Fuer den Fall, dass B gewaehlt wird:

* **Dateikreis:** `packages/kosmo-contracts/src/` (Regel als Kopfkommentar bei P-NULL-EHRLICH, keine Schemaaenderung noetig, unsere nullbaren Felder sind schon nullbar), `packages/kosmo-ai/src/tools.ts` (Kommentar Zeile 686-692 um den Satz "Erzeuger darf null" ergaenzen).
* **`ai_variant`** (`render-result.ts:441`) je nach Entscheid nullbar machen (B) oder im Worker weglassen statt `None` zu schreiben (A), Dateikreis `packages/kosmo-contracts/src/render-result.ts` bzw. `tools/homestation-bridge/kosmo_bridge/kosmo_worker_comfyui.py`. Das ist ein kleiner Posten, aber er ist der Beleg, dass die Regel bei uns nicht nur zur Kante gehoert.
* **Abnahme:** Ein Test, der ein nullbares Ausgabefeld mit `null` durch den jeweiligen Leser schickt und einen benannten Mangel erwartet, keinen Schemafehler.

## Was nicht gemessen wurde

* Die vier Felder am Erzeuger und die Vorpruefung selbst (liegen bei euch).
* Ob `aiimaging_query_render` `job_id` wirklich als Pflichtfeld fuehrt (euer Code).

```
{"beantwortet_am": "2026-09-29"}
```
