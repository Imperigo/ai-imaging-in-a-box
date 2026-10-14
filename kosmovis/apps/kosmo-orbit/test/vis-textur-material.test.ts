import { describe, expect, it } from 'vitest';
import { REZEPT_KLASSEN, materialTextur } from '@kosmo/kernel';
import { texturMaterialOptionen } from '../src/modules/vis/textur-material';

/**
 * Abnahmezeile 6 — «Textur-Knopf» (P16, Welle 2, `docs/V016-SPEZ.md`
 * Zeile 246: «Vis-Haelfte I: Textur-Knopf (Zeile 6) … Bildkarten aus
 * `derive/textur.ts` bedienbar machen»).
 *
 * WOHER DER ZURUF KOMMT: «bitte entweder hochaufloesende texturen im
 * interner gratis finden mit allen maps oder selber generieren und maps
 * hinzufuegen» (Abnahmeliste Nr. 6). Der Kern kann seit `derive/textur.ts`
 * generieren — es fehlte nur der Bedienweg (P60-Nachmessung 23.09.2026,
 * `docs/RENDERPROJEKT-2026-09-10/60-ABNAHMELISTE.md` Zeile 526: «kein
 * Bedienelement»).
 *
 * WAS DIESE PROBE PRUEFT — nicht das Rechnen selbst (das hat
 * `derive/textur.ts` mit eigenen Proben), sondern die AUSWAHL, die der Knopf
 * anbietet: nur Materialien mit einem ECHTEN Rezept (Regel 5,
 * `docs/kosmodata-neugestaltung/UI-REGELN.md`: Ehrlichkeit vor
 * Vollstaendigkeit). Ein Material ohne Rezept in der Liste anzubieten hiesse,
 * einen Knopf zu zeigen, der dann `null` liefert — genau das schliesst die
 * letzte Probe hier aus, indem sie JEDE angebotene Option wirklich rechnet.
 */
describe('texturMaterialOptionen — nur Materialien mit echtem Rezept aus derive/textur.ts', () => {
  it('liefert mindestens eine Option', () => {
    expect(texturMaterialOptionen().length).toBeGreaterThan(0);
  });

  it('jede Option traegt eine SIA-Klasse aus REZEPT_KLASSEN', () => {
    for (const m of texturMaterialOptionen()) {
      expect(REZEPT_KLASSEN, m.key).toContain(m.sia);
    }
  });

  it('«sonstig» (keine SIA-Klasse mit Rezept) ist NIE dabei', () => {
    expect(texturMaterialOptionen().some((m) => m.sia === 'sonstig')).toBe(false);
  });

  it('jeder Schluessel ist eindeutig (keine Doppeleintraege im Auswahlfeld)', () => {
    const keys = texturMaterialOptionen().map((m) => m.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it('materialTextur() liefert fuer JEDE angebotene Option wirklich Karten — kein Knopf, der ins Leere zeigt', () => {
    for (const m of texturMaterialOptionen()) {
      expect(materialTextur(m.key), m.key).not.toBeNull();
    }
  });
});
