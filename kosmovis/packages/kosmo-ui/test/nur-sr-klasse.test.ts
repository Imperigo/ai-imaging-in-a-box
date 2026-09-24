import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/**
 * **`.k-nur-sr` — Text, den nur die Sprachausgabe bekommt.**
 *
 * Der Befund: `KAnsageBereich` (08.09.2026) brauchte diese Klasse und hat
 * sie NICHT gebaut, sondern das Muster als Inline-Stil dupliziert. Der
 * Kommentar daneben nannte den Grund und meldete den Posten ausdruecklich —
 * `aura.css` lag damals ausserhalb des Dateikreises. Der Kreis ist offen,
 * die Klasse steht, die Verdopplung ist weg.
 *
 * **Warum diese Probe scharf sein muss.** Eine Klasse, die «Text verstecken»
 * heisst, wird frueher oder spaeter von jemandem zu `display: none`
 * «vereinfacht» — das ist die naheliegende, kuerzere, und **falsche** Form:
 * sie nimmt den Text auch der Sprachausgabe weg und schaltet damit genau
 * das ab, wofuer die Klasse da ist. Der Fehler waere unsichtbar: am
 * Bildschirm sieht beides gleich aus, und keine Zahl faellt.
 */

const HIER = dirname(fileURLToPath(import.meta.url));
const AURA = readFileSync(resolve(HIER, '../src/aura.css'), 'utf8');

/** Blockkommentare weg (CSS und TSX teilen die Syntax). */
function ohneKommentare(text: string): string {
  return text.replace(/\/\*[\s\S]*?\*\//g, '');
}
/* Kommentare weg — ZUM VIERTEN MAL in diesem Repo hat ein erklaerender Text
   seinen eigenen Test gebrochen: der Kommentar in `meldungen.tsx` zitiert
   das entfernte `VERBORGEN_STYLE` woertlich, um zu erklaeren, was dort
   frueher stand. Ohne diese Zeile faellt die Probe darauf herein und meldet
   eine Verdopplung, die es nicht mehr gibt. */
const MELDUNGEN = ohneKommentare(readFileSync(resolve(HIER, '../src/meldungen.tsx'), 'utf8'));

function regelBlock(css: string, selektor: string): string {
  const i = css.indexOf(`${selektor} {`);
  expect(i, `Selektor ${selektor} nicht gefunden`).toBeGreaterThanOrEqual(0);
  const start = css.indexOf('{', i) + 1;
  return css.slice(start, css.indexOf('}', start));
}

const CSS = ohneKommentare(AURA);

describe('.k-nur-sr — das Clip-Muster, und ausdruecklich NICHT display:none', () => {
  const regel = () => regelBlock(CSS, '.k-nur-sr');

  it('KONTROLLFALL: die Datei wird ueberhaupt richtig gelesen — bleibt in BEIDEN Laeufen gruen', () => {
    // Ohne ihn bewiese ein roter Lauf gegen die alte Fassung nur, dass die
    // Probe irgendetwas nicht findet — nicht, dass sie das Richtige sucht.
    // `.k-meldungen-host` steht seit Langem da und ist von diesem Paket
    // unberuehrt.
    expect(CSS).toContain('.k-meldungen-host {');
    expect(MELDUNGEN).toContain('export function KAnsageBereich()');
  });

  it('die Klasse existiert ueberhaupt', () => {
    expect(CSS).toContain('.k-nur-sr {');
  });

  it('sie versteckt per Clip: aus dem Fluss, auf 1px geklemmt, ueberlauf abgeschnitten', () => {
    const r = regel();
    expect(r).toMatch(/position\s*:\s*absolute\s*;/);
    expect(r).toMatch(/width\s*:\s*1px\s*;/);
    expect(r).toMatch(/height\s*:\s*1px\s*;/);
    expect(r).toMatch(/overflow\s*:\s*hidden\s*;/);
    expect(r).toMatch(/clip\s*:\s*rect\(/);
  });

  it('FALSIFIZIERBAR: KEIN display:none und KEIN visibility:hidden — beide nehmen der Sprachausgabe den Text weg', () => {
    // Der eigentliche Kern. Ohne diesen Fall waere auch eine Fassung gruen,
    // die zusaetzlich `display: none` setzt — und die waere fuer eine blinde
    // Nutzerin vollstaendig wirkungslos, ohne dass es irgendwo auffiele.
    const r = regel();
    expect(r, 'display:none nimmt den Text auch der Hilfstechnik').not.toMatch(/display\s*:\s*none/);
    expect(r, 'visibility:hidden nimmt den Text auch der Hilfstechnik').not.toMatch(/visibility\s*:\s*hidden/);
    expect(r, 'opacity:0 laesst die Box stehen und faengt Klicks').not.toMatch(/opacity\s*:\s*0/);
  });

  it('die Randstellen sind mitgedacht — Umbruch und Rahmen wuerden die geklemmte Box sonst aufziehen', () => {
    const r = regel();
    expect(r).toMatch(/white-space\s*:\s*nowrap\s*;/);
    expect(r).toMatch(/border\s*:\s*0\s*;/);
    expect(r).toMatch(/margin\s*:\s*-1px\s*;/);
  });

  it('der Ansage-Bereich BENUTZT die Klasse — und traegt das Muster nicht mehr doppelt', () => {
    // Zwei Kopien laufen auseinander: die zweite wird «vereinfacht», und
    // dann versteckt eine Stelle richtig und die andere falsch.
    expect(MELDUNGEN).toMatch(/className="k-nur-sr" data-testid="ansage-polite"/);
    expect(MELDUNGEN).toMatch(/className="k-nur-sr" data-testid="ansage-assertive"/);
    expect(MELDUNGEN, 'das Inline-Muster steht noch da').not.toMatch(/VERBORGEN_STYLE/);
    expect(MELDUNGEN, 'ein zweites Clip-Muster in derselben Datei').not.toMatch(/clip:\s*'rect\(/);
  });
});
