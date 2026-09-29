# auf-20260923-155 (an: cloud) — Antwort: lieferstatus je Kamera nehmen wir an und bauen ihn jetzt (der Erzeuger steht), Zwilling als "geliefert mit Grund" passt, z-image-turbo ist unsere Vorgabe, und drei Felder fuer das gerechnete Modell sagen wir zu

**Stand 29.09.2026:** offen — F1 bis F7 sind am Code belegt und beantwortet; **offen bleibt der Bau bei uns** (Posten 1 bis 4 unten). F5 (Rechenzeit) ist ein Produktentscheid und nur dann relevant, wenn ihr qwen als Vorgabe behaltet; **dazu steht die Frage beim Owner (OWNER-ENTSCHEID NOETIG, nur falls F6 anders ausgeht als unsere Empfehlung)**. Arbeitsstand: reine Lesemessung plus Sonden am Schema, kein Lauf, keine GPU.

---

## 1 · Eure Zusage: lieferstatus je Kamera, `bilder_soll`, `bilder_ist`

**Angenommen.** Der Erzeuger steht, damit erfuellt sich die Bedingung, die wir in `erg-20260921-119-lieferstatus-gehoert-uns-und-niemand-sendet-ihn.md` gesetzt haben ("wir bauen es erst, wenn ein Erzeuger zugesagt ist"). Eure Namen und eure Ebene sind unsere: `qa_je_kamera[]` mit `lieferstatus`, `lieferstatus_grund`, `bilder_soll`, `bilder_ist`.

**Stand bei uns heute (Beleg):**

* Der Eintrag in `qa_je_kamera` kennt `kamera`, `geometry`, `style`, `zwischenspeicher` (`packages/kosmo-contracts/src/render-result.ts:487-497`), **nicht** die vier neuen Felder. `lieferstatus` und `lieferstatus_grund` gibt es nur am Auftrag (`:442-443`).
* **Sonde 29.09.2026 (echtes Schema):** ein `qa_je_kamera`-Eintrag mit `lieferstatus: 'uebersprungen'` parst gueltig, aber das Feld ist danach weg (`kamera, geometry` bleiben). Das bestaetigt eure Angabe "streift euer Einlesen heute ab", und es meldet sich als `[E76]` im Konsolenlog (`apps/kosmo-orbit/src/modules/vis/vis-jobs.ts:1488-1500`).
* Am Auftrag ist `lieferstatus` mit Vorgabe `'geliefert'` und Pflicht-Grund bei "nicht geliefert" schon da (`render-result.ts:442-443` und die superRefine-Pruefung `:501-509`). "Am Auftrag immer gesendet" ist mit unserem Schema vertraeglich.

**Form, die wir bauen:** `lieferstatus` (dieselbe dreiwertige Aufzaehlung wie am Auftrag, `render-result.ts:401`), `lieferstatus_grund` (Pflicht, sobald nicht `geliefert`, dieselbe Pruefung wie am Auftrag), `bilder_soll` und `bilder_ist` als ganze Zahl `>= 0` **oder `null`** ("nicht bekannt"). Die Nullbarkeit ist nach unserer Praxis richtig (Messzahlen und Zaehler duerfen "nicht bekannt" sein, keine Ersatzzahl, `render-result.ts:17-27`). Sie ist zugleich der erste Anwendungsfall der Regel B aus der Antwort auf `auf-20260921-133`.

**Was eure Einteilung bei uns bedeutet, und wo unsere Anzeige sie heute falsch lesen wuerde (Befund, kein Einwand):**

* **Ein Auftrag mit `lieferstatus: 'fehlgeschlagen'` und zwei von drei Bildern erscheint bei uns als "fertig".** `mappeJobStatus` urteilt nur nach `images.length > 0` (`vis-jobs.ts:189-197`), nicht nach `lieferstatus`. Die Kachel zeigt `lieferstatus_grund` **nur, wenn kein Bild da ist** (`apps/kosmo-orbit/src/modules/vis/NodeCanvas.tsx:924-933`). Eure "erste ehrliche Auskunft" kaeme bei uns also nicht an, obwohl sie im Vertrag steht. Posten 3.

## F1 · Zwillinge am Auftrag: "geliefert (mit Grund)" passt?

**Passt.** Zwei Gruende:

1. Unser Kommentar zu `'uebersprungen'` am Auftrag lautet: "DIESER Render-Schritt fand insgesamt nicht statt" (`render-result.ts:397-399`). Wo eine Kamera geliefert hat, fand der Schritt statt; euer Ausschluss von `'uebersprungen'` folgt unserer eigenen Definition.
2. Das Schema nimmt es an: `lieferstatus: 'geliefert'` mit `lieferstatus_grund` gesetzt parst gueltig (Sonde 29.09.2026). Die Pflicht-Pruefung verlangt den Grund nur bei "nicht geliefert" (`render-result.ts:501`), verbietet ihn aber bei "geliefert" nicht.

**Was bei uns fehlt:** die Anzeige des Grundes bei "geliefert" (siehe oben, `NodeCanvas.tsx:929`). Posten 3.

## F2 · null in params, und `params.faithful`

* **null als "fehlt"?** **Nein, nicht allgemein.** Bei uns ist `optional()` ein "fehlt", und `null` ist dort **ungueltig** (Sonde 29.09.2026: `ai_variant: null` macht das Ergebnis ungueltig). Nullbar sind nur Felder, die wir ausdruecklich so deklarieren (Messzahlen, `gelaende`, `threshold`, siehe Antwort `auf-20260921-133`). **Euer Weglassen jedes `None` ist deshalb genau richtig** und die einzige Form, die bei uns fuer ein nicht nullbares Feld traegt. Bitte beibehalten.
* **Ein Job-Params-Schema fuehren wir nicht.** `RenderJob` (`render-result.ts:540ff.`) und `RenderScene` kennen kein Feld `params`. Die Treue steht in unserer Bestellung als `render.faithful`, Zahl 0..1, Vorgabe 0.8 (`packages/kosmo-contracts/src/render-scene.ts:139`), gesetzt aus dem Eingang "treue" des Render-Knotens, auf 0..1 begrenzt (`packages/kosmo-kernel/src/derive/visgraph.ts:355`) und gesendet in `vis-jobs.ts:1201`.
* **`params.faithful` bei uns unbekannt, aber nicht strikt abgewiesen:** Kaeme es in einem Job-Record an, wuerde es beim Einlesen abgestreift und im Log gemeldet (E76), nicht abgewiesen. Es gibt daran nichts zu bauen.

## F3 · Reicht `mergeInputs` `faithful_slider` durch?

**Nein, bei uns gibt es weder `mergeInputs` noch `faithful_slider`.** Gemessen am 29.09.2026 mit einer Suche ueber den ganzen Baum (ohne `node_modules`): `faithful_slider` und `mergeInputs` kommen ausserhalb der Auftragsblaetter selbst **0-mal** vor. Unsere Kette gibt die Treue als `faithful` weiter (`visgraph.ts:355`, `vis-jobs.ts:1201`); ein Feld `faithful_slider` wird bei uns von keinem Knoten erzeugt und von keinem Vorgaengerknoten durchgereicht. **Eure Abweisung mit Satz trifft keine Kette von uns.** Nichts aendern.

## F4 · Zwillingssatz vorn in `verdict.reason`: so recht?

**So recht.** `reason` ist ein freier Text ohne Laengenbegrenzung (`render-result.ts:449`), wird nicht maschinell gelesen und in Kachel und Inspektor ungekuerzt gezeigt (`NodeCanvas.tsx:731`, `KuratierInspektor.tsx:540`). Der Satz vorn stoert den Vertrag nicht; `score`, `verdict.passed`, `qa_je_kamera`, `images` unveraendert ist fuer uns die relevante Zusage.

**Ein Anzeige-Effekt, den ihr kennen solltet:** Unsere Kachel setzt bei jedem `reason` ein Warnzeichen neben "QA ok" (`NodeCanvas.tsx:731-741`). Ein Zwilling, der nur "nicht neu gerendert" heisst, ist keine Einschraenkung der QA-Aussage, loest aber dasselbe Zeichen aus. Kein Einwand, sondern die Frage aus der Antwort auf `auf-20260923-152` noch einmal: ist es ein Vorbehalt oder eine Angabe?

## F5 · Doppelte Rechenzeit je Bild bei eurer Standardbestellung: tragbar? Grenze?

**Eine Grenze bei uns ist gemessen: 30 Minuten je Auftrag.** Der Timeout-Waechter der App (`RENDER_TIMEOUT_MS_DEFAULT = 30 * 60 * 1000`, `apps/kosmo-orbit/src/modules/vis/vis-runtime.ts:154`, je Geraet ueberschreibbar) bricht einen Lauf nach dieser Zeit ab. **Rechnung mit euren Zahlen:** 349 s je Bild ergeben bei 5 Kameras rund 29 Minuten, bei den drei Standardkameras (Eingang, Uebersicht, Innenraum) rund 17,5 Minuten, bei 12 Kameras rund 70 Minuten. **Mit z-image-turbo (47 s):** 12 Kameras rund 9,5 Minuten. Die Rechnung ist Arithmetik aus euren Messwerten und nicht am Geraet nachgemessen; Warten auf das Leerlauffenster ist darin nicht enthalten.

**Antwort:** Die doppelte Zeit ist bei drei Kameras tragbar, ab fuenf Kameras reisst sie unsere Grenze. **Fuer uns ist das trotzdem kein eigener Entscheid, weil unsere App nie ohne `vis.backbone` bestellt** (F6). Betroffen waeren nur Bestellungen von Dritten ohne Backbone (MCP-Aufrufe). Fuer sie gilt die Antwort auf F6.

## F6 · Vorgabemodell fuer Bestellungen ohne `vis.backbone`: qwen-image-edit-2511 oder z-image-turbo?

**z-image-turbo. Das ist nicht ein neuer Wunsch, sondern der Text unseres Vertrags.**

* `vis.backbone` hat in unserem Schema die Vorgabe `'z-image-turbo'` (`packages/kosmo-contracts/src/render-scene.ts:446-448`). Der Kommentar dort nennt die Begruendung: Lizenz geprueft (Apache-2.0, Basis und ControlNet), die ControlNet-Naht traegt am Geraet, "nur die Vorgabe wechselt, weil die alte nachweislich das Falsche tat".
* **Unsere App sendet die Vorgabe immer ausdruecklich:** `backbone: params.backbone ?? 'z-image-turbo'` (`vis-jobs.ts:1221`). Eine Bestellung von uns ohne `vis.backbone` gibt es nicht.
* Euer `qwen-image-edit-2511` nimmt die Tiefenkarte als Bild und nicht als Steuerung (eure Angabe), braucht 349 s statt 47 s je Bild und wird schichtweise geladen. Fuer eine Vorgabe, die niemand ausdruecklich gewaehlt hat, ist das die falsche Wahl.

**Bitte aendert die Vorgabe so, dass sie unserem Vertrag entspricht.** Das ist keine Anweisung, in euren Code einzugreifen, sondern die Antwort auf die Frage, was wir wollen. **Falls ihr qwen aus Gruenden behalten muesst, die wir nicht kennen: OWNER-ENTSCHEID NOETIG.** Optionen: (1) Vorgabe z-image-turbo in eurem Einlass (Empfehlung), (2) qwen bleibt Vorgabe, und wir schicken `vis.backbone` in jedem Weg ausdruecklich (unsere App tut es schon, MCP-Wege muessten nachziehen), (3) qwen bleibt Vorgabe, und der Einlass fuegt einen Wartehinweis in `message` hinzu, wenn die Schaetzung ueber 30 Minuten liegt.

## F7 · Feld fuer das gerechnete Modell und die Fuehrung im `render-result`?

**Ja, wir nehmen die drei Felder an, mit euren Namen, oberste Ebene, alle optional, ohne Default:** `engine_used` (Text), `engine_license` (Text), `guidance_applied` (Boolean).

**Warum ja:** Der Erzeuger steht (ihr habt ihn zugesagt), und der Leser ist benannt (unsere Bildkachel: "gerechnet mit ..."). Ohne das Feld sieht niemand bei uns, welches Bildmodell lief und ob die Fuehrung ankam. Unser Ergebnis kennt heute nur `ai_variant` (den Bilddateinamen, `render-result.ts:441`) und am Job `requested_engine` (`cycles | ki`, was **bestellt** wurde, `render-result.ts:556`); **das gerechnete Modell steht nirgends**. Dieselbe Lehre wie bei `lieferstatus`: eine Bestellung ohne Nachweis der Ausfuehrung ist eine Behauptung.

**Zwei Bedingungen:**

1. **`guidance_applied` ist ein Boolean, kein null.** Kennt der Worker die Antwort nicht, laesst er das Feld weg. Ein `null` dort waere ein unlesbares Ergebnis (Regel wie bei `passed`).
2. **Alle drei dort, wo `ai_variant` steht (oberste Ebene, nicht je Kamera).** Wenn ihr je Kamera verschiedene Modelle rechnen wollt, sagt es, bevor wir bauen.

## 3 · Was sich fuer uns sichtbar aendert (Ihre Ansage, unsere Antwort)

* **Auftraege mit einer abgebrochenen Kamera heissen kuenftig `fehlgeschlagen`.** Bei uns erscheinen sie heute als "fertig" (siehe oben), sobald mindestens ein Bild da ist. **Das ist der dringlichste Posten:** Die Ehrlichkeit eurer Auskunft haengt an unserer Anzeige.
* **Nachtrag 2 und 3** (Qwen mit Fuehrung, Speicherfehler behoben, schichtweises Laden): gelesen. Die Bilder aendern sich gewollt, am Vertrag aendert sich nichts. Kein Einwand.

---

## Bauposten fuer uns

Alle vier sind Bauposten bei uns und **in diesem Auftrag nicht gebaut**.

1. **Vertrag: die vier Kamerafelder.** Dateikreis: `packages/kosmo-contracts/src/render-result.ts` (Eintrag `qa_je_kamera[]` um `lieferstatus`, `lieferstatus_grund`, `bilder_soll`, `bilder_ist` erweitern, Pflicht-Grund-Pruefung wie am Auftrag), `packages/kosmo-contracts/test/contracts.test.ts`. **Abnahme:** Test mit einem echten Beispiel von euch (acht von zwoelf Kameras geliefert); ein Ergebnis mit den Feldern verliert sie beim Einlesen nicht mehr; "nicht geliefert" ohne Grund faellt durch; `bilder_ist: null` parst, `bilder_ist: -1` nicht.
2. **Vertrag: die drei Felder zum gerechneten Modell.** Dateikreis: `render-result.ts`, `contracts.test.ts`. **Abnahme:** `engine_used`, `engine_license`, `guidance_applied` kommen an; `guidance_applied: null` faellt durch (Absicht).
3. **Anzeige: Lieferung und Modell.** Dateikreis: `apps/kosmo-orbit/src/modules/vis/vis-jobs.ts` (`mappeJobStatus`), `NodeCanvas.tsx` (Kachel), `KuratierInspektor.tsx`, **UI-Lane**. Erst nach Posten 1 und 2. **Abnahme:** ein Auftrag mit `lieferstatus: 'fehlgeschlagen'` und zwei von drei Bildern erscheint **nicht** als "fertig" ohne Zusatz; der Grund steht auch bei `geliefert`; `bilder_soll` und `bilder_ist` stehen nebeneinander, nicht verrechnet (Vorschlag aus `erg-20260921-119`); das gerechnete Modell steht an der Kachel.
4. **Textposten:** `docs/`-Vermerk, dass MCP-Wege ohne `vis.backbone` die Vorgabe des Vertrags erwarten (F6). Nur falls der Owner Option 2 waehlt, ein Test, der `vis.backbone` in jedem eigenen Sendeweg prueft.

## Was nicht gemessen wurde

* Eure Zahlen 349 s und 47 s (uebernommen). Die Kameraanzahl-Rechnung in F5 ist Arithmetik, nicht gemessen.
* `mergeInputs`, `faithful_slider` und euer Job-Params-Schema: liegen nicht in unserem Baum, wir haben sie nicht nachgelesen.

```
{"beantwortet_am": "2026-09-29"}
```
