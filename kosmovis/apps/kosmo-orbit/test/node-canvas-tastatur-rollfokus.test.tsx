// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { useProject } from '../src/state/project-store';

// jsdom kennt kein ResizeObserver — Muster `node-canvas-pan.test.tsx` (dort
// ausführlich begründet: NodeCanvas nutzt ihn nur für die viewBox-Messung,
// für den Tastatur-Fund hier irrelevant, aber ohne Stub bricht der
// useLayoutEffect beim Mount mit «ResizeObserver is not defined» ab).
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * S3-a (`docs/UI-UX-2026-09-09-GRAPH-TASTATUR.md`) — der Knotengraph war
 * VOR diesem Auftrag vollständig tastaturlos (Gegenprobe im Bericht:
 * `onKeyDown`/`tabIndex`/`role=`/`aria-` kein einziger Treffer auf einem
 * Node in `NodeCanvas.tsx`). Diese Datei prüft NUR die Erreichbarkeit
 * (Wandern über `useRollfokus`) — Auswahl per Enter/Leertaste steht in
 * `node-canvas-tastatur-auswahl.test.tsx`.
 *
 * Beide Fälle unten liefen VOR dem Fix rot (kein `[data-rf-index]`-Element
 * existierte überhaupt — s. Bericht «Rot vor Grün», dort mit `git checkout
 * -- NodeCanvas.tsx` gegen den unveränderten Bestandscode nachgemessen).
 */

let root: Root | null = null;
let container: HTMLDivElement | null = null;

afterEach(() => {
  if (root) {
    act(() => root!.unmount());
    root = null;
  }
  if (container) {
    container.remove();
    container = null;
  }
});

function montiere(graphId: string): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root!.render(<NodeCanvas graphId={graphId} />);
  });
}

function neuerGraph(): string {
  const { runCommand } = useProject.getState();
  const res = runCommand('vis.graphErstellen', { name: `S3a-Rollfokus-${Math.random()}` });
  return (res.patches[0] as { id: string }).id;
}

/** Drei einfache, seiteneffektfreie Node-Typen — keine Render-/Kamera-
 *  Abhängigkeiten (`modell`/`material` haben keine Inputs, `zahl` ist ein
 *  reiner Wert-Node), reichen für Wandern/Home/End völlig aus. */
function dreiNodesSetzen(graphId: string): void {
  const { runCommand } = useProject.getState();
  runCommand('vis.nodeSetzen', { graphId, typ: 'modell', x: 0, y: 0 });
  runCommand('vis.nodeSetzen', { graphId, typ: 'material', x: 300, y: 0 });
  runCommand('vis.nodeSetzen', { graphId, typ: 'zahl', x: 600, y: 0 });
}

/** Alle Node-`<g>` in Dokumentreihenfolge (== `data-rf-index`-Reihenfolge). */
function nodeGs(): SVGGElement[] {
  return Array.from(container!.querySelectorAll<SVGGElement>('[data-rf-index]')).sort(
    (a, b) => Number(a.getAttribute('data-rf-index')) - Number(b.getAttribute('data-rf-index')),
  );
}

/** tabIndex als Zahl, direkt vom Attribut (nicht über die DOM-Property —
 *  jsdom implementiert `SVGElement.tabIndex` nicht immer vollständig). */
function tabIndexVon(el: Element): number {
  const raw = el.getAttribute('tabindex');
  return raw === null ? NaN : Number(raw);
}

/** Das aktuell EINE tabbare Node-`<g>` (tabIndex 0) — wirft, wenn es nicht
 *  GENAU eines gibt (die Invariante, die dieser Test nach jedem Tastendruck
 *  prüft). */
function dasEineTabbareOderWirf(): SVGGElement {
  const treffer = nodeGs().filter((g) => tabIndexVon(g) === 0);
  expect(treffer).toHaveLength(1);
  return treffer[0]!;
}

function druecke(el: Element, key: string): void {
  act(() => {
    el.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }));
  });
}

describe('NodeCanvas — Tastatur-Rückgrat, Rollfokus (S3-a)', () => {
  it('genau EIN Node trägt initial tabIndex=0, alle anderen -1', () => {
    const graphId = neuerGraph();
    dreiNodesSetzen(graphId);
    montiere(graphId);

    const gs = nodeGs();
    expect(gs).toHaveLength(3);
    expect(gs.map(tabIndexVon)).toEqual([0, -1, -1]);
    expect(gs.map((g) => g.getAttribute('role'))).toEqual(['button', 'button', 'button']);
    expect(gs.map((g) => g.hasAttribute('aria-label'))).toEqual([true, true, true]);
  });

  it('Pfeiltasten wandern in Dokumentreihenfolge, Home/End springen an die Enden — die EIN-tabIndex=0-Invariante gilt nach JEDEM Tastendruck, nicht nur am Anfang', () => {
    // Falsifizierbarer Fehlerfall 1 (Auftrag): eine Gruppe hat NIE zwei
    // gleichzeitige tabIndex=0-Einträge. `dasEineTabbareOderWirf()` prüft
    // das nach JEDER Zeile unten erneut — nicht bloss am Ende der Sequenz.
    const graphId = neuerGraph();
    dreiNodesSetzen(graphId);
    montiere(graphId);

    // Start: Index 0 aktiv.
    let aktiv = dasEineTabbareOderWirf();
    expect(aktiv.getAttribute('data-rf-index')).toBe('0');

    druecke(aktiv, 'ArrowRight');
    aktiv = dasEineTabbareOderWirf();
    expect(aktiv.getAttribute('data-rf-index')).toBe('1');

    druecke(aktiv, 'ArrowRight');
    aktiv = dasEineTabbareOderWirf();
    expect(aktiv.getAttribute('data-rf-index')).toBe('2');

    // Ohne `umlaufend` (Default) bleibt ArrowRight am letzten Element stehen.
    druecke(aktiv, 'ArrowRight');
    aktiv = dasEineTabbareOderWirf();
    expect(aktiv.getAttribute('data-rf-index')).toBe('2');

    druecke(aktiv, 'Home');
    aktiv = dasEineTabbareOderWirf();
    expect(aktiv.getAttribute('data-rf-index')).toBe('0');

    // Am ersten Element bleibt ArrowLeft ebenfalls stehen (kein Umlauf).
    druecke(aktiv, 'ArrowLeft');
    aktiv = dasEineTabbareOderWirf();
    expect(aktiv.getAttribute('data-rf-index')).toBe('0');

    druecke(aktiv, 'End');
    aktiv = dasEineTabbareOderWirf();
    expect(aktiv.getAttribute('data-rf-index')).toBe('2');

    druecke(aktiv, 'ArrowLeft');
    aktiv = dasEineTabbareOderWirf();
    expect(aktiv.getAttribute('data-rf-index')).toBe('1');
  });

  it('falsifizierbarer Fehlerfall 2: eine leere Gruppe (kein Node) wirft nicht und wandert nicht ins Leere', () => {
    const graphId = neuerGraph();
    // BEWUSST kein `dreiNodesSetzen()` — der Graph bleibt leer.
    expect(() => montiere(graphId)).not.toThrow();
    expect(nodeGs()).toHaveLength(0);

    // Aus dem Leeren heraus einen Node dazu — die Gruppe muss sauber auf
    // GENAU einen tabbaren Eintrag "landen", nicht auf einem Rest-Index
    // aus der leeren Phase hängen bleiben oder werfen.
    const { runCommand } = useProject.getState();
    expect(() => {
      act(() => {
        runCommand('vis.nodeSetzen', { graphId, typ: 'modell', x: 0, y: 0 });
      });
    }).not.toThrow();

    const gs = nodeGs();
    expect(gs).toHaveLength(1);
    expect(tabIndexVon(gs[0]!)).toBe(0);
  });
});
