// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { execute, History, KosmoDoc, rechnetOhneFreigabe, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { kiSchritte, leereKiZustand, offeneVorschlaege, rueckgaengigKi } from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';
// Die Laufzeit der Varianten meldet im Original den Stand-Leser an — hier mitgeladen.
import '../../kosmo-orbit/src/modules/vis/varianten';
import { setzeCoopZurueck, setzeModusVonApp } from '../../kosmo-orbit/src/state/kosmo-coop';
import { haengeKiAn, type VisboxKi } from '../src/ki-wirt';
import { VOLL_BILDMODELLE, type VollLage } from '../src/voll-render';

/**
 * Owner-Entscheid 146 (24.10.2026, Klickfrage über die Zentrale, Variante A «Alles ohne Klick,
 * Grenzen bleiben»; Wortlaut: «bitte behebe das kartenproblem und ständige "ich muss bestätigen" mit
 * karten wenn vollautomatik läuft»). Bis 0.3.55 war `vis_render` auch in «Voll» eine Karte (Probe R57
 * hielt das fest) — jetzt rechnet es ohne Karte, solange der Heim-PC «frei» meldet und das Bildmodell
 * eine zulässige Lizenz hat. Gegen den alten Stand rot: dort lag immer eine Karte. Namen erfunden.
 */

let graphId = '';
let renderId = '';
let variantenId = '';
let ki: VisboxKi;
let ab: () => void = () => undefined;

const FREI: VollLage = { frei: true, laeufe: 1, grenze: 5, wiederFreiAb: null };
const VOLL: VollLage = {
  frei: false,
  laeufe: 5,
  grenze: 5,
  wiederFreiAb: '2026-10-24T14:05:00+00:00',
  satz: 'Grenze erreicht: 5 Läufe ohne Klick in der letzten Stunde — wieder frei ab 16:05.',
};

function neuesDokument(backbone?: string): KosmoDoc {
  const doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 0, y: 0, ...(backbone ? { params: { backbone } } : {}) });
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'varianten', x: 300, y: 0 });
  [renderId, variantenId] = doc.get<VisGraph>(graphId)!.nodes.map((n) => n.id) as [string, string];
  execute(doc, 'vis.verbinden', { graphId, from: renderId, fromPort: 'bild', to: variantenId, toPort: 'render' });
  return doc;
}

function lade(backbone?: string): void {
  useProject.setState({ doc: neuesDokument(backbone), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] } as never);
  useVisRuntime.setState({ aktiverGraphId: graphId, laeufe: {} });
}

beforeEach(() => {
  leereKiZustand();
  setzeCoopZurueck();
  lade();
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

describe('«Voll» mit «frei» vom Heim-PC: rechnet ohne Karte', () => {
  it('vis_render in voller Güte: sofort, Satz «rechnet ohne Freigabe, Vollautomatik», Auftrag im Dokument', () => {
    const a = ki.rufe(render('F-1'), 'voll', FREI);
    expect('sofort' in a).toBe(true);
    const text = 'sofort' in a ? a.sofort.text : '';
    expect(text).toContain('Bild in voller Güte rechnen am Render-Knoten (rechnet ohne Freigabe, Vollautomatik)');
    expect(text).not.toContain('Freigabe durch den Architekten');
    expect(offeneVorschlaege()).toEqual([]);
    expect(useProject.getState().doc.settings.visRenderAuftrag).toMatchObject({ nodeId: renderId, guete: 'voll' });
    // Ein Verlaufseintrag, zurücknehmbar in der Leiste.
    expect(kiSchritte().map((s) => s.kennung)).toEqual(['F-1']);
    expect(rueckgaengigKi('claude').ok).toBe(true);
  });

  it('vis_varianten: sofort, «jeder startet ohne Freigabe»', () => {
    const a = ki.rufe({ kennung: 'F-2', werkzeug: 'vis_varianten', argumente: { nodeId: variantenId, stimmungen: ['abend'] } }, 'voll', FREI);
    expect('sofort' in a).toBe(true);
    const text = 'sofort' in a ? a.sofort.text : '';
    expect(text).toContain(`jeder startet ohne Freigabe (Vollautomatik) am Knoten «Varianten» (${variantenId}).`);
    expect(text).not.toContain('wartet auf Freigabe');
  });

  it('vis_grundlage (neu): sofort, nur Blender', () => {
    const a = ki.rufe({ kennung: 'F-3', werkzeug: 'vis_grundlage', argumente: { graphId, nodeId: renderId } }, 'voll', FREI);
    expect('sofort' in a).toBe(true);
    expect('sofort' in a && a.sofort.text).toContain('Grundlage rendern am Render-Knoten — nur Blender, alle Ebenen (rechnet ohne Freigabe, Vollautomatik)');
  });

  it('der Satz gilt nur während des Aufrufs — danach meldet der Kern wieder «mit Freigabe»', () => {
    ki.rufe(render('F-4'), 'voll', FREI);
    expect(rechnetOhneFreigabe()).toBe(false);
  });

  it('der Assistent bekommt dieselbe Regel', () => {
    const a = ki.rufe({ ...render('A-1'), urheber: 'assistent' }, 'voll', FREI);
    expect('sofort' in a).toBe(true);
  });
});

describe('Grenzen bleiben: dann eine Karte', () => {
  it('Grenze erreicht (5 je Stunde, am Heim-PC gezählt) → Karte mit «wieder frei ab»', () => {
    const a = ki.rufe(render('G-1'), 'voll', VOLL);
    expect('karte' in a).toBe(true);
    const satz = 'karte' in a ? a.karte.zusammenfassung : '';
    expect(satz).toContain('(Freigabe durch den Architekten — nach «Anwenden» jetzt am Render-Knoten «Freigeben»)');
    expect(satz).toContain('Karte statt Vollautomatik: Grenze erreicht: 5 Läufe ohne Klick in der letzten Stunde — wieder frei ab 16:05.');
    expect(useProject.getState().doc.settings.visRenderAuftrag ?? null).toBeNull();
  });

  it('ohne Lage vom Heim-PC (nicht erreicht) → Karte', () => {
    const a = ki.rufe(render('G-2'), 'voll', null);
    expect('karte' in a).toBe(true);
    expect('karte' in a && a.karte.zusammenfassung).toContain('Stand der Vollautomatik nicht gemeldet');
  });

  it('Qwen-Image 2.1 (offene Lizenz) → Karte, auch wenn der Heim-PC «frei» meldet — am Aufruf wie am Knoten', () => {
    const a = ki.rufe(render('Q-1', { backbone: 'qwen-image-2.1' }), 'voll', FREI);
    expect('karte' in a).toBe(true);
    expect('karte' in a && a.karte.zusammenfassung).toContain('«qwen-image-2.1» hat eine offene oder Forschungs-Lizenz');
    lade('qwen-image-2.1');
    const b = ki.rufe(render('Q-2'), 'voll', FREI);
    expect('karte' in b).toBe(true);
    const c = ki.rufe({ kennung: 'Q-3', werkzeug: 'vis_varianten', argumente: { nodeId: variantenId, stimmungen: ['abend'] } }, 'voll', FREI);
    expect('karte' in c).toBe(true);
  });

  it('nur kommerziell zulässige Bildmodelle sind ohne Klick erlaubt', () => {
    expect([...VOLL_BILDMODELLE].sort()).toEqual(['flux2-klein', 'qwen', 'z-image-turbo']);
  });

  it('Löschen bleibt eine Karte, auch in einem Paket mit Rendern', () => {
    const a = ki.rufe(
      {
        kennung: 'L-1',
        werkzeug: 'vis_paket',
        argumente: { schritte: [{ befehl: 'vis_render', argumente: { graphId, nodeId: renderId } }, { befehl: 'vis_nodeLoeschen', argumente: { graphId, nodeId: variantenId } }] },
      },
      'voll',
      FREI,
    );
    expect('karte' in a).toBe(true);
  });

  it('in «Karte» und «Coop» bleibt Rendern eine Karte mit «Freigabe durch den Architekten»', () => {
    for (const modus of ['karte', 'coop'] as const) {
      const a = ki.rufe(render(`M-${modus}`), modus, FREI);
      expect('karte' in a).toBe(true);
      expect('karte' in a && a.karte.zusammenfassung).toBe('Bild in voller Güte rechnen am Render-Knoten (Freigabe durch den Architekten — nach «Anwenden» jetzt am Render-Knoten «Freigeben»)');
    }
  });
});
