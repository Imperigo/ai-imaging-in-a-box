// @vitest-environment jsdom
import { readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { KosmoDoc, newId, type FreeMesh, type Storey } from '@kosmo/kernel';
import { basisNodeHoehe, MODELL_KOERPER_H_MIT_LADEN, NodeCanvas } from '../src/modules/vis/NodeCanvas';
import {
  MODELL_3D_H,
  MODELL_3D_HILFE,
  MODELL_3D_HILFE_H,
  MODELL_3D_ZUSATZ,
  modellStand,
} from '../src/modules/vis/ModellKnoten';
import { registriereModellLaden, setzeModellLadeZustand } from '../src/modules/vis/modell-laden';
import { SAETZE_3D } from '../src/modules/vis/modell-vorschau-3d';
import { useProject } from '../src/state/project-store';

/**
 * F1 Modell-Knoten (Bauplan «Neue Knoten» 20.10.2026, Owner-Entscheid 109 A: das 3D-Fenster klein
 * fest im Knoten, Doppelklick gross). Geprüft am echten Knotengraph in jsdom — dort gibt es kein
 * WebGL, das Fenster zeigt also seinen Rückfall-Satz; ob es zeichnet, prüft die E2E-Probe
 * `kv-modell-3d.spec.ts` im Browser.
 *
 *  - ohne Wirt (KosmoOrbit) steht das Fenster unter der Szenen-Zeile, mit der Zeile darunter;
 *  - mit Wirt (Visbox) erst, wenn ein Modell geladen ist — auch unter «Noch geladen: …»;
 *  - Doppelklick öffnet die grosse Ansicht, Escape schliesst sie;
 *  - die Höhen im Knotengraph rechnen das Fenster mit;
 *  - der Modellstand zählt nur Bauteile, nicht den Vis-Graph (sonst exportierte jeder Regler neu);
 *  - Hülle und grosse Ansicht lädt der Knoten nur über `import()` (eigene Teile des Baus).
 */

class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const HIER = path.dirname(fileURLToPath(import.meta.url));

let root: Root | null = null;
let container: HTMLDivElement | null = null;
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  registriereModellLaden(null);
});

function montiere(): void {
  const { runCommand } = useProject.getState();
  const res = runCommand('vis.graphErstellen', { name: `KV-MODELL-3D-${Math.random()}` });
  const graphId = (res.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'modell', x: 40, y: 40 });
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
}

const q = (id: string) => container!.querySelector(`[data-testid="${id}"]`);

/** Bis die lazy geladene Hülle steht (und ihr Kern geantwortet hat). */
async function warteAufFenster(): Promise<void> {
  for (let i = 0; i < 50; i++) {
    await act(async () => {
      await new Promise((r) => setTimeout(r, 5));
    });
    const f = q('modell-3d');
    if (f && f.getAttribute('data-stand') !== 'laedt') return;
  }
}

describe('F1 · ohne Wirt: das Fenster unter der Szenen-Zeile', () => {
  it('Szenen-Zeile, Fenster, Zeile «Doppelklick: gross»', async () => {
    montiere();
    await warteAufFenster();
    const zeile = container!.querySelector('.vis-node-info-zeile');
    const fenster = q('modell-3d');
    expect(zeile?.textContent).toMatch(/^Szene: \d+ Bauteile \(GLB\)$/);
    expect(fenster).not.toBeNull();
    // Die Szenen-Zeile steht vor dem Fenster, die Hilfe danach.
    expect(zeile!.compareDocumentPosition(fenster!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(q('modell-3d-hilfe')?.textContent).toBe(MODELL_3D_HILFE);
    expect(fenster!.getAttribute('aria-label')).toContain('Doppelklick: gross');
    expect((fenster as HTMLElement).style.height).toBe(`${MODELL_3D_H}px`);
    expect((fenster as HTMLElement).style.width).toBe('100%');
  });

  it('ohne Bauteile: «Kein Modell geladen» statt eines leeren Bilds', async () => {
    montiere();
    await warteAufFenster();
    const bauteile = Number(/(\d+)/.exec(container!.querySelector('.vis-node-info-zeile')!.textContent!)![1]);
    if (bauteile === 0) {
      expect(q('modell-3d')?.getAttribute('data-stand')).toBe('leer');
      expect(q('modell-3d-satz')?.textContent).toBe(SAETZE_3D.leer);
    } else {
      // Mit Bauteilen im Dokument: in jsdom gibt es kein WebGL.
      expect(q('modell-3d-satz')?.textContent).toBe(SAETZE_3D.keinWebgl);
    }
  });

  it('Doppelklick öffnet die grosse Ansicht, Escape schliesst sie', async () => {
    montiere();
    await warteAufFenster();
    await act(async () => {
      q('modell-3d')!.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
    });
    for (let i = 0; i < 50 && !document.querySelector('[data-testid="modell-3d-gross"]'); i++) {
      await act(async () => {
        await new Promise((r) => setTimeout(r, 5));
      });
    }
    const gross = document.querySelector('[data-testid="modell-3d-gross"]');
    expect(gross).not.toBeNull();
    // Im Körper des Knotens nicht eingesperrt: die Ansicht hängt am Dokument.
    expect(container!.contains(gross)).toBe(false);
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });
    expect(document.querySelector('[data-testid="modell-3d-gross"]')).toBeNull();
  });
});

describe('F1 · mit Wirt: das Fenster, sobald ein Modell geladen ist', () => {
  const wirt = { formate: ['IFC'], annehmen: '.ifc', laden: async () => ({ stand: 'leer' as const }) };

  it('leer: kein Fenster', async () => {
    registriereModellLaden(wirt);
    montiere();
    await warteAufFenster();
    expect(q('modell-datei-laden')).not.toBeNull();
    expect(q('modell-3d')).toBeNull();
  });

  it('geladen: Fenster zwischen Szenen-Zeile und Mappe', async () => {
    registriereModellLaden(wirt);
    setzeModellLadeZustand({ stand: 'geladen', bauteile: 12, herkunft: 'IFC', mappe: 'haus' });
    montiere();
    await warteAufFenster();
    const szene = q('modell-szene')!;
    const fenster = q('modell-3d')!;
    const mappe = q('modell-mappe')!;
    expect(fenster).not.toBeNull();
    expect(szene.compareDocumentPosition(fenster) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(fenster.compareDocumentPosition(mappe) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('nicht lesbar mit «Noch geladen»: das Fenster zeigt das Modell, das weiter gilt', async () => {
    registriereModellLaden(wirt);
    setzeModellLadeZustand({ stand: 'fehler', satz: 'Nicht lesbar.', noch: { bauteile: 12, herkunft: 'IFC', mappe: 'haus' } });
    montiere();
    await warteAufFenster();
    expect(q('modell-noch')).not.toBeNull();
    expect(q('modell-3d')).not.toBeNull();
  });

  it('nicht lesbar ohne vorheriges Modell: kein Fenster', async () => {
    registriereModellLaden(wirt);
    setzeModellLadeZustand({ stand: 'fehler', satz: 'Nicht lesbar.' });
    montiere();
    await warteAufFenster();
    expect(q('modell-3d')).toBeNull();
  });
});

describe('F1 · Höhen', () => {
  it('Fenster und Zeile gehen in beide Körperhöhen ein', () => {
    expect(MODELL_3D_ZUSATZ).toBe(4 + MODELL_3D_H + 4 + MODELL_3D_HILFE_H);
    expect(basisNodeHoehe('modell')).toBe(26 + 8 + 20 + 22 + MODELL_3D_ZUSATZ + 10);
    expect(MODELL_KOERPER_H_MIT_LADEN).toBe(140 + MODELL_3D_ZUSATZ);
  });
});

describe('F1 · Modellstand', () => {
  it('zählt bei einem neuen Bauteil hoch, nicht bei einer Änderung am Vis-Graph', () => {
    const doc = new KosmoDoc();
    const a = modellStand(doc);
    expect(modellStand(doc)).toBe(a);
    const graph = { id: newId('visgraph'), kind: 'visgraph', name: 'g', nodes: [], edges: [] };
    doc.apply([{ id: graph.id, before: null, after: graph as never }]);
    expect(modellStand(doc)).toBe(a);
    const geschoss: Storey = { id: newId('st'), kind: 'storey', name: 'EG', index: 0, elevation: 0, height: 3000, cutHeight: 1100 };
    const netz: FreeMesh = { id: newId('fm'), kind: 'freemesh', storeyId: geschoss.id, name: 'Box', positions: [0, 0, 0, 1, 0, 0, 0, 1, 0], faces: [0, 1, 2] };
    doc.apply([
      { id: geschoss.id, before: null, after: geschoss },
      { id: netz.id, before: null, after: netz },
    ]);
    const b = modellStand(doc);
    expect(b).toBeGreaterThan(a);
    expect(modellStand(doc)).toBe(b);
  });
});

describe('F1 · Bau: Hülle und grosse Ansicht kommen nur über import()', () => {
  it('kein Quelltext ausser den beiden selbst lädt sie statisch', () => {
    const src = path.resolve(HIER, '../src');
    const dateien: string[] = [];
    const gehe = (d: string) => {
      for (const n of readdirSync(d)) {
        const p = path.join(d, n);
        if (statSync(p).isDirectory()) gehe(p);
        else if (/\.(ts|tsx)$/.test(n)) dateien.push(p);
      }
    };
    gehe(src);
    const statisch = /^\s*import\s+(?!type\b)[^;]*from\s+['"][^'"]*modell-vorschau-3d(-gross)?['"]/m;
    const treffer = dateien
      .filter((p) => !/modell-vorschau-3d(-gross)?\.tsx$/.test(p))
      .filter((p) => statisch.test(readFileSync(p, 'utf8')))
      .map((p) => path.relative(src, p));
    expect(treffer).toEqual([]);
    const knoten = readFileSync(path.join(src, 'modules/vis/ModellKnoten.tsx'), 'utf8');
    expect(knoten).toContain("import('./modell-vorschau-3d')");
    expect(knoten).toContain("import('./modell-vorschau-3d-gross')");
  });
});
