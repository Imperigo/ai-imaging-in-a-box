// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { registriereModellLaden, setzeModellLadeZustand, type ModellLadeWirt } from '../src/modules/vis/modell-laden';
import { useProject } from '../src/state/project-store';

/**
 * A0266 (Geräteprobe 0.3.75, Befund 2, 08.11.2026): Der Modell-Knoten ist fest hoch. Ein langer
 * Satz (am Mac der Nachzug-Satz aus A0063b) stand VOR dem Knopf und schob «Andere Datei …» unten
 * aus dem Knoten; damit fehlte der Rückweg. Der Knopf steht jetzt vor dem Satz, und der Satz
 * ist auf wenige Zeilen begrenzt; der volle Text steht im Hinweis (title).
 */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let root: Root | null = null;
let container: HTMLDivElement | null = null;
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  registriereModellLaden(null);
});

const wirt: ModellLadeWirt = { formate: ['IFC', 'glb/glTF'], annehmen: '.ifc,.glb', laden: async () => ({ stand: 'leer' }) };

function montiere(): void {
  const { runCommand } = useProject.getState();
  const res = runCommand('vis.graphErstellen', { name: `A0266-${Math.random()}` });
  const graphId = (res.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'modell', x: 40, y: 40 });
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
}

const q = (id: string) => container!.querySelector(`[data-testid="${id}"]`);
/** true, wenn a im Dokument vor b steht. */
const vor = (a: Element | null, b: Element | null) =>
  !!a && !!b && (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;

const LANG =
  'Das Modell wurde am Mac aus der liegenden Datei nachgezogen: 38 Bauteile, Oberkante 9,1 m; '
  + 'das Gelände ist nicht abgetrennt, die Standpunkte fehlen noch. Für Standpunkte das Modell '
  + 'über «Andere Datei …» am Heim-PC neu umwandeln lassen.';

describe('A0266: «Andere Datei …» bleibt im Modell-Knoten erreichbar', () => {
  it('geladen mit langem Satz: der Knopf steht vor dem Satz', () => {
    registriereModellLaden(wirt);
    setzeModellLadeZustand({ stand: 'geladen', bauteile: 38, herkunft: 'glb', mappe: 'haus-am-hang', fassung: 1, satz: LANG });
    montiere();
    const knopf = q('modell-datei-laden');
    const satz = q('modell-satz');
    expect(knopf?.textContent).toBe('Andere Datei …');
    expect(satz?.textContent).toBe(LANG);
    expect(vor(knopf, satz)).toBe(true);
  });

  it('geladen: der Satz trägt den vollen Text im Hinweis', () => {
    registriereModellLaden(wirt);
    setzeModellLadeZustand({ stand: 'geladen', bauteile: 38, herkunft: 'glb', mappe: 'haus-am-hang', fassung: 1, satz: LANG });
    montiere();
    expect(q('modell-satz')?.getAttribute('title')).toBe(LANG);
  });

  it('nicht lesbar mit vorigem Modell: der Knopf steht vor dem 3D-Fenster des vorigen Modells', () => {
    registriereModellLaden(wirt);
    setzeModellLadeZustand({
      stand: 'fehler',
      datei: 'haus.pln',
      satz: LANG,
      noch: { bauteile: 30, herkunft: 'glb', mappe: 'haus', fassung: 1 },
    });
    montiere();
    const knopf = q('modell-datei-laden');
    expect(knopf?.textContent).toBe('Andere Datei …');
    expect(vor(q('modell-satz'), knopf)).toBe(true);
    expect(vor(knopf, q('modell-noch'))).toBe(true);
    expect(q('modell-satz')?.getAttribute('title')).toBe(LANG);
  });

  it('der Satz ist im Stil auf wenige Zeilen begrenzt (fester Knoten)', () => {
    const css = readFileSync(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src/modules/vis/vis-visual.css'), 'utf8');
    const regel = /\.vis-modell-satz\s*\{([^}]*)\}/.exec(css)?.[1] ?? '';
    expect(regel).toMatch(/-webkit-line-clamp:\s*\d/);
    expect(regel).toMatch(/overflow:\s*hidden/);
  });
});
