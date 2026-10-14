import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { RADIUS_ABGELOEST, radius, radiusR } from '../src/tokens';
import { auraCss as liesAuraCss, quelldateien as leiterQuelldateien, repoWurzel, zaehle } from './leiter-bestand';

/**
 * FORM-FAMILIE-WÄCHTER — Owner-Entscheid 21.09.2026.
 *
 * Der Auftrag im Wortlaut: «ich moechte das alles also jeder knopf jede
 * insel, jeder tab was auch immer alles immer den gleichen kreisradius
 * aufweist … und die insel sind z.b einfach zwei selbe halbkreise mit einer
 * pille also rechteck drin als verlaengerung das es zur pille wird».
 *
 * Das ist keine neue Regel neben `docs/kosmodata-neugestaltung/UI-REGELN.md`,
 * sondern deren Regel 4 («Kreis-Knöpfe als Grundform der Werkzeuge») zu Ende
 * gedacht: ein Kreis erzeugt die ganze Form-Familie.
 *
 *   - Bedienelemente (Knopf, Tab, Insel, Chip, Feld, Schalter) sind
 *     VOLLRUND — `--k-radius-pill`. Bei einem quadratischen Element ergibt
 *     das einen Kreis, bei einer Leiste eine Pille.
 *   - Flächen (Popup, Dialog, Karte, Panel, Tafel) tragen EINE Rundung R —
 *     `--k-radius` = 16px.
 *   - Der Zusammenhang ist der Punkt: ein Bedienelement von 2·R = 32px Höhe
 *     ist unter «vollrund» und unter R dieselbe Geometrie.
 *
 * Dieser Wächter verhindert den Rückfall: eine ROHE `border-radius`-Angabe
 * in `packages/kosmo-ui` fällt auf. Eine rohe Zahl ist genau der Weg, auf dem
 * die acht Radius-Werte entstanden sind, die der Owner eingezogen hat.
 */

const srcDir = path.resolve(__dirname, '../src');
const auraCss = readFileSync(path.join(srcDir, 'aura.css'), 'utf8');

/**
 * ALLE Blockausschnitte zu einem Selektor. Bewusst alle und nicht der erste:
 * `.k-switch-daumen` steht zweimal in aura.css (einmal nur mit
 * `pointer-events`, einmal mit der Form) — ein Wächter, der nur den ersten
 * Treffer liest, meldet dort einen Fehler, den es nicht gibt.
 */
function bloecke(css: string, selektor: string): string[] {
  const treffer: string[] = [];
  const nadel = `\n${selektor} {`;
  let ab = 0;
  for (;;) {
    const start = css.indexOf(nadel, ab);
    if (start === -1) break;
    const open = css.indexOf('{', start);
    const close = css.indexOf('}', open);
    treffer.push(css.slice(open, close + 1));
    ab = close + 1;
  }
  if (treffer.length === 0) {
    throw new Error(`form-familie: Selektor "${selektor}" nicht in aura.css gefunden — umbenannt/verschoben?`);
  }
  return treffer;
}

/**
 * BENANNTE AUSNAHMEN — jede mit Begründung, keine ohne.
 *
 * Wer hier etwas einträgt, nimmt der Form-Familie eine Stelle weg; das soll
 * beim Lesen wehtun. Datei + Zeilentext müssen exakt stimmen, damit eine
 * verschobene Ausnahme auffällt statt still weiterzugelten.
 */
const AUSNAHMEN: ReadonlyArray<{ datei: string; zeile: string; grund: string }> = [];

/**
 * Alle Quelldateien BEIDER Geltungswurzeln (CSS + TS/TSX), rekursiv.
 *
 * **AM 21.09.2026 ERWEITERT, und die Erweiterung war der eigentliche Fund.**
 * Vorher las diese Zusage nur die oberste Ebene von `packages/kosmo-ui/src` —
 * die Bibliothek also, nicht das Produkt. Sie meldete jahrelang grün,
 * während im App-Baum 32 rohe Rundungen standen (6px, 4px, 2px, 10px). Eine
 * Wache, die den halben Geltungsbereich liest, ist keine halbe Wache,
 * sondern eine, die die falsche Frage stellt.
 *
 * Der Geltungsbereich ist jetzt derselbe wie bei den drei Leiter-Wächtern
 * (`leiter-bestand.ts`): `apps/kosmo-orbit/src` UND `packages/kosmo-ui/src`.
 */
function alleQuellen(): { datei: string; inhalt: string }[] {
  return leiterQuelldateien(['.css', '.ts', '.tsx']).map((abs) => ({
    datei: path.relative(repoWurzel, abs).split(path.sep).join('/'),
    inhalt: readFileSync(abs, 'utf8'),
  }));
}

/** Zeilen mit einer Rundungs-Angabe, die KEIN Radius-Token benutzt. */
function roheRundungen(): Array<{ datei: string; nr: number; zeile: string }> {
  const treffer: Array<{ datei: string; nr: number; zeile: string }> = [];
  for (const { datei, inhalt } of alleQuellen()) {
    const zeilen = inhalt.split('\n');
    zeilen.forEach((roh, i) => {
      const zeile = roh.trim();
      // Kommentarzeilen zählen nicht — sie erzeugen keine Form.
      if (zeile.startsWith('*') || zeile.startsWith('//') || zeile.startsWith('/*')) return;
      if (!/(^|[^-\w])(border(-[a-z]+)*-radius|borderRadius)\s*:/.test(zeile)) return;
      if (zeile.includes('var(--k-radius')) return;
      // NULL IST KEINE RUNDUNG, sondern deren Abwesenheit — eine
      // Formentscheidung, kein Zwischenwert. Die scharfe Sprech-Ecke der
      // Chatblasen ist genau das (s. `kosmo-panel.css`), und die
      // Tusche-Karte mit ihrem Eckschnitt ebenso. Beide standen vorher als
      // benannte Ausnahme hier; eine Regel ist besser als eine Liste.
      if (/(?:border(?:-[a-z]+)*-radius|borderRadius)\s*:\s*['"`]?0(?:px)?['"`]?\s*[;,]?$/.test(zeile)) return;
      // Ein echter Kreis (`50%`) meint dasselbe wie die Pille und ist keine
      // dritte Rundung — er ist die Form, die der Owner verlangt hat.
      if (/(?:border(?:-[a-z]+)*-radius|borderRadius)\s*:\s*['"`]?50%/.test(zeile)) return;
      treffer.push({ datei, nr: i + 1, zeile });
    });
  }
  return treffer;
}

describe('Form-Familie (Owner 21.09.2026): ein Kreis erzeugt die ganze Form-Familie', () => {
  it('kein roher border-radius im ganzen Haus — ausser den benannten Ausnahmen', () => {
    const offen = roheRundungen().filter(
      (t) => !AUSNAHMEN.some((a) => a.datei === t.datei && a.zeile === t.zeile),
    );
    const meldung = offen
      .map(
        (t) =>
          `  ${t.datei}:${t.nr}  ${t.zeile}\n` +
          '      → Flächen nehmen var(--k-radius), Bedienelemente var(--k-radius-pill).',
      )
      .join('\n');
    expect(
      offen,
      offen.length
        ? `Rohe Rundung(en) gefunden — die Form-Familie kennt nur zwei Werte:\n${meldung}\n` +
            'Ist die Stelle wirklich eine Ausnahme, gehört sie MIT BEGRÜNDUNG in AUSNAHMEN ' +
            'in dieser Datei, nicht roh in die Quelle.'
        : '',
    ).toEqual([]);
  });

  it('jede benannte Ausnahme existiert noch — eine verwaiste Ausnahme wird entfernt, nicht vergessen', () => {
    const treffer = roheRundungen();
    for (const a of AUSNAHMEN) {
      expect(
        treffer.some((t) => t.datei === a.datei && t.zeile === a.zeile),
        `Ausnahme "${a.datei}: ${a.zeile}" trifft nichts mehr — aus AUSNAHMEN streichen. Grund war: ${a.grund}`,
      ).toBe(true);
    }
  });

  it('zwei Token tragen die ganze Rundung: --k-radius = 16px, --k-radius-pill = 999px', () => {
    expect(auraCss, '--k-radius (R, die eine Flächenrundung)').toMatch(/--k-radius:\s*16px;/);
    expect(auraCss, '--k-radius-pill (Vollrundung der Bedienelemente)').toMatch(/--k-radius-pill:\s*999px;/);
  });

  it('R ist die halbe Regelhöhe: 2·R = 32px = Höhe des Werkzeug-Kreises', () => {
    const kreis = bloecke(auraCss, '.k-werkzeug-kreis').join('\n');
    expect(kreis, '.k-werkzeug-kreis width').toMatch(/width:\s*32px;/);
    expect(kreis, '.k-werkzeug-kreis height').toMatch(/height:\s*32px;/);
    expect(2 * Number.parseInt(radiusR, 10), '2·R vs. Regelhöhe 32px').toBe(32);
  });

  it('die abgelösten Radius-Namen sind Verweise auf --k-radius, nicht eigene Werte', () => {
    for (const { name } of RADIUS_ABGELOEST) {
      expect(auraCss, `${name} muss auf var(--k-radius) verweisen (abgelöst 21.09.2026)`).toMatch(
        new RegExp(`${name}:\\s*var\\(--k-radius\\);`),
      );
    }
  });

  it('tokens.ts spiegelt den Einzug: sm/md/lg tragen alle R', () => {
    expect(radiusR, 'radiusR').toBe('16px');
    expect(radius.sm, 'radius.sm').toBe(radiusR);
    expect(radius.md, 'radius.md').toBe(radiusR);
    expect(radius.lg, 'radius.lg').toBe(radiusR);
    expect(radius.pill, 'radius.pill').toBe('999px');
  });

  it('jedes Bedienelement des Gestaltungssystems ist vollrund', () => {
    // Knopf, Feld, Auswahl, Kommandofeld, Chip, Kästchen, Karten-Aktion,
    // Tab-Leiste und Tab, Pille, Werkzeug-Kreis, Schalter.
    const bedienelemente = [
      '.k-btn',
      '.k-input',
      '.k-select',
      '.k-input-wrap--command',
      '.k-chip',
      '.k-checkbox-box',
      '.k-variantenkarte-aktion',
      '.k-tabs',
      '.k-tab',
      '.k-pill',
      '.k-status-chip',
      '.k-chip-geschlossen',
      '.k-werkzeug-kreis',
      '.k-switch-strecke',
      '.k-switch-daumen',
    ];
    for (const sel of bedienelemente) {
      const alle = bloecke(auraCss, sel);
      expect(
        alle.some((b) => /border-radius:\s*var\(--k-radius-pill\);/.test(b)),
        `${sel} muss var(--k-radius-pill) tragen (Form-Familie)`,
      ).toBe(true);
      // und keine Regel desselben Selektors darf die Vollrundung zurücknehmen
      const zurueck = alle.filter((b) => /border-radius:/.test(b) && !/var\(--k-radius-pill\)/.test(b));
      expect(zurueck, `${sel} nimmt die Vollrundung an anderer Stelle wieder zurück`).toEqual([]);
    }
  });
});

/**
 * ══ ABGELÖST-WACHE — Form-Entscheid 1a, Owner 21.09.2026 ══════════════════
 *
 * Der Einzug der sieben Namen auf eine Rundung ist gebaut; die 157
 * Aufrufstellen zieht ein eigenes Paket nach. Bis dahin ist der gefährliche
 * Zustand nicht der Bestand, sondern das WACHSTUM: ein abgelöster Name, der
 * an einer NEUEN Stelle auftaucht, verlängert die Umstellung, ohne dass es
 * jemandem auffällt — genau der Weg, auf dem die sieben Namen überhaupt
 * entstanden sind.
 *
 * Diese Wache hält darum zwei Zusagen:
 *   1. Jeder abgelöste Name trägt in `aura.css` die Marke `ABGELOEST` —
 *      maschinenlesbar, nicht als Prosa. Ein Name ohne Marke gilt als
 *      lebendig, und das soll auffallen.
 *   2. Der Bestand je Name WÄCHST NICHT. Er darf fallen (dann hat das
 *      Umstellungs-Paket gearbeitet) — dann meldet die Wache, um wie viel,
 *      damit die Zahl in `tokens.ts` nachgezogen wird statt zu verrotten.
 */
describe('Abgelöst-Wache: die alten Rundungsnamen sind Bestandsschutz, kein Angebot', () => {
  const aura = liesAuraCss();

  it('jeder abgelöste Name trägt die Marke ABGELOEST in aura.css', () => {
    for (const { name, war } of RADIUS_ABGELOEST) {
      const zeile = aura.split('\n').find((z) => z.trimStart().startsWith(`${name}:`));
      expect(zeile, `${name} steht nicht mehr in aura.css`).toBeDefined();
      expect(
        zeile,
        `${name} (war ${war}) ist abgelöst, trägt die Marke aber nicht. ` +
          'Ohne `ABGELOEST` in der Zeile liest die Wache ihn als lebendigen Namen — ' +
          'und dann darf er wieder neu verbaut werden.',
      ).toMatch(/ABGELOEST/);
    }
  });

  it('kein abgelöster Name ist lebendig geblieben: --k-radius und --k-radius-pill tragen KEINE Marke', () => {
    for (const lebend of ['--k-radius', '--k-radius-pill']) {
      const zeile = aura.split('\n').find((z) => z.trimStart().startsWith(`${lebend}:`));
      expect(zeile, `${lebend} steht nicht in aura.css`).toBeDefined();
      expect(zeile, `${lebend} ist einer der zwei lebendigen Namen und darf nicht als abgelöst markiert sein`).not.toMatch(
        /ABGELOEST/,
      );
    }
  });

  it('--k-radius-hub ist eingezogen — null Verbraucher, also kein Bestand zu schützen', () => {
    expect(aura.split('\n').some((z) => z.trimStart().startsWith('--k-radius-hub:')), '--k-radius-hub lebt wieder').toBe(
      false,
    );
    const { anzahl, stellen } = zaehle(/var\(--k-radius-hub(?![-a-zA-Z0-9])/);
    expect(
      anzahl,
      anzahl
        ? `--k-radius-hub wurde am 21.09.2026 eingezogen (0 Verbraucher, gemessen), hat aber wieder welche:\n` +
            stellen.map((s) => `  ${s.datei}:${s.zeile}  ${s.text}`).join('\n')
        : '',
    ).toBe(0);
  });

  it('der Bestand je abgelöstem Namen wächst nicht', () => {
    const abweichungen: string[] = [];
    for (const { name, bestand } of RADIUS_ABGELOEST) {
      const { anzahl, stellen } = zaehle(new RegExp(`var\\(${name}(?![-a-zA-Z0-9])`));
      if (anzahl > bestand) {
        const neu = stellen.slice(-(anzahl - bestand)).map((s) => `      ${s.datei}:${s.zeile}  ${s.text}`);
        abweichungen.push(
          `  ${name}: ${bestand} gehalten, ${anzahl} gefunden — ${anzahl - bestand} NEU.\n` +
            `${neu.join('\n')}\n` +
            '      → Dieser Name ist abgelöst. Flächen nehmen var(--k-radius), Bedienelemente var(--k-radius-pill).',
        );
      } else if (anzahl < bestand) {
        abweichungen.push(
          `  ${name}: ${bestand} gehalten, nur noch ${anzahl} gefunden — das Umstellungs-Paket hat gearbeitet.\n` +
            `      → Bestandszahl in tokens.ts (RADIUS_ABGELOEST) auf ${anzahl} nachziehen; ` +
            'eine veraltete Zahl ist eine Wache, die nicht mehr wacht.',
        );
      }
    }
    expect(abweichungen, abweichungen.length ? `Abgelöster Rundungsname bewegt sich:\n${abweichungen.join('\n')}` : '').toEqual(
      [],
    );
  });
});
