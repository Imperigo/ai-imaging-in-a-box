// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { BILDWERKZEUG_NAMEN, execute, GUETE_NAMEN, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { setzeVerlaufWache, useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import { anwenden, behandle, leereKiZustand, offeneVorschlaege, VIS_PAKET, type KiVorschlag } from '../src/modules/vis/ki-werkzeuge';
import { BILDWERKZEUG_TEXTE } from '../src/modules/vis/vis-jobs';
import { GUETE_TEXTE } from '../src/modules/vis/guete';
import { erzaehlungAus } from '../src/shell/claude-anschluss/erzaehl-zeile';

/**
 * K-10 (Visbox-Owner-Entscheid 22.10.2026, Mac-Test 0.3.33): «die Karte zeigt WERTE statt
 * Feldnamen». Je Befehlsart eine Probe auf die Zeile der Karte «Vorschlag von Claude» — gebaut im
 * Probelauf (Vorher aus dem Dokument), und dieselbe Zeile nach «Anwenden» im KI-Verlauf (dort ist
 * das Dokument schon geändert; der Vorher-Wert kommt aus dem gemerkten Graphen).
 */

let graphId = '';
let modellId = '';
let renderId = '';
let stimmungId = '';
let kamId = '';
let kombiId = '';
let kanteId = '';

function karte(kennung: string, werkzeug: string, argumente: Record<string, unknown>): KiVorschlag {
  const a = behandle({ kennung, werkzeug, argumente }, 'karte');
  if (!('karte' in a)) throw new Error(`keine Karte: ${JSON.stringify(a)}`);
  return a.karte;
}

beforeEach(() => {
  leereKiZustand();
  const doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'modell', x: 0, y: 0 });
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 300, y: 0, params: { guete: 'voll', aufloesung: '1600x1000' } });
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'stimmung', x: 0, y: 200, params: { preset: 'morgen' } });
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'kamera', x: 0, y: 400, params: { art: 'auto', richtungen: '["s"]' } });
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'kombinierer', x: 150, y: 200 });
  const g = doc.get<VisGraph>(graphId)!;
  [modellId, renderId, stimmungId, kamId, kombiId] = g.nodes.map((n) => n.id) as [string, string, string, string, string];
  execute(doc, 'vis.verbinden', { graphId, from: modellId, fromPort: 'szene', to: renderId, toPort: 'szene' });
  execute(doc, 'vis.verbinden', { graphId, from: stimmungId, fromPort: 'prompt', to: kombiId, toPort: 'stimmung' });
  kanteId = doc.get<VisGraph>(graphId)!.edges[1]!.id;
  useProject.setState({ doc, journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: graphId, laeufe: {} });
});

afterEach(() => {
  leereKiZustand();
  setzeVerlaufWache(null);
});

describe('Kartenzeile: Werte statt Feldnamen, je Befehlsart', () => {
  it('Stimmung: Vorher → Nachher in Anzeige-Namen, kein «preset»', () => {
    const k = karte('Z-1', 'vis_nodeParametrieren', { graphId, nodeId: stimmungId, params: { preset: 'abend', presets: '["abend"]' } });
    expect(k.zusammenfassung).toBe('Stimmung: Morgenlicht → Abendstimmung');
    expect(k.zusammenfassung).not.toMatch(/preset|Node/);
  });

  it('nach «Anwenden» sagt der Verlauf dasselbe (Vorher aus dem gemerkten Graphen)', () => {
    karte('Z-2', 'vis_nodeParametrieren', { graphId, nodeId: stimmungId, params: { preset: 'abend', presets: '["abend"]' } });
    expect(anwenden('Z-2')!.ok).toBe(true);
    expect(useProject.getState().journal.at(-1)!.summary).toBe('Stimmung: Morgenlicht → Abendstimmung');
  });

  // Visbox-Mac-Befund 0.3.35 (22.10.2026): Claude schlug nur `preset: "morgen"` vor, am Knoten stand die
  // Liste `presets: ["abend"]`. Angewendet wurde richtig Morgenlicht (`stimmungAufruf`), die Karte und
  // «ANGEWENDET: …» sagten aber «Stimmung: Abendstimmung» — die Zeile mischte die alte Liste darüber.
  it('nur «preset» ersetzt die Wahl auch auf der Karte (Regel wie der Befehl, nicht die alte Liste)', () => {
    const doc = useProject.getState().doc;
    execute(doc, 'vis.nodeParametrieren', { graphId, nodeId: stimmungId, params: { presets: '["abend"]' } });
    const k = karte('Z-1b', 'vis_nodeParametrieren', { graphId, nodeId: stimmungId, params: { preset: 'morgen' } });
    expect(k.zusammenfassung).toBe('Stimmung: Abendstimmung → Morgenlicht');
    expect(anwenden('Z-1b')!.ok).toBe(true);
    expect(useProject.getState().journal.at(-1)!.summary).toBe('Stimmung: Abendstimmung → Morgenlicht');
    const knoten = useProject.getState().doc.get<VisGraph>(graphId)!.nodes.find((n) => n.id === stimmungId)!;
    expect(knoten.params?.['presets']).toBe('["morgen"]');
  });

  it('das Band oben (Erzählzeile) zeigt denselben Neu-Wert wie die Karte', () => {
    // Das Band nimmt die Zusammenfassung der offenen Karte (KosmoOrbit: über den Claude-Anschluss, dessen
    // Satz dieselbe `parameterZeile` des Befehls ist; Visbox: über den Werkzeugsatz) — hier über den
    // Werkzeugsatz, den beide Programme tragen.
    const doc = useProject.getState().doc;
    execute(doc, 'vis.nodeParametrieren', { graphId, nodeId: stimmungId, params: { presets: '["abend"]' } });
    karte('B-1', 'vis_nodeParametrieren', { graphId, nodeId: stimmungId, params: { preset: 'morgen' } });
    const offen = offeneVorschlaege().map((v) => ({ kennung: v.kennung, zusammenfassung: v.zusammenfassung }));
    expect(offen).toEqual([{ kennung: 'B-1', zusammenfassung: 'Stimmung: Abendstimmung → Morgenlicht' }]);
    const band = erzaehlungAus({ jetzt: 0, offeneKarten: offen, letzterSchritt: null, zuletztAktiv: null });
    expect(band).toMatchObject({ art: 'wartet', text: 'Claude wartet auf dich', zusatz: 'Stimmung: Abendstimmung → Morgenlicht' });
  });

  it('«presets» gewinnt vor «preset» auch auf der Karte', () => {
    const k = karte('Z-1c', 'vis_nodeParametrieren', { graphId, nodeId: stimmungId, params: { preset: 'winter', presets: '["abend"]' } });
    expect(k.zusammenfassung).toBe('Stimmung: Morgenlicht → Abendstimmung');
  });

  it('Kamera-Richtungen als Himmelsrichtungen', () => {
    const k = karte('Z-3', 'vis_nodeParametrieren', { graphId, nodeId: kamId, params: { richtungen: '["sSE","nNW"]' } });
    expect(k.zusammenfassung).toBe('Kamera · Richtungen: Süd → Südost, Nordwest');
  });

  it('ohne Eintrag am Knoten gilt die Vorgabe als Vorher (Richtungen der Vorgabe, Güte Vorschau)', () => {
    const k = karte('Z-15', 'vis_nodeParametrieren', { graphId, nodeId: kamId, params: { art: 'auto' } });
    expect(k.zusammenfassung).toBe('Kamera · Art: Auto');
    execute(useProject.getState().doc, 'vis.nodeSetzen', { graphId, typ: 'kamera', x: 0, y: 800, params: { art: 'auto' } });
    const neu = useProject.getState().doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
    expect(karte('Z-16', 'vis_nodeParametrieren', { graphId, nodeId: neu, params: { richtungen: '["sSE","nNW"]' } }).zusammenfassung)
      .toBe('Kamera · Richtungen: Südost, Süd, Nordwest → Südost, Nordwest');
  });

  it('Güte und Auflösung am Render-Knoten', () => {
    const k = karte('Z-4', 'vis_nodeParametrieren', { graphId, nodeId: renderId, params: { guete: 'vorschau', aufloesung: '1920x1200' } });
    expect(k.zusammenfassung).toBe('Render-Knoten · Güte: Voll → Vorschau · Auflösung: 1600 × 1000 → 1920 × 1200');
  });

  it('ein unbekanntes Feld heisst «weitere Einstellung», nie mit Rohnamen', () => {
    const k = karte('Z-5', 'vis_nodeParametrieren', { graphId, nodeId: renderId, params: { zzInternFeld: 3 } });
    expect(k.zusammenfassung).toBe('Render-Knoten · eine weitere Einstellung');
    expect(k.zusammenfassung).not.toContain('zzInternFeld');
  });

  it('Stil-Text gekürzt in «»', () => {
    const lang = 'Sichtbeton sandgestrahlt, warmes Abendlicht, lange Schatten auf dem Vorplatz';
    const k = karte('Z-6', 'vis_nodeSetzen', { graphId, typ: 'prompt', x: 0, y: 600, params: { text: lang } });
    expect(k.zusammenfassung).toBe('Neuer Knoten «Prompt» · Stil-Text: «Sichtbeton sandgestrahlt, warmes Abendl…»');
  });

  it('Verbinden und Trennen nennen Knoten und Eingang', () => {
    expect(karte('Z-7', 'vis_verbinden', { graphId, from: kamId, fromPort: 'kameras', to: renderId, toPort: 'kameras' }).zusammenfassung)
      .toBe('Verbinden: «Kamera» an Render-Knoten, Eingang «Kamera-Standpunkte»');
    expect(karte('Z-8', 'vis_trennen', { graphId, edgeId: kanteId }).zusammenfassung)
      .toBe('Verbindung lösen: «Stimmung» von «Prompt-Kombinierer», Eingang «Stimmung»');
  });

  it('Schieben, Einklappen, Löschen nennen den Knoten', () => {
    expect(karte('Z-9', 'vis_nodeSchieben', { graphId, nodeId: stimmungId, x: 5, y: 5 }).zusammenfassung).toBe('Knoten «Stimmung» verschieben');
    expect(karte('Z-10', 'vis_nodeKollabieren', { graphId, nodeId: stimmungId, collapsed: true }).zusammenfassung).toBe('Knoten «Stimmung» einklappen');
    expect(karte('Z-11', 'vis_nodeLoeschen', { graphId, nodeId: stimmungId }).zusammenfassung).toBe('Knoten «Stimmung» löschen, samt seinen Verbindungen');
    expect(karte('Z-12', 'vis_graphLoeschen', { graphId }).zusammenfassung).toBe('Render-Graph «Probe» löschen');
  });

  it('Render-Auftrag: was gerechnet wird, wo, und dass der Architekt freigibt', () => {
    const k = karte('Z-13', 'vis_render', { graphId, nodeId: renderId, kameraWahl: 'auto', guete: 'vorschau', stimmungPreset: 'abend', aufloesung: [1600, 1000] });
    expect(k.zusammenfassung).toBe('Vorschau rechnen am Render-Knoten (Freigabe durch den Architekten — nach «Anwenden» jetzt am Render-Knoten «Freigeben») · Stimmung: Abendstimmung · Auflösung: 1600 × 1000');
  });

  it('Paket: ein Kopf, eine Zeile je Schritt', () => {
    const k = karte('Z-14', VIS_PAKET, {
      schritte: [
        { befehl: 'vis_nodeParametrieren', argumente: { graphId, nodeId: stimmungId, params: { preset: 'abend', presets: '["abend"]' } } },
        { befehl: 'vis_nodeParametrieren', argumente: { graphId, nodeId: renderId, params: { guete: 'vorschau' } } },
      ],
    });
    expect(k.zusammenfassung).toBe('Paket: 2 Schritte als ein Schritt (ein Rückgängig)');
    expect(k.schritte.map((s) => s.zusammenfassung)).toEqual(['Stimmung: Morgenlicht → Abendstimmung', 'Render-Knoten · Güte: Voll → Vorschau']);
  });

  it('Anzeige-Namen im Kern sind die der App (Bildwerkzeug, Güte)', () => {
    expect(BILDWERKZEUG_NAMEN).toEqual(Object.fromEntries(Object.entries(BILDWERKZEUG_TEXTE).map(([k, v]) => [k, v.name])));
    expect(GUETE_NAMEN).toEqual(Object.fromEntries(Object.entries(GUETE_TEXTE).map(([k, v]) => [k, v.name])));
  });
});
