/**
 * Visbox-eigen — die zweite Brücke der Knotenansicht: **`visboxWirt`** (Kopfteile, Entscheide
 * 115/116, Plan UI-Gleichheit S1/S2, 20.10.2026).
 *
 * Neben `visboxKi` (dem KI-Werkzeugsatz, `ki-wirt.ts`) spricht die Seite hier mit der Mac-App über
 * das, was die Kopfteile aus KosmoOrbit brauchen und nur die App weiss oder tun kann:
 *
 *  - **Seite → App** (`webkit.messageHandlers.visboxWirt.postMessage`): `bereit`, `modus`
 *    (Karte | Coop | Voll, Entscheid 108 A), `rechner` («Wer rechnet?» — mit `arbeit` und `ort` eine
 *    Wahl), `claude` (Claude über MCP an/aus), `oeffne` (Startansicht, Visbox-Seite, «Einrichten» am
 *    Mac, «Aktualisieren»), `einstellung` (das Blatt «Einrichten» an einem Abschnitt), `assistent`
 *    (S3: Frage, Anwenden, Ablehnen, Ändern), `merke` (S4: eine Einstellung der Seite, die die App
 *    über das Neuladen hinaus hält — nur die Schlüssel von `MERKBAR`).
 *  - **App → Seite** (`window.visboxWirt.lage({...})`): Leitung, Sperre, Rechner (der Chip),
 *    Claude-Lage, Fassung, Selbständigkeit, Thema; seit S3/S4 das Gespräch des Assistenten
 *    (`assistent`), «Wer rechnet?» (`rechnerwahl`), «Claude über MCP» (`claudeMcp`) und
 *    «Neuigkeiten» (`neuigkeiten`). Jedes Feld ist wahlfrei; was fehlt, bleibt.
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
import { setzeGespraechVonApp, registriereGespraechWeg, type GespraechVonApp, type GespraechWunsch, type Assistentenstand } from '../../kosmo-orbit/src/shell/kosmo-gespraech';
import { setzeThema } from './thema';

/** Der Bote der Mac-App (`WKScriptMessageHandler` «visboxWirt»). */
export interface WirtBote {
  postMessage(nachricht: unknown): void;
}

export type WirtZiel = 'startansicht' | 'visbox-seite' | 'einrichten' | 'aktualisieren' | 'mappen';

/** Die Arbeiten und Orte von «Wer rechnet?» — Wörter wie im Kern (`Rechenarbeit`, `Rechnerort`). */
export type Rechenarbeit = 'blenderRender' | 'bildmodell' | 'bedienKI';
export type Rechnerort = 'heimPC' | 'diesesGeraet';

/**
 * Was die Seite über das Neuladen hinaus behält — die App merkt es (das Webfenster hat keinen
 * bleibenden Speicher) und legt es vor dem ersten Bild zurück. **Nur diese Schlüssel**: Thema, Akzent,
 * Anzeige (Schrift, Bewegung) und der Rückgängig-Schalter — dieselbe Liste im Kern (`Knotenwirt.merkbar`).
 */
export const MERKBAR: readonly string[] = ['kosmo.thema', 'kosmo.akzent', 'kosmo.anzeige', 'kosmo.touch-undo-geste'];

/** Was die Seite von der App will. */
export type WirtWunsch =
  | { art: 'bereit' }
  | { art: 'modus'; modus: VisboxModus }
  | { art: 'rechner' }
  | { art: 'claude'; an: boolean }
  | { art: 'oeffne'; ziel: WirtZiel }
  | { art: 'einstellung'; abschnitt?: string }
  | { art: 'rechner'; arbeit: Rechenarbeit; ort: Rechnerort }
  | ({ art: 'assistent' } & GespraechWunsch)
  | { art: 'merke'; schluessel: string; wert: string };

/** Ein Feld von «Wer rechnet?» (`Rechnerwahlansicht.swift`): gewählt, wählbar, die Zeile darunter. */
export interface RechnerFeld {
  ort: Rechnerort;
  titel: string;
  zeile: string;
  gewaehlt: boolean;
  waehlbar: boolean;
}

/** «Wer rechnet?» — Titel, je Arbeit zwei Felder, die Sätze darunter; alles aus dem Kern (`Rechnerwahl`). */
export interface RechnerwahlLage {
  titel: string;
  untertitel: string;
  arbeiten: { arbeit: Rechenarbeit; titel: string; felder: RechnerFeld[] }[];
  mcpSatz: string;
  heuteSatz: string;
}

/** «Claude über MCP» — Schalter und die Sätze des Abschnitts (Kern `Claudeeinrichtung`). */
export interface ClaudeMcpLage {
  an: boolean;
  satz: string;
  titel: string;
  codeTitel: string;
  befehl: string;
  kopieren: string;
  datenTitel: string;
  daten: string;
  werkzeugeTitel: string;
  werkzeuge: string;
  nurHier: string;
}

/** «Neuigkeiten» — die laufende Fassung und, wenn eine neuere bereitsteht, was sie bringt. */
export interface NeuigkeitenLage {
  fassung: string;
  angebot: { nummer: string; zeilen: string[] } | null;
}

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
  assistent?: GespraechVonApp;
  rechnerwahl?: RechnerwahlLage;
  claudeMcp?: ClaudeMcpLage;
  neuigkeiten?: NeuigkeitenLage;
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
  rechnerwahl: RechnerwahlLage | null;
  claudeMcp: ClaudeMcpLage | null;
  neuigkeiten: NeuigkeitenLage | null;
}

export const useWirt = create<WirtZustand>(() => ({
  inDerApp: false,
  leitung: null,
  sperre: null,
  rechner: null,
  version: null,
  sichern: { stand: 'gesichert', iso: null },
  rechnerwahl: null,
  claudeMcp: null,
  neuigkeiten: null,
}));

type MitWebkit = { webkit?: { messageHandlers?: { visboxWirt?: WirtBote } } };

/** Der Bote, wenn die Seite in der Mac-App läuft — sonst `null`. */
export function boteDesWirts(fenster: unknown): WirtBote | null {
  return (fenster as MitWebkit).webkit?.messageHandlers?.visboxWirt ?? null;
}

const text = (x: unknown): string | null => (typeof x === 'string' ? x : null);
const objekt = (x: unknown): Record<string, unknown> | null =>
  x && typeof x === 'object' && !Array.isArray(x) ? (x as Record<string, unknown>) : null;
const texte = (x: unknown): string[] | null =>
  Array.isArray(x) && x.every((t) => typeof t === 'string') ? (x as string[]) : null;
const STAENDE: readonly Assistentenstand[] = ['bereit', 'laedt', 'fehlt', 'aus'];
const ARBEITEN: readonly Rechenarbeit[] = ['blenderRender', 'bildmodell', 'bedienKI'];
const ORTE: readonly Rechnerort[] = ['heimPC', 'diesesGeraet'];

/** Das Gespräch des Assistenten — nur die Felder von `Knotenwirt.Assistentenlage`, jedes geprüft. */
export function liesAssistent(roh: unknown): GespraechVonApp | null {
  const o = objekt(roh);
  if (!o || !Array.isArray(o['beitraege']) || typeof o['wartet'] !== 'boolean') return null;
  const beitraege = (o['beitraege'] as unknown[]).flatMap((b) => {
    const x = objekt(b);
    return x && (x['von'] === 'mensch' || x['von'] === 'assistent') && typeof x['text'] === 'string'
      ? [{ von: x['von'] as 'mensch' | 'assistent', text: x['text'] }]
      : [];
  });
  const k = objekt(o['karte']);
  const zeilen = k ? texte(k['zeilen']) : null;
  const g = objekt(o['grenzen']);
  const f = objekt(o['feld']);
  return {
    beitraege,
    wartet: o['wartet'],
    hinweis: text(o['hinweis']),
    karte: k && zeilen ? { zeilen, rechenzeit: text(k['rechenzeit']) } : null,
    stand: STAENDE.includes(o['stand'] as Assistentenstand) ? (o['stand'] as Assistentenstand) : null,
    modell: text(o['modell']),
    feldSatz: text(o['feldSatz']),
    grenzen: g && typeof g['titel'] === 'string' && typeof g['satz'] === 'string' ? { titel: g['titel'], satz: g['satz'] } : null,
    feld: f && typeof f['nummer'] === 'number' && typeof f['text'] === 'string' ? { nummer: f['nummer'], text: f['text'] } : null,
  };
}

/** «Wer rechnet?» — nur die genannten Felder. */
export function liesRechnerwahl(roh: unknown): RechnerwahlLage | null {
  const o = objekt(roh);
  if (!o || !Array.isArray(o['arbeiten'])) return null;
  const arbeiten = (o['arbeiten'] as unknown[]).flatMap((a) => {
    const x = objekt(a);
    if (!x || !ARBEITEN.includes(x['arbeit'] as Rechenarbeit) || typeof x['titel'] !== 'string' || !Array.isArray(x['felder'])) return [];
    const felder = (x['felder'] as unknown[]).flatMap((f) => {
      const y = objekt(f);
      return y && ORTE.includes(y['ort'] as Rechnerort) && typeof y['titel'] === 'string' && typeof y['zeile'] === 'string' &&
        typeof y['gewaehlt'] === 'boolean' && typeof y['waehlbar'] === 'boolean'
        ? [{ ort: y['ort'] as Rechnerort, titel: y['titel'], zeile: y['zeile'], gewaehlt: y['gewaehlt'], waehlbar: y['waehlbar'] }]
        : [];
    });
    return [{ arbeit: x['arbeit'] as Rechenarbeit, titel: x['titel'], felder }];
  });
  return {
    titel: text(o['titel']) ?? '',
    untertitel: text(o['untertitel']) ?? '',
    arbeiten,
    mcpSatz: text(o['mcpSatz']) ?? '',
    heuteSatz: text(o['heuteSatz']) ?? '',
  };
}

const CLAUDE_MCP_FELDER = ['satz', 'titel', 'codeTitel', 'befehl', 'kopieren', 'datenTitel', 'daten', 'werkzeugeTitel', 'werkzeuge', 'nurHier'] as const;

/** «Claude über MCP» — nur die genannten Felder; ohne Schalterstand gar nichts. */
export function liesClaudeMcp(roh: unknown): ClaudeMcpLage | null {
  const o = objekt(roh);
  if (!o || typeof o['an'] !== 'boolean') return null;
  const raus = { an: o['an'] } as ClaudeMcpLage;
  for (const f of CLAUDE_MCP_FELDER) (raus as unknown as Record<string, string>)[f] = text(o[f]) ?? '';
  return raus;
}

/** «Neuigkeiten» — die Fassung und ein Angebot. */
export function liesNeuigkeiten(roh: unknown): NeuigkeitenLage | null {
  const o = objekt(roh);
  if (!o || typeof o['fassung'] !== 'string') return null;
  const a = objekt(o['angebot']);
  const zeilen = a ? texte(a['zeilen']) : null;
  return { fassung: o['fassung'], angebot: a && typeof a['nummer'] === 'string' && zeilen ? { nummer: a['nummer'], zeilen } : null };
}

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
  const assistent = 'assistent' in o ? liesAssistent(o['assistent']) : null;
  if (assistent) raus.assistent = assistent;
  const rechnerwahl = 'rechnerwahl' in o ? liesRechnerwahl(o['rechnerwahl']) : null;
  if (rechnerwahl) raus.rechnerwahl = rechnerwahl;
  const claudeMcp = 'claudeMcp' in o ? liesClaudeMcp(o['claudeMcp']) : null;
  if (claudeMcp) raus.claudeMcp = claudeMcp;
  const neuigkeiten = 'neuigkeiten' in o ? liesNeuigkeiten(o['neuigkeiten']) : null;
  if (neuigkeiten) raus.neuigkeiten = neuigkeiten;
  return raus;
}

/** Legt eine (gelesene) Lage in die Seite. */
export function legeLage(lage: WirtLage): void {
  const z: Partial<WirtZustand> = {};
  if (lage.leitung !== undefined) z.leitung = lage.leitung;
  if (lage.sperre !== undefined) z.sperre = lage.sperre;
  if (lage.rechner !== undefined) z.rechner = lage.rechner;
  if (lage.version !== undefined) z.version = lage.version;
  if (lage.rechnerwahl !== undefined) z.rechnerwahl = lage.rechnerwahl;
  if (lage.claudeMcp !== undefined) z.claudeMcp = lage.claudeMcp;
  if (lage.neuigkeiten !== undefined) z.neuigkeiten = lage.neuigkeiten;
  useWirt.setState(z);
  if (lage.assistent) setzeGespraechVonApp(lage.assistent);
  if (lage.claude) setzeClaudeLage(lage.claude);
  if (lage.modus) setzeModusVonApp(lage.modus);
  if (lage.thema) setzeThema(lage.thema);
}

/** Der Satz im Gesprächsfeld, wenn keine App da ist (Browser am Heim-PC). */
export const OHNE_APP_ASSISTENT = 'Den Assistenten fragst du in der Visbox-App am Mac — dort meldet sie sich beim Heim-PC an.';

/** Wo es das gibt, wenn keine App da ist — ein Satz statt eines Knopfs ohne Wirkung. */
export function ohneApp(w: WirtWunsch): string | null {
  switch (w.art) {
    case 'bereit':
    case 'modus':
      return null;
    case 'rechner':
      return '«Wer rechnet?» stellst du in der Visbox-App am Mac ein.';
    case 'assistent':
      return OHNE_APP_ASSISTENT;
    case 'merke':
      return null;
    case 'claude':
      return 'Claude über MCP schaltest du in der Visbox-App am Mac ein und aus.';
    case 'oeffne':
      if (w.ziel === 'visbox-seite') return null;
      if (w.ziel === 'einrichten') return 'Den Heim-PC richtest du in der Visbox-App am Mac ein.';
      if (w.ziel === 'aktualisieren') return 'Aktualisiert wird in der Visbox-App am Mac.';
      if (w.ziel === 'mappen') return 'Mappen am Mac öffnest du in der Visbox-App am Mac.';
      return 'Die Startansicht gibt es nur in der Visbox-App am Mac.';
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
  // DAS GESPRAECH FUEHRT DIE APP (S3): ohne App kein Weg — das Feld sagt dann, wo es das gibt.
  registriereGespraechWeg(b ? (w) => sende({ art: 'assistent', ...w }) : null);
  sende({ art: 'bereit' });
  return () => {
    registriereModusWeg(null);
    registriereGespraechWeg(null);
    bote = null;
    useWirt.setState({ inDerApp: false });
    delete (fenster as unknown as { visboxWirt?: VisboxWirt }).visboxWirt;
  };
}

/** Für `graph-sichern.ts`: die Lage des Sicherns an den Speichern-Kreis. */
export function meldeSichern(lage: AutosaveLage): void {
  useWirt.setState({ sichern: lage });
}

/**
 * S4: Die Einstellungen der Seite, die die App über das Neuladen hinaus hält (`MERKBAR`) — jede mit
 * ihrem jetzigen Wert an die App. Ohne App bleibt es beim Speicher des Browsers.
 */
export function merkeEinstellungen(speicher: Pick<Storage, 'getItem'> | null = typeof localStorage === 'undefined' ? null : localStorage): void {
  if (!bote || !speicher) return;
  for (const schluessel of MERKBAR) {
    let wert: string | null = null;
    try {
      wert = speicher.getItem(schluessel);
    } catch {
      wert = null;
    }
    if (wert !== null) sende({ art: 'merke', schluessel, wert });
  }
}
