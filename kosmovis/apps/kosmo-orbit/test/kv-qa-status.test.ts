import { describe, expect, it } from 'vitest';
import { kameraQaZeilen, type JobQaJeKameraEintrag } from '../src/modules/vis/varianten-diff';

/**
 * kv-qa-status (V017-SPEZ, Antwortblatt auf-20260922-142 Bauposten 2): der
 * Cloud-Worker sendet fuer eine ungepruefte Kamera `geometry: {passed: false,
 * status: 'not_measured'}`. Das `false` heisst dort NICHT «durchgefallen»
 * (render-result.ts, `GeometryStatus`). Vor diesem Paket las
 * `kameraQaZeilen` nur `passed` und machte daraus ein «durchgefallen».
 */
function eintrag(geometry: Record<string, unknown>, style?: Record<string, unknown>): JobQaJeKameraEintrag {
  return { kamera: 'innenraum', geometry, ...(style ? { style } : {}) } as JobQaJeKameraEintrag;
}

describe('kameraQaZeilen liest geometry.status', () => {
  it('passed:false mit status not_measured ergibt keine Aussage, sondern «nicht geprueft»', () => {
    const [zeile] = kameraQaZeilen([eintrag({ passed: false, status: 'not_measured' })]);
    expect(zeile).toEqual({ kamera: 'innenraum', geometryNichtGeprueft: 'not_measured' });
    expect(zeile?.geometryBestanden).toBeUndefined();
    expect(zeile?.bestanden).toBeUndefined();
  });

  it('dieselbe Regel fuer not_applicable', () => {
    const [zeile] = kameraQaZeilen([eintrag({ passed: false, status: 'not_applicable' })]);
    expect(zeile).toEqual({ kamera: 'innenraum', geometryNichtGeprueft: 'not_applicable' });
  });

  it('ungepruefte Geometrie faellt aus dem UND heraus, der Stil urteilt allein', () => {
    const [zeile] = kameraQaZeilen([eintrag({ passed: false, status: 'not_measured' }, { passed: true })]);
    expect(zeile).toEqual({
      kamera: 'innenraum',
      geometryNichtGeprueft: 'not_measured',
      styleBestanden: true,
      bestanden: true,
    });
  });

  it('Gegenprobe: status measured mit passed:false bleibt «durchgefallen»', () => {
    const [zeile] = kameraQaZeilen([eintrag({ passed: false, status: 'measured' })]);
    expect(zeile).toEqual({ kamera: 'innenraum', geometryBestanden: false, bestanden: false });
  });

  it('Gegenprobe: ohne status bleibt es wie vor diesem Paket (passed gilt)', () => {
    const [zeile] = kameraQaZeilen([eintrag({ passed: false })]);
    expect(zeile).toEqual({ kamera: 'innenraum', geometryBestanden: false, bestanden: false });
  });
});
