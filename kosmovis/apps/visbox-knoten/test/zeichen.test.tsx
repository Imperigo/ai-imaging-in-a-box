// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { KosmoOrb } from '../../kosmo-orbit/src/modules/design/island/KosmoOrb';
import { _setzeGespraechZurueck } from '../../kosmo-orbit/src/shell/kosmo-gespraech';
import { useKosmoStatus } from '../../kosmo-orbit/src/state/kosmo-status';
import { meldeAssistentAn, VisboxKopf, wechsleGespraech } from '../src/kopf';
import { useWirt } from '../src/wirt-bruecke';
import { legeThema } from '../src/thema';

/**
 * VISBOX-EIGEN (Owner-Entscheide 132/133, 22.10.2026, Blätter 47/48; Kleinauftrag vor der Demo): Oben links trägt
 * die Palette das Logo von Visbox statt der Kosmo-Spirale, unten rechts ist das Zeichen des Assistenten das Lot statt
 * der roten Kugel. Das Lot kommt allein aus `visbox.css` (die Kugel ist wortgleich aus der Kopie) — die Probe legt
 * darum die Regeln des Wirts in die Seite und fragt, was davon sichtbar bleibt.
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const CSS = readFileSync(resolve(process.cwd(), 'src/visbox.css'), 'utf8');

let root: Root | null = null;
let halter: HTMLDivElement | null = null;
let stil: HTMLStyleElement | null = null;

function zeichne(): void {
  stil = document.createElement('style');
  stil.textContent = CSS;
  document.head.appendChild(stil);
  halter = document.createElement('div');
  document.body.appendChild(halter);
  root = createRoot(halter);
  act(() =>
    root!.render(
      <div className="app-wurzel" data-station="vis">
        <VisboxKopf />
        <KosmoOrb onKosmoOeffnen={wechsleGespraech} />
      </div>,
    ),
  );
}

beforeEach(() => {
  _setzeGespraechZurueck();
  useKosmoStatus.setState({ zustand: 'idle', beschaeftigt: false, antwortBlase: null, auftrag: null });
  useWirt.setState({ rechner: null, version: null });
  legeThema();
  meldeAssistentAn();
  zeichne();
});

afterEach(() => {
  act(() => root?.unmount());
  halter?.remove();
  stil?.remove();
  root = null;
  halter = null;
  stil = null;
});

describe('Die zwei Zeichen von Visbox (Entscheide 132/133)', () => {
  it('oben links: das Visbox-Logo an der Palette, keine Kosmo-Spirale', () => {
    const logo = document.querySelector('[data-testid="werkzeug-palette-logo"]');
    expect(logo).not.toBeNull();
    expect(logo!.querySelector('[data-testid="visbox-logo"]')).not.toBeNull();
    // Kein Zeichen von KosmoOrbit im Kopf: weder die Station «vis» noch die Orbit-Marke.
    expect(logo!.querySelector('svg[data-logo="vis"], svg[data-logo="orbit"], svg[data-logo="kosmo"]')).toBeNull();
    // Die Palette dahinter bleibt wortgleich: Klick = Startansicht.
    expect(logo!.tagName).toBe('BUTTON');
  });

  it('unten rechts: das Lot statt der roten Kugel — der Inhalt des Kosmo-Zeichens ist verborgen', () => {
    const knopf = document.querySelector<HTMLButtonElement>('[data-testid="kosmo-eck-orb"]');
    expect(knopf).not.toBeNull();
    // Knopf und Name bleiben (wortgleich aus der Kopie, Name «Assistent»).
    expect(knopf!.getAttribute('aria-label')).toMatch(/^Assistent öffnen/);
    const zeichen = knopf!.querySelector('svg[data-logo="kosmo"]');
    expect(zeichen).not.toBeNull();
    const kern = zeichen!.querySelector('[data-kosmo-kern]');
    expect(kern).not.toBeNull();
    expect(getComputedStyle(kern as Element).display).toBe('none');
    for (const kind of Array.from(zeichen!.children)) expect(getComputedStyle(kind).display).toBe('none');
  });

  it('das Lot steht im Wirt: Senklot an der Schnur, Visbox-Blau, in beiden Themen', () => {
    const lote = CSS.match(/--visbox-lot: url\("data:image\/svg\+xml,[^"]+"\)/g) ?? [];
    expect(lote).toHaveLength(2);
    for (const lot of lote) {
      expect(lot).toContain("d='M32 6V30'"); // die Schnur
      expect(lot).toContain("d='M22 30H42L32 56Z'"); // das Lot
      expect(lot).toContain("fill='%232f6fd6'"); // Visbox-Blau
    }
    expect(CSS).toMatch(/\.app-wurzel svg\[data-logo='kosmo'\] \{\s*background: var\(--visbox-lot\)/);
    // Die rote Kugel hat in Visbox keine Farbe mehr: der Akzent an Kugel und Fensterkopf ist Visbox-Blau.
    expect(CSS).toMatch(/\.kp-kopf-orb-huelle \{\s*--k-mod-kosmo: var\(--visbox-blau\);/);
  });

  it('das Lot pendelt nur beim Rechnen, und bei reduzierter Bewegung gar nicht', () => {
    expect(CSS).toMatch(/\.app-wurzel \.keo-aktiv svg\[data-logo='kosmo'\][^{]*\{\s*animation: visbox-lot-pendeln/);
    expect(CSS).toMatch(/@media \(prefers-reduced-motion: reduce\) \{\s*\.app-wurzel svg\[data-logo='kosmo'\] \{\s*animation: none;/);
    expect(CSS).toContain(":root[data-bewegung='aus'] .app-wurzel svg[data-logo='kosmo']");
    expect(CSS).toContain(".app-wurzel [data-reduziert='true'] svg[data-logo='kosmo']");
    // Ruhig ist ruhig: kein Pendeln, solange der Assistent bereit ist.
    const wurzel = document.querySelector('[data-testid="kosmo-eck-orb-wurzel"]');
    expect(wurzel!.classList.contains('keo-aktiv')).toBe(false);
  });
});
