import { z } from 'zod';

/**
 * kosmo.bestand-aus-netz/0.3 — Vertrag zwischen der KosmoPrepare-Stufe
 * «Bestand aus Netz» und dem Kernel-Befehl, der den erkannten Bestand als
 * EINEN Rueckgaengig-Schritt ins Projekt einspielt (Integrator, 14.10.2026,
 * nach dem Prototyp des lokalen Workers an einer echten Halle und den fuenf
 * Vorschlaegen von Prepare).
 *
 * Grundsaetze:
 *  - EINGANG ist ein Netz aus der Visbox/RealityScan-Bruecke (bereinigt,
 *    lagegleich zu COLMAP und Splat). Ein aus dem Splat gerechnetes Netz taugt
 *    nicht (6–10 % Deckung, auf-277) und ist hier nicht vorgesehen.
 *  - Geliefert werden DATEN (Geschosse, Waende, Oeffnungen, Boeden, Daecher),
 *    keine Befehlsliste: Befehlsnamen aendern sich, die Bauteile nicht. Die
 *    Befehle leitet erst der Kernel ab.
 *  - Ehrlichkeit je Bauteil: `quelle` sagt, ob es gemessen (`netz`) oder
 *    angenommen (`annahme`) ist, mit Begruendung. Die Abweichung zum Netz
 *    steht als Verteilung; fehlt die Messung, fehlt das Feld und
 *    `abweichungFehlt` nennt den Grund — nie `null`, nie eine erfundene Zahl.
 *  - Ohne verlaesslichen Massstab gibt es kein Ergebnis: Ampel «rot» wird
 *    vom Schema abgelehnt (lieber nichts als falsche Meter).
 *
 * 0.2 (14.10.2026, Rueckfragen von Prepare): Dachrichtung (`fallrichtung`
 * Pflicht bei Pult, `firstrichtung` Pflicht bei Sattel, dieselben Werte wie
 * `design.dachErstellen`), eigene Herkunft der Dicke (`dickeQuelle`, weil
 * meist nur die Innenflaeche gemessen ist). Oeffnungen kommen an der
 * GEMESSENEN Lage; der Kernel verschiebt Bestand nicht nach der Pfeilerregel,
 * er meldet eine Unterschreitung als Hinweis (eine echte Tuer an der Ecke
 * steht dort).
 *
 * 0.3 (14.10.2026): ein Handmass hat keine Ampel (Owner-Entscheid E86).
 * `ampel` ist Pflicht bei `herkunft: 'imu'` und verboten bei `'hand'`; dort
 * steht stattdessen `handmass` (welche Strecke, Soll in mm, Ist in der Szene).
 * Ein Handmass als «gruen» zu fuehren hiesse eine Pruefung behaupten, die es
 * nicht gab.
 *
 * Koordinaten: alle Masse in mm im BESTANDSRAHMEN = Planrahmen des Projekts
 * (x/y wie im Grundriss, z ab Projektnull). Der Weg vom Szenenrahmen
 * (COLMAP/Splat) dorthin steht als Matrix im Kopf.
 */

const Mm = z.number().finite();
const Punkt = z.object({ x: Mm, y: Mm });
const Schluessel = z.string().min(1).max(64);

/** Herkunft eines Bauteils: gemessen oder angenommen, immer mit Grund. */
const Herkunft = z.discriminatedUnion('quelle', [
  z.object({ quelle: z.literal('netz'), begruendung: z.string().min(1).optional() }),
  z.object({ quelle: z.literal('annahme'), begruendung: z.string().min(1) }),
]);

/** Abweichung zum Netz in mm. Fehlt sie, steht der Grund in `abweichungFehlt`. */
export const BestandAbweichung = z.object({
  medianMm: z.number().nonnegative(),
  p95Mm: z.number().nonnegative(),
  n: z.number().int().positive(),
});
export type BestandAbweichung = z.infer<typeof BestandAbweichung>;

/** Eigene Herkunft der Dicke (gemessen ist oft nur eine Flaeche). Fehlt sie, gilt die Herkunft des Bauteils. */
const DickeQuelle = z.object({
  dickeQuelle: z
    .discriminatedUnion('quelle', [
      z.object({ quelle: z.literal('netz'), begruendung: z.string().min(1).optional() }),
      z.object({ quelle: z.literal('annahme'), begruendung: z.string().min(1) }),
    ])
    .optional(),
});

const Messung = z.object({
  abweichung: BestandAbweichung.optional(),
  abweichungFehlt: z.string().min(1).optional(),
});

function abweichungOderGrund(b: { abweichung?: unknown; abweichungFehlt?: unknown }, ctx: z.RefinementCtx): void {
  const hat = b.abweichung !== undefined;
  const grund = b.abweichungFehlt !== undefined;
  if (hat === grund) {
    ctx.addIssue({
      code: 'custom',
      message: hat
        ? 'abweichung und abweichungFehlt schliessen sich aus'
        : 'abweichung fehlt — dann muss abweichungFehlt den Grund nennen',
    });
  }
}

export const BestandGeschoss = z.object({
  schluessel: Schluessel,
  name: z.string().min(1),
  /** Oberkante Boden ab Projektnull. */
  koteMm: Mm,
  hoeheMm: z.number().positive(),
});
export type BestandGeschoss = z.infer<typeof BestandGeschoss>;

export const BestandWand = z
  .object({
    schluessel: Schluessel,
    geschoss: Schluessel,
    a: Punkt,
    b: Punkt,
    dickeMm: z.number().positive(),
    hoeheMm: z.number().positive(),
  })
  .and(DickeQuelle)
  .and(Herkunft)
  .and(Messung)
  .superRefine(abweichungOderGrund);
export type BestandWand = z.infer<typeof BestandWand>;

export const BestandOeffnung = z
  .object({
    schluessel: Schluessel,
    wand: Schluessel,
    art: z.enum(['fenster', 'tuer', 'tor']),
    /** Mitte der Oeffnung, gemessen ab `a` der Wand entlang der Achse. */
    mitteMm: z.number().nonnegative(),
    breiteMm: z.number().positive(),
    hoeheMm: z.number().positive(),
    bruestungMm: z.number().nonnegative(),
  })
  .and(Herkunft)
  .and(Messung)
  .superRefine(abweichungOderGrund);
export type BestandOeffnung = z.infer<typeof BestandOeffnung>;

export const BestandBoden = z
  .object({
    schluessel: Schluessel,
    geschoss: Schluessel,
    umriss: z.array(Punkt).min(3),
    dickeMm: z.number().positive(),
  })
  .and(DickeQuelle)
  .and(Herkunft)
  .and(Messung)
  .superRefine(abweichungOderGrund);
export type BestandBoden = z.infer<typeof BestandBoden>;

export const BestandDach = z
  .object({
    schluessel: Schluessel,
    geschoss: Schluessel,
    umriss: z.array(Punkt).min(3),
    form: z.enum(['flach', 'pult', 'sattel']),
    neigungGrad: z.number().min(0).max(75).optional(),
    /** Pflicht bei `pult`: wohin das Dach faellt (Werte wie `design.dachErstellen`). */
    fallrichtung: z.enum(['x+', 'x-', 'y+', 'y-']).optional(),
    /** Pflicht bei `sattel`: Richtung des Firsts. */
    firstrichtung: z.enum(['x', 'y']).optional(),
    /** Unterkante an der Traufe ab Projektnull (gemessen ist die Unterseite). */
    traufeUnterkanteMm: Mm,
  })
  .and(Herkunft)
  .and(Messung)
  .superRefine(abweichungOderGrund)
  .superRefine((d, ctx) => {
    if (d.form === 'pult' && !d.fallrichtung) ctx.addIssue({ code: 'custom', message: `${d.schluessel}: Pultdach braucht fallrichtung` });
    if (d.form === 'sattel' && !d.firstrichtung) ctx.addIssue({ code: 'custom', message: `${d.schluessel}: Satteldach braucht firstrichtung` });
  });
export type BestandDach = z.infer<typeof BestandDach>;

export const BestandMassstab = z.discriminatedUnion('herkunft', [
  z.object({
    /** Faktor Szene → Meter. */
    wert: z.number().positive(),
    herkunft: z.literal('imu'),
    ampel: z.enum(['gruen', 'gelb', 'rot']),
  }),
  z.object({
    wert: z.number().positive(),
    herkunft: z.literal('hand'),
    /** Die von Hand gemessene Strecke: Beschreibung, Soll (mm), Ist in Szenen-Einheiten. */
    handmass: z.object({ strecke: z.string().min(1), sollMm: z.number().positive(), istSzene: z.number().positive() }),
  }).strict(),
]);

export const BestandAusNetz = z
  .object({
    schema: z.literal('kosmo.bestand-aus-netz/0.3'),
    eingang: z.object({
      art: z.literal('netz'),
      herkunft: z.literal('visbox-realityscan'),
      datei: z.string().min(1),
      sha256: z.string().regex(/^[0-9a-f]{64}$/),
    }),
    rahmen: z.object({
      /** 4×4 zeilenweise: Szenenrahmen (COLMAP/Splat) → Bestandsrahmen (mm). */
      matrix: z.array(z.number().finite()).length(16),
      massstab: BestandMassstab,
      ausrichtungGrund: z.string().min(1),
      entzerrungGrund: z.string().min(1).optional(),
    }),
    seed: z.number().int(),
    werkzeug: z.string().min(1),
    geschosse: z.array(BestandGeschoss).min(1),
    waende: z.array(BestandWand),
    oeffnungen: z.array(BestandOeffnung),
    boeden: z.array(BestandBoden),
    daecher: z.array(BestandDach),
    /** Was erkannt, aber nicht abbildbar ist (z.B. offenes Hallenende), oder nicht erkannt wurde. */
    nichtErkannt: z.array(z.object({ was: z.string().min(1), wo: z.string().optional(), grund: z.string().min(1) })),
  })
  .superRefine((d, ctx) => {
    if (d.rahmen.massstab.herkunft === 'imu' && d.rahmen.massstab.ampel === 'rot') {
      ctx.addIssue({ code: 'custom', path: ['rahmen', 'massstab', 'ampel'], message: 'Massstab rot: kein Ergebnis — lieber nichts als falsche Meter' });
    }
    const geschosse = new Set(d.geschosse.map((g) => g.schluessel));
    const waende = new Set(d.waende.map((w) => w.schluessel));
    const alle = [...d.geschosse, ...d.waende, ...d.oeffnungen, ...d.boeden, ...d.daecher].map((x) => x.schluessel);
    const doppelt = alle.filter((s, i) => alle.indexOf(s) !== i);
    if (doppelt.length > 0) ctx.addIssue({ code: 'custom', message: `Schluessel doppelt: ${[...new Set(doppelt)].join(', ')}` });
    for (const [art, liste] of [['waende', d.waende], ['boeden', d.boeden], ['daecher', d.daecher]] as const) {
      for (const b of liste) {
        if (!geschosse.has(b.geschoss)) ctx.addIssue({ code: 'custom', path: [art], message: `${b.schluessel}: Geschoss «${b.geschoss}» fehlt` });
      }
    }
    for (const o of d.oeffnungen) {
      if (!waende.has(o.wand)) ctx.addIssue({ code: 'custom', path: ['oeffnungen'], message: `${o.schluessel}: Wand «${o.wand}» fehlt` });
    }
  });
export type BestandAusNetz = z.infer<typeof BestandAusNetz>;
