# auf-20260922-142 (an: cloud) — Antwort: `geometry_gates` wird bei uns abgestreift, `passed: null` nehmen wir nicht an (bitte `status` nutzen), und unsere Anzeige liest ein ungeprueftes `false` heute als "durchgefallen"

**Stand 29.09.2026:** offen — V1 bis V4 sind am Code und an einer Sonde gegen das echte Schema beantwortet; **offen bleibt der Bau auf unserer Seite** (drei Posten unten: `geometry_gates` im Vertrag, Kamerazeile liest `status`, Anzeige der Tore) und ein Beispiel-JSON von euch fuer die Form von `geometry_gates`. Arbeitsstand: reine Lesemessung plus eine Sonde am Schema, kein Lauf, keine GPU.

---

## V1 · Streift unser Einlesen von render-result unbekannte Felder der obersten Ebene ab?

**JA — und zwar an genau einer Stelle, und nicht still.**

* `RenderResult` ist ein nicht-strenges `z.object` (`packages/kosmo-contracts/src/render-result.ts:403`), eingebettet in `RenderJob.result` (`:567`). Ein Feld, das nicht im Schema steht, faellt beim Einlesen weg.
* **Sonde 29.09.2026** (echtes `RenderResult`, zod 4.4.3): ein Ergebnis mit `geometry_gates: {passed: false}` und `qa_je_kamera[0].lieferstatus` parst gueltig, die geparsten Schluessel sind `schema, job_id, images, lieferstatus, qa, qa_je_kamera`, und der Eintrag in `qa_je_kamera` traegt danach nur noch `kamera, geometry`. `geometry_gates` und der Kamera-`lieferstatus` sind weg.
* **Unsere Bridge streift nichts ab.** Sie bettet `render-result.json` unveraendert in den Job-Record ein (`tools/homestation-bridge/kosmo_bridge/main.py:1912-1914`). Das Abstreifen geschieht erst in der App, in `parseJob` (`apps/kosmo-orbit/src/modules/vis/vis-jobs.ts:1488-1500`).
* **Nicht still:** `parseJob` meldet jedes abgestreifte Feld mit Pfad ins Konsolenlog ("[E76] ... Feld(er) ... wurden von zod abgestreift", Owner-Entscheid 19.09.2026, `packages/kosmo-contracts/src/unbekannte-felder.ts`). Auf der Oberflaeche sieht es niemand; im Log sieht es jeder, der nachschaut.

Eure Vermutung stimmt also, und die Herleitung aus `erg-20260917-37` (F6, render-scene) trifft auch fuer render-result zu.

## V2 · Wollen wir `geometry_gates` im Vertrag?

**JA, unter dem Namen `geometry_gates`, oberste Ebene, additiv und optional, ohne Default.** Wir wollen es aus zwei Gruenden:

1. Es gibt einen Erzeuger (ihr) und, sobald wir bauen, einen Leser (unsere Anzeige). Damit ist es kein Feld ohne Empfaenger, so wie `lieferstatus` bis zum 21.09. eines war (`erg-20260921-119-lieferstatus-gehoert-uns-und-niemand-sendet-ihn.md`).
2. Die Aussage "`released` ist auf dem heutigen Weg immer `false`, weil die Gegenprobe fehlt" ist genau die Sorte Vorbehalt, die bei uns zum Bild gehoert und nicht ins Log.

**Was wir dafuer von euch brauchen:** Ihr habt uns die Feldliste geschickt (`camera`, `passed`, `released`, `status`, `fail_reasons`, dazu einen Grund), aber keine Typen. **Bitte ein echtes Beispiel-JSON** (gemessen, nicht gebaut). Wir schreiben das Schema nach dem Beispiel, nicht nach der Liste. Dabei gilt die Regel aus V3: `passed` ist ein Boolean, kein null.

**Bedingung, die wir daran knuepfen:** `status` benutzt die drei Werte, die unser Vertrag schon fuehrt (`measured | not_measured | not_applicable`, `render-result.ts:218`), keine vierte Schreibweise. Falls euer Block andere Werte braucht, sagt es vor dem Bau.

## V3 · Liest unser Werkzeug `qa_je_kamera[].geometry`? Laesst das Schema `passed: null` zu?

**Lesen: ja. `passed: null`: NEIN — bitte nicht auf null umstellen.**

**Wer liest:** `qa_je_kamera` kommt in der App an (`apps/kosmo-orbit/src/modules/vis/NodeCanvas.tsx:924`), wird in der Kuratierflaeche gezeigt (`KuratierFlaeche.tsx:430`) und je Kamera zu einer Zeile gerechnet: `kameraQaZeilen` (`varianten-diff.ts:86-95`).

**Warum nicht null:** `passed` ist bei uns ein Boolean an drei Stellen (`render-result.ts:33` StyleQA, `:327` GeometryQA, `:448` verdict). Sonde 29.09.2026: `qa_je_kamera[0].geometry.passed = null` macht das **ganze Ergebnis** ungueltig, und `parseJob` wirft dann den ganzen Job weg (`vis-jobs.ts:1490-1494`). Ihr wuerdet mit dem Umstellen auf null nicht "ehrlicher", sondern jedes Ergebnis mit einer ungeprueften Kamera bei uns unlesbar machen. Der Kommentar bei `render-result.ts:190-194` sagt es ausdruecklich: ein `passed: null` waere "ein fehlendes Urteil, eine andere Frage, die einen eigenen Entscheid braucht".

**Was ihr stattdessen senden koennt, ohne dass ein Vertrag sich aendert:** `geometry: { passed: false, status: 'not_measured', ... }`. Das Feld `status` gibt es bei uns seit dem 03.09.2026 (`render-result.ts:262`), dreiwertig, ohne Default. `not_measured` heisst dort genau eure Lage ("das `false` heisst NICHT durchgefallen").

**Aber: unsere Anzeige liest das heute falsch.** `kameraQaZeilen` liest nur `geometry.passed` (`varianten-diff.ts:89`) und rechnet `bestanden` als UND der Flaggen (`:91-95`). Ein ungeprueftes `passed: false` erscheint bei uns heute als **"durchgefallen"**, egal was `status` sagt. Das ist unser Fehler, nicht eurer, und er wird erst sichtbar, seit die Kamerabloecke wirklich ankommen. Bauposten 2 unten.

## V4 · Wird `verdict.reason` vollstaendig durchgereicht?

**JA, ohne Kuerzung, an jeder Stelle, die wir gemessen haben.**

* Vertrag: `reason: z.string().optional()` (`render-result.ts:449`), keine Laengenbegrenzung.
* Bridge: unveraendert eingebettet (`main.py:1912-1914`).
* App: Kachel (`NodeCanvas.tsx:731` und `:746-750`) und Inspektor (`KuratierInspektor.tsx:540`, Kommentar: "ungekuerzt (Auflage)") zeigen den ganzen Text. In `vis-visual.css:71-76` steht keine Zeilenbegrenzung.

**Eine Einschraenkung, die wir nicht gemessen haben:** Ein Grund mit mehreren Saetzen je Kamera steht in einem Block mit sehr kleiner Schrift (`--k-t-xxs`). Ob eine sehr lange Fassung dort noch lesbar ist, ist ungetestet; das ist ein Anzeige-Punkt fuer den ui-Worker, kein Vertragspunkt.

---

## Bauposten fuer uns

Alle drei sind Bauten bei uns und **nicht in diesem Auftrag gebaut**. Gemeinsamer Grundsatz: nichts bauen, bevor der Erzeuger sein Beispiel geliefert hat (Posten 1) beziehungsweise nichts anzeigen, was der Vertrag nicht traegt.

1. **`geometry_gates` in den Vertrag.** Dateikreis: `packages/kosmo-contracts/src/render-result.ts` (neues `GeometryGates`-Schema, Feld an `RenderResult`), `packages/kosmo-contracts/test/contracts.test.ts`. **Abnahme:** ein Test mit eurem Beispiel-JSON, der zeigt, dass `geometry_gates` nach dem Einlesen ankommt und `[E76]` fuer dieses Feld nicht mehr meldet; ein Gegenlauf mit einem unbekannten Nachbarfeld, das weiter abgestreift und gemeldet wird.
2. **Die Kamerazeile liest `status`.** Dateikreis: `apps/kosmo-orbit/src/modules/vis/varianten-diff.ts` (`kameraQaZeilen`), Test in `apps/kosmo-orbit/test/`. **Abnahme:** `geometry: {passed: false, status: 'not_measured'}` ergibt **keine** `geometryBestanden`-Aussage (kein "durchgefallen", kein "bestanden"), analog zur Regel "keine erfundene Aussage ueber eine Kamera ohne Messung" (`varianten-diff.ts:74-76`). Dieselbe Regel fuer `not_applicable`. **Das ist der Posten mit Dringlichkeit**, weil er heute schon eine falsche Anzeige erzeugt, sobald ihr `false` mit Vorbehalt sendet.
3. **Anzeige der zwei Tore.** Dateikreis: `apps/kosmo-orbit/src/modules/vis/` (Kuratierflaeche/Inspektor), **UI-Lane**. Erst nach Posten 1. **Abnahme:** `released: false` erscheint als ausdrueckliche Aussage ("Gegenprobe fehlt") und nicht als Abwesenheit.

## Was nicht gemessen wurde

* Die Form von `geometry_gates` (keine Typen, kein Beispiel von euch).
* Der Aufbau der Anzeige mit sehr langem `reason` (ungetestet).

```
{"beantwortet_am": "2026-09-29"}
```
