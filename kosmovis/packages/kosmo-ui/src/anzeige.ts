import { useSyncExternalStore } from 'react';

/**
 * **Anzeige: Schriftgrösse und Bewegung einstellbar** (U14, Owner B6/B18,
 * 01.10.2026).
 *
 * * **Schrift:** klein · normal · gross. Wirkt über `data-schrift` an <html>;
 *   `aura.css` skaliert dort jede Stufe der Schrift-Leiter (`--k-t-*`).
 * * **Bewegung:** «wie das Gerät» (Vorgabe) oder der eigene Schalter
 *   voll · ruhig · aus. Wirkt über `data-bewegung` an <html>:
 *   - **aus** wie der Riegel des Geräts (jede Bewegung auf 0,01 ms);
 *   - **ruhig** lässt Übergänge, hält aber jede Schleife nach einem Durchgang
 *     an (kein Atmen, kein Kreisen). Ein Zustand, der sonst nur in der
 *     Bewegung steckt, braucht dann sein Wort (Owner G1, Visbox).
 *
 * Komponenten fragen `useBewegung()` (oder `bewegungJetzt()` ausserhalb von
 * React) statt selbst `prefers-reduced-motion` zu lesen — sonst gilt der
 * eigene Schalter dort nicht.
 */

export type Schriftgroesse = 'klein' | 'normal' | 'gross';
export type BewegungsWahl = 'geraet' | 'voll' | 'ruhig' | 'aus';
export type Bewegung = 'voll' | 'ruhig' | 'aus';

interface AnzeigeStand {
  schrift: Schriftgroesse;
  bewegung: BewegungsWahl;
}

const SCHLUESSEL = 'kosmo.anzeige';
const VORGABE: AnzeigeStand = { schrift: 'normal', bewegung: 'geraet' };
let stand: AnzeigeStand = { ...VORGABE };
const hoerer = new Set<() => void>();

function lies(): AnzeigeStand {
  try {
    const roh = typeof localStorage !== 'undefined' ? localStorage.getItem(SCHLUESSEL) : null;
    if (!roh) return { ...VORGABE };
    const j = JSON.parse(roh) as Partial<AnzeigeStand>;
    return {
      schrift: j.schrift === 'klein' || j.schrift === 'gross' ? j.schrift : 'normal',
      bewegung: j.bewegung === 'voll' || j.bewegung === 'ruhig' || j.bewegung === 'aus' ? j.bewegung : 'geraet',
    };
  } catch {
    return { ...VORGABE };
  }
}

function schreibe(): void {
  try {
    localStorage.setItem(SCHLUESSEL, JSON.stringify(stand));
  } catch {
    /* privater Modus: gilt dann nur für diese Sitzung */
  }
}

/**
 * Welle E3 · C14 (Home-PC-Worker, 06.10.2026): zeichnet diese Engine das Glas
 * ohne Weichzeichner? Ja bei WebKitGTK — der Desktop-App unter Linux. Dort
 * liest WebKit `backdrop-filter` (für CSS also «unterstützt»), zeichnet ihn je
 * nach Version und Grafiktreiber aber nicht: Fenster und Listen waren
 * halbdurchsichtig und der Inhalt dahinter scharf lesbar. `aura.css` macht das
 * Glas bei `data-glas="deckend"` deckend. Chromium (auch unter Linux), Safari
 * am Mac, das iPad, Android und Firefox behalten das Glas.
 */
export function glasOhneWeichzeichner(ua: string = typeof navigator !== 'undefined' ? navigator.userAgent : ''): boolean {
  return /AppleWebKit/.test(ua) && /(X11|Linux)/.test(ua) && !/(Chrome|Chromium|Android|jsdom)/.test(ua);
}

function wende(): void {
  if (typeof document === 'undefined') return;
  const el = document.documentElement;
  el.dataset.schrift = stand.schrift;
  if (glasOhneWeichzeichner()) el.dataset.glas = 'deckend';
  else el.removeAttribute('data-glas');
  // «wie das Gerät» setzt kein Attribut: dann gilt allein die Systemeinstellung.
  if (stand.bewegung === 'geraet') el.removeAttribute('data-bewegung');
  else el.dataset.bewegung = stand.bewegung;
  hoerer.forEach((h) => h());
}

/** Beim Start einmal aufrufen (liest die gemerkte Wahl). */
export function ladeAnzeige(): void {
  stand = lies();
  wende();
}

export function setzeSchrift(s: Schriftgroesse): void {
  stand = { ...stand, schrift: s };
  schreibe();
  wende();
}

export function setzeBewegung(b: BewegungsWahl): void {
  stand = { ...stand, bewegung: b };
  schreibe();
  wende();
}

export function anzeigeWahl(): Readonly<AnzeigeStand> {
  return stand;
}

function geraetWill(): boolean {
  try {
    return typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  } catch {
    return false;
  }
}

/** Die wirksame Bewegung: der eigene Schalter, sonst das Gerät. */
export function bewegungJetzt(): Bewegung {
  if (stand.bewegung !== 'geraet') return stand.bewegung;
  return geraetWill() ? 'aus' : 'voll';
}

function abonniere(melde: () => void): () => void {
  hoerer.add(melde);
  let mq: MediaQueryList | null = null;
  try {
    mq = typeof window !== 'undefined' && window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
    mq?.addEventListener?.('change', melde);
  } catch {
    mq = null;
  }
  return () => {
    hoerer.delete(melde);
    mq?.removeEventListener?.('change', melde);
  };
}

export function useBewegung(): Bewegung {
  return useSyncExternalStore(abonniere, bewegungJetzt, () => 'voll');
}

export function useAnzeigeWahl(): Readonly<AnzeigeStand> {
  return useSyncExternalStore(abonniere, anzeigeWahl, () => VORGABE);
}

if (typeof window !== 'undefined') stand = lies();
