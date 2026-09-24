import { z } from 'zod';

/**
 * .kosmo-Projektpaket — das universelle Austauschformat (Zip).
 * Kompatibel gedacht zur kosmo.project.json-Kultur des bestehenden
 * examples/kosmo-projects/kosmo-demo-001 (Module, review_gates, rights_status).
 */

export const ReviewGate = z.object({
  enabled: z.boolean().default(false),
  requires_human_approval: z.boolean().default(true),
});

/**
 * Herkunfts-Fingerprint (Anti-Copy Stufe 1) — additiv im Manifest, NIE im
 * Modell selbst (s. `apps/kosmo-orbit/src/state/herkunft.ts`, `interface
 * Herkunft`, das dieses Schema spiegelt). Der Vertrag lebt bewusst hier
 * gleich mit, statt nur app-seitig zu existieren (P-PAKETWAHRHEIT,
 * `auftraege/von-homestation/auf-orbit-20260827-12.md` Posten 2): vorher
 * baute `packProject` das Manifest als Objektliteral OHNE `KosmoProjectManifest`
 * zu durchlaufen — ein `herkunft`-Feld, das der (damals ungenutzte) Vertrag
 * nicht kannte, wäre bei einem `.parse()` als unbekannter Schlüssel
 * stillschweigend abgeschnitten worden. Jetzt gehört es zum Vertrag, kann
 * also nicht mehr wegdriften.
 */
export const KosmoHerkunft = z.object({
  editionId: z.string(),
  exportedAt: z.string(),
  docHash: z.string(),
});
export type KosmoHerkunft = z.infer<typeof KosmoHerkunft>;

export const KosmoProjectManifest = z.object({
  /** PFLICHT — bewusst OHNE `.default(...)` (auf-orbit-20260828-16, Posten
   *  11). Ein `.default()` macht das Feld beim LESEN optional: ein Manifest
   *  ganz ohne `schema` würde stillschweigend als v1 durchgewunken — genau
   *  die Stelle, an der eine künftige v2 unbemerkt als v1 gelesen würde. Der
   *  Schreibpfad (`apps/kosmo-orbit/src/state/project-io.ts`, `packProject`)
   *  braucht den Default nicht: er übergibt `schema` an `.parse(...)` immer
   *  ausdrücklich. Nur der Lesepfad (`parseKosmoPaket`, `.safeParse(...)`)
   *  bekam den Default zu sehen — dort war er falsch. */
  schema: z.literal('kosmo.project/v1'),
  id: z.string(),
  name: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  location: z
    .object({
      address: z.string().optional(),
      canton: z.string().optional(),
      coordinates: z.tuple([z.number(), z.number()]).optional(),
    })
    .optional(),
  // Alle acht SIA-Teilphasen des Kernels (`SiaPhase` in
  // `packages/kosmo-kernel/src/model/doc.ts`). Bis 08.09.2026 kannte diese
  // Aufzaehlung nur fuenf; `strategie`, `ausschreibung` und `abnahme` fielen
  // beim Export still auf den Vorgabewert `'wettbewerb'` zurueck — das
  // Manifest behauptete dann einen Projektstand, den das Projekt nicht hat.
  // `baueingabe` ist die einzige bewusste Umbenennung: der Kernel nennt
  // dieselbe Sache `bewilligung` und fuehrt sie im eigenen Kommentar
  // woertlich als «Baugesuch». Erweiterung ist additiv — jedes bisher
  // geschriebene Manifest bleibt lesbar.
  phase: z
    .enum([
      'strategie',
      'wettbewerb',
      'vorprojekt',
      'baueingabe',
      'bauprojekt',
      'ausschreibung',
      'ausfuehrung',
      'abnahme',
    ])
    .default('wettbewerb'),
  modules: z
    .object({
      prepare: z.boolean().default(true),
      design: z.boolean().default(true),
      data: z.boolean().default(true),
      vis: z.boolean().default(true),
      publish: z.boolean().default(true),
    })
    .prefault({}),
  review_gates: z
    .object({
      public_release: ReviewGate.default({ enabled: false, requires_human_approval: true }),
      external_upload: ReviewGate.default({ enabled: false, requires_human_approval: true }),
      paid_cloud_job: ReviewGate.default({ enabled: true, requires_human_approval: true }),
    })
    .prefault({}),
  /** Dateien im Paket, relativ zum Zip-Root. */
  contents: z
    .object({
      model: z.string().default('model/model.json'),
      journal: z.string().default('memory/journal.jsonl'),
      brief: z.string().optional(),
      ifc: z.string().optional(),
      assets_dir: z.string().default('assets/'),
      plans_dir: z.string().default('plans/'),
      renders_dir: z.string().default('renders/'),
    })
    .prefault({}),
  /** s. `KosmoHerkunft` oben — nur gesetzt, wenn der Schreiber (`packProject`)
   *  eine Herkunftskennung mitgibt; ein von Hand gebautes/älteres Manifest
   *  ohne dieses Feld bleibt gültig. */
  herkunft: KosmoHerkunft.optional(),
});
export type KosmoProjectManifest = z.infer<typeof KosmoProjectManifest>;
