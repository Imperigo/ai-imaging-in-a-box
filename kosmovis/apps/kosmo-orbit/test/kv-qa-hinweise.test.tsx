// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import type { VisGraph, VisNode } from '@kosmo/kernel';
import { KuratierInspektor } from '../src/modules/vis/KuratierInspektor';
import { BildKachel } from '../src/modules/vis/NodeCanvas';
import type { KuratierKartenDaten } from '../src/modules/vis/varianten-diff';
import type { JobQa } from '../src/modules/vis/vis-jobs';

/**
 * KosmoVis-Auftrag 180 (Paket kv-qa-hinweise): `qa.verdict.hinweise` ist eine
 * Auskunft, kein Vorbehalt. Kachel und Inspektor zeigen sie als ruhige Zeile
 * ohne Warnzeichen; das Warnzeichen bleibt allein an `reason` gebunden.
 */
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const HINWEIS =
  "INNENANSICHT: Standpunkt im Raum 'Raum-Sued' (frontal), aus 'interior' {'rooms': 'auto'} aus den Raeumen der IFC gerechnet. " +
  'Das Bild zeigt den Raum von innen, nicht das Gebaeude von aussen.';

const qaMitHinweis = (): JobQa => ({ verdict: { passed: true, hinweise: [HINWEIS] } });

describe('kv-qa-hinweise', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;
  afterEach(() => {
    if (root) act(() => root!.unmount());
    container?.remove();
    root = null;
    container = null;
  });
  function mount(el: React.ReactElement) {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => root!.render(el));
  }
  function kachel(qa: JobQa | undefined) {
    mount(<BildKachel jobId="vis-1-abc" bild="a.png" qa={qa} alt="Bild 1" />);
  }
  function inspektor(qa: JobQa) {
    const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };
    const graph: VisGraph = { id: 'g1', kind: 'visgraph', name: 'Test', nodes: [node], edges: [] };
    const karte: KuratierKartenDaten = {
      node,
      quelle: { jobId: 'vis-1-abc', bild: 'a.png', qa },
      kur: { markiert: false, verworfen: false },
    };
    mount(
      <KuratierInspektor graph={graph} karte={karte} id="V-01" onMarkieren={() => {}} onVerwerfen={() => {}} onInsProjekt={() => {}} />,
    );
  }

  it('Kachel: hinweise ohne reason zeigt den Hinweis und KEIN Warnzeichen', () => {
    kachel(qaMitHinweis());
    expect(container!.textContent).toContain('INNENANSICHT');
    expect(container!.textContent).not.toContain('⚠');
    expect(container!.querySelector('.vis-bild-kachel-qa--vorbehalt')).toBeNull();
    expect(container!.querySelector('[data-testid="vis-bild-kachel-qa-vorbehalt"]')).toBeNull();
    expect(container!.querySelector('[data-testid="vis-bild-kachel-qa-hinweise"]')).not.toBeNull();
  });

  it('Kachel: langer Hinweis ist gekuerzt, «mehr» zeigt ihn ganz', () => {
    kachel(qaMitHinweis());
    const zeile = container!.querySelector('[data-testid="vis-bild-kachel-qa-hinweise"]')!;
    expect(zeile.textContent).not.toContain('nicht das Gebaeude von aussen');
    const mehr = container!.querySelector('[data-testid="vis-bild-kachel-qa-hinweise-mehr"]') as HTMLButtonElement;
    expect(mehr).not.toBeNull();
    act(() => mehr.click());
    expect(zeile.textContent).toContain('nicht das Gebaeude von aussen');
  });

  it('Kachel: reason bleibt Warnzeichen, hinweise steht getrennt daneben', () => {
    kachel({ verdict: { passed: true, reason: 'Vorbehalt X', hinweise: ['Auskunft Y'] } });
    expect(container!.textContent).toContain('⚠');
    expect(container!.querySelector('[data-testid="vis-bild-kachel-qa-vorbehalt"]')!.textContent).toBe('Vorbehalt X');
    expect(container!.querySelector('[data-testid="vis-bild-kachel-qa-hinweise"]')!.textContent).toContain('Auskunft Y');
  });

  it('Kachel: fehlende oder leere Liste zeigt nichts', () => {
    kachel({ verdict: { passed: true } });
    expect(container!.querySelector('[data-testid="vis-bild-kachel-qa-hinweise"]')).toBeNull();
    act(() => root!.unmount());
    container!.remove();
    kachel({ verdict: { passed: true, hinweise: [] } });
    expect(container!.querySelector('[data-testid="vis-bild-kachel-qa-hinweise"]')).toBeNull();
  });

  it('Inspektor: Hinweis ungekuerzt, ohne Vorbehalt-Zeile', () => {
    inspektor(qaMitHinweis());
    expect(container!.textContent).toContain(HINWEIS);
    expect(container!.textContent).toContain('QA-Hinweis');
    expect(container!.textContent).not.toContain('QA-Vorbehalt');
  });

  it('Inspektor: ohne hinweise keine Hinweis-Zeile', () => {
    inspektor({ verdict: { passed: true } });
    expect(container!.textContent).not.toContain('QA-Hinweis');
  });
});
