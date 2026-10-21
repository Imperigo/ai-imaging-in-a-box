/**
 * STELLVERTRETER (Visbox) (KI-Bedienung Stufe 6, 21.10.2026) fuer `state/desktop-datei.ts` von
 * KosmoOrbit: dort liest die Desktop-App (Tauri) fuer `kosmo_maus` mit `datei` eine Datei aus dem
 * Heimordner des Architekten.
 *
 * **In Visbox gibt die KI keine Dateien von der Platte.** Die Mappe und ihr Modell kommen vom
 * Heim-PC; eine Datei aus dem Heimordner an ein Feld zu geben, waere ein Weg an der Mappe vorbei
 * (und Regel 3: keine Pfade an ein Modell). `pruefePfad` weist darum jeden Pfad mit Satz ab; die
 * KosmoMaus antwortet dann «FEHLER: …», und nichts wurde gelesen. Die Namen wie dort.
 */
export const DATEI_TEIL_BYTES = 64 * 1024 * 1024;

export const SATZ_KEINE_DATEIEN =
  'In Visbox gibt die KI keine Dateien von der Platte — Modell und Mappe kommen vom Heim-PC. Nichts gelesen.';

export function pruefePfad(_pfad: string): void {
  throw new Error(SATZ_KEINE_DATEIEN);
}

export async function leseDesktopDatei(_pfad: string): Promise<File> {
  throw new Error(SATZ_KEINE_DATEIEN);
}
