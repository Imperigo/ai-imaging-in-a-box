import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { RenderResult, renderResultMaengel, unbekannteFelder } from '../src';

/**
 * P-LIZENZMARKE Schritt 1 gegen ein ECHTES Ergebnis: ein Qwen-Image-2.1-Lauf
 * der Gegenseite, unveraendert abgelegt als `fixtures/qwen21-render-result.json`
 * (Quelle `docs/auftraege-kosmovis/meldung-20261006-qwen21-render-result.json`,
 * Blatt `meldung-20261006-kosmovis-qwen21-echtes-ergebnis.md`). Bisher stand
 * die Marke nur an von Hand gebauten Beispielen.
 *
 * Bedeutung der Marke (Antwortblatt `antwort-20260930-int1-an-kosmovis.md` F2):
 * `true` heisst «die Lizenzfrage dieses Bildwegs ist OFFEN», frei heisst: Feld
 * fehlt. Darum passt `true` neben `Qwen Research License Agreement` — kein
 * Widerspruch. Ob die Marke eine Veroeffentlichung sperrt, ist Schritt 2.
 */
const echt = JSON.parse(
  readFileSync(fileURLToPath(new URL('./fixtures/qwen21-render-result.json', import.meta.url)), 'utf8'),
) as Record<string, unknown>;

describe('echtes Qwen-2.1-Ergebnis (KosmoVis, 06.10.2026)', () => {
  it('parst, und nichts wird abgestreift', () => {
    const r = RenderResult.parse(echt);
    expect(unbekannteFelder(echt, r)).toEqual([]);
  });

  it('die Lizenzmarke kommt als true an und ergibt keinen Mangel', () => {
    const r = RenderResult.parse(echt);
    expect(r.engine_license_open).toBe(true);
    expect(r.engine_used).toBe(echt.engine_used);
    expect(r.engine_license).toBe(echt.engine_license);
    expect(renderResultMaengel(r).filter((m) => m.startsWith('engine_license_open'))).toEqual([]);
  });

  it('Gegenprobe: dasselbe Ergebnis mit false wird als benannter Mangel gemeldet, nicht abgewiesen', () => {
    const r = RenderResult.parse({ ...echt, engine_license_open: false });
    expect(renderResultMaengel(r)).toContain('engine_license_open: false gemeldet, der Vertrag kennt nur true');
  });
});
