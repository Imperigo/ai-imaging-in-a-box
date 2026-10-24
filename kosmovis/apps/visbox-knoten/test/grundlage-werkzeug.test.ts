// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { execute, History, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { anwenden, artVonBefehl, leereKiZustand, rueckgaengigKi, visWerkzeuge } from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';
import { haengeKiAn, type VisboxKi } from '../src/ki-wirt';
import { grundlageAuftragIn, haengeGrundlageAn, type GrundlageAuftrag } from '../src/grundlage-werkzeug';

/**
 * Owner-Entscheid 146 (24.10.2026), Befund (4) vom Mac: «Für "Grundlage rendern" gibt es kein
 * Werkzeug». Jetzt `vis_grundlage`: ein Auftrag im Dokument wie `vis_render`, ausgeführt auf dem Weg
 * des Knopfs; Karte in «Karte»/«Coop», ohne Karte in «Voll» (mit den Grenzen, `freigabe-voll.test.ts`).
 * Ein zurückgeholter früherer Auftrag startet nichts. Namen erfunden.
 */

let graphId = '';
let renderId = '';
let ki: VisboxKi;
let ab: () => void = () => undefined;
let abAusfuehrer: () => void = () => undefined;
let bestellt: GrundlageAuftrag[] = [];

function neuesDokument(): KosmoDoc {
  const doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 0, y: 0 });
  renderId = doc.get<VisGraph>(graphId)!.nodes[0]!.id;
  return doc;
}

beforeEach(() => {
  leereKiZustand();
  useProject.setState({ doc: neuesDokument(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] } as never);
  useVisRuntime.setState({ aktiverGraphId: graphId, laeufe: {} });
  ab = haengeKiAn(window, null);
  ki = (window as unknown as { visboxKi: VisboxKi }).visboxKi;
  bestellt = [];
  abAusfuehrer = haengeGrundlageAn((a) => bestellt.push(a));
});

afterEach(() => {
  abAusfuehrer();
  ab();
  leereKiZustand();
});

const grundlage = (kennung: string) => ({ kennung, werkzeug: 'vis_grundlage', argumente: { graphId, nodeId: renderId } });

describe('vis_grundlage', () => {
  it('steht in der Werkzeugliste, als «rendern» eingeteilt', () => {
    const w = visWerkzeuge().find((x) => x.name === 'vis_grundlage');
    expect(w?.art).toBe('rendern');
    expect(w?.description).toContain('nur Blender');
    expect(artVonBefehl('vis.grundlage')).toBe('rendern');
  });

  it('in «Karte»: eine Karte; erst «Anwenden» bestellt — einmal', () => {
    const a = ki.rufe(grundlage('K-1'), 'karte', null);
    expect('karte' in a).toBe(true);
    expect(bestellt).toEqual([]);
    expect(anwenden('K-1')!.ok).toBe(true);
    expect(bestellt).toEqual([{ graphId, nodeId: renderId }]);
  });

  it('in «Voll» mit «frei»: ohne Karte bestellt; Zurücknehmen startet den früheren Auftrag nicht neu', () => {
    const frei = { frei: true };
    expect('sofort' in ki.rufe(grundlage('V-1'), 'voll', frei)).toBe(true);
    expect('sofort' in ki.rufe(grundlage('V-2'), 'voll', frei)).toBe(true);
    expect(bestellt).toHaveLength(2);
    expect(rueckgaengigKi('claude').ok).toBe(true);
    // Der erste Auftrag steht wieder im Dokument, wird aber nicht noch einmal bestellt.
    expect(grundlageAuftragIn(useProject.getState().doc)).not.toBeNull();
    expect(bestellt).toHaveLength(2);
  });

  it('ein Knoten, der kein Render-Knoten ist, wird abgewiesen — nichts vorgeschlagen', () => {
    const a = ki.rufe({ kennung: 'X-1', werkzeug: 'vis_grundlage', argumente: { graphId, nodeId: 'gibts-nicht' } }, 'voll', { frei: true });
    expect('sofort' in a && a.sofort.ok).toBe(false);
    expect(bestellt).toEqual([]);
  });

  it('ein Dokument, das schon einen Auftrag trägt (andere Mappe geladen), startet nichts', () => {
    const doc = neuesDokument();
    execute(doc, 'vis.grundlage', { graphId, nodeId: renderId });
    useProject.setState({ doc, history: new History(), journal: [], revision: 1 } as never);
    expect(bestellt).toEqual([]);
  });
});
