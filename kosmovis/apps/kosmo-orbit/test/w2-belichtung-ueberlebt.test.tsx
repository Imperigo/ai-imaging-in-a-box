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
 * WOHER DIESE PROBE KOMMT: eine unabhaengige Pruefung am 17.09.2026 hat
 * gemessen, dass **keine einzige Probe im Baum** den Oberflaechenweg der
 * Belichtung beruehrt — weder `rechneBelichtung` noch den Knopf «Heller».
 * Das Kernmodul `bild/belichtung.ts` ist seither mit 42 Proben bewacht; der
 * WEG dorthin war es nicht.
 *
 * WAS SIE BEWACHT, und zwar genau: dass das gehobene Bild einen NEUAUFBAU
 * der Komponente ueberlebt. Bis zum 17.09. lag es in einem `useState` des
 * Inspektors — wer das Feld schloss und wieder oeffnete, stand ohne sein
 * Ergebnis da, ohne dass ihm jemand sagte warum. Die zwei Nachbargriffe
 * (Farbangleich, Nachbearbeitung) lagen von Anfang an im Store.
 *
 * WARUM EINE EIGENE ABLAGE UND NICHT EIN DRITTER WERT IN `art`: die
 * Belichtung ersetzt die zwei anderen nicht, sie liegt DARUEBER und rechnet
 * auf deren Ergebnis — der Zuruf sagt «DANACH». In dieselbe Ablage
 * geschrieben waere die Schicht darunter verloren.
 *
 * KEIN CANVAS: echtes Zeichnen in jsdom mit vorbelegtem Store. Die Rechnung
 * selbst braucht `<img>` und `<canvas>`, die es in dieser Umgebung nicht gibt
 * — sie ist im Kern mit 42 Proben geprueft. Hier wird die NAHT geprueft.
 *
 * WARUM NICHT `renderToStaticMarkup` (mein erster Anlauf, gemessen und
 * verworfen): das statische Zeichnen sieht Store-Aenderungen GRUNDSAETZLICH
 * nicht — der Server-Schnappschuss von zustand bleibt beim Anfangszustand.
 * Eine Sonde hat das gezeigt: Wert gesetzt, `getState()` sieht ihn, das
 * gezeichnete Bild sagt «NICHTS». Die Probe waere rot gewesen, obwohl der
 * Code stimmt — und ich haette am Code gesucht.
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const NODE: VisNode = { id: 'node-49', typ: 'render', x: 0, y: 0, params: {} } as VisNode;

const KARTE: KuratierKartenDaten = {
  node: NODE,
  quelle: { dataUrl: 'data:image/png;base64,iVBORw0KGgo=' },
  kur: { markiert: false, verworfen: false },
};

const BERICHT = [
  'Bild 800 × 600, Hebung 1.080',
  'Maske über dem Spitzkanal max(R,G,B), Knie 0.66/0.92: 76.6 % voll gehoben',
  'Ausgebrannt 20.6919 → 20.6919 %, Sättigung 0.5312 → 0.5312',
];

const GRAPH = { id: 'g1', typ: 'VisGraph', name: 'P', nodes: [NODE], edges: [] } as unknown as VisGraph;

let root: Root | null = null;
let container: HTMLDivElement | null = null;

/** Frisch zeichnen — jeder Aufruf ist eine NEUE Komponenteninstanz, genau der
 *  Fall, der vorher das Ergebnis verlor. */
function zeichne(): string {
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
  return container.innerHTML;
}

beforeEach(() => {
  useVisRuntime.setState({ gerechneteBilder: {}, gehobeneBilder: {} });
});

afterEach(() => {
  if (root) { act(() => root!.unmount()); root = null; }
  if (container) { container.remove(); container = null; }
});

describe('Zeile 49 — das gehobene Bild ueberlebt einen Neuaufbau', () => {
  it('ohne Ergebnis zeigt der Inspektor KEINEN Belichtungsbericht (Gegenprobe zuerst)', () => {
    // Ohne diese Zeile waere «der Bericht ist da» kein Beleg, sondern ein
    // Zufallstreffer: er koennte schlicht immer dastehen.
    expect(zeichne()).not.toContain('vis-kuratier-belichtung-bericht');
  });

  it('liegt ein Ergebnis in der Ablage, zeigt JEDER neue Aufbau es wieder', () => {
    useVisRuntime.getState().setzeGehobenesBild('node-49', {
      nodeId: 'node-49',
      dataUrl: 'data:image/png;base64,ZZZ',
      bericht: BERICHT,
      zusage: 'nur die Helligkeit',
      grundlage: 'das Original',
    });

    // Dreimal frisch gezeichnet = dreimal eine neue Komponenteninstanz. Genau
    // das war der Fall, der vorher das Ergebnis verlor.
    for (let i = 0; i < 3; i++) {
      const html = zeichne();
      expect(html, `Aufbau ${i + 1}`).toContain('vis-kuratier-belichtung-bericht');
      expect(html, `Aufbau ${i + 1}`).toContain('Ausgebrannt 20.6919 → 20.6919 %');
      expect(html, `Aufbau ${i + 1}`).toContain('vis-kuratier-belichtung-zuruecksetzen');
    }
  });

  it('das Ergebnis gehoert EINER Karte — eine andere Karte zeigt es nicht', () => {
    useVisRuntime.getState().setzeGehobenesBild('eine-andere-karte', {
      nodeId: 'eine-andere-karte',
      dataUrl: 'data:image/png;base64,ZZZ',
      bericht: BERICHT,
      zusage: 'nur die Helligkeit',
      grundlage: 'das Original',
    });
    expect(zeichne()).not.toContain('vis-kuratier-belichtung-bericht');
  });

  it('«zuruecknehmen» raeumt die Ablage wirklich, nicht nur die Anzeige', () => {
    const s = useVisRuntime.getState();
    s.setzeGehobenesBild('node-49', {
      nodeId: 'node-49', dataUrl: 'd', bericht: BERICHT, zusage: 'z', grundlage: 'g',
    });
    expect(useVisRuntime.getState().gehobeneBilder['node-49']).toBeDefined();
    useVisRuntime.getState().verwirfGehobenesBild('node-49');
    expect(useVisRuntime.getState().gehobeneBilder['node-49']).toBeUndefined();
    expect(zeichne()).not.toContain('vis-kuratier-belichtung-bericht');
  });

  it('faellt die Schicht DARUNTER weg, faellt die Belichtung mit', () => {
    // Der Bericht der Belichtung nennt seine Grundlage («auf die
    // Nachbearbeitung gerechnet»). Verschwindet die Nachbearbeitung, gehoerte
    // der Bericht zu etwas, das es nicht mehr gibt. Ein Bild mit fremdem
    // Bericht ist schlechter als kein Bild.
    const s = useVisRuntime.getState();
    s.setzeGerechnetesBild('node-49', {
      dataUrl: 'd', art: 'nachbearbeitung', bericht: ['x'], zusage: 'z',
    });
    s.setzeGehobenesBild('node-49', {
      nodeId: 'node-49', dataUrl: 'd2', bericht: BERICHT, zusage: 'z', grundlage: 'die Nachbearbeitung',
    });
    useVisRuntime.getState().verwirfGerechnetesBild('node-49');
    expect(useVisRuntime.getState().gerechneteBilder['node-49']).toBeUndefined();
    expect(useVisRuntime.getState().gehobeneBilder['node-49']).toBeUndefined();
  });
});
