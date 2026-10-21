// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { readdirSync, readFileSync } from 'node:fs';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
  KENNWORT_SELEKTOR,
  LOESCHEN_SELEKTOR,
  RECHEN_FREIGABE_SELEKTOR,
  RENDER_BESTELLEN_SELEKTOR,
  SPERRZONEN_SICHTBAR_SELEKTOR,
  fuehreBlickAus,
  registriereSperrzone,
  sperrGrund,
} from '../src/state/kosmo-maus';
import { setzeFreigabe, setzeKosmoMausZurueck, setzeZeiger } from '../src/state/kosmo-maus-freigabe';
import { APP_NAME_VORGABE, appName, registriereAppName } from '../src/state/kosmo-name';
import { BEDIENT_ATTR, KosmoMausEbene } from '../src/shell/kosmo-maus/KosmoMausEbene';

/**
 * KosmoVis-Kopf (Visbox Plan KI-Bedienung Stufe 6, 21.10.2026): die Sperrzonen der KosmoMaus im
 * Vis-Werkzeug und zwei Nahtstellen fuer einen Wirt. Je Fall der Visbox-Fall und der Gegenbeleg
 * (ohne Wirt ist alles wie vorher).
 */
function teil(html: string): Element {
  const d = document.createElement('div');
  d.innerHTML = html;
  document.body.appendChild(d);
  return d.firstElementChild!;
}

let wurzel: Root | null = null;
let host: HTMLDivElement | null = null;

beforeEach(() => setzeKosmoMausZurueck());
afterEach(() => {
  if (wurzel) act(() => wurzel!.unmount());
  wurzel = null;
  host?.remove();
  host = null;
  document.body.innerHTML = '';
  registriereAppName(null);
});

describe('Sperrzonen im Vis-Werkzeug', () => {
  it('«Alle freigeben» am Varianten-Knoten ist eine Rechenfreigabe wie «Freigeben» am Render-Knoten', () => {
    expect(sperrGrund(teil('<button data-testid="varianten-freigeben">Alle freigeben</button>'))).toMatch(/Rechenfreigaben/);
    expect(sperrGrund(teil('<button data-testid="render-freigeben">Freigeben</button>'))).toMatch(/Rechenfreigaben/);
  });

  it.each(['render-ausfuehren', 'render-grundlage', 'island-render-ausfuehren-n1', 'varianten-bestellen'])(
    '%s schickt direkt an die Grafikkarte und ist gesperrt',
    (id) => {
      expect(sperrGrund(teil(`<button data-testid="${id}">Los</button>`))).toMatch(/nur über eine Karte/);
    },
  );

  it('jede Stelle im Vis-Werkzeug, die direkt an die Brücke schickt, ist bekannt (sonst fehlt ihr Knopf oben)', () => {
    // Wer hier rot wird: die neue Stelle schickt ein Bild an der Wache vorbei. Ihren Knopf in
    // RENDER_BESTELLEN_SELEKTOR (und kosmo-maus.css) eintragen, dann die Datei hier.
    const wurzel = `${process.cwd()}/src/modules/vis`;
    const dateien = (readdirSync(wurzel, { recursive: true }) as string[]).filter((d) => d.endsWith('.tsx') && !d.includes('test'));
    const senden = dateien
      .filter((d) => {
        const code = readFileSync(`${wurzel}/${d}`, 'utf8').replace(/\/\*[\s\S]*?\*\/|\/\/.*$/gm, '');
        return /\b(sendeGraphRenderAuftrag|variantenBestellenKlick)\(/.test(code);
      })
      .map((d) => d.replace(/\\/g, '/'))
      .sort();
    // VisWorkspace: der Weg ueber den Befehl vis.render (der ist fuer Agenten schon eine Karte).
    expect(senden).toEqual(['NodeCanvas.tsx', 'VariantenKnoten.tsx', 'VisWorkspace.tsx', 'island/inhalte/austausch.tsx']);
  });

  it('Löschen am Knoten und in der Insel ist gesperrt, auch ein Kind darin', () => {
    expect(sperrGrund(teil('<button data-testid="visisl-graph-loeschen">Graph löschen</button>'))).toMatch(/Löschen/);
    const g = teil('<svg><g data-testid="node-loeschen"><rect></rect></g></svg>');
    expect(sperrGrund(g.querySelector('rect')!)).toMatch(/Löschen/);
  });

  it('«Node löschen» ist ein SVG-<g>: der gestrichelte Rand liegt auf einem eigenen Rechteck (Befund 305)', () => {
    // `outline` zeichnet der Browser an SVG-Kindern nicht; darum misst die Probe stroke-dasharray am rect.
    const code = readFileSync(`${process.cwd()}/src/modules/vis/NodeCanvas.tsx`, 'utf8');
    const g = code.slice(code.indexOf('data-testid="node-loeschen"'), code.indexOf('</g>', code.indexOf('data-testid="node-loeschen"')));
    expect(g).toContain('className="vis-node-knopf-rahmen"');
    const css = readFileSync(`${process.cwd()}/src/shell/kosmo-maus/kosmo-maus.css`, 'utf8');
    const regel = css.slice(css.indexOf("[data-kosmo-maus-bedient] [data-testid='node-loeschen'] .vis-node-knopf-rahmen"));
    expect(regel.slice(0, regel.indexOf('}'))).toMatch(/stroke-dasharray:\s*4 3/);
  });

  it('Kennwort-Felder tippt nur der Architekt', () => {
    expect(sperrGrund(teil('<input type="password" />'))).toMatch(/Kennwörter/);
    expect(sperrGrund(teil('<input autocomplete="current-password" />'))).toMatch(/Kennwörter/);
  });

  it('Gegenbeleg: ein gewöhnliches Feld und «Abbrechen» bleiben frei', () => {
    expect(sperrGrund(teil('<input type="text" data-testid="prompt" />'))).toBeNull();
    expect(sperrGrund(teil('<button data-testid="render-abbrechen">Abbrechen</button>'))).toBeNull();
  });

  it('die sichtbare Liste umfasst genau die drei Selektoren, und das CSS nennt jeden Teil', () => {
    expect(SPERRZONEN_SICHTBAR_SELEKTOR).toBe(`${RECHEN_FREIGABE_SELEKTOR}, ${RENDER_BESTELLEN_SELEKTOR}, ${LOESCHEN_SELEKTOR}, ${KENNWORT_SELEKTOR}`);
    const css = readFileSync(`${process.cwd()}/src/shell/kosmo-maus/kosmo-maus.css`, 'utf8').replace(/"/g, "'");
    for (const teilSel of SPERRZONEN_SICHTBAR_SELEKTOR.split(',').map((x) => x.trim().replace(/"/g, "'"))) {
      expect(css).toContain(teilSel);
    }
  });
});

describe('Nahtstelle registriereSperrzone', () => {
  it('ein Wirt meldet eine Zone an und ab', () => {
    const el = teil('<button data-testid="wirt-heim-anmeldung">Anmelden</button>');
    expect(sperrGrund(el)).toBeNull();
    const ab = registriereSperrzone((e) => (e.closest('[data-testid="wirt-heim-anmeldung"]') ? 'Die Anmeldung bleibt beim Architekten.' : null));
    expect(sperrGrund(el)).toBe('Die Anmeldung bleibt beim Architekten.');
    ab();
    expect(sperrGrund(el)).toBeNull();
  });

  it('die festen Zonen gehen vor', () => {
    const ab = registriereSperrzone(() => 'vom Wirt');
    expect(sperrGrund(teil('<button data-testid="render-freigeben">Freigeben</button>'))).toMatch(/Rechenfreigaben/);
    ab();
  });
});

describe('Nahtstelle registriereAppName', () => {
  it('ohne Wirt «KosmoOrbit», mit Wirt dessen Name im Satz an den Agenten', async () => {
    expect(appName()).toBe(APP_NAME_VORGABE);
    setzeFreigabe('claude', 'mitschauen', false);
    expect((await fuehreBlickAus('claude', {}, 'lokal')).text).toContain('in KosmoOrbit einschalten');
    registriereAppName('Visbox');
    expect((await fuehreBlickAus('claude', {}, 'lokal')).text).toContain('in Visbox einschalten');
  });
});

describe('Sperrzonen sichtbar, solange ein Agent bedient', () => {
  it('die Wurzel trägt das Merkmal nur mit sichtbarem Zeiger', () => {
    host = document.createElement('div');
    document.body.appendChild(host);
    wurzel = createRoot(host);
    act(() => wurzel!.render(<KosmoMausEbene />));
    expect(document.documentElement.hasAttribute(BEDIENT_ATTR)).toBe(false);
    act(() => setzeZeiger('claude', 10, 10));
    expect(document.documentElement.getAttribute(BEDIENT_ATTR)).toBe('claude');
    act(() => setzeFreigabe('claude', 'bedienen', false));
    expect(document.documentElement.hasAttribute(BEDIENT_ATTR)).toBe(false);
  });
});
