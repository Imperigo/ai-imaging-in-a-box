// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import type { VisGraph } from '@kosmo/kernel';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { dreiStimmungenEinfuegen, kameraVorschlagenAktion } from '../src/modules/vis/vis-graph-aktionen';
import { useVisRuntime, type NodeLaufStatus } from '../src/modules/vis/vis-runtime';
import { useProject } from '../src/state/project-store';

/**
 * KV-B5-Nachgang (Meldeblatt `docs/auftraege-kosmovis/meldung-20261006-kosmovis-b5-nachgang.md`).
 * Zwei der drei Befunde des lokalen Workers (`auf-20261006-242`, WebKitGTK)
 * haengen nicht an der Engine, sondern an Zahlen — die prueft diese Probe
 * ohne Browser, am gerenderten Kasten (`.vis-knoten`, Inline-`left/top/height`):
 *
 *  - Nach einem Abbruch ist der Render-Knoten so hoch wie frisch, und die
 *    Bildflaeche ist der Streifen. Vorher wuchs er um 122 px (Karte 580 → 702)
 *    und ragte im Fenster unter den Knopf unten in der Mitte.
 *  - Knoten, die «Kamera vorschlagen» und «Drei Stimmungen» anlegen,
 *    ueberschneiden sich mit keinem anderen — auch nicht, wenn ein
 *    Render-Knoten danach durch einen Lauf waechst. Vorher setzte «Kamera
 *    vorschlagen» ungeprueft auf (40, 40), und ein laufender Render-Knoten
 *    reichte bei «Drei Stimmungen» 82 px in den naechsten.
 *
 * Die Hoehen kommen aus dem gerenderten Kasten, nicht aus einer Hilfsfunktion
 * der Platzsuche — sonst pruefte die Probe die Rechnung mit sich selbst.
 * Die Sichtbarkeit der Schiene «Umgebung drehen» braucht gezeichnete
 * Bildpunkte; sie prueft `e2e/kv-b5-nachgang.spec.ts`.
 */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let root: Root | null = null;
let container: HTMLDivElement | null = null;
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  useVisRuntime.setState({ laeufe: {} });
});

function neuerGraph(): string {
  const res = useProject.getState().runCommand('vis.graphErstellen', { name: `KV-B5N-${Math.random()}` });
  return (res.patches[0] as { id: string }).id;
}

function setze(graphId: string, typ: string, x: number, y: number): string {
  useProject.getState().runCommand('vis.nodeSetzen', { graphId, typ, x, y });
  const g = useProject.getState().doc.get<VisGraph>(graphId)!;
  return g.nodes[g.nodes.length - 1]!.id;
}

function montiere(graphId: string): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
}

function lauf(nodeId: string, status: NodeLaufStatus): void {
  act(() => useVisRuntime.getState().setzeLauf(nodeId, { status, memoKey: 'kv-b5n' }));
}

type Kasten = { typ: string; x: number; y: number; h: number };

/** Die gerenderten Kaesten (Welt-Pixel), Reihenfolge wie im Graphen. */
function kaesten(): Kasten[] {
  return [...container!.querySelectorAll<HTMLElement>('.vis-knoten')].map((k) => ({
    typ: (k.dataset['testid'] ?? '').replace('vis-node-', ''),
    x: Number.parseFloat(k.style.left),
    y: Number.parseFloat(k.style.top),
    h: Number.parseFloat(k.style.height),
  }));
}

function ueberschneidungen(boxen: Kasten[], breite: number): string[] {
  const funde: string[] = [];
  for (let i = 0; i < boxen.length; i++) {
    for (let j = i + 1; j < boxen.length; j++) {
      const a = boxen[i]!;
      const b = boxen[j]!;
      const dx = Math.min(a.x + breite, b.x + breite) - Math.max(a.x, b.x);
      const dy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
      if (dx > 0 && dy > 0) funde.push(`${a.typ}#${i} (${a.x}, ${a.y}, h ${a.h}) und ${b.typ}#${j} (${b.x}, ${b.y}, h ${b.h})`);
    }
  }
  return funde;
}

function renderKasten(): HTMLElement {
  return container!.querySelector<HTMLElement>('[data-testid="vis-node-render"]')!;
}

describe('KV-B5-Nachgang · Hoehe des Render-Knotens nach einem Abbruch', () => {
  it('nach «abgebrochen» ist der Knoten so hoch wie frisch, und die Bildflaeche ist der Streifen', () => {
    const graphId = neuerGraph();
    const renderId = setze(graphId, 'render', 320, 120);
    montiere(graphId);
    const frisch = Number.parseFloat(renderKasten().style.height);
    expect(frisch).toBeGreaterThan(0);

    lauf(renderId, 'abgebrochen');
    expect(container!.querySelector('[data-testid="render-status"]')!.textContent).toBe('abgebrochen');
    expect(Number.parseFloat(renderKasten().style.height), 'Kasten nach dem Abbruch').toBe(frisch);
    const leerbild = renderKasten().querySelector<HTMLElement>('.vis-node-leerbild')!;
    expect(leerbild.textContent).toContain('abgebrochen');
    expect(leerbild.style.height, 'Bildflaeche nach dem Abbruch').toBe('auto');
    expect(container!.querySelector('[data-testid="render-abbrechen"]')).toBeNull();
  });

  it('Gegenprobe: waehrend der Auftrag wartet, waechst der Knoten (Abbrechen/Freigeben und Bildrahmen brauchen den Platz)', () => {
    const graphId = neuerGraph();
    const renderId = setze(graphId, 'render', 320, 120);
    montiere(graphId);
    const frisch = Number.parseFloat(renderKasten().style.height);
    lauf(renderId, 'wartetFreigabe');
    expect(container!.querySelector('[data-testid="render-abbrechen"]')).not.toBeNull();
    expect(container!.querySelector('[data-testid="render-freigeben"]')).not.toBeNull();
    expect(Number.parseFloat(renderKasten().style.height)).toBeGreaterThan(frisch);
  });

  it('Gegenprobe: ein Fehler behaelt den Bildrahmen fuer seinen Text', () => {
    const graphId = neuerGraph();
    const renderId = setze(graphId, 'render', 320, 120);
    montiere(graphId);
    const frisch = Number.parseFloat(renderKasten().style.height);
    act(() => useVisRuntime.getState().setzeLauf(renderId, { status: 'fehler', fehler: 'Bruecke meldet einen Fehler', memoKey: 'kv-b5n' }));
    const leerbild = renderKasten().querySelector<HTMLElement>('.vis-node-leerbild')!;
    expect(leerbild.style.height).toBe('');
    expect(Number.parseFloat(renderKasten().style.height)).toBeGreaterThan(frisch);
  });
});

describe('KV-B5-Nachgang · neue Knoten ueberschneiden sich nicht', () => {
  it('«Kamera vorschlagen» neben einem Render-Knoten bei (220, 20): die Kamera landet nicht auf ihm', () => {
    const graphId = neuerGraph();
    // Die Lage aus der Palette (Chromium, 1400×900): Modell, Prompt, Render.
    setze(graphId, 'modell', 460, 257);
    setze(graphId, 'prompt', 700, 240);
    setze(graphId, 'render', 220, 20);
    act(() => kameraVorschlagenAktion(graphId));
    montiere(graphId);
    const boxen = kaesten();
    expect(boxen.map((b) => b.typ)).toContain('kamera');
    expect(ueberschneidungen(boxen, 200)).toEqual([]);
  });

  it('«Drei Stimmungen»: waehrend ein Render-Knoten laeuft, reicht er nicht in den naechsten', () => {
    const graphId = neuerGraph();
    act(() => dreiStimmungenEinfuegen(graphId));
    montiere(graphId);
    expect(ueberschneidungen(kaesten(), 200), 'frisch').toEqual([]);
    const g = useProject.getState().doc.get<VisGraph>(graphId)!;
    for (const n of g.nodes.filter((k) => k.typ === 'render')) lauf(n.id, 'wartetGpu');
    expect(ueberschneidungen(kaesten(), 200), 'alle drei Render-Knoten im Lauf').toEqual([]);
  });

  it('«Drei Stimmungen» unter einem bestehenden, laufenden Render-Knoten: der neue Teilgraph beginnt unter dessen voller Hoehe', () => {
    const graphId = neuerGraph();
    const renderId = setze(graphId, 'render', 40, 20);
    act(() => dreiStimmungenEinfuegen(graphId));
    montiere(graphId);
    lauf(renderId, 'rendert');
    expect(ueberschneidungen(kaesten(), 200)).toEqual([]);
  });
});
