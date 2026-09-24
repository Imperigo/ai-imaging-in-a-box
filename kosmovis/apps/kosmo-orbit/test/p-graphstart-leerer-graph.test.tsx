// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { execute, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
// Import-Seiteneffekt: registriert die GRAPH-Insel-Inhalte — dieselbe echte,
// produktiv gerenderte Stufe2-Komponente wie die Oberfläche selbst nutzt
// (Muster `vis-graph-loeschen-bedienweg.test.tsx`).
import { visInhaltsRegistry } from '../src/modules/vis/island';
import { neuerGraphErstellen } from '../src/modules/vis/vis-graph-aktionen';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * P-GRAPHSTART (`docs/MESSUNG-GRAPHSTART-ZWEITKANTE-2026-08-24.md`) — Fund A
 * («"+ Graph erstellen" liefert seit v0.9.47 einen leeren Graph statt des
 * vorverdrahteten»).
 *
 * **Das ist kein Rückfall — dieser Test hält fest, WARUM nicht:**
 *
 * `vis.graphErstellen` (`packages/kosmo-kernel/src/commands/vis.ts:29-39`)
 * trägt seit seiner Einführung (`62da5530`, V1-Finish P2, der allererste
 * KosmoVis-Commit) wörtlich die Beschreibung «Erstellt einen LEEREN
 * Render-Graphen» — Wort für Wort unverändert, s. `git log -S` auf genau
 * diesen Satz: EIN Treffer, `62da5530` selbst. Der App-Handgriff
 * `neuerGraphErstellen()` (`vis-graph-aktionen.ts`, hierher importiert —
 * exakt die Funktion, die der «+ Graph erstellen»-Knopf ruft) tut nichts
 * weiter als `runCommand('vis.graphErstellen', …)` + `setAktiverGraphId`.
 * Ganze Historie beider Dateien geprüft (`git log --oneline --all`):
 * `vis.ts` 6 Commits, `vis-graph-aktionen.ts` 2 Commits (Erstanlage v0.8.4 +
 * die U-7-Löschfunktion) — KEINER fügt je eine Vorverdrahtung hinzu oder
 * entfernt sie. Zwischen v0.9.41 (dem Lauf mit der «vorverdrahteten»
 * Oberfläche) und v0.9.47 (dem Lauf mit dem leeren Graphen) hat KEIN
 * einziger Commit diese beiden Dateien angefasst.
 *
 * Die naheliegendste Erklärung, die zu allen Belegen passt: die Oberfläche
 * vom 20.08. lief auf demselben Browser-Profil wie der 19.08.-Lauf, an dem
 * ein Mensch den Graphen (Modell → Auto-Kamera → Prompt → Render) von Hand
 * gebaut hatte (`19.08.-Bericht`: «GEHT — "+ Graph erstellen" → "Graph 1",
 * Node-Palette, Verbinden» — 12 Knoten in vier Gruppen) — und
 * `state/project-vault.ts` («Projekt-Tresor — Autosave … in IndexedDB»)
 * hat dieses Projekt beim nächsten Öffnen einfach wiederhergestellt. Der
 * 24.08.-Lauf nutzte zwei FRISCHE Profile (leeres IndexedDB) — dort erzeugt
 * der Knopf, wie er es schon immer tat, einen leeren Graphen.
 *
 * Dieser Test ist darum kein Regressionstest für einen Fehler (es gibt
 * keinen), sondern ein Vertrags-Riegel: er hält den seit jeher geltenden
 * Vertrag («"+ Graph erstellen" liefert 0 Knoten/0 Kanten») fest, damit eine
 * künftige, unbedachte Vorverdrahtung — die ohne Wissen um diesen Befund
 * plausibel aussehen könnte — hier sichtbar rot wird. Er hat darum KEINEN
 * Vorher/Nachher-Kontrast (git stash) wie der P-ZWEITKANTE-Test — es gibt
 * keinen Fix, gegen den er falsifiziert werden könnte; er ist bereits am
 * unveränderten Code grün, weil der Vertrag bereits unverändert gilt.
 */

let container: HTMLDivElement | null = null;
let root: Root | null = null;

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

describe('P-GRAPHSTART — "+ Graph erstellen" liefert einen leeren Graphen (Vertrags-Riegel)', () => {
  beforeEach(() => {
    const doc = new KosmoDoc();
    useProject.setState({ doc, journal: [], revision: 0, activeStoreyId: null, selection: [] });
    useVisRuntime.setState({ aktiverGraphId: null, aufnahmen: {}, gespeicherteAnsichten: {}, reviewPins: {}, laeufe: {} });
  });

  it('der echte Knopf (GRAPH-Insel, leerer Zustand) liefert 0 Knoten/0 Kanten', () => {
    const Palette = visInhaltsRegistry.inhaltFuer('palette')!.Stufe2!;
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root!.render(<Palette />);
    });

    const knopf = q('visisl-graph-erstellen');
    expect(knopf, 'Erstellen-Knopf sichtbar (leerer Zustand, kein aktiver Graph)').not.toBeNull();

    act(() => {
      knopf!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });

    const graphId = useVisRuntime.getState().aktiverGraphId;
    expect(graphId, 'neuer Graph wurde aktiv').not.toBeNull();
    const graph = useProject.getState().doc.get<VisGraph>(graphId!)!;
    expect(graph.nodes).toHaveLength(0);
    expect(graph.edges).toHaveLength(0);
  });

  it('bleibt leer, auch wenn im Doc bereits ein ANDERER, voll verdrahteter Graph existiert', () => {
    // Deckt einen naheliegenden Fehlschluss ab: dass "+Graph erstellen"
    // irgendwie vom bestehenden Graphen abschreibt/kopiert.
    const { doc } = useProject.getState();
    const altId = (execute(doc, 'vis.graphErstellen', { name: 'Bestehend, voll verdrahtet' }).patches[0] as { id: string }).id;
    execute(doc, 'vis.nodeSetzen', { graphId: altId, typ: 'modell', x: 0, y: 0 });
    execute(doc, 'vis.nodeSetzen', { graphId: altId, typ: 'kamera', x: 0, y: 200 });
    execute(doc, 'vis.nodeSetzen', { graphId: altId, typ: 'render', x: 400, y: 100 });
    useProject.setState((s) => ({ revision: s.revision + 1 }));
    const altGraphVorher = useProject.getState().doc.get<VisGraph>(altId)!;
    expect(altGraphVorher.nodes).toHaveLength(3);

    const neuId = neuerGraphErstellen();
    expect(neuId).not.toBeUndefined();
    const neuerGraph = useProject.getState().doc.get<VisGraph>(neuId!)!;
    expect(neuerGraph.nodes).toHaveLength(0);
    expect(neuerGraph.edges).toHaveLength(0);

    // der alte, verdrahtete Graph bleibt unangetastet daneben stehen
    const altGraphNachher = useProject.getState().doc.get<VisGraph>(altId)!;
    expect(altGraphNachher.nodes).toHaveLength(3);
  });
});
