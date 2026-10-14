import { describe, expect, it } from 'vitest';
import { BridgeHealth, unbekannteFelder } from '../src';

/**
 * kv-abholer-puls (Antwortblatt auf-20260924-171 K2, Abnahme d): ein
 * `BridgeHealth` mit und ohne `abholer` parst, und der Block wird nicht mehr
 * abgestreift. Die Bloecke unten sind WOERTLICH das gemessene Beispiel der
 * Gegenseite (`kosmo-orbit/docs/auftraege-kosmovis/erg-20260929-e124-beispiele-und-glas.md`
 * Abschnitt 5, feste Uhr 29.09.2026 12:00 UTC).
 */

const BASIS = {
  ok: true,
  version: '1.0.0',
  services: { jobstore: true, ollama: false, stt: false, tts: false, embed: false },
};

const NIE_GESEHEN = {
  zustand: 'nie_gesehen',
  zuletzt: null,
  alter_s: null,
  frist_s: 120,
  grund: 'Kein Lebenszeichen des Abholers in dieser Ablage. Entweder läuft er nicht, oder er schaut in eine andere Ablage.',
};

const WARTET = {
  zustand: 'wartet',
  zuletzt: '2026-09-29T12:00:00Z',
  alter_s: 31.0,
  frist_s: 120,
  letzter_durchgang: { gesehen: 1, verarbeitet: 1, liegengelassen: 1, fehler: 0, waisen: 0 },
  grund: '',
};

describe('BridgeHealth.abholer (optional)', () => {
  it('ohne abholer parst wie bisher (Fake-Modus, aeltere Bruecke)', () => {
    const h = BridgeHealth.parse(BASIS);
    expect(h).not.toHaveProperty('abholer');
  });

  it('nie_gesehen mit zuletzt und alter_s als null parst und bleibt null (E123)', () => {
    const roh = { ...BASIS, abholer: NIE_GESEHEN };
    const h = BridgeHealth.parse(roh);
    expect(h.abholer).toEqual(NIE_GESEHEN);
    expect(unbekannteFelder(roh, h)).toEqual([]);
  });

  it('alle fuenf Zustaende des Beispiels parsen, der Durchgang kommt an', () => {
    for (const zustand of ['laeuft_leer', 'steht', 'wartet', 'arbeitet'] as const) {
      const roh = { ...BASIS, abholer: { ...WARTET, zustand } };
      const h = BridgeHealth.parse(roh);
      expect(h.abholer?.zustand).toBe(zustand);
      expect(h.abholer?.letzter_durchgang).toEqual(WARTET.letzter_durchgang);
      expect(unbekannteFelder(roh, h)).toEqual([]);
    }
  });

  it('ein unbekannter Zustand wird abgewiesen, nicht geraten', () => {
    expect(BridgeHealth.safeParse({ ...BASIS, abholer: { ...WARTET, zustand: 'schlaeft' } }).success).toBe(false);
  });

  it('ein negativer Zaehler wird abgewiesen', () => {
    const kaputt = { ...WARTET, letzter_durchgang: { ...WARTET.letzter_durchgang, fehler: -1 } };
    expect(BridgeHealth.safeParse({ ...BASIS, abholer: kaputt }).success).toBe(false);
  });
});
