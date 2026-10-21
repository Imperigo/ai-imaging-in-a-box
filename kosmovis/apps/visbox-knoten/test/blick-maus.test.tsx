// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { execute, History, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { kiSchritte, leereKiZustand, offeneVorschlaege } from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';
import { setzeFreigabe, setzeKosmoMausZurueck, useKosmoMaus } from '../../kosmo-orbit/src/state/kosmo-maus-freigabe';
import { beendeNachlauf } from '../../kosmo-orbit/src/state/kosmo-maus';
import { setzeCoopZurueck, setzeModusVonApp } from '../../kosmo-orbit/src/state/kosmo-coop';
import { registriereKosmoName } from '../../kosmo-orbit/src/state/kosmo-name';
import { BLICK_NAME, blickMausWerkzeuge, haengeKiAn, MAUS_NAME, WIRT_SPERRZONEN, type VisboxKi } from '../src/ki-wirt';

/**
 * VISBOX-EIGEN (Plan «KI-Bedienung» Stufe 6, 21.10.2026): Blick und Maus. Claude und der Assistent
 * sehen die Knotenansicht und klicken mit einer eigenen Maus — nie in eine Sperrzone, und was ein
 * Klick am Render-Graph aendert, geht durch denselben Werkzeugsatz wie ein Werkzeugaufruf: Karte, Coop
 * oder Voll; Loeschen und Rendern immer Karte; die Grafikkarte gibt nie eine KI frei.
 */

let graphId = '';
let modellId = '';
let renderId = '';
let ab: () => void = () => undefined;
const ki = () => (window as unknown as { visboxKi: VisboxKi }).visboxKi;
const graph = () => useProject.getState().doc.get<VisGraph>(graphId)!;

function neuesDokument(): KosmoDoc {
  const doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'modell', x: 0, y: 0 });
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 300, y: 0 });
  const g = doc.get<VisGraph>(graphId)!;
  modellId = g.nodes[0]!.id;
  renderId = g.nodes[1]!.id;
  return doc;
}

/** Ein Knopf, wie ihn die Knotenansicht zeichnet: sein Klick laeuft ueber `runCommand`. */
function knopf(testid: string, wirkung: () => void, text = testid): HTMLButtonElement {
  const b = document.createElement('button');
  b.setAttribute('data-testid', testid);
  b.textContent = text;
  b.addEventListener('click', wirkung);
  document.body.appendChild(b);
  return b;
}

beforeEach(() => {
  // jsdom misst nichts: jedes Element bekommt ein sichtbares Rechteck (wie die Proben dort).
  vi.spyOn(Element.prototype, 'getBoundingClientRect').mockImplementation(function (this: Element) {
    const i = [...document.querySelectorAll('*')].indexOf(this);
    return { left: 10, top: 10 + i * 30, width: 100, height: 20, right: 110, bottom: 30 + i * 30, x: 10, y: 10 + i * 30, toJSON: () => ({}) } as DOMRect;
  });
  leereKiZustand();
  setzeKosmoMausZurueck();
  setzeCoopZurueck();
  beendeNachlauf();
  registriereKosmoName('Assistent');
  useProject.setState({ doc: neuesDokument(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] } as never);
  useVisRuntime.setState({ aktiverGraphId: graphId, laeufe: {} });
  ab = haengeKiAn(window, null);
});

afterEach(() => {
  ab();
  leereKiZustand();
  registriereKosmoName(null);
  document.body.innerHTML = '';
  vi.restoreAllMocks();
});

describe('die zwei Werkzeuge', () => {
  it('heissen wie die App sie nennt, Blick liest, Maus bedient — keines gibt frei', () => {
    const w = blickMausWerkzeuge();
    expect(w.map((x) => [x.name, x.art])).toEqual([
      [BLICK_NAME, 'lesen'],
      [MAUS_NAME, 'bedienen'],
    ]);
    expect(JSON.stringify(w)).not.toMatch(/approv|gpu/i);
    expect(w[1]!.description).toMatch(/Löschen und Rendern immer eine Karte/);
  });
});

describe('Blick', () => {
  it('nennt die Knotenansicht und die Regel von Visbox; mit ausgeschaltetem Mitschauen «in Visbox einschalten»', async () => {
    document.body.insertAdjacentHTML('beforeend', '<div data-testid="vis-island-fuellen"><button data-testid="render-freigeben">Freigeben</button></div>');
    const r = await ki().blick('claude', {});
    expect(r.ok).toBe(true);
    expect(r.text).toContain('Knotenansicht');
    expect(r.text).toMatch(/Löschen und Rendern bleiben in jedem Modus eine Karte/);
    setzeFreigabe('kosmo', 'mitschauen', false);
    const a = await ki().blick('assistent', {});
    expect(a.ok).toBe(false);
    expect(a.text).toContain('für Assistent ausgeschaltet');
    expect(a.text).toContain('in Visbox einschalten');
  });

  it('ein Bild gibt es nur für Claude — der Assistent bekommt den Text mit einem Satz', async () => {
    const a = await ki().blick('assistent', { bild: true });
    expect(a.bild).toBeUndefined();
    expect(a.text).toContain('BILD: für Assistent hier nicht');
  });
});

describe('Maus: Sperrzonen', () => {
  it.each(['render-freigeben', 'varianten-freigeben', 'render-ausfuehren', 'varianten-bestellen', 'visisl-graph-loeschen'])(
    '%s wird nie geklickt',
    async (id) => {
      let geklickt = false;
      knopf(id, () => (geklickt = true));
      const r = await ki().maus('claude', { aktion: 'klick', testid: id });
      expect(r.ok).toBe(false);
      expect(r.text).toMatch(/^VERWEIGERT/);
      expect(geklickt).toBe(false);
    },
  );

  it('die Teile, die es nur in Visbox gibt, sind gesperrt (Claude-Schalter, Heim-PC, «Wer rechnet?», Gespräch)', async () => {
    expect(WIRT_SPERRZONEN.length).toBeGreaterThanOrEqual(5);
    let geklickt = false;
    knopf('einstellungen-claude-schalter', () => (geklickt = true));
    const r = await ki().maus('assistent', { aktion: 'klick', testid: 'einstellungen-claude-schalter' });
    expect(r.text).toMatch(/^VERWEIGERT.*Claude über MCP/);
    expect(geklickt).toBe(false);
  });

  it('ein Kennwort-Feld bekommt nie Text', async () => {
    document.body.insertAdjacentHTML('beforeend', '<input type="password" data-testid="kennwort" />');
    const r = await ki().maus('claude', { aktion: 'tippen', testid: 'kennwort', eingabe: 'geheim' });
    expect(r.text).toMatch(/^VERWEIGERT.*Kennwörter/);
    expect((document.querySelector('[data-testid="kennwort"]') as HTMLInputElement).value).toBe('');
  });

  it('keine Dateien von der Platte', async () => {
    document.body.insertAdjacentHTML('beforeend', '<input type="file" data-testid="datei" />');
    const r = await ki().maus('claude', { aktion: 'datei', testid: 'datei', pfad: '/tmp/x.ply' });
    expect(r.ok).toBe(false);
    expect(r.text).toContain('keine Dateien von der Platte');
  });

  it('mit ausgeschaltetem «Bedienen» klickt nichts', async () => {
    let geklickt = false;
    knopf('frei', () => (geklickt = true));
    setzeFreigabe('claude', 'bedienen', false);
    const r = await ki().maus('claude', { aktion: 'klick', testid: 'frei' });
    expect(r.ok).toBe(false);
    expect(geklickt).toBe(false);
  });
});

describe('Maus: was ein Klick am Graph ändert, geht durch den Werkzeugsatz', () => {
  const schieben = () => useProject.getState().runCommand('vis.nodeSchieben', { graphId, nodeId: modellId, x: 40, y: 40 });
  const loeschen = () => useProject.getState().runCommand('vis.nodeLoeschen', { graphId, nodeId: modellId });

  it('Modus Karte: eine Karte «M-…» mit dem Urheber, der Graph bleibt', async () => {
    knopf('probe-schieben', schieben);
    const r = await ki().maus('assistent', { aktion: 'klick', testid: 'probe-schieben' });
    expect(r.ok).toBe(true);
    const karten = offeneVorschlaege();
    expect(karten).toHaveLength(1);
    expect(karten[0]).toMatchObject({ urheber: 'assistent', art: 'aendern' });
    expect(karten[0]!.kennung).toMatch(/^M-\d+$/);
    expect(r.text).toContain('als Karte für den Architekten angehalten');
    expect(graph().nodes.find((n) => n.id === modellId)).toMatchObject({ x: 0, y: 0 });
    // Keine zweite Kartenart: die KosmoMaus legte keine eigene Maus-Karte an.
    expect(useKosmoMaus.getState().vorschlaege).toHaveLength(0);
  });

  it('Coop: direkt als KI-Schritt, zurücknehmbar; die Antwort sagt es', async () => {
    setzeModusVonApp('coop');
    knopf('probe-schieben', schieben);
    const r = await ki().maus('claude', { aktion: 'klick', testid: 'probe-schieben' });
    expect(r.text).toContain('Ohne Karte angewendet');
    expect(graph().nodes.find((n) => n.id === modellId)).toMatchObject({ x: 40, y: 40 });
    expect(kiSchritte().map((s) => [s.urheber, s.kennung.slice(0, 2)])).toEqual([['claude', 'M-']]);
    expect(ki().rueckgaengigKi('claude').ok).toBe(true);
    expect(graph().nodes.find((n) => n.id === modellId)).toMatchObject({ x: 0, y: 0 });
  });

  it('Voll: Löschen bleibt eine Karte, auch wenn ein Knopf ohne Sperre es auslöst', async () => {
    setzeModusVonApp('voll');
    knopf('probe-loeschen', loeschen);
    await ki().maus('claude', { aktion: 'klick', testid: 'probe-loeschen' });
    expect(offeneVorschlaege()).toHaveLength(1);
    expect(offeneVorschlaege()[0]!.art).toBe('loeschen');
    expect(graph().nodes.some((n) => n.id === modellId)).toBe(true);
  });

  it('Voll: ein Bild bestellen (vis.render) bleibt eine Karte', async () => {
    setzeModusVonApp('voll');
    knopf('probe-render', () => useProject.getState().runCommand('vis.render', { graphId, nodeId: renderId }));
    await ki().maus('assistent', { aktion: 'klick', testid: 'probe-render' });
    expect(offeneVorschlaege().map((v) => v.art)).toEqual(['rendern']);
    expect(useProject.getState().doc.settings.visRenderAuftrag ?? null).toBeNull();
  });

  it('ein Klick des Architekten selbst läuft wie immer (keine Agenten-Hand)', () => {
    knopf('probe-schieben', schieben).click();
    expect(graph().nodes.find((n) => n.id === modellId)).toMatchObject({ x: 40, y: 40 });
    expect(offeneVorschlaege()).toHaveLength(0);
  });
});
