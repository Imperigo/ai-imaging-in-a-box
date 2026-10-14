// auf-248 (07.10.2026): Die Brücke trägt bei jeder Übernahme `worker` und
// `worker_seit` ein; leitet sie den Abholer ab, markiert sie das mit
// `worker_quelle: 'abgeleitet'`. Ohne diese Vertragsfelder streift zod sie in
// der App stumm ab (E76-Warnung) — die Herkunft käme nie an.
import { describe, expect, it } from 'vitest';
import { BakeJob, BlenderSimJob, DevJob, RenderJob, VideoSplatJob, unbekannteFelder } from '../src';

const SEIT = '2026-10-07T07:00:00+00:00';

describe('auf-248 — worker/worker_seit/worker_quelle im Job-Record', () => {
  it('RenderJob: gemeldeter Worker mit worker_seit bleibt vollständig', () => {
    const roh = {
      job_id: 'vis-1791357460-e8cc6e',
      status: 'running',
      scene: 'render-scene.json',
      created_at: SEIT,
      worker: 'abholer',
      worker_seit: SEIT,
    };
    const job = RenderJob.parse(roh);
    expect(job.worker).toBe('abholer');
    expect(job.worker_seit).toBe(SEIT);
    expect(unbekannteFelder(roh, job)).toEqual([]);
  });

  it('RenderJob: abgeleiteter Abholer ohne worker_seit', () => {
    const roh = {
      job_id: 'vis-1791357460-e8cc6e',
      status: 'done',
      scene: 'render-scene.json',
      created_at: SEIT,
      worker: 'abholer',
      worker_quelle: 'abgeleitet',
    };
    const job = RenderJob.parse(roh);
    expect(job.worker_quelle).toBe('abgeleitet');
    expect(job.worker_seit).toBeUndefined();
    expect(unbekannteFelder(roh, job)).toEqual([]);
  });

  it('RenderJob: unbekannte worker_quelle wird abgewiesen, alte Records bleiben gültig', () => {
    expect(
      RenderJob.safeParse({
        job_id: 'vis-1791357460-e8cc6e',
        status: 'done',
        scene: 's',
        created_at: SEIT,
        worker_quelle: 'geraten',
      }).success,
    ).toBe(false);
    const alt = RenderJob.parse({ job_id: 'vis-1791357460-e8cc6e', status: 'queued', scene: 's', created_at: SEIT });
    expect(alt.worker).toBeUndefined();
    expect(alt.worker_seit).toBeUndefined();
  });

  it('VideoSplatJob, BakeJob, BlenderSimJob, DevJob tragen worker_seit', () => {
    const splat = VideoSplatJob.parse({
      job_id: 'vsplat-1-abcdef',
      status: 'running',
      created_at: SEIT,
      worker: 'splat-worker',
      worker_seit: SEIT,
    });
    expect(splat.worker_seit).toBe(SEIT);
    const bake = BakeJob.parse({
      job_id: 'bake-1-abcdef',
      status: 'kein-blender-worker',
      scene: 's',
      created_at: SEIT,
      worker: 'blender-worker-fake',
      worker_seit: SEIT,
    });
    expect(bake.worker_seit).toBe(SEIT);
    const sim = BlenderSimJob.parse({
      job_id: 'bsim-1-abcdef',
      status: 'kein-blender-worker',
      art: 'wind',
      scene: 's',
      created_at: SEIT,
      worker: 'blender-worker-fake',
      worker_seit: SEIT,
    });
    expect(sim.worker_seit).toBe(SEIT);
    const dev = DevJob.parse({
      job_id: 'dev-1-abcdef',
      status: 'running',
      created_at: SEIT,
      anzahl_auftraege: 1,
      worker: 'claude-code',
      worker_seit: SEIT,
    });
    expect(dev.worker_seit).toBe(SEIT);
  });
});
