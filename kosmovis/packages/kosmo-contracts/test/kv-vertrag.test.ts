import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { RenderResult, renderResultMaengel, unbekannteFelder } from '../src';

/**
 * kv-vertrag (V017-SPEZ Kern-Spur): additive, optionale Felder im
 * Ergebnisvertrag, je Feld eine Probe «vorher abgestreift oder abgewiesen,
 * nachher gelesen». Quellen:
 *  - `auftraege/ergebnisse/auf-20260923-155-antwort-lieferstatus-und-standardmodell.md`
 *    Bauposten 1 (vier Kamerafelder) und 2 (drei Felder zum gerechneten Modell),
 *  - `auftraege/ergebnisse/auf-20260921-133-antwort-null-regel.md` und E123
 *    (`ai_variant` nullbar, benannter Mangel statt Schemafehler),
 *  - `auftraege/ergebnisse/auf-20260922-142-antwort-geometry-gates-und-qa-je-kamera.md`
 *    Bauposten 1 (`geometry_gates`), gebaut nach dem Beispiel-JSON der
 *    Gegenseite `docs/auftraege-kosmovis/erg-20260929-e124-beispiele-und-glas.md`
 *    §3, abgelegt als `fixtures/e124-render-result.json` (unveraendert).
 *
 * Die Beispiele unten sind nach der Form in den Antwortblaettern gebaut,
 * nicht gemessen: ein echtes Beispiel der Gegenseite (acht von zwoelf
 * Kameras geliefert) liegt im Repo nicht vor.
 */

const BASIS = {
  job_id: 'vis-kv-1',
  images: ['renders/eingang.png'],
  qa: { verdict: { passed: true } },
};

describe('qa_je_kamera[]: lieferstatus, lieferstatus_grund, bilder_soll, bilder_ist', () => {
  const roh = {
    ...BASIS,
    qa_je_kamera: [
      { kamera: 'eingang', lieferstatus: 'geliefert', bilder_soll: 1, bilder_ist: 1 },
      {
        kamera: 'innenraum',
        lieferstatus: 'fehlgeschlagen',
        lieferstatus_grund: 'Speicher voll nach dem zweiten Bild',
        bilder_soll: 3,
        bilder_ist: 2,
      },
      { kamera: 'uebersicht', lieferstatus: 'geliefert', lieferstatus_grund: 'Zwilling, nicht neu gerendert', bilder_soll: null, bilder_ist: null },
    ],
  };

  it('die vier Felder kommen nach dem Einlesen an und werden nicht mehr als unbekannt gemeldet', () => {
    const r = RenderResult.parse(roh);
    expect(r.qa_je_kamera?.[0]).toMatchObject({ lieferstatus: 'geliefert', bilder_soll: 1, bilder_ist: 1 });
    expect(r.qa_je_kamera?.[1]).toMatchObject({
      lieferstatus: 'fehlgeschlagen',
      lieferstatus_grund: 'Speicher voll nach dem zweiten Bild',
      bilder_soll: 3,
      bilder_ist: 2,
    });
    expect(r.qa_je_kamera?.[2]).toMatchObject({ bilder_soll: null, bilder_ist: null });
    expect(unbekannteFelder(roh, r)).toEqual([]);
  });

  it('kein Default: ein Eintrag ohne die Felder bleibt ohne sie («nichts gesagt»)', () => {
    const r = RenderResult.parse({ ...BASIS, qa_je_kamera: [{ kamera: 'eingang' }] });
    expect(r.qa_je_kamera?.[0]).toEqual({ kamera: 'eingang' });
  });

  it('nicht geliefert ohne Grund faellt durch, je Kamera wie am Auftrag', () => {
    const res = RenderResult.safeParse({
      ...BASIS,
      qa_je_kamera: [{ kamera: 'innenraum', lieferstatus: 'uebersprungen' }],
    });
    expect(res.success).toBe(false);
    expect(res.error?.issues.map((i) => i.path.join('.'))).toContain('qa_je_kamera.0.lieferstatus_grund');
  });

  it('bilder_ist: -1 und 1.5 werden abgewiesen, null parst', () => {
    for (const falsch of [-1, 1.5]) {
      const res = RenderResult.safeParse({ ...BASIS, qa_je_kamera: [{ kamera: 'k', bilder_ist: falsch }] });
      expect(res.success).toBe(false);
    }
    expect(RenderResult.safeParse({ ...BASIS, qa_je_kamera: [{ kamera: 'k', bilder_soll: -1 }] }).success).toBe(false);
  });

  it('ein unbekannter Wert fuer lieferstatus wird abgewiesen (dreiwertig wie am Auftrag)', () => {
    const res = RenderResult.safeParse({
      ...BASIS,
      qa_je_kamera: [{ kamera: 'k', lieferstatus: 'teilweise', lieferstatus_grund: 'x' }],
    });
    expect(res.success).toBe(false);
  });
});

describe('oberste Ebene: engine_used, engine_license, guidance_applied', () => {
  it('die drei Felder kommen an', () => {
    const roh = { ...BASIS, engine_used: 'z-image-turbo', engine_license: 'Apache-2.0', guidance_applied: true };
    const r = RenderResult.parse(roh);
    expect(r.engine_used).toBe('z-image-turbo');
    expect(r.engine_license).toBe('Apache-2.0');
    expect(r.guidance_applied).toBe(true);
    expect(unbekannteFelder(roh, r)).toEqual([]);
  });

  it('kein Default: fehlen die Felder, fehlen sie auch nach dem Einlesen', () => {
    const r = RenderResult.parse(BASIS);
    expect(r).not.toHaveProperty('engine_used');
    expect(r).not.toHaveProperty('engine_license');
    expect(r).not.toHaveProperty('guidance_applied');
  });

  it('guidance_applied: null faellt durch (Absicht, Antwortblatt 155 F7 Bedingung 1)', () => {
    expect(RenderResult.safeParse({ ...BASIS, guidance_applied: null }).success).toBe(false);
  });
});

describe('engine_license_open (P-LIZENZMARKE, E128)', () => {
  it('true kommt an und wird nicht mehr als [E76] abgestreift', () => {
    const roh = { ...BASIS, engine_used: 'qwen-image-2.1', engine_license_open: true };
    const r = RenderResult.parse(roh);
    expect(r.engine_license_open).toBe(true);
    expect(unbekannteFelder(roh, r)).toEqual([]);
    expect(renderResultMaengel(r)).toEqual([]);
  });

  it('kein Default: fehlt das Feld, fehlt es auch nach dem Einlesen und ist kein Mangel', () => {
    const r = RenderResult.parse(BASIS);
    expect(r).not.toHaveProperty('engine_license_open');
    expect(renderResultMaengel(r)).toEqual([]);
  });

  it('false verwirft das Ergebnis nicht, sondern ergibt eine benannte Mangelzeile', () => {
    const roh = { ...BASIS, engine_license_open: false };
    const r = RenderResult.parse(roh);
    expect(r.engine_license_open).toBe(false);
    expect(r.images).toEqual(['renders/eingang.png']);
    expect(renderResultMaengel(r)).toEqual([
      'engine_license_open: false gemeldet, der Vertrag kennt nur true',
    ]);
  });

  it('null faellt durch wie guidance_applied (nicht nullbar)', () => {
    expect(RenderResult.safeParse({ ...BASIS, engine_license_open: null }).success).toBe(false);
  });
});

describe('ai_variant nullbar mit benanntem Mangel (E123)', () => {
  it('ai_variant: null parst (vorher: ganzes Ergebnis ungueltig) und bleibt null', () => {
    const r = RenderResult.parse({ ...BASIS, ai_variant: null });
    expect(r.ai_variant).toBeNull();
  });

  it('renderResultMaengel benennt null als «nicht bekannt», statt still zu schweigen', () => {
    const r = RenderResult.parse({ ...BASIS, ai_variant: null });
    expect(renderResultMaengel(r)).toEqual(['ai_variant: nicht bekannt (die Gegenseite meldete null)']);
  });

  it('Gegenprobe: ein Name oder ein fehlendes Feld ist kein Mangel', () => {
    expect(renderResultMaengel(RenderResult.parse({ ...BASIS, ai_variant: 'eingang_ki.png' }))).toEqual([]);
    expect(renderResultMaengel(RenderResult.parse(BASIS))).toEqual([]);
  });

  it('bilder_soll/bilder_ist null je Kamera werden ebenfalls benannt', () => {
    const r = RenderResult.parse({ ...BASIS, qa_je_kamera: [{ kamera: 'innenraum', bilder_soll: 3, bilder_ist: null }] });
    expect(renderResultMaengel(r)).toEqual(['qa_je_kamera[innenraum].bilder_ist: nicht bekannt (die Gegenseite meldete null)']);
  });
});

describe('geometry_gates nach dem Beispiel der Gegenseite (erg-20260929-e124 §3/§4)', () => {
  // Das Blatt 142 (Posten 1) wartete auf ein Beispiel-JSON; es liegt seit
  // 29.09.2026 vor. Die WERTE darin sind Attrappe (Wert 0,9 ohne Maskenweg),
  // die FORM ist nach Angabe der Gegenseite dieselbe wie im echten Lauf.
  const beispiel = JSON.parse(
    readFileSync(fileURLToPath(new URL('./fixtures/e124-render-result.json', import.meta.url)), 'utf8'),
  ) as Record<string, unknown>;

  it('das ganze Beispiel-Ergebnis parst, und seit kv-ebenen (E124) wird nichts mehr abgestreift', () => {
    // Bis kv-ebenen stand hier «abgestreift wird nur noch `ebenen`»; die
    // Probe dazu steht jetzt in `kv-ebenen.test.ts`.
    const r = RenderResult.parse(beispiel);
    expect(unbekannteFelder(beispiel, r)).toEqual([]);
  });

  it('geometry_gates kommt mit allen Feldern des Beispiels an', () => {
    const r = RenderResult.parse(beispiel);
    expect(r.geometry_gates).toEqual(beispiel.geometry_gates);
    expect(r.geometry_gates?.released).toBe(false);
    expect(r.geometry_gates?.status).toBe('not_measured');
  });

  it('engine_used und engine_license aus dem Beispiel kommen an, guidance_applied fehlt wie im Beispiel', () => {
    const r = RenderResult.parse(beispiel);
    expect(r.engine_used).toBe('z-image-turbo');
    expect(r.engine_license).toBe('Apache-2.0');
    expect(r).not.toHaveProperty('guidance_applied');
  });

  it('kein Default: ein Ergebnis ohne geometry_gates bleibt ohne', () => {
    expect(RenderResult.parse(BASIS)).not.toHaveProperty('geometry_gates');
  });

  it('passed: null und released: null fallen durch (Blatt 142 V3: passed ist Boolean)', () => {
    const gates = beispiel.geometry_gates as Record<string, unknown>;
    expect(RenderResult.safeParse({ ...BASIS, geometry_gates: { ...gates, passed: null } }).success).toBe(false);
    expect(RenderResult.safeParse({ ...BASIS, geometry_gates: { ...gates, released: null } }).success).toBe(false);
  });

  it('status spricht nur die drei Woerter des Vertrags (Blatt 142 V2), auch in den Unterstatus', () => {
    const gates = beispiel.geometry_gates as Record<string, unknown>;
    expect(RenderResult.safeParse({ ...BASIS, geometry_gates: { ...gates, status: 'fehlt' } }).success).toBe(false);
    expect(
      RenderResult.safeParse({ ...BASIS, geometry_gates: { ...gates, rho_mask_status: 'degeneriert' } }).success,
    ).toBe(false);
    expect(
      RenderResult.safeParse({ ...BASIS, geometry_gates: { ...gates, status: 'not_applicable' } }).success,
    ).toBe(true);
  });

  it('Frage 2 der Gegenseite: fehlgeschlagen bei voller Bilderzahl (Ebene fehlt) wird angenommen', () => {
    const r = RenderResult.safeParse({
      ...BASIS,
      qa_je_kamera: [
        {
          kamera: 'Suedost',
          lieferstatus: 'fehlgeschlagen',
          lieferstatus_grund: 'BESTELLTE EBENE FEHLT: tiefe (Blender-Bericht ohne Tiefe)',
          bilder_soll: 1,
          bilder_ist: 1,
        },
      ],
    });
    expect(r.success).toBe(true);
  });
});
