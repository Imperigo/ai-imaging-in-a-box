import { describe, expect, it } from 'vitest';
import { auraCss, ohneKommentare } from './leiter-bestand';

/**
 * Wache d11: `.k-einblenden` haelt kein Endbild fest. Mit `both`/`forwards`
 * bleibt die Animation nach dem Ende wirksam; ein wirkendes transform macht
 * die Flaeche zum Anker fuer jedes `position:fixed` darin (Dialoge und
 * Kosmo-Blase lagen deshalb an der Flaeche statt am Bildschirm). `backwards`
 * haelt nur das Anfangsbild waehrend der Verzoegerung.
 */
describe('.k-einblenden haelt kein Endbild', () => {
  it('animation-Kurzform ohne both/forwards, mit backwards', () => {
    const css = ohneKommentare(auraCss());
    const m = /\.k-einblenden\s*\{([^}]*)\}/.exec(css);
    expect(m, '.k-einblenden-Regel fehlt').not.toBeNull();
    const koerper = m![1]!;
    expect(koerper).not.toMatch(/\b(both|forwards)\b/);
    expect(koerper).toMatch(/\bbackwards\b/);
  });
});
