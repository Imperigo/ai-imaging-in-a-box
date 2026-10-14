// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { type VisGraph, type VisNode } from '@kosmo/kernel';
import { KuratierInspektor, type VorbildWahl } from '../src/modules/vis/KuratierInspektor';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import type { KuratierKartenDaten } from '../src/modules/vis/varianten-diff';

/**
 * ZEILE 55 — «das ganze bild wieder an das aktuelle neue bild angleichen,
 * starke kontraste von bolognese wieder raus, farblichkeit, kontrast etc
 * wie in diesem bild wo ich jetzt sende bitte».
 *
 * WOHER DIESE PROBE KOMMT: `docs/RENDERPROJEKT-2026-09-10/60-ABNAHMELISTE.md`
 * fuehrt Zeile 55 als «bedienbar» — «heute 23.09. am Quelltext nachgeprueft».
 * Das war eine CODE-LESUNG, kein Klick: `KuratierInspektor.tsx` verdrahtet
 * den Knopf «Farbe angleichen» seit dem 12.09.2026 (`rechneFarbangleich`),
 * aber KEINE Probe im Baum hat je auf ihn geklickt — anders als sein
 * Nachbar «Nachbearbeiten» (Zeile 52, `a10-uebernahme-oberflaeche.test.tsx`)
 * und die Belichtung (Zeile 49, `w2-belichtung-ueberlebt.test.tsx`). Diese
 * Luecke schliesst diese Datei, nach demselben Muster.
 *
 * WAS SIE BEWACHT: dass der Knopf NUR mit Vorbild da ist (Gegenprobe
 * zuerst — sonst waere «er ist da» ein Zufallstreffer), dass er aktiv ist,
 * und dass ein Klick wirklich die Rechnung anstösst — gemessen am
 * Seiteneffekt, der VOR der Rechnung laeuft (`verwirf`/`setBelichtet(null)`
 * in `KuratierInspektor.tsx`s `rechne()`), Muster der Nachbearbeiten-Probe.
 *
 * WAS SIE NICHT MISST: die Rechnung selbst. Die braucht `<img>`/`<canvas>`,
 * die es in jsdom nicht gibt; `farbangleich()` ist im Kern mit eigenen
 * Proben bewacht (`packages/kosmo-kernel/test/*farbangleich*`).
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const NODE: VisNode = { id: 'node-55', typ: 'render', x: 0, y: 0, params: {} } as VisNode;

const KARTE: KuratierKartenDaten = {
  node: NODE,
  quelle: { dataUrl: 'data:image/png;base64,iVBORw0KGgo=' },
  kur: { markiert: false, verworfen: false },
};

const VORBILDER: readonly VorbildWahl[] = [
  { id: 'ref-1', label: 'Bild-Referenz', quelle: { dataUrl: 'data:image/png;base64,AAAA' } },
];

const GRAPH = { id: 'g1', typ: 'VisGraph', name: 'P', nodes: [NODE], edges: [] } as unknown as VisGraph;

const BERICHT = [
  'Stärke 1.000, Kennlinie aus 32 Stützstellen je Kanal',
  'vorher:  Helligkeit 0.400, Sättigung 0.300, Schwarzpunkt 0.020, Rot−Blau im Schatten 4.0',
  'Vorbild: Helligkeit 0.500, Sättigung 0.350, Schwarzpunkt 0.030, Rot−Blau im Schatten 5.0',
  'nachher: Helligkeit 0.500, Sättigung 0.350, Schwarzpunkt 0.030, Rot−Blau im Schatten 5.0',
];

let root: Root | null = null;
let container: HTMLDivElement | null = null;

function zeichne(vorbilder: readonly VorbildWahl[] = VORBILDER): HTMLDivElement {
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
        vorbilder={vorbilder}
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

describe('Zeile 55 — «Farbe angleichen»', () => {
  it('ohne Vorbild gibt es KEINEN Knopf (Gegenprobe zuerst)', () => {
    zeichne([]);
    expect(finde('vis-kuratier-farbangleich')).toBeNull();
    expect(finde('vis-kuratier-kein-vorbild')).not.toBeNull();
  });

  it('mit Vorbild ist der Knopf da und aktiv', () => {
    zeichne();
    const knopf = finde('vis-kuratier-farbangleich') as HTMLButtonElement;
    expect(knopf).not.toBeNull();
    expect(knopf.disabled).toBe(false);
  });

  it('ein Klick stösst die Rechnung wirklich an — die Uebernahme-Schicht wird VOR der Rechnung geraeumt', () => {
    // Dieselbe Schicht wie Nachbearbeiten (Zeile 52): beide sind Griffe ins
    // Original, eine Uebernahme darf nicht stehen bleiben, sonst zeigte der
    // Inspektor ein Bild mit fremdem Bericht.
    useVisRuntime.getState().setzeGerechnetesBild('node-55', {
      art: 'uebernahme',
      nodeId: 'node-55',
      dataUrl: 'data:image/png;base64,UUU',
      bericht: BERICHT,
      zusage: 'x',
      kopfzeile: 'x',
    });
    zeichne();
    expect(finde('vis-kuratier-uebernommenes-bild')).not.toBeNull();
    const knopf = finde('vis-kuratier-farbangleich') as HTMLButtonElement;
    act(() => {
      knopf.click();
    });
    // Die Rechnung selbst scheitert in jsdom (kein Canvas) und meldet sich;
    // das WEGRAEUMEN passiert davor und ist genau das, was hier gemessen
    // wird — derselbe Beleg, den die Nachbearbeiten-Probe fuer Zeile 52
    // fuehrt.
    expect(useVisRuntime.getState().gerechneteBilder['node-55']).toBeUndefined();
    expect(finde('vis-kuratier-uebernommenes-bild')).toBeNull();
  });
});
