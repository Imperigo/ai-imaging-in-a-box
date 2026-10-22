import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { knotenEbenenStil, RASTER_MAX, rasterInGeste, rasterStufe, ZOOM_RUHE_MS } from '../src/modules/vis/knoten-zoom';

/**
 * **Owner-Funde 22.10.2026 (Mac): «Beim Zoomen waechst der Text anders als der Knoten» (Visbox 0.3.33) und
 * «die Schrift ist nicht fixiert an den Knoten, sie jittert und aendert teils die Groesse» (0.3.35).**
 *
 * Die Knotenebene trug ihre Zoomstufe als CSS `zoom` (ab 0.3.33 nur noch ab 1). `zoom` legt die Ebene bei jeder
 * Stufe neu aus — Breiten, Zeilen und Glyphen werden je Stufe neu gerundet, Umbruch und Hoehen springen; beim
 * Uebergang ueber 1 wechselte zudem der Weg. Die Regel jetzt: EIN Weg — feste Auslegung in ganzzahligem Raster,
 * `transform: scale()` auf die Stufe, Raster erst in der Ruhe heben. Die Messung am Bildschirm (Zeilen und Lage
 * jedes Textblocks gleich bei 0,5 … 2 und mitten in der Geste) steht in `e2e/kv-zoom-schrift.spec.ts`.
 */
describe('Knotenebene: ein Weg fuer alle Stufen', () => {
  it('jede Stufe ist Raster (ganzzahliger zoom) mal Skalierung — nie ein gebrochener zoom', () => {
    for (const s of [0.1, 0.25, 0.5, 0.75, 0.95, 1, 1.05, 1.25, 2, 2.5, 4]) {
      const st = knotenEbenenStil(s);
      expect(Number.isInteger(st.zoom), `zoom bei ${s}`).toBe(true);
      expect(st.transform).toMatch(/^scale\(/);
      expect(st.transformOrigin).toBe('0 0');
    }
  });

  it('die wirksame Stufe ist immer genau die Ansicht — Draehte und Treffer rechnen weiter ueber `view`', () => {
    for (const s of [0.3, 0.5, 0.8, 0.95, 1, 1.05, 1.6, 2.5, 4]) {
      for (const raster of [1, 2, 3, 4]) {
        const st = knotenEbenenStil(s, raster);
        const tf = Number(/scale\(([\d.e-]+)\)/.exec(st.transform)![1]);
        expect(st.zoom * tf).toBeCloseTo(s, 12);
      }
    }
  });

  it('das Raster ist die naechste ganze Zahl ueber der Stufe, 1 … RASTER_MAX', () => {
    expect(rasterStufe(0.1)).toBe(1);
    expect(rasterStufe(0.95)).toBe(1);
    expect(rasterStufe(1)).toBe(1);
    expect(rasterStufe(1.05)).toBe(2);
    expect(rasterStufe(2)).toBe(2);
    expect(rasterStufe(2.5)).toBe(3);
    expect(rasterStufe(4)).toBe(RASTER_MAX);
    expect(rasterStufe(9)).toBe(RASTER_MAX);
  });

  it('in der Geste: hinein bleibt das Raster der Ruhe, heraus sinkt es sofort', () => {
    // Pinch von 1 auf 1,05 und 2: noch Raster 1 (keine Neuauslegung waehrend der Geste).
    expect(rasterInGeste(1.05, 1)).toBe(1);
    expect(rasterInGeste(2, 1)).toBe(1);
    // nach der Ruhe auf 2: Raster 2; zurueck auf 0,95 senkt es sofort (keine vielfache Aufloesung im Speicher).
    expect(rasterInGeste(2, 2)).toBe(2);
    expect(rasterInGeste(0.95, 2)).toBe(1);
    expect(ZOOM_RUHE_MS).toBeGreaterThanOrEqual(100);
    expect(ZOOM_RUHE_MS).toBeLessThanOrEqual(300);
  });

  it('beim Pinch 0,95 ↔ 1,05 aendert sich das Raster nicht — kein Wegwechsel bei 1', () => {
    for (let i = 0; i <= 20; i++) {
      const s = 0.95 + (0.1 * i) / 20;
      expect(knotenEbenenStil(s, rasterInGeste(s, 0.95)).zoom).toBe(1);
    }
  });

  it('Unsinn faellt auf 1', () => {
    expect(knotenEbenenStil(Number.NaN)).toEqual({ zoom: 1, transform: 'scale(1)', transformOrigin: '0 0' });
    expect(knotenEbenenStil(0)).toEqual({ zoom: 1, transform: 'scale(1)', transformOrigin: '0 0' });
    expect(knotenEbenenStil(-2, Number.NaN)).toEqual({ zoom: 1, transform: 'scale(1)', transformOrigin: '0 0' });
  });

  it('NodeCanvas setzt die Stufe nur ueber die Regel, und Inhalte sehen nur die Ruhestufe', () => {
    const quelle = readFileSync(resolve(__dirname, '../src/modules/vis/NodeCanvas.tsx'), 'utf8');
    expect(quelle).not.toMatch(/zoom:\s*view\.scale/);
    expect(quelle).toMatch(/style=\{knotenEbenenStil\(view\.scale, knotenRaster\)\}/);
    expect(quelle).toMatch(/data-knoten-zoom=\{view\.scale\}/);
    expect(quelle).toMatch(/data-knoten-raster=\{knotenRaster\}/);
    // 3D-Fenster waehlen ihre Pixeldichte nach dem Zoom — nur in der Ruhe, nicht je Zoomschritt.
    expect(quelle).not.toMatch(/knotenZoom=\{view\.scale\}/);
    expect(quelle).toMatch(/knotenZoom=\{ruheStufe\}/);
  });

  it('die Knotenschrift ist linear ausgelegt — SVG-Text und Bedienelemente eingeschlossen', () => {
    const css = readFileSync(resolve(__dirname, '../src/modules/vis/vis-visual.css'), 'utf8');
    expect(css).toMatch(/\.vis-knoten-svg text\s*\{\s*text-rendering:\s*geometricPrecision;/);
    expect(css).toMatch(
      /\.vis-knoten-zoom,\s*\.vis-knoten-zoom :is\(button, input, select, textarea\)\s*\{\s*text-rendering:\s*geometricPrecision;/,
    );
  });
});
