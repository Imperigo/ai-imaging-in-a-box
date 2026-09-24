import { z } from 'zod';

/**
 * Kosmo-Bridge — HTTP-API des HomeStation-Servers (tools/homestation-bridge).
 * Die Bridge ist die einzige Naht zwischen KosmoOrbit (Desktop/iPad) und der
 * lokalen Pipeline: Render-Job-Store, Whisper-STT, TTS, Ollama-Proxy,
 * IFC-Validierung. Token-geschützt, nur Büronetz.
 */

export const BridgeHealth = z.object({
  ok: z.boolean(),
  version: z.string(),
  services: z.object({
    jobstore: z.boolean(),
    ollama: z.boolean(),
    stt: z.boolean(),
    tts: z.boolean(),
    // Die Bridge liefert `embed` längst — der Contract zog nach (V2-Technik
    // Block 1). Optional, damit ältere Health-Antworten weiter parsen.
    embed: z.boolean().optional(),
  }),
  /**
   * GPU-Status. Auf der echten HomeStation aus nvidia-smi; im Fake-Modus
   * ehrlich als Simulation benannt (`name: "fake-gpu (Simulation)"`). Fehlt
   * ganz, wenn keine GPU/kein Fake-Gate aktiv ist — nie vorgetäuscht.
   */
  gpu: z
    .object({
      name: z.string().optional(),
      idle: z.boolean().optional(),
    })
    .optional(),
});
export type BridgeHealth = z.infer<typeof BridgeHealth>;

export const SttResponse = z.object({
  text: z.string(),
  /** Roh-Transkript vor der Normalisierung (CH-Dialekt-Hypothese). */
  raw: z.string().optional(),
  language: z.string().optional(),
  duration_s: z.number().optional(),
});
export type SttResponse = z.infer<typeof SttResponse>;

export const TtsRequest = z.object({
  text: z.string().min(1).max(4000),
  voice: z.string().default('kosmo-de'),
  speed: z.number().min(0.5).max(2).default(1),
});
export type TtsRequest = z.infer<typeof TtsRequest>;

export const IfcValidationResult = z.object({
  valid: z.boolean(),
  schema: z.string().optional(),
  element_counts: z.record(z.string(), z.number()).optional(),
  errors: z.array(z.string()).default([]),
  warnings: z.array(z.string()).default([]),
});
export type IfcValidationResult = z.infer<typeof IfcValidationResult>;

/** Embedding (bge-m3) — der RAG-Pfad von KosmoPrepare (E3). */
export const EmbedRequest = z.object({
  texts: z.array(z.string().min(1)).min(1).max(256),
});
export type EmbedRequest = z.infer<typeof EmbedRequest>;

export const EmbedResponse = z.object({
  vectors: z.array(z.array(z.number())).min(1),
  model: z.string().optional(),
});
export type EmbedResponse = z.infer<typeof EmbedResponse>;

/**
 * Video→Splat-Job-Record. Eigenes Schema (NICHT die `vis-`-Regex von
 * RenderJob aufweichen): Präfix `vsplat-`. Die Bridge extrahiert nur die
 * Frames und übergibt ehrlich — ohne SfM-Worker endet der Job beweisbar als
 * `kein-sfm-worker` mit Begründung, NIE als vorgetäuschter Splat.
 */
export const VideoSplatJobStatus = z.enum([
  // `awaiting_approval` (additiv, HS3-Nachbesserung/Fable-Auflage 4): auch
  // Video→Splat ist rechenintensiv — bei aktiver Freigabe-Pflicht wartet der
  // Job auf ein explizites /approve, bevor ein echter SfM-Worker ihn nimmt.
  'awaiting_approval',
  'queued',
  'running',
  'done',
  'error',
  'cancelled',
  'kein-sfm-worker',
]);
export type VideoSplatJobStatus = z.infer<typeof VideoSplatJobStatus>;

export const VideoSplatJob = z.object({
  job_id: z.string().regex(/^vsplat-\d+-[0-9a-f]{6}$/),
  status: VideoSplatJobStatus,
  kind: z.literal('video-splat').default('video-splat'),
  /** Freigabe-Token bei aktiver Freigabe-Pflicht (Symmetrie zu RenderJob). */
  approval_token: z.string().optional(),
  created_at: z.string(),
  updated_at: z.string().optional(),
  /** Zahl der lokal extrahierten Frames — die Bridge schreibt es, der Client
   * zeigt es, `sim-ki-imaging` assertet es (Fable-Review-1). */
  frame_count: z.number().int().optional(),
  /** Ehrliche Begründung, v. a. bei `kein-sfm-worker`. */
  message: z.string().optional(),
  worker: z.string().optional(),
});
export type VideoSplatJob = z.infer<typeof VideoSplatJob>;

/** Pfade der Bridge-Endpoints — eine Quelle für Client UND Server-Tests. */
export const bridgeRoutes = {
  health: '/health',
  jobs: '/jobs',
  job: (id: string) => `/jobs/${id}`,
  jobArtifact: (id: string, name: string) => `/jobs/${id}/artifacts/${name}`,
  /** Freigabe eines wartenden Jobs (nur bei aktiver Freigabe-Pflicht) —
   * braucht den `approval_token` aus dem Create-Response. */
  jobApprove: (id: string) => `/jobs/${id}/approve`,
  /** Kooperativer Abbruch: awaiting_approval/queued sofort, running vor dem
   * nächsten teuren Schritt. */
  jobCancel: (id: string) => `/jobs/${id}/cancel`,
  /** Blender-Simulation (Wind/Sonne/Gebäude) — ohne Blender-Worker endet der
   * Job als `kein-blender-worker` (Physik wird NIE gefakt). */
  jobsBlenderSim: '/jobs/blender-sim',
  /** Textur-Bake (Smart-UV-Unwrap + AO-Bake) — ohne Blender-Worker endet der
   * Job als `kein-blender-worker` (eine Geometrie-Optimierungs-Behauptung
   * wird NIE gefakt, v0.8.9 §9 E9, Sanktion 12). */
  jobsBake: '/jobs/bake',
  /** Video→Splat: ehrliche Übergabe der lokal extrahierten Frames — keine
   * SfM-Optimierung in der Bridge selbst (siehe kosmo_bridge/main.py). */
  jobsVideoSplat: '/jobs/video-splat',
  /** KosmoDev-Workorders (kosmodev.workorder/v1, Block 2): die Bridge nimmt
   * Auftrags-Text an und vermittelt ihn an einen Dev-Worker — sie führt NIE
   * selbst Code aus. Lebenszyklus queued→running→done|error|cancelled. */
  jobsDev: '/jobs/dev',
  jobDev: (id: string) => `/jobs/dev/${id}`,
  /** Worker übernimmt den Job (setzt running + worker — verhindert Doppelarbeit). */
  jobDevClaim: (id: string) => `/jobs/dev/${id}/claim`,
  /** Worker meldet das Ergebnis (DevJobResult) — done oder error. */
  jobDevResult: (id: string) => `/jobs/dev/${id}/result`,
  jobDevCancel: (id: string) => `/jobs/dev/${id}/cancel`,
  stt: '/stt',
  tts: '/tts',
  ollama: '/ollama',
  validateIfc: '/validate-ifc',
  embed: '/embed',
} as const;
