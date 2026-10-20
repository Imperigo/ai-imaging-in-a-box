// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { basisNodeHoehe, MODELL_KOERPER_H_MIT_LADEN, NodeCanvas } from '../src/modules/vis/NodeCanvas';
import {
  ladeModellDatei,
  modellLadeStand,
  registriereModellLaden,
  setzeModellLadeZustand,
  szeneZeile,
  type ModellLadeWirt,
  type ModellLadeZustand,
} from '../src/modules/vis/modell-laden';
import { MODELL_3D_ZUSATZ } from '../src/modules/vis/ModellKnoten';
import { useProject } from '../src/state/project-store';

/**
 * KV-MODELL-LADEN (Owner-Entscheid 90 der Visbox, 14.10.2026, Blatt 21): Der Modell-Knoten
 * bekommt «Datei laden …» — aber nur, wenn der WIRT eine Lade-Faehigkeit bereitstellt.
 *
 *  - Ohne Wirt (KosmoOrbit) bleibt der Knoten, wie er war: eine Zeile, kein Knopf, dieselbe
 *    Hoehe. Das Gebaeude kommt dort aus dem Entwurf.
 *  - Mit Wirt (Visbox) die vier Zustaende des Blatts: leer mit Formaten, laeuft, geladen mit
 *    «Szene: N Bauteile (aus IFC)» und Mappe, nicht lesbar mit Satz.
 *  - Waehrend eine Datei laeuft, wird keine zweite angenommen.
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

function montiere(): void {
  const { runCommand } = useProject.getState();
  const res = runCommand('vis.graphErstellen', { name: `KV-MODELL-${Math.random()}` });
  const graphId = (res.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'modell', x: 40, y: 40 });
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
}

const q = (id: string) => container!.querySelector(`[data-testid="${id}"]`);

/** Ein Wirt, dessen Laden die Probe von aussen beendet. */
function wirtMitHand(): { wirt: ModellLadeWirt; beende: (z: ModellLadeZustand) => void; geladen: File[] } {
  let beende: (z: ModellLadeZustand) => void = () => {};
  const geladen: File[] = [];
  const wirt: ModellLadeWirt = {
    formate: ['IFC', 'glb/glTF', 'OBJ'],
    annehmen: '.ifc,.glb,.gltf,.obj,.pln',
    laden(datei, melde) {
      geladen.push(datei);
      melde({ stand: 'laeuft', datei: datei.name, satz: 'IFC: Bauteile und Räume werden gelesen …' });
      return new Promise((fertig) => {
        beende = fertig;
      });
    },
  };
  return { wirt, beende: (z) => beende(z), geladen };
}

describe('KV-MODELL-LADEN · ohne Wirt bleibt der Modell-Knoten, wie er war', () => {
  it('eine Zeile, kein Knopf, kein Dateiwaehler', () => {
    montiere();
    const knoten = container!.querySelector('.vis-node-info-zeile');
    expect(knoten?.textContent).toMatch(/^Szene: \d+ Bauteile \(GLB\)$/);
    expect(q('modell-datei-laden')).toBeNull();
    expect(q('modell-datei-waehler')).toBeNull();
    expect(container!.querySelector('input[type="file"]')).toBeNull();
  });

  it('Hoehe wie vorher (Koerper 22) plus das 3D-Fenster (F1, Entscheid 109 A)', () => {
    // Kopf 26 + 8 + ein Ausgang 20 + Koerper 22 + 10 — die Zahl von vor dem Entscheid 90;
    // seit F1 steht darunter das 3D-Fenster samt Zeile (4 + 140 + 4 + 14 = 162).
    expect(MODELL_3D_ZUSATZ).toBe(162);
    expect(basisNodeHoehe('modell')).toBe(86 + MODELL_3D_ZUSATZ);
  });
});

describe('KV-MODELL-LADEN · mit Wirt die vier Zustaende von Blatt 21', () => {
  it('(1) leer: Knopf «Datei laden …», die Formate des Wirts, accept vom Wirt', () => {
    registriereModellLaden(wirtMitHand().wirt);
    montiere();
    expect(q('modell-datei-laden')?.textContent).toBe('Datei laden …');
    expect(q('modell-formate')?.textContent).toBe('IFC, glb/glTF, OBJ');
    expect((q('modell-datei-waehler') as HTMLInputElement).accept).toBe('.ifc,.glb,.gltf,.obj,.pln');
    expect(basisNodeHoehe('modell')).toBe(86 - 22 + MODELL_KOERPER_H_MIT_LADEN);
    expect(MODELL_KOERPER_H_MIT_LADEN).toBe(140 + MODELL_3D_ZUSATZ);
  });

  it('(2) laeuft → (3) geladen: Szene, Mappe, «Andere Datei …»', async () => {
    const hand = wirtMitHand();
    registriereModellLaden(hand.wirt);
    montiere();
    let ende: Promise<unknown> = Promise.resolve();
    act(() => {
      ende = ladeModellDatei(new File(['ISO-10303-21;'], 'haus.ifc'));
    });
    expect(q('modell-laden')?.getAttribute('data-stand')).toBe('laeuft');
    expect(q('modell-satz')?.textContent).toContain('Räume werden gelesen');
    expect(container!.querySelector('[aria-busy="true"]')?.getAttribute('aria-label')).toBe('läuft · haus.ifc');
    await act(async () => {
      hand.beende({ stand: 'geladen', bauteile: 12, herkunft: 'IFC', mappe: 'haus', fassung: 1 });
      await ende;
    });
    expect(q('modell-szene')?.textContent).toBe('Szene: 12 Bauteile (aus IFC)');
    expect(q('modell-mappe')?.textContent).toBe('Mappe «haus»');
    expect(q('modell-datei-laden')?.textContent).toBe('Andere Datei …');
  });

  it('(3) eine zweite Fassung steht an der Mappe', () => {
    registriereModellLaden(wirtMitHand().wirt);
    setzeModellLadeZustand({ stand: 'geladen', bauteile: 1, herkunft: 'glb', mappe: 'haus', fassung: 2 });
    montiere();
    expect(q('modell-szene')?.textContent).toBe('Szene: 1 Bauteil (aus glb)');
    expect(q('modell-mappe')?.textContent).toBe('Mappe «haus» · Fassung 2');
  });

  it('(4) nicht lesbar: der Satz des Wirts, als Meldung, und ein Knopf zum Weitermachen', async () => {
    const satz = 'ArchiCAD-Dateien sind ein geschlossenes Format. In ArchiCAD: Ablage → Sichern unter → IFC, dann die IFC laden.';
    registriereModellLaden({ formate: ['IFC'], annehmen: '.ifc', laden: async () => ({ stand: 'fehler', satz }) });
    montiere();
    await act(async () => {
      await ladeModellDatei(new File(['x'], 'haus.pln'));
    });
    expect(q('modell-satz')?.textContent).toBe(satz);
    expect(q('modell-satz')?.getAttribute('role')).toBe('alert');
    expect(q('modell-datei-laden')?.textContent).toBe('Andere Datei …');
  });

  it('wirft der Wirt, wird daraus der Zustand «nicht lesbar» mit seinem Text', async () => {
    registriereModellLaden({ formate: [], annehmen: '', laden: async () => { throw new Error('Der Heim-PC antwortet nicht.'); } });
    const z = await ladeModellDatei(new File(['x'], 'a.glb'));
    expect(z).toEqual({ stand: 'fehler', datei: 'a.glb', satz: 'Der Heim-PC antwortet nicht.' });
  });

  it('waehrend eine Datei laeuft, wird keine zweite angenommen', async () => {
    const hand = wirtMitHand();
    registriereModellLaden(hand.wirt);
    const erste = ladeModellDatei(new File(['a'], 'a.ifc'));
    expect(await ladeModellDatei(new File(['b'], 'b.ifc'))).toBeNull();
    expect(hand.geladen.map((d) => d.name)).toEqual(['a.ifc']);
    hand.beende({ stand: 'fehler', satz: 'abgebrochen' });
    await erste;
  });

  it('der Dateiwaehler gibt die gewaehlte Datei an den Wirt und laesst dieselbe ein zweites Mal zu', async () => {
    const hand = wirtMitHand();
    registriereModellLaden(hand.wirt);
    montiere();
    const waehler = q('modell-datei-waehler') as HTMLInputElement;
    const datei = new File(['glTF'], 'haus.glb');
    Object.defineProperty(waehler, 'files', { value: [datei], configurable: true });
    await act(async () => {
      waehler.dispatchEvent(new Event('change', { bubbles: true }));
    });
    expect(hand.geladen).toEqual([datei]);
    expect(waehler.value).toBe('');
    await act(async () => {
      hand.beende({ stand: 'geladen', bauteile: 3, herkunft: 'glb', mappe: 'haus' });
    });
  });

  it('ohne Wirt (wieder abgemeldet) faellt der Zustand auf leer zurueck', () => {
    registriereModellLaden(wirtMitHand().wirt);
    setzeModellLadeZustand({ stand: 'fehler', satz: 'x' });
    registriereModellLaden(null);
    expect(modellLadeStand()).toEqual({ wirt: null, zustand: { stand: 'leer' } });
    expect(szeneZeile(2, 'IFC')).toBe('Szene: 2 Bauteile (aus IFC)');
  });
});
