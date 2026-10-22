import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { knotenEbenenStil } from '../src/modules/vis/knoten-zoom';

/**
 * **Owner-Fund 22.10.2026 (Mac, Visbox 0.3.33): «Beim Zoomen waechst der Text anders als der Knoten.»**
 *
 * Die Knotenebene trug ihre Zoomstufe seit L69 als CSS `zoom`. `zoom` legt Text in der
 * gezoomten Groesse neu aus, und unter 1 haelt die Mindestschrift der Engine (WebKit 9 px,
 * Chromium 6 px) ihn gross, waehrend der Rahmen schrumpft. Die Regel: unter 1 eine einzige
 * Skalierung fuer Rahmen und Inhalt (`transform: scale()`), ab 1 `zoom` wie bisher.
 * Die Messung am Bildschirm (Schrift/Knotenhoehe konstant, Ziehen und Verbinden bei 0,5) steht
 * in `e2e/kv-zoom-schrift.spec.ts`.
 */
describe('Knotenebene: Zoom unter 1 als eine Skalierung, ab 1 als zoom', () => {
  it('unter 1 wird nichts neu ausgelegt — Massstab 1, verkleinert als Ganzes', () => {
    for (const s of [0.25, 0.35, 0.5, 0.75, 0.99]) {
      const st = knotenEbenenStil(s);
      expect(st.zoom).toBe(1);
      expect(st.transform).toBe(`scale(${s})`);
      expect(st.transformOrigin).toBe('0 0');
    }
  });

  it('ab 1 bleibt zoom (scharf in WebKit), ohne zweite Skalierung', () => {
    for (const s of [1, 1.25, 2, 2.5]) {
      const st = knotenEbenenStil(s);
      expect(st.zoom).toBe(s);
      expect(st.transform).toBeUndefined();
    }
  });

  it('die wirksame Stufe ist immer genau die Ansicht — Draehte und Treffer rechnen weiter ueber `view`', () => {
    for (const s of [0.3, 0.5, 0.8, 1, 1.6, 2.5]) {
      const st = knotenEbenenStil(s);
      const tf = st.transform ? Number(/scale\(([\d.e-]+)\)/.exec(st.transform)![1]) : 1;
      expect(st.zoom * tf).toBeCloseTo(s, 12);
    }
  });

  it('Unsinn faellt auf 1', () => {
    expect(knotenEbenenStil(Number.NaN)).toEqual({ zoom: 1 });
    expect(knotenEbenenStil(0)).toEqual({ zoom: 1 });
    expect(knotenEbenenStil(-2)).toEqual({ zoom: 1 });
  });

  it('NodeCanvas setzt die Stufe nur ueber die Regel, nie roh als `zoom: view.scale`', () => {
    const quelle = readFileSync(resolve(__dirname, '../src/modules/vis/NodeCanvas.tsx'), 'utf8');
    expect(quelle).not.toMatch(/zoom:\s*view\.scale/);
    expect(quelle).toMatch(/style=\{knotenEbenenStil\(view\.scale\)\}/);
    expect(quelle).toMatch(/data-knoten-zoom=\{view\.scale\}/);
  });
});
