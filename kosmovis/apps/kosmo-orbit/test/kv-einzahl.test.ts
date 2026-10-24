import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { execute, History, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import { startGraphAnlegen } from '../src/modules/vis/start-graph';
import { useVariantenBestellung, variantenStandText, type VariantenBestellung } from '../src/modules/vis/varianten';
import { szeneZeile, szeneZeileGlb } from '../src/modules/vis/modell-laden';
import { mitZahl } from '../src/modules/vis/einzahl';
import { registriereHeimStandpunkte } from '../src/modules/vis/heim-standpunkte';

/**
 * EINZAHL BEI EINS in der Knotenansicht (Visbox-Generalprobe, letzter offener Punkt «1 Bild» vor der Demo).
 *
 * Die Demo rechnet meist mit einer Kamera und einem Bild. Dort stand «Gewählt: 1 Bilder», «Bestellung 1: 1 Bilder —
 * 0 fertig, 1 warten auf Freigabe» und am Modell-Knoten «Szene: 1 Bauteile (GLB)». Gegen den alten Stand sind die
 * Fälle mit eins rot. Alle Zahlen und Namen sind erfunden.
 */

const VIS = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src/modules/vis');
const doc = () => useProject.getState().doc;
const graph = (id: string) => doc().get<VisGraph>(id)!;
const knoten = (gid: string, typ: string) => graph(gid).nodes.find((n) => n.typ === typ)!;

beforeEach(() => {
  useProject.setState({ doc: new KosmoDoc(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: null, laeufe: {} });
  useVariantenBestellung.setState({ bestellungen: {} });
});
afterEach(() => registriereHeimStandpunkte(null));

describe('die Hilfe', () => {
  it('eins in der Einzahl, null und mehr in der Mehrzahl — auch für Verben', () => {
    expect(mitZahl(1, 'Bild', 'Bilder')).toBe('1 Bild');
    expect(mitZahl(0, 'Bild', 'Bilder')).toBe('0 Bilder');
    expect(mitZahl(3, 'Bild', 'Bilder')).toBe('3 Bilder');
    expect(mitZahl(1, 'wartet', 'warten')).toBe('1 wartet');
    expect(mitZahl(2, 'wartet', 'warten')).toBe('2 warten');
  });
});

describe('Modell-Knoten', () => {
  it('«Szene: 1 Bauteil (GLB)» ohne Wirt, «Szene: 1 Bauteil (aus IFC)» mit', () => {
    expect(szeneZeileGlb(1)).toBe('Szene: 1 Bauteil (GLB)');
    expect(szeneZeileGlb(14)).toBe('Szene: 14 Bauteile (GLB)');
    expect(szeneZeile(1, 'IFC')).toBe('Szene: 1 Bauteil (aus IFC)');
  });
});

describe('Varianten-Knoten: der Stand für Kosmo und Claude', () => {
  it('vor der Bestellung mit einem Standpunkt: «Gewählt: 1 Bild —»', () => {
    // Ohne Geometrie (wie in Visbox, wo der Kern keine design.*-Befehle kennt): die Standpunkte des Heim-PCs, und der
    // Knoten «Kamera» wählt eine Richtung — die Demo-Lage mit einer Kamera.
    registriereHeimStandpunkte({
      standpunkte: ['Süd', 'Südost', 'Nordwest'].map((name, i) => ({
        kuerzel: ['s', 'sSE', 'nNW'][i]!,
        name,
        art: 'frontal',
        abstand_m: 30,
        auge: [0, 0, 1.6],
        blick_auf: [0, 0, 0],
        vollstaendig: true,
        begruendung: '',
      })),
      satz: 'erfunden',
    });
    const gid = startGraphAnlegen()!;
    useProject.getState().runCommand('vis.nodeParametrieren', {
      graphId: gid,
      nodeId: knoten(gid, 'kamera').id,
      params: { art: 'auto', richtungen: JSON.stringify(['sSE']) },
    });
    const r = execute(doc(), 'vis.varianten', { stand: true }, { actor: 'kosmo', dryRun: true });
    expect(r.summary).toContain('noch nichts bestellt. Gewählt: 1 Bild — ');
    expect(r.summary).not.toContain('1 Bilder');
  });

  const bestellung = (zeilen: string[], gruppen: VariantenBestellung['gruppen']): VariantenBestellung => ({
    graphId: 'g',
    nodeId: 'v1',
    nr: 1,
    zeilen,
    stimmungen: gruppen.map((g) => g.stimmung),
    entwuerfe: [{ id: 'aktuell', name: 'Aktuelles Modell' }],
    gruppen,
    anzahl: zeilen.length * gruppen.length,
  });

  it('ein Bild, ein Auftrag, wartet: «1 Bild — 0 fertig, 1 wartet auf Freigabe, 0 rechnen … Auftrag:»', () => {
    useVariantenBestellung.getState().setze(
      bestellung(['Südost'], [{ laufId: 'v1::abend::aktuell', stimmung: 'abend', entwurf: 'aktuell', standpunkte: ['Südost'] }]),
    );
    useVisRuntime.setState({ laeufe: { 'v1::abend::aktuell': { status: 'wartetFreigabe', jobId: 'job-a', approvalToken: 't' } } });
    const text = variantenStandText('g', 'v1');
    expect(text).toContain('Bestellung 1: 1 Bild — 0 fertig, 1 wartet auf Freigabe, 0 rechnen, 0 fehlgeschlagen. Auftrag: ');
    expect(text).toContain('abend/Aktuelles Modell = job-a');
  });

  it('ein Bild rechnet: «1 rechnet»; zwei Aufträge bleiben «Aufträge:»', () => {
    useVariantenBestellung.getState().setze(
      bestellung(['Südost'], [
        { laufId: 'v1::abend::aktuell', stimmung: 'abend', entwurf: 'aktuell', standpunkte: ['Südost'] },
        { laufId: 'v1::morgen::aktuell', stimmung: 'morgen', entwurf: 'aktuell', standpunkte: ['Südost'] },
      ]),
    );
    useVisRuntime.setState({
      laeufe: {
        'v1::abend::aktuell': { status: 'rendert', jobId: 'job-a' },
        'v1::morgen::aktuell': { status: 'wartetFreigabe', jobId: 'job-m', approvalToken: 't' },
      },
    });
    const text = variantenStandText('g', 'v1');
    expect(text).toContain('Bestellung 1: 2 Bilder — 0 fertig, 1 wartet auf Freigabe, 1 rechnet, 0 fehlgeschlagen. Aufträge: ');
  });
});

/**
 * WÄCHTER über das Vis-Werkzeug: eine Zahl direkt vor einem Mehrzahl-Wort (`${n} Bilder`, `{n} Varianten`) ist eine
 * Stelle, die bei eins falsch spricht. Ausgenommen sind Sätze, deren Zahl nie eins ist — mit Grund.
 */
const AUSNAHMEN: Record<string, string> = {
  'varianten.ts|${anzahl} Bilder': 'dauerSatz steht erst ab 12 Bildern (Entscheid 92b)',
  'modus-marke.ts|${alle.length} Kameras': '«1 von 3 Kameras»: die Zeile steht nur ab zwei Kameras',
  'RenderVerlauf.tsx|{n} Läufe': 'der Verlauf steht erst ab zwei Läufen (verlaufSichtbar)',
  'RenderVerlauf.tsx|${n} Läufe': 'der Verlauf steht erst ab zwei Läufen (verlaufSichtbar)',
};
const MEHRZAHL = /(\$?\{[\w.()]+\}) (Bilder|Bauteile|Varianten|Favoriten|Aufträge|Kameras|Läufe|Standpunkte|Entwürfe|Zellen)\b/g;

describe('Wächter: keine Zahl vor einem festen Mehrzahl-Wort im Vis-Werkzeug', () => {
  it('jede Fundstelle beugt oder steht mit Grund in den Ausnahmen', () => {
    const funde: string[] = [];
    for (const name of readdirSync(VIS)) {
      if (!/\.tsx?$/.test(name)) continue;
      const zeilen = readFileSync(path.join(VIS, name), 'utf8').split('\n');
      zeilen.forEach((zeile, i) => {
        if (/^\s*(\/\/|\*|\/\*)/.test(zeile)) return;
        for (const m of zeile.matchAll(MEHRZAHL)) {
          if (!(`${name}|${m[0]}` in AUSNAHMEN)) {
            funde.push(`${name}:${i + 1} ${m[0]}`);
          }
        }
      });
    }
    expect(funde).toEqual([]);
  });
});
