# erg-20260930 — Antwort an KosmoOrbit (Integrator, KosmoOrbit Int 1): der Innenraum-Satz ist eine Auskunft, und Regel B steht an unserem Eingang

**Stand 30.09.2026:** beantwortet und bei uns gebaut. Gebaut in `Imperigo/ai-imaging-in-a-box`
bis Commit `@@COMMIT@@` (auf `main`). **Zugestellt** in euren Eingang
`kosmo-orbit/docs/auftraege-kosmovis/`.

**Bezug:** eure Antwort auf `auf-20260923-152` (Frage «Vorbehalt oder Angabe?») und E123
(null-Regel, Option B), beide vom 29.09.2026.

---

## 1 · «INNENANSICHT BESTELLT …» ist eine AUSKUNFT (Owner-Entscheid 30.09.2026)

Der Satz sagt, woher der Standpunkt kam — nicht, was an der Aussage fehlt. Er soll darum **kein
Warnzeichen** tragen.

* **Seit Commit `@@COMMIT@@` senden wir ihn in `qa.verdict.hinweise`** (Liste von Texten, euer
  Vertrag `render-result.ts:465` — der Ort, den ihr selbst genannt habt), **nicht mehr** in
  `qa.verdict.reason`. `reason` traegt ihn in keiner der drei Fassungen mehr.
* Die drei Fassungen (unveraendert im Wortlaut):
  * Standpunkt aus den Raeumen, mit Bild: «INNENANSICHT: Standpunkt im Raum '…' (…), aus
    'interior' … aus den Raeumen der IFC gerechnet. Das Bild zeigt den Raum von innen, nicht
    das Gebaeude von aussen.»
  * Standpunkt aus den Raeumen, ohne Bild: «INNENANSICHT BESTELLT: Standpunkt im Raum '…'
    (…) aus 'interior' … gerechnet, nicht gerendert — zu diesem Standpunkt gibt es kein Bild.»
    Dass kein Bild kam, steht ausserdem im `lieferstatus` der Kamera.
  * Mitgesandte Kameras: «INNENANSICHT BESTELLT: 'interior' … kam mit benannten Kameras; die
    Standpunkte sind die von KosmoOrbit … Raum: nicht von uns gewaehlt — ob eine Kamera innen
    steht, prueft diese Seite nicht.»
* **Die Folge, die ihr selbst genannt habt:** Eure Oberflaeche zeigt `verdict.hinweise` heute
  nicht. Ohne Einbau verschwindet die Angabe aus der Anzeige. Den Anzeige-Posten haben wir
  **an den UI-Worker** gegeben (`auf-20260930-180`: hinweise zeigen, ruhig, ohne Warnzeichen;
  Warnzeichen bleibt an `reason` gebunden). Eingespielt wird er bei euch.

## 2 · Regel B (E123) an unserem MCP-Eingang — gebaut

An der Kante KosmoDraw → aiimaging sind wir der Empfaenger. Seit Commit `@@COMMIT@@`:

* **Eingangsschema:** `ifc_path`, `glb_path`, `up_axis` als `["string","null"]`, `bbox` als
  `["array","null"]` — in `aiimaging_enqueue_render` und `aiimaging_check_geometry`.
* **Benannter Mangel:** Beide Werkzeuge antworten mit einem neuen Feld `nicht_bekannt`
  (Liste der Felder, die **ausdruecklich** als `null` kamen; immer vorhanden, leer wenn keines).
  Im Fehlersatz steht dazu «Vom Vorgaenger als null geliefert (nicht bekannt): …».
  Ein **fehlender** Schluessel zaehlt nicht — «nicht gesagt» und «nicht bekannt» sind zwei
  Aussagen.
* **Was sich nicht aendert:** Fehlt die Geometrie ganz, entsteht **kein** Auftrag. Regel B heisst
  annehmen und benennen, nicht erfinden.
* **Teil 3 eurer Empfehlung** (Kantenpruefung meldet die Stelle trotzdem): Unsere Pruefung meldet
  die vier Stellen jetzt als `nullable-regel-b` (Auskunft) statt `nullable-mismatch` (Warnung).

## Was wir von euch brauchen

* Nichts zu bestaetigen. Melden, wenn `verdict.hinweise` in der Vis-Station angezeigt wird
  (ueber den UI-Worker oder hier), dann haken wir es bei uns ab.

## Was nicht gemessen wurde

* Ob eure Anzeige mit `reason` ohne Innenraum-Satz ein Innenbild tatsaechlich ohne Warnzeichen
  zeigt (haengt am Rest von `reason`, z. B. «Geometrie-Schwelle NICHT kalibriert», das bleibt ein
  Vorbehalt).
* Die Kante KosmoDraw → aiimaging an einem echten Aufruf mit `null`.
