// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { KosmoEckOrb } from '../src/shell/kosmo-eck-orb/KosmoEckOrb';
import { KosmoKopfOrb } from '../src/shell/kosmo-fenster/KosmoKopfOrb';
import { VollautomatikSchalter } from '../src/shell/kosmo-maus/KosmoCoop';
import { erzaehlungAus, type ErzaehlEingang } from '../src/shell/claude-anschluss/erzaehl-zeile';
import { URHEBER_NAME } from '../src/state/kosmo-maus-freigabe';
import { KOSMO_NAME_VORGABE, kosmoName, registriereKosmoName } from '../src/state/kosmo-name';
import {
  AbschnittAnzeige,
  AbschnittBewegungKlang,
  AbschnittDarstellung,
  EinstellungenSchale,
  SchalterTouchUndo,
} from '../src/shell/einstellungen-teile';

/**
 * KosmoVis-Kopf S3/S4 (Visbox-Entscheide 115/116, 20.10.2026): Visbox uebernimmt die Kugel, den
 * Fensterkopf, die Coop-Teile und die Schale der Einstellungen wortgleich. Zwei Nahtstellen:
 *
 *  1. `registriereKosmoName` — der Name des Assistenten neben Claude (Visbox: «Assistent»), gelesen
 *     beim Zeichnen von Kugel, Fensterkopf, Coop-Teilen und Erzaehlzeile;
 *  2. `einstellungen-teile.tsx` — Schale, «Darstellung», «Anzeige» und der Rahmen von «Bewegung &
 *     Klang» als eigene Bausteine, die `Einstellungen.tsx` unveraendert einsetzt.
 *
 * Und fuer jede: **ohne Wirt bleibt KosmoOrbit, wie es war** (Gegenbelege; die Bestandsproben der
 * Einstellungen und des Eck-Orbs laufen unveraendert).
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let root: Root | null = null;
let halter: HTMLDivElement | null = null;
const q = (id: string) => document.querySelector<HTMLElement>(`[data-testid="${id}"]`);
function render(el: React.ReactElement): void {
  halter = document.createElement('div');
  document.body.appendChild(halter);
  root = createRoot(halter);
  act(() => root!.render(el));
}

afterEach(() => {
  if (root) act(() => root!.unmount());
  root = null;
  halter?.remove();
  halter = null;
  registriereKosmoName(null);
});

const SCHRITT_VON_KOSMO = {
  offeneKarten: [],
  letzterSchritt: { urheber: 'kosmo', zusammenfassung: 'Wand gesetzt', zeit: 1000, zurueckgenommen: false },
  taetigkeit: null,
  zuletztAktiv: null,
  jetzt: 1500,
} as unknown as ErzaehlEingang;

describe('1 · Der Name des Assistenten', () => {
  it('ohne Wirt heisst er «Kosmo» — Kugel, Kopf-Orb, Namenstafel und Erzaehlzeile', () => {
    expect(kosmoName()).toBe(KOSMO_NAME_VORGABE);
    expect(URHEBER_NAME.kosmo).toBe('Kosmo');
    render(<KosmoEckOrb onOeffnen={() => undefined} />);
    expect(q('kosmo-eck-orb')?.getAttribute('aria-label')).toMatch(/^Kosmo öffnen — /);
    expect(erzaehlungAus(SCHRITT_VON_KOSMO)).toMatchObject({ text: 'Kosmo · Wand gesetzt' });
  });

  it('mit Wirt traegt jede dieser Stellen dessen Namen', () => {
    registriereKosmoName('Assistent');
    expect(URHEBER_NAME.kosmo).toBe('Assistent');
    expect(URHEBER_NAME.claude).toBe('Claude');
    render(
      <>
        <KosmoEckOrb onOeffnen={() => undefined} offen />
        <KosmoKopfOrb zustand="denkt" arbeitet abbruchVerlangt={false} onStopp={() => undefined} />
        <VollautomatikSchalter />
      </>,
    );
    expect(q('kosmo-eck-orb')?.getAttribute('aria-label')).toMatch(/^Assistent schliessen — /);
    expect(document.querySelector('[aria-label="Assistent anhalten"]')).not.toBeNull();
    expect(document.body.textContent).toContain('Claude und Assistent wenden ihre Vorschläge selbst an');
    expect(erzaehlungAus(SCHRITT_VON_KOSMO)).toMatchObject({ text: 'Assistent · Wand gesetzt' });
    expect(document.body.textContent).not.toMatch(/Kosmo/);
  });

  it('ein leerer Name stellt «Kosmo» wieder her', () => {
    registriereKosmoName('Assistent');
    registriereKosmoName('   ');
    expect(kosmoName()).toBe('Kosmo');
  });
});

describe('2 · Die Teile der Einstellungen', () => {
  it('die Schale traegt Scrim, Panel, Titel und Schliessen — Escape und Klick daneben schliessen', () => {
    const zu = vi.fn();
    render(
      <EinstellungenSchale titel="Einstellungen" onClose={zu}>
        <p data-testid="inhalt">Inhalt</p>
      </EinstellungenSchale>,
    );
    expect(q('einstellungen-panel')?.className).toContain('es-panel');
    expect(q('einstellungen-panel')?.textContent).toContain('Einstellungen');
    expect(q('einstellungen-panel')?.contains(q('inhalt'))).toBe(true);
    act(() => q('einstellungen-schliessen')!.click());
    act(() => q('einstellungen-scrim')!.click());
    expect(zu).toHaveBeenCalledTimes(2);
    act(() => q('inhalt')!.click());
    expect(zu).toHaveBeenCalledTimes(2);
  });

  it('Darstellung ruft die Setter des Aufrufers, Anzeige setzt Schrift und Bewegung an <html>', () => {
    const thema = vi.fn();
    const akzent = vi.fn();
    render(
      <>
        <AbschnittDarstellung theme="orbit" setTheme={thema} akzent="tusche" setAkzent={akzent} />
        <AbschnittAnzeige />
        <AbschnittBewegungKlang>
          <SchalterTouchUndo />
        </AbschnittBewegungKlang>
      </>,
    );
    expect(q('einstellung-thema-orbit')?.getAttribute('aria-pressed')).toBe('true');
    act(() => q('einstellung-thema-paper')!.click());
    act(() => q('einstellung-akzent-kupfer')!.click());
    expect(thema).toHaveBeenCalledWith('paper');
    expect(akzent).toHaveBeenCalledWith('kupfer');
    act(() => q('einstellung-schrift-gross')!.click());
    expect(document.documentElement.dataset['schrift']).toBe('gross');
    expect(q('einstellungen-bewegung-klang')?.textContent).toContain('Bewegung & Klang');
    const touch = q('einstellung-touch-undo-geste')?.querySelector('input') ?? (q('einstellung-touch-undo-geste') as HTMLInputElement);
    expect(touch).not.toBeNull();
  });
});
