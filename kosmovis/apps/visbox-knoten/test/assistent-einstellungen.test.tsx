// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { KosmoOrb } from '../../kosmo-orbit/src/modules/design/island/KosmoOrb';
import { _setzeGespraechZurueck, useKosmoGespraech } from '../../kosmo-orbit/src/shell/kosmo-gespraech';
import { useKosmoStatus } from '../../kosmo-orbit/src/state/kosmo-status';
import { registriereKosmoName } from '../../kosmo-orbit/src/state/kosmo-name';
import { URHEBER_NAME } from '../../kosmo-orbit/src/state/kosmo-maus-freigabe';
import { haengeWirtAn, liesLage, MERKBAR, OHNE_APP_ASSISTENT, useWirt, type VisboxWirt } from '../src/wirt-bruecke';
import { ASSISTENT_NAME, meldeAssistentAn, VisboxAssistent, VisboxKopf, wechsleGespraech } from '../src/kopf';
import { LIZENZ_ZEILEN, schliesseEinstellungen, VisboxEinstellungen } from '../src/einstellungen';
import { legeThema, THEMA_SCHLUESSEL } from '../src/thema';

/**
 * VISBOX-EIGEN (Plan UI-Gleichheit S3/S4, Entscheide 115/116, 20.10.2026): die Kugel und das
 * Gesprächsfeld des Assistenten (Kennungen von KosmoOrbit, Name «Assistent»; das Gespräch führt die
 * Mac-App) und die Einstellungs-Insel (Schale und drei Abschnitte wortgleich, dazu Heim-PC, «Wer
 * rechnet?», «Claude über MCP», Lizenzen, Neuigkeiten). Das Heim-PC-Kennwort läuft nie durch die Seite.
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let root: Root | null = null;
let halter: HTMLDivElement | null = null;
let gesendet: Record<string, unknown>[] = [];
let ab: (() => void) | null = null;

const q = (id: string) => document.querySelector<HTMLElement>(`[data-testid="${id}"]`);
const wirt = () => (window as unknown as { visboxWirt: VisboxWirt }).visboxWirt;
const bote = { postMessage: (n: unknown) => void gesendet.push(n as Record<string, unknown>) };

const GRENZEN = { titel: 'Was der Assistent nicht tut', satz: 'das Urteil am Bild ändern, eine Prüfung überspringen, etwas ohne «Anwenden» rechnen.' };
function gespraech(teil: Record<string, unknown> = {}) {
  return {
    beitraege: [],
    wartet: false,
    hinweis: null,
    karte: null,
    stand: 'bereit',
    modell: 'qwen3:14b',
    feldSatz: null,
    grenzen: GRENZEN,
    feld: null,
    ...teil,
  };
}

function zeichne(): void {
  halter = document.createElement('div');
  document.body.appendChild(halter);
  root = createRoot(halter);
  act(() =>
    root!.render(
      <div className="app-wurzel" data-station="vis">
        <VisboxKopf />
        <KosmoOrb onKosmoOeffnen={wechsleGespraech} />
        <VisboxAssistent />
        <VisboxEinstellungen />
      </div>,
    ),
  );
}

beforeEach(() => {
  _setzeGespraechZurueck();
  useKosmoStatus.setState({ zustand: 'idle', beschaeftigt: false, antwortBlase: null, auftrag: null });
  useWirt.setState({ rechner: null, version: null, leitung: null, sperre: null, rechnerwahl: null, claudeMcp: null, neuigkeiten: null });
  try {
    localStorage.clear();
  } catch {
    /* ohne Speicher */
  }
  legeThema();
  meldeAssistentAn();
  gesendet = [];
  ab = haengeWirtAn(window, bote);
});

afterEach(() => {
  if (root) act(() => root!.unmount());
  root = null;
  halter?.remove();
  halter = null;
  ab?.();
  ab = null;
  schliesseEinstellungen();
  registriereKosmoName(null);
});

describe('S3 · die Kugel und das Gesprächsfeld', () => {
  it('die Kugel steht mit den Kennungen von KosmoOrbit und heisst «Assistent»', () => {
    zeichne();
    expect(q('kosmo-orb-wurzel')).not.toBeNull();
    expect(q('kosmo-eck-orb-wurzel')).not.toBeNull();
    expect(q('kosmo-eck-orb')!.getAttribute('aria-label')).toMatch(/^Assistent öffnen — /);
    expect(URHEBER_NAME.kosmo).toBe(ASSISTENT_NAME);
    expect(document.body.textContent).not.toMatch(/Kosmo/);
  });

  it('ein Klick öffnet das Feld mit Kopf, Verlauf und Eingabe; noch ein Klick schliesst es', () => {
    zeichne();
    act(() => q('kosmo-eck-orb')!.click());
    const feld = q('kosmo-panel')!;
    expect(feld.className).toContain('kp-panel');
    act(() => wirt().lage({ assistent: gespraech() }));
    for (const id of ['kosmo-kopf-orb', 'kp-marke', 'kosmo-panel-schliessen', 'kosmo-input', 'kosmo-send', 'assistent-grenzen']) {
      expect(q(id), id).not.toBeNull();
    }
    expect(feld.querySelector('.kp-titel')!.textContent).toBe('Assistent');
    expect(q('kp-marke')!.textContent).toBe('Heim-PC · qwen3:14b · bereit');
    expect(q('kosmo-eck-orb')!.getAttribute('aria-label')).toMatch(/^Assistent schliessen/);
    act(() => q('kosmo-eck-orb')!.click());
    expect(q('kosmo-panel')).toBeNull();
  });

  it('eine Frage geht an die App; was die App sagt, steht im Verlauf — die Kugel denkt, solange es wartet', () => {
    zeichne();
    act(() => wechsleGespraech());
    act(() => wirt().lage({ assistent: gespraech() }));
    const eingabe = q('kosmo-input') as HTMLTextAreaElement;
    act(() => {
      const setze = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')!.set!;
      setze.call(eingabe, 'Abendstimmung, warm');
      eingabe.dispatchEvent(new Event('input', { bubbles: true }));
    });
    act(() => q('kosmo-send')!.click());
    expect(gesendet.at(-1)).toEqual({ art: 'assistent', tat: 'frage', text: 'Abendstimmung, warm' });
    act(() =>
      wirt().lage({ assistent: gespraech({ beitraege: [{ von: 'mensch', text: 'Abendstimmung, warm' }], wartet: true, feld: { nummer: 1, text: '' } }) }),
    );
    expect(q('kosmo-fortschritt')!.textContent).toBe('Assistent antwortet …');
    expect(useKosmoStatus.getState().zustand).toBe('thinking');
    expect((q('kosmo-input') as HTMLTextAreaElement).value).toBe('');
    act(() =>
      wirt().lage({
        assistent: gespraech({
          beitraege: [
            { von: 'mensch', text: 'Abendstimmung, warm' },
            { von: 'assistent', text: 'Ich schlage «Abend» vor.' },
          ],
          karte: { zeilen: ['Stimmung: Abend'], rechenzeit: 'Rechenzeit noch nicht gemessen.' },
        }),
      }),
    );
    expect(useKosmoStatus.getState().zustand).toBe('idle');
    expect([...document.querySelectorAll('[data-testid="assistent-beitrag"]')].map((b) => (b as HTMLElement).dataset.von)).toEqual(['mensch', 'assistent']);
    expect(document.querySelector('.kp-bubble--kosmo')!.textContent).toBe('Ich schlage «Abend» vor.');
    act(() => q('assistent-anwenden')!.click());
    act(() => q('assistent-ablehnen')!.click());
    act(() => q('assistent-aendern')!.click());
    expect(gesendet.slice(-3)).toEqual([
      { art: 'assistent', tat: 'anwenden' },
      { art: 'assistent', tat: 'ablehnen' },
      { art: 'assistent', tat: 'aendern' },
    ]);
    act(() => wirt().lage({ assistent: gespraech({ feld: { nummer: 2, text: 'Bitte ändern: Stimmung: Abend' } }) }));
    expect((q('kosmo-input') as HTMLTextAreaElement).value).toBe('Bitte ändern: Stimmung: Abend');
  });

  it('ohne Heim-PC sagt das Feld den Satz der App statt einer Eingabe', () => {
    zeichne();
    act(() => wechsleGespraech());
    act(() => wirt().lage({ assistent: gespraech({ stand: null, feldSatz: 'Heim-PC nicht erreichbar · Rechnen und Assistent gesperrt — alles andere geht.' }) }));
    expect(q('kosmo-input')).toBeNull();
    expect(q('assistent-sperre')!.textContent).toBe('Heim-PC nicht erreichbar · Rechnen und Assistent gesperrt — alles andere geht.');
    expect(q('kp-marke')!.dataset.zustand).toBe('nicht verbunden');
  });

  it('ohne App sagt das Feld, wo es den Assistenten gibt', () => {
    ab?.();
    ab = haengeWirtAn(window, null);
    zeichne();
    act(() => wechsleGespraech());
    expect(q('assistent-sperre')!.textContent).toBe(OHNE_APP_ASSISTENT);
  });

  it('eine Antwort bei geschlossenem Feld steht als Blase an der Kugel', () => {
    zeichne();
    act(() => wirt().lage({ assistent: gespraech({ beitraege: [{ von: 'mensch', text: 'Hallo' }], wartet: true }) }));
    act(() => wirt().lage({ assistent: gespraech({ beitraege: [{ von: 'mensch', text: 'Hallo' }, { von: 'assistent', text: 'Guten Abend.' }] }) }));
    expect(q('kosmo-antwort-blase-text')!.textContent).toBe('Guten Abend.');
    expect(q('kosmo-antwort-blase-text')!.getAttribute('aria-label')).toBe('Assistent hat geantwortet: Guten Abend. — Fenster öffnen');
  });

  it('das Gespräch liest nur seine Felder — kein Kennwort', () => {
    const lage = liesLage({ assistent: { ...gespraech(), kennwort: 'geheim', anmeldung: { kennwort: 'geheim' } } });
    expect(JSON.stringify(lage)).not.toContain('geheim');
    expect(lage.assistent!.modell).toBe('qwen3:14b');
  });
});

const WAHL = {
  titel: 'Wer rechnet?',
  untertitel: 'Je Arbeit wählbar. Vorgabe: Heim-PC.',
  arbeiten: [
    {
      arbeit: 'blenderRender',
      titel: 'Blender-Render',
      felder: [
        { ort: 'heimPC', titel: 'Heim-PC', zeile: '· verbunden', gewaehlt: true, waehlbar: true },
        { ort: 'diesesGeraet', titel: 'Dieses Gerät', zeile: 'nicht verfügbar — kein Blender gefunden', gewaehlt: false, waehlbar: false },
      ],
    },
  ],
  mcpSatz: 'Claude über MCP: eingerichtet …',
  heuteSatz: 'Heute rechnet alles am Heim-PC …',
};
const CLAUDE = {
  an: true,
  satz: 'Hört auf diesem Mac.',
  titel: 'Claude über MCP',
  codeTitel: 'Claude Code — einmal im Terminal:',
  befehl: 'claude mcp add --transport http visbox http://127.0.0.1:8631/mcp',
  kopieren: 'Befehl kopieren',
  datenTitel: 'Was Claude bekommt:',
  daten: 'Mappennamen …',
  werkzeugeTitel: 'Werkzeuge:',
  werkzeuge: 'Knoten setzen …',
  nurHier: 'Nur auf diesem Mac. Kein Weg aus dem Internet.',
};

describe('S4 · die Einstellungs-Insel', () => {
  it('der Einstellungs-Kreis öffnet die Insel mit der Schale und allen Abschnitten von KosmoOrbit', () => {
    zeichne();
    act(() => q('island-einstellungen-kreis')!.click());
    expect(gesendet.filter((n) => n['art'] === 'einstellung')).toEqual([]);
    for (const id of [
      'einstellungen-scrim',
      'einstellungen-panel',
      'einstellungen-schliessen',
      'einstellungen-heimpc',
      'einstellungen-darstellung',
      'einstellung-thema',
      'einstellungen-anzeige',
      'einstellung-schrift',
      'einstellung-bewegung',
      'einstellungen-bewegung-klang',
      'einstellung-touch-undo-geste',
      'einstellungen-rechner',
      'einstellungen-claude',
      'einstellungen-lizenzen',
      'einstellungen-neuigkeiten',
    ]) {
      expect(q(id), id).not.toBeNull();
    }
    // Ausnahmen (UI_AUSNAHMEN.json): keine Phase, kein Projekt, keine Nutzungszeit, kein Rundgang.
    for (const id of ['einstellungen-phase', 'einstellungen-projekt', 'einstellungen-paket-ursprung', 'einstellungen-nutzungszeit', 'einstellungen-rundgang', 'einstellung-sounds']) {
      expect(q(id), id).toBeNull();
    }
    expect(q('einstellungen-lizenzen')!.textContent).toContain(LIZENZ_ZEILEN[0]!);
    act(() => q('einstellungen-schliessen')!.click());
    expect(q('einstellungen-panel')).toBeNull();
  });

  it('der Heim-PC-Chip öffnet die Insel bei «Wer rechnet?»; eine Wahl geht an die App', () => {
    zeichne();
    act(() => wirt().lage({ rechnerwahl: WAHL }));
    act(() => q('heimpc-chip')!.click());
    expect(q('einstellungen-rechner')!.textContent).toContain('Je Arbeit wählbar. Vorgabe: Heim-PC.');
    expect(q('einstellungen-rechner-blenderRender-heimPC')!.getAttribute('aria-pressed')).toBe('true');
    expect((q('einstellungen-rechner-blenderRender-diesesGeraet') as HTMLButtonElement).disabled).toBe(true);
    expect(q('einstellungen-rechner')!.textContent).toContain('nicht verfügbar — kein Blender gefunden');
    act(() => q('einstellungen-rechner-blenderRender-heimPC')!.click());
    expect(gesendet.at(-1)).toEqual({ art: 'rechner', arbeit: 'blenderRender', ort: 'heimPC' });
  });

  it('Heim-PC: die Lage von der App und «Am Mac einrichten» — kein Feld für Adresse oder Kennwort', () => {
    zeichne();
    act(() => wirt().lage({ rechner: { text: 'Heim-PC · bereit', ton: 'gut' } }));
    act(() => q('island-einstellungen-kreis')!.click());
    expect(q('einstellungen-heimpc-lage')!.textContent).toBe('Heim-PC · bereit');
    expect(q('einstellungen-panel')!.querySelector('input[type="password"]')).toBeNull();
    act(() => q('einstellungen-heimpc-einrichten')!.click());
    expect(gesendet.at(-1)).toEqual({ art: 'oeffne', ziel: 'einrichten' });
  });

  it('Claude über MCP: an/aus über die App, der Befehl zum Verbinden steht da', () => {
    zeichne();
    act(() => wirt().lage({ claudeMcp: CLAUDE }));
    act(() => q('island-einstellungen-kreis')!.click());
    expect(q('einstellungen-claude-befehl')!.textContent).toBe(CLAUDE.befehl);
    const schalter = q('einstellungen-claude-schalter')!;
    const eingabe = (schalter.tagName === 'INPUT' ? schalter : schalter.querySelector('input')) as HTMLInputElement;
    expect(eingabe.checked).toBe(true);
    act(() => eingabe.click());
    expect(gesendet.at(-1)).toEqual({ art: 'claude', an: false });
  });

  it('Darstellung schaltet das Thema an <html>; die App merkt sich die Wahl', async () => {
    zeichne();
    act(() => q('island-einstellungen-kreis')!.click());
    act(() => q('einstellung-thema-paper')!.click());
    expect(document.documentElement.dataset.theme).toBe('paper');
    await act(async () => new Promise((r) => setTimeout(r, 1)));
    expect(gesendet).toContainEqual({ art: 'merke', schluessel: THEMA_SCHLUESSEL, wert: 'paper' });
    expect(gesendet.filter((n) => n['art'] === 'merke').every((n) => MERKBAR.includes(n['schluessel'] as string))).toBe(true);
  });

  it('Neuigkeiten: die Fassung, und was eine bereitstehende Fassung bringt', () => {
    zeichne();
    act(() => wirt().lage({ neuigkeiten: { fassung: 'v0.3.8', angebot: { nummer: '0.3.9', zeilen: ['Kugel und Gesprächsfeld'] } } }));
    act(() => q('island-einstellungen-kreis')!.click());
    expect(q('einstellungen-neuigkeiten-fassung')!.textContent).toContain('v0.3.8');
    expect(q('neuigkeiten-version-0.3.9')!.textContent).toContain('Kugel und Gesprächsfeld');
    act(() => q('einstellungen-aktualisieren')!.click());
    expect(gesendet.at(-1)).toEqual({ art: 'oeffne', ziel: 'aktualisieren' });
  });
});
