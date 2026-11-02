// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { execute, History, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { leereKiZustand } from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';
import '../../kosmo-orbit/src/modules/vis/varianten';
import { SKIZZE_IPAD_TYP } from '../../kosmo-orbit/src/modules/vis/skizze-quelle';
import { setzeCoopZurueck, setzeModusVonApp } from '../../kosmo-orbit/src/state/kosmo-coop';
import { haengeKiAn, type VisboxKi } from '../src/ki-wirt';
import { VOLL_BILDMODELLE, VOLL_SKIZZEN_BILDMODELLE, VOLL_VORGABE_BILDMODELL, type VollLage } from '../src/voll-render';

/**
 * Entscheid 153 (Owner, 25.10.2026, über die Zentrale): «Ja, Qwen-Image darf für Skizzen in
 * Vollautomatik ohne Klick laufen.» Ein Bild AUS EINER SKIZZE mit Qwen-Image 2.1 rechnet in «Voll»
 * ohne Karte (gezählt und markiert am Heim-PC); jedes andere Qwen-Bild bleibt eine Karte (E146), die
 * Grenze je Stunde gilt, und Qwen ist nie Vorgabe (E128 Auflage 1). Gegen den alten Stand rot: dort
 * war jedes Qwen-Bild eine Karte. Namen erfunden.
 */

let graphId = '';
let renderId = '';
let ki: VisboxKi;
let ab: () => void = () => undefined;

const FREI: VollLage = { frei: true, laeufe: 1, grenze: 5, wiederFreiAb: null };
const VOLL: VollLage = { frei: false, laeufe: 5, grenze: 5, wiederFreiAb: '2026-10-25T14:05:00+00:00', satz: 'Grenze erreicht: 5 Läufe ohne Klick in der letzten Stunde — wieder frei ab 16:05.' };

function lade(mitSkizze: boolean, backbone?: string): void {
  const doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 0, y: 0 });
  renderId = doc.get<VisGraph>(graphId)!.nodes[0]!.id;
  if (backbone) {
    // Umgestellt (A0093): eine gesperrte Wahl am Knoten weist der Kern jetzt ab (A0061); die Probe legt sie als alte Wahl
    // (Projekt von vorher) am Kern vorbei ins Dokument.
    const g = doc.get<VisGraph>(graphId)!;
    doc.apply([{ id: graphId, before: g, after: { ...g, nodes: g.nodes.map((n) => (n.id === renderId ? { ...n, params: { ...(n.params ?? {}), backbone } } : n)) } } as never]);
  }
  if (mitSkizze) {
    execute(doc, 'vis.nodeSetzen', { graphId, typ: SKIZZE_IPAD_TYP, x: -300, y: 0 });
    const s = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
    execute(doc, 'vis.verbinden', { graphId, from: s, fromPort: 'bild', to: renderId, toPort: 'skizze' });
  }
  useProject.setState({ doc, history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] } as never);
  useVisRuntime.setState({ aktiverGraphId: graphId, laeufe: {} });
}

beforeEach(() => {
  leereKiZustand();
  setzeCoopZurueck();
  setzeModusVonApp('voll');
  ab = haengeKiAn(window, null);
  ki = (window as unknown as { visboxKi: VisboxKi }).visboxKi;
});

afterEach(() => {
  ab();
  leereKiZustand();
  setzeCoopZurueck();
});

/**
 * A0093 (Owner-Entscheid «Immer vom Render», 31.10.2026; KosmoOrbit A0061): ein Bildwerkzeug ohne belegten Start vom Render
 * wird in der Seite abgewiesen — keine Karte, kein Auftrag, auch aus einer Skizze. E153 tritt zurück (der neuere Entscheid
 * gilt: Qwen-Image 2.1 ist ungemessen und darum gesperrt).
 */
function abgewiesen(a: ReturnType<VisboxKi['rufe']>, bw: string): void {
  expect('sofort' in a, 'keine Karte').toBe(true);
  expect('sofort' in a && a.sofort.text).toContain(`Bildwerkzeug «${bw}» ist gesperrt`);
  expect(useProject.getState().doc.settings.visRenderAuftrag ?? null).toBeNull();
}

const render = (kennung: string, argumente: Record<string, unknown> = {}) => ({ kennung, werkzeug: 'vis_render', argumente: { graphId, nodeId: renderId, kameraWahl: 'auto', guete: 'voll', ...argumente } });

describe('Entscheid 153: Qwen-Image aus einer Skizze in «Voll»', () => {
  // Umgestellt (A0093, Owner «Immer vom Render» 31.10.2026): vorher rechnete Qwen-Image 2.1 aus einer Skizze ohne Karte (E153).
  it('Skizze am Render-Knoten + Qwen-Image 2.1 (am Aufruf oder am Knoten) → abgewiesen, nichts bestellt (E153 tritt zurück)', () => {
    lade(true);
    abgewiesen(ki.rufe(render('S-1', { backbone: 'qwen-image-2.1' }), 'voll', FREI), 'qwen-image-2.1');
    lade(true, 'qwen-image-2.1');
    abgewiesen(ki.rufe(render('S-2'), 'voll', FREI), 'qwen-image-2.1');
  });

  // Umgestellt (A0093): vorher Karte (E146) — jetzt Absage.
  it('ohne Skizze wird Qwen-Image 2.1 abgewiesen', () => {
    lade(false);
    abgewiesen(ki.rufe(render('S-3', { backbone: 'qwen-image-2.1' }), 'voll', FREI), 'qwen-image-2.1');
  });

  // Umgestellt (A0093): vorher Karte mit «Grenze erreicht» — die Sperre greift vor der Grenze.
  it('auch bei erreichter Grenze: Qwen-Image 2.1 abgewiesen; Z-Image Turbo wird dort eine Karte', () => {
    lade(true);
    abgewiesen(ki.rufe(render('S-4', { backbone: 'qwen-image-2.1' }), 'voll', VOLL), 'qwen-image-2.1');
    const b = ki.rufe(render('S-4b'), 'voll', VOLL);
    expect('karte' in b && b.karte.zusammenfassung).toContain('Grenze erreicht');
  });

  // Umgestellt (A0093): vorher Karte — jetzt Absage.
  it('FLUX.1-Krea wird auch aus einer Skizze abgewiesen', () => {
    lade(true);
    abgewiesen(ki.rufe(render('S-5', { backbone: 'flux-krea' }), 'voll', FREI), 'flux-krea');
  });

  it('nie Vorgabe: ohne Wahl rechnet die Skizze auf Z-Image Turbo, Qwen steht nicht in der freien Liste', () => {
    expect(VOLL_VORGABE_BILDMODELL).toBe('z-image-turbo');
    expect(VOLL_SKIZZEN_BILDMODELLE).toEqual(['qwen-image-2.1']);
    expect(VOLL_BILDMODELLE).not.toContain('qwen-image-2.1');
    lade(true);
    expect('sofort' in ki.rufe(render('S-6'), 'voll', FREI)).toBe(true);
  });
});
