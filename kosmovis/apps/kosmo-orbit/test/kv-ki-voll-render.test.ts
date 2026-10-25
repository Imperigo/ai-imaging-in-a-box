// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { execute, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { setzeVerlaufWache, useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import {
  artVonBefehl,
  behandle,
  kiSchritte,
  leereKiZustand,
  offeneVorschlaege,
  rueckgaengigKi,
  setzeVollRenderLeser,
  VIS_PAKET,
  VOLL_RENDER_KOPF,
  visWerkzeuge,
  type KiAufruf,
  type KiModus,
} from '../src/modules/vis/ki-werkzeuge';

/**
 * Visbox-Entscheid 146 (24.10.2026, Variante A «Alles ohne Klick, Grenzen bleiben»): In «voll» darf
 * Rendern ohne Karte laufen, wenn der Wirt es erlaubt (`setzeVollRenderLeser`). Ohne Wirt — KosmoOrbit,
 * der Kern allein — bleibt alles wie bisher: Rendern ist eine Karte. Sagt der Wirt nein (Grenze je
 * Stunde, offene Lizenz), bleibt es eine Karte mit dem Grund. Loeschen bleibt in jedem Fall eine
 * Karte, auch in einem Paket mit Rendern. Der Schritt ohne Karte steht im KI-Verlauf und laesst sich
 * zuruecknehmen. Namen erfunden.
 */

let graphId = '';
let modellId = '';
let renderId = '';

function stand(): string {
  return JSON.stringify(useProject.getState().doc.toJSON());
}

beforeEach(() => {
  leereKiZustand();
  setzeVollRenderLeser(null);
  const doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'modell', x: 0, y: 0 });
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 300, y: 0 });
  const g = doc.get<VisGraph>(graphId)!;
  modellId = g.nodes[0]!.id;
  renderId = g.nodes[1]!.id;
  execute(doc, 'vis.verbinden', { graphId, from: modellId, fromPort: 'szene', to: renderId, toPort: 'szene' });
  useProject.setState({ doc, journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: graphId, laeufe: {} });
});

afterEach(() => {
  leereKiZustand();
  setzeVollRenderLeser(null);
  setzeVerlaufWache(null);
});

const render = (kennung: string): KiAufruf => ({ kennung, werkzeug: 'vis_render', argumente: { graphId, nodeId: renderId, kameraWahl: 'auto', guete: 'voll' } });

describe('ohne Wirt (KosmoOrbit, Kern allein): Rendern bleibt eine Karte', () => {
  it('auch in «voll», ohne angehaengten Grund', () => {
    const a = behandle(render('R-1'), 'voll');
    expect('karte' in a).toBe(true);
    expect('karte' in a && a.karte.zusammenfassung).not.toContain('Vollautomatik');
  });
});

describe('der Wirt erlaubt Rendern in «voll»', () => {
  let gefragt: { kennung: string; modus: KiModus }[] = [];
  beforeEach(() => {
    gefragt = [];
    setzeVollRenderLeser((a, modus) => {
      gefragt.push({ kennung: a.kennung, modus });
      return { frei: true };
    });
  });

  it('vis_render in voller Güte: keine Karte, der Auftrag steht im Dokument, im KI-Verlauf zurücknehmbar', () => {
    const a = behandle(render('R-2'), 'voll');
    expect('sofort' in a).toBe(true);
    const text = 'sofort' in a ? a.sofort.text : '';
    expect(text.startsWith(VOLL_RENDER_KOPF)).toBe(true);
    expect(text).toContain('ohne Freigabe');
    expect(offeneVorschlaege()).toEqual([]);
    expect(useProject.getState().doc.settings.visRenderAuftrag).toMatchObject({ graphId, nodeId: renderId, guete: 'voll' });
    expect(kiSchritte().map((s) => s.kennung)).toEqual(['R-2']);
    expect(gefragt).toEqual([{ kennung: 'R-2', modus: 'voll' }]);
    // Zuruecknehmen nimmt den Auftrag aus dem Dokument (den Lauf haelt «Alle anhalten» an).
    expect(rueckgaengigKi('claude').ok).toBe(true);
    expect(useProject.getState().doc.settings.visRenderAuftrag ?? null).toBeNull();
  });

  it('in «karte» und «coop» wird der Wirt nicht gefragt — Rendern ist dort eine Karte', () => {
    for (const modus of ['karte', 'coop'] as const) {
      const a = behandle(render(`R-${modus}`), modus);
      expect('karte' in a).toBe(true);
    }
    expect(gefragt).toEqual([]);
  });

  it('ein Paket mit Rendern und Löschen bleibt eine Karte (106c)', () => {
    const vorher = stand();
    const a = behandle(
      {
        kennung: 'P-1',
        werkzeug: VIS_PAKET,
        argumente: {
          schritte: [
            { befehl: 'vis_render', argumente: { graphId, nodeId: renderId } },
            { befehl: 'vis_nodeLoeschen', argumente: { graphId, nodeId: modellId } },
          ],
        },
      },
      'voll',
    );
    expect('karte' in a).toBe(true);
    expect(stand()).toBe(vorher);
    expect(gefragt).toEqual([]);
  });

  it('Löschen allein bleibt eine Karte', () => {
    const a = behandle({ kennung: 'D-1', werkzeug: 'vis_nodeLoeschen', argumente: { graphId, nodeId: modellId } }, 'voll');
    expect('karte' in a).toBe(true);
  });
});

describe('der Wirt sagt nein', () => {
  it('Grenze erreicht → Karte mit dem Grund, nichts geändert', () => {
    setzeVollRenderLeser(() => ({ frei: false, grund: 'Grenze erreicht: 5 Läufe ohne Klick in der letzten Stunde, wieder frei ab 14:05' }));
    const vorher = stand();
    const a = behandle(render('R-3'), 'voll');
    expect('karte' in a).toBe(true);
    expect('karte' in a && a.karte.zusammenfassung).toContain('— Karte statt Vollautomatik: Grenze erreicht');
    expect(stand()).toBe(vorher);
  });

  it('ein scheiternder Wirt heisst Karte', () => {
    setzeVollRenderLeser(() => {
      throw new Error('App weg');
    });
    const a = behandle(render('R-4'), 'voll');
    expect('karte' in a).toBe(true);
  });
});

describe('Werkzeugtexte', () => {
  // Visbox-Mac-Test 0.3.67 (B): in «Voll» fragte eine Claude-Sitzung nach, weil der Text «Immer eine
  // Karte … startet erst, wenn der Architekt freigibt» sagte. Der Satz je Modus, an allen drei Bildwerkzeugen.
  it.each(['vis_render', 'vis_varianten'])('%s nennt Karte und Voll je Modus, und Freigeben bleibt kein Werkzeug', (name) => {
    const d = visWerkzeuge().find((w) => w.name === name)!.description;
    expect(d).toContain('Im Modus Karte (und Coop): eine Karte, der Architekt gibt frei.');
    expect(d).toContain('Im Modus Voll: rechnet ohne Karte und ohne Freigabe (höchstens 5 je Stunde; Modelle mit offener Lizenz bleiben eine Karte — Ausnahme: Bild aus Skizze mit Qwen-Image, Entscheid 153).');
    expect(d).toContain('Freigeben selbst ist kein Werkzeug');
    expect(d).not.toContain('Immer eine Karte');
    expect(d).not.toContain('startet erst');
  });

  it('«vis.grundlage» ist als Rendern eingeteilt (der Befehl selbst ist Visbox-eigen)', () => {
    expect(artVonBefehl('vis.grundlage')).toBe('rendern');
  });
});

describe('Zurücknehmen startet nichts (Ausführer des Render-Auftrags)', () => {
  it('ein zurückgeholter früherer Auftrag ist nicht frisch — nur ein neuer wird gesendet', async () => {
    const { istFrischerAuftrag } = await import('../src/modules/vis/vis-jobs');
    const gesehen = new WeakSet<object>();
    setzeVollRenderLeser(() => ({ frei: true }));
    behandle(render('R-5'), 'voll');
    const erster = useProject.getState().doc.settings.visRenderAuftrag!;
    expect(istFrischerAuftrag(gesehen, erster)).toBe(true);
    behandle(render('R-6'), 'voll');
    const zweiter = useProject.getState().doc.settings.visRenderAuftrag!;
    expect(zweiter).not.toBe(erster);
    expect(istFrischerAuftrag(gesehen, zweiter)).toBe(true);
    // «Claudes letzten Schritt zurücknehmen» holt den ersten Auftrag zurück — er startet nichts.
    expect(rueckgaengigKi('claude').ok).toBe(true);
    expect(useProject.getState().doc.settings.visRenderAuftrag).toBe(erster);
    expect(istFrischerAuftrag(gesehen, useProject.getState().doc.settings.visRenderAuftrag)).toBe(false);
    expect(istFrischerAuftrag(gesehen, null)).toBe(false);
  }, 20000);
});
