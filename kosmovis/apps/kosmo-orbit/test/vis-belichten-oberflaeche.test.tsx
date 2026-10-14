// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { type VisGraph, type VisNode } from '@kosmo/kernel';
import { KuratierInspektor } from '../src/modules/vis/KuratierInspektor';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import type { KuratierKartenDaten } from '../src/modules/vis/varianten-diff';

/**
 * ZEILE 49 — «danach bitte bild noch minimal grundsaetzlich heller als
 * aktuell und schau das aussen nicht zu viel ausbrennt».
 *
 * WOHER DIESE PROBE KOMMT: `docs/RENDERPROJEKT-2026-09-10/60-ABNAHMELISTE.md`
 * fuehrt Zeile 49 als «bedienbar» (Knopf «Belichten», Datei + `data-testid`
 * genannt). `w2-belichtung-ueberlebt.test.tsx` bewacht, dass ein gerechnetes
 * Ergebnis einen Neuaufbau ueberlebt — sie saet das Ergebnis dafuer direkt in
 * den Store und klickt den Knopf «Heller» selbst NIE. Keine Probe im Baum
 * tat das bisher. Diese Datei schliesst die Luecke, nach demselben Muster
 * wie `vis-farbangleich-oberflaeche.test.tsx` (Zeile 55) und die
 * «Uebernehmen»-Ergaenzung in `a10-uebernahme-oberflaeche.test.tsx`
 * (Zeile 54).
 *
 * WAS SIE BEWACHT: dass der Knopf da und aktiv ist (auch OHNE Vorbild — die
 * Belichtung braucht keins), und dass ein Klick den Lauf wirklich anstösst
 * (`laeuft` wird SYNCHRON gesetzt, bevor `rechneBelichtung()` async
 * weiterrechnet — direkt nach dem Klick ist der Knopf darum gesperrt, noch
 * bevor die eigentliche Rechnung — die in jsdom ohnehin nie fertig wird,
 * kein `<canvas>` — je zurückkommt).
 *
 * WAS SIE NICHT MISST: die Rechnung selbst — die ist im Kern bewacht
 * (`packages/kosmo-kernel/test/*belichtung*`).
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const NODE: VisNode = { id: 'node-49b', typ: 'render', x: 0, y: 0, params: {} } as VisNode;

const KARTE: KuratierKartenDaten = {
  node: NODE,
  quelle: { dataUrl: 'data:image/png;base64,iVBORw0KGgo=' },
  kur: { markiert: false, verworfen: false },
};

const GRAPH = { id: 'g1', typ: 'VisGraph', name: 'P', nodes: [NODE], edges: [] } as unknown as VisGraph;

let root: Root | null = null;
let container: HTMLDivElement | null = null;

function zeichne(): HTMLDivElement {
  if (root) act(() => root!.unmount());
  if (container) container.remove();
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root!.render(
      <KuratierInspektor
        graph={GRAPH}
        karte={KARTE}
        id="pruef"
        onMarkieren={() => {}}
        onVerwerfen={() => {}}
        onInsProjekt={() => {}}
      />,
    );
  });
  return container;
}

function finde(testid: string): HTMLElement | null {
  return container?.querySelector<HTMLElement>(`[data-testid="${testid}"]`) ?? null;
}

beforeEach(() => {
  useVisRuntime.setState({ gerechneteBilder: {}, gehobeneBilder: {} });
});

afterEach(() => {
  if (root) { act(() => root!.unmount()); root = null; }
  if (container) { container.remove(); container = null; }
});

describe('Zeile 49 — «Heller»', () => {
  it('der Knopf ist da und aktiv, auch OHNE Vorbild (die Belichtung braucht keins)', () => {
    zeichne();
    const knopf = finde('vis-kuratier-belichten') as HTMLButtonElement;
    expect(knopf).not.toBeNull();
    expect(knopf.disabled).toBe(false);
  });

  it('die Hebung-Wahl steht mit «minimal (+8 %)» vor — Zuruf «minimal grundsaetzlich heller»', () => {
    zeichne();
    const wahl = finde('vis-kuratier-hebung-wahl') as HTMLSelectElement;
    expect(wahl.value).toBe('1.08');
  });

  it('ein Klick stösst den Lauf wirklich an — der Knopf ist direkt danach gesperrt', () => {
    const c = zeichne();
    const knopf = finde('vis-kuratier-belichten') as HTMLButtonElement;
    act(() => {
      knopf.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
    // `laeuft` wird SYNCHRON auf `true` gesetzt, bevor `rechneBelichtung()`
    // (async, ohne <canvas> in jsdom nie fertig) weiterlaeuft — der Knopf
    // ist darum direkt nach dem Klick gesperrt. Das ist der Beleg, dass der
    // Klick wirklich in die Rechnung fuehrt, nicht nur, dass er existiert.
    const knopfDanach = c.querySelector('[data-testid="vis-kuratier-belichten"]') as HTMLButtonElement;
    expect(knopfDanach.disabled).toBe(true);
  });
});
