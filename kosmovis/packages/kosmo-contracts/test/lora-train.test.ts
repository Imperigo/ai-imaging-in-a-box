import { describe, expect, it } from 'vitest';
import { LoraTrainAdapterId, LoraTrainBerichtV1, LoraTrainManifest } from '../src';

const HASH_A = 'a'.repeat(64);
const HASH_B = 'b'.repeat(64);

function basisManifest(overrides: Partial<Parameters<typeof LoraTrainManifest.parse>[0]> = {}) {
  return {
    adapter: 'kosmo-buero',
    erzeugt_um: '2026-07-17T09:00:00.000Z',
    dateien: [{ pfad: 'kosmo-buero-sft.jsonl', sha256: HASH_A, format: 'kosmo-sft/v1', visibility: 'private' }],
    rezept: 'docs/KOSMOTRAIN.md §3',
    evalSuite: 'wissen/training/eval/kosmo-buero/',
    visibility: 'private',
    ...overrides,
  };
}

describe('kosmo.lora-train/v1 — Manifest', () => {
  it('akzeptiert ein vollständiges Manifest und füllt das Schema-Literal', () => {
    const m = LoraTrainManifest.parse(basisManifest());
    expect(m.schema).toBe('kosmo.lora-train/v1');
    expect(m.adapter).toBe('kosmo-buero');
    expect(m.dateien[0]?.sha256).toBe(HASH_A);
  });

  it('kennt die sechs Adapter aus der Zielkompetenz-Karte (§5.1)', () => {
    expect(LoraTrainAdapterId.options).toEqual([
      'kosmo-buero',
      'kosmo-zeichner-grundriss',
      'kosmo-zeichner-commands',
      'kosmo-buero-dpo',
      'whisper-ch',
      'kosmo-werkplan',
    ]);
    expect(() => LoraTrainManifest.parse(basisManifest({ adapter: 'kosmo-unbekannt' }))).toThrow();
  });

  it('verweigert einen ungültigen sha256 (nicht 64 Hex-Zeichen)', () => {
    expect(() =>
      LoraTrainManifest.parse(
        basisManifest({
          dateien: [{ pfad: 'x.jsonl', sha256: 'nicht-hex', format: 'kosmo-sft/v1', visibility: 'private' }],
        }),
      ),
    ).toThrow();
  });

  it('verweigert eine Rezept-Referenz ohne docs/KOSMOTRAIN.md bzw. docs/LORA-KONZEPT.md + §', () => {
    expect(() => LoraTrainManifest.parse(basisManifest({ rezept: 'irgendein Rezept' }))).toThrow();
    expect(() => LoraTrainManifest.parse(basisManifest({ rezept: 'docs/KOSMOTRAIN.md' }))).toThrow();
    expect(LoraTrainManifest.parse(basisManifest({ rezept: 'docs/LORA-KONZEPT.md §1.3' })).rezept).toBe(
      'docs/LORA-KONZEPT.md §1.3',
    );
  });

  it('verweigert ein leeres Dateien-Array (mindestens eine Datei nötig)', () => {
    expect(() => LoraTrainManifest.parse(basisManifest({ dateien: [] }))).toThrow();
  });

  it('Owner-Entscheid 1: visibility-Deckel muss "private" sein, sobald eine Datei privat ist', () => {
    expect(() =>
      LoraTrainManifest.parse(
        basisManifest({
          visibility: 'public',
          dateien: [{ pfad: 'x.jsonl', sha256: HASH_A, format: 'kosmo-sft/v1', visibility: 'private' }],
        }),
      ),
    ).toThrow();
    // sind ALLE Dateien public, darf der Deckel public sein:
    const oeffentlich = LoraTrainManifest.parse(
      basisManifest({
        visibility: 'public',
        dateien: [{ pfad: 'x.jsonl', sha256: HASH_A, format: 'kosmo-sft/v1', visibility: 'public' }],
      }),
    );
    expect(oeffentlich.visibility).toBe('public');
  });

  it('Manifest-Hash-Gate: zwei Dateien mit unterschiedlichem Inhalt tragen unterschiedliche Hashes', () => {
    const m = LoraTrainManifest.parse(
      basisManifest({
        dateien: [
          { pfad: 'a.jsonl', sha256: HASH_A, format: 'kosmo-sft/v1', visibility: 'private' },
          { pfad: 'b.jsonl', sha256: HASH_B, format: 'kosmo-sft/v1', visibility: 'private' },
        ],
      }),
    );
    expect(m.dateien[0]?.sha256).not.toBe(m.dateien[1]?.sha256);
  });
});

describe('kosmo.lora-train-bericht/v1 — verallgemeinerter Bericht', () => {
  const basisBericht = {
    adapter: 'kosmo-buero' as const,
    trainerId: 'fake-lora-trainer-stub',
    fake: true,
    beispiele: 3,
    verworfen: 1,
    fingerprint: 'fake-lora-abc123',
    hinweise: ['Fake-Trainer-Stub (kein echtes Training, keine GPU) — 3 Beispiel(e) verarbeitet.'],
    erzeugt_um: '2026-07-17T09:00:00.000Z',
  };

  it('akzeptiert einen vollständigen Bericht und füllt das Schema-Literal', () => {
    const b = LoraTrainBerichtV1.parse(basisBericht);
    expect(b.schema).toBe('kosmo.lora-train-bericht/v1');
    expect(b.fake).toBe(true);
    expect(b.hinweise).toHaveLength(1);
  });

  it('verweigert einen Bericht ohne mindestens einen Hinweis', () => {
    expect(() => LoraTrainBerichtV1.parse({ ...basisBericht, hinweise: [] })).toThrow();
  });

  it('verweigert negative Zähler (beispiele/verworfen)', () => {
    expect(() => LoraTrainBerichtV1.parse({ ...basisBericht, beispiele: -1 })).toThrow();
    expect(() => LoraTrainBerichtV1.parse({ ...basisBericht, verworfen: -1 })).toThrow();
  });

  it('ein echter (nicht-fake) Trainer ist ebenso darstellbar — kein Fake-Zwang im Schema selbst', () => {
    const b = LoraTrainBerichtV1.parse({ ...basisBericht, fake: false, trainerId: 'homestation-unsloth' });
    expect(b.fake).toBe(false);
  });
});
