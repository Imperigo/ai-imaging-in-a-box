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
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 0, y: 0, ...(backbone ? { params: { backbone } } : {}) });
  renderId = doc.get<VisGraph>(graphId)!.nodes[0]!.id;
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

const render = (kennung: string, argumente: Record<string, unknown> = {}) => ({ kennung, werkzeug: 'vis_render', argumente: { graphId, nodeId: renderId, kameraWahl: 'auto', guete: 'voll', ...argumente } });

describe('Entscheid 153: Qwen-Image aus einer Skizze in «Voll»', () => {
  it('Skizze am Render-Knoten + Qwen-Image 2.1 (am Aufruf oder am Knoten) → ohne Karte', () => {
    lade(true);
    const a = ki.rufe(render('S-1', { backbone: 'qwen-image-2.1' }), 'voll', FREI);
    expect('sofort' in a).toBe(true);
    expect('sofort' in a && a.sofort.text).toContain('rechnet ohne Freigabe, Vollautomatik');
    lade(true, 'qwen-image-2.1');
    expect('sofort' in ki.rufe(render('S-2'), 'voll', FREI)).toBe(true);
  });

  it('ohne Skizze bleibt Qwen-Image 2.1 eine Karte (E146)', () => {
    lade(false);
    const a = ki.rufe(render('S-3', { backbone: 'qwen-image-2.1' }), 'voll', FREI);
    expect('karte' in a).toBe(true);
    expect('karte' in a && a.karte.zusammenfassung).toContain('«qwen-image-2.1» hat eine offene oder Forschungs-Lizenz');
  });

  it('die Grenze je Stunde gilt auch für die Skizze → Karte', () => {
    lade(true);
    const a = ki.rufe(render('S-4', { backbone: 'qwen-image-2.1' }), 'voll', VOLL);
    expect('karte' in a).toBe(true);
    expect('karte' in a && a.karte.zusammenfassung).toContain('Grenze erreicht');
  });

  it('Forschungsmodelle bleiben auch aus einer Skizze eine Karte', () => {
    lade(true);
    expect('karte' in ki.rufe(render('S-5', { backbone: 'flux-krea' }), 'voll', FREI)).toBe(true);
  });

  it('nie Vorgabe: ohne Wahl rechnet die Skizze auf Z-Image Turbo, Qwen steht nicht in der freien Liste', () => {
    expect(VOLL_VORGABE_BILDMODELL).toBe('z-image-turbo');
    expect(VOLL_SKIZZEN_BILDMODELLE).toEqual(['qwen-image-2.1']);
    expect(VOLL_BILDMODELLE).not.toContain('qwen-image-2.1');
    lade(true);
    expect('sofort' in ki.rufe(render('S-6'), 'voll', FREI)).toBe(true);
  });
});
