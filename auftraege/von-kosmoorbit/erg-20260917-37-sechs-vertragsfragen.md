# erg-20260917-37 — `auf-20260823-37` (an: cloud): sechs Vertragsfragen — F1 ist geloest, F6 ist gegenstandslos geworden

**Stand 17.09.2026:** erledigt — woran gemessen: alle sechs Fragen sind frisch am heutigen
Stand von `packages/kosmo-contracts/src/render-result.ts` und
`packages/kosmo-contracts/src/render-scene.ts` nachgeprueft (Lesen und Grep, kein Testlauf
— siehe Fussnote zur Messdisziplin am Ende). Fuenf Punkte sind im Vertrag umgesetzt und mit
Codezeile belegt; einer (F4, der Hochskalierer selbst) liegt ausserhalb dieses
Vertragspakets und wird als solcher benannt, nicht als offen verschwiegen. Es gibt in
diesem Blatt **keinen** verbleibenden Owner-Entscheid — die beiden, die es gab (F1b-Status-Feld,
F6-Referenzweg), sind inzwischen entschieden und im Code sichtbar.

Hinweis zur Vorgeschichte: Auf dieses Blatt liegt bereits eine Antwort vom 03.09.2026 vor
(`auftraege/ergebnisse/auf-20260823-37.json`), die laut `docs/AUFTRAG-B118-...md` am
08./09.09.2026 in euer eigenes Repo uebertragen wurde. Diese Datei hier ersetzt sie nicht,
sondern misst denselben Vertrag **elf Tage spaeter erneut nach** — zwei Punkte (F1b, F6)
haben sich seither veraendert.

---

## F1 — null im QA-Schema (das Dringendste)

**Antwort: Ja, seit dem 23.08.2026 (also seit dem Tag eures Auftrags).** Sowohl Weg (b) als
auch Weg (c) sind gebaut: `geometry_fidelity` und `spearman` duerfen als `null` **und** als
ganz fehlender Schluessel ankommen.

Beleg:
```
sed -n '218,226p' packages/kosmo-contracts/src/render-result.ts
```
zeigt
```ts
geometry_fidelity: z.number().nullable().optional(),
spearman: z.number().nullable().optional(),
geom_iou: z.number().nullable().optional(),
threshold: z.number().nullable().default(0.65),
status: GeometryStatus.optional(),
```
— `nullable()` nimmt `null` an, `optional()` nimmt einen fehlenden Schluessel an. Dieselbe
Regel gilt fuer **jedes** Zahlenmass in diesem Block (auch `rho_maske`, `kantenanteil`,
`kante`, `paarurteil.rho_maske`). Ein passender Test liegt vor:
```
grep -n "GANZ FEHLEN" packages/kosmo-contracts/test/contracts.test.ts
```
→ Zeile 1400, `it('F1 (c): geometry_fidelity/spearman duerfen als Schluessel GANZ FEHLEN, nicht nur null sein', ...)`.

## F1b — die drei Zustaende (gemessen / nicht gemessen / nicht zustaendig)

**Antwort: Euer bevorzugter Weg (a) ist inzwischen gebaut — das ist neu seit unserer
letzten Antwort vom 03.09.2026, damals stand hier noch «offen».**

```
sed -n '196,226p' packages/kosmo-contracts/src/render-result.ts
```
zeigt das Enum `GeometryStatus = z.enum(['measured', 'not_measured', 'not_applicable'])`
und das Feld `status: GeometryStatus.optional()` in `GeometryQA` — mit euren drei
Namen wortgleich uebernommen. **Kein Default**: ein fehlendes `status`-Feld heisst «keine
Aussage zu dieser Unterscheidung getroffen», nicht `measured`. Ihr koennt den Zustand
`not_applicable` ab sofort senden; sendet ihr ihn nicht, aendert sich fuer euch nichts
gegenueber heute.

Test, der den dritten Zustand mit eurem eigenen Beispiel (Nachbargebaeude statt Himmel)
durchspielt:
```
grep -n "not_applicable erlaubt weiterhin null-Zahlenfelder" packages/kosmo-contracts/test/contracts.test.ts
```
→ Zeile 1450.

**Ehrlich dazu:** Der Vertrag kann den dritten Zustand jetzt annehmen und weitergeben.
Ob die Oberflaeche (Kuratier-Ansicht) ihn schon **anzeigt** — also ob ein Bild mit
`status: 'not_applicable'` sichtbar anders dargestellt wird als eines mit `not_measured`
— wurde fuer dieses Blatt nicht geprueft; das liegt ausserhalb des Dateikreises
(`kosmo-contracts`/`kosmo-ai`/`tools/homestation-bridge`), den dieser Auftrag vorgibt.

## F2 — render.sun: Nullpunkt von azimuth, Bedeutung von elevation

**Antwort, unveraendert seit dem 24.08.2026 (einen Tag vor eurem Auftrag bereits
festgelegt):**
- `azimuth`: Grad, **im Uhrzeigersinn ab Norden** (0=Norden, 90=Osten, 180=Sueden,
  270=Westen). **Nicht** gegen die +Y-Achse der Szene gemessen.
- `elevation`: Grad **ueber dem Horizont**; negativ = unter dem Horizont (Nacht).

Beleg:
```
sed -n '141,169p' packages/kosmo-contracts/src/render-scene.ts
```
Der Code-Kommentar leitet die Konvention aus den drei Cycles-Presets her (nicht erfunden):
`entwurf-schnell` 180°/45° = "Flaches Mittagslicht" (180° = Sueden bestaetigt die
Nord-Zaehlung im Uhrzeigersinn), `nacht` 0°/**-8°** = "Sonne unter dem Horizont" (bestaetigt,
dass `elevation` der Stand ueber dem Horizont ist, nicht ein Einfallswinkel).

**Neu seit dem 16.09.2026, ausserhalb eurer Frage, aber am selben Feld:** `render.sun`
traegt jetzt zusaetzlich `staerke`, `kelvin`, `winkelGrad` (Staerke/Farbtemperatur/
Winkeldurchmesser der Sonne), alle drei optional ohne Vorgabewert. Der Code sagt selbst
ehrlich dazu: in diesem Repo liest sie **niemand** — nur der ferne Cycles-Schritt auf der
HomeStation. Falls das fuer euch relevant ist: `sed -n '170,203p' packages/kosmo-contracts/src/render-scene.ts`.

## F3 — vis.skip: was soll es bewirken?

**Antwort: Seit dem 01.09.2026 gebaut, der dritte Zustand fehlt hier nicht mehr.** Neues
Feld `RenderResult.lieferstatus`:
```
sed -n '296,341p' packages/kosmo-contracts/src/render-result.ts
```
`Lieferstatus = z.enum(['geliefert', 'uebersprungen', 'fehlgeschlagen'])`, additiv, Default
`'geliefert'` (jeder alte Record ohne dieses Feld WAR tatsaechlich eine Lieferung).
`lieferstatus_grund` ist **Pflicht**, sobald `lieferstatus` nicht `'geliefert'` ist — per
`superRefine` erzwungen:
```
sed -n '396,406p' packages/kosmo-contracts/src/render-result.ts
```
Test:
```
grep -n "lieferstatus trennt uebersprungen" packages/kosmo-contracts/test/contracts.test.ts
```
→ Zeile 469.

## F4 — vis.upscale: Bedeutung geklaert, Hochskalierer selbst nicht angeschlossen

**Zwei getrennte Antworten, weil es zwei getrennte Fragen sind:**

**Die Bedeutung ist erledigt** (festgelegt 01.09.2026, im Code dokumentiert):
```
sed -n '377,401p' packages/kosmo-contracts/src/render-scene.ts
```
1. Die Geometrie-QA misst **immer** am urspruenglichen Bild, nie am hochskalierten — ein
   Hochskalierer erfindet Bildinhalt, die QA misst Bildinhalt.
2. Ein Hochskalierer braucht eine permissive Lizenz (MIT, Apache-2.0, BSD, MPL-2.0 — kein
   GPL, keine NonCommercial-Klausel).

**Die Umsetzung (ein tatsaechlicher Hochskalierer) ist NICHT HIER.** `vis.upscale: true`
liefert heute dasselbe wie `false` — unveraendert seit der letzten Messung. Ein
Hochskalierer waere Modell-/Inferenzcode, nicht Vertragscode; er gehoert nicht in
`kosmo-contracts` und ist auch sonst in diesem Dateikreis nicht auffindbar:
```
grep -rn "upscal" tools/homestation-bridge/kosmo_bridge/*.py
```
→ kein Treffer ausser Wortnennungen in Kommentaren/Konfiguration, kein lauffaehiger
Hochskalierungs-Code.

## F5 — style.mode: die Stil-QA laeuft nicht

**Antwort, unveraendert seit dem 01.09.2026:** bewusste Entscheidung, kein Bau-Ruecktand.
```
sed -n '296,311p' packages/kosmo-contracts/src/render-scene.ts
```
`mode` fuehrt `'none' | 'redux' | 'ipadapter' | 'lora' | 'lineart'`. `'none'` und
`'lineart'` sind gebaut (Lineart erzwingt `vis.skip: true`). `'redux'`, `'ipadapter'`,
`'lora'` sind bestellbar, wirken aber heute **nicht anders** als `'none'` — es fehlt ein
eigenes Referenzset fuer die Stil-QA bei euch, ausdruecklich als eure Entscheidung benannt,
nicht als unsere Luecke.

## F6 — style.refs: **gegenstandslos geworden**

**Das Feld existiert nicht mehr.** Es gab `style.refs` vom 01.09. bis zum 04.09.2026; seither
ist es **zurueckgezogen** (Owner-Entscheid 04.09.2026, "B97 Posten A"):
```
grep -n "ZURUECKGEZOGEN 04.09.2026" packages/kosmo-contracts/src/render-scene.ts
```
→ Zeile 312, mit ausfuehrlicher Begruendung im Kommentar: im ganzen Baum gab es genau EINEN
Erzeuger eines `style`-Objekts, und der schrieb `refs: []` fest verdrahtet — niemand las das
Feld, niemand fuellte es. Ein Feld, das Zeichenketten annimmt und nichts bewirkt, ist
schlechter als kein Feld.

**Fuer euch heisst das:** eure Frage F6 ("welcher Weg fuer fremde Referenzbilder") ist damit
nicht beantwortet, sondern **vom Tisch** — es gibt derzeit keinen Ort im Vertrag, an dem
ihr Referenzbilder ueberhaupt ablegen koenntet, auch keinen leeren. Zod ist hier non-strict
(kein `.strict()`): schickt ihr trotzdem `style.refs`, wird es beim Parsen still
abgestreift, kein Fehler, keine Wirkung. Wer Stilreferenzen wirklich will, muss die Frage
**neu** stellen — der Code selbst nennt zwei fehlende Voraussetzungen (ein Zustellweg fuer
fremde Bilder UND ein Leser auf der Bildseite), beides gemeinsam mit KosmoOrbit zu klaeren.

---

## Was ausdruecklich OWNER-ENTSCHEID war und jetzt entschieden ist

- **F1b** (Status-Feld `measured`/`not_measured`/`not_applicable`): am 03.09.2026 vom
  Owner entschieden ("euer bevorzugter Weg a"), inzwischen gebaut — kein offener Punkt mehr.
- **F6** (`style.refs`): am 04.09.2026 vom Owner entschieden — **entfernt**, nicht gebaut.
  Auch das ist kein offener Punkt mehr, nur ein anderes Ergebnis als erwartet.

## Messdisziplin — was diese Antwort NICHT ist

Kein Testlauf: die Auflage fuer diese Sitzung verbietet `npm test`/`npm run build`, weil ein
anderes Paket parallel im selben Baum arbeitet. Alle Aussagen oben stammen aus dem
Lesen des Quelltexts und aus `grep`/`sed`, nicht aus einem gruenen Testergebnis. Wo ein
Test zitiert wird, ist das ein Verweis auf **vorhandenen, gelesenen** Testcode (105
`it()`-Bloecke in `contracts.test.ts`, Stand heute), keine Behauptung, dass er gerade
gelaufen und gruen ist.
