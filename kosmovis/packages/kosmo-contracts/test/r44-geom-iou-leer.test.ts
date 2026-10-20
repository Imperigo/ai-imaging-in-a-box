import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { RenderResult } from '../src';

/**
 * R44 (Visbox 0.3.6): ohne gemeinsame Silhouette schreibt der Heim-PC
 * qa.geometry.geom_iou = null mit geom_iou_grund und laesst
 * geometry_gates.geom_iou weg. Das Ergebnis muss lesbar bleiben — auch wenn
 * geometry_gates.geom_iou doch einmal null traegt (Absicherung).
 */
const echt = JSON.parse(
  readFileSync(fileURLToPath(new URL('./fixtures/kv-geom-iou-leer.json', import.meta.url)), 'utf8'),
) as Record<string, unknown>;

describe('R44 · geom_iou leer', () => {
  it('echtes Heim-PC-Ergebnis: lesbar, geom_iou null mit Grund, kein geom_iou in geometry_gates', () => {
    const r = RenderResult.parse(echt);
    expect(r.qa.geometry?.geom_iou).toBeNull();
    expect(r.qa.geometry?.geom_iou_grund).toMatch(/keinen Bildpunkt gemeinsam/);
    expect(r.geometry_gates?.geom_iou).toBeUndefined();
  });

  it('Absicherung: geometry_gates.geom_iou = null weist das Ergebnis nicht ab', () => {
    const gates = { ...(echt['geometry_gates'] as Record<string, unknown>), geom_iou: null, geom_iou_grund: 'kein gemeinsamer Bildpunkt' };
    const r = RenderResult.parse({ ...echt, geometry_gates: gates });
    expect(r.geometry_gates?.geom_iou).toBeNull();
    expect(r.geometry_gates?.geom_iou_grund).toBe('kein gemeinsamer Bildpunkt');
  });
});
