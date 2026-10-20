import { describe, expect, it } from 'vitest';
import type { VisGraph } from '@kosmo/kernel';
import { ENTZERREN_ABSTAND, entzerreGraph, entzerreLagen } from '../src/modules/vis/knoten-entzerren';
import { NODE_W } from '../src/modules/vis/NodeCanvas';

/**
 * Gesicherte Graphen beim Laden einmal sanft entzerren (Owner-Befund am Mac 20.10.2026: die
 * Auto-Kamera lag über dem unteren Rand des Modell-Knotens, der mit dem 3D-Fenster gewachsen
 * ist). Geprüft mit fester Höhe je Art, damit die Probe nicht an der Knotenhöhe hängt.
 */
const H: Record<string, number> = { modell: 366, kamera: 150, stimmung: 120, render: 400 };
const hoehe = (n: { typ: string }) => H[n.typ] ?? 100;
const knoten = (id: string, typ: string, x: number, y: number) => ({ id, typ, x, y, params: {} });

function ueberlappt(ns: readonly { x: number; y: number; typ: string }[]): boolean {
  return ns.some((a, i) =>
    ns.some((b, j) => j > i && a.x < b.x + NODE_W && b.x < a.x + NODE_W && a.y < b.y + hoehe(b) && b.y < a.y + hoehe(a)),
  );
}

describe('entzerreLagen', () => {
  it('ohne Überlappung: nichts rückt', () => {
    const ns = [knoten('m', 'modell', 40, 40), knoten('k', 'kamera', 40, 40 + 366 + 32), knoten('r', 'render', 320, 40)];
    expect(entzerreLagen(ns, hoehe).size).toBe(0);
  });

  it('der alte Anfang (Modell-Knoten früher kürzer): die Auto-Kamera rückt unter das Modell', () => {
    // Vor dem 3D-Fenster stand die Kamera 204 + 32 px unter dem Modell.
    const ns = [knoten('m', 'modell', 40, 400), knoten('k', 'kamera', 40, 400 + 204 + 32)];
    const neu = entzerreLagen(ns, hoehe);
    expect(neu.get('k')).toBe(400 + 366 + ENTZERREN_ABSTAND);
    expect(neu.has('m'), 'oben bleibt, wo es war').toBe(false);
  });

  it('schiebt mit, was darunter liegt, und lässt die andere Spalte in Ruhe', () => {
    const ns = [
      knoten('m', 'modell', 40, 0),
      knoten('k', 'kamera', 40, 300),
      knoten('s', 'stimmung', 40, 480),
      knoten('r', 'render', 320, 100),
    ];
    const neu = entzerreLagen(ns, hoehe);
    const nachher = ns.map((n) => ({ ...n, y: neu.get(n.id) ?? n.y }));
    expect(ueberlappt(nachher)).toBe(false);
    expect(neu.has('r')).toBe(false);
    for (const n of ns) expect(neu.get(n.id) ?? n.y, `${n.id} rückt nie nach oben`).toBeGreaterThanOrEqual(n.y);
  });

  it('entzerreGraph: derselbe Gegenstand ohne Überlappung, sonst eine Kopie mit neuen y', () => {
    const g: VisGraph = {
      id: 'g', kind: 'visgraph', name: 'g', edges: [],
      nodes: [knoten('m', 'modell', 40, 40), knoten('k', 'kamera', 40, 600)],
    } as VisGraph;
    expect(entzerreGraph(g, hoehe)).toBe(g);
    const eng = { ...g, nodes: [knoten('m', 'modell', 40, 40), knoten('k', 'kamera', 40, 200)] } as VisGraph;
    const neu = entzerreGraph(eng, hoehe);
    expect(neu).not.toBe(eng);
    expect(neu.nodes[1]!.y).toBe(40 + 366 + ENTZERREN_ABSTAND);
    expect(eng.nodes[1]!.y, 'das Original bleibt').toBe(200);
  });
});
