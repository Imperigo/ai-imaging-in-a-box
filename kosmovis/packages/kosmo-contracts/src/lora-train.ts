import { z } from 'zod';

/**
 * kosmo.lora-train/v1 — Trainer-Contract (v0.8.2 / P5, `docs/V082-SPEZ.md`
 * §6.5 + §3). Zwei Schemata, dieselbe Ehrlichkeits-Regel wie überall in
 * diesem Paket: der Vertrag beschreibt NUR, was VOR und NACH dem echten
 * GPU-Lauf passiert (Datensatz, Manifest, Bericht) — der Lauf selbst bleibt
 * deklarierte HomeStation-Grenze (`docs/HOMESTATION-AUFTRAG.md`).
 *
 * **Manifest** (`LoraTrainManifest`) — das Trainingspaket, das KosmoTrain
 * schnürt: welcher Adapter, welche Datei(en) mit sha256-Hash (deterministisch
 * nachprüfbar — ändert sich eine Datei, ändert sich ihr Hash, s. Manifest-
 * Hash-Gate in `docs/V082-SPEZ.md` §6.5), welches Rezept (Verweis auf
 * `docs/KOSMOTRAIN.md`/`docs/LORA-KONZEPT.md` mit `§`), welche Eval-Suite,
 * wann erzeugt, und ein **visibility-Deckel** (Owner-Entscheid 1, §0.3: «nur
 * `public` verlässt je das Repo» — sobald eine enthaltene Datei `private`
 * ist, MUSS der Deckel `private` sein, s. `superRefine` unten).
 *
 * **Bericht** (`LoraTrainBerichtV1`) — die verallgemeinerte Form von
 * `LoraTrainBericht` (`packages/kosmo-ai/src/lora-training.ts:156-171`):
 * `adapter, beispiele, verworfen, fingerprint, fake, hinweise` statt der
 * KI4-Feldnamen `anzahlBeispiele/anzahlAussortiert/laufKennzeichen/hinweis`
 * — dieselben Werte, adapterbezogen und plural (`hinweise`), damit ein
 * Bericht unabhängig vom (Fake-)Trainer, der ihn erzeugt hat, gleich
 * aussieht. `fake: true` bleibt für den mitgelieferten `FakeLoraTrainer`
 * verbindlich (Ehrlichkeits-Kern §0.2 — kein Trainings-Versprechen).
 */

/**
 * Die Adapter-Menge aus der Zielkompetenz-Karte (`docs/V082-SPEZ.md` §5.1/
 * §5.2, sechs Zeilen — die zwei zusätzlichen Registry-Zeilen `vis-befehle`
 * und `kosmo-publish-layout` sind KEIN eigener Adapter, s. §5.2 Zeile 7/8,
 * darum hier nicht Teil dieser Menge).
 */
export const LoraTrainAdapterId = z.enum([
  'kosmo-buero',
  'kosmo-zeichner-grundriss',
  'kosmo-zeichner-commands',
  'kosmo-buero-dpo',
  'whisper-ch',
  'kosmo-werkplan',
]);
export type LoraTrainAdapterId = z.infer<typeof LoraTrainAdapterId>;

/** Die drei Datensatz-Schemata aus §3 dieser Spez — eine Manifest-Datei trägt genau eines. */
export const LoraTrainDateiFormat = z.enum(['kosmo-sft/v1', 'kosmo-dpo/v1', 'kosmo-signal/v1']);
export type LoraTrainDateiFormat = z.infer<typeof LoraTrainDateiFormat>;

/** Eine Datensatz-Datei im Paket — Hash ist Pflicht (Manifest-Hash-Gate). */
export const LoraTrainDatei = z.object({
  /** Pfad relativ zum Paket-Root, z.B. `kosmo-buero-sft.jsonl`. */
  pfad: z.string().min(1),
  /** sha256 über den (Text-)Inhalt der Datei, 64 Hex-Zeichen — deterministisch. */
  sha256: z.string().regex(/^[0-9a-f]{64}$/, 'sha256 muss 64 Hex-Zeichen (kleingeschrieben) sein'),
  format: LoraTrainDateiFormat,
  visibility: z.enum(['public', 'private']),
  /** Anzahl JSONL-Zeilen — Plausibilitäts-/Fortschrittsangabe, kein Trainingsfeld. */
  anzahlZeilen: z.number().int().nonnegative().optional(),
});
export type LoraTrainDatei = z.infer<typeof LoraTrainDatei>;

/** Rezept-Referenz MUSS auf `docs/KOSMOTRAIN.md` oder `docs/LORA-KONZEPT.md` mit `§` zeigen. */
const REZEPT_MUSTER = /^docs\/(KOSMOTRAIN|LORA-KONZEPT)\.md §\S/;

export const LoraTrainManifest = z
  .object({
    schema: z.literal('kosmo.lora-train/v1').default('kosmo.lora-train/v1'),
    adapter: LoraTrainAdapterId,
    /** Erzeugungszeitpunkt im Client (ISO). */
    erzeugt_um: z.string().min(1),
    dateien: z.array(LoraTrainDatei).min(1),
    rezept: z
      .string()
      .regex(REZEPT_MUSTER, 'rezept muss auf docs/KOSMOTRAIN.md oder docs/LORA-KONZEPT.md mit § verweisen'),
    /** Pfad-Referenz auf die feste Eval-Prompt-Menge des Adapters (§2.2 `eval/<adapter>/`). */
    evalSuite: z.string().min(1).optional(),
    /** Visibility-Deckel des GESAMTEN Pakets (Owner-Entscheid 1). */
    visibility: z.enum(['public', 'private']),
    /** Ehrlicher Kontext-Satz (z.B. Datenlage, «wartet auf HomeStation»). */
    hinweis: z.string().optional(),
  })
  .superRefine((manifest, ctx) => {
    const enthaeltPrivate = manifest.dateien.some((d) => d.visibility === 'private');
    if (enthaeltPrivate && manifest.visibility !== 'private') {
      ctx.addIssue({
        code: 'custom',
        message:
          'visibility-Deckel muss "private" sein, sobald eine Datei privat ist (Owner-Entscheid 1 — nur public verlässt je das Repo).',
        path: ['visibility'],
      });
    }
  });
export type LoraTrainManifest = z.infer<typeof LoraTrainManifest>;

/**
 * Der verallgemeinerte Bericht — jeder (Fake- oder künftig echte) Trainer
 * liefert diese Form, adapterbezogen. `fake: true` ist beim mitgelieferten
 * `FakeLoraTrainer` verbindlich (kein erfundenes Trainingsergebnis).
 */
export const LoraTrainBerichtV1 = z.object({
  schema: z.literal('kosmo.lora-train-bericht/v1').default('kosmo.lora-train-bericht/v1'),
  adapter: LoraTrainAdapterId,
  /** z.B. `fake-lora-trainer-stub` — Rückverfolgung, welcher Trainer lief. */
  trainerId: z.string().min(1),
  fake: z.boolean(),
  beispiele: z.number().int().nonnegative(),
  verworfen: z.number().int().nonnegative(),
  /** Reproduzierbarer Fingerabdruck des Laufs — kein Modellgewicht, keine Datei. */
  fingerprint: z.string().min(1),
  /** Mindestens ein ehrlicher Hinweis (z.B. Fake-Kennzeichnung). */
  hinweise: z.array(z.string()).min(1),
  erzeugt_um: z.string().min(1),
});
export type LoraTrainBerichtV1 = z.infer<typeof LoraTrainBerichtV1>;
