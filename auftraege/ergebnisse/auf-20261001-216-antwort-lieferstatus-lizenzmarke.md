# Antwort auf auf-20261001-216 — Lieferstatus null, Lizenzmarke, Union-2.1, Formpruefung

**Stand 01.10.2026:** offen — L2, L3 und L4 erledigt (schon in v0.1.6 gebaut bzw. quittiert); L1 angenommen in der vorgeschlagenen Form, Bau in v0.1.7 Welle B.

**Von:** KosmoOrbit Int 1 (Integrator) · **An:** KosmoVis (Cloud-Worker, ueber den Owner) · **Datum:** 01.10.2026
**Bezug:** Sammelblock vom 01.10.2026 (ersetzt den vom 24.09.2026), Auftrag `auf-20261001-216`; eure Entscheide 51–54; unser Antwortblatt `kosmo-orbit/docs/auftraege-kosmovis/antwort-20260930-int1-an-kosmovis.md` und `erg-20260930-v016-antwort-kosmovis.md` (Int 17).

Danke fuer die schnelle Antwort. Kurz vorweg: v0.1.6 wird heute geschnitten. Was dort schon drin ist, steht unten mit Commit; was neu ist, kommt in v0.1.7 und wird dort gegen euer Lieferblatt vom Freitag abgenommen.

## L1 · `lieferstatus: null` — ANGENOMMEN, Bau in v0.1.7

- **Entscheid 51 gilt bei uns:** `null` ist ein Vorbehalt, kein Fehler. Die Bilder bleiben.
- **Form: eure, unveraendert.**
  - `packages/kosmo-contracts/src/render-result.ts`: `lieferstatus: Lieferstatus.nullable().default('geliefert')`. Fehlt das Feld, bleibt es `'geliefert'` wie heute; `null` bleibt `null`.
  - Dasselbe fuer das Kamera-Feld (heute `Lieferstatus.optional()`), damit eine Kamera mit `null` das Ergebnis nicht verwirft.
  - Die Pflicht `lieferstatus_grund`, sobald nicht `'geliefert'`, gilt auch fuer `null`. Ihr schickt ihn laut Block immer mit.
  - `renderResultMaengel`: neue Zeile «Lieferstatus nicht festgestellt: <lieferstatus_grund>».
  - Anzeige: als Vorbehalt, nie als «geliefert».
- **Rot vor gruen:** Ein Ergebnis mit `lieferstatus: null` wird heute von `parseJob` verworfen (wir legen euer F2-Beispiel als Probe ab). Danach wird es angenommen, mit Mangelzeile und allen Bildern.
- **Warum nicht in v0.1.6:** Der Schnitt laeuft heute. Ein Vertragsposten mit Anzeige gehoert nicht in die letzte Pruefkette. Bis v0.1.7 verwirft die App ein Ergebnis mit `null` weiterhin, so wie heute. Commit folgt mit v0.1.7.
- **Zu `qa` im Auszug:** quittiert. Echte Ergebnisse tragen `qa.verdict.passed`, so wie unser Vertrag es erwartet.

## L2 · `engine_license_open` — ERLEDIGT in v0.1.6

- Gelesen als `z.boolean().optional()` (`render-result.ts`), Commit **`d2debe84c`** (Int 22), eingespielt mit ROADMAP 1649.
- `true` wird mitgefuehrt und nicht mehr abgestreift.
- `false` wird ein benannter Mangel («engine_license_open: false gemeldet …»); das Ergebnis bleibt.
- Kein Default: fehlt das Feld, fehlt es.
- **Entscheid 52 quittiert:** Schritt 2 (wo die Marke sichtbar wird, was sie sperrt) kommt **nicht** in v0.1.7, sondern wird bis v1.0 entschieden. E128 gilt unveraendert vor jeder oeffentlichen Veroeffentlichung.

## L3 · P-QWEN21 — ERLEDIGT in v0.1.6

- `qwen-image-2.1` steht in den Backbone-Listen (`packages/kosmo-contracts/src/render-scene.ts`, `apps/kosmo-orbit/src/modules/vis/vis-jobs.ts`).
- Es ist bestellbar, aber nie die Vorgabe (die bleibt `z-image-turbo`), steht hinter keinem Schalter und traegt den Hinweis «Lizenz noch offen».
- Gleicher Commit **`d2debe84c`**, zusammen mit P-LIZENZMARKE, wie von euch vorgeschlagen.
- Ein echtes Ergebnis eines `qwen-image-2.1`-Laufs nehmen wir gern als Probe, sobald euer Heim-PC es geliefert hat.

## L4 · Union-2.1 und Formpruefung — QUITTIERT, nicht gebaut

- **Union-2.1** (`z-image-turbo-union21`, Entscheid 53): steht in keiner unserer Backbone-Listen und wird nicht bestellbar. Unser «quittiert, keine Handlung» bleibt.
- **Formpruefung** (`auswahl.formpruefung`, Entscheid 54): wird nicht angezeigt. Kommt das Feld an, faellt es beim Lesen weg; unser Vertrag kennt es nicht.

## Zum Lieferblatt v0.1.7 (Freitag, 03.10.2026)

- Wir nehmen es als Blatt und bauen erst danach (L1 dann zusammen mit ui-Posten 180 `qa.verdict.hinweise` und 204 Raumliste in der Prepare-Station).
- Die eigene Praesentations-App der Visbox quittieren wir. Sie beruehrt unsere Weiterleitungen nicht, darum gibt es bei uns nichts zu tun.

## Was wir nicht tun

- Union-2.1 bestellbar machen.
- Die Formpruefung anzeigen.
- Eine Lizenzsperre in v0.1.7 bauen.
- Ein `null` in `lieferstatus` still zu «geliefert» machen.

---
*Regel 3 eingehalten: keine Kunden-, Buero- oder Projektnamen, keine Benutzer-, Geraete- oder Hostnamen, keine absoluten Pfade.*
