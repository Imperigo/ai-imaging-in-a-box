import { describe, expect, it } from 'vitest';
import { RenderResult, RenderScene } from '../src';

/**
 * Owner-Auftrag 20.10.2026 (ueber LW, KosmoVis 0.3.2): schnelle KI-Vorschau
 * noch in v0.1.9. `vis.guete` 'vorschau' | 'voll'; fehlt das Feld, rechnet die
 * Gegenseite voll. Zusammen mit `skip` abgewiesen. Das Ergebnis traegt `guete`
 * oben, `engine_used` nennt das gerechnete Modell.
 */

const SZENE = { geometry: { path: 'model/model.glb', format: 'glb' }, out: 'out' } as const;
const ERGEBNIS = { job_id: 'vis-g-1', images: ['renders/a.png'], qa: { verdict: { passed: true } } };

describe('vis.guete im Auftrag', () => {
  it('ohne Feld: kein guete im Auftrag (alte Auftraege bleiben gleich)', () => {
    expect('guete' in RenderScene.parse(SZENE).vis).toBe(false);
  });

  it('vorschau und voll kommen unveraendert an', () => {
    expect(RenderScene.parse({ ...SZENE, vis: { guete: 'vorschau' } }).vis.guete).toBe('vorschau');
    expect(RenderScene.parse({ ...SZENE, vis: { guete: 'voll' } }).vis.guete).toBe('voll');
  });

  it('unbekannter Wert wird abgewiesen', () => {
    expect(RenderScene.safeParse({ ...SZENE, vis: { guete: 'schnell' } }).success).toBe(false);
  });

  it('zusammen mit skip abgewiesen, Pfad vis.guete', () => {
    const r = RenderScene.safeParse({ ...SZENE, vis: { guete: 'vorschau', skip: true } });
    expect(r.success).toBe(false);
    expect(r.success ? [] : r.error.issues.map((i) => i.path.join('.'))).toContain('vis.guete');
  });
});

describe('guete im Ergebnis', () => {
  it('oben gelesen, zusammen mit engine_used', () => {
    const r = RenderResult.parse({ ...ERGEBNIS, guete: 'vorschau', engine_used: 'z-image-turbo' });
    expect(r.guete).toBe('vorschau');
    expect(r.engine_used).toBe('z-image-turbo');
  });

  it('fehlt das Feld, sagt der Worker es nicht — kein Default', () => {
    expect(RenderResult.parse(ERGEBNIS)).not.toHaveProperty('guete');
  });

  it('ein unbekannter Wert faellt still weg, das Ergebnis bleibt lesbar', () => {
    const r = RenderResult.parse({ ...ERGEBNIS, guete: 'turbo' });
    expect(r.guete).toBeUndefined();
    expect(r.images).toEqual(['renders/a.png']);
  });
});
