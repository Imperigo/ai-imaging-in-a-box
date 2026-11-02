// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { execute, History, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { NodeCanvas } from '../../kosmo-orbit/src/modules/vis/NodeCanvas';
import { BILDWERKZEUG_IDS } from '../../kosmo-orbit/src/modules/vis/vis-jobs';
import { leereKiZustand, offeneVorschlaege } from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';
import { setzeCoopZurueck, setzeModusVonApp } from '../../kosmo-orbit/src/state/kosmo-coop';
import { haengeKiAn, type VisboxKi } from '../src/ki-wirt';
import type { VollLage } from '../src/voll-render';

/**
 * A0093 (Owner-Entscheid «Immer vom Render», 31.10.2026; KosmoOrbit A0061, eingespielt in v0.1.12, Stand 7e4c1b6ca):
 * die Knotenansicht der Visbox sperrt wie KosmoOrbit.
 *
 * (a) Am Wähler «Bildwerkzeug» ist nur Z-Image Turbo wählbar; jedes Bildwerkzeug ohne belegten Start vom Render steht
 *     mit «gesperrt bis Messung» da und ist nicht wählbar. Vorher: 7 von 7 wählbar.
 * (b) Der Knopf «Vorschau» an der Güte ist gesperrt. Vorher: wählbar.
 * (c) `window.visboxKi.rufe` mit `vis_render` und einem gesperrten Bildwerkzeug wird schon in der Seite abgewiesen —
 *     keine Karte, kein Auftrag im Dokument, kein Aufruf der Brücke. Vorher: Karte bzw. POST /bruecke/jobs.
 * (e) Die Kurzhilfe der Vorschau sagt den Stand nach A0051b: die Brücke startet die Vorschau seither selbst vom
 *     Grundbild, gemessen ist es nicht — darum gesperrt bis zur Messung.
 *
 * Gegen den Stand vor A0093 rot. Alle Namen erfunden (Regel 3).
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
(globalThis as unknown as { ResizeObserver: unknown }).ResizeObserver = class {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
};

const GESPERRT = ['qwen', 'qwen-image-2.1', 'sdxl', 'flux2-klein'] as const;
const FREI: VollLage = { frei: true, laeufe: 0, grenze: 5, wiederFreiAb: null };

let graphId = '';
let renderId = '';
let container: HTMLDivElement | null = null;
let root: Root | null = null;
let ab: () => void = () => undefined;
let fetchZahl = 0;

const q = (id: string): HTMLElement | null => document.body.querySelector(`[data-testid="${id}"]`);

function neuesDokument(): KosmoDoc {
  const doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 0, y: 0 });
  renderId = doc.get<VisGraph>(graphId)!.nodes[0]!.id;
  return doc;
}

function zeichne(): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
}

beforeEach(() => {
  leereKiZustand();
  setzeCoopZurueck();
  useProject.setState({ doc: neuesDokument(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] } as never);
  useVisRuntime.setState({ aktiverGraphId: graphId, laeufe: {} });
  fetchZahl = 0;
  vi.stubGlobal('fetch', (async () => {
    fetchZahl++;
    return { ok: true, json: async () => ({}) };
  }) as unknown as typeof fetch);
});

afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  ab();
  ab = () => undefined;
  leereKiZustand();
  setzeCoopZurueck();
  vi.unstubAllGlobals();
});

describe('A0093 (a) — Wähler «Bildwerkzeug»: nur Z-Image Turbo wählbar', () => {
  it('die übrigen fünf stehen gesperrt mit «gesperrt bis Messung» da', () => {
    zeichne();
    const waehler = q('render-bildwerkzeug') as HTMLButtonElement | null;
    expect(waehler, 'Wähler am Render-Knoten').not.toBeNull();
    act(() => waehler!.click());
    const optionen = [...document.body.querySelectorAll<HTMLButtonElement>('[role="option"]')];
    expect(optionen).toHaveLength(1 + BILDWERKZEUG_IDS.length);
    const wert = (o: HTMLButtonElement) => o.getAttribute('data-value') ?? '';
    const waehlbar = optionen.filter((o) => !o.disabled).map(wert);
    expect(waehlbar, 'wählbar: nur die Vorgabe und Z-Image Turbo').toEqual(['', 'z-image-turbo']);
    // Messgrösse von A0093: wählbare gesperrte Werkzeuge in der Seite → 0 (heute fünf: Qwen-Image-Edit, Qwen-Image 2.1, SDXL,
    // FLUX.2 [klein], FLUX.1-Krea; die Vorgabe und Z-Image Turbo sind dasselbe Werkzeug).
    const gesperrt = optionen.filter((o) => o.disabled);
    expect(gesperrt.map(wert).sort()).toEqual([...GESPERRT, 'flux-krea'].sort());
    for (const o of gesperrt) expect(o.textContent, wert(o)).toContain('gesperrt bis Messung');
    // Ein Klick auf ein gesperrtes Werkzeug setzt nichts.
    act(() => gesperrt[0]!.click());
    const n = useProject.getState().doc.get<VisGraph>(graphId)!.nodes.find((x) => x.id === renderId)!;
    expect(n.params?.['backbone']).toBeUndefined();
  });
});

describe('A0093 (b) — Knopf «Vorschau» an der Güte gesperrt', () => {
  it('render-guete-vorschau ist gesperrt, ein Klick ändert die Wahl am Knoten nicht', () => {
    zeichne();
    const knopf = q('render-guete-vorschau') as HTMLButtonElement | null;
    expect(knopf, 'Knopf «Vorschau»').not.toBeNull();
    expect(knopf!.getAttribute('aria-disabled')).toBe('true');
    expect(knopf!.getAttribute('data-gesperrt')).toBe('true');
    act(() => knopf!.click());
    const n = useProject.getState().doc.get<VisGraph>(graphId)!.nodes.find((x) => x.id === renderId)!;
    expect(n.params?.['guete']).not.toBe('vorschau');
  });
});

describe('A0093 (c) — window.visboxKi weist gesperrte Bildwerkzeuge in der Seite ab', () => {
  for (const modus of ['karte', 'voll'] as const) {
    for (const bb of GESPERRT) {
      it(`vis_render mit backbone «${bb}» (${modus}): sofort abgewiesen, keine Karte, kein Auftrag, keine Brücke`, () => {
        setzeModusVonApp(modus === 'voll' ? 'voll' : 'coop');
        ab = haengeKiAn(window, null);
        const ki = (window as unknown as { visboxKi: VisboxKi }).visboxKi;
        const a = ki.rufe(
          { kennung: `A93-${bb}`, werkzeug: 'vis_render', argumente: { graphId, nodeId: renderId, kameraWahl: 'auto', guete: 'voll', backbone: bb } },
          modus,
          modus === 'voll' ? FREI : null,
        );
        expect('sofort' in a, 'keine Karte').toBe(true);
        const text = 'sofort' in a ? a.sofort.text : '';
        expect(text).toContain(`Bildwerkzeug «${bb}» ist gesperrt`);
        expect(text).toContain('Nichts wurde bestellt');
        expect(offeneVorschlaege()).toEqual([]);
        expect(useProject.getState().doc.settings.visRenderAuftrag ?? null).toBeNull();
        expect(fetchZahl, 'kein Aufruf der Brücke').toBe(0);
      });
    }
  }

  it('Vorgabe Z-Image Turbo bleibt bestellbar (Karte wie bisher)', () => {
    setzeModusVonApp('coop');
    ab = haengeKiAn(window, null);
    const ki = (window as unknown as { visboxKi: VisboxKi }).visboxKi;
    const a = ki.rufe({ kennung: 'A93-zit', werkzeug: 'vis_render', argumente: { graphId, nodeId: renderId, kameraWahl: 'auto', guete: 'voll' } }, 'karte', null);
    expect('karte' in a).toBe(true);
  });
});

describe('A0093 (e) — Kurzhilfe der Vorschau nach A0051b', () => {
  it('am gesperrten Knopf: startet an der Brücke vom Grundbild (A0051b), ungemessen, darum gesperrt bis Messung', () => {
    zeichne();
    const knopf = q('render-guete-vorschau')!;
    const ids = (knopf.getAttribute('aria-describedby') ?? '').split(' ').filter(Boolean);
    const kurzhilfe = ids.map((id) => document.getElementById(id)?.textContent ?? '').join(' ');
    // Vorher: der Text der Vorschau aus KosmoOrbit, «ohne das Grundbild als Bildeingang» — für die Visbox seit A0051b falsch.
    expect(kurzhilfe).not.toContain('ohne das Grundbild als Bildeingang');
    expect(kurzhilfe).not.toContain('ohne das Beauty-Render als Bildeingang');
    expect(kurzhilfe).toContain('gesperrt bis Messung');
    expect(kurzhilfe).toContain('A0051b');
    expect(kurzhilfe).toContain('vom Grundbild');
    expect(kurzhilfe).toContain('nicht gemessen');
    expect(kurzhilfe).toContain('«Voll» wählen');
  });
});
