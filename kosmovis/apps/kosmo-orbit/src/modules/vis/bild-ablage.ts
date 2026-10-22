import { melde } from '@kosmo/ui';
import { useProject } from '../../state/project-store';
import {
  ablageSchluessel,
  ablegenDa,
  istBlattDa,
  laufNichtWaehlbar,
  projektBild,
  setzeAblageStand,
  sichereImProjekt,
  useBildAblage,
  vergissZuordnung,
} from './bild-ablage-kern';
import { verlaufReihe, type VerlaufEintrag } from './render-verlauf';
import { bescheideBridgeCatch, bildBlob, holeBildMitHerkunft, lizenzFuersBlatt } from './vis-jobs';
import { laufMitBild, useVisRuntime, type NodeLauf } from './vis-runtime';

/**
 * Video-Befunde L4-16, L3-A4, L3-A5 (Demolauf 16.10.2026; Blatt «Bild aufs Blatt») — die
 * Netzseite der Bildablage. Die Rechnung steht in `bild-ablage-kern.ts`.
 *
 *  - **Sichern beim Fertigwerden** (`starteBildAblage`): jeder fertige Lauf mit Bild — der
 *    aktuelle UND die im Verlauf — kommt in voller Aufloesung ins Projekt, einer nach dem
 *    anderen. Ist der Heim-PC gerade nicht da, wird es spaeter noch einmal versucht
 *    (`NACHHOLEN_MS`); ein Klick auf «Aufs Blatt» oder «Exportieren» holt es sofort.
 *  - **Welcher Lauf aufs Blatt** (`blattQuelleAusLauf`): das neueste FERTIGE Bild, nicht blind
 *    der letzte Lauf. Ist der letzte abgebrochen oder leer, geht der vorige fertige, und der
 *    Knoten sagt welcher; gibt es keinen, sagt er warum.
 *  - **Exportieren** (`exportiereBild`): die Datei im Original — aus dem Projekt, sonst vom
 *    Heim-PC. Im Browser ein Herunterladen; in der Mac-App von Visbox ein Sichern-Dialog
 *    (die Mac-App faengt das Herunterladen ab).
 */

/** Ein gescheitertes Sichern wird fruehestens nach dieser Zeit wieder versucht. */
export const NACHHOLEN_MS = 60_000;

let warteschlange: Array<{ jobId: string; bild: string; guete?: 'vorschau' | 'voll' | undefined }> = [];
let arbeitet = false;
let abmelden: (() => void) | null = null;
let nutzer = 0;

function braucht(jobId: string, bild: string, jetzt: number): boolean {
  const stand = useBildAblage.getState().stand[ablageSchluessel(jobId, bild)];
  if (!stand) return true;
  return stand.zustand === 'fehler' && jetzt - stand.um >= NACHHOLEN_MS;
}

/** Holt ein Bild vom Heim-PC und legt es ins Projekt; der Stand steht danach in `useBildAblage`. */
export async function sichereLauf(jobId: string, bild: string, guete?: 'vorschau' | 'voll'): Promise<void> {
  const schluessel = ablageSchluessel(jobId, bild);
  if (projektBild(jobId, bild, guete)) {
    // Schon da (etwa aus einer frueheren Sitzung, mit dem Projekt geladen).
    await sichereImProjekt(jobId, bild, '', '', { guete });
    return;
  }
  setzeAblageStand(schluessel, { zustand: 'sichert' });
  try {
    const { dataUrl, label, angabe } = await holeBildMitHerkunft(jobId, bild);
    // Prepare/Owner 21.10.2026: Guete und Lizenzvermerk reisen mit dem Bild, damit ein Bild mit
    // offener Lizenz auch dann erkennbar bleibt, wenn es jemand per Kennung aufs Blatt setzt.
    await sichereImProjekt(jobId, bild, label, dataUrl, { guete, lizenzOffen: lizenzFuersBlatt(angabe) });
  } catch (err) {
    setzeAblageStand(schluessel, {
      zustand: 'fehler',
      grund: `der Heim-PC gab das Bild nicht her (${err instanceof Error ? err.message : String(err)}).`,
      um: Date.now(),
    });
  }
}

async function arbeite(): Promise<void> {
  if (arbeitet) return;
  arbeitet = true;
  try {
    while (warteschlange.length > 0) {
      const naechster = warteschlange.shift()!;
      await sichereLauf(naechster.jobId, naechster.bild, naechster.guete);
    }
  } finally {
    arbeitet = false;
  }
}

/** Alle fertigen Laeufe mit Bild, die noch nicht im Projekt sind, in die Warteschlange. */
export function pruefeLaeufe(): void {
  if (!istBlattDa() || !ablegenDa()) return;
  const { laeufe, verlauf } = useVisRuntime.getState();
  const jetzt = Date.now();
  const kandidaten: NodeLauf[] = [...Object.values(laeufe), ...Object.values(verlauf).flat()];
  for (const l of kandidaten) {
    if (!laufMitBild(l)) continue;
    const jobId = l.jobId!;
    const bild = l.bild!;
    if (!braucht(jobId, bild, jetzt)) continue;
    if (warteschlange.some((w) => w.jobId === jobId && w.bild === bild)) continue;
    warteschlange.push({ jobId, bild, guete: l.guete });
  }
  void arbeite();
}

/**
 * Sichern beim Fertigwerden anmelden — die Knotenansicht ruft es beim Einhaengen und die
 * zurueckgegebene Funktion beim Aushaengen. Mehrfach angemeldet zaehlt einmal.
 */
export function starteBildAblage(): () => void {
  nutzer++;
  if (!abmelden) {
    abmelden = useVisRuntime.subscribe((s, vorher) => {
      if (s.laeufe !== vorher.laeufe || s.verlauf !== vorher.verlauf) pruefeLaeufe();
    });
    pruefeLaeufe();
  }
  return () => {
    nutzer = Math.max(0, nutzer - 1);
    if (nutzer === 0 && abmelden) {
      abmelden();
      abmelden = null;
    }
  };
}

/** Nur fuer Proben: Warteschlange und Stand leeren. */
export function setzeBildAblageZurueck(): void {
  warteschlange = [];
  vergissZuordnung();
  useBildAblage.setState({ stand: {} });
}

export type BlattQuelle =
  | { eintrag: VerlaufEintrag; hinweis: string | null }
  | { eintrag: null; grund: string };

/**
 * L4-16: welcher Lauf eines Render-Knotens aufs Blatt geht — das neueste fertige Bild. Ist der
 * letzte Lauf es nicht, nennt `hinweis` den genommenen und warum; ohne fertiges Bild sagt
 * `grund`, woran es liegt (der letzte Lauf).
 */
export function blattQuelleAusLauf(lauf: NodeLauf | undefined, frueher: readonly NodeLauf[] | undefined): BlattQuelle {
  const reihe = verlaufReihe(lauf, frueher);
  const neuester = reihe[0];
  const grundLetzter = laufNichtWaehlbar(lauf);
  if (!neuester) return { eintrag: null, grund: grundLetzter ?? 'Kein fertiges Bild.' };
  if (grundLetzter === null) return { eintrag: neuester, hinweis: null };
  const nummer = neuester.laufNummer !== undefined ? `Lauf ${neuester.laufNummer}` : 'der vorige Lauf';
  return { eintrag: neuester, hinweis: `${nummer} — der letzte Lauf hat kein fertiges Bild: ${grundLetzter}` };
}

/**
 * Visbox-Gegenprobe 328 (S9, 22.10.2026): der Stamm des Dateinamens. In KosmoOrbit der Projektname; ein Wirt,
 * der das Projekt anders fuehrt (Visbox: die Mappe, das Dokument heisst dort immer «Unbenannt»), meldet hier
 * seinen Namen. Ohne Meldung oder bei leerem Namen gilt der Projektname wie bisher.
 */
let exportStamm: (() => string | null | undefined) | null = null;

export function registriereExportStamm(stamm: (() => string | null | undefined) | null): void {
  exportStamm = stamm;
}

function namensTeil(text: string): string {
  return text.trim().replace(/[\s/\\:]+/g, '-');
}

/**
 * «Projekt-Lauf-3-render_0.png» — der Name, den das Sichern vorschlaegt. `zusatz` (eine Variante:
 * «Varianten-2-Abendstimmung») steht vor dem Dateinamen der Kamera, damit zwei Bestellungen mit
 * derselben Kamera nicht denselben Namen tragen.
 */
export function exportName(bild: string, laufNummer?: number, zusatz?: string): string {
  let stamm: string | null | undefined = null;
  try {
    stamm = exportStamm?.();
  } catch {
    stamm = null;
  }
  const projekt = namensTeil(stamm || useProject.getState().doc.settings.projectName || 'Visualisierung');
  const datei = bild.split('/').pop() || 'bild.png';
  const mitte = zusatz ? `-${namensTeil(zusatz)}` : '';
  return `${projekt}${laufNummer !== undefined ? `-Lauf-${laufNummer}` : ''}${mitte}-${datei}`;
}

function blobAusBase64(mime: string, b64: string): Blob {
  const roh = atob(b64);
  const bytes = new Uint8Array(roh.length);
  for (let i = 0; i < roh.length; i++) bytes[i] = roh.charCodeAt(i);
  return new Blob([bytes], { type: mime });
}

/**
 * «Exportieren»: die Datei im Original — aus dem Projekt, wenn sie dort liegt, sonst vom
 * Heim-PC. Gibt den Dateinamen zurueck. Ein Herunterladen wie bei den anderen Ausgaben
 * (`a[download]`); die Mac-App von Visbox zeigt dafuer einen Sichern-Dialog.
 */
export async function exportiereBild(jobId: string, bild: string, laufNummer?: number, zusatz?: string): Promise<string> {
  const asset = projektBild(jobId, bild);
  const blob = asset ? blobAusBase64(asset.mime, asset.data) : await bildBlob(jobId, bild);
  const name = exportName(bild, laufNummer, zusatz);
  const url = URL.createObjectURL(blob);
  try {
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    a.rel = 'noopener';
    document.body.appendChild(a);
    a.click();
    a.remove();
  } finally {
    // Erst nach dem Klick freigeben — sonst bekommt das Herunterladen eine leere Adresse.
    setTimeout(() => URL.revokeObjectURL(url), 10_000);
  }
  return name;
}

/** «Exportieren» mit Meldung — fuer die Knoepfe. */
export function exportiereMitMeldung(jobId: string, bild: string, laufNummer?: number, zusatz?: string): void {
  void exportiereBild(jobId, bild, laufNummer, zusatz)
    .then((name) => melde(`Exportiert: «${name}» — im Original.`, { ton: 'erfolg' }))
    .catch(bescheideBridgeCatch);
}
