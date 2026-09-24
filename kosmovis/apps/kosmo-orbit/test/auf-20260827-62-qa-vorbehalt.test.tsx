// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import type { VisGraph, VisNode } from '@kosmo/kernel';
import { KuratierInspektor } from '../src/modules/vis/KuratierInspektor';
import { varianteDiff, varianteMerkmale, type KuratierKartenDaten } from '../src/modules/vis/varianten-diff';
import type { JobQa } from '../src/modules/vis/vis-jobs';

/**
 * Auftrag auf-20260827-62 (Posten 2, `docs/auftraege-kosmovis/
 * auf-20260827-62.md`) — «ein bestandener Score kann ein Bild ohne Bauwerk
 * sein». Der Vertrag trägt den Vorbehalt seit 27.08.2026 in
 * `qa.verdict.reason`, GENAU dann, wenn `passed:true` UND das Paarurteil
 * widerspricht (gemessenes Beispiel aus dem Auftrag: Score 0.9507,
 * geom_iou 1.0000, rho_maske −0.018 bei vollständig verschwundenem Bauwerk).
 * `qa.verdict.reason` wurde vor diesem Paket an KEINER Stelle in
 * `modules/vis/` gelesen (Repo-Grep, 03.09.2026: 0 Treffer) — diese Datei
 * prüft, dass der Vorbehalt jetzt bei der Zahl mitreist, die er
 * einschränkt (U11), ohne selbst eine Schwelle einzuführen oder das Tor
 * nachzubauen (Auflagen), und dass er OHNE `reason` spurlos verschwindet
 * (U10 — keine Dauerwarnung).
 */
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const VORBEHALT_SATZ =
  'SCORE BESTEHT, MASKENWEG WIDERSPRICHT: Das Tor liest den Score, und der kann bei viel Boden hoch ' +
  'bleiben, obwohl das Bauwerk fehlt (gemessen: Score 0.951, geom_iou 1.000, rho_maske -0.018 bei ' +
  "vollständig verschwundenem Bauwerk). 'passed: true' heisst hier: der Score besteht — nicht, dass " +
  'überhaupt gebaut wurde.';

function qaMitVorbehalt(): JobQa {
  return {
    geometry: { rho_maske: -0.018, passed: true, method: 'depthanything-v2-redepth' },
    verdict: { passed: true, reason: VORBEHALT_SATZ },
  };
}

function qaOhneVorbehalt(): JobQa {
  return {
    geometry: { rho_maske: 0.91, passed: true, method: 'depthanything-v2-redepth' },
    verdict: { passed: true },
  };
}

describe('varianten-diff.ts — qaVorbehalt (Auftrag auf-20260827-62)', () => {
  const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };

  it('reine Weitergabe: reason vorhanden → qaVorbehalt gesetzt, wortgleich', () => {
    const merkmale = varianteMerkmale(node, undefined, qaMitVorbehalt());
    expect(merkmale.qaVorbehalt).toBe(VORBEHALT_SATZ);
    expect(merkmale.qaBestanden).toBe(true);
  });

  it('U10 — ohne reason bleibt qaVorbehalt undefined (kein erfundener/stehender Text)', () => {
    const merkmale = varianteMerkmale(node, undefined, qaOhneVorbehalt());
    expect(merkmale.qaVorbehalt).toBeUndefined();
    expect(merkmale.qaBestanden).toBe(true);
  });

  it('U11 — der Vorbehalt steht in DERSELBEN Diff-Tabelle wie das QA-Verdikt, direkt daneben', () => {
    const mitVorbehalt = varianteMerkmale(node, undefined, qaMitVorbehalt());
    const ohneVorbehalt = varianteMerkmale(node, undefined, qaOhneVorbehalt());
    const zeilen = varianteDiff(mitVorbehalt, ohneVorbehalt);
    const iVerdikt = zeilen.findIndex((z) => z.label === 'QA-Verdikt');
    const iVorbehalt = zeilen.findIndex((z) => z.label === 'QA-Vorbehalt');
    expect(iVerdikt).toBeGreaterThanOrEqual(0);
    expect(iVorbehalt).toBe(iVerdikt + 1);
    expect(zeilen[iVorbehalt]!.a).toBe(VORBEHALT_SATZ);
    expect(zeilen[iVorbehalt]!.b).toBe('—');
  });
});

describe('KuratierInspektor — der Vorbehalt erreicht den Benutzer ohne Aufklappen (Auftrag auf-20260827-62)', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

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

  function render(qa: JobQa) {
    const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };
    const graph: VisGraph = { id: 'g1', kind: 'visgraph', name: 'Test', nodes: [node], edges: [] };
    const karte: KuratierKartenDaten = {
      node,
      quelle: { jobId: 'vis-1788277501-b799e4', bild: 'a.png', qa },
      kur: { markiert: false, verworfen: false },
    };
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root!.render(
        <KuratierInspektor
          graph={graph}
          karte={karte}
          id="V-01"
          onMarkieren={() => {}}
          onVerwerfen={() => {}}
          onInsProjekt={() => {}}
        />,
      );
    });
  }

  it('U9/U9b — der Score bleibt grün («bestanden»), UND der Vorbehalt steht daneben, ungekürzt', () => {
    render(qaMitVorbehalt());
    const text = container!.textContent ?? '';
    expect(text).toContain('bestanden');
    // Auflage: der Satz darf nicht gekürzt/umformuliert werden — er trägt
    // gemessene Zahlen.
    expect(text).toContain(VORBEHALT_SATZ);
    // U9b: ohne den Vertragsgrund «aufzuklappen» — die KKeyValue-Zeilen
    // stehen offen im DOM, nicht hinter einem Accordion/Klapp-Text.
    const inspektor = container!.querySelector('[data-testid="vis-kuratier-inspektor"]');
    expect(inspektor).not.toBeNull();
    expect(inspektor!.textContent).toContain(VORBEHALT_SATZ);
  });

  it('U10 — ohne Vertragsgrund erscheint KEIN Vorbehalt-Text (keine Dauerwarnung)', () => {
    render(qaOhneVorbehalt());
    const text = container!.textContent ?? '';
    expect(text).toContain('bestanden');
    expect(text).not.toContain('SCORE BESTEHT');
    expect(text).not.toContain('QA-Vorbehalt');
  });

  it('U12-Gegenprobe — ohne QA überhaupt erscheint ebenfalls kein Vorbehalt', () => {
    const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };
    const graph: VisGraph = { id: 'g1', kind: 'visgraph', name: 'Test', nodes: [node], edges: [] };
    const karte: KuratierKartenDaten = {
      node,
      quelle: { jobId: 'vis-1788277501-b799e4', bild: 'a.png' },
      kur: { markiert: false, verworfen: false },
    };
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root!.render(
        <KuratierInspektor
          graph={graph}
          karte={karte}
          id="V-01"
          onMarkieren={() => {}}
          onVerwerfen={() => {}}
          onInsProjekt={() => {}}
        />,
      );
    });
    expect(container!.textContent).not.toContain('QA-Vorbehalt');
  });
});
