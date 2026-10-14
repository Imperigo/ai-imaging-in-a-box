// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { KDialog } from '../src/overlay';

/**
 * U19, Owner C5 (01.10.2026): «Ein Fenster erscheint aus dem Auslöser» — es
 * wächst aus dem Knopf, der es geöffnet hat, statt irgendwo aufzutauchen.
 * Das ist Visbox-Regel 4 «ein Gegenstand, ein Weg» für Fenster.
 *
 * Rot vor gruen: vorher wuchs jeder `KDialog` aus seiner eigenen Mitte.
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
let root: Root | null = null;
let halter: HTMLDivElement | null = null;
afterEach(() => {
  act(() => root?.unmount());
  halter?.remove();
  document.body.innerHTML = '';
});

function rechteck(el: Element, x: number, y: number, b: number, h: number) {
  (el as HTMLElement).getBoundingClientRect = () => ({ left: x, top: y, width: b, height: h, right: x + b, bottom: y + h, x, y, toJSON() {} }) as DOMRect;
}

function oeffneAus(knopf: HTMLButtonElement | null): HTMLElement {
  halter = document.createElement('div');
  document.body.appendChild(halter);
  root = createRoot(halter);
  if (knopf) knopf.focus();
  // Die Box steht bei (400, 200); jsdom rechnet kein Layout, darum gesetzt.
  const orig = HTMLElement.prototype.getBoundingClientRect;
  HTMLElement.prototype.getBoundingClientRect = function () {
    if (this.classList.contains('k-dialog-box')) return { left: 400, top: 200, width: 500, height: 300, right: 900, bottom: 500, x: 400, y: 200, toJSON() {} } as DOMRect;
    return orig.call(this);
  };
  act(() => root!.render(<KDialog titel="Probe" onClose={() => {}}>Inhalt</KDialog>));
  HTMLElement.prototype.getBoundingClientRect = orig;
  return document.querySelector('.k-dialog-box') as HTMLElement;
}

describe('Fenster wachsen aus dem Auslöser (C5)', () => {
  it('der Ursprung liegt auf der Mitte des Knopfs, der das Fenster geöffnet hat', () => {
    const knopf = document.createElement('button');
    document.body.appendChild(knopf);
    rechteck(knopf, 100, 50, 40, 20); // Mitte (120, 60)
    const box = oeffneAus(knopf);
    expect(box.classList.contains('k-aus-ausloeser')).toBe(true);
    // relativ zur Box: 120 − 400 = −280, 60 − 200 = −140
    expect(box.style.transformOrigin).toBe('-280px -140px');
  });

  it('ohne Auslöser wächst das Fenster aus seiner Mitte (kein Ursprung gesetzt)', () => {
    const box = oeffneAus(null);
    expect(box.style.transformOrigin).toBe('');
  });
});
