import { describe, expect, it } from 'vitest';
import {
  DECKUNG_HILFE,
  DECKUNG_SCHWELLE,
  DECKUNG_SCHWELLE_HERKUNFT,
  SATZ_FORM_WEICHT_AB,
  deckungDerReihe,
  deckungUrteil,
  deckungUrteilDesLaufs,
  formWeichtAbLautErgebnis,
} from '../src/modules/vis/grossansicht';
import type { NodeLauf } from '../src/modules/vis/vis-runtime';

/**
 * Visbox-Entscheid 138 (22.10.2026): der Rechenkern hob die Deckungsschwelle von 0,10 auf 0,25 und schreibt bei
 * Unterschreitung «FORM WEICHT VOM GRUNDBILD AB, Kamera '<name>': …» ins Ergebnis. Die Oberflaeche urteilte weiter
 * selbst mit 0,10 und zeigte bei Laeufen wie 339 KS (ein anderes Haus, Kanten 0,213) «deckungsgleich».
 *
 * Gegen den alten Stand rot: 0,10 nannte 0,142 / 0,213 / 0,216 «deckungsgleich», und der Satz im Ergebnis zaehlte nicht.
 */

const lauf = (deckung: number | undefined, hinweise: string[] = [], extra: Partial<NodeLauf> = {}): NodeLauf =>
  ({
    status: 'fertig',
    bild: 'KS.png',
    qaJeKamera: [{ kamera: 'KS', ...(deckung !== undefined ? { deckung } : {}) }],
    qa: { verdict: { passed: true, hinweise } },
    ...extra,
  }) as NodeLauf;

const satz = (kamera: string, iou: number) =>
  `${SATZ_FORM_WEICHT_AB}, Kamera '${kamera}': Kanten des KI-Bilds gegen das Grundbild ${iou} unter 0.25 — gleiche ` +
  'Grundlage, aber Form oder Fensterteilung nicht wie im Grundbild (Schwelle gesetzt aus …).';

describe('Deckungsschwelle wie im Kern (Entscheid 138)', () => {
  it('die Schwelle ist 0,25 und nennt ihre Quelle; die Kurzhilfe liest dieselbe Zahl', () => {
    expect(DECKUNG_SCHWELLE).toBe(0.25);
    expect(DECKUNG_SCHWELLE_HERKUNFT).toContain('Entscheid 138');
    expect(DECKUNG_HILFE).toContain('mindestens 25 %');
  });

  it('die Laeufe aus 337/339 fallen auf die richtige Seite der Luecke', () => {
    // Form nein (ohne Bildeingang, anderes Haus)
    expect([0.142, 0.213, 0.216].map(deckungUrteil)).toEqual(['weicht-ab', 'weicht-ab', 'weicht-ab']);
    // Form ja (mit Bildeingang)
    expect([0.294, 0.296, 0.367, 0.481].map(deckungUrteil)).toEqual(Array(4).fill('deckungsgleich'));
  });

  it('339 KS: ohne Satz im Ergebnis urteilt die Zahl, mit Satz das Ergebnis', () => {
    expect(deckungUrteilDesLaufs(lauf(0.213))).toBe('weicht-ab');
    expect(deckungUrteilDesLaufs(lauf(0.213, [satz('KS', 0.213)]))).toBe('weicht-ab');
    expect(deckungDerReihe([lauf(0.213), lauf(0.481)]).urteil).toBe('weicht-ab');
  });

  it('das Urteil des Ergebnisses gilt auch, wenn die Zahl fehlt oder hoeher laege', () => {
    expect(deckungUrteilDesLaufs(lauf(undefined, [satz('KS', 0.2)]))).toBe('weicht-ab');
    expect(deckungUrteilDesLaufs(lauf(0.3, [satz('KS', 0.2)]))).toBe('weicht-ab');
  });

  it('ein Satz zu einer anderen Kamera betrifft das gezeigte Bild nicht', () => {
    const zwei = lauf(0.4, [satz('KN', 0.1)], {
      qaJeKamera: [
        { kamera: 'KS', deckung: 0.4 },
        { kamera: 'KN', deckung: 0.1 },
      ],
    } as Partial<NodeLauf>);
    expect(formWeichtAbLautErgebnis(zwei)).toBe(false);
    expect(deckungUrteilDesLaufs(zwei)).toBe('deckungsgleich');
    expect(deckungUrteilDesLaufs({ ...zwei, bild: 'KN.png' })).toBe('weicht-ab');
  });

  it('andere Hinweise zaehlen nicht; ohne Zahl und ohne Satz bleibt «ungemessen»', () => {
    expect(deckungUrteilDesLaufs(lauf(0.3, ['KI-BILD OHNE GRUNDLAGENBILD, Kamera \'KS\'']))).toBe('deckungsgleich');
    expect(deckungUrteilDesLaufs(lauf(undefined))).toBe('ungemessen');
  });
});
