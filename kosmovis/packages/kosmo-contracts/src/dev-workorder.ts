import { z } from 'zod';

/**
 * kosmodev.workorder/v1 — der Vertrag, der den KosmoDev-Kreis schliesst
 * (V2-Technik Block 2, Buildplan E2). Der Owner erfasst Aufträge in der App,
 * übergibt sie als Workorder an die Bridge (Job-Typ `dev-`), ein Dev-Worker
 * (Claude Code an der HomeStation) holt sie per claim→result ab. Die Bridge
 * speichert und vermittelt NUR Text — sie führt nie Code aus.
 *
 * Bewusst OHNE `awaiting_approval`: eine Workorder kostet keine GPU, und ihr
 * Absenden IST bereits die explizite Owner-Handlung (Knopf in KosmoDev).
 */

/** Ein Auftrag, 1:1 die Felder des App-Auftragsbuchs (state/auftragsbuch.ts). */
export const WorkorderAuftrag = z.object({
  id: z.string().min(1),
  /** Erfassungszeitpunkt (ISO). */
  ts: z.string(),
  text: z.string().min(1),
  quelle: z.enum(['gesprochen', 'getippt', 'kosmo']),
  /** Station, in der der Owner bei der Erfassung war (Kontext-Pin). */
  station: z.string(),
  /** Optionaler Ort-Hinweis («wo» — z. B. «Werkzeugleiste»). */
  ort: z.string().optional(),
});
export type WorkorderAuftrag = z.infer<typeof WorkorderAuftrag>;

/** Die Workorder-Hülle, die der Client an POST /jobs/dev schickt. */
export const Workorder = z.object({
  schema: z.literal('kosmodev.workorder/v1').default('kosmodev.workorder/v1'),
  projekt: z.string().min(1),
  /** Erzeugungszeitpunkt im Client (ISO). */
  erzeugt_um: z.string(),
  auftraege: z.array(WorkorderAuftrag).min(1).max(200),
});
export type Workorder = z.infer<typeof Workorder>;

export const DevJobStatus = z.enum(['queued', 'running', 'done', 'error', 'cancelled']);
export type DevJobStatus = z.infer<typeof DevJobStatus>;

/** Ergebnis je Auftrag — der Rückkanal des Workers. Ehrlichkeits-Kante (E5):
 * ein Fake-Worker meldet zwingend `umgesetzt: false` + Simulation-Notiz und
 * erfindet NIE einen `commit` (Belege werden nicht gefakt — Blender-Regel). */
export const AuftragErgebnis = z.object({
  auftrag_id: z.string().min(1),
  umgesetzt: z.boolean(),
  /** Beleg der echten Arbeit (Commit-Hash/Link) — nur wenn wirklich passiert. */
  commit: z.string().optional(),
  notiz: z.string().optional(),
});
export type AuftragErgebnis = z.infer<typeof AuftragErgebnis>;

/** Das Result, das der Worker an POST /jobs/dev/{id}/result meldet. */
export const DevJobResult = z.object({
  /** Wer gearbeitet hat — Pflicht, damit «Simulation» sichtbar bleibt. */
  worker: z.string().min(1),
  abgeschlossen_um: z.string(),
  ergebnisse: z.array(AuftragErgebnis).min(1),
});
export type DevJobResult = z.infer<typeof DevJobResult>;

/** Der Dev-Job-Record im Bridge-Store (GET /jobs/dev, GET /jobs/dev/{id}). */
export const DevJob = z.object({
  job_id: z.string().regex(/^dev-\d+-[0-9a-f]{6}$/),
  status: DevJobStatus,
  kind: z.literal('dev-workorder').default('dev-workorder'),
  created_at: z.string(),
  updated_at: z.string().optional(),
  projekt: z.string().optional(),
  /** Zahl der übergebenen Aufträge — der Client zeigt sie, Tests asserten sie. */
  anzahl_auftraege: z.number().int().min(0),
  /** Wer den Job per claim übernommen hat (sichtbar im Client). */
  worker: z.string().optional(),
  /** Ehrliche Begründung, v. a. bei `error`. */
  message: z.string().optional(),
  result: DevJobResult.optional(),
});
export type DevJob = z.infer<typeof DevJob>;

/** Claim-Request des Workers — setzt `running` + `worker` (verhindert
 * Doppelarbeit; normatives Protokoll in tools/homestation-bridge/README.md). */
export const DevJobClaim = z.object({
  worker: z.string().min(1),
});
export type DevJobClaim = z.infer<typeof DevJobClaim>;
