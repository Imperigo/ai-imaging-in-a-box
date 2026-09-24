import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { belichtung } from '../src/bild/belichtung';
import type { Bild } from '../src/bild/farbangleich';

/**
 * B · BEFUND 6 — «vier ungueltige Zahlen bei einem leeren Bild», entschieden.
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * WAS DIESE DATEI IST, UND WAS SIE NICHT IST
 * ═══════════════════════════════════════════════════════════════════════════
 * `test/a16-belichtung.test.ts` hat den IST-ZUSTAND verankert: «bei einem
 * leeren Bild kommt NaN heraus, GEMESSEN und nicht gewuenscht». Das war
 * richtig — eine unbemerkte Reparatur ist schlimmer als ein bekannter Befund.
 *
 * Diese Datei verankert den ENTSCHEID, und das ist etwas anderes: **NaN ist
 * bei null Bildpunkten die richtige Antwort, und null waere falsch.** Ein
 * Prozentsatz ausgebrannter Flaeche bei null Flaeche ist nicht null, er ist
 * nicht bestimmbar; eine Null waere die Behauptung «nichts ist ausgebrannt»
 * ueber ein Bild, in dem nichts brennen koennte. Die Begruendung steht
 * ausfuehrlich an `jeBildpunkt()` in `src/bild/belichtung.ts`.
 *
 * Der Anker von A16 WANDERT damit mit, statt zu verschwinden: er misst
 * weiterhin dieselben vier Zahlen, und er bleibt gruen. Neu ist, dass daneben
 * eine Probe steht, die sagt WARUM sie so sind — und die rot wird, wenn
 * jemand sie «repariert».
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * ROT VOR GRUEN — nachgestellt, nicht behauptet (17.09.2026)
 * ═══════════════════════════════════════════════════════════════════════════
 * Verfaelschung 1 — `if (n <= 0) return Number.NaN;` zu `return 0;`.
 * Gemessen: **3 von 7** Faellen dieser Datei rot («die vier … sind NaN»,
 * «NaN heisst NICHT null», «der Entscheid steht als Zeile im Code»), dazu der
 * Anker von A16 («ein leeres Bild: der Bericht darf keine Zahl liefern, die
 * niemand lesen kann»). Vier Faelle blieben gruen — auch das gehoert dazu:
 * eine Datei, die bei JEDER Aenderung komplett rot wird, sagt nicht, WAS
 * kaputt ist.
 *
 * Verfaelschung 2 — `if (n <= 0)` zu `if (n < 0)`. Die Null faellt dann
 * wieder in die Rechnung und ergibt NaN wie zuvor, also WERTgleich. Gemessen:
 * **1 von 7** rot, und zwar genau «der Entscheid steht als Zeile im Code».
 * Das ist der Fall, der den Unterschied zwischen entschieden und
 * uebriggeblieben ueberhaupt sehen kann; ohne ihn waere der Entscheid nur
 * nacherzaehlt (Muster 3).
 *
 * Beide Male zurueckgenommen, `sha256sum` der Quelldatei vorher wie nachher
 * `a48ffc6e31a3c87828f198f5fce48eee4805d81222e4b44df89f6fa618744637`.
 */

const KNIE = { schutzUnten: 0.66, schutzOben: 0.92 } as const;

/** Ein Bild ohne einen einzigen Bildpunkt. */
const leeresBild = (): Bild => ({ daten: new Uint8Array(0), breite: 0, hoehe: 0, kanaele: 3 });

/** Ein Bild mit genau EINEM Bildpunkt — die kleinste nicht-leere Gegenprobe. */
const einPunkt = (): Bild => ({ daten: new Uint8Array([200, 100, 50]), breite: 1, hoehe: 1, kanaele: 3 });

describe('B · Befund 6 — bei null Bildpunkten ist «nicht bestimmbar» die Antwort', () => {
  it('die vier direkt geteilten Kennzahlen sind NaN — jede einzeln benannt', () => {
    const { bericht } = belichtung(leeresBild(), { hebung: 1.08, ...KNIE });
    // Einzeln und nicht als Schleife: faellt eine davon auf 0, soll der Name
    // im Fehlertext stehen und nicht «eine von vier».
    expect(bericht.ausgebranntVorherProzent, 'ausgebranntVorherProzent').toBeNaN();
    expect(bericht.ausgebranntNachherProzent, 'ausgebranntNachherProzent').toBeNaN();
    expect(bericht.saettigungVorher, 'saettigungVorher').toBeNaN();
    expect(bericht.saettigungNachher, 'saettigungNachher').toBeNaN();
  });

  it('NaN heisst NICHT null — die Verwechslung, gegen die dieser Entscheid steht', () => {
    const { bericht } = belichtung(leeresBild(), { hebung: 1.08, ...KNIE });
    // `expect(NaN).not.toBe(0)` allein waere zu schwach: auch `undefined`
    // bestuende sie. Geprueft wird darum beides — es ist eine Zahl, UND sie
    // ist nicht null.
    for (const [name, wert] of [
      ['ausgebranntVorherProzent', bericht.ausgebranntVorherProzent],
      ['ausgebranntNachherProzent', bericht.ausgebranntNachherProzent],
      ['saettigungVorher', bericht.saettigungVorher],
      ['saettigungNachher', bericht.saettigungNachher],
    ] as const) {
      expect(typeof wert, name).toBe('number');
      expect(wert === 0, `${name} steht auf 0 — das ist eine Behauptung, keine Messung`).toBe(false);
    }
  });

  it('DIE GEGENPROBE: bei EINEM Bildpunkt sind dieselben vier Zahlen echte Zahlen', () => {
    // Ohne sie waere die Probe oben stumpf: eine Fassung, die IMMER NaN
    // liefert, bestuende sie ebenfalls. Muster 3 der Anleitung.
    const { bericht } = belichtung(einPunkt(), { hebung: 1.08, ...KNIE });
    expect(bericht.ausgebranntVorherProzent).toBe(0);
    expect(bericht.ausgebranntNachherProzent).toBe(0);
    expect(Number.isFinite(bericht.saettigungVorher)).toBe(true);
    expect(Number.isFinite(bericht.saettigungNachher)).toBe(true);
    // Und die Saettigung eines Punktes 200/100/50 ist (200−50)/200 = 0.75,
    // in float32 gerechnet. Eine Zahl, die aus der Rechnung folgt und nicht
    // aus dem Modul geholt ist.
    expect(bericht.saettigungVorher).toBeCloseTo(0.75, 6);
  });

  it('der Entscheid steht als Zeile im Code, nicht nur in einem Kommentar', () => {
    // WARUM PER DATEILESUNG: `(0/0)*100` ergibt von selbst NaN. Eine Probe
    // auf den WERT allein kann darum nicht unterscheiden, ob NaN entschieden
    // oder nur uebriggeblieben ist — und genau das ist der ganze Befund 6.
    // Diese Probe prueft, dass die Entscheidung als ausdrueckliche Verzweigung
    // im Quelltext steht. Faellt sie weg, ist der Befund wieder offen.
    //
    // (Gelesen und nicht importiert, aus demselben Grund wie in
    // `a16-belichtung.test.ts`: `import('../src/index')` im Testrumpf kostet
    // gemessen 3.3 s und sprengt das 5-Sekunden-Fenster — s.
    // `test/b-kalter-fasslauf.test.ts`. Hier reicht ohnehin die Datei selbst.)
    const quelle = readFileSync(
      fileURLToPath(new URL('../src/bild/belichtung.ts', import.meta.url)),
      'utf8',
    );
    expect(quelle).toContain('function jeBildpunkt(');
    expect(quelle).toContain('if (n <= 0) return Number.NaN;');
    // Und die vier Kennzahlen gehen wirklich durch diese Stelle — sonst waere
    // die Funktion da und niemand riefe sie (Muster 15, «der Lauf, der kein
    // Ergebnis ist»).
    for (const feld of [
      'ausgebranntVorherProzent: jeBildpunkt(',
      'ausgebranntNachherProzent: jeBildpunkt(',
      'saettigungVorher: jeBildpunkt(',
      'saettigungNachher: jeBildpunkt(',
    ]) {
      expect(quelle, `${feld} laeuft nicht mehr ueber jeBildpunkt()`).toContain(feld);
    }
  });

  it('OFFEN UND GEMELDET: die drei Flaechenmasse fangen dieselbe Null ab und behaupten 0', () => {
    // Das ist kein gruener Haken, sondern ein festgehaltener Widerspruch:
    // nach derselben Logik sind auch `anteilProzent`, `vorher` und `nachher`
    // bei null Bildpunkten nicht bestimmbar. `Teilflaeche.mass()` faengt die
    // Null mit `Math.max(gesamt, 1)` bzw. `this.punkte || 1` ab.
    //
    // NICHT MITREPARIERT, weil es ein zweiter Entscheid mit eigener Messung
    // ist und weil sein Anker in `test/a16-belichtung.test.ts:955` liegt —
    // einer fremden Datei. Diese Probe haelt den Ist-Zustand fest, damit die
    // Aenderung, wenn sie kommt, bewusst geschieht und hier sichtbar wird.
    const { bericht } = belichtung(leeresBild(), { hebung: 1.08, ...KNIE });
    expect(bericht.vollGehoben.anteilProzent).toBe(0);
    expect(bericht.vollGehoben.vorher).toBe(0);
    expect(bericht.vollGehoben.nachher).toBe(0);
    expect(bericht.teilweise.anteilProzent).toBe(0);
    expect(bericht.unangetastet.anteilProzent).toBe(0);
  });

  it('der Rest des Berichts bleibt bei einem leeren Bild brauchbar', () => {
    // Damit niemand «dann wirf halt» als billige Loesung nimmt, ohne zu
    // wissen, was er wegwirft: Kennlinie, Grenze und Zusage stehen auch hier.
    const { bild, bericht } = belichtung(leeresBild(), { hebung: 1.08, ...KNIE });
    expect(bild.daten.length).toBe(0);
    expect(bericht.bild).toEqual([0, 0]);
    expect(bericht.kennlinie).toHaveLength(256);
    expect(bericht.hoechsterAusgabewert).toBe(1);
    expect(bericht.hebungAngewendet).toBe(1.08);
    expect(bericht.geklemmt).toBe(false);
  });

  it('DER EMPFAENGER, gemessen: genau ein Aufrufer, und der laesst kein leeres Bild durch', () => {
    // Muster 15 der Anleitung, Frage 7: «Wer ist der Empfaenger?» Der
    // Entscheid oben steht und faellt damit, ob die Oberflaeche ein leeres
    // Bild ueberhaupt herunterreichen kann. Gemessen statt geglaubt — und
    // hier festgehalten, damit ein zweiter Aufrufer nicht still dazukommt.
    const app = readFileSync(
      fileURLToPath(new URL('../../../apps/kosmo-orbit/src/modules/vis/bild-rechnen.ts', import.meta.url)),
      'utf8',
    );
    expect(app).toContain('belichtung(await bildpunkteAus(url)');
    expect(app).toContain("throw new Error('Das Bild hat keine messbare Grösse.')");
    expect(app).toContain('if (!(breite > 0) || !(hoehe > 0))');
  });
});
