// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import type { VisGraph, VisNode } from '@kosmo/kernel';
import { KuratierInspektor } from '../src/modules/vis/KuratierInspektor';
import { bewertungsLage, type KuratierKartenDaten } from '../src/modules/vis/varianten-diff';
import type { JobQa } from '../src/modules/vis/vis-jobs';

/**
 * P3-Nachzug (ROADMAP 1339 — der Agent hat es selbst als ausserhalb seines
 * Dateikreises gemeldet, ROADMAP 1340 zaehlt es explizit als offenen Rest).
 * `bewertungsLage()` (N3, `varianten-diff.ts`) kennt seit v0.9.59 den vierten
 * Fall `'nicht-zustaendig'` (`qa.geometry.status === 'not_applicable'`) —
 * `KuratierInspektor.tsx` prüfte bisher nur `'ohne-qa'` und `'widerrufen'`,
 * der vierte Fall fiel dabei durch beide Siebe und blieb OHNE JEDEN Text.
 *
 * Der Unterschied, um den es geht: «hier war nichts zu messen»
 * (`not_applicable`) ist nicht dasselbe wie «wir haben es nicht geschafft»
 * (`ohne-qa`/`widerrufen`) — und ohne eigenen Satz sah der Inspektor beide
 * gleich (bzw. den vierten Fall gar nicht) aus.
 */
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

function qaNichtZustaendig(): JobQa {
  return {
    // Nur alte, widerlegte Geometrie-Zahlen — GENAU der Fall, der ohne den
    // `status`-Vorrang als 'widerrufen' durchgegangen wäre.
    geometry: { status: 'not_applicable' },
    verdict: { passed: true },
  };
}

describe('varianten-diff.ts — bewertungsLage kennt den vierten Fall (N3-Nachzug)', () => {
  it('qa.geometry.status "not_applicable" ergibt "nicht-zustaendig", nicht "widerrufen"', () => {
    expect(bewertungsLage(qaNichtZustaendig())).toBe('nicht-zustaendig');
  });
});

describe('KuratierInspektor — "nicht-zustaendig" bekommt einen eigenen Satz statt keinen', () => {
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

  it('zeigt den eigenen "nichts zu messen"-Satz, NICHT den widerrufen-Satz', () => {
    render(qaNichtZustaendig());
    const text = container!.textContent ?? '';
    expect(text).toContain('nichts zu messen');
    expect(text).not.toContain('Bewertung zurueckgezogen');
    expect(text).not.toContain('zurückgezogen');
    expect(text).not.toContain('Keine QA-Bewertung vorhanden');
  });

  it('Gegenprobe: "widerrufen" bleibt weiterhin sein EIGENER Satz (keine Vermischung)', () => {
    const qa: JobQa = {
      geometry: { rho_maske: null, kantenanteil: null, kante: null },
      verdict: { passed: true },
    };
    expect(bewertungsLage(qa)).toBe('widerrufen');
    render(qa);
    const text = container!.textContent ?? '';
    expect(text).toContain('Bewertung zurueckgezogen');
    expect(text).not.toContain('nichts zu messen');
  });
});
