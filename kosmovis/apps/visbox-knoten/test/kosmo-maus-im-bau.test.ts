import { readFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import postcss, { type Rule } from 'postcss';
import { describe, expect, it } from 'vitest';

/**
 * VISBOX-EIGEN (Befund 305 B1, 21.10.2026): Im Bau der Knotenansicht fehlten Leiste «… bedient —
 * Esc beendet», Figur am Punkt und die gestrichelten Sperrzonen. Die Regeln standen in
 * `kosmo-maus.css`, kamen im Bau aber nur verschachtelt unter `.vis-raster-gross-urteil` an: In
 * `vis-visual.css` fehlte nach dieser Regel die schliessende Klammer, und der Bau hängt alle
 * CSS-Dateien hintereinander. Behoben in KosmoOrbit (Zweig claude/kosmovis-kopf), Probe dort
 * `kv-css-geschlossen.test.ts`.
 *
 * Diese Probe liest den **Bau selbst** (`dist/`): Die Regeln der KosmoMaus stehen dort auf oberster
 * Ebene — die Leiste fest oben in der Mitte, die Figur fest an ihrem Punkt, der Löschen-Knopf mit
 * gestricheltem Rahmen. Ob sie im Fenster sichtbar sind,
 * misst die HomeStation im Browser (Messauftrag nach 305).
 */
const DIST = resolve(process.cwd(), 'dist');

function bauCss(): string {
  const html = readFileSync(resolve(DIST, 'index.html'), 'utf-8');
  const namen = [...html.matchAll(/href="\.\/assets\/([^"]+\.css)"/g)].map((m) => m[1]);
  expect(namen.length, 'dist/index.html nennt kein CSS — python3 tools/knoten_bau.py').toBeGreaterThan(0);
  const vorhanden = new Set(readdirSync(resolve(DIST, 'assets')));
  return namen.map((n) => {
    expect(vorhanden.has(n), `dist/assets/${n} fehlt`).toBe(true);
    return readFileSync(resolve(DIST, 'assets', n), 'utf-8');
  }).join('\n');
}

function obersteRegeln(css: string): Map<string, Rule> {
  const regeln = new Map<string, Rule>();
  postcss.parse(css).each((k) => {
    if (k.type === 'rule') regeln.set(k.selector.replace(/\s+/g, ' ').replace(/["']/g, '').trim(), k);
  });
  return regeln;
}

function wert(regel: Rule | undefined, eigenschaft: string): string | undefined {
  let w: string | undefined;
  regel?.walkDecls(eigenschaft, (d) => {
    w = d.value;
  });
  return w;
}

describe('KosmoMaus im Bau der Knotenansicht (Befund 305 B1)', () => {
  const css = bauCss();
  const oben = obersteRegeln(css);

  it('die Leiste steht auf oberster Ebene, fest oben in der Mitte', () => {
    const leiste = oben.get('.kosmo-maus-leiste');
    expect(leiste, '.kosmo-maus-leiste fehlt auf oberster Ebene — eine offene Klammer davor?').toBeDefined();
    expect(wert(leiste, 'position')).toBe('fixed');
    expect(wert(leiste, 'top')).toBeDefined();
    expect(wert(leiste, 'left')).toBe('50%');
  });

  it('die Figur steht auf oberster Ebene und fest (ihr Punkt kommt als transform)', () => {
    const figur = oben.get('.agent-figur');
    expect(figur).toBeDefined();
    expect(wert(figur, 'position')).toBe('fixed');
  });

  it('die Sperrzonen sind gestrichelt, «Node löschen» (SVG) über sein Rahmen-Rechteck', () => {
    const zonen = [...oben.entries()].find(([s]) => s.startsWith('[data-kosmo-maus-bedient] :is('));
    expect(zonen, 'die Sperrzonen-Regel fehlt auf oberster Ebene').toBeDefined();
    expect(wert(zonen![1], 'outline')).toMatch(/dashed/);
    const rahmen = oben.get('[data-kosmo-maus-bedient] [data-testid=node-loeschen] .vis-node-knopf-rahmen');
    expect(rahmen).toBeDefined();
    expect(wert(rahmen, 'stroke-dasharray')).toMatch(/^4\s*3$/);
  });

  it('nichts der KosmoMaus ist unter einer fremden Regel verschachtelt', () => {
    const fremd: string[] = [];
    postcss.parse(css).walkRules((r) => {
      if (r.parent?.type === 'rule' && /kosmo-maus|agent-figur/.test(r.selector)) fremd.push(r.selector);
    });
    postcss.parse(css).walkRules(/^\.vis-raster-gross-urteil .*kosmo-maus/, (r) => {
      fremd.push(r.selector);
    });
    expect(fremd).toEqual([]);
  });
});
