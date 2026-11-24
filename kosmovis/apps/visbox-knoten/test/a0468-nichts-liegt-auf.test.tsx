// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { rechteKanteUntereInsel, VisboxKopf } from '../src/kopf';
import { schliesseEinstellungen, VisboxEinstellungen } from '../src/einstellungen';
import { ladeMappe, SATZ_MAPPE_NICHT_LESBAR, SATZ_OHNE_MAPPE, satzFuerMenschen } from '../src/mappe';

/**
 * A0468 «Nichts liegt auf dem Bild», neu geschnitten am 20.11.2026 auf zwei Befunde des UI-Kehraus Visbox:
 *
 *  - **M05:** Der Heim-PC-Chip öffnet «Wer rechnet?» nicht. Gemessen im Wirt (Chromium, echter `server.py`): Die
 *    Insel rollte nur bis zum Anschlag, «Wer rechnet?» stand bei 1024x640 unter «Bewegung & Klang» in der Mitte,
 *    bei 1440x900 rollte sie 59 px, und der Fokus blieb am Chip hinter der Insel. Die bisherige Probe
 *    (`assistent-einstellungen.test.tsx`) sah das nicht: In jsdom gibt es kein Layout, und ein fehlendes
 *    `scrollIntoView` fiel still durch. Diese Probe gibt dem Rollkörper die GEMESSENE Geometrie beider Fenster.
 *  - **M06:** Ohne Projekt stand in der Meldung «In /tmp/… liegt kein Projekt (projekt.json fehlt). Ein neues legt
 *    `neu()` an.», 240 px über der Kante auf den Zeilen des Knotens «Kamera». Jetzt ein Satz mit dem nächsten
 *    Schritt, und der Meldungswirt steht in der Zeile der unteren Leisten.
 *
 * Bleiben (Prüfpunkt 10): Der Einstellungs-Kreis öffnet die Insel weiter oben bei «Heim-PC», ohne Markierung und
 * ohne leeren Rest; ein Satz des Heim-PC, der schon einer für Menschen ist, bleibt wörtlich stehen.
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const q = (id: string) => document.querySelector<HTMLElement>(`[data-testid="${id}"]`);

/**
 * Die Geometrie des Rollkörpers der Insel, gemessen am 20.11.2026 in Chromium (Stand int-0377): Oberkante 78 px,
 * Inhalt 856 px hoch, Abschnitte «Heim-PC» bei 16, «Wer rechnet?» bei 521, «Claude über MCP» bei 569 (im Inhalt,
 * Innenrand 16 px eingerechnet). Sichtbare Höhe je Fenster: 537 px (1024x640), 797 px (1440x900).
 */
const INHALT = 856;
const OBEN = 78;
const LAGE: Record<string, number> = { 'einstellungen-heimpc': 16, 'einstellungen-rechner': 521, 'einstellungen-claude': 569 };
const FENSTER = [
  { name: '1024x640', sichtbar: 537 },
  { name: '1440x900', sichtbar: 797 },
] as const;

let rollen = new WeakMap<HTMLElement, number>();
let sichtbar = 537;

function restHoehe(koerper: HTMLElement): number {
  const rest = koerper.querySelector<HTMLElement>('[data-testid="einstellungen-ziel-rest"]');
  return rest ? parseFloat(rest.style.height || '0') || 0 : 0;
}

function istKoerper(el: Element): el is HTMLElement {
  return el instanceof HTMLElement && el.classList.contains('es-koerper-scroll');
}

/** Wie der Browser: `scrollTop` hält sich zwischen 0 und Inhalt minus Sichtbares. */
function legeGeometrieAn(): void {
  rollen = new WeakMap();
  const rechteck = (top: number, hoehe: number) =>
    ({ top, bottom: top + hoehe, left: 0, right: 600, width: 600, height: hoehe, x: 0, y: top, toJSON: () => ({}) }) as DOMRect;
  vi.spyOn(Element.prototype, 'getBoundingClientRect').mockImplementation(function (this: Element) {
    if (istKoerper(this)) return rechteck(OBEN, sichtbar);
    const id = this.getAttribute('data-testid') ?? '';
    const koerper = this.closest('.es-koerper-scroll') as HTMLElement | null;
    if (koerper && id in LAGE) return rechteck(OBEN + LAGE[id]! - (rollen.get(koerper) ?? 0), 40);
    return rechteck(0, 0);
  });
  Object.defineProperty(HTMLElement.prototype, 'scrollTop', {
    configurable: true,
    get(this: HTMLElement) {
      return rollen.get(this) ?? 0;
    },
    set(this: HTMLElement, wert: number) {
      if (!istKoerper(this)) return;
      const hoechstens = Math.max(0, INHALT + restHoehe(this) - sichtbar);
      rollen.set(this, Math.min(Math.max(0, wert), hoechstens));
    },
  });
  // Wie Chromium: `scrollIntoView({ block: 'start' })` rollt den Körper bis zum Abschnitt, höchstens bis zum Anschlag
  // (so sah der Kehraus den alten Sprung: «Wer rechnet?» bei 1024x640 in der Mitte, bei 1440x900 kaum gerollt).
  Object.defineProperty(Element.prototype, 'scrollIntoView', {
    configurable: true,
    value(this: Element) {
      const koerper = this.closest('.es-koerper-scroll') as HTMLElement | null;
      const id = this.getAttribute('data-testid') ?? '';
      if (koerper && id in LAGE) koerper.scrollTop = LAGE[id]!;
    },
  });
  Object.defineProperty(HTMLElement.prototype, 'clientHeight', {
    configurable: true,
    get(this: HTMLElement) {
      return istKoerper(this) ? sichtbar : 0;
    },
  });
  Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
    configurable: true,
    get(this: HTMLElement) {
      return istKoerper(this) ? sichtbar : 0;
    },
  });
  Object.defineProperty(HTMLElement.prototype, 'scrollHeight', {
    configurable: true,
    get(this: HTMLElement) {
      return istKoerper(this) ? INHALT + restHoehe(this) : 0;
    },
  });
}

function raeumeGeometrieAb(): void {
  for (const name of ['scrollTop', 'clientHeight', 'offsetHeight', 'scrollHeight']) {
    delete (HTMLElement.prototype as unknown as Record<string, unknown>)[name];
  }
  delete (Element.prototype as unknown as Record<string, unknown>)['scrollIntoView'];
}

/** Welcher Abschnittstitel als erster ganz im Sichtbaren steht (wie die Messung im Browser). */
function ersterSichtbarerAbschnitt(koerper: HTMLElement): string | null {
  const roll = rollen.get(koerper) ?? 0;
  const ids = Object.keys(LAGE).sort((a, b) => LAGE[a]! - LAGE[b]!);
  for (const id of ids) if (LAGE[id]! - roll >= 0) return id;
  return null;
}

let root: Root | null = null;
let halter: HTMLDivElement | null = null;

function zeichne(): void {
  halter = document.createElement('div');
  document.body.appendChild(halter);
  root = createRoot(halter);
  act(() =>
    root!.render(
      <div className="app-wurzel" data-station="vis">
        <VisboxKopf />
        <VisboxEinstellungen />
      </div>,
    ),
  );
}

beforeEach(() => {
  legeGeometrieAn();
});

afterEach(() => {
  act(() => schliesseEinstellungen());
  act(() => root?.unmount());
  halter?.remove();
  root = null;
  halter = null;
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  raeumeGeometrieAb();
});

describe('A0468 M05: der Heim-PC-Chip öffnet «Wer rechnet?»', () => {
  for (const f of FENSTER) {
    it(`bei ${f.name}: «Wer rechnet?» steht oben, ist markiert und hat den Fokus`, () => {
      sichtbar = f.sichtbar;
      zeichne();
      act(() => q('heimpc-chip')!.click());
      const koerper = document.querySelector<HTMLElement>('.es-koerper-scroll')!;
      const abschnitt = q('einstellungen-rechner')!;
      // Oben: der Abschnitt beginnt an der Oberkante des Rollkörpers, nichts darüber ist mehr zu sehen.
      expect(abschnitt.getBoundingClientRect().top - koerper.getBoundingClientRect().top).toBe(0);
      expect(ersterSichtbarerAbschnitt(koerper)).toBe('einstellungen-rechner');
      // Markiert und mit Fokus: Tab geht von hier in seine Felder, nicht vom Chip hinter der Insel.
      expect(abschnitt.getAttribute('data-ziel')).toBe('ja');
      expect(document.activeElement).toBe(abschnitt);
      expect(q('heimpc-chip')!.contains(document.activeElement)).toBe(false);
      // Nur so viel leerer Rest, wie zum Hochrollen fehlt.
      expect(restHoehe(koerper)).toBe(Math.max(0, 521 + f.sichtbar - INHALT));
    });

    it(`bei ${f.name}: Tab vom Abschnitt bleibt in der Insel, auch ohne Felder in «Wer rechnet?»`, () => {
      sichtbar = f.sichtbar;
      zeichne();
      act(() => q('heimpc-chip')!.click());
      const abschnitt = q('einstellungen-rechner')!;
      const insel = q('einstellungen-panel')!;
      // Ohne App: in «Wer rechnet?» und danach kein Feld mehr, also zum ersten Feld der Insel (Schliessen).
      act(() => void abschnitt.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true })));
      expect(insel.contains(document.activeElement)).toBe(true);
      expect(document.activeElement).toBe(q('einstellungen-schliessen'));
      // Rückwärts: zum Feld vor dem Abschnitt, nicht hinter die Insel.
      act(() => abschnitt.focus());
      act(() => void abschnitt.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true, cancelable: true })));
      expect(insel.contains(document.activeElement)).toBe(true);
      expect(abschnitt.contains(document.activeElement)).toBe(false);
    });

    it(`bei ${f.name}: der Einstellungs-Kreis öffnet weiter oben bei «Heim-PC» (bleibt)`, () => {
      sichtbar = f.sichtbar;
      zeichne();
      act(() => q('island-einstellungen-kreis')!.click());
      const koerper = document.querySelector<HTMLElement>('.es-koerper-scroll')!;
      expect(koerper.scrollTop).toBe(0);
      expect(ersterSichtbarerAbschnitt(koerper)).toBe('einstellungen-heimpc');
      expect(document.querySelector('[data-ziel]')).toBeNull();
      expect(q('einstellungen-ziel-rest')).toBeNull();
    });
  }
});

describe('A0468 M06: die Meldung ohne Projekt ist ein Satz für Menschen, am unteren Rand', () => {
  const KERN_SATZ = 'In /tmp/vb-ord liegt kein Projekt (projekt.json fehlt). Ein neues legt `neu()` an.';
  const antwort = (status: number, rumpf: string) => new Response(rumpf, { status, headers: { 'Content-Type': 'application/json' } });

  it('ohne Projekt: kein Pfad, kein Dateiname, kein Funktionsaufruf, dafür der nächste Schritt', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => antwort(404, JSON.stringify({ fehler: KERN_SATZ }))));
    const satz = await ladeMappe();
    expect(satz).toBe(SATZ_OHNE_MAPPE);
    expect(satz).not.toMatch(/\/tmp|projekt\.json|neu\(\)|`/);
    expect(satz).toContain('«Datei laden …»');
  });

  it('ohne Projektordner (Satz mit Startoption): derselbe Satz', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => antwort(404, JSON.stringify({ fehler: 'Kein Projektordner — mit --ordner starten oder auf der Visbox-Seite einen öffnen.' }))));
    expect(await ladeMappe()).toBe(SATZ_OHNE_MAPPE);
  });

  it('Fehlerseite oder keine Antwort: ein Satz mit Weg, kein Programmtext', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('<html><body>Traceback (most recent call last)</body></html>', { status: 500 })));
    expect(await ladeMappe()).toBe(SATZ_MAPPE_NICHT_LESBAR);
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))));
    expect(await ladeMappe()).toBe(SATZ_MAPPE_NICHT_LESBAR);
  });

  it('bleibt: ein Satz des Heim-PC für Menschen steht wörtlich', async () => {
    const satz = 'Eine Mappe «gegenprobe» gibt es auf diesem Heim-PC nicht.';
    vi.stubGlobal('fetch', vi.fn(async () => antwort(404, JSON.stringify({ fehler: satz }))));
    expect(await ladeMappe()).toBe(satz);
    expect(satzFuerMenschen('Die Mappe hat noch kein Modell.')).toBe('Die Mappe hat noch kein Modell.');
    expect(satzFuerMenschen(KERN_SATZ)).toBeNull();
    expect(satzFuerMenschen('Die Projektdatei liess sich nicht lesen: [Errno 13] Permission denied.')).toBeNull();
  });

  it('der Wirt misst die rechte Kante der Austausch-Insel, auch offen (Leiste breiter als die Pille)', () => {
    const wurzel = document.createElement('div');
    wurzel.innerHTML = '<div class="isl-root isl-rand-unten"><button class="pille"></button><div class="isl-leiste"></div><div class="aus" style="visibility:hidden"></div></div>';
    document.body.appendChild(wurzel);
    const rechts: Record<string, number> = { 'isl-root isl-rand-unten': 556, pille: 556, 'isl-leiste': 612, aus: 900 };
    vi.spyOn(Element.prototype, 'getBoundingClientRect').mockImplementation(function (this: Element) {
      const r = rechts[this.className] ?? 0;
      return { left: r - 88, right: r, top: 0, bottom: 34, width: r ? 88 : 0, height: r ? 34 : 0, x: 0, y: 0, toJSON: () => ({}) } as DOMRect;
    });
    expect(rechteKanteUntereInsel(wurzel)).toBe(612);
    wurzel.querySelector('.isl-leiste')!.remove();
    expect(rechteKanteUntereInsel(wurzel)).toBe(556);
    expect(rechteKanteUntereInsel(document.createElement('div'))).toBeNull();
    wurzel.remove();
  });

  it('der Meldungswirt steht in der Zeile der unteren Leisten, rechts neben der Austausch-Pille', () => {
    const css = readFileSync(resolve(__dirname, '../src/visbox.css'), 'utf-8');
    const regel = /\.app-wurzel \.k-meldungen-host\s*\{([^}]*)\}/.exec(css)?.[1] ?? '';
    expect(regel).toMatch(/bottom:\s*var\(--isl-rand-abstand, 14px\)/);
    expect(regel).toMatch(/left:\s*calc\(var\(--visbox-meldung-links, calc\(var\(--visbox-meldung-pille-mitte\) \+ 44px\)\) \+ var\(--k-s3\)\)/);
    expect(regel).toMatch(/right:\s*calc\(var\(--k-s4\) \+ 56px \+ var\(--k-s3\)\)/);
    expect(regel).toMatch(/transform:\s*none/);
    expect(regel).not.toMatch(/240px/);
  });
});
