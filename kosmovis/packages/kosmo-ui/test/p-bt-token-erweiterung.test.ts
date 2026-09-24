import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

/**
 * P-BT (Owner-Freigabe 28.07.2026, `docs/KOSMO-UI-FREIGABE-01.md` §2j
 * «Token-Erweiterung · additiv, beide Farbwelten», TOKENS · BLATT 05) —
 * Wächter für die dort tabellierten Tokens: jedes NEUE Token muss in BEIDEN
 * Farbwelten (Papier UND Kosmos) stehen und exakt den in der Freigabe-
 * Tabelle genannten Wert tragen.
 *
 * KORREKTUR P-TT (Owner-Entscheid 28.07.2026, Welle 1): P-BT hatte den
 * abgedunkelten Papier-Ton («eine Stufe dunkler für Kontrast») direkt als
 * Theme-Override auf `--k-signal` umgesetzt — der GEMEINSAMEN Marken-
 * Konstante, nicht auf ein eigenes Token. Der eigene P-BT-Kommentar (s. Git-
 * Historie dieser Datei) hielt schon fest, dass das «ALLE Bestands-
 * Konsumenten … nicht nur die drei in der Freigabe genannten Rollen»
 * betrifft; der Faktencheck zählte 68 Vorkommen in 19 Dateien (Cursor,
 * Feedback-Leisten, Dock, Werkzeug-Glyphen, GPU-Status, Onboarding,
 * Companion, Orb-Kern u.a.). Owner-Entscheid: der dunklere Ton gilt NUR für
 * Kosmo (Antwortblase/Rückgängig/aktiver Ring), die Marke `--k-signal`
 * bleibt themeninvariant. Der erste Test unten prüfte bisher GENAU das
 * überholte Verhalten («--k-signal (paper) === #2e8794») — er wird durch
 * P-TT bewusst gedreht: er beweist jetzt, dass `--k-signal` WIEDER
 * themeninvariant ist (Lehre `wissen/training/claude/lehren/v0.9.3.md` §5:
 * ein Test, der ein überholtes Verhalten festschreibt, ist gefährlicher als
 * ein fehlender). Der abgedunkelte Ton lebt jetzt in `--k-kosmo-stimme`,
 * geprüft im zweiten Test — Name bewusst NICHT `--kosmo-signal` (Freigabe-
 * Wortlaut), weil `kosmo-signal` im Repo bereits das LoRA-Export-Schema
 * `kosmo-signal/v1` heisst (`state/proposal-log.ts`) und ein gleichnamiges
 * CSS-Token beim Lesen/Grep damit verwechselbar wäre; `--k-kosmo-stimme`
 * übernimmt stattdessen die Rollen-Beschreibung der Tabelle wörtlich
 * («Kosmos Stimme»).
 *
 * Muster wie `token-spiegel.test.ts`: aura.css mit Regex parsen statt einen
 * Browser zu starten, block()/lies()-Helfer 1:1 aus jener Datei übernommen
 * (hier bewusst OHNE Abhängigkeit auf `tokens.ts`/`../src/tokens` — dieses
 * Paket bleibt beim Dateikreis `aura.css` + Tests, `tokens.ts` ist nicht
 * Teil dieses Auftrags).
 */

const auraPath = path.resolve(__dirname, '../src/aura.css');
const auraCss = readFileSync(auraPath, 'utf8');

/** Extrahiert den `{ ... }`-Block, dessen öffnende Klammer als erste nach
 * `selectorNeedle` folgt (Klammer-Tiefe wird gezählt). `selectorNeedle` muss
 * VOR der öffnenden Klammer des Zielblocks liegen (nicht schon im Block
 * selbst), sonst greift die nächste `{` im Text, nicht die gewünschte. */
function block(css: string, selectorNeedle: string): string {
  const start = css.indexOf(selectorNeedle);
  if (start === -1) {
    throw new Error(`p-bt-token-erweiterung: Nadel "${selectorNeedle}" nicht in aura.css gefunden — Datei verändert?`);
  }
  const open = css.indexOf('{', start);
  let depth = 0;
  let i = open;
  for (; i < css.length; i++) {
    const zeichen = css.charAt(i);
    if (zeichen === '{') depth++;
    else if (zeichen === '}') {
      depth--;
      if (depth === 0) break;
    }
  }
  return css.slice(open, i + 1);
}

/** Liest `--k-name: WERT;` aus einem Block-Ausschnitt. */
function lies(blockCss: string, varName: string, blockLabel: string): string {
  const m = blockCss.match(new RegExp(`${varName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}:\\s*([^;]+);`));
  const wert = m?.[1];
  if (wert === undefined) {
    throw new Error(`p-bt-token-erweiterung: "${varName}" nicht im Block "${blockLabel}" von aura.css gefunden.`);
  }
  return wert.trim();
}

// Die drei Blöcke, die diese Freigabe-Welle anfasst. Needles sind bewusst
// EINDEUTIGE Textstellen kurz VOR der jeweiligen öffnenden Klammer (nicht
// die Klammer selbst bei paper/invariant, da `[data-theme='paper']` mehrfach
// im Datei-Kopf vorkommt — s. Kommentar der `block()`-Funktion oben).
const paperBlock = block(auraCss, 'muss NACH dem');
const orbitBlock = block(auraCss, "[data-theme='orbit'] {");
const invarianteBlock = block(auraCss, 'die vier theme-invarianten');

describe('P-BT Token-Erweiterung (BLATT 05): jedes neue Token in beiden Farbwelten mit dem freigegebenen Wert', () => {
  it('P-TT-Korrektur — --k-signal ist wieder themeninvariant (KEIN Papier-Override mehr)', () => {
    // Vor P-TT stand hier `--k-signal (paper) === #2e8794` — das schrieb den
    // P-BT-Übergriff auf die Marken-Konstante als Vertrag fest. Der Owner-
    // Entscheid vom 28.07.2026 (Welle 1) hebt genau diesen Override auf: die
    // Marke bleibt in beiden Farbwelten `#57b6c2`, der abgedunkelte Ton
    // gehört jetzt exklusiv `--k-kosmo-stimme` (nächster Test).
    expect(paperBlock, 'paper-Block darf --k-signal nicht mehr überschreiben').not.toMatch(/--k-signal:/);
    expect(orbitBlock, 'orbit-Block überschreibt --k-signal wie zuvor nicht').not.toMatch(/--k-signal:/);
    expect(auraCss).toMatch(/--k-signal:\s*#57b6c2;/); // einzige Deklaration, im gemeinsamen :root-Block
  });

  it('--k-kosmo-stimme (NEU, Freigabe-Rolle «Kosmos Stimme»): Papier eine Stufe dunkler als Kosmos, in beiden Farbwelten deklariert', () => {
    // Kosmos-Wert lebt im gemeinsamen :root-Block (kein eigener orbit-
    // Override nötig — byte-identisch mit der Marke --k-signal, s. dort).
    expect(auraCss).toMatch(/--k-kosmo-stimme:\s*#57b6c2;/);
    expect(orbitBlock, '--k-kosmo-stimme (orbit) bleibt unüberschrieben').not.toMatch(/--k-kosmo-stimme:/);
    // Papier bekommt exakt den Ton, den P-BT zuvor auf --k-signal legte.
    expect(lies(paperBlock, '--k-kosmo-stimme', 'paper'), '--k-kosmo-stimme (paper)').toBe('#2e8794');
    // Bewusst KEIN Alias-Token `--kosmo-signal` (Freigabe-Wortlaut) ANGELEGT
    // — Namenskollision mit dem LoRA-Export-Schema `kosmo-signal/v1`
    // vermieden (der Name selbst darf in Prosa-Kommentaren erklärend
    // auftauchen, s. `aura.css`-Kopfkommentar zu `--k-kosmo-stimme` — nur
    // eine echte Deklaration `--kosmo-signal:` wäre hier ein Fehler).
    expect(auraCss).not.toMatch(/--kosmo-signal:/);
  });

  it('--k-ergebnis-linie: Papier #edeae1, Kosmos weiss 6 %', () => {
    expect(lies(paperBlock, '--k-ergebnis-linie', 'paper'), '--k-ergebnis-linie (paper)').toBe('#edeae1');
    expect(lies(orbitBlock, '--k-ergebnis-linie', 'orbit'), '--k-ergebnis-linie (orbit)').toBe(
      'rgba(255, 255, 255, 0.06)',
    );
  });

  it('--k-ergebnis-ok: Papier #3f9b79, Kosmos #74c2a0', () => {
    expect(lies(paperBlock, '--k-ergebnis-ok', 'paper'), '--k-ergebnis-ok (paper)').toBe('#3f9b79');
    expect(lies(orbitBlock, '--k-ergebnis-ok', 'orbit'), '--k-ergebnis-ok (orbit)').toBe('#74c2a0');
  });

  it('--k-ergebnis-still: Papier #b8b2a4, Kosmos #5c6271', () => {
    expect(lies(paperBlock, '--k-ergebnis-still', 'paper'), '--k-ergebnis-still (paper)').toBe('#b8b2a4');
    expect(lies(orbitBlock, '--k-ergebnis-still', 'orbit'), '--k-ergebnis-still (orbit)').toBe('#5c6271');
  });

  it('--k-risiko-marke: Papier #b25750, Kosmos #cd7670 — Regel «nur Linie und Text, nie Fläche, nie Knopf» steht als Kommentar im Code', () => {
    expect(lies(paperBlock, '--k-risiko-marke', 'paper'), '--k-risiko-marke (paper)').toBe('#b25750');
    expect(lies(orbitBlock, '--k-risiko-marke', 'orbit'), '--k-risiko-marke (orbit)').toBe('#cd7670');
    expect(auraCss).toMatch(/NUR Linie und Text — NIE Fläche, NIE Knopf/);
  });

  it('--k-risiko-schraffur-farbe: Papier 5.5 % / Kosmos 7 % auf --k-risiko-marke, Grösse 6/14px theme-invariant', () => {
    expect(lies(paperBlock, '--k-risiko-schraffur-farbe', 'paper'), '--k-risiko-schraffur-farbe (paper)').toBe(
      'rgba(178, 87, 80, 0.055)',
    );
    expect(lies(orbitBlock, '--k-risiko-schraffur-farbe', 'orbit'), '--k-risiko-schraffur-farbe (orbit)').toBe(
      'rgba(205, 118, 112, 0.07)',
    );
    expect(
      lies(invarianteBlock, '--k-risiko-schraffur-mass', ':root (invariant)'),
      '--k-risiko-schraffur-mass',
    ).toBe('6px 14px');
  });

  it('--k-zone-offen-rahmen: Papier #1a1815, Kosmos weiss 55 %', () => {
    expect(lies(paperBlock, '--k-zone-offen-rahmen', 'paper'), '--k-zone-offen-rahmen (paper)').toBe('#1a1815');
    expect(lies(orbitBlock, '--k-zone-offen-rahmen', 'orbit'), '--k-zone-offen-rahmen (orbit)').toBe(
      'rgba(255, 255, 255, 0.55)',
    );
  });

  it('--k-archiv-band: Papier #f2f0e9, Kosmos weiss 3 %', () => {
    expect(lies(paperBlock, '--k-archiv-band', 'paper'), '--k-archiv-band (paper)').toBe('#f2f0e9');
    expect(lies(orbitBlock, '--k-archiv-band', 'orbit'), '--k-archiv-band (orbit)').toBe('rgba(255, 255, 255, 0.03)');
  });

  it('--k-blase-s/-m/-l (Breite × Höhe): identisch in beiden Farbwelten, alle vier Werte durch 4 teilbar', () => {
    // Je zwei Tokens statt eines Wertpaares: CSS kann `480px 300px` nicht auf
    // width und height verteilen (Orchestrator-Nachzug beim Zusammenfuehren
    // mit dem Blasen-Paket, das die Werte einzeln braucht).
    expect(lies(invarianteBlock, '--k-blase-s-breite', ':root (invariant)')).toBe('480px');
    expect(lies(invarianteBlock, '--k-blase-s-hoehe', ':root (invariant)')).toBe('300px');
    expect(lies(invarianteBlock, '--k-blase-m-breite', ':root (invariant)')).toBe('620px');
    expect(lies(invarianteBlock, '--k-blase-m-hoehe', ':root (invariant)')).toBe('520px');
    expect(lies(invarianteBlock, '--k-blase-l-breite', ':root (invariant)')).toBe('760px');
    expect(lies(invarianteBlock, '--k-blase-l-hoehe', ':root (invariant)')).toBe('880px');
    const stufen: Array<[number, number]> = [
      [480, 300],
      [620, 520],
      [760, 880],
    ];
    for (const [b, h] of stufen) {
      expect(b % 4, `${b} durch 4 teilbar`).toBe(0);
      expect(h % 4, `${h} durch 4 teilbar`).toBe(0);
    }
  });

  it('--k-zeile-h-ergebnis/-archiv: 32px / 36px, identisch in beiden Farbwelten', () => {
    expect(lies(invarianteBlock, '--k-zeile-h-ergebnis', ':root (invariant)'), '--k-zeile-h-ergebnis').toBe('32px');
    expect(lies(invarianteBlock, '--k-zeile-h-archiv', ':root (invariant)'), '--k-zeile-h-archiv').toBe('36px');
  });

  it('--k-mot-schrumpf/-stufe/-zeile: 520ms / 320ms / 240ms, identisch in beiden Farbwelten', () => {
    expect(lies(invarianteBlock, '--k-mot-schrumpf', ':root (invariant)'), '--k-mot-schrumpf').toBe('520ms');
    expect(lies(invarianteBlock, '--k-mot-stufe', ':root (invariant)'), '--k-mot-stufe').toBe('320ms');
    expect(lies(invarianteBlock, '--k-mot-zeile', ':root (invariant)'), '--k-mot-zeile').toBe('240ms');
  });

  it('NICHT NEU EINGEFÜHRT: keine neue Schriftfamilie/Radius/Schattenstufe/zweite Akzentfarbe durch dieses Paket', () => {
    // Alle Radius-/Font-/Schatten-Definitionen der Datei bleiben unverändert
    // an ihrer bestehenden Zeilenzahl-Nachbarschaft — dieser Test bewacht nur
    // die harte Grenze: keine neuen `--k-radius-*`/`--k-font-*`/
    // `--k-shadow-*`/`--k-akzent`-artigen Tokens tauchen NEBEN den P-BT-
    // Blöcken auf.
    expect(invarianteBlock).not.toMatch(/--k-radius/);
    expect(invarianteBlock).not.toMatch(/--k-font/);
    expect(invarianteBlock).not.toMatch(/--k-shadow/);
    expect(paperBlock).not.toMatch(/--k-radius/);
    expect(paperBlock).not.toMatch(/--k-font/);
  });

  it('--kosmo-blase-fill (Freigabe «bestehend»): kein Duplikat angelegt, bestehende Tönungen bleiben unverändert', () => {
    // Papier-Wert der Freigabe-Tabelle (#EAF6F8) ist bereits --k-signal-hell.
    expect(auraCss).toMatch(/--k-signal-hell:\s*#eaf6f8;/);
    // Kosmos-Wert der Freigabe-Tabelle ("teal 10 %") ist bereits --k-signal-fill.
    expect(auraCss).toMatch(/--k-signal-fill:\s*#57b6c21f;/);
    // Kein neues `--kosmo-blase-fill` oder `--k-blase-fill`-Token wurde angelegt.
    expect(auraCss).not.toMatch(/--kosmo-blase-fill/);
    expect(auraCss).not.toMatch(/--k-blase-fill/);
  });
});
