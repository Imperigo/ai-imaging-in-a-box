// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { VARIANTEN_TYP } from '@kosmo/kernel';
import { NodeCanvas } from '../../kosmo-orbit/src/modules/vis/NodeCanvas';
import { registriereHeimStandpunkte, registriereStandpunkteNachgezogen } from '../../kosmo-orbit/src/modules/vis/heim-standpunkte';
import { useProject } from '../../kosmo-orbit/src/state/project-store';

/**
 * A0735 (virtuelle Geräteprobe 0.3.76, Befund V01/V02): bei einer nachgezogenen Mappe stand der Satz
 * «Keine Standpunkte — sie entstehen erst, wenn das Modell über «Andere Datei …» …» in der Standpunkte-Wahl,
 * einem Kasten mit `max-height: 34px` und `overflow-y: auto`. Der Satz ist 59 px hoch: er rollte, die
 * zweite Zeile war abgeschnitten. Die A0270-Probe las nur `textContent` und blieb grün.
 *
 * jsdom hat kein Layout (`scrollHeight` ist immer 0). Diese Probe legt darum die echten Regeln aus
 * `vis-visual.css` und `varianten-daumen.css` in die Seite und prüft an jedem Vorfahren des Satzes bis zur
 * Karte die berechnete Regel: kein Kasten darf den Satz mit einer Höchsthöhe und einem Überlauf ausser
 * `visible` kappen. Die Messung in Pixeln macht der Browser (A0735 Satz 1, `mass.js`).
 */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const VIS = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../kosmo-orbit/src/modules/vis');
const REGELN = ['vis-visual.css', 'varianten-daumen.css'].map((f) => readFileSync(path.join(VIS, f), 'utf8')).join('\n');

let root: Root | null = null;
let container: HTMLDivElement | null = null;
let stil: HTMLStyleElement | null = null;
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  stil?.remove();
  root = null;
  container = null;
  stil = null;
  registriereStandpunkteNachgezogen(false);
  registriereHeimStandpunkte(null);
});

function montiere(): void {
  stil = document.createElement('style');
  stil.textContent = REGELN;
  document.head.appendChild(stil);
  const { runCommand } = useProject.getState();
  const res = runCommand('vis.graphErstellen', { name: `A0735-${Math.random()}` });
  const graphId = (res.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: VARIANTEN_TYP, x: 40, y: 40 });
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
}

/** Die Vorfahren des Elements, die es mit Höchsthöhe und Überlauf kappen — bis zur Karte (`vis-node-…`). */
function kappendeKaesten(el: Element): string[] {
  const funde: string[] = [];
  for (let k: Element | null = el; k && k !== container; k = k.parentElement) {
    const cs = getComputedStyle(k);
    const hoechst = cs.maxHeight;
    const ueberlauf = [cs.overflowY, cs.overflow].find((x) => x) ?? 'visible';
    if (hoechst && hoechst !== 'none' && ueberlauf !== 'visible') {
      funde.push(`${k.className || k.tagName}: max-height ${hoechst}, overflow ${ueberlauf}`);
    }
    if ((k.getAttribute('data-testid') ?? '').startsWith('vis-node-')) break;
  }
  return funde;
}

describe('A0735: der Standpunkt-Satz bei nachgezogener Mappe steht ganz da', () => {
  it('die Regeln sind geladen: die Standpunkte-Wahl trägt ihre Höchsthöhe (Gegenprobe der Messung)', () => {
    montiere();
    const wahl = container!.querySelector('[data-testid="varianten-standpunkte-wahl"]')!;
    expect(getComputedStyle(wahl).maxHeight).toBe('34px');
  });

  it('nachgezogen: kein Kasten zwischen Satz und Karte kappt den Satz', () => {
    registriereStandpunkteNachgezogen(true);
    montiere();
    const satz = container!.querySelector('[data-testid="varianten-nachgezogen"]');
    expect(satz).not.toBeNull();
    expect(kappendeKaesten(satz!)).toEqual([]);
  });

  it('nicht nachgezogen: der kurze Satz und sein Kasten bleiben wie in 0.3.76', () => {
    montiere();
    const wahl = container!.querySelector('[data-testid="varianten-standpunkte-wahl"]')!;
    expect(wahl.className).toBe('vis-varianten-wahl');
    expect(getComputedStyle(wahl).maxHeight).toBe('34px');
  });

  it('der Wechsel der Mappe schaltet den Kasten mit, ohne neuen Knoten', () => {
    montiere();
    const wahl = () => container!.querySelector('[data-testid="varianten-standpunkte-wahl"]')!;
    act(() => registriereStandpunkteNachgezogen(true));
    expect(kappendeKaesten(container!.querySelector('[data-testid="varianten-nachgezogen"]')!)).toEqual([]);
    act(() => registriereStandpunkteNachgezogen(false));
    expect(getComputedStyle(wahl()).maxHeight).toBe('34px');
  });
});
