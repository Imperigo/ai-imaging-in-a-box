// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { evaluiereGraph, VARIANTEN_TYP, variantenLaufId, type VisGraph } from '@kosmo/kernel';
import { RenderResult } from '@kosmo/contracts';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { holeLetzteLaeufe, merkeLetztenLauf, type GeholterAuftrag } from '../src/modules/vis/letzter-lauf';
import {
  anzeigeLaufAmKnoten,
  letzterFertigerLauf,
  letzterVersuchSatz,
  memoKey,
  useVisRuntime,
  type NodeLauf,
} from '../src/modules/vis/vis-runtime';
import {
  holeLetzteVarianten,
  LETZTE_BESTELLUNG_PARAM,
  letzteBestellungAmKnoten,
  merkeVariantenLauf,
  useVariantenBestellung,
  variantenZellen,
} from '../src/modules/vis/varianten';
import { useProject } from '../src/state/project-store';

/**
 * Generalprobe 373 (S8 rot, B6/B7, 27.10.2026): ein abgebrochener zweiter Lauf nahm dem Render-Knoten sein letztes
 * fertiges Bild — ABGEBROCHEN ohne Bild, der Bildvergleich leer, «Aufs Plakat» sagte «Kein fertiger Render», kein PDF.
 * Nach einem Neustart waren Varianten-Knoten und Bildvergleich leer.
 *
 * Ursache: Knoten, Bildvergleich, Kuratier-Karte und «Aufs Plakat» lasen nur den AKTUELLEN Lauf; das fertige Bild lag
 * schon im Verlauf, wurde aber nur von «Aufs Blatt» und den fruehen Kuratier-Karten gelesen. Die Bestellung des
 * Varianten-Knotens war reine Laufzeit.
 *
 * Gegen den alten Stand rot: «Knoten und Vergleich behalten das Bild …» (render-bild fehlte, vergleich-leer stand), die
 * Wiederherstellung neben einem Lauf ohne Bild (gab 0 zurueck, nichts im Verlauf) und «Varianten nach dem Öffnen»
 * (keine Funktion, kein Parameter). Namen erfunden.
 */

class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
if (!('createObjectURL' in URL)) {
  Object.assign(URL, { createObjectURL: () => 'blob:stub', revokeObjectURL: () => undefined });
}

const ERSTER = 'vis-1792688229-591d59';
const ZWEITER = 'vis-1792688999-0a0b0c';

function ergebnis(): RenderResult {
  const pfad = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    '../../../packages/kosmo-contracts/test/fixtures/kv-grundlage-variante.json',
  );
  return RenderResult.parse(JSON.parse(readFileSync(pfad, 'utf8')));
}

function auftrag(jobId = ERSTER): GeholterAuftrag & Record<string, unknown> {
  return { job_id: jobId, status: 'done', scene: 'scene.json', created_at: '2026-10-27T15:00:00Z', updated_at: '2026-10-27T15:03:00Z', result: ergebnis() };
}

const fertig = (jobId: string, bild = 'render_0.png'): NodeLauf => ({ status: 'fertig', jobId, bild, memoKey: 'm', bilder: [bild] });

let root: Root | null = null;
let container: HTMLDivElement | null = null;
let graphId = '';
let renderId = '';
let vergleichId = '';

function montiere(): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
}

async function warte(): Promise<void> {
  for (let i = 0; i < 10; i++) {
    await act(async () => {
      await Promise.resolve();
    });
  }
}

beforeEach(() => {
  vi.stubGlobal('fetch', (async (url: unknown) => {
    const href = String(url);
    if (href.includes('/artifacts/')) return { ok: true, status: 200, blob: async () => new Blob(['x'], { type: 'image/png' }) } as Response;
    if (href.includes(`/jobs/${ERSTER}`)) return { ok: true, status: 200, json: async () => auftrag(ERSTER) } as Response;
    return { ok: false, status: 404, json: async () => ({}) } as Response;
  }) as unknown as typeof fetch);
  useVisRuntime.setState({ laeufe: {}, verlauf: {}, laufZaehler: {} });
  useVariantenBestellung.setState({ bestellungen: {} });
  const { runCommand, doc } = useProject.getState();
  graphId = (runCommand('vis.graphErstellen', { name: `Letztes-${Math.random()}` }).patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 40, y: 20 });
  renderId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'vergleich', x: 400, y: 20 });
  vergleichId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  runCommand('vis.verbinden', { graphId, from: renderId, fromPort: 'bild', to: vergleichId, toPort: 'bild1' });
});

afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  vi.unstubAllGlobals();
});

describe('S8 — das letzte fertige Bild ist vom laufenden Zustand getrennt', () => {
  it('letzterFertigerLauf: der aktuelle mit Bild, sonst der neueste fertige im Verlauf', () => {
    const a = fertig(ERSTER);
    const ab: NodeLauf = { status: 'abgebrochen', jobId: ZWEITER, memoKey: 'm' };
    expect(letzterFertigerLauf(a, [])).toBe(a);
    expect(letzterFertigerLauf(ab, [a])).toBe(a);
    expect(letzterFertigerLauf(ab, [])).toBeUndefined();
    expect(letzterFertigerLauf(undefined, [ab, a])).toBe(a);
  });

  it('anzeigeLaufAmKnoten: nur ein Lauf, der OHNE Bild endete, macht dem letzten fertigen Platz', () => {
    const a = fertig(ERSTER);
    for (const status of ['abgebrochen', 'fehler', 'zeitueberschreitung'] as const) {
      const v: NodeLauf = { status, jobId: ZWEITER, memoKey: 'm' };
      expect(anzeigeLaufAmKnoten(v, [a])).toEqual({ lauf: a, versuch: v });
    }
    // Ein Lauf, der noch rechnet, behaelt den Bildplatz (Fortschritt); ohne fertiges Bild bleibt alles wie bisher.
    const r: NodeLauf = { status: 'rendert', jobId: ZWEITER, memoKey: 'm' };
    expect(anzeigeLaufAmKnoten(r, [a])).toEqual({ lauf: r });
    const ab: NodeLauf = { status: 'abgebrochen', jobId: ZWEITER, memoKey: 'm' };
    expect(anzeigeLaufAmKnoten(ab, [])).toEqual({ lauf: ab });
    expect(letzterVersuchSatz(ab, 1)).toBe('Letzter Lauf abgebrochen — das Bild ist Lauf 1');
  });

  it('Knoten und Bildvergleich behalten das Bild, wenn der zweite Lauf abgebrochen wird', async () => {
    const { setzeLauf, patchLauf } = useVisRuntime.getState();
    const g = useProject.getState().doc.get<VisGraph>(graphId)!;
    const schluessel = memoKey(evaluiereGraph(useProject.getState().doc, g).renderAuftraege.get(renderId)!);
    setzeLauf(renderId, { ...fertig(ERSTER), memoKey: schluessel });
    setzeLauf(renderId, { status: 'wartetFreigabe', jobId: ZWEITER, memoKey: 'm2' });
    patchLauf(renderId, { status: 'abgebrochen' });
    expect(useVisRuntime.getState().laeufe[renderId]!.status, 'der Lauf selbst bleibt abgebrochen').toBe('abgebrochen');
    montiere();
    await warte();
    const knoten = container!.querySelector('[data-testid="vis-node-render"]')!;
    expect(knoten.querySelector('[data-testid="render-hauptbild"]'), 'das Bild steht am Knoten').not.toBeNull();
    expect(knoten.querySelector('[data-testid="render-letzter-versuch"]')?.textContent).toMatch(/abgebrochen/i);
    const vergleich = container!.querySelector('[data-testid="vis-node-vergleich"]')!;
    expect(vergleich.textContent).not.toContain('verbinde Render-Bilder');
  });
});

describe('S8 — Wiederholen nach dem Öffnen neben einem Lauf ohne Bild', () => {
  it('der gemerkte Lauf kommt in den Verlauf, der Lauf am Knoten bleibt', async () => {
    const graph = useProject.getState().doc.get<VisGraph>(graphId)!;
    const schluessel = memoKey(evaluiereGraph(useProject.getState().doc, graph).renderAuftraege.get(renderId)!);
    merkeLetztenLauf(renderId, { graphId, memoKey: schluessel }, ERSTER);
    useVisRuntime.getState().setzeLauf(renderId, { status: 'abgebrochen', jobId: ZWEITER, memoKey: 'm2' });
    const g = useProject.getState().doc.get<VisGraph>(graphId)!;
    expect(await holeLetzteLaeufe(g, async () => auftrag())).toBe(1);
    expect(useVisRuntime.getState().laeufe[renderId]!.status).toBe('abgebrochen');
    expect(useVisRuntime.getState().verlauf[renderId]?.[0]?.jobId).toBe(ERSTER);
    expect(letzterFertigerLauf(useVisRuntime.getState().laeufe[renderId], useVisRuntime.getState().verlauf[renderId])?.jobId).toBe(ERSTER);
    // Ein zweiter Aufruf legt nichts doppelt ab.
    expect(await holeLetzteLaeufe(g, async () => auftrag())).toBe(0);
  });
});

describe('B7 — die letzte Bestellung des Varianten-Knotens übersteht das Öffnen', () => {
  it('merken (ohne Rückgängig-Schritt) und nach dem Öffnen wieder anlegen', async () => {
    const { runCommand, doc } = useProject.getState();
    runCommand('vis.nodeSetzen', { graphId, typ: VARIANTEN_TYP, x: 400, y: 400 });
    const vId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
    const laufId = variantenLaufId(vId, 'abend', 'aktuell');
    useVariantenBestellung.getState().setze({
      graphId,
      nodeId: vId,
      nr: 3,
      zeilen: ['Eingang'],
      stimmungen: ['abend'],
      entwuerfe: [{ id: 'aktuell', name: 'Aktuelles Modell' }],
      gruppen: [{ laufId, stimmung: 'abend', entwurf: 'aktuell', standpunkte: ['Eingang'] }],
      anzahl: 1,
    });
    const vorher = useProject.getState().history.undoStack.length;
    expect(merkeVariantenLauf(laufId, ERSTER)).toBe(true);
    expect(useProject.getState().history.undoStack.length, 'kein Schritt des Architekten').toBe(vorher);
    const knoten = () => useProject.getState().doc.get<VisGraph>(graphId)!.nodes.find((n) => n.id === vId)!;
    expect(letzteBestellungAmKnoten(knoten().params)?.gruppen[0]?.jobId).toBe(ERSTER);
    expect(merkeVariantenLauf('kein-lauf', ERSTER)).toBe(false);
    expect(merkeVariantenLauf(laufId, 'falsch')).toBe(false);

    // «Neustart»: Laufzeit leer, das Dokument traegt den Parameter.
    useVariantenBestellung.setState({ bestellungen: {} });
    useVisRuntime.setState({ laeufe: {}, verlauf: {}, laufZaehler: {} });
    const g = useProject.getState().doc.get<VisGraph>(graphId)!;
    expect(await holeLetzteVarianten(g, async () => auftrag())).toBe(1);
    const b = useVariantenBestellung.getState().bestellungen[vId]!;
    expect(b.nr).toBe(3);
    const zellen = variantenZellen(b, useVisRuntime.getState().laeufe);
    expect(zellen.map((z) => z.zustand)).toEqual(['fertig']);
    expect(zellen[0]!.jobId).toBe(ERSTER);
    // Unlesbares bleibt still.
    expect(letzteBestellungAmKnoten({ [LETZTE_BESTELLUNG_PARAM]: 'kein json' })).toBeNull();
  });
});
