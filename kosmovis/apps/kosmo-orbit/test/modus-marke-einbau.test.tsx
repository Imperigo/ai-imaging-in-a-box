// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import type { VisGraph, VisNode } from '@kosmo/kernel';
import { KuratierFlaeche } from '../src/modules/vis/KuratierFlaeche';
import { KuratierInspektor } from '../src/modules/vis/KuratierInspektor';
import { ModusMarke } from '../src/modules/vis/ModusMarke';
import { quelleAusLauf, type KuratierKartenDaten, type KuratierQuelle } from '../src/modules/vis/varianten-diff';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const OHNE = { modus: { bestellt: 'image_edit', gerechnet: 'txt2img', abweichung: true } };
const ANDERS = { modus: { bestellt: 'bild_und_tiefe', gerechnet: 'tiefe_als_bild', abweichung: true } };
const NULL = { modus: { bestellt: 'image_edit', gerechnet: null, abweichung: null } };
const q = (extra: object): KuratierQuelle => ({ jobId: 'vis-1-aaaaaa', bild: 'a.png', ...extra }) as KuratierQuelle;
const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };
const graph: VisGraph = { id: 'g1', kind: 'visgraph', name: 'T', nodes: [node, { ...node, id: 'n2' }], edges: [] } as VisGraph;
const karte = (id: string, quelle: KuratierQuelle): KuratierKartenDaten => ({ node: { ...node, id }, quelle, kur: { markiert: false, verworfen: false } });

let root: Root | null = null;
let host: HTMLDivElement | null = null;
afterEach(() => {
  if (root) act(() => root!.unmount());
  host?.remove();
  root = null;
  host = null;
});
function mount(el: React.ReactElement): HTMLDivElement {
  host = document.createElement('div');
  document.body.appendChild(host);
  root = createRoot(host);
  act(() => root!.render(el));
  return host;
}
const leer = () => {};

describe('ModusMarke: Formen', () => {
  it.each(['bild', 'abzeichen', 'zeile'] as const)('Ohne Grundlagenbild in Form %s', (form) => {
    const h = mount(<ModusMarke lauf={OHNE} testid="m" form={form} />);
    const m = h.querySelector('[data-testid="m"]')!;
    expect(m.textContent).toBe('Ohne Grundlagenbild');
    expect(m.getAttribute('data-modus')).toBe('ohne-grundlagenbild');
    expect(m.getAttribute('data-form')).toBe(form);
    expect(m.getAttribute('tabindex')).toBe('0');
  });
  it('Anders gerechnet', () => {
    const h = mount(<ModusMarke lauf={ANDERS} testid="m" />);
    expect(h.querySelector('[data-testid="m"]')!.getAttribute('data-modus')).toBe('anders-gerechnet');
  });
  it('nicht gemeldet: nur in der Zeile, nie im Bild oder Abzeichen', () => {
    expect(mount(<ModusMarke lauf={NULL} testid="m" form="zeile" />).querySelector('[data-testid="m"]')!.textContent).toBe('Rechenweg nicht gemeldet');
    act(() => root!.unmount());
    root = null;
    host!.remove();
    expect(mount(<ModusMarke lauf={NULL} testid="m" form="bild" />).querySelector('[data-testid="m"]')).toBeNull();
    act(() => root!.unmount());
    root = null;
    host!.remove();
    expect(mount(<ModusMarke lauf={NULL} testid="m" form="abzeichen" />).querySelector('[data-testid="m"]')).toBeNull();
  });
  it('Kamera-Fall und kein Vermerk', () => {
    const lauf = { modus: { bestellt: 'image_edit', gerechnet: null, abweichung: null, kameras: { Ost: { gerechnet: 'txt2img', abweichung: true }, Nord: { gerechnet: 'image_edit', abweichung: false } } } };
    expect(mount(<ModusMarke lauf={lauf} testid="m" kamera="Ost" />).querySelector('[data-testid="m"]')).not.toBeNull();
    act(() => root!.unmount());
    root = null;
    host!.remove();
    expect(mount(<ModusMarke lauf={lauf} testid="m" kamera="Nord" />).querySelector('[data-testid="m"]')).toBeNull();
    act(() => root!.unmount());
    root = null;
    host!.remove();
    expect(mount(<ModusMarke lauf={{ status: 'fertig' }} testid="m" />).querySelector('[data-testid="m"]')).toBeNull();
  });
});

describe('ModusMarke: Einbau', () => {
  it('quelleAusLauf reicht modus durch', () => {
    const quelle = quelleAusLauf({ status: 'fertig', jobId: 'j', bild: 'b.png', ...OHNE });
    expect((quelle as { modus?: unknown }).modus).toEqual(OHNE.modus);
  });
  it('Kuratier-Karte: Abzeichen nur am abweichenden Bild', () => {
    const h = mount(<KuratierFlaeche graph={graph} karten={[karte('n1', q(OHNE)), karte('n2', q({}))]} vergleichAuswahl={[]} onMarkieren={leer} onVerwerfen={leer} onVergleichWahl={leer} />);
    const karten = h.querySelectorAll('[data-testid="vis-kuratier-karte"]');
    expect(karten[0]!.querySelector('[data-testid="vis-kuratier-karte-modus-marke"]')!.getAttribute('data-form')).toBe('abzeichen');
    expect(karten[1]!.querySelector('[data-testid="vis-kuratier-karte-modus-marke"]')).toBeNull();
  });
  it('Vergleich: Marke an B, nicht an A', () => {
    const h = mount(<KuratierFlaeche graph={graph} karten={[karte('n1', q({})), karte('n2', q(ANDERS))]} vergleichAuswahl={['n1', 'n2']} onMarkieren={leer} onVerwerfen={leer} onVergleichWahl={leer} />);
    expect(h.querySelector('[data-testid="vis-kuratier-vergleich-modus-marke-a"]')).toBeNull();
    expect(h.querySelector('[data-testid="vis-kuratier-vergleich-modus-marke-b"]')!.textContent).toBe('Anders gerechnet');
  });
  it('Inspektor: Zeile; neben Vorschau stehen beide Marken, je eine Ursache', () => {
    const h = mount(<KuratierInspektor graph={graph} karte={karte('n1', q({ guete: 'vorschau', ...OHNE }))} id="V-01" onMarkieren={leer} onVerwerfen={leer} onInsProjekt={leer} />);
    expect(h.querySelector('[data-testid="vis-kuratier-inspektor-guete-marke"]')).not.toBeNull();
    const m = h.querySelector('[data-testid="vis-kuratier-inspektor-modus-marke"]')!;
    expect(m.getAttribute('data-form')).toBe('zeile');
    expect(m.getAttribute('data-modus')).toBe('ohne-grundlagenbild');
    act(() => root!.unmount());
    root = null;
    host!.remove();
    const n = mount(<KuratierInspektor graph={graph} karte={karte('n1', q(NULL))} id="V-01" onMarkieren={leer} onVerwerfen={leer} onInsProjekt={leer} />);
    expect(n.querySelector('[data-testid="vis-kuratier-inspektor-modus-marke"]')!.getAttribute('data-modus')).toBe('nicht-gemeldet');
    act(() => root!.unmount());
    root = null;
    host!.remove();
    const v = mount(<KuratierInspektor graph={graph} karte={karte('n1', q({}))} id="V-01" onMarkieren={leer} onVerwerfen={leer} onInsProjekt={leer} />);
    expect(v.querySelector('[data-testid="vis-kuratier-inspektor-modus-marke"]')).toBeNull();
  });
});
