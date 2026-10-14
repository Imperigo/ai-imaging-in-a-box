// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { VisGraph, VisNode } from '@kosmo/kernel';
import { BildKachel } from '../src/modules/vis/NodeCanvas';
import { KuratierInspektor } from '../src/modules/vis/KuratierInspektor';
import { laufGrund, laufUrteil, treueText } from '../src/modules/vis/render-verlauf';
import {
  bewertungsLage,
  sterneAusQa,
  varianteDiff,
  varianteMerkmale,
  type KuratierKartenDaten,
} from '../src/modules/vis/varianten-diff';
import type { JobQa } from '../src/modules/vis/vis-jobs';

/**
 * Owner-Entscheid E189 (bei uns 70): fuellt das Haus weniger als 20 % des
 * Bildes, ist das Urteil «nicht beurteilbar» statt «durchgefallen». Der
 * Vertrag bleibt: `verdict.passed` und `qa.geometry.passed` sind weiter
 * `false`; die Bildseite schreibt in `verdict.reason` einen Satz mit dem
 * Grossbuchstaben-Wort «NICHT BEURTEILBAR» (heute «(Gebaeudeanteil)», schon
 * laenger «(Rahmung)»). Andere Saetze koennen davor stehen.
 *
 * Bis hierhin las jede Anzeige nur `passed` und zeigte ✗ / «durchgefallen» /
 * «verfehlt» — rot, obwohl der Absender ausdruecklich sagt, dass nicht
 * geurteilt wurde.
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

const SATZ_GEBAEUDE =
  "NICHT BEURTEILBAR (Gebaeudeanteil): Das Haus fuellt nur 18% des Bildes, weniger als 20 %; der Gesamtwert ist hier nicht anwendbar. 'passed: false' heisst hier nicht durchgefallen, sondern nicht beurteilbar.";
const SATZ_DAVOR = `SCHWELLE FUER DIESE AUFNAHME UNERREICHBAR: die Nullprobe liegt ueber der Schwelle. ${SATZ_GEBAEUDE}`;
const SATZ_RAHMUNG = 'NICHT BEURTEILBAR (Rahmung): Das Haus ist angeschnitten; der Gesamtwert ist hier nicht anwendbar.';

function qa(passed: boolean, reason?: string): JobQa {
  return {
    verdict: { passed, ...(reason !== undefined ? { reason } : {}) },
    geometry: { rho_maske: 0.31, threshold: 0.65, passed, method: 'probe', status: 'measured' },
    style: { style_score: 0.7, threshold: 0.3, passed: true, method: 'probe' },
  };
}
const NB_GEBAEUDE = qa(false, SATZ_GEBAEUDE);
const NB_DAVOR = qa(false, SATZ_DAVOR);
const NB_RAHMUNG = qa(false, SATZ_RAHMUNG);
const FEHL = qa(false, 'Das Bild zeigt einen Anbau, den die Geometrie nicht hat.');
const FEHL_KLEIN = qa(false, 'Ein Teil ist nicht beurteilbar, der Rest faellt durch.');
const OK = qa(true);

let root: Root | null = null;
let container: HTMLDivElement | null = null;
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  vi.unstubAllGlobals();
});
function mount(el: React.ReactElement): HTMLDivElement {
  if (root) act(() => root!.unmount());
  container?.remove();
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(el));
  return container;
}
function stubBridge(): void {
  vi.stubGlobal('fetch', (async () =>
    ({ ok: true, status: 200, blob: async () => new Blob(['x'], { type: 'image/png' }) }) as Response) as unknown as typeof fetch);
}

const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };
const graph: VisGraph = { id: 'g1', kind: 'visgraph', name: 'T', nodes: [node], edges: [] };
function karte(q: JobQa): KuratierKartenDaten {
  return { node, quelle: { jobId: 'j1', bild: 'b.png', qa: q }, kur: { markiert: false, verworfen: false } };
}
function kachelQa(q: JobQa): HTMLElement {
  stubBridge();
  const c = mount(<BildKachel jobId="j1" bild="b.png" qa={q} alt="Bild" />);
  return c.querySelector<HTMLElement>('.vis-bild-kachel-qa')!;
}
function inspektorVerdikt(q: JobQa): string {
  stubBridge();
  const c = mount(<KuratierInspektor graph={graph} karte={karte(q)} id="V-01" onMarkieren={() => {}} onVerwerfen={() => {}} onInsProjekt={() => {}} />);
  const zeile = [...c.querySelectorAll('*')].find((e) => e.children.length > 0 && e.textContent?.startsWith('QA-Verdikt'));
  return zeile?.textContent?.replace('QA-Verdikt', '').trim() ?? '';
}

describe('E189 — passed:false mit «NICHT BEURTEILBAR» im Grund ist nicht beurteilbar, nicht durchgefallen', () => {
  for (const [name, q] of [
    ['Gebaeudeanteil', NB_GEBAEUDE],
    ['anderer Satz davor', NB_DAVOR],
    ['Rahmung', NB_RAHMUNG],
  ] as const) {
    it(`${name}: Kachel, Verlauf, Inspektor, Vergleich und Sterne`, () => {
      const k = kachelQa(q);
      expect(k.textContent, 'Kachel').toBe('QA nicht beurteilbar ⚠');
      expect(k.classList.contains('vis-bild-kachel-qa--fehl'), 'Kachel nicht rot').toBe(false);
      expect(k.classList.contains('vis-bild-kachel-qa--neutral'), 'Kachel neutral').toBe(true);
      // Der Satz des Absenders steht woertlich darunter.
      expect(container!.querySelector('[data-testid="vis-bild-kachel-qa-vorbehalt"]')!.textContent).toBe(q.verdict.reason);

      expect(laufUrteil(q), 'Verlauf').toBe('nicht-beurteilbar');
      expect(laufGrund(q)).toBe(q.verdict.reason);
      expect(treueText(q)).toBe('nicht anwendbar — siehe Grund');

      expect(inspektorVerdikt(q), 'Inspektor').toBe('nicht beurteilbar');
      expect(container!.textContent).toContain('Nicht beurteilbar — der Grund steht unter «QA-Vorbehalt», keine Wertung.');

      const m = varianteMerkmale(node, undefined, q);
      const zeile = varianteDiff(m, varianteMerkmale(node, undefined, OK)).find((z) => z.label === 'QA-Verdikt')!;
      expect(zeile.a, 'Vergleich').toBe('nicht beurteilbar');
      expect(zeile.b).toBe('bestanden');

      expect(sterneAusQa(q), 'Sterne gelten nicht').toBe(0);
      expect(bewertungsLage(q)).toBe('nicht-beurteilbar');
    });
  }

  it('Gegenprobe: passed:false ohne das Grossbuchstaben-Wort bleibt ✗ / durchgefallen / verfehlt', () => {
    for (const q of [FEHL, FEHL_KLEIN, qa(false)]) {
      const k = kachelQa(q);
      expect(k.textContent!.startsWith('QA ✗')).toBe(true);
      expect(k.classList.contains('vis-bild-kachel-qa--fehl')).toBe(true);
      expect(laufUrteil(q)).toBe('durchgefallen');
      expect(inspektorVerdikt(q)).toBe('verfehlt');
      expect(varianteDiff(varianteMerkmale(node, undefined, q), varianteMerkmale(node, undefined, OK)).find((z) => z.label === 'QA-Verdikt')!.a).toBe('verfehlt');
      expect(sterneAusQa(q)).toBeGreaterThan(0);
      expect(bewertungsLage(q)).toBe('bewertet');
    }
  });

  it('Gegenprobe: passed:true bleibt bestanden, auch wenn der Grund das Wort enthielte', () => {
    for (const q of [OK, qa(true, SATZ_GEBAEUDE)]) {
      const k = kachelQa(q);
      expect(k.textContent!.startsWith('QA ok')).toBe(true);
      expect(k.classList.contains('vis-bild-kachel-qa--ok')).toBe(true);
      expect(laufUrteil(q)).toBe('bestanden');
      expect(inspektorVerdikt(q)).toBe('bestanden');
      expect(bewertungsLage(q)).toBe('bewertet');
    }
  });
});
