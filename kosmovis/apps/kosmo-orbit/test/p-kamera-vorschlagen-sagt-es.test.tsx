// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { KMeldungen } from '@kosmo/ui';
import { execute, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import { kameraVorschlagenAktion } from '../src/modules/vis/vis-graph-aktionen';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * Posten 6 (`auftraege/von-homestation/auf-orbit-20260828-16.md`, Block A) —
 * «Kamera vorschlagen» setzt ungefragt einen Knoten.
 *
 * Offen war die zweite Haelfte der Beobachtung aus Blatt 07: findet
 * `kameraVorschlagenAktion()` (`vis-graph-aktionen.ts`) keinen `kamera`-Node,
 * ruft sie `vis.nodeSetzen` und setzt einen — **ohne zu fragen und ohne es zu
 * sagen**. Ein Knopf, der «vorschlagen» heisst und baut, ist eine
 * Falschmeldung an den Nutzer.
 *
 * Gewaehlter Weg (Auftrag: «entweder fragen, oder sagen, dass es geschehen
 * ist»): **sagen**, ueber das vorhandene Meldungs-Modul `@kosmo/ui`s
 * `melde()`. Begruendung steht im Kommentar an der Stelle selbst.
 *
 * Hausmuster fuer Meldungs-Tests (`packages/kosmo-ui/test/
 * meldungen-stapel-deckel.test.tsx`): der Meldungs-Speicher in `@kosmo/ui`
 * ist ein Modul-Singleton OHNE exportierten Reset — darum falsche Zeitgeber
 * und `vi.advanceTimersByTime(9000)` im `afterEach`, sonst leckt der Zustand
 * zwischen den Faellen.
 */

let root: Root | null = null;
let container: HTMLDivElement | null = null;
let graphId = '';

function montiere(): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root!.render(<KMeldungen />);
  });
}

function meldungsTexte(): string[] {
  return [...document.body.querySelectorAll('.k-meldung-text')].map((e) => e.textContent ?? '');
}

function graph(): VisGraph {
  return useProject.getState().doc.get<VisGraph>(graphId)!;
}

beforeEach(() => {
  vi.useFakeTimers();
  const doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'P6' }).patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 400, y: 100 });
  useProject.setState({ doc, journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: graphId });
});

afterEach(() => {
  // Modul-Singleton ohne Reset — alle offenen Toasts ausklingen lassen.
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
  vi.useRealTimers();
});

describe('Posten 6 — «Kamera vorschlagen» sagt, dass es einen Knoten gesetzt hat', () => {
  it('ohne kamera-Node: der Knoten wird gesetzt UND gemeldet (nicht stillschweigend)', () => {
    montiere();
    expect(graph().nodes.some((n) => n.typ === 'kamera')).toBe(false);

    act(() => kameraVorschlagenAktion(graphId));

    // Der Knoten ist da (Verhalten unveraendert) …
    expect(graph().nodes.filter((n) => n.typ === 'kamera')).toHaveLength(1);
    expect(graph().edges).toHaveLength(1);
    // … und er ist angesagt.
    const texte = meldungsTexte();
    expect(texte).toHaveLength(1);
    expect(texte[0]).toMatch(/Kamera/);
    expect(texte[0]).toMatch(/gesetzt/);
  });

  it('Gegenprobe: gibt es schon einen kamera-Node, wird nichts gesetzt und nichts gemeldet', () => {
    const { runCommand } = useProject.getState();
    runCommand('vis.nodeSetzen', { graphId, typ: 'kamera', x: 40, y: 40 });
    montiere();

    act(() => kameraVorschlagenAktion(graphId));

    expect(graph().nodes.filter((n) => n.typ === 'kamera')).toHaveLength(1);
    expect(graph().edges).toHaveLength(1);
    expect(meldungsTexte()).toEqual([]);
  });
});
