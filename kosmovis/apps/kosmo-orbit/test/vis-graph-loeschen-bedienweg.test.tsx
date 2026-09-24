// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { execute, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { KBestaetigung } from '@kosmo/ui';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
// Import-Seiteneffekt: registriert die GRAPH-Insel-Inhalte (Muster
// `vis-island-registry.test.ts`) — `visInhaltsRegistry.inhaltFuer('palette')`
// liefert danach die echte, produktiv gerenderte Stufe2-Komponente.
import { visInhaltsRegistry } from '../src/modules/vis/island';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * U-7 (`docs/BERICHT-FABLE-CODE-2026-08-18.md` B-3, Bauauftrag §4) —
 * Abnahme: ein `runCommand`-Aufrufer für `vis.graphLoeschen` existiert UND
 * ein Bedienweg-Test übt ihn. **Der Unterschied ist der ganze Punkt des
 * Befunds**: dieser Test klickt den echten «Graph löschen»-Knopf der GRAPH-
 * Insel-Palette (`island/inhalte/graph.tsx`, über die produktive
 * `visInhaltsRegistry`, nicht über eine eigens für den Test gebaute
 * Stub-Komponente) und den echten `bestaetigen()`-Dialog — er ruft NICHT
 * `execute(doc, 'vis.graphLoeschen', …)` direkt auf (das wäre nur ein
 * Kernel-Test, den es laut Befund B-3 bereits gibt und der den Befund nicht
 * aufgedeckt hätte).
 *
 * Aufbau/Dialog-Polling exakt nach dem Vorbild
 * `inspector-loeschen-bestaetigen.test.tsx` (dortiger Kommentar: `KBestaetigung`
 * portalt via `createPortal(..., document.body)`, echte Timer statt
 * `vi.waitFor`).
 */

function frischesDocMitGraph(name: string): { graphId: string } {
  const doc = new KosmoDoc();
  const graphId = (execute(doc, 'vis.graphErstellen', { name }).patches[0] as { id: string }).id;
  useProject.setState({ doc, journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: graphId });
  return { graphId };
}

let container: HTMLDivElement | null = null;
let root: Root | null = null;

function mounten(): void {
  const Palette = visInhaltsRegistry.inhaltFuer('palette')!.Stufe2!;
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root!.render(
      <>
        <Palette />
        <KBestaetigung />
      </>,
    );
  });
}

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

function q(testid: string): HTMLElement | null {
  return document.body.querySelector(`[data-testid="${testid}"]`);
}

/** Echte Timer-Polling — Muster `inspector-loeschen-bestaetigen.test.tsx`. */
async function wartAufDom(pruefe: () => boolean, versuche = 30): Promise<void> {
  for (let i = 0; i < versuche; i++) {
    if (pruefe()) return;
    await new Promise((resolve) => setTimeout(resolve, 20));
  }
  throw new Error(`Element nicht im DOM erschienen/verschwunden nach ${versuche * 20}ms`);
}
async function warteAufDialog(): Promise<void> {
  await wartAufDom(() => q('bestaetigung') !== null);
}
async function warteAufDialogEnde(): Promise<void> {
  await wartAufDom(() => q('bestaetigung') === null);
}

describe('vis.graphLoeschen — UI-Handgriff (U-7, B-3)', () => {
  beforeEach(() => {
    useVisRuntime.setState({ aufnahmen: {}, gespeicherteAnsichten: {}, reviewPins: {}, laeufe: {} });
  });

  it('der Knopf existiert (der Befund selbst: 0 UI-Weg vor diesem Paket)', () => {
    frischesDocMitGraph('Wettbewerb Nord');
    mounten();
    expect(q('visisl-graph-loeschen')).not.toBeNull();
  });

  it('fragt zuerst nach — Abbrechen löscht nichts, kein Undo-Eintrag', async () => {
    const { graphId } = frischesDocMitGraph('Wettbewerb Nord');
    mounten();

    const tiefeVorher = useProject.getState().history.depth;
    const knopf = q('visisl-graph-loeschen') as HTMLButtonElement;
    act(() => knopf.click());

    await warteAufDialog();
    expect(q('bestaetigung')!.textContent).toContain('Wettbewerb Nord');
    expect(q('bestaetigung')!.textContent).toContain('löschen?');

    // Noch NIEMAND hat bestätigt — der Graph muss jetzt noch existieren.
    expect(useProject.getState().doc.get<VisGraph>(graphId)).not.toBeUndefined();

    act(() => (q('bestaetigung-nein') as HTMLButtonElement).click());
    await warteAufDialogEnde();

    expect(useProject.getState().doc.get<VisGraph>(graphId)).not.toBeUndefined();
    expect(useProject.getState().history.depth).toBe(tiefeVorher);
    expect(useVisRuntime.getState().aktiverGraphId).toBe(graphId);
  });

  it('bei Bestätigung läuft der Handgriff über runCommand — der Graph ist weg, Undo bringt ihn zurück', async () => {
    const { graphId } = frischesDocMitGraph('Wettbewerb Nord');
    mounten();

    act(() => (q('visisl-graph-loeschen') as HTMLButtonElement).click());
    await warteAufDialog();
    act(() => (q('bestaetigung-ja') as HTMLButtonElement).click());
    await warteAufDialogEnde();

    expect(useProject.getState().doc.get<VisGraph>(graphId)).toBeUndefined();
    // Der gelöschte Graph war der aktive — der Handgriff räumt die Laufzeit
    // auf, Muster `neuerGraphErstellen()` (`vis-graph-aktionen.ts`).
    expect(useVisRuntime.getState().aktiverGraphId).toBeNull();

    act(() => useProject.getState().undo());
    expect(useProject.getState().doc.get<VisGraph>(graphId)).not.toBeUndefined();
  });
});
