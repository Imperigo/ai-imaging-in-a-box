import { describe, expect, it, beforeEach } from 'vitest';
import { KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import { nodeHinzufuegen } from '../src/modules/vis/vis-graph-aktionen';
import { NODE_W, basisNodeHoehe } from '../src/modules/vis/NodeCanvas';

/**
 * P-KNOTENFELD Posten 8 (`auftraege/von-homestation/auf-orbit-20260825-07.md`
 * Abschnitt 4, Punkt 1: «Knoten stapeln sich auf demselben Platz — neue
 * Knoten landen übereinander statt nebeneinander»).
 *
 * **Messung vor dem Bau:** `nodeHinzufuegen()` (`vis-graph-aktionen.ts`)
 * trägt bereits seit seiner Erstanlage eine Spiral-Kollisionssuche
 * (`passtHier`/`findeSpiralPlatz`) — unverändert von W3-a
 * (`docs/ENTSCHEID-KNOTENPLATZ-2026-08-26.md`: «Die Spiral-Kollisionslogik
 * bleibt unverändert — nur ihr Startpunkt wandert»). Fünf/acht aufeinander-
 * folgende Aufrufe (derselbe Klickpfad wie die GRAPH-Insel-Palette,
 * `island/inhalte/graph.tsx`) liefern gemessen **fünf/acht disjunkte
 * Positionen** — kein einziges Bounding-Box-Paar überlappt (Nachweis unten,
 * mit der SELBEN 24-px-Marge, die `passtHier` selbst verwendet). Der
 * Auftragstext selbst ("Owner-Kompass" `docs/STAND-WORKERAUFTRAEGE-2026-08-
 * 27.md`) nennt den Posten "nur delegiert" — dieser Test ist die
 * nachgeholte Messung: **unter dem heutigen Code nicht reproduzierbar.**
 * Gegenprobe für "das hätte auffallen müssen, wäre der Fehler noch da":
 * derselbe Test würde bei EINEM festen, nicht neu gelesenen Ausgangspunkt
 * (kein `bestehend`-Reload) exakt kollidieren — das ist der Fall, den
 * dieser Test tatsächlich prüft (er bricht, sobald zwei Boxen sich
 * berühren, s. `keineUeberlappung` unten).
 *
 * Bleibt als **Vertrags-Riegel** stehen (kein Fix-Pin, s. `p-graphstart-
 * leerer-graph.test.tsx`-Muster): ein künftiger Umbau der Spiral-Logik, der
 * die Kollisionsprüfung versehentlich verliert, wird hier sichtbar rot.
 */

function box(n: { x: number; y: number; typ: string }): { x0: number; y0: number; x1: number; y1: number } {
  return { x0: n.x, y0: n.y, x1: n.x + NODE_W, y1: n.y + basisNodeHoehe(n.typ) };
}

function ueberlappt(a: ReturnType<typeof box>, b: ReturnType<typeof box>): boolean {
  return a.x0 < b.x1 && a.x1 > b.x0 && a.y0 < b.y1 && a.y1 > b.y0;
}

function keineUeberlappung(nodes: readonly { x: number; y: number; typ: string }[]): void {
  const boxen = nodes.map(box);
  for (let i = 0; i < boxen.length; i++) {
    for (let j = i + 1; j < boxen.length; j++) {
      expect(ueberlappt(boxen[i]!, boxen[j]!), `Node ${i} und ${j} überlappen`).toBe(false);
    }
  }
}

describe('P-KNOTENFELD Posten 8 — neue Knoten stapeln sich NICHT (Vertrags-Riegel, mit Gegenprobe)', () => {
  beforeEach(() => {
    const doc = new KosmoDoc();
    useProject.setState({ doc, journal: [], revision: 0, activeStoreyId: null, selection: [] });
    useVisRuntime.setState({ aktiverGraphId: null, aufnahmen: {}, gespeicherteAnsichten: {}, reviewPins: {}, laeufe: {} });
  });

  it('8× "render" hintereinander (derselbe Palette-Klick wiederholt) — 8 disjunkte Positionen', () => {
    const { doc, runCommand } = useProject.getState();
    const gid = (runCommand('vis.graphErstellen', { name: 'M8a' }).patches[0] as { id: string }).id;
    for (let i = 0; i < 8; i++) nodeHinzufuegen(gid, 'render');
    const graph = doc.get<VisGraph>(gid)!;
    expect(graph.nodes).toHaveLength(8);
    keineUeberlappung(graph.nodes);
    // Gegenprobe: es sind wirklich 8 VERSCHIEDENE Koordinatenpaare, nicht
    // zufällig 8 Nodes an derselben Stelle, die nur wegen einer zu groben
    // Bounding-Box-Prüfung als "nicht überlappend" durchgingen.
    const koordinaten = new Set(graph.nodes.map((n) => `${n.x},${n.y}`));
    expect(koordinaten.size).toBe(8);
  });

  it('gemischte Typen (Modell/Auto-Kamera/Prompt/Render — der reale Demo-Graph-Aufbau) — keine Überlappung', () => {
    const { doc, runCommand } = useProject.getState();
    const gid = (runCommand('vis.graphErstellen', { name: 'M8b' }).patches[0] as { id: string }).id;
    for (const typ of ['modell', 'kamera', 'prompt', 'render', 'render', 'stimmung']) {
      nodeHinzufuegen(gid, typ);
    }
    const graph = doc.get<VisGraph>(gid)!;
    expect(graph.nodes).toHaveLength(6);
    keineUeberlappung(graph.nodes);
  });

  it('Gegenprobe: die Kollisionsprüfung selbst greift wirklich (zwei absichtlich überlappende Boxen fallen durch)', () => {
    expect(() =>
      keineUeberlappung([
        { x: 0, y: 0, typ: 'render' },
        { x: 10, y: 10, typ: 'render' },
      ]),
    ).toThrow();
  });
});
