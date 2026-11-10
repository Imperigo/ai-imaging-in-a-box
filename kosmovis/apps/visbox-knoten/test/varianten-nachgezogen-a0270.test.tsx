// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { VARIANTEN_TYP } from '@kosmo/kernel';
import { NodeCanvas } from '../../kosmo-orbit/src/modules/vis/NodeCanvas';
import { registriereHeimStandpunkte, registriereStandpunkteNachgezogen } from '../../kosmo-orbit/src/modules/vis/heim-standpunkte';
import { useProject } from '../../kosmo-orbit/src/state/project-store';

/**
 * A0270 (Geräteprobe 0.3.75, Befund A0261): Wer am Mac aus einer nachgezogenen Mappe (Standpunkte
 * null, `auskunft_nachgezogen` wahr) Varianten will, las «Keine Standpunkte — erst ein Modell laden …»
 * und kam nicht weiter. Jetzt nennt der Varianten-Knoten den Weg: «Andere Datei …» am Modell-Knoten.
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
  registriereStandpunkteNachgezogen(false);
  registriereHeimStandpunkte(null);
});

function montiere(): void {
  const { runCommand } = useProject.getState();
  const res = runCommand('vis.graphErstellen', { name: `A0270-${Math.random()}` });
  const graphId = (res.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: VARIANTEN_TYP, x: 40, y: 40 });
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
}

const satz = () => container!.querySelector('.vis-varianten-satz');

describe('A0270: Varianten-Knoten bei einer nachgezogenen Mappe', () => {
  it('nachgezogen: der Satz nennt «Andere Datei …» am Modell-Knoten', () => {
    registriereStandpunkteNachgezogen(true);
    montiere();
    const text = satz()?.textContent ?? '';
    expect(text).toContain('Andere Datei …');
    expect(text).toContain('Modell-Knoten');
    expect(text).toContain('Standpunkte');
    expect(container!.querySelector('[data-testid="varianten-nachgezogen"]')).not.toBeNull();
  });

  it('nicht nachgezogen: der bisherige Satz bleibt', () => {
    montiere();
    expect(satz()?.textContent).toBe('Keine Standpunkte — erst ein Modell laden oder einen Blick sichern.');
  });

  it('der Satz wechselt mit der Mappe, ohne dass der Knoten neu gebaut wird', () => {
    montiere();
    act(() => registriereStandpunkteNachgezogen(true));
    expect(satz()?.textContent).toContain('Andere Datei …');
    act(() => registriereStandpunkteNachgezogen(false));
    expect(satz()?.textContent).toContain('erst ein Modell laden');
  });
});
