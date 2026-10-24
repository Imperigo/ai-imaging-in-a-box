/**
 * EINZAHL BEI EINS — Zahl und Wort in einem Satz der Knotenansicht.
 *
 * Die Demo rechnet meist mit einer Kamera und einem Bild; dort stand «Gewählt: 1 Bilder», «1 warten auf
 * Freigabe» und «Szene: 1 Bauteile». `mitZahl(n, 'Bild', 'Bilder')` sagt «1 Bild», «0 Bilder», «3 Bilder» —
 * ein Wort für eins, eins für alles andere (auch null). Dieselbe Form taugt für Verben:
 * `mitZahl(n, 'wartet', 'warten')` → «1 wartet», «2 warten». Probe `kv-einzahl.test.ts`.
 */
export function mitZahl(n: number, eins: string, mehr: string): string {
  return `${n} ${n === 1 ? eins : mehr}`;
}
