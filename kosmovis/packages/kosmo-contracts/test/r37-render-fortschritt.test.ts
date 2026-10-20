import { describe, expect, it } from 'vitest';
import { RenderJobProgress } from '../src/render-result';

/** R37: Render-Fortschritt mit Kamera, Zwischenbild und Restzeit — additiv. */
describe('R37 RenderJobProgress', () => {
  it('der alte Fortschritt bleibt gültig', () => {
    expect(RenderJobProgress.parse({ phase: 'blender', pct: 0.4 })).toEqual({ phase: 'blender', pct: 0.4 });
  });
  it('neue Felder: Kamera i/n, Vorschau, Restzeit (null in der ersten Kamera)', () => {
    const p = { phase: 'blender', pct: 0.25, kamera_i: 1, kamera_n: 4, vorschau: 'cycles-kamera-1.png', rest_s: null };
    expect(RenderJobProgress.parse(p)).toEqual(p);
    expect(RenderJobProgress.parse({ ...p, kamera_i: 2, rest_s: 83 }).rest_s).toBe(83);
  });
  it('unsinnige Werte werden abgewiesen', () => {
    expect(RenderJobProgress.safeParse({ phase: 'x', pct: 0.1, rest_s: -1 }).success).toBe(false);
    expect(RenderJobProgress.safeParse({ phase: 'x', pct: 0.1, kamera_i: 0 }).success).toBe(false);
    expect(RenderJobProgress.safeParse({ phase: 'x', pct: 0.1, vorschau: '' }).success).toBe(false);
  });
});

describe('R37 RenderJob.teilbild (Nr. 76)', () => {
  it('ein abgebrochener Job darf sein letztes Zwischenbild nennen; ohne bleibt er gültig', async () => {
    const { RenderJob } = await import('../src/render-result');
    const basis = { job_id: 'vis-1-abcdef', status: 'cancelled', scene: 's.json', created_at: '2026-10-20T10:00:00Z' };
    expect(RenderJob.parse(basis).teilbild).toBeUndefined();
    expect(RenderJob.parse({ ...basis, teilbild: 'cycles-kamera-2.png' }).teilbild).toBe('cycles-kamera-2.png');
    expect(RenderJob.safeParse({ ...basis, teilbild: '' }).success).toBe(false);
  });
});
