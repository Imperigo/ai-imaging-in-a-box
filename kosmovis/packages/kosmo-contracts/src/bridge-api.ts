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
  /**
   * kv-abholer-puls (Antwortblatt `auftraege/ergebnisse/auf-20260924-171-
   * antwort-vier-punkte-k1-bis-k4.md` K2): Lebenszeichen des Abholers der
   * Gegenseite, gerechnet von der Bruecke aus `abholer-puls.json` in der
   * Job-Ablage. Form nach dem gemessenen Beispiel
   * (`docs/auftraege-kosmovis/erg-20260929-e124-beispiele-und-glas.md` §5).
   * Fehlt im Fake-Modus ganz (dort arbeitet kein Abholer, ein `nie_gesehen`
   * waere ein falscher Alarm). Bei `nie_gesehen` stehen `zuletzt` und
   * `alter_s` als `null` da (E123: annehmen, als «nicht bekannt» lesen) und
   * `letzter_durchgang` fehlt. Wahrheit ist `alter_s`, nicht `frist_s`.
   */
  abholer: z
    .object({
      zustand: z.enum(['nie_gesehen', 'arbeitet', 'steht', 'wartet', 'laeuft_leer']),
      zuletzt: z.string().nullable(),
      alter_s: z.number().nullable(),
      frist_s: z.number(),
      letzter_durchgang: z
        .object({
          gesehen: z.number().int().min(0),
          verarbeitet: z.number().int().min(0),
          liegengelassen: z.number().int().min(0),
          fehler: z.number().int().min(0),
          waisen: z.number().int().min(0),
        })
        .optional(),
      grund: z.string(),
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

/**
 * B5 (06.10.2026) — die Felder, die der Splat-Worker der Brücke schreibt
 * (`tools/homestation-bridge/kosmo_bridge/splat_worker.py`, Funktion
 * `_bearbeite`). WARUM im Vertrag: zod streifte sie bisher still ab — die App
 * sah weder Stufe noch Ergebnis und konnte das `.ply` nicht holen.
 */
export const VideoSplatProgress = z.object({
  /** `start`, `dfisheye`, die STAGE-Namen der Kette (`frame_extraction` …
   *  `brush_training`) oder `fertig`. Offen als Text: neue Stufen der Kette
   *  sollen die App nicht brechen. */
  phase: z.string(),
  pct: z.number().min(0).max(1),
  /** Das Wort für die Anzeige, z. B. «Bilder abgleichen (COLMAP)». */
  stufe: z.string(),
});
export type VideoSplatProgress = z.infer<typeof VideoSplatProgress>;

export const VideoSplatMeta = z
  .object({
    quelle: z.string().optional(),
    fps: z.number().optional(),
    /** `perspektiv` | `equirect` | `dual-fisheye` (B4) — der Worker liest es
     *  (`ist_dual_fisheye`, `videoquelle_aus_meta`). Als Text, weil der
     *  Worker auch Synonyme versteht. */
    projektion: z.string().optional(),
    frameCount: z.number().int().optional(),
    /** splat-video2: Dauer laut Browser (s) — nur Anzeige; die Brücke misst selbst. */
    dauerS: z.number().optional(),
  })
  .passthrough();
export type VideoSplatMeta = z.infer<typeof VideoSplatMeta>;

/** `kosmo.splat-result/v1` — `splat-result.json` im Jobordner. Das `.ply`
 *  selbst holt die App über `bridgeRoutes.jobArtifact(id, ply)`. */
export const SplatResult = z.object({
  schema: z.literal('kosmo.splat-result/v1'),
  job_id: z.string().optional(),
  /** Dateiname des Artefakts im Jobordner (heute immer `splat.ply`). */
  ply: z.string().min(1),
  /** Zahl der Gaussians laut PLY-Kopf. */
  count: z.number().int().min(0),
  bytes: z.number().int().min(0),
  /** Besteht der Kopf die Regeln von `splat-import.ts::parsePlyGaussian`? */
  app_lesbar: z.boolean(),
  /** Warum nicht — `null`/fehlend, wenn lesbar. */
  app_grund: z.string().nullable().optional(),
  videoquelle: z.enum(['standard', 'insta360']).optional(),
  frames_eingang: z.number().int().min(0).optional(),
  /** `null`, wenn die Nachlese der Kette nichts liefert (gemessen möglich). */
  bilder_gesamt: z.number().int().min(0).nullable().optional(),
  bilder_registriert: z.number().int().min(0).nullable().optional(),
  dauer_s: z.number().min(0).optional(),
  kette: z.string().optional(),
  protokoll: z.string().optional(),
  // splat-video2 (06.10.2026), Video-Weg über `tools/splat_kette.py` — alles
  // optional, ein Ergebnis des Bilder-Wegs bleibt gültig.
  /** `standard` | `insta360` | `insv` — die Quelle, mit der die Kette rechnete.
   *  `videoquelle` oben bleibt im alten Wertebereich (360-Zweig = insta360). */
  kette_quelle: z.string().optional(),
  /** Zahl der COLMAP-Teilmodelle — mehr als 1 heisst: Weg nicht zusammenhängend. */
  modelle: z.number().int().min(0).nullable().optional(),
  /** Punkte der SfM-Rekonstruktion (nicht der Gaussians). */
  punkte_sfm: z.number().int().min(0).nullable().optional(),
  schleifenschluss: z.boolean().nullable().optional(),
  bildplan: z.lazy(() => VideoSplatBildplan).optional(),
  /** Woher die Linsenwinkel kamen (gemessen / Vorgabe mit Grund). */
  linsen_quelle: z.string().nullable().optional(),
  /** Hinweise der Kette (Abdeckung, max-res gedeckelt, Schleifenschluss …). */
  hinweise: z.array(z.string()).optional(),
});
export type SplatResult = z.infer<typeof SplatResult>;

/**
 * splat-video2 (06.10.2026, N2) — wie viele Bilder die Brücke aus dem Video
 * zieht: aus der DAUER (`splat_worker.py::bildplan`), nicht fest. `max_frames`
 * gilt je Ansicht; ein 360°-Zeitpunkt hat vier Ansichten (`bilder`).
 */
export const VideoSplatBildplan = z
  .object({
    dauer_s: z.number().nullable().optional(),
    fps: z.number().positive(),
    max_frames: z.number().int().min(1),
    zeitpunkte: z.number().int().min(1),
    ansichten: z.number().int().min(1).optional(),
    bilder: z.number().int().min(1).optional(),
    kette_quelle: z.string().optional(),
  })
  .passthrough();
export type VideoSplatBildplan = z.infer<typeof VideoSplatBildplan>;

/**
 * splat-video2 (06.10.2026, N9) — WARUM eine Kette ohne Splat endete, aus dem
 * Protokoll gelesen (`splat_worker.py::kette_diagnose`). Vorher stand nur
 * «Kette endete mit Code 101 ohne splat.ply».
 */
export const VideoSplatDiagnose = z
  .object({
    bilder: z.number().int().min(0).nullable().optional(),
    /** registrierte Bilder je COLMAP-Teilmodell `sparse/N`, in Reihenfolge. */
    teilmodelle: z.array(z.number().int().min(0)).optional(),
    brush_absturz: z.string().nullable().optional(),
    fail: z.string().nullable().optional(),
    abgelehnt: z.string().nullable().optional(),
    code: z.number().int().nullable().optional(),
    /** Der Grund als Satz — steht auch in `message`. */
    satz: z.string(),
    /** Was der Architekt ändern kann (z. B. «mehr Bilder wählen»). */
    rat: z.string().optional(),
  })
  .passthrough();
export type VideoSplatDiagnose = z.infer<typeof VideoSplatDiagnose>;

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
  /** Ehrliche Begründung, v. a. bei `kein-sfm-worker`; beim Lauf die Stufe
   *  («rechnet: …»), bei `done` die Zusammenfassung des Splat-Workers. */
  message: z.string().optional(),
  worker: z.string().optional(),
  /** auf-248: Zeitpunkt der Übernahme (ISO-8601), von der Brücke bzw. vom
   * Worker gesetzt. Fehlt, wenn die Brücke den Worker nur ableitet. */
  worker_seit: z.string().optional(),
  /** B5: was die App beim Anlegen als `meta` schickte — die Brücke legt es
   *  unverändert in `job.json`. Locker (`passthrough`), weil der Inhalt vom
   *  Client stammt; geprüft werden nur die Felder, die der Worker liest. */
  meta: VideoSplatMeta.optional(),
  /** B5: Stand der Kette (Splat-Worker). `pct` 0…1 ist eine grobe Schätzung
   *  je Stufe — exakt ist nur `1` bei `done`. */
  progress: VideoSplatProgress.optional(),
  /** B5: welcher Zweig der Kette rechnet — `insta360` = 360°-Rig. */
  videoquelle: z.enum(['standard', 'insta360']).optional(),
  /** B5: Prozessgruppe der laufenden Kette (nur während `running`). */
  kette_pid: z.number().int().optional(),
  gestartet_at: z.string().optional(),
  /** B5: eingebettet aus `splat-result.json`, sobald der Worker fertig ist. */
  result: SplatResult.optional(),
  // splat-video2 (06.10.2026) — rückwärtsverträglich, alles optional.
  /** `video`: die App schickte das Video, die Brücke zieht die Bilder selbst. */
  eingang: z.enum(['bilder', 'video']).optional(),
  /** Verweis auf das hochgeladene Video (Name, Grösse) — die Datei selbst
   *  löscht der Worker nach dem Lauf (`video_geloescht`). */
  video: z.object({ datei: z.string(), name: z.string(), bytes: z.number().int().min(0) }).passthrough().optional(),
  video_geloescht: z.boolean().optional(),
  bildplan: VideoSplatBildplan.optional(),
  diagnose: VideoSplatDiagnose.optional(),
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
