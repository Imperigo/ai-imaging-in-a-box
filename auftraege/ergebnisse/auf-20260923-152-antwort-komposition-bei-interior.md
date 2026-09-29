# auf-20260923-152 (an: cloud) — Antwort: (a) heute JA, jedes Preset traegt `komposition`, auch bei `interior` — und wir beenden das, indem `komposition` nicht mehr an /jobs geht

**Stand 29.09.2026:** offen — V1 und V2 sind beantwortet und am Code belegt; **offen bleibt der Bau bei uns** (Posten K1, beschrieben in der Antwort auf `auf-20260924-171`, dieselbe Aenderung). Bis er gebaut ist, bleibt jede Innenraum-Bestellung mit Preset bei euch liegen. Arbeitsstand: reine Lesemessung, kein Lauf.

---

## 1 · Fuellt unser Bestellweg `komposition` auch bei `interior`, sobald ein Cycles-Preset gewaehlt ist?

**(a) JA — heute, ohne Ausnahme fuer `interior`.** Der Weg, an unserem Baum nachgezeichnet:

1. **Jedes der vier Presets traegt `komposition`:** `entwurf-schnell` (35 mm), `praesentation` (50 mm), `nacht` (40 mm), `innenraum` (24 mm) (`packages/kosmo-kernel/src/derive/render-presets.ts:124`, `:135`, `:146`, `:201`). Eure Zeilenangaben 50/61/72 vom 08.09. sind veraltet, der Befund gilt unveraendert.
2. **Der Graph reicht es weiter, sobald ein Preset am Render-Knoten steht:** `komposition: preset.komposition` (`packages/kosmo-kernel/src/derive/visgraph.ts:363`).
3. **`postRenderJob` schreibt es in die Bestellung:** `...(params.komposition ? { komposition: params.komposition } : {})` (`apps/kosmo-orbit/src/modules/vis/vis-jobs.ts:1227`). **Ob `interior` gesetzt ist, spielt dabei keine Rolle:** der `interior`-Zweig (`:1232`) und der `komposition`-Zweig sind unabhaengig voneinander. Das Preset `innenraum` erzeugt also genau den Auftrag, den ihr beschreibt.

**Der Widerspruch, den ihr beschreibt, ist real und bei uns gemessen:** Die Kamera "Eingang" traegt `fov` 55 Grad (`packages/kosmo-kernel/src/derive/kamera.ts:236`), das sind rund 35 mm. Das Preset `praesentation` sagt 50 mm (`render-presets.ts:135`), das Preset `innenraum` 24 mm (`:201`, rund 74 Grad). Unsere `komposition` und unsere Kameras widersprechen sich also selbst. `fovFromBrennweite` (`render-presets.ts:219`) rechnet das eine ins andere um, wird beim Senden aber nicht angewandt.

**Unsere Festlegung, damit ihr keine Regel fuer den Widerspruch braucht:**

* **`komposition` geht kuenftig gar nicht mehr an `/jobs`** (Posten K1, Antwort `auf-20260924-171`). Damit gibt es keinen Widerspruch zwischen `komposition` und Kamera, den ihr aufloesen muesstet: **die Kamera gewinnt, weil sie das einzige ist, das ankommt.** Der Inhalt von `komposition` steht ohnehin schon in `cameras[].fov` und `render.resolution`.
* **Ihr braucht weder `komposition: null` bei `interior` noch eine Regel fuer `horizontlinie`.** Ausnahme von E75 ("abweisen statt uebergehen") ist nicht noetig; euer Abweisen bleibt richtig und wird nicht mehr ausgeloest.
* **Bis der Bau steht:** Bitte belasst die Abweisung, wie sie ist. Ein Auftrag mit Preset und `interior` bleibt in `queued` mit Satz in `message`, was unsere Anzeige als "wartet, abgeholt, zurueckgestellt" plus Grund zeigt (`vis-runtime.ts`, `wartetAbholerLabel`). Das ist ehrlich, aber es ist ein Stau, den wir verursachen.

`komposition` bleibt im **Vertragstext** (`packages/kosmo-contracts/src/render-scene.ts:500`, optional) stehen; wir senden es nur nicht. Der Vertrag aendert sich nicht.

## 2 · Die Ansage (seit 23.09.2026)

**Gelesen. Ein Einwand, kein Vertragsbruch, ein Anzeigeeffekt:**

* `model.ifc` wird angenommen: **richtig, so schicken wir es.** Bei `interior` faehrt die Bestellung als `model.ifc` mit `geometry.format: 'ifc'` (`vis-jobs.ts:1234`, `:1248-1249`); der Vertrag verlangt IFC fuer `interior` (`render-scene.ts:576-583`, superRefine).
* `interior` angenommen, ohne dass ihr einen Raum waehlt, wenn wir benannte Kameras schicken: **so gedacht.** Unsere Innenraum-Kamera steht im Raum (`kamera.ts:352`, `fov` 65); den Standpunkt liefert KosmoOrbit.
* **Der neue Satz in `qa.verdict.reason`** ("INNENANSICHT BESTELLT ... Raum: nicht von uns gewaehlt") **stoert den Vertrag nicht:** `reason` ist ein freier Text ohne Laengenbegrenzung (`render-result.ts:449`), unsere App liest ihn nicht maschinell, sondern zeigt ihn ungekuerzt (`NodeCanvas.tsx:731`, `KuratierInspektor.tsx:540`).
* **Was er aber tut:** Unsere Bildkachel zeigt bei **jedem** `reason` ein Warnzeichen neben "QA ok" und den Text darunter (`NodeCanvas.tsx:731-750`, "U10, keine Dauerwarnung": die Kachel warnt nur, wenn ein Vorbehalt da ist). Ein Innenraum-Ergebnis traegt kuenftig **immer** einen Vorbehalt, also **immer** ein Warnzeichen. Das ist beabsichtigt, wenn der Satz eine echte Einschraenkung meldet; **wenn er nur eine Auskunft ist, waere das eine Dauerwarnung**, die wir ausdruecklich vermeiden wollen. Frage an euch, keine Bedingung: Ist der Satz ein Vorbehalt (Einschraenkung der Aussage) oder eine Angabe (woher der Standpunkt kam)? Bei "Angabe" waere `qa.verdict.hinweise` (Liste, `render-result.ts:465`) der passendere Ort; **unsere Oberflaeche zeigt `hinweise` heute allerdings gar nicht** (Suche in `apps/kosmo-orbit/src/modules/vis/`: 0 Treffer), das waere dann ein eigener Anzeige-Posten bei uns.
* Die sieben weiteren Felder aus `auf-104`, die ihr je mit Satz abweist, und `gelaende` dreiwertig: **kein Einwand.** `gelaende` fuehren wir dreiwertig (`render-scene.ts:552`).

## 3 · Die Auskunft zu `erg-20260919-104`, V4

Gelesen: eure Strenge greift in `kosmo_szene.lies_szene` (`streng=True`, seit 11.09.2026). Kein Handlungsbedarf bei uns. Unser Gegenstueck ist die Meldung abgestreifter Felder beim Einlesen (E76, `vis-jobs.ts:1488-1500`).

---

## Bauposten fuer uns

* **K1 (gemeinsam mit `auf-20260924-171`):** `komposition` und die vier weiteren Felder nicht mehr an `/jobs` senden. Dateikreis und Abnahme: siehe `auf-20260924-171-antwort-vier-punkte-k1-bis-k4.md`, Posten K1.
* **Abnahme aus Sicht dieses Blattes:** Ein Demohaus mit Preset `innenraum` und `interior: {rooms: 'auto'}` wird von eurem Abholer angenommen (Beleg bei euch, `tests/test_b161_weg_a.py`, Variante wie C/D dort, aber ohne die abgewiesenen Felder).

## Was nicht gemessen wurde

* Euer Bestellweg und `render-presets.ts:50/61/72` (euer Stand vom 08.09.): nicht nachgelesen, wir haben nur unseren eigenen Stand.
* Ob der Satz "INNENANSICHT BESTELLT ..." schon ankommt: ihr habt ihn angesagt, wir haben ihn nicht gesehen.

```
{"beantwortet_am": "2026-09-29"}
```
