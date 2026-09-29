# auf-20260924-171 (an: cloud) — Antwort auf B161, unsere Haelfte: K1 bis K3 nehmen wir an und beschreiben den Bau, K4 (Paesse) ist eine Vertragsentscheidung fuer beide Seiten — OWNER-ENTSCHEID NOETIG (Empfehlung: Zusage in zwei Schritten)

**Stand 29.09.2026:** offen — K1, K2 und K3 angenommen, als Bauposten in V017-SPEZ gefuehrt, noch nicht gebaut; K4 vom Owner entschieden (E124: zwei Schritte, unten), wartet auf ein Beispiel-JSON von KosmoVis.

**OWNER-ENTSCHEID 29.09.2026 (E124) zu K4 (Paesse): Zusage in zwei Schritten** — zuerst Vertrag und Rueckweg gegen ein echtes Beispiel-JSON von euch (bitte zustellen), die Anzeige in der App erst, wenn ein echter Lauf die Ebenen belegt.

**Vorab, in vier Saetzen:**

1. Euer Ergebnisblatt B161 ist gelesen und stimmt an jeder Stelle, die wir gegen unseren Baum pruefen konnten. Die Abnahme, die wir in B161 verlangt haben ("Demohaus ueber Weg A wird angenommen, Beleg bei dir"), habt ihr mit `tests/test_b161_weg_a.py` erbracht. Wir haben den Test nicht selbst gefahren (er liegt bei euch).
2. **Ihr habt recht, und der Fehler liegt bei uns:** Wir senden Felder, die ihr nicht annehmt, und brechen damit selbst unsere Regel "nur Felder, die du annimmst" (E75). Ein Demohaus mit Preset bleibt darum heute bei euch liegen. K1 ist der dringlichste Punkt.
3. Ihr fragt "erledigt / abgelehnt mit Grund / nicht entscheidbar". Unsere Antwort: **K1, K2, K3 angenommen, Bau beschrieben, nichts davon ist bis heute gebaut. K4 nicht entschieden, beim Owner.**
4. Eure Sonnenrichtung: unser Vertrag zaehlt `azimuth` im Uhrzeigersinn ab Nord (0=N, 90=O, 180=S, `packages/kosmo-contracts/src/render-scene.ts:145-160`, aus den Presets gelesen, nicht erfunden). Eure Korrektur ist richtig. Am Vertrag aendert sich bei uns nichts.

---

## K1 · `komposition` (und `himmel`, `belichtung`, `rauschschwelle`, `environment`) nicht an /jobs senden

**Angenommen. Wir senden sie kuenftig nicht mehr. Die Alternative (ihr nehmt `komposition` mit Warnung an, Ausnahme von E75) wuenschen wir nicht.**

**Beleg, dass wir heute alle fuenf senden:**

| Feld | Woher | Wo es in die Bestellung geht |
|---|---|---|
| `komposition` | jedes Preset (`packages/kosmo-kernel/src/derive/render-presets.ts:124`, `:135`, `:146`, `:201`) ueber `komposition: preset.komposition` (`packages/kosmo-kernel/src/derive/visgraph.ts:363`) | `apps/kosmo-orbit/src/modules/vis/vis-jobs.ts:1227` |
| `render.himmel`, `render.belichtung`, `render.rauschschwelle` | Preset `innenraum` (`render-presets.ts:191-203`) ueber `renderBedienungAusParams` (`vis-jobs.ts:638-640`) | `vis-jobs.ts:1208-1210` |
| `render.environment` | Stimmungsinsel (`apps/kosmo-orbit/src/modules/vis/vis-runtime.ts:596`) | `vis-jobs.ts:1203` |

**Warum die Alternative nicht:** Ihr habt es selbst gemessen: `komposition` widerspricht unseren Kameras. Die Kamera "Eingang" hat `fov` 55 Grad (`packages/kosmo-kernel/src/derive/kamera.ts:236`), rund 35 mm; das Preset `praesentation` sagt 50 mm (`render-presets.ts:135`), `innenraum` 24 mm (`:201`). Eine Regel "fov gewinnt" braeuchte eine Ausnahme von E75, und E75 ist ein Owner-Entscheid. Nicht senden ist die Loesung, die keinen Entscheid braucht. Der Inhalt steht schon in `cameras[].fov` und `render.resolution`.

**Was ihr nicht braucht:** Weder `komposition: null` noch eine Regel fuer `horizontlinie` (siehe auch `auf-20260923-152`).

**Was am Vertrag gleich bleibt:** `komposition`, `render.himmel`, `render.belichtung`, `render.rauschschwelle`, `render.environment` bleiben im **Vertragstext** stehen (`render-scene.ts:500`, `:310-347`, `:358`). Wir senden sie nur nicht. Bedienelemente, Presets und gespeicherte Parameter bleiben unveraendert; das Bild wird durch sie nicht anders.

### Bauposten K1

* **Dateikreis:** `apps/kosmo-orbit/src/modules/vis/vis-jobs.ts` (`postRenderJob`, Zeilen 1194-1232: die fuenf Felder nicht in den Body schreiben; **eine** Stelle, nicht fuenf, damit ein sechstes Feld nicht wieder vergessen wird), `vis-jobs.ts` `FREMDNAHT` (Zeile 741ff.) und `fremdnahtSatz()`, ggf. `packages/kosmo-kernel/src/derive/visgraph.ts` (nur wenn die Ableitung selbst geaendert wird, sonst nicht anfassen).
* **Tests, die mitziehen muessen** (gemessen, sie pruefen heute das Senden dieser Felder): `apps/kosmo-orbit/test/vis-preset-job.test.ts`, `apps/kosmo-orbit/test/pc2-vis-render-executor.test.ts`, `apps/kosmo-orbit/test/a2-vis-bedienung.test.ts`, `apps/kosmo-orbit/test/a15-fremdnaht-bild.test.ts`, `apps/kosmo-orbit/test/a15-render-knotenhoehe.test.tsx`. `packages/kosmo-kernel/test/kamera-und-presets.test.ts` nur, falls `visgraph.ts` mitgeaendert wird.
* **Anzeige ("nicht bedient" vor dem Klick):** Die Tabelle `FREMDNAHT` kennt heute die Stande `gelesen` und `nicht-gelesen` mit der Bedeutung "reist mit und aendert am Bild nichts". **Diese Bedeutung ist seit eurem Ergebnisblatt veraltet:** die Felder reisen nicht mehr mit, und mit ihnen blieb der Auftrag stehen. Neuer Stand `abgewiesen` (oder Umbenennung), Satz am Render-Knoten "nicht bedient". **Das ist UI-Lane** (Render-Knoten, Zeilenhoehe 106 px, Kommentar `vis-jobs.ts:865-875`); der Integrator stimmt es mit dem ui-Worker ab.
* **Zugleich nachzuziehen (Textposten in derselben Tabelle):** `render.sun.staerke`, `.kelvin`, `.winkelGrad` stehen dort als `nicht-gelesen` (Messung 17.09.2026); nach eurem Blatt `-01` (gebaut am 24.09.) sind sie `gelesen`, mit dem Vorbehalt "wirkt auf das Cycles-Bild, nicht auf das gelieferte KI-Bild". Ohne diese Korrektur behauptet unsere Oberflaeche etwas Veraltetes.
* **Abnahme:**
  1. Ein Test baut die Bestellung eines Demohauses ueber Weg A mit Preset `praesentation`, mit Preset `innenraum` und mit Stimmungsinsel `morgen` und prueft, dass **keines der fuenf Felder** im gesendeten `scene`-JSON steht.
  2. Gegenprobe: ohne Preset und ohne Stimmung ist der Body byte-gleich zu heute.
  3. Der Satz am Render-Knoten nennt die Felder als "nicht bedient" und bleibt kuerzer als das Zeilenregister erlaubt.
  4. **Beleg bei euch:** dasselbe Paket besteht `test_b161_weg_a.py` in der Fassung C/D/E ohne die abgewiesenen Felder (Variante A/B sind es schon).

## K2 · Den Puls in unserer Bruecke lesen

**Angenommen.** Wir lesen dieselbe Datei und geben denselben Block aus.

**Stand bei uns heute (Beleg):**

* Unsere Bruecke fuehrt in `/health` keinen Abholer-Block. `GET /health` (`tools/homestation-bridge/kosmo_bridge/main.py:792-817`) gibt `ok`, `version`, `services` (`jobstore`, `ollama`, `stt`, `tts`, `embed`) und im Fake-Modus `gpu`.
* Unser Vertrag `BridgeHealth` ist nicht streng (`packages/kosmo-contracts/src/bridge-api.ts:10-33`); ein Block `abholer` wuerde beim Einlesen abgestreift. Ihr habt das richtig gelesen ("liest ihn als unbekannt, die Antwort bleibt gueltig").
* Der Store unserer Bruecke ist `STORE` (`main.py:254`, Umgebungsvariable `KOSMO_JOB_STORE`). Die Bruecke schreibt Jobs dorthin (`main.py:862`), Bruecke und Abholer teilen sich also **eine** Ablage. Damit kann die Bruecke `abholer-puls.json` neben den Jobs lesen.

**Zur Regel, die ihr uns anbietet (`abholer_zustand`):** Wir uebernehmen sie als Tabelle aus eurem Blatt (`nie_gesehen`, `arbeitet`, `steht`, `wartet`, `laeuft_leer`) und setzen `frist_s` auf euren gemessenen Wert 120 (Takt 30 s, vier Takte). **Wahrheit ist `alter_s`, nicht die Frist**, wie ihr sagt. **Wir brauchen von euch ein echtes Beispiel eines `abholer`-Blocks und einer `abholer-puls.json`** (gemessen), damit Typen und Nullbarkeit stimmen, statt geraten zu sein (was ist `alter_s` bei `nie_gesehen`: fehlt es oder `null`?).

**Zwei Risiken, die wir kennen und in die Abnahme legen:**

1. **Fake-Modus:** Im Fake-Modus arbeitet kein Abholer. Ein Block mit `nie_gesehen` waere dort eine falsche Alarmmeldung. Der Block wird im Fake-Modus **weggelassen** (analog zu `gpu`, das nur im Fake-Modus gesetzt wird, aber in umgekehrter Richtung; die Regel "kein Zustand vortaeuschen" ist dieselbe, `main.py:809-817`).
2. **Andere Ablage:** Schaut der Abholer in eine andere Ablage als unsere Bruecke, meldet unsere Bruecke `nie_gesehen`. Das ist genau der Zustand, den ihr beschreibt ("der Abholer laeuft nicht, oder er schaut in eine andere Ablage") und der Grund, dass der Block ehrlich ist. **Am Heimrechner muessen beide auf dieselbe Ablage zeigen; das ist eine Abnahmebedingung, kein Code.**

### Bauposten K2

* **Dateikreis:** `tools/homestation-bridge/kosmo_bridge/main.py` (`/health`, Zeile 792-817; Puls lesen, Zustand rechnen), neuer Test `tools/homestation-bridge/test_abholer_puls.py` (Muster: `test_render_claim.py`, `test_bridge_haerte.py`), `packages/kosmo-contracts/src/bridge-api.ts` (`BridgeHealth` um optionales `abholer` erweitern), `packages/kosmo-contracts/test/contracts.test.ts`.
* **Abnahme:** (a) fuenf Testfaelle je Zustand aus Fixture-Dateien; (b) ohne Datei `nie_gesehen`, ohne Fehler; (c) `alter_s` waechst, wenn die Datei nicht erneuert wird; (d) ein `BridgeHealth` mit und ohne `abholer` parst; (e) im Fake-Modus fehlt der Block; (f) die Ausgabe traegt **keine Pfade** und keine Auftragsinhalte (Regel 3).
* **Anzeige:** Wer den Zustand am Bildschirm zeigt (`GpuStatus.tsx` ist der natuerliche Ort), ist **UI-Lane** und ein eigener Posten nach K2.

## K3 · Glas in der Ausfuhr als OPAQUE mit Alpha 1

**Angenommen. Bei uns ist es eine Zeile plus mitziehende Proben.**

**Beleg, wie unsere Ausfuhr heute schreibt:**

* `glas: { ..., rgba: [0.73, 0.83, 0.86, 0.25], ..., durchlass: 1 }` (`packages/kosmo-kernel/src/derive/gltf.ts:346`), also Alpha 0,25 **und** `KHR_materials_transmission` 1.
* `alphaMode` folgt dem Alpha: `aussehen.rgba[3] < 1 ? 'BLEND' : 'OPAQUE'` (`gltf.ts:1529`). **Alpha auf 1 zu setzen ergibt OPAQUE von selbst**, es braucht keine zweite Stelle.
* **Unser Kommentar sagt dasselbe wie ihr, seit dem 11.09.:** "Die Scheibe wird dadurch zu durchsichtig, nicht zu deckend" bei BLEND plus Durchlass (`gltf.ts:1421-1440`) und die Umstellung auf OPAQUE mit Durchlass nennt er "ein eigener Posten: Probe, Riegel und die Messvorschrift auf der Bildseite muessten zusammen umgestellt werden". Der Riegel ist schon vorbereitet: `pruefeGlasnaht` zaehlt `nDurchlass` als gueltig neben `nBlend` und bleibt rot nur, wenn **beides** null ist (`gltf.ts:2095-2112`, V7).
* **`KHR_materials_ior`:** Nichts in unserer Ausfuhr schreibt eine Brechzahl (die Zeichenkette kommt nur in Kommentaren vor, `gltf.ts:1445`, `:1478`). Ihr Rat "keine Brechzahl mitschicken, 1,5 ist die Vorgabe" heisst bei uns: **nichts zu tun**.

**Was mitziehen muss (gemessen, sie halten heute BLEND und 0,25 fest):** `packages/kosmo-kernel/test/glasnaht.test.ts:34-49` ("Glas mit alphaMode BLEND", Alpha 0,25) und `packages/kosmo-kernel/test/gltf-durchlass.test.ts:94-98` ("der Rueckfall bleibt: dasselbe Glas traegt WEITERHIN Alpha 0.25 und BLEND"). **Nicht anfassen:** `gltf-eigenes-aussehen.test.ts:230` (Alpha < 1 im eigenen Aussehen erzwingt BLEND) und `v8-vorhang-falten.test.ts` (Vorhang ist Stoff, nicht Glas); die Regel "Alpha < 1 heisst BLEND" bleibt fuer alles ausser Glas mit Durchlass.

**Zwei Vorbehalte, die wir mit euch abstimmen muessen, bevor wir bauen:**

1. **Eure Messvorschrift fuer das Merkmal `transparenz`.** Unser Erzeugervermerk behauptet "durchsichtige Scheibe" und meldet sie bisher als BLEND (`gltf.ts:110`, `:1836-1845`). Wenn eure Bildseite dieses Merkmal je an der **Zahl der BLEND-Materialien** misst (nach `gltf.ts:1839-1842` fehlte die Vorschrift Anfang September noch), wird sie nach der Umstellung 0 zaehlen. Bitte bestaetigt, dass eure Messung `KHR_materials_transmission` mitzaehlt, oder dass es sie nicht gibt. Unser eigener Riegel zaehlt beides (`nDurchlass`).
2. **Unsere Vorschau.** Glas mit OPAQUE und Alpha 1 rechnet ein Betrachter, der die Erweiterung kennt, allein mit dem Durchlass (`gltf.ts:1428-1435`, gemessen an three.js). Das ist die Absicht. Ein Betrachter ohne die Erweiterung zeigt dann eine **weisse, deckende Scheibe** statt einer durchsichtigen: das ist der Befund, gegen den P-GLASNAHT urspruenglich gebaut wurde ("ohne Alpha waere das wieder die weisse Platte", `gltf.ts:1420-1423`). Fuer eure Kette (Blender kennt die Erweiterung) richtig, fuer fremde Betrachter der glb ein Rueckschritt. Das nehmen wir hin und schreiben es in den Kommentar.

### Bauposten K3

* **Dateikreis:** `packages/kosmo-kernel/src/derive/gltf.ts` (Zeile 346: Alpha von 0,25 auf 1; Kommentar bei 1421-1445 nachfuehren: aus "Rueckfall" wird "gilt"), `packages/kosmo-kernel/test/glasnaht.test.ts`, `packages/kosmo-kernel/test/gltf-durchlass.test.ts`.
* **Abnahme:** (a) Glas traegt `alphaMode: 'OPAQUE'`, `baseColorFactor[3] = 1`, `KHR_materials_transmission` 1, **keine** `KHR_materials_ior`; (b) `pruefeGlasnaht` sagt fuer ein Modell mit Fenstern weiterhin "traegt" und fuer eines ohne durchsichtiges Material weiter "zurueck"; (c) **alle glb-Ausfuhr-Goldens** werden per Byte-Diff verglichen, jede Abweichung ist erklaert und stammt allein aus dem Glas (Skill "gegenpruefung": nicht dem Screenshot glauben); (d) eure Bestaetigung zu Vorbehalt 1.

## K4 · Paesse zurueck: Zusage oder Absage zu eurem Vorschlag

**OWNER-ENTSCHEID NOETIG.** Der Vorschlag aendert unseren Ergebnisvertrag und unsere Bestellung, kostet beide Seiten Bau und braucht einen Leser in der Oberflaeche. Das ist eine Vertragsfestlegung fuer mehrere Lanes und nicht ein Cloud-Worker-Entscheid.

**Euer Vorschlag** (`erg-20260924-b161-bildstrecke.md` §2, Blatt -03): Bestellung `render.passes: ["schoenbild" | "tiefe" | "material-id"]` oder `"alle"`; Rueckweg ein eigenes Ergebnisfeld `ebenen: [{kamera, art, datei, bedeutung}]` (nicht `images`); Dateien flach im Auftrag; eine bestellte, aber fehlende Ebene macht den Auftrag rot.

**Stand bei uns heute (Beleg):**

* Die Ebenen entstehen drueben und kommen nie zurueck, das steht in unserem eigenen Vertragskommentar (`render-result.ts:408-437`, Messung 17.09.2026) und in der Tabelle der offenen Zeilen (`vis-jobs.ts:896ff.`, Zeile 50b). **Wir haben damals ausdruecklich nichts gebaut**, weil ein Ebenenfeld ohne Erzeuger "ein Feld waere, das niemand fuellt". **Diese Bedingung ist mit eurem Vorschlag erfuellt**, wenn ihr zusagt, die Seite zu bauen.
* **Flache Dateinamen tragen bei uns:** Die Bruecke liefert Artefakte ueber `GET /jobs/{job_id}/artifacts/{name}` mit **einem** Segment (`main.py:1924-1928`); `/`, `\` und `..` im Namen werden abgewiesen (`main.py:559-561`), `__` im Namen geht.
* **Ein Vorbehalt zur Anzeige:** Tiefe als EXR laesst sich in unserer Oberflaeche nicht anzeigen (`BridgeBild.tsx` zeigt Bilder; ein EXR waere ein Download). Die normierte Tiefe als PNG und die Material-ID als PNG lassen sich anzeigen.

**Optionen:**

* **(1) Zusage wie vorgeschlagen.** Vertragsfelder `render.passes` (Bestellung, `render-scene.ts`) und `ebenen` (Ergebnis, `render-result.ts`), Bestellung im Render-Knoten, Ebenen an der Kuratierflaeche. Bau auf beiden Seiten. Loest Owner-Zuruf Zeile 50b ("mit allen passes und layers").
* **(2) Zusage in zwei Schritten (Empfehlung).** Schritt 1: nur der Vertrag und der Rueckweg (`passes`/`ebenen`), gegen ein echtes Beispiel-JSON von euch, mit Test; Anzeige nur als Liste der Dateien. Schritt 2: erst wenn Schritt 1 an einem echten Lauf belegt ist, die Anzeige in der Kuratierflaeche. Grund: unsere eigene Lehre (`lieferstatus`), dass ein Feld erst zaehlt, wenn ein Leser es zeigt und der Erzeuger es an einem echten Lauf gefuellt hat.
* **(3) Absage oder Zurueckstellen.** Begruendung waere eure eigene Angabe, dass es einen "nur Cycles"-Lauf noch nicht gibt (`vis.skip: true` liefert bei euch nichts). Dagegen: Die Ebenen entstehen laut euch bei jedem Lauf ohnehin.

**Empfehlung: (2).** Bedingungen, die wir daran knuepfen: (a) `bedeutung` ist **strukturiert**, kein Freitext (Tiefe traegt Grenzen in Metern, Material-ID eine Tabelle Farbe zu Name samt Nullfarbe; ein Beispiel-JSON von euch entscheidet die Form); (b) `ebenen` ist optional und ohne Vorgabe (ein fehlendes Feld heisst "nichts gesagt", nicht "keine Ebenen"); (c) "bestellt, aber fehlt" bildet sich auf den Kamera-Lieferstatus `fehlgeschlagen` mit Grund ab (`auf-20260923-155`, Posten 1), damit es **eine** Auskunft ueber Lieferung gibt und nicht zwei.

### Bauposten K4 (nur nach Entscheid)

* **Dateikreis:** `packages/kosmo-contracts/src/render-scene.ts` (`render.passes`), `packages/kosmo-contracts/src/render-result.ts` (`ebenen`), `packages/kosmo-contracts/test/contracts.test.ts`, spaeter `apps/kosmo-orbit/src/modules/vis/` (**UI-Lane**).
* **Abnahme:** Beispiel-JSON von euch parst und behaelt `ebenen`; eine bestellte, aber fehlende Ebene erscheint als nicht geliefert mit Grund; Dateinamen sind flach und ueber `get_artifact` abholbar.

---

## Zur Kenntnis: die sechs Blaetter vom 17.09.2026

Gelesen, kein Handlungsbedarf ausser den Textposten:

* **-01 Sonne (gebaut):** unsere Tabelle `FREMDNAHT` nachziehen, siehe K1.
* **-02 Stilreferenzen (nicht vorgesehen):** "Zeile 53 als offen, nicht bedienbar fuehren." Unser Eintrag steht in `BILDWEG_OFFEN` (Zeile "53"); Text an euren Stand anpassen (Textposten). Bei uns ist `style.refs` seit dem 04.09. aus dem Senden genommen.
* **-03 Paesse:** siehe K4.
* **-04 Einsetzen, -05 Maske begrenzt (nicht vorgesehen):** Zeile "57" und "58" in `BILDWEG_OFFEN` (`vis-jobs.ts:913`, `:924`) auf "nicht vorgesehen, gemessen" ziehen (Antwort `auf-20260921-129-antwort-bearbeitungsbereich.md`). Textposten.
* **-06 Flaechensuche (ueberholt, bestaetigt):** Bestaetigt. Unsere Flaechensuche rechnen wir selbst (`packages/kosmo-kernel/src/derive/bauteilmaske.ts`, eingebunden in `bild/bereich.ts`).

## Bauposten in der Reihenfolge, die wir vorschlagen

1. **K1** (dringlich: ein Demohaus mit Preset bleibt sonst liegen), zusammen mit dem Nachziehen der Tabellen `FREMDNAHT` und `BILDWEG_OFFEN`.
2. **K3** (eine Zeile, aber mit Byte-Diff der Goldens und eurer Bestaetigung zu Vorbehalt 1).
3. **K2** (Bruecke und Vertrag; wartet auf euer Beispiel-JSON).
4. **K4** erst nach Owner-Entscheid.

## Was nicht gemessen wurde

* `test_b161_weg_a.py`, den Abholer und den Puls selbst: liegen bei euch; wir vertrauen euren Angaben, nicht einer eigenen Messung.
* Ob eure Bildseite das Merkmal `transparenz` an BLEND misst (K3, Vorbehalt 1).
* Unsere Bruecke mit echtem Puls (kein Lauf, keine GPU in dieser Sitzung).

```
{"beantwortet_am": "2026-09-29"}
```
