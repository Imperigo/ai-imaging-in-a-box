/**
 * Trackpad-Geste wie in Miro (E152, 06.10.2026, Owner: «auf sämtlichen
 * beweglichen Oberflächen … das Wischen auf dem Mac-Trackpad aktivieren, also
 * dass ich bewegen kann mit Wischfunktion»).
 *
 * Eine Regel fuer alle 2D-Flaechen (Grundriss, Schnitt/Ansicht, Knoten,
 * Prepare-Tafel, Publish-Blatt):
 *
 *  - **zwei Finger wischen** → schieben;
 *  - **zwei Finger auseinander/zusammen (Pinch)** → zoomen am Zeiger;
 *  - **Mausrad** → zoomen am Zeiger, wie bisher.
 *
 * Zwei Wege, wie ein Pinch ankommt — beide gemessen bekannt, darum beide hier:
 *
 *  1. Chromium (Browser, Vorschau, Proben): als `wheel` mit `ctrlKey: true`.
 *  2. WebKit (die Mac-App, Safari): als eigene Gesten-Ereignisse
 *     `gesturestart`/`gesturechange`/`gestureend` mit `scale` — dort kommt KEIN
 *     `wheel` mit `ctrlKey`. Ohne eigenen Hoerer zoomte in der Mac-App bisher
 *     keine Flaeche per Pinch (die Seite selbst wurde gezoomt oder nichts).
 *
 * Unterscheidung Wischen/Mausrad: dieselbe Regel wie seit P-NAV im Grundriss
 * (`istTrackpadSchritt`): ein Wischen hat `deltaX ≠ 0` oder einen nicht-ganzen
 * bzw. nicht-120er Schritt; ein Mausrad-Notch ist ganzzahlig und ein
 * Vielfaches von 120 in `wheelDelta`.
 *
 * Rein, ohne React: `deuteRad` sagt nur, WAS ein Rad-Ereignis bedeutet;
 * `bindeWebkitPinch` haengt die drei WebKit-Hoerer an ein Element und meldet
 * je Schritt einen Faktor. Die Flaechen rechnen ihre eigene Kamera weiter
 * wie bisher (jede hat eine andere Form, s. Kopf dieser Datei oben).
 */

import { istTrackpadSchritt, radZoomFaktor } from '../modules/design/navigation-geste';

/** Empfindlichkeit eines Chromium-Pinch (`wheel` + `ctrlKey`): feiner als das
 *  Mausrad, weil ein Pinch viele kleine Schritte liefert. */
export const PINCH_RAD_EMPFINDLICHKEIT = 0.01;

export type RadDeutung =
  | { readonly art: 'zoom'; readonly faktor: number }
  | { readonly art: 'schwenk'; readonly dx: number; readonly dy: number };

/** Die Felder eines `WheelEvent`, die die Deutung braucht (testbar ohne DOM). */
export interface RadEreignis {
  readonly deltaX?: number;
  readonly deltaY?: number;
  readonly deltaMode?: number;
  readonly ctrlKey?: boolean;
  readonly wheelDelta?: number;
}

/** Zeilen-/Seitenmodus in Pixel umrechnen (Firefox meldet Zeilen). */
function inPixel(wert: number, modus: number | undefined): number {
  if (modus === 1) return wert * 16;
  if (modus === 2) return wert * 800;
  return wert;
}

/**
 * Was bedeutet dieses Rad-Ereignis?
 *  - `ctrlKey` → Pinch (Chromium): zoomen, fein.
 *  - Wischen (Trackpad) → schieben um `dx`/`dy` Bildschirm-Pixel (die Flaeche
 *    bewegt sich MIT den Fingern: positiver `deltaY` schiebt den Inhalt nach oben).
 *  - sonst Mausrad → zoomen wie bisher (`radZoomFaktor`).
 */
export function deuteRad(e: RadEreignis): RadDeutung {
  const dy = inPixel(e.deltaY ?? 0, e.deltaMode);
  const dx = inPixel(e.deltaX ?? 0, e.deltaMode);
  if (e.ctrlKey) return { art: 'zoom', faktor: Math.exp(-dy * PINCH_RAD_EMPFINDLICHKEIT) };
  if (dx !== 0 || istTrackpadSchritt(e.deltaY ?? 0, e.wheelDelta)) return { art: 'schwenk', dx, dy };
  return { art: 'zoom', faktor: radZoomFaktor(dy) };
}

/** Ein WebKit-`GestureEvent`, so weit gebraucht. */
interface GestenEreignis extends Event {
  readonly scale: number;
  readonly clientX: number;
  readonly clientY: number;
}

/**
 * Haengt den WebKit-Pinch an `el` und meldet je Schritt den Zoomfaktor
 * relativ zum vorigen Schritt, mit Zeigerposition. Gibt die Abmelde-Funktion
 * zurueck. In Chromium feuern diese Ereignisse nie — dann tut der Hoerer
 * nichts, und der Pinch kommt ueber `deuteRad` (ctrlKey).
 */
export function bindeWebkitPinch(
  el: HTMLElement | SVGElement,
  onZoom: (faktor: number, clientX: number, clientY: number) => void,
): () => void {
  let letzte = 1;
  const start = (e: Event) => {
    e.preventDefault();
    letzte = 1;
  };
  const aendern = (e: Event) => {
    e.preventDefault();
    const g = e as GestenEreignis;
    if (!Number.isFinite(g.scale) || g.scale <= 0) return;
    const faktor = g.scale / letzte;
    letzte = g.scale;
    if (faktor !== 1) onZoom(faktor, g.clientX, g.clientY);
  };
  const ende = (e: Event) => {
    e.preventDefault();
    letzte = 1;
  };
  el.addEventListener('gesturestart', start, { passive: false } as AddEventListenerOptions);
  el.addEventListener('gesturechange', aendern, { passive: false } as AddEventListenerOptions);
  el.addEventListener('gestureend', ende, { passive: false } as AddEventListenerOptions);
  return () => {
    el.removeEventListener('gesturestart', start);
    el.removeEventListener('gesturechange', aendern);
    el.removeEventListener('gestureend', ende);
  };
}
