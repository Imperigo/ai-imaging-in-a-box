import type { MassBody } from '../model/entities';

/**
 * B9 (Owner-Entscheid 06.10.2026, Teil b): die EINE Regel, woran ein
 * Bestandskörper (Umgebung/Nachbar, z. B. aus dem Splat) erkannt wird.
 *
 * WARUM `program: 'bestand'` und nicht `meta.renovation`: `renovation`
 * meint den Umbau-Status EIGENER Bauteile (SIA 400: Bestand grau, Neu rot,
 * Abbruch gelb) — ein Nachbarhaus wird nicht umgebaut. Und `program` ist das
 * Feld, nach dem GF, Berechnungsliste und KV ohnehin gruppieren; dort muss
 * der Bestand heraus, sonst rechnet der Kostenvoranschlag die Nachbarschaft
 * als eigenes Gebäude.
 *
 * Eigene Datei OHNE Einfuhren, weil `sia416.ts`, `berechnungsliste.ts`,
 * `schwarzplan.ts`, `checks.ts` und `ausnuetzungsnachweis.ts` sie alle lesen
 * und `derive/bestand.ts` seinerseits `sia416.ts` braucht — ein Ring wäre
 * die Folge, stünde die Regel dort.
 */
export const BESTAND_PROGRAMM = 'bestand';

export function istBestandVolumen(m: Pick<MassBody, 'program'>): boolean {
  return m.program === BESTAND_PROGRAMM;
}
