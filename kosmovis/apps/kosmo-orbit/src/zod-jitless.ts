/**
 * CSP-Härtung (Serie I / Batch B2, R6) — deaktiviert Zods internen
 * eval-Schnellpfad-Test, BEVOR irgendein Command-Zod-Schema gebaut wird.
 *
 * `zod` v4 probiert beim Bau eines Objekt-Schemas einmalig `new Function("")`,
 * um zu entscheiden, ob es einen kompilierten («fast») oder einen
 * interpretierten Parse-Pfad nimmt (`node_modules/zod/v4/core/util.js`,
 * `allowsEval`). Unter unserer strikten CSP (`script-src 'self'`, kein
 * `'unsafe-eval'`) wirft dieser Test intern — Zod fängt den Fehler ab und
 * fällt sauber auf den interpretierten Pfad zurück (funktional folgenlos),
 * ABER der Browser meldet den geblockten `Function`-Aufruf trotzdem als
 * `securitypolicyviolation`. Zod kennt dieses Muster genau (siehe Kommentar
 * in `util.js`: „strict CSPs report the caught new Function as a
 * securitypolicyviolation“) und bietet dafür `z.config({ jitless: true })` —
 * das überspringt den Test komplett, keine Konsolen-Meldung mehr, keine
 * CSP-Lockerung nötig.
 *
 * WICHTIG: Diese Datei muss in `main.tsx` vor JEDEM Import stehen, der ein
 * Zod-Objektschema baut — «vor `./App`» ist zu schwach formuliert und hat
 * genau einmal versagt: `import './state/regelwissen-laden'` (P-REGELWERK,
 * 18.08.2026) stand davor, zog `@kosmo/kernel` und damit dessen
 * Command-Schemas, und die Probe lief. Zod merkt sich das Ergebnis in einem
 * `cached()`-Getter (`node_modules/zod/v4/core/util.js:145`), gelesen bei
 * der Schema-KONSTRUKTION (`core/schemas.js:971`) — ein späteres
 * `z.config({ jitless: true })` kommt darum zu spät, obwohl der Parse-Pfad
 * danach korrekt interpretiert. Messung: `docs/BEFUND-CSP-ZODPROBE.md`.
 *
 * ESM wertet Geschwister-Imports in Quelltextreihenfolge vollständig aus,
 * bevor der nächste an der Reihe ist; nur so läuft dieser Aufruf zuerst.
 * Einzige Ausnahme davor: `./shell/stream-luecke` — die Datei hat KEINE
 * Imports (baut also kein Schema) und muss ihrerseits vor allem laufen.
 */
import { z } from 'zod';

z.config({ jitless: true });
