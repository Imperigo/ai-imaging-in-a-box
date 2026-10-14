import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { boot, orbit } from '../src/tokens';

/**
 * Owner-Entscheid 01.10.2026: «Die blasse graue Nebenschrift … soll überall
 * etwas heller werden» — im dunklen Thema (`orbit`) lag `--k-ink-faint`
 * (#7f8695) auf getoenten Kacheln bei 3.6:1, unter 4.5:1 fuer kleine Schrift
 * (Farbprobe 30.09.2026, gemessen am gezeichneten Bild: Paketwahl-Kachel
 * rgb(35,49,58), Kopfleiste rgb(34,37,42), heller Grau-Grund rgb(44,48,56)).
 *
 * Diese Probe haelt den Wert gegen ALLE gemessenen Gruende ueber 4.5:1 und
 * prueft, dass `aura.css`, `tokens.ts` und die Startsequenz dieselbe Zahl
 * tragen. Rot vor gruen: mit #7f8695 rot (3.66 / 4.21 / 3.62).
 */

const GRUENDE: Record<string, [number, number, number]> = {
  'Paketwahl-Kachel': [35, 49, 58],
  'Kopfleiste (Sync-Pille)': [34, 37, 42],
  'heller Grau-Grund': [44, 48, 56],
  raised: [26, 30, 39],
  surface: [20, 23, 31],
  'hellster Grund 11.09.': [28, 31, 37],
};

const hex = (s: string): [number, number, number] => [1, 3, 5].map((i) => parseInt(s.slice(i, i + 2), 16)) as [number, number, number];
const lum = (c: [number, number, number]) => {
  const [r, g, b] = c.map((v) => {
    const x = v / 255;
    return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const kontrast = (a: [number, number, number], b: [number, number, number]) => {
  const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p) as [number, number];
  return (x + 0.05) / (y + 0.05);
};

const aura = readFileSync(new URL('../src/aura.css', import.meta.url), 'utf8');
function orbitWert(name: string): string {
  // Der Block selbst (Zeilenanfang), nicht die Erwaehnungen in Kommentaren davor.
  const anfang = aura.search(/^\[data-theme='orbit'\] \{/m);
  const block = aura.slice(anfang, aura.indexOf('\n}', anfang));
  return block.match(new RegExp(`--${name}:\\s*(#[0-9a-fA-F]{6})`))![1]!.toLowerCase();
}

describe('Nebenschrift im dunklen Thema', () => {
  it('erreicht 4.5:1 auf jedem gemessenen Grund', () => {
    const farbe = hex(orbitWert('k-ink-faint'));
    for (const [name, grund] of Object.entries(GRUENDE)) {
      expect(kontrast(farbe, grund), name).toBeGreaterThanOrEqual(4.5);
    }
  });

  it('bleibt leiser als die zweite Textstufe (ink-soft)', () => {
    expect(lum(hex(orbitWert('k-ink-faint')))).toBeLessThan(lum(hex(orbitWert('k-ink-soft'))));
  });

  it('dieselbe Zahl in aura.css, tokens.ts und der Startsequenz', () => {
    const wert = orbitWert('k-ink-faint');
    expect(orbit.inkFaint.toLowerCase()).toBe(wert);
    expect(boot.schriftFaint.toLowerCase()).toBe(wert);
    expect(aura.match(/--k-boot-schrift-faint:\s*(#[0-9a-fA-F]{6})/)![1]!.toLowerCase()).toBe(wert);
  });
});
