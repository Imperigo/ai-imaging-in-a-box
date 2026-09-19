# meldung-orbit-20260919-01 — drei Nachtraege, und eine Berichtigung an euch

**Stand 19.09.2026:** erledigt — woran gemessen: alle drei Punkte sind am
heutigen Stand im Code nachgeprueft (Befehl und Fundstelle je Punkt unten) und
tragen den vollen Commit-Hash ihrer Entstehung. Was NICHT gemessen ist: ob ihr
diese Meldung erreicht — der Abholweg ist derselbe wie am 17.09.2026
(`meldung-orbit-20260917-01`), Zweig und Ordner unveraendert.

Keine Rueckfrage, keine Arbeit fuer euch. **Eine unserer frueheren Antworten
steht falsch bei euch im Repo**, und zwei Sachen sind laengst gebaut, ohne dass
wir es je gesagt haben. Das holen wir hier nach.

---

## 1 · BERICHTIGUNG: `CameraSpec.referenzpunkt` WIRD gesetzt

Unsere Antwort auf `auf-20260901-68` sagt ausdruecklich, der Kern **setze das
Feld noch nicht**. Das stimmt nicht mehr — und zwar schon seit dem Tag, an dem
wir es geschrieben haben.

Heute nachgemessen:
`grep -n "referenzpunkt" packages/kosmo-kernel/src/derive/kamera.ts`
→ Zeile 308: `referenzpunkt: eingangGeschossElevationMm !== null ? 'okff' : 'huellbox_unterkante'`

Gebaut mit Commit `7297192e4ae6b43fd6527593d7e9928a6e61c7d6` (03.09.2026).
Gesamtnachweis liegt bei uns in `test/n1-kamera-referenzpunkt.test.ts`.

**Wenn ihr auf unsere alte Aussage hin etwas gebaut oder unterlassen habt,
ist das unser Fehler, nicht eurer.** Die Antwort war beim Schreiben schon
ueberholt; wir haben sie nicht nachgezogen.

## 2 · NACHTRAG: `RenderScene.gelaende` ist gebaut — der zugesagte Beleg kommt hier

In derselben Runde hatten wir zu `auf-20260901-67` geschrieben, der Beleg «R5»
werde nachgereicht. Er wurde nie nachgereicht.

Heute nachgemessen:
`grep -n "gelaende" packages/kosmo-contracts/src/render-scene.ts`
→ Zeile 529: `gelaende: z.boolean().nullable().optional()`

Gebaut mit Commit `9693bff5dcf921f5a4a9eb7af558af355292a874` (03.09.2026).
Das Feld ist dreiwertig gemeint: `true` / `false` / `null` (= nicht geprueft) —
die Unterscheidung steht im Kopfkommentar derselben Datei.

## 3 · NACHTRAG: der Bruecken-Fehler, der euren IFC-Weg blockierte, ist behoben

Aus eurer Sicht war das vermutlich der aergerlichste Punkt: unsere
HomeStation-Bruecke hat an drei Endpunkten `geometry.format` **unbedingt auf
`"glb"` zurueckgebogen** — egal, was hochgeladen wurde. Damit war der IFC- und
Innenraum-Weg strukturell blockiert, und es sah von aussen so aus, als
ignorierten wir euer Format.

Behoben mit Commit `fe20a8afc97c7988d655fbc0620cacf10a31bac9` (11.09.2026).
Heute nachgemessen in `tools/homestation-bridge/kosmo_bridge/main.py`:
die Formatliste fuehrt jetzt `("glb", "gltf", "fbx", "blend", "ifc")`, und der
Kopfkommentar der Datei benennt den alten Fehler ausdruecklich, statt ihn
stillschweigend verschwinden zu lassen.

**Das ist seit acht Tagen behoben und wir haben es euch nicht gesagt.** Wenn
ihr seither um diesen Fehler herumgebaut habt, koennt ihr den Umweg zurueckbauen.

---

## Warum das alles erst heute kommt

Wir haben am 19.09.2026 zum ersten Mal systematisch durchgesehen, was in den
19 Auftragsblaettern trotz Antwort noch offen ist. Dabei kam heraus: **26 Punkte
sind offen, vierzehn davon bei uns** — und drei davon waren keine Arbeit mehr,
sondern nur eine Nachricht, die nie geschrieben wurde.

Beantwortet ist nicht abgeschlossen. Das war unser blinder Fleck, und die
Schlussfolgerung daraus ist eine Aufgabe an uns, nicht an euch.

---

**Stand 19.09.2026 — erledigt**: die Berichtigung und die zwei Nachtraege sind
geschrieben und liegen auf dem bekannten Abholweg; die uebrigen elf offenen
Punkte auf unserer Seite arbeiten wir nacheinander ab.
