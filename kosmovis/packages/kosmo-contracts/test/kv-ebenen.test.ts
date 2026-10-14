import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { RenderResult, RenderScene, renderResultMaengel, unbekannteFelder } from '../src';

/**
 * kv-ebenen (E124 Schritt 1, Owner-Entscheid 29.09.2026 «zwei Schritte»):
 * NUR Vertrag und Rueckweg, gegen das echte Beispiel der Gegenseite
 * (`docs/auftraege-kosmovis/erg-20260929-e124-beispiele-und-glas.md` §2/§3).
 * Die Anzeige in der App kommt erst, wenn ein echter Lauf die Ebenen belegt.
 *
 * Beide Fixtures sind WOERTLICH aus dem Blatt uebernommen:
 *  - `fixtures/e124-render-scene.json` (§2, die Bestellung, `passes: "alle"`),
 *  - `fixtures/e124-render-result.json` (§3, das Ergebnis mit `ebenen`).
 *
 * Probe je Feld: «vorher abgestreift, nachher gelesen».
 */

function fixture(name: string): Record<string, unknown> {
  return JSON.parse(readFileSync(fileURLToPath(new URL(`./fixtures/${name}`, import.meta.url)), 'utf8')) as Record<
    string,
    unknown
  >;
}

type Roh = Record<string, unknown>;

const ergebnis = fixture('e124-render-result.json');
// FUND (29.09.2026): die Beispiel-Bestellung der Gegenseite traegt kein
// `out`, unser `RenderScene` verlangt es (Pflichtfeld seit jeher; unser
// Sender setzt es immer). Nicht Teil von E124 und hier NICHT geaendert; die
// Probe ergaenzt `out`, damit sie `passes` misst und nicht diese Luecke.
const bestellungWoertlich = fixture('e124-render-scene.json');
const bestellung: Roh = { ...bestellungWoertlich, out: 'renders/' };

const BASIS = {
  job_id: 'vis-ebenen-1',
  images: ['Suedost.png'],
  qa: { verdict: { passed: true } },
};

const ebenenRoh = ergebnis['ebenen'] as Roh[];
const tiefeRoh = ebenenRoh.find((e) => e['art'] === 'tiefe')!;

describe('Bestellung render.passes (Blatt §2)', () => {
  it('woertlich, ohne out, faellt die Beispiel-Bestellung an `out` durch (benannter Fund, nicht E124)', () => {
    const r = RenderScene.safeParse(bestellungWoertlich);
    expect(r.success).toBe(false);
    expect(r.error!.issues.map((i) => i.path.join('.'))).toEqual(['out']);
  });

  it('die Beispiel-Bestellung parst, und render.passes wird gelesen statt abgestreift', () => {
    const s = RenderScene.parse(bestellung);
    expect((s.render as Roh)['passes']).toBe('alle');
    const unbekannt = unbekannteFelder(bestellung, s);
    expect(unbekannt).not.toContain('render.passes');
  });

  it('eine Liste aus den drei Namen ist gueltig, auch leer', () => {
    const ohne = { ...bestellung, render: { ...(bestellung['render'] as Roh) } };
    for (const passes of [['schoenbild'], ['tiefe', 'material-id'], ['schoenbild', 'tiefe', 'material-id'], []]) {
      const s = RenderScene.parse({ ...ohne, render: { ...(ohne.render as Roh), passes } });
      expect((s.render as Roh)['passes']).toEqual(passes);
    }
  });

  it('ein unbekannter Name wird abgewiesen, wie drueben (keine Ebene raten)', () => {
    const r = RenderScene.safeParse({ ...bestellung, render: { ...(bestellung['render'] as Roh), passes: ['normalen'] } });
    expect(r.success).toBe(false);
    const t = RenderScene.safeParse({ ...bestellung, render: { ...(bestellung['render'] as Roh), passes: 'alles' } });
    expect(t.success).toBe(false);
  });

  it('kein Default: ohne passes bleibt die Bestellung ohne (Bedingung b, keine Ebene)', () => {
    const render = { ...(bestellung['render'] as Roh) };
    delete render['passes'];
    const s = RenderScene.parse({ ...bestellung, render });
    expect(s.render).not.toHaveProperty('passes');
  });
});

describe('Rueckweg ebenen (Blatt §3)', () => {
  it('das ganze Beispiel parst, ebenen kommt vollstaendig an, NICHTS wird mehr abgestreift', () => {
    const r = RenderResult.parse(ergebnis);
    expect((r as Roh)['ebenen']).toEqual(ergebnis['ebenen']);
    expect(unbekannteFelder(ergebnis, r)).toEqual([]);
  });

  it('die Ebenen stehen NICHT in images (sechs Ebenen, zwei Bilder)', () => {
    const r = RenderResult.parse(ergebnis) as Roh;
    expect((r['ebenen'] as unknown[]).length).toBe(6);
    expect(r['images']).toEqual(['Suedost.png', 'Suedwest.png']);
  });

  it('kein Default: ein Ergebnis ohne ebenen bleibt ohne (Bedingung b)', () => {
    expect(RenderResult.parse(BASIS)).not.toHaveProperty('ebenen');
  });

  it('bedeutung der Tiefe ist strukturiert und in Metern lesbar (Bedingung a)', () => {
    const r = RenderResult.parse(ergebnis) as Roh;
    const tiefe = (r['ebenen'] as Roh[]).find((e) => e['art'] === 'tiefe' && e['kamera'] === 'Suedost')!;
    const b = tiefe['bedeutung'] as Roh;
    expect(b['einheit']).toBe('m');
    expect(typeof b['min_m']).toBe('number');
    expect(typeof b['max_m']).toBe('number');
    expect(b['bittiefe']).toBe(8);
  });

  it('eine Tiefe mit Text statt Zahl in min_m faellt durch (die Bedeutung ist typisiert)', () => {
    const kaputt = { ...tiefeRoh, bedeutung: { ...(tiefeRoh['bedeutung'] as Roh), min_m: 'sechs' } };
    expect(RenderResult.safeParse({ ...BASIS, ebenen: [kaputt] }).success).toBe(false);
  });

  it('eine unbekannte Art wird abgewiesen', () => {
    expect(RenderResult.safeParse({ ...BASIS, ebenen: [{ ...tiefeRoh, art: 'normalen' }] }).success).toBe(false);
  });

  it('der Dateiname ist flach (ein Segment, wie get_artifact ihn verlangt)', () => {
    for (const datei of ['renders/Suedost__tiefe.png', 'a\\b.png', '..']) {
      expect(RenderResult.safeParse({ ...BASIS, ebenen: [{ ...tiefeRoh, datei }] }).success, datei).toBe(false);
    }
  });
});

describe('bestellt, aber fehlt (Bedingung c)', () => {
  const fehlt = {
    kamera: 'Suedost',
    art: 'tiefe',
    datei: null,
    bedeutung: null,
    grund: 'Tiefenpass lieferte keine Datei',
  };

  it('datei: null und bedeutung: null mit grund werden angenommen und als Mangel benannt', () => {
    const r = RenderResult.parse({
      ...BASIS,
      ebenen: [fehlt],
      qa_je_kamera: [
        {
          kamera: 'Suedost',
          lieferstatus: 'fehlgeschlagen',
          lieferstatus_grund: 'BESTELLTE EBENE FEHLT: tiefe (Tiefenpass lieferte keine Datei)',
          bilder_soll: 1,
          bilder_ist: 1,
        },
      ],
    });
    expect((r as Roh)['ebenen']).toEqual([fehlt]);
    expect(renderResultMaengel(r)).toContain(
      'ebenen[Suedost/tiefe]: bestellt, nicht geliefert (Tiefenpass lieferte keine Datei)',
    );
  });

  it('eine fehlende Ebene ohne grund faellt durch: ein Loch ohne Begruendung ist keine Antwort', () => {
    const { grund: _grund, ...ohneGrund } = fehlt;
    expect(RenderResult.safeParse({ ...BASIS, ebenen: [ohneGrund] }).success).toBe(false);
  });

  it('eine gelieferte Ebene erzeugt keinen Mangel', () => {
    expect(renderResultMaengel(RenderResult.parse(ergebnis))).toEqual([]);
  });
});
