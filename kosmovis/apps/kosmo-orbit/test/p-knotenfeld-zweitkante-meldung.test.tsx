// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { KMeldungen } from '@kosmo/ui';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { useProject } from '../src/state/project-store';
import type { VisGraph } from '@kosmo/kernel';

/**
 * P-KNOTENFELD Posten 7 (`auftraege/von-homestation/auf-orbit-20260825-07.md`
 * Abschnitt 3, `docs/STAND-WORKERAUFTRAEGE-2026-08-27.md` Zeilen 254-258).
 *
 * **Erst gemessen: ist das ROADMAP 1096 (P-ZWEITKANTE)?** Ja — wortgleiche
 * Stelle (`NodeCanvas.tsx`s `onPointerCancel`), wortgleiches Ereignis
 * (`pointerdown` auf dem Quell-Port, dann `pointercancel` statt `pointerup`,
 * `docs/MESSUNG-GRAPHSTART-ZWEITKANTE-2026-08-24.md` Fund B), und der
 * dortige Bericht selbst sagt bereits: **die verlorene Kante selbst kommt
 * durch App-Code nicht zurück** — der Browser beendet die Geste, bevor die
 * Zielkoordinaten je ankommen (`e2e/vis-editor.spec.ts`s `dragReset`-
 * Kopfkommentar, unabhängig von diesem Auftrag dokumentiert). Ohne
 * Playwright ist dieser Teil hier nicht neu nachstellbar — er war es auch
 * beim Original-Fund nur über echtes Chromium/Playwright, nicht über jsdom.
 *
 * **Was DIESES Paket beigetragen hat, weil es NEU im Auftrag steht, nicht
 * schon in 1096:** der Auftrag rügt ausdrücklich «OHNE jede Meldung an den
 * Nutzer» — GENAU dieser Teil war nach 1096 noch offen (die damalige
 * Reparatur räumt `pending` still auf, s. `node-canvas-pointer-cancel.
 * test.tsx`, sagt dem Nutzer aber nichts). Dieser Test prüft NUR die
 * Meldung, nicht die (App-seitig unbehebbare) Kante selbst.
 *
 * **Rot vor grün:** vor dieser Reparatur blieb `[data-testid="meldung-info"]`
 * nach einem abgebrochenen Kanten-Zug leer — belegt in
 * `docs/MESSUNG-KNOTENFELD-2026-08-27.md`, per `git show HEAD:<Pfad>` gegen
 * den unveränderten Stand gefahren (kein `git stash`, drei fremde Agenten
 * arbeiten im selben Baum).
 */

// Gleiche Stubs wie `node-canvas-pan.test.tsx`/`node-canvas-pointer-cancel.
// test.tsx` (F6) — jsdom kennt weder ResizeObserver noch PointerCapture.
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
if (!('setPointerCapture' in Element.prototype)) {
  Object.assign(Element.prototype, {
    setPointerCapture(): void {},
    releasePointerCapture(): void {},
    hasPointerCapture(): boolean {
      return false;
    },
  });
}

let root: Root | null = null;
let container: HTMLDivElement | null = null;

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  // Alle offenen Toasts ausklingen lassen, BEVOR der naechste Fall startet.
  // `meldungen` in `@kosmo/ui` ist ein Modul-Singleton ohne exportierten
  // Ruecksetzer — dasselbe Muster wie in
  // `packages/kosmo-ui/test/meldungen-stapel-deckel.test.tsx`.
  // OHNE das findet die Gegenprobe «kein Rauschen» den Toast des VORIGEN
  // Falls und faellt — gemessen, nicht vermutet: dieser Test war beim
  // ersten Volllauf genau daran rot, obwohl der Produktcode stimmt.
  act(() => {
    vi.advanceTimersByTime(9000);
  });
  if (root) {
    act(() => root!.unmount());
    root = null;
  }
  if (container) {
    container.remove();
    container = null;
  }
});

function neuerGraphMitZweiRenderZielen(): string {
  const { runCommand } = useProject.getState();
  const res = runCommand('vis.graphErstellen', { name: `P-ZWEITKANTE-Meldung-${Math.random()}` });
  const graphId = (res.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'kamera', x: 40, y: 40 });
  runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 400, y: 40 });
  return graphId;
}

function hitKreisVon(sichtbarerPort: Element): SVGCircleElement {
  const hit = sichtbarerPort.nextElementSibling;
  expect(hit).not.toBeNull();
  expect(hit!.getAttribute('class')).toContain('vis-node-port-hit');
  return hit as SVGCircleElement;
}

function feuere(el: Element, typ: string): void {
  const ev = new MouseEvent(typ, { bubbles: true, cancelable: true, button: 0 });
  Object.defineProperty(ev, 'pointerId', { value: 1, configurable: true });
  el.dispatchEvent(ev);
}

describe('NodeCanvas — P-KNOTENFELD Posten 7: pointercancel meldet sich jetzt beim Nutzer', () => {
  it('ein abgebrochener Kanten-Zug (pointercancel) zeigt eine Info-Meldung', () => {
    const graphId = neuerGraphMitZweiRenderZielen();

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root!.render(
        <>
          <NodeCanvas graphId={graphId} />
          <KMeldungen />
        </>,
      );
    });

    const svg = container.querySelector('[data-testid="node-canvas"]') as SVGSVGElement;
    expect(svg).not.toBeNull();
    const kameraNode = container.querySelector('[data-testid="vis-node-kamera"]')!;
    const kameraAusgang = kameraNode.querySelector('[data-testid="port-out-kameras"]')!;

    // Vorher: keine Meldung.
    expect(container.querySelector('[data-testid="meldung-info"]')).toBeNull();

    act(() => {
      feuere(hitKreisVon(kameraAusgang), 'pointerdown');
    });
    act(() => {
      feuere(svg, 'pointercancel');
    });

    const toast = container.querySelector('[data-testid="meldung-info"]');
    expect(toast, 'Meldung nach abgebrochenem Kanten-Zug').not.toBeNull();
    expect(toast!.textContent).toContain('erneut');
  });

  it('Gegenprobe: ein `pointercancel` OHNE laufenden Kanten-Zug (kein `pending`) meldet nichts — kein Rauschen', () => {
    const graphId = neuerGraphMitZweiRenderZielen();

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root!.render(
        <>
          <NodeCanvas graphId={graphId} />
          <KMeldungen />
        </>,
      );
    });

    const svg = container.querySelector('[data-testid="node-canvas"]') as SVGSVGElement;
    act(() => {
      feuere(svg, 'pointercancel');
    });

    expect(container.querySelector('[data-testid="meldung-info"]')).toBeNull();
  });

  it('Gegenprobe: ein erfolgreicher Kanten-Zug (kein Abbruch) meldet nichts extra', () => {
    const graphId = neuerGraphMitZweiRenderZielen();

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root!.render(
        <>
          <NodeCanvas graphId={graphId} />
          <KMeldungen />
        </>,
      );
    });

    const kameraNode = container.querySelector('[data-testid="vis-node-kamera"]')!;
    const renderNode = container.querySelector('[data-testid="vis-node-render"]')!;
    const kameraAusgang = kameraNode.querySelector('[data-testid="port-out-kameras"]')!;
    const renderEingang = renderNode.querySelector('[data-testid="port-in-kameras"]')!;

    act(() => {
      feuere(hitKreisVon(kameraAusgang), 'pointerdown');
    });
    act(() => {
      feuere(hitKreisVon(renderEingang), 'pointerup');
    });

    expect(container.querySelector('[data-testid="meldung-info"]')).toBeNull();
    const graph = useProject.getState().doc.get<VisGraph>(graphId)!;
    expect(graph.edges).toHaveLength(1);
  });
});
