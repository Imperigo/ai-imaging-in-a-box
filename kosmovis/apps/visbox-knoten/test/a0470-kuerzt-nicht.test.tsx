// @vitest-environment node
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

/**
 * A0470 «Visbox kürzt nicht», neu geschnitten am 20.11.2026 auf den Visbox-Rest B126 des UI-Kehraus:
 * Der Urteilssatz unter dem Bild der Web-Seite (`oberflaeche/seite.html`, `.rahmen .auflage`, «DURCHGEFALLEN · 0.40
 * (Schwelle 0.70) · Die Geometrieprüfung …») wurde bei 1024x640 abgeschnitten, ausgerechnet die dritte Antwort.
 *
 * Ursache, gemessen am 21.11.2026 in Chromium mit dem echten `server.py`: Die Auflage stand `position: absolute`
 * im Rahmen, und der Rahmen hat `overflow: hidden` (runde Ecken). Seine Höhe kam allein vom Bild. Solange das Bild
 * lädt oder `loading="lazy"` es noch zurückhält, war der Rahmen 4 px hoch (nur die Ränder) und der ganze Satz weg;
 * ein Streifenbild, flacher als der Satz, kappte ihn ebenso. Jetzt liegen Bild und Auflage in derselben
 * Rasterzelle: Die Auflage sitzt unten auf dem Bild, und die Zelle ist mindestens so hoch wie der Satz.
 *
 * Diese Probe liest die Regeln aus der Seite selbst (in jsdom gibt es kein Layout, darum keine Messung hier); die
 * Messung im Fenster (1024x640, 1440x900, hell und dunkel, mit WCAG 1.4.12) liegt bei der Meldung in der Zentrale
 * unter `anhang/20261120-A0470/`. Der alte Stand von `int-0377` fällt in dieser Probe durch (rot vor grün).
 *
 * Bleiben (Prüfpunkt 10): Die Auflage sitzt weiter AUF dem Bild (dieselbe Zelle, unten bündig), deckt mit .94 wie
 * vorher (`tests/test_kontrast.py`), die zweite Zeile «SKIZZE NICHT ANGEKOMMEN» steht weiter als eigene Zeile, und der
 * Rahmen behält seine runden Ecken (`overflow: hidden`).
 */

const SEITE = resolve(__dirname, '../../../../oberflaeche/seite.html');

type Regel = { selektor: string; werte: Record<string, string> };

/** Die Regeln aus dem `<style>` der Seite, ohne Kommentare; `@media`-Blöcke werden mitgelesen. */
function regeln(html: string): Regel[] {
  const stil = html.match(/<style>([\s\S]*?)<\/style>/);
  if (!stil) throw new Error('kein <style> in seite.html');
  const css = stil[1].replace(/\/\*[\s\S]*?\*\//g, '');
  const aus: Regel[] = [];
  const muster = /([^{}]+)\{([^{}]*)\}/g;
  for (let m = muster.exec(css); m; m = muster.exec(css)) {
    const selektor = m[1].replace(/^[\s\S]*@media[^{]*\{/, '').trim().replace(/\s+/g, ' ');
    const werte: Record<string, string> = {};
    for (const teil of m[2].split(';')) {
      const i = teil.indexOf(':');
      if (i < 0) continue;
      werte[teil.slice(0, i).trim().toLowerCase()] = teil.slice(i + 1).trim().replace(/\s+/g, ' ').toLowerCase();
    }
    aus.push({ selektor, werte });
  }
  return aus;
}

/** Alle Regeln, deren Selektor (einer der Teile vor dem Komma) auf das Ziel endet. */
function fuer(alle: Regel[], ende: RegExp): Regel[] {
  return alle.filter((r) => r.selektor.split(',').some((s) => ende.test(s.trim())));
}

/** Die Gründe, warum der Urteilssatz gekürzt werden kann; leer heisst: kürzt nicht. */
function kuerzungen(html: string): string[] {
  const alle = regeln(html);
  const gruende: string[] = [];
  for (const r of alle) {
    if (/ellipsis/.test(r.werte['text-overflow'] ?? '')) gruende.push(`Ellipse in «${r.selektor}»`);
  }
  const auflage = fuer(alle, /\.auflage$/);
  if (!auflage.length) gruende.push('keine Regel für .auflage');
  for (const r of auflage) {
    const w = r.werte;
    if (/absolute|fixed/.test(w.position ?? '')) gruende.push(`«${r.selektor}» steht ${w.position}: die Höhe des Rahmens kommt dann allein vom Bild`);
    if (/nowrap|pre$/.test(w['white-space'] ?? '')) gruende.push(`«${r.selektor}» bricht nicht um (${w['white-space']})`);
    if (/hidden|clip/.test(w.overflow ?? '')) gruende.push(`«${r.selektor}» schneidet selbst ab (overflow ${w.overflow})`);
    for (const k of ['height', 'max-height']) if (w[k] && w[k] !== 'auto' && w[k] !== 'none') gruende.push(`«${r.selektor}» hat ${k} ${w[k]}`);
  }
  const rahmen = fuer(alle, /^\.rahmen$/);
  if (!rahmen.length) gruende.push('keine Regel für .rahmen');
  const raster = rahmen.some((r) => r.werte.display === 'grid');
  if (!raster) gruende.push('.rahmen ist kein Raster: Bild und Satz teilen sich keine Zelle');
  for (const r of rahmen) for (const k of ['height', 'max-height']) if (r.werte[k] && r.werte[k] !== 'auto' && r.werte[k] !== 'none') gruende.push(`.rahmen hat ${k} ${r.werte[k]}`);
  // Bild und Satz in derselben Zelle, der Satz unten
  const zelle = (ziel: RegExp) => fuer(alle, ziel).map((r) => r.werte['grid-area']).find(Boolean);
  if (raster) {
    if (zelle(/^\.rahmen > img$/) !== '1 / 1') gruende.push('das Bild liegt nicht in Zelle 1 / 1');
    if (zelle(/^\.rahmen > \.auflage$/) !== '1 / 1') gruende.push('der Satz liegt nicht in der Zelle des Bildes');
    if (!auflage.some((r) => r.werte['align-self'] === 'end')) gruende.push('der Satz sitzt nicht unten auf dem Bild');
    if (zelle(/^\.rahmen > \.fehlt ~ \.auflage$/) !== '2 / 1') gruende.push('bei fehlender Datei liegt der Satz über dem Text der Lücke');
  }
  return gruende;
}

const html = readFileSync(SEITE, 'utf-8');

describe('A0470: der Urteilssatz der Web-Seite wird nie gekürzt (B126)', () => {
  it('die Seite hat keine Regel, die den Urteilssatz kürzen kann', () => {
    expect(kuerzungen(html)).toEqual([]);
  });

  it('keine Ellipse irgendwo auf der Seite', () => {
    expect(html).not.toMatch(/text-overflow\s*:\s*ellipsis/i);
  });

  it('rot vor grün: der Stand von int-0377 (Auflage absolut im Rahmen) fällt durch', () => {
    const alt = html
      .replace(/display: grid; grid-template-columns: minmax\(0, 1fr\); \}/, '}')
      .replace(/position: relative; align-self: end; min-width: 0; overflow-wrap: anywhere; padding: 6px 10px;/,
        'position: absolute; left: 0; right: 0; bottom: 0; padding: 6px 10px;');
    expect(alt).not.toEqual(html);
    const gruende = kuerzungen(alt);
    expect(gruende.some((g) => /steht absolute/.test(g))).toBe(true);
    expect(gruende.some((g) => /kein Raster/.test(g))).toBe(true);
  });

  it('absichtlich gebrochen: Ellipse und nowrap am Satz werden erkannt', () => {
    const gebrochen = html.replace('</style>', '.rahmen .auflage { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }\n</style>');
    const gruende = kuerzungen(gebrochen);
    expect(gruende.some((g) => /Ellipse/.test(g))).toBe(true);
    expect(gruende.some((g) => /bricht nicht um/.test(g))).toBe(true);
    expect(gruende.some((g) => /schneidet selbst ab/.test(g))).toBe(true);
  });

  it('bleibt: Auflage auf dem Bild mit .94 Deckung, zweite Zeile als eigene Zeile, runde Ecken', () => {
    const alle = regeln(html);
    const auflage = fuer(alle, /^\.rahmen \.auflage$/);
    expect(auflage.some((r) => r.werte.background === 'rgba(8,10,13,.94)')).toBe(true);
    expect(auflage.some((r) => r.werte['z-index'] === '2')).toBe(true);
    expect(fuer(alle, /^\.rahmen \.auflage \.zweit$/).some((r) => r.werte.display === 'block')).toBe(true);
    expect(fuer(alle, /^\.rahmen$/).some((r) => r.werte.overflow === 'hidden' && r.werte['border-radius'] === '6px')).toBe(true);
    // Der Satz wird nach dem Bild in den Rahmen gesetzt, also liegt er im Raster über dem Bild.
    expect(html).toMatch(/rahmen\.append\(auflage\);\s*return rahmen;/);
    // Wortlaut des Urteils unverändert (der Auftrag ändert keine Texte).
    expect(html).toContain('zeichenwort(b) +\n    (zahl ? " · " + zahl.score + (zahl.schwelle ? " (Schwelle " + zahl.schwelle + ")" : "") : "") +\n    " · " + b.satz');
  });
});
