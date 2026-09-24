import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/**
 * **B123 — eine abgelaufene Meldung schloss das Fenster, das der Nutzer
 * gerade vergroessern wollte.**
 *
 * Befund des lokalen Workers (09.09.2026, am Geraet mit `elementFromPoint`
 * auf dem Knopfmittelpunkt gemessen, nicht aus einem Testartefakt
 * geschlossen): eine Meldung verschwindet nicht sofort, wenn ihre Zeit
 * ablaeuft — sie lebt 320 ms als Geist weiter (`meldungen.tsx`, `EXIT_MS`).
 * Die Geisterkarte war schon klickdurchlaessig (`.k-meldung--aus`), **ihr
 * Wirt aber nicht**, und der liegt bei `bottom: 160px` genau ueber der
 * unteren Insel. Ein Klick auf den Vergroessern-Knopf traf in diesem Fenster
 * den Wirt, zaehlte als Aussenklick — und das Fenster schloss sich.
 *
 * **Was diese Probe kann und was nicht.** Sie liest die AUSGELIEFERTE Regel
 * und haelt die drei Aussagen fest, aus denen die Reparatur besteht. Sie
 * kann NICHT belegen, dass `elementFromPoint` waehrend des Ausblendens
 * niemals den Wirt liefert — das verlangt einen echten Bildschirm und steht
 * im Blatt als offener Posten. Was sie verhindert, ist die Rueckkehr der
 * URSACHE: dass der Wirt wieder Klicks faengt.
 */

const HIER = dirname(fileURLToPath(import.meta.url));
const AURA = readFileSync(resolve(HIER, '../src/aura.css'), 'utf8');

/** Kommentare weg — sonst zaehlt die Begruendung, die den Wert nennt, als
 *  Regelwert. Dieselbe Vorsicht wie in `cursor-ebene-compositing.test.tsx`;
 *  in diesem Repo ist sie schon dreimal zugeschlagen. */
function ohneKommentare(css: string): string {
  return css.replace(/\/\*[\s\S]*?\*\//g, '');
}

function regelBlock(css: string, selektor: string): string {
  const i = css.indexOf(`${selektor} {`);
  expect(i, `Selektor ${selektor} nicht gefunden`).toBeGreaterThanOrEqual(0);
  const start = css.indexOf('{', i) + 1;
  return css.slice(start, css.indexOf('}', start));
}

const CSS = ohneKommentare(AURA);

describe('B123 — der Meldungs-Wirt faengt keine Klicks mehr', () => {
  it('`.k-meldungen-host` ist klickdurchlaessig — die Ursache des Befunds', () => {
    expect(regelBlock(CSS, '.k-meldungen-host')).toMatch(/pointer-events\s*:\s*none\s*;/);
  });

  it('die LEBENDE Karte holt sich den Zeiger zurueck — sonst waere der Schliessen-Knopf tot', () => {
    // Der Gegenfall. Ohne ihn waere auch eine Fassung gruen, die den ganzen
    // Meldungsbereich unbedienbar macht — und die haette einen Fehler durch
    // einen groesseren ersetzt.
    expect(regelBlock(CSS, '.k-meldung-karte')).toMatch(/pointer-events\s*:\s*auto\s*;/);
  });

  it('der GEIST holt ihn sich NICHT zurueck — er ist auf dem Weg hinaus', () => {
    expect(regelBlock(CSS, '.k-meldung-geist')).not.toMatch(/pointer-events\s*:\s*auto/);
    // Und seine eigene Abschaltung steht weiterhin da, unabhaengig vom Wirt.
    expect(regelBlock(CSS, '.k-meldung--aus')).toMatch(/pointer-events\s*:\s*none\s*;/);
  });

  it('der Stapel-Hinweis bleibt durchlaessig — reiner Text ohne Bedienelement', () => {
    expect(regelBlock(CSS, '.k-meldung-stapel-hinweis')).not.toMatch(/pointer-events\s*:\s*auto/);
  });

  it('die Geisterzeit ist unveraendert 320 ms — die Reparatur kuerzt das Fenster NICHT weg', () => {
    // Eine Reparatur, die einfach `EXIT_MS` verkleinert, macht das Fenster
    // kleiner statt es zu schliessen — der Fehler bliebe, nur seltener. Diese
    // Probe haelt fest, dass wir ihn nicht auf diese Weise «behoben» haben.
    const meldungen = readFileSync(resolve(HIER, '../src/meldungen.tsx'), 'utf8');
    expect(meldungen).toMatch(/const EXIT_MS = 320;/);
  });
});
