// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { History, KosmoDoc, VARIANTEN_TYP, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { FreiesBildMarke } from '../src/modules/vis/FreiesBildMarke';
import * as freiesBild from '../src/modules/vis/freies-bild';
import { FREIES_BILD_ABSAGE, FREIES_BILD_MARKE_TEXT, SATZ_FREIES_BILD, freiesBildAusErgebnis, freiesBildZusatz } from '../src/modules/vis/freies-bild';
import { sendeGraphRenderAuftrag } from '../src/modules/vis/vis-jobs';

/**
 * A0256 (Owner-Entscheid Masstreue 30.10.2026: «jedes bild muss basierend auf blender render und multipasses
 * laufen»; Abgleich mit KosmoOrbit A0049): am Varianten-Knoten bietet nichts mehr ein KI-Bild ohne Blender-Render
 * an. Der Haken «Freies Bild (ohne Grundbild)» und das Wort «Frei» sind weg, eine Bestellung traegt nie
 * `vis.freies_bild: true`, eine alte Wahl am Knoten gilt nicht mehr. Bereits gerechnete freie Bilder bleiben
 * lesbar und tragen ihre Marke. Alle Namen erfunden; die Bruecke ist eine Attrappe.
 */
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;

const hier = path.dirname(fileURLToPath(import.meta.url));
const quelltext = (datei: string): string => readFileSync(path.join(hier, '../src/modules/vis', datei), 'utf8');

let root: Root | null = null;
let container: HTMLDivElement | null = null;
function zeige(el: React.ReactElement): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(el));
}
const q = (id: string): HTMLElement | null => document.body.querySelector(`[data-testid="${id}"]`);

beforeEach(() => {
  useProject.setState({ doc: new KosmoDoc(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: null, aufnahmen: {}, gespeicherteAnsichten: {}, reviewPins: {}, laeufe: {} });
});
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  vi.unstubAllGlobals();
});

function graphMit(typ: string, params?: Record<string, unknown>): { gid: string; nid: string } {
  const { runCommand } = useProject.getState();
  const gid = (runCommand('vis.graphErstellen', { name: 'Ohne Frei' }).patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId: gid, typ, x: 40, y: 40, ...(params ? { params } : {}) });
  const g = useProject.getState().doc.get<VisGraph>(gid)!;
  return { gid, nid: g.nodes[g.nodes.length - 1]!.id };
}

describe('A0256 · Oberflaeche', () => {
  it('der Varianten-Knoten hat keinen Haken «Freies Bild (ohne Grundbild)»', () => {
    const { gid } = graphMit(VARIANTEN_TYP);
    zeige(<NodeCanvas graphId={gid} />);
    expect(q('varianten-freigeben')).not.toBeNull(); // der Knoten steht
    expect(q('varianten-freies-bild')).toBeNull();
    expect(q('varianten-freies-bild-zeile')).toBeNull();
    expect(document.body.textContent).not.toContain('Freies Bild (ohne Grundbild)');
  });

  it('auch ein Knoten aus einem alten Projekt (freiesBild: true) zeigt keinen Haken', () => {
    const { gid } = graphMit(VARIANTEN_TYP, { freiesBild: true });
    zeige(<NodeCanvas graphId={gid} />);
    expect(q('varianten-freies-bild')).toBeNull();
    expect(document.body.textContent).not.toContain('Freies Bild (ohne Grundbild)');
  });

  it('die Zeile «Güte» am Render-Knoten kennt das Wort «Frei» nicht mehr', () => {
    const { gid } = graphMit('render', { freiesBild: true });
    zeige(<NodeCanvas graphId={gid} />);
    expect(q('render-guete')).not.toBeNull();
    expect(q('render-guete-frei')).toBeNull();
    expect(q('render-guete')!.textContent).not.toMatch(/\bFrei\b/);
    expect(q('render-guete')!.getAttribute('data-freies-bild')).toBeNull();
  });
});

describe('A0256 · Bestellung', () => {
  it('ein ausdruecklich verlangtes freies Bild wird abgewiesen, die Bruecke wird nicht gerufen', () => {
    const { gid, nid } = graphMit('render');
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    const saetze: string[] = [];
    const hoere = (e: Event) => saetze.push(String((e as CustomEvent<{ text: string }>).detail.text));
    window.addEventListener('kosmo-fehlermeldung', hoere);
    try {
      sendeGraphRenderAuftrag(gid, nid, undefined, { freiesBild: true });
    } finally {
      window.removeEventListener('kosmo-fehlermeldung', hoere);
    }
    expect(fetchMock).not.toHaveBeenCalled();
    expect(saetze).toContain(FREIES_BILD_ABSAGE);
    expect(FREIES_BILD_ABSAGE).toMatch(/Blender/);
  });

  it('der Bestellweg liest keine Wahl am Knoten mehr und setzt `freies_bild: true` nie', () => {
    expect('freiesBildAmKnoten' in freiesBild).toBe(false);
    for (const datei of ['vis-jobs.ts', 'varianten.ts', 'VariantenKnoten.tsx', 'NodeCanvas.tsx']) {
      const t = quelltext(datei);
      expect(t, datei).not.toMatch(/freiesBildAmKnoten/);
      expect(t, datei).not.toMatch(/freies_bild\s*:\s*true/);
    }
    expect(quelltext('VariantenKnoten.tsx')).not.toMatch(/FREIES_BILD_(NAME|HINWEIS)/);
    expect(quelltext('NodeCanvas.tsx')).not.toMatch(/FREIES_BILD_(NAME|HINWEIS|WORT)|onFrei\b|VARIANTEN_FREI_H/);
  });

  it('der Katalog der KI-Werkzeuge bietet den Parameter freiesBild nicht mehr an', () => {
    expect(quelltext('ki-werkzeuge.ts')).not.toMatch(/FREIES_BILD_PARAM|FREIES_BILD_HINWEIS/);
  });
});

describe('A0256 · bereits gerechnete freie Bilder bleiben lesbar', () => {
  it('das Ergebnis meldet es (freies_bild oder der Satz der Gegenseite), die Marke steht', () => {
    expect(freiesBildAusErgebnis({ freies_bild: true })).toBe(true);
    expect(freiesBildAusErgebnis({ qa: { verdict: { hinweise: [`${SATZ_FREIES_BILD}: ohne Grundbild`] } } })).toBe(true);
    expect(freiesBildAusErgebnis({})).toBeUndefined();
    expect(freiesBildZusatz({ freiesBild: true })).toBe(`, ${FREIES_BILD_MARKE_TEXT}`);
    zeige(<FreiesBildMarke lauf={{ freiesBild: true }} testid="marke" />);
    expect(q('marke')?.textContent).toBe(FREIES_BILD_MARKE_TEXT);
  });
});
