import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/**
 * **KTabs brach Reiterbeschriftungen mitten im Wort** («Allge/mein»,
 * «Durchbr/üche», «Darste/llung» im Wand-Inspector bei 340 px, gefunden im
 * Paket K7 d1, 25.09.2026). UI-REGELN Regel 3: keine abgeschnittenen Wörter;
 * Regel 2: kein Text verlässt seine Box.
 *
 * Der Vertrag liegt im Baustein, nicht beim Verbraucher: `.k-tab` bricht nie
 * um (`white-space: nowrap`), und `.k-tabs` lässt einen Reiter, der nicht
 * mehr passt, in eine neue Zeile rücken (`flex-wrap: wrap`) — sonst würde
 * `nowrap` den Text nur aus der Leiste schieben statt ihn zu brechen.
 * Abschneiden (`text-overflow`, `overflow: hidden`) ist ebenso verboten.
 *
 * jsdom rechnet kein Layout; darum wird die Regel in `aura.css` selbst
 * geprüft, wie in den übrigen Wächtern dieses Pakets.
 */
const css = readFileSync(fileURLToPath(new URL('../src/aura.css', import.meta.url)), 'utf8');

function block(selektor: string): string {
  const re = new RegExp(`(^|\\n)${selektor.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\{([^}]*)\\}`);
  const m = css.match(re);
  if (!m) throw new Error(`Regel ${selektor} fehlt in aura.css`);
  return m[2]!;
}

describe('KTabs — kein Wortbruch in der Beschriftung', () => {
  it('.k-tab bricht nie um', () => {
    expect(block('.k-tab')).toMatch(/white-space:\s*nowrap/);
  });
  it('.k-tabs rückt einen Reiter, der nicht passt, in eine neue Zeile', () => {
    expect(block('.k-tabs')).toMatch(/flex-wrap:\s*wrap/);
  });
  it('Gegenfall: nichts wird abgeschnitten', () => {
    for (const s of ['.k-tab', '.k-tabs']) {
      expect(block(s)).not.toMatch(/text-overflow|overflow:\s*hidden|overflow-x:\s*hidden/);
    }
  });
});

/**
 * Der fette aktive Reiter springt nicht (Vorschlag UI-Worker, Lieferung 6,
 * 30.09.2026): die Beschriftung reserviert die Breite ihrer fetten Fassung
 * vorab ueber ein unsichtbares `::after` mit `attr(data-text)`. Ohne das
 * wird ein Reiter beim Aktivieren breiter, und die Leiste rueckt nach.
 */
describe('KTabs — aktiver Reiter springt nicht', () => {
  it('.k-tab-text reserviert die fette Breite', () => {
    const regel = block('.k-tab-text::after');
    expect(regel).toMatch(/content:\s*attr\(data-text\)/);
    expect(regel).toMatch(/font-weight:\s*var\(--k-gewicht-stark\)/);
    expect(regel).toMatch(/visibility:\s*hidden/);
  });
  it('tabs.tsx traegt die Beschriftung als data-text', () => {
    const tsx = readFileSync(fileURLToPath(new URL('../src/tabs.tsx', import.meta.url)), 'utf8');
    expect(tsx).toMatch(/className="k-tab-text"\s+data-text=\{item\.label\}/);
  });
});
