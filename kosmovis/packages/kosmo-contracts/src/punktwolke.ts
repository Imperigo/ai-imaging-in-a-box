import { z } from 'zod';

/**
 * kosmo.punktwolke/0.2 — Vertrag zwischen der KosmoPrepare-Umwandlung
 * (LAS, LAZ, E57, XYZ, PLY jeder Art) und der App (Integrator, 14.10.2026,
 * nach dem Befund des lokalen Workers an einer echten Drohnen-Wolke).
 *
 * Die App liest kuenftig NUR dieses eine Format; jede Quellform wandelt
 * Prepare hinter der Prozessgrenze um. Der Kopf (dieses Schema, als
 * Begleitdatei `.punktwolke.json`) beschreibt die Daten; die Punkte selbst
 * liegen binaer daneben (`daten`, kleines Endian, je Feld ein Block in der
 * Reihenfolge von `felder`).
 *
 * 0.2 (14.10.2026, Rueckfragen von Prepare): `lage.hoehenbezug` (Pflicht bei
 * LV95; eine ellipsoidische Hoehe liegt rund 50 m neben der Gebrauchshoehe,
 * «unbekannt» ist eine ehrliche Angabe) und `lage.erkannt` (woher «LV95»
 * kommt: CRS-Eintrag, Wertebereich oder von Hand). Eine Umrechnung von
 * 16-bit- auf 8-bit-Farben steht in `verworfen`.
 *
 * Grundsaetze:
 *  - EHRLICHE LAGE: Eine Wolke, die schon in LV95 vorliegt, bringt das als
 *    Herkunft mit (`lage.art: 'lv95'`), statt vorgetaeuschter Passpunkte.
 *    Gespeichert wird in einem lokalen Rahmen um `ursprung` (Float32 reicht
 *    dann fuer mm-Genauigkeit); der Ursprung steht in LV95.
 *  - NICHTS GEHT STILL VERLOREN: Intensitaet, Klasse, Normale bleiben
 *    erhalten, wenn die Quelle sie hat; was die Quelle hatte, aber nicht
 *    uebernommen wurde, steht in `verworfen` mit Grund.
 *  - AUSDUENNUNG wird angegeben, nie verschwiegen (Verfahren, vorher/nachher).
 */

const Feld = z.enum(['xyz', 'rgb', 'intensitaet', 'klasse', 'normale']);
export type PunktwolkeFeld = z.infer<typeof Feld>;

/** Typ je Feld im Binaerblock (fest, damit kein Leser raten muss). */
export const PUNKTWOLKE_FELDTYP: Readonly<Record<PunktwolkeFeld, string>> = {
  xyz: 'float32 x3, Meter, lokaler Rahmen um `ursprung`',
  rgb: 'uint8 x3',
  intensitaet: 'uint16',
  klasse: 'uint8 (ASPRS-Klassencode)',
  normale: 'float32 x3, Einheitsvektor',
};

export const Punktwolke = z
  .object({
    schema: z.literal('kosmo.punktwolke/0.2'),
    quelle: z.object({
      format: z.enum(['las', 'laz', 'e57', 'xyz', 'ply']),
      datei: z.string().min(1),
      sha256: z.string().regex(/^[0-9a-f]{64}$/),
      punkteQuelle: z.number().int().nonnegative(),
    }),
    lage: z.discriminatedUnion('art', [
      /** Die Quelle liegt in LV95 (CH1903+). */
      z.object({
        art: z.literal('lv95'),
        ursprung: z.object({ e: z.number(), n: z.number(), h: z.number() }),
        /** Worauf sich h bezieht. «unbekannt» ist erlaubt und ehrlich; raten nicht. */
        hoehenbezug: z.enum(['ln02', 'lhn95', 'ellipsoid', 'unbekannt']),
        /** Woher die LV95-Lage stammt. */
        erkannt: z.enum(['crs', 'wertebereich', 'hand']),
      }),
      /** Lokale Koordinaten ohne Verortung: die App verortet spaeter (Passpunkte), nie still. */
      z.object({ art: z.literal('lokal'), hinweis: z.string().min(1) }),
    ]),
    /** +Z ist oben. Wurde dafuer gedreht, steht hier warum (sonst steht die Wolke «hochkant»). */
    achsen: z.object({ zOben: z.literal(true), gedrehtGrund: z.string().min(1).optional() }),
    daten: z.string().min(1),
    punkte: z.number().int().positive(),
    felder: z.array(Feld).min(1),
    begrenzung: z.object({ min: z.tuple([z.number(), z.number(), z.number()]), max: z.tuple([z.number(), z.number(), z.number()]) }),
    ausduennung: z.discriminatedUnion('art', [
      z.object({ art: z.literal('keine') }),
      z.object({ art: z.enum(['raster', 'zufall-fester-seed']), rasterMm: z.number().positive().optional(), seed: z.number().int().optional(), grund: z.string().min(1) }),
    ]),
    /** Was die Quelle hatte und nicht uebernommen wurde, mit Grund. */
    verworfen: z.array(z.object({ was: z.string().min(1), grund: z.string().min(1) })),
    werkzeug: z.string().min(1),
  })
  .superRefine((d, ctx) => {
    if (!d.felder.includes('xyz')) ctx.addIssue({ code: 'custom', path: ['felder'], message: 'xyz fehlt' });
    if (new Set(d.felder).size !== d.felder.length) ctx.addIssue({ code: 'custom', path: ['felder'], message: 'Feld doppelt' });
    if (d.punkte > d.quelle.punkteQuelle) ctx.addIssue({ code: 'custom', path: ['punkte'], message: 'mehr Punkte als die Quelle' });
    if (d.ausduennung.art === 'keine' && d.punkte !== d.quelle.punkteQuelle) {
      ctx.addIssue({ code: 'custom', path: ['ausduennung'], message: 'Punkte fehlen, aber keine Ausduennung angegeben' });
    }
    for (let i = 0; i < 3; i++) {
      if (!(d.begrenzung.min[i]! <= d.begrenzung.max[i]!)) ctx.addIssue({ code: 'custom', path: ['begrenzung'], message: 'min > max' });
      // Lokaler Rahmen: Float32-Meter bleiben bis rund 10 km mm-genau. Groesser = falscher Ursprung.
      if (Math.abs(d.begrenzung.min[i]!) > 10_000 || Math.abs(d.begrenzung.max[i]!) > 10_000) {
        ctx.addIssue({ code: 'custom', path: ['begrenzung'], message: 'Koordinaten ueber 10 km vom Ursprung: lokalen Ursprung setzen' });
        break;
      }
    }
  });
export type Punktwolke = z.infer<typeof Punktwolke>;
