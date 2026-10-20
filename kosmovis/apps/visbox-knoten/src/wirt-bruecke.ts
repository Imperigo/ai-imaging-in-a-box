/**
 * Visbox-eigen — die zweite Brücke der Knotenansicht: **`visboxWirt`** (Kopfteile, Entscheide
 * 115/116, Plan UI-Gleichheit S1/S2, 20.10.2026).
 *
 * Neben `visboxKi` (dem KI-Werkzeugsatz, `ki-wirt.ts`) spricht die Seite hier mit der Mac-App über
 * das, was die Kopfteile aus KosmoOrbit brauchen und nur die App weiss oder tun kann:
 *
 *  - **Seite → App** (`webkit.messageHandlers.visboxWirt.postMessage`): `bereit`, `modus`
 *    (Karte | Coop | Voll, Entscheid 108 A), `rechner` («Wer rechnet?» öffnen — der Heim-PC-Chip),
 *    `claude` (Claude über MCP an/aus), `oeffne` (Startansicht oder Visbox-Seite — die Palette am
 *    Logo), `einstellung` (der Einstellungs-Kreis).
 *  - **App → Seite** (`window.visboxWirt.lage({...})`): Leitung, Sperre, Rechner (der Chip),
 *    Claude-Lage, Fassung, Selbständigkeit, Thema. Jedes Feld ist wahlfrei; was fehlt, bleibt.
 *
 * **Das Heim-PC-Kennwort läuft nie durch die Seite** (Entscheid 116 (6)): `lage` liest nur die
 * genannten Felder und legt nichts anderes ab; die App schickt keines (Probe `wirt-bruecke.test.ts`).
 *
 * Im Browser ohne App (Heim-PC, Entwicklungsserver) fehlt der Bote: Die Wünsche gehen dann an
 * `ohneApp` und werden dort als Satz gesagt, statt still nichts zu tun.
 */
import { create } from 'zustand';
import { melde } from '@kosmo/ui';
import type { ThemeName } from '@kosmo/ui';
import { setzeClaudeLage, type ClaudeLage } from '../../kosmo-orbit/src/state/claude-anschluss';
import { registriereModusWeg, setzeModusVonApp, type VisboxModus } from '../../kosmo-orbit/src/state/kosmo-coop';
import type { AutosaveLage } from '../../kosmo-orbit/src/state/project-vault';
import { setzeThema } from './thema';

/** Der Bote der Mac-App (`WKScriptMessageHandler` «visboxWirt»). */
export interface WirtBote {
  postMessage(nachricht: unknown): void;
}

export type WirtZiel = 'startansicht' | 'visbox-seite';

/** Was die Seite von der App will. */
export type WirtWunsch =
  | { art: 'bereit' }
  | { art: 'modus'; modus: VisboxModus }
  | { art: 'rechner' }
  | { art: 'claude'; an: boolean }
  | { art: 'oeffne'; ziel: WirtZiel }
  | { art: 'einstellung'; abschnitt?: string };

/** Der Chip an der Stelle des Sync-Chips: was rechnet, in der Farbe des Sync-Chips. */
export interface RechnerLage {
  text: string;
  ton: 'gut' | 'aus' | 'warnung';
}

/** Was die App der Seite sagt — alles wahlfrei. */
export interface WirtLage {
  /** Der Satz der Leitung zum Heim-PC (Band), `null`: steht. */
  leitung?: string | null;
  /** Was ohne Rechner gesperrt ist, als Satz; `null`: nichts. */
  sperre?: string | null;
  rechner?: RechnerLage;
  claude?: ClaudeLage;
  /** Die laufende Fassung der App, z. B. «v0.4.0». */
  version?: string;
  modus?: VisboxModus;
  thema?: ThemeName;
}

export const MODI: readonly VisboxModus[] = ['karte', 'coop', 'voll'];
const THEMEN: readonly ThemeName[] = ['paper', 'orbit'];
const TOENE: readonly RechnerLage['ton'][] = ['gut', 'aus', 'warnung'];

interface WirtZustand {
  /** Ob eine App da ist (der Bote) — ohne sie sagen die Knöpfe, wo es das gibt. */
  inDerApp: boolean;
  leitung: string | null;
  sperre: string | null;
  rechner: RechnerLage | null;
  version: string | null;
  /** Die Lage des Sicherns für den Speichern-Kreis (`graph-sichern.ts`). */
  sichern: AutosaveLage;
}

export const useWirt = create<WirtZustand>(() => ({
  inDerApp: false,
  leitung: null,
  sperre: null,
  rechner: null,
  version: null,
  sichern: { stand: 'gesichert', iso: null },
}));

type MitWebkit = { webkit?: { messageHandlers?: { visboxWirt?: WirtBote } } };

/** Der Bote, wenn die Seite in der Mac-App läuft — sonst `null`. */
export function boteDesWirts(fenster: unknown): WirtBote | null {
  return (fenster as MitWebkit).webkit?.messageHandlers?.visboxWirt ?? null;
}

const text = (x: unknown): string | null => (typeof x === 'string' ? x : null);

/**
 * Liest eine Lage der App — **nur die genannten Felder**, jedes geprüft. Was sonst darin stünde,
 * fällt weg (Entscheid 116 (6): kein Kennwort, kein Token in der Seite).
 */
export function liesLage(roh: unknown): WirtLage {
  const o = roh && typeof roh === 'object' && !Array.isArray(roh) ? (roh as Record<string, unknown>) : {};
  const raus: WirtLage = {};
  if ('leitung' in o) raus.leitung = text(o['leitung']);
  if ('sperre' in o) raus.sperre = text(o['sperre']);
  const r = o['rechner'] as Record<string, unknown> | undefined;
  if (r && typeof r === 'object' && typeof r['text'] === 'string' && TOENE.includes(r['ton'] as RechnerLage['ton'])) {
    raus.rechner = { text: r['text'], ton: r['ton'] as RechnerLage['ton'] };
  }
  const c = o['claude'] as Record<string, unknown> | undefined;
  if (c && typeof c === 'object' && typeof c['verbunden'] === 'boolean') {
    raus.claude = { verbunden: c['verbunden'], ...(typeof c['internet'] === 'boolean' ? { internet: c['internet'] } : {}) };
  }
  if (typeof o['version'] === 'string') raus.version = o['version'];
  if (MODI.includes(o['modus'] as VisboxModus)) raus.modus = o['modus'] as VisboxModus;
  if (THEMEN.includes(o['thema'] as ThemeName)) raus.thema = o['thema'] as ThemeName;
  return raus;
}

/** Legt eine (gelesene) Lage in die Seite. */
export function legeLage(lage: WirtLage): void {
  const z: Partial<WirtZustand> = {};
  if (lage.leitung !== undefined) z.leitung = lage.leitung;
  if (lage.sperre !== undefined) z.sperre = lage.sperre;
  if (lage.rechner !== undefined) z.rechner = lage.rechner;
  if (lage.version !== undefined) z.version = lage.version;
  useWirt.setState(z);
  if (lage.claude) setzeClaudeLage(lage.claude);
  if (lage.modus) setzeModusVonApp(lage.modus);
  if (lage.thema) setzeThema(lage.thema);
}

/** Wo es das gibt, wenn keine App da ist — ein Satz statt eines Knopfs ohne Wirkung. */
export function ohneApp(w: WirtWunsch): string | null {
  switch (w.art) {
    case 'bereit':
    case 'modus':
      return null;
    case 'rechner':
      return '«Wer rechnet?» stellst du in der Visbox-App am Mac ein.';
    case 'claude':
      return 'Claude über MCP schaltest du in der Visbox-App am Mac ein und aus.';
    case 'oeffne':
      return w.ziel === 'visbox-seite' ? null : 'Die Startansicht gibt es nur in der Visbox-App am Mac.';
    case 'einstellung':
      return 'Die Einstellungen stehen in der Visbox-App am Mac.';
  }
}

let bote: WirtBote | null = null;

/** Ein Wunsch an die App. Ohne App: die Visbox-Seite direkt, sonst der Satz von `ohneApp`. */
export function sende(w: WirtWunsch, ort: Pick<Location, 'assign'> | null = typeof location === 'undefined' ? null : location): void {
  if (bote) {
    try {
      bote.postMessage(JSON.parse(JSON.stringify(w)));
    } catch (err) {
      console.error('[wirt-bruecke] Bote warf', err);
    }
    return;
  }
  // AUF DEM HEIM-PC IM BROWSER: Die Visbox-Seite liegt neben den Knoten (`/knoten/` → `/`).
  if (w.art === 'oeffne' && w.ziel === 'visbox-seite') {
    ort?.assign('../');
    return;
  }
  const satz = ohneApp(w);
  if (satz) melde(satz);
}

export interface VisboxWirt {
  /** App → Seite: die Lage (jedes Feld wahlfrei). */
  lage(roh: unknown): void;
}

/**
 * Hängt `window.visboxWirt` an, meldet «bereit» und verbindet die Selbständigkeits-Schalter mit
 * der App. Liefert das Abhängen (für Proben).
 */
export function haengeWirtAn(fenster: Window, b: WirtBote | null = boteDesWirts(fenster)): () => void {
  bote = b;
  useWirt.setState({ inDerApp: b !== null });
  (fenster as unknown as { visboxWirt?: VisboxWirt }).visboxWirt = {
    lage: (roh) => legeLage(liesLage(roh)),
  };
  registriereModusWeg((modus) => sende({ art: 'modus', modus }));
  sende({ art: 'bereit' });
  return () => {
    registriereModusWeg(null);
    bote = null;
    useWirt.setState({ inDerApp: false });
    delete (fenster as unknown as { visboxWirt?: VisboxWirt }).visboxWirt;
  };
}

/** Für `graph-sichern.ts`: die Lage des Sicherns an den Speichern-Kreis. */
export function meldeSichern(lage: AutosaveLage): void {
  useWirt.setState({ sichern: lage });
}
