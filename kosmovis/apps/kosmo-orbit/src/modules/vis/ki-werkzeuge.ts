/**
 * KI-Werkzeugsatz der Knotenansicht (Visbox Plan «KI-Bedienung» Stufe 1, 20.10.2026;
 * Visbox-Entscheide 105, 106–106f, 108).
 *
 * EIN Satz Werkzeuge fuer die Knotenansicht, den Claude (ueber den MCP-Kern der Visbox-Mac-App,
 * `Mcpkern.swift`) und spaeter der Visbox-Assistent gleich benutzen. Vorlage ist der
 * Claude-Anschluss von KosmoOrbit (`state/claude-anschluss.ts`: Werkzeugliste aus den Befehlen,
 * Probelauf vor der Karte, Anwenden ueber `runCommand`, Sammelwerkzeug mit «$neu:N») — hier aber
 * NUR das Vis-Werkzeug, und darum ohne `@kosmo/ai`, ohne KosmoMaus, Coop-Verlauf und
 * Tätigkeits-Store von KosmoOrbit: die Datei muss woertlich in die Visbox-Kopie
 * (`kosmovis/`) passen, deren Kern duenn ist (nur Modell, `commands/core`, `commands/vis`,
 * Vis-Graph; `@kosmo/ai` ist dort ein Stellvertreter).
 *
 * DIE REGEL (gleich wie `Mcpfreigabe.brauchtKarte` in Swift, an EINER Stelle: `brauchtKarte`):
 *  - lesen     — nie eine Karte (graph_lesen).
 *  - aendern   — Karte nur im Modus «karte» (Vorgabe); in «coop» und «voll» sofort.
 *  - loeschen  — IMMER eine Karte, auch in «voll» (Entscheid 106c).
 *  - rendern   — IMMER eine Karte (Entscheid 106b). Und auch nach «Anwenden» stellt `vis.render`
 *                nur den AUFTRAG ins Dokument; die Grafikkarte gibt danach der Architekt am
 *                Render-Knoten frei. Die GPU-Freigabe ist darum NIE ein Werkzeug.
 *
 * Ein Aufruf wird zuerst geprueft (zod-Schema des Befehls) und als Probelauf gerechnet
 * (`execute(..., { dryRun: true })` — das Dokument bleibt unveraendert). Erst «Anwenden» (oder
 * Coop/Voll bei «aendern») fuehrt ueber `useProject.runCommand` aus — derselbe eine Weg wie jeder
 * Handgriff (Journal, Sync, Rueckgaengig), als EINE Rueckgaengig-Gruppe, auch fuer ein Paket.
 *
 * Journal-Akteur: Karte → 'kosmo' (KI-Vorschlag, vom Architekten freigegeben; wie
 * `wendeClaudeVorschlagAn`); ohne Karte (Coop/Voll) → 'claude' fuer Claude, 'kosmo' fuer den
 * Assistenten (der Kern kennt keinen eigenen Akteur «assistent»).
 *
 * ZWEI RUECKGAENGIG-VERLAEUFE (Visbox-Entscheid 114, 20.10.2026, «getrennt wie in KosmoOrbit»):
 * Was die KI OHNE Karte tut (Coop/Voll), laeuft ueber `runCommand` (Journal, Sync), aber
 * AUSSERHALB der Rueckgaengig-Kette des Architekten (`ohneVerlauf`, wie `versucheCoop` in
 * `state/kosmo-coop.ts`) und steht als KI-Schritt hier (`kiSchritte`). Strg+Z nimmt darum nur
 * die eigenen Schritte des Architekten zurueck; «Claudes letzten Schritt zurücknehmen» nimmt den
 * letzten KI-Schritt zurueck (`rueckgaengigKi`) — nur, wenn seine Teile noch so dastehen, wie die
 * KI sie hinterliess, sonst mit Satz und ohne Aenderung. Die Ruecknahme ist ein Schritt des
 * Architekten (`wendeSchrittAn`): Strg+Z macht sie wieder rueckgaengig. Eine KARTE, die der
 * Architekt anwendet, ist SEIN Schritt (eine Rueckgaengig-Gruppe in seiner Kette). Die Wache
 * fuer Strg+Z/Strg+Y (`kiVerlaufWache`) setzt der Wirt (`setzeVerlaufWache`), nicht diese Datei —
 * in KosmoOrbit haelt `kosmo-coop.ts` die Wache, und zwei Wachen gibt es nicht.
 *
 * Taetigkeit und Karten gehen als EREIGNIS hinaus (`abonniere`), nicht in einen Store: der Wirt
 * (Visbox: die Mac-App ueber `webkit.messageHandlers.visboxKi`; KosmoOrbit: wahlweise
 * `claude-taetigkeit.ts`) entscheidet, wo sie stehen.
 */
import { z } from 'zod';
import {
  allCommands,
  execute,
  getCommand,
  invertPatches,
  isSettingsPatch,
  KosmoDoc,
  VIS_NODE_KATALOG,
  type AnyPatch,
  type ExecuteOptions,
  type ExecutionResult,
  type History,
  type JournalEntry,
  type VisEdge,
  type VisGraph,
  type VisNode,
} from '@kosmo/kernel';
import { ohneVerlauf, useProject, wendeSchrittAn, type VerlaufWacheUrteil } from '../../state/project-store';
import { useVisRuntime } from './vis-runtime';
import { grundlageAmKnoten } from './grundlage';
import { gueteAmKnoten } from './guete';
import { blickAufrufErgaenzen, waehlbareBlicke } from './blick-quelle';

// ---------------------------------------------------------------------------------- Arten, Modus

/** Was ein Werkzeug tut — dieselben vier Worte wie `Werkzeugart` in `Mcpkern.swift`. */
export type KiWerkzeugArt = 'lesen' | 'aendern' | 'loeschen' | 'rendern';

/** Wie selbstaendig die KI arbeitet — dieselben drei Worte wie `Selbstaendigkeit` in Swift. */
export type KiModus = 'karte' | 'coop' | 'voll';

/** Wer ruft. Claude ueber MCP oder der Visbox-Assistent (Stufe 5). */
export type KiUrheber = 'claude' | 'assistent';

/**
 * `true`: ein Mensch entscheidet an einer Karte. Lesen nie; Loeschen und Rendern immer (106b,
 * 106c), auch in «voll»; Aendern nur im Modus «karte». Wortgleich zu `Mcpfreigabe.brauchtKarte`.
 */
export function brauchtKarte(art: KiWerkzeugArt, modus: KiModus): boolean {
  switch (art) {
    case 'lesen':
      return false;
    case 'loeschen':
    case 'rendern':
      return true;
    case 'aendern':
      return modus === 'karte';
  }
}

/**
 * Die Einteilung je Vis-Befehl, ausdruecklich. Ein neuer `vis.*`-Befehl ohne Eintrag faellt auf
 * `artAusName` zurueck — und die Probe `ki-werkzeuge.test.ts` wird rot, damit er hier bewusst
 * eingeteilt wird.
 */
export const VIS_BEFEHL_ART: Readonly<Record<string, KiWerkzeugArt>> = {
  'vis.graphErstellen': 'aendern',
  'vis.nodeSetzen': 'aendern',
  'vis.nodeParametrieren': 'aendern',
  'vis.nodeSchieben': 'aendern',
  'vis.verbinden': 'aendern',
  'vis.trennen': 'aendern',
  'vis.nodeKollabieren': 'aendern',
  'vis.nodeLoeschen': 'loeschen',
  'vis.graphLoeschen': 'loeschen',
  'vis.render': 'rendern',
  // Auf dem Vorschau-Stand (Varianten-Knoten, R40): bestellt alle Kombinationen, jede wartet auf
  // die Freigabe am Knoten — also wie vis.render. Mit `stand: true` liest er nur (keine Patches →
  // «OHNE ÄNDERUNG» mit dem Stand, ohne Karte). Steht hier, bevor der Befehl auf diesem Zweig ist,
  // damit die Visbox-Kopie (auf dem Hilfszweig visbox-stand) ihn eingeteilt bekommt.
  'vis.varianten': 'rendern',
};

/** Rueckfall fuer einen nicht eingeteilten Befehl: im Zweifel die strengere Art. */
function artAusName(commandId: string): KiWerkzeugArt {
  if (/l(ö|oe)sch|entfern/i.test(commandId)) return 'loeschen';
  if (/render|variant|freig/i.test(commandId)) return 'rendern';
  return 'aendern';
}

export function artVonBefehl(commandId: string): KiWerkzeugArt {
  return VIS_BEFEHL_ART[commandId] ?? artAusName(commandId);
}

/** Wie `Werkzeugart` geordnet: was die strengste Freigabe braucht, zuerst. */
const ART_STRENGE: Readonly<Record<KiWerkzeugArt, number>> = { lesen: 0, aendern: 1, loeschen: 2, rendern: 3 };

// ---------------------------------------------------------------------------------- Werkzeuge

export const GRAPH_LESEN = 'graph_lesen';
export const VIS_PAKET = 'vis_paket';
export const VIS_PAKET_MAX_SCHRITTE = 40;
const NEU_VERWEIS = /^\$neu:(\d+)$/;

export interface KiWerkzeug {
  /** 1–64 Zeichen aus Buchstaben, Ziffern, `_`, `-` (wie `Mcpwerkzeug.nameIstGueltig`). */
  name: string;
  description: string;
  /** JSON-Schema der Argumente, immer `type: 'object'`, ohne Draft-7-Tupel (Claude-API). */
  inputSchema: Record<string, unknown>;
  art: KiWerkzeugArt;
}

/** `vis.nodeSetzen` → `vis_nodeSetzen` (wie `toolNameFor` in `@kosmo/ai`). */
export function werkzeugNameFuer(commandId: string): string {
  return commandId.replace(/\./g, '_');
}

/** `vis_nodeSetzen` → `vis.nodeSetzen`; auch die Befehls-Id selbst wird angenommen. */
export function befehlFuer(name: string): string {
  return name.includes('.') ? name : name.replace('_', '.');
}

/** Die Vis-Befehle, die Werkzeug werden: nur `vis.*`, nichts Verborgenes (kein Blatt-Stellvertreter). */
function visBefehle() {
  return allCommands().filter((c) => c.id.startsWith('vis.') && !c.kiVerborgen);
}

const RENDER_ZUSATZ =
  ' NUR der Auftrag: die Grafikkarte startet erst, wenn der Architekt am Render-Knoten freigibt — das ist kein Werkzeug. Immer eine Karte.';
const LOESCHEN_ZUSATZ = ' Immer eine Karte, in jedem Modus.';
/**
 * Der Paketweg an den beiden Einzelwerkzeugen, die er betrifft (Visbox-Messung auf-20261021-319,
 * 21.10.2026): Assistent und Claude setzten einen Knoten und verbanden ihn in derselben Runde mit
 * einer GERATENEN Kennung — nur `vis_paket` erklaerte «$neu», die Einzelwerkzeuge schwiegen davon.
 * Der Satz steht hier und nicht im Kernbefehl (`commands/vis.ts`), weil `vis_paket` nur in diesem
 * Werkzeugsatz existiert; der Kosmo-Chat von `@kosmo/ai` kennt es nicht.
 */
export const PAKET_HINWEIS =
  ' Neu setzen und gleich verbinden: vis_paket mit «$neu:0» (die Kennung eines neuen Knotens gibt es erst in der Antwort).';
const MIT_PAKET_HINWEIS = new Set(['vis.nodeSetzen', 'vis.verbinden']);

const GRAPH_LESEN_SCHEMA: Record<string, unknown> = {
  type: 'object',
  properties: {
    graphId: { type: 'string', description: 'Nur diesen Graphen; ohne: alle.' },
    katalog: { type: 'boolean', description: 'Auch die Knotentypen mit ihren Ports.' },
  },
  additionalProperties: false,
};

const GRAPH_LESEN_BESCHREIBUNG =
  'Liest die Render-Graphen der Knotenansicht: je Knoten nodeId, Typ, Label, Lage, Ports (Eingänge mit ihrer Kante), Parameter, letzter Lauf (Zustand), Grundlage und Güte; dazu alle Kanten (edgeId) und den offenen Render-Auftrag. IMMER zuerst aufrufen, um gültige graphId/nodeId/edgeId zu bekommen. Ändert nichts.';

const PAKET_SCHEMA: Record<string, unknown> = {
  type: 'object',
  properties: {
    schritte: {
      type: 'array',
      minItems: 1,
      maxItems: VIS_PAKET_MAX_SCHRITTE,
      items: {
        type: 'object',
        properties: {
          befehl: { type: 'string', description: 'Werkzeugname, z.B. vis_nodeSetzen' },
          argumente: { type: 'object' },
        },
        required: ['befehl'],
        additionalProperties: false,
      },
    },
  },
  required: ['schritte'],
  additionalProperties: false,
};

const PAKET_BESCHREIBUNG = `Mehrere vis_*-Befehle als EIN Schritt: eine Karte, ein Rückgängig. Bis ${VIS_PAKET_MAX_SCHRITTE} Schritte; Argumente wie beim Einzelwerkzeug; «$neu:N» = die Kennung, die Schritt N (ab 0) neu anlegt (Knoten, Graph oder Kante). Vorher Probelauf: ist ein Schritt ungültig, wird nichts vorgeschlagen und die Antwort nennt ihn. Enthält das Paket Löschen oder Rendern, ist es in jedem Modus eine Karte.`;

/**
 * Alle Werkzeuge der Knotenansicht: `graph_lesen`, jeder `vis.*`-Befehl und `vis_paket`.
 * `doc` ist fuer kuenftige dokumentabhaengige Beschreibungen da (wie `werkzeugeFuerClaude`).
 */
export function visWerkzeuge(_doc: KosmoDoc = useProject.getState().doc): KiWerkzeug[] {
  const befehle = visBefehle().map((cmd): KiWerkzeug => {
    const art = artVonBefehl(cmd.id);
    const zusatz = (art === 'rendern' ? RENDER_ZUSATZ : art === 'loeschen' ? LOESCHEN_ZUSATZ : '')
      + (MIT_PAKET_HINWEIS.has(cmd.id) ? PAKET_HINWEIS : '');
    return {
      name: werkzeugNameFuer(cmd.id),
      description: cmd.description + zusatz,
      inputSchema: fuerKiSchema(z.toJSONSchema(cmd.params as z.ZodType, { io: 'input', target: 'draft-7' }) as Record<string, unknown>),
      art,
    };
  });
  return [
    { name: GRAPH_LESEN, description: GRAPH_LESEN_BESCHREIBUNG, inputSchema: GRAPH_LESEN_SCHEMA, art: 'lesen' },
    ...befehle,
    { name: VIS_PAKET, description: PAKET_BESCHREIBUNG, inputSchema: PAKET_SCHEMA, art: 'aendern' },
  ];
}

// ---------------------------------------------------------------------------------- Schema an der Grenze

/**
 * Das JSON-Schema fuer die Claude-API (JSON Schema 2020-12), dieselbe Wandlung wie
 * `fuerClaudeSchema` + `ohneStandardGrenzen` in `@kosmo/ai` (dort nicht importierbar, s. Kopf):
 * die Draft-7-Kopfzeile faellt weg, die Standardgrenzen von zod (±MAX_SAFE_INTEGER) fallen weg,
 * ein Tupel (`items: [a, b]` aus Draft 7 oder `prefixItems`) wird `items` + feste Laenge.
 * Rein und rekursiv. Die Pruefung selbst bleibt beim zod-Schema des Befehls.
 */
export function fuerKiSchema(schema: Record<string, unknown>): Record<string, unknown> {
  const raus: Record<string, unknown> = {};
  const einzeln = (v: unknown): unknown => (v && typeof v === 'object' && !Array.isArray(v) ? fuerKiSchema(v as Record<string, unknown>) : v);
  for (const [k, v] of Object.entries(schema)) {
    if (k === '$schema' || k === 'additionalItems') continue;
    if ((k === 'minimum' && v === -Number.MAX_SAFE_INTEGER) || (k === 'maximum' && v === Number.MAX_SAFE_INTEGER)) continue;
    if (['properties', 'patternProperties', 'definitions', '$defs'].includes(k) && v && typeof v === 'object' && !Array.isArray(v)) {
      raus[k] = Object.fromEntries(Object.entries(v).map(([n, s]) => [n, einzeln(s)]));
    } else if (['anyOf', 'oneOf', 'allOf'].includes(k) && Array.isArray(v)) {
      raus[k] = v.map(einzeln);
    } else if (k === 'items' && Array.isArray(v)) {
      // unten
    } else if (k === 'prefixItems' && Array.isArray(v)) {
      // unten
    } else if (['items', 'additionalProperties', 'not'].includes(k)) {
      raus[k] = einzeln(v);
    } else {
      raus[k] = v;
    }
  }
  const tupel = Array.isArray(schema['items']) ? schema['items'] : Array.isArray(schema['prefixItems']) ? schema['prefixItems'] : null;
  if (!tupel) return raus;
  const teile = tupel.map(einzeln);
  const restRoh = Array.isArray(schema['items']) ? schema['additionalItems'] : schema['items'];
  const rest = restRoh === undefined ? false : einzeln(restRoh);
  const gleich = teile.length > 0 && teile.every((t) => JSON.stringify(t) === JSON.stringify(teile[0]));
  delete raus['prefixItems'];
  if (gleich && (rest === false || JSON.stringify(rest) === JSON.stringify(teile[0]))) {
    raus['items'] = teile[0];
  } else {
    raus['prefixItems'] = teile;
    raus['items'] = rest;
  }
  raus['minItems'] = Math.max(teile.length, typeof schema['minItems'] === 'number' ? schema['minItems'] : 0);
  if (rest === false) raus['maxItems'] = teile.length;
  return raus;
}

// ---------------------------------------------------------------------------------- graph_lesen

export interface GraphLesenKnoten {
  nodeId: string;
  typ: string;
  label: string;
  x: number;
  y: number;
  eingeklappt: boolean;
  eingaenge: { name: string; typ: string; label: string; nurVon?: readonly string[]; kante: { edgeId: string; von: string; port: string } | null }[];
  ausgaenge: { name: string; typ: string; label: string; kanten: { edgeId: string; nach: string; port: string }[] }[];
  parameter: Record<string, string | number | boolean>;
  /** Der letzte Lauf des Knotens (Laufzeit), `null`: keiner. */
  lauf: { status: string; stufe?: string; jobId?: string; seed?: number; guete?: string; laufNummer?: number; fehler?: string; wartetGrund?: string; mitBild: boolean } | null;
  /** Nur am Render-Knoten: die Grundlage aus den Parametern, `null`: keine. */
  grundlage?: { id: string; seed: number; kameras: number; ebenen: string[] } | null;
  /** Nur am Render-Knoten: die Wahl am Schalter «Güte». */
  guete?: 'vorschau' | 'voll';
  /** Typ nicht im Katalog (Alt-Stand/Import). */
  unbekannterTyp?: true;
  /**
   * Nur am Knoten «Kamera» (L4-4): die gesicherten Blicke, die er anbietet. Gesetzt wird einer mit
   * vis_nodeParametrieren `{ art: 'blick', blick: '<Name>' }` oder `{ art: 'blick', blickId: '…' }`.
   */
  blicke?: { blickId: string; name: string }[];
}

export interface GraphLesenGraph {
  graphId: string;
  name: string;
  /** Der Graph, den die Knotenansicht gerade zeigt. */
  gezeigt: boolean;
  knoten: GraphLesenKnoten[];
  kanten: { edgeId: string; from: string; fromPort: string; to: string; toPort: string }[];
}

export interface GraphLesenDaten {
  graphen: GraphLesenGraph[];
  renderAuftrag: unknown;
  katalog?: { typ: string; label: string; hilfe: string; eingaenge: string[]; ausgaenge: string[] }[];
}

function leseKnoten(graph: VisGraph, n: VisNode, doc: KosmoDoc): GraphLesenKnoten {
  const kat = VIS_NODE_KATALOG[n.typ];
  const lauf = useVisRuntime.getState().laeufe[n.id];
  const params = n.params ?? {};
  const k: GraphLesenKnoten = {
    nodeId: n.id,
    typ: n.typ,
    label: kat?.label ?? n.typ,
    x: n.x,
    y: n.y,
    eingeklappt: n.collapsed === true,
    eingaenge: (kat?.inputs ?? []).map((p) => {
      const e = graph.edges.find((x) => x.to === n.id && x.toPort === p.name);
      return {
        name: p.name,
        typ: p.typ,
        label: p.label,
        ...(p.nurVon ? { nurVon: p.nurVon } : {}),
        kante: e ? { edgeId: e.id, von: e.from, port: e.fromPort } : null,
      };
    }),
    ausgaenge: (kat?.outputs ?? []).map((p) => ({
      name: p.name,
      typ: p.typ,
      label: p.label,
      kanten: graph.edges.filter((x) => x.from === n.id && x.fromPort === p.name).map((x) => ({ edgeId: x.id, nach: x.to, port: x.toPort })),
    })),
    parameter: { ...params },
    lauf: lauf
      ? {
          status: lauf.status,
          ...(lauf.stufe !== undefined ? { stufe: lauf.stufe } : {}),
          ...(lauf.jobId !== undefined ? { jobId: lauf.jobId } : {}),
          ...(lauf.seed !== undefined ? { seed: lauf.seed } : {}),
          ...(lauf.guete !== undefined ? { guete: lauf.guete } : {}),
          ...(lauf.laufNummer !== undefined ? { laufNummer: lauf.laufNummer } : {}),
          ...(lauf.fehler !== undefined ? { fehler: lauf.fehler } : {}),
          ...(lauf.wartetGrund !== undefined ? { wartetGrund: lauf.wartetGrund } : {}),
          mitBild: typeof lauf.bild === 'string' && lauf.bild.length > 0,
        }
      : null,
    ...(kat ? {} : { unbekannterTyp: true as const }),
  };
  if (n.typ === 'kamera') k.blicke = waehlbareBlicke(doc).map((b) => ({ blickId: b.id, name: b.name }));
  if (n.typ === 'render') {
    const g = grundlageAmKnoten(params);
    k.grundlage = g ? { id: g.id, seed: g.seed, kameras: g.kameras, ebenen: g.ebenen } : null;
    k.guete = gueteAmKnoten(params);
  }
  return k;
}

/** Die Daten von `graph_lesen` — rein lesend (Dokument und Laufzeit bleiben, wie sie sind). */
export function graphLesen(doc: KosmoDoc, args: { graphId?: string; katalog?: boolean } = {}): GraphLesenDaten {
  const gezeigt = useVisRuntime.getState().aktiverGraphId;
  const alle = doc.byKind<VisGraph>('visgraph');
  const graphen = (args.graphId ? alle.filter((g) => g.id === args.graphId) : alle).map(
    (g): GraphLesenGraph => ({
      graphId: g.id,
      name: g.name,
      gezeigt: g.id === gezeigt || (gezeigt === null && alle.length === 1),
      knoten: g.nodes.map((n) => leseKnoten(g, n, doc)),
      kanten: g.edges.map((e) => ({ edgeId: e.id, from: e.from, fromPort: e.fromPort, to: e.to, toPort: e.toPort })),
    }),
  );
  return {
    graphen,
    renderAuftrag: doc.settings.visRenderAuftrag ?? null,
    ...(args.katalog
      ? {
          katalog: Object.values(VIS_NODE_KATALOG).map((t) => ({
            typ: t.typ,
            label: t.label,
            hilfe: t.hilfe,
            eingaenge: t.inputs.map((p) => `${p.name}:${p.typ}`),
            ausgaenge: t.outputs.map((p) => `${p.name}:${p.typ}`),
          })),
        }
      : {}),
  };
}

// ---------------------------------------------------------------------------------- Aufruf, Karte, Ereignis

export interface KiAufruf {
  /** Eindeutig je Aufruf (Swift: «K-1», «K-2» …). */
  kennung: string;
  werkzeug: string;
  argumente?: unknown;
  urheber?: KiUrheber;
}

export interface KiErgebnis {
  kennung: string;
  ok: boolean;
  text: string;
  /** Maschinenlesbar: bei graph_lesen die Daten, nach dem Anwenden die neuen Kennungen. */
  daten?: unknown;
}

export interface KiSchritt {
  commandId: string;
  /** Parameter wie geschickt — «$neu:N» bleibt stehen und wird erst beim Ausfuehren aufgeloest. */
  params: unknown;
  zusammenfassung: string;
}

export interface KiVorschlag {
  kennung: string;
  werkzeug: string;
  art: KiWerkzeugArt;
  urheber: KiUrheber;
  zusammenfassung: string;
  schritte: KiSchritt[];
}

export type KiAntwort = { sofort: KiErgebnis } | { karte: KiVorschlag };

export interface KiNeueKennungen {
  knoten: { nodeId: string; typ: string; graphId: string }[];
  graphen: string[];
  kanten: { edgeId: string; graphId: string }[];
}

export type KiEreignis =
  | { art: 'taetigkeit'; phase: 'beginn'; kennung: string; werkzeug: string; urheber: KiUrheber; zeit: number }
  | { art: 'taetigkeit'; phase: 'ende'; kennung: string; werkzeug: string; urheber: KiUrheber; zeit: number; ok: boolean; text: string }
  | { art: 'karte'; vorschlag: KiVorschlag }
  | { art: 'entschieden'; kennung: string; angewendet: boolean; ergebnis: KiErgebnis }
  /** Der KI-Verlauf hat sich geaendert (Schritt dazu, zurueckgenommen, verworfen): je Urheber der letzte stehende Schritt. */
  | { art: 'kiverlauf'; anzahl: number; letzter: Record<KiUrheber, KiSchrittKurz | null> };

/** Ein KI-Schritt ohne Karte (Coop/Voll), wie ihn der Wirt zeigt. */
export interface KiSchrittKurz {
  kennung: string;
  urheber: KiUrheber;
  zusammenfassung: string;
}

const zuhoerer = new Set<(e: KiEreignis) => void>();
const offen = new Map<string, KiVorschlag>();

/** Ereignisse abonnieren (Taetigkeit beginnt/endet, Karte liegt, Karte entschieden). Liefert das Abbestellen. */
export function abonniere(fn: (e: KiEreignis) => void): () => void {
  zuhoerer.add(fn);
  return () => void zuhoerer.delete(fn);
}

function melde(e: KiEreignis): void {
  for (const fn of zuhoerer) {
    try {
      fn(e);
    } catch (err) {
      console.error('[ki-werkzeuge] Zuhoerer warf', err);
    }
  }
}

function beginne(a: KiAufruf, urheber: KiUrheber): void {
  melde({ art: 'taetigkeit', phase: 'beginn', kennung: a.kennung, werkzeug: a.werkzeug, urheber, zeit: Date.now() });
}

function beende(kennung: string, werkzeug: string, urheber: KiUrheber, e: KiErgebnis): void {
  melde({ art: 'taetigkeit', phase: 'ende', kennung, werkzeug, urheber, zeit: Date.now(), ok: e.ok, text: e.text });
}

/** Die offenen Karten, aelteste zuerst. */
export function offeneVorschlaege(): KiVorschlag[] {
  return [...offen.values()];
}

function alsObjekt(x: unknown): Record<string, unknown> {
  return x && typeof x === 'object' && !Array.isArray(x) ? (x as Record<string, unknown>) : {};
}

const NICHTS = ' — nichts wurde vorgeschlagen.';

/**
 * Einen Aufruf behandeln. `{ sofort }`: fertig (Lesen, Fehler, oder ohne Karte angewendet).
 * `{ karte }`: ein Vorschlag liegt; die Antwort kommt mit `anwenden`/`ablehnen`.
 * Ein Aufruf mit einer Kennung, deren Karte schon liegt, legt keine zweite an.
 */
export function behandle(aufruf: KiAufruf, modus: KiModus = 'karte'): KiAntwort {
  const urheber: KiUrheber = aufruf.urheber ?? 'claude';
  const schon = offen.get(aufruf.kennung);
  if (schon) return { karte: schon };
  beginne(aufruf, urheber);
  const antwort = behandleIntern(aufruf, modus, urheber);
  if ('sofort' in antwort) beende(aufruf.kennung, aufruf.werkzeug, urheber, antwort.sofort);
  else {
    offen.set(antwort.karte.kennung, antwort.karte);
    melde({ art: 'karte', vorschlag: antwort.karte });
  }
  return antwort;
}

/** `params.blick` ohne `blickKamera` an vis_nodeParametrieren / vis_nodeSetzen (Typ kamera): ergaenzt. */
function mitBlickKamera(doc: KosmoDoc, commandId: string, argumente: unknown): unknown {
  if (commandId !== 'vis.nodeParametrieren' && commandId !== 'vis.nodeSetzen') return argumente;
  const a = alsObjekt(argumente);
  if (commandId === 'vis.nodeSetzen' && a['typ'] !== 'kamera') return argumente;
  const p = a['params'];
  if (!p || typeof p !== 'object' || Array.isArray(p)) return argumente;
  const neu = blickAufrufErgaenzen(doc, p as Record<string, string | number | boolean>);
  return neu === p ? argumente : { ...a, params: neu };
}

function behandleIntern(aufruf: KiAufruf, modus: KiModus, urheber: KiUrheber): KiAntwort {
  const { kennung, werkzeug } = aufruf;
  const doc = useProject.getState().doc;
  if (werkzeug === GRAPH_LESEN) {
    const roh = alsObjekt(aufruf.argumente);
    const args = {
      ...(typeof roh['graphId'] === 'string' ? { graphId: roh['graphId'] } : {}),
      ...(roh['katalog'] === true ? { katalog: true } : {}),
    };
    const daten = graphLesen(doc, args);
    if (daten.graphen.length === 0) {
      const text = args.graphId
        ? `FEHLER: Render-Graph «${args.graphId}» existiert nicht. graph_lesen ohne graphId nennt alle.`
        : 'Kein Render-Graph im Projekt — lege mit vis_graphErstellen einen an.';
      return { sofort: { kennung, ok: !args.graphId, text, daten } };
    }
    return { sofort: { kennung, ok: true, text: JSON.stringify(daten), daten } };
  }
  const schritte: { name: string; argumente: unknown }[] =
    werkzeug === VIS_PAKET ? [] : [{ name: werkzeug, argumente: aufruf.argumente }];
  if (werkzeug === VIS_PAKET) {
    const roh = alsObjekt(aufruf.argumente)['schritte'];
    if (!Array.isArray(roh) || roh.length === 0) return fehler(kennung, `«schritte» ist eine nicht leere Liste von {befehl, argumente}${NICHTS}`);
    if (roh.length > VIS_PAKET_MAX_SCHRITTE) return fehler(kennung, `höchstens ${VIS_PAKET_MAX_SCHRITTE} Schritte je Paket (geschickt: ${roh.length})${NICHTS}`);
    for (const x of roh) {
      const e = alsObjekt(x);
      schritte.push({ name: typeof e['befehl'] === 'string' ? e['befehl'] : '', argumente: e['argumente'] ?? {} });
    }
  }
  // Probelauf in Reihenfolge auf einer Kopie (ein Einzelaufruf ist ein Paket mit einem Schritt):
  // das Projekt bleibt unveraendert, spaetere Schritte sehen die Kennungen der frueheren.
  const bekannt = new Set(visBefehle().map((c) => c.id));
  const kopie = kopiereDoc(doc);
  const probeNeu: string[] = [];
  const fehlerListe: string[] = [];
  const geprueft: KiSchritt[] = [];
  let art: KiWerkzeugArt = 'aendern';
  let patchSumme = 0;
  schritte.forEach((s, i) => {
    probeNeu.push('');
    const commandId = befehlFuer(s.name);
    const vor = werkzeug === VIS_PAKET ? `Schritt ${i} (${s.name || '?'}): ` : '';
    if (!bekannt.has(commandId)) {
      return void fehlerListe.push(`${vor}${s.name === VIS_PAKET ? '«vis_paket» lässt sich nicht verschachteln' : s.name === GRAPH_LESEN ? '«graph_lesen» ändert nichts — einzeln aufrufen' : `Unbekanntes Werkzeug «${s.name}»`}`);
    }
    const kaputt = sammleNeuVerweise(s.argumente).find((n) => n >= i || probeNeu[n] === '');
    if (kaputt !== undefined) return void fehlerListe.push(`${vor}«$neu:${kaputt}» zeigt auf keinen früheren Schritt, der etwas neu anlegt`);
    // L4-4: ein gesicherter Blick nur mit Namen bekommt hier seine Kamera — aus der Liste, die der
    // Knoten zeigt (auch die des Wirts). Gespeichert wird der ergaenzte Aufruf, damit «Anwenden»
    // dasselbe schreibt wie der Probelauf.
    let argumente: unknown;
    try {
      argumente = mitBlickKamera(doc, commandId, s.argumente ?? {});
    } catch (err) {
      return void fehlerListe.push(`${vor}${err instanceof Error ? err.message : String(err)}`);
    }
    const params = ersetzeNeuVerweise(argumente, probeNeu);
    const cmd = getCommand(commandId)!;
    const parsed = cmd.params.safeParse(params);
    if (!parsed.success) return void fehlerListe.push(`${vor}${parsed.error.issues.map((x) => `${x.path.join('.') || '(root)'}: ${x.message}`).join('; ')}`);
    let r: ExecutionResult;
    try {
      r = execute(kopie, commandId, params, { actor: urheber === 'claude' ? 'claude' : 'kosmo' });
    } catch (err) {
      return void fehlerListe.push(`${vor}${err instanceof Error ? err.message : String(err)}`);
    }
    const neu = neueKennungen(r.patches);
    probeNeu[i] = neu.knoten[0]?.nodeId ?? neu.graphen[0] ?? neu.kanten[0]?.edgeId ?? '';
    patchSumme += r.patches.length;
    const a = artVonBefehl(commandId);
    if (ART_STRENGE[a] > ART_STRENGE[art]) art = a;
    geprueft.push({ commandId, params: argumente, zusammenfassung: r.summary });
  });
  if (fehlerListe.length > 0) {
    if (werkzeug !== VIS_PAKET) return fehler(kennung, `${fehlerListe[0]}${NICHTS}`);
    return fehler(
      kennung,
      `im Probelauf: ${fehlerListe.length} von ${schritte.length} Schritten ungültig — ${fehlerListe.join(' · ')}. Das Paket gilt als EIN Schritt, darum wurde nichts vorgeschlagen; schicke es korrigiert als Ganzes neu.`,
    );
  }
  if (patchSumme === 0) {
    // EIN LESENDER LAUF (z.B. vis_varianten mit stand:true): seine Zusammenfassung IST die Antwort.
    const saetze = geprueft.map((g) => g.zusammenfassung).filter(Boolean).join(' · ');
    return { sofort: { kennung, ok: true, text: `OHNE ÄNDERUNG: der Probelauf ergab keine Änderung, keine Karte.${saetze ? ` ${saetze}` : ''}` } };
  }
  const vorschlag: KiVorschlag = {
    kennung,
    werkzeug,
    art,
    urheber,
    zusammenfassung:
      werkzeug === VIS_PAKET ? `Paket: ${geprueft.length} Schritte als ein Schritt (ein Rückgängig) — ${geprueft.map((g) => g.zusammenfassung).join(' · ')}` : geprueft[0]!.zusammenfassung,
    schritte: geprueft,
  };
  if (brauchtKarte(art, modus)) return { karte: vorschlag };
  // Coop/Voll und «aendern»: sofort, mit dem Urheber im Journal — im KI-Verlauf, nicht in der
  // Rueckgaengig-Kette des Architekten (Entscheid 114).
  const knopf = urheber === 'claude' ? 'Claudes letzten Schritt zurücknehmen' : 'Letzten Schritt des Assistenten zurücknehmen';
  return {
    sofort: fuehreAus(
      vorschlag,
      urheber === 'claude' ? 'claude' : 'kosmo',
      `ANGEWENDET (${modus === 'voll' ? 'Voll' : 'Coop'}, ohne Karte; der Architekt nimmt es in der Leiste mit «${knopf}» zurück — Strg+Z trifft nur seine eigenen Schritte)`,
      true,
    ),
  };
}

function fehler(kennung: string, text: string): KiAntwort {
  return { sofort: { kennung, ok: false, text: `FEHLER: ${text}` } };
}

/**
 * «Anwenden»: die Karte als EINE Rueckgaengig-Gruppe ueber `runCommand` (Akteur 'kosmo'). Die
 * Antwort nennt die NEUEN Kennungen (nodeId bei vis_nodeSetzen, Nr. 54). `null`: keine solche Karte.
 */
export function anwenden(kennung: string): KiErgebnis | null {
  const v = offen.get(kennung);
  if (!v) return null;
  offen.delete(kennung);
  const ergebnis = fuehreAus(v, 'kosmo', 'ANGEWENDET vom Architekten');
  melde({ art: 'entschieden', kennung, angewendet: true, ergebnis });
  beende(kennung, v.werkzeug, v.urheber, ergebnis);
  return ergebnis;
}

/** «Ablehnen»: nichts aendert sich. `null`: keine solche Karte. */
export function ablehnen(kennung: string): KiErgebnis | null {
  const v = offen.get(kennung);
  if (!v) return null;
  offen.delete(kennung);
  const ergebnis: KiErgebnis = { kennung, ok: false, text: 'ABGELEHNT: Der Architekt hat den Vorschlag abgelehnt; das Projekt ist unverändert.' };
  melde({ art: 'entschieden', kennung, angewendet: false, ergebnis });
  beende(kennung, v.werkzeug, v.urheber, ergebnis);
  return ergebnis;
}

/** Anwenden (`ja`) oder Ablehnen — der eine Knopfweg der Karte. */
export function entscheide(kennung: string, ja: boolean): KiErgebnis | null {
  return ja ? anwenden(kennung) : ablehnen(kennung);
}

/** Alle offenen Karten fallen weg (Mappe gewechselt); je Karte geht «VERWORFEN» hinaus. */
export function verwirfVorschlaege(grund: string): KiErgebnis[] {
  const weg = [...offen.values()];
  offen.clear();
  // Die KI-Schritte gehoerten zur alten Mappe: dort gibt es nichts mehr zurueckzunehmen.
  if (kiVerlauf.length > 0) {
    kiVerlauf.length = 0;
    letzterKiEintrag = null;
    meldeKiVerlauf();
  }
  return weg.map((v) => {
    const ergebnis: KiErgebnis = { kennung: v.kennung, ok: false, text: `VERWORFEN: ${grund} — «${v.zusammenfassung}» wurde nicht angewendet; nichts wurde geändert.` };
    melde({ art: 'entschieden', kennung: v.kennung, angewendet: false, ergebnis });
    beende(v.kennung, v.werkzeug, v.urheber, ergebnis);
    return ergebnis;
  });
}

/**
 * Ausfuehren als EINE Rueckgaengig-Gruppe: erst Probe auf frischer Kopie (scheitert ein Schritt,
 * bleibt das Projekt unberuehrt), dann echt ueber `runCommand`; «$neu:N» wird mit den ECHTEN
 * Kennungen aufgeloest. Scheitert der echte Lauf doch, wird die Gruppe zurueckgenommen.
 */
function fuehreAus(v: KiVorschlag, actor: NonNullable<ExecuteOptions['actor']>, kopf: string, imKiVerlauf = false): KiErgebnis {
  const lauf = (ausf: (id: string, p: unknown) => ExecutionResult, erg: ExecutionResult[]): void => {
    const neu: string[] = [];
    for (const s of v.schritte) {
      const r = ausf(s.commandId, ersetzeNeuVerweise(s.params, neu));
      const k = neueKennungen(r.patches);
      neu.push(k.knoten[0]?.nodeId ?? k.graphen[0] ?? k.kanten[0]?.edgeId ?? '');
      erg.push(r);
    }
  };
  const fehlschlag = (e: unknown): KiErgebnis => ({
    kennung: v.kennung,
    ok: false,
    text: `FEHLGESCHLAGEN: ${e instanceof Error ? e.message : String(e)} — nichts wurde geändert.`,
  });
  try {
    const kopie = kopiereDoc(useProject.getState().doc);
    lauf((id, p) => execute(kopie, id, p, { actor }), []);
  } catch (e) {
    return fehlschlag(e);
  }
  const ergebnisse: ExecutionResult[] = [];
  if (imKiVerlauf) {
    // ENTSCHEID 114: ausserhalb der Kette des Architekten. Scheitert der echte Lauf doch (der
    // Probelauf ging), bleibt das schon Gelaufene als KI-Schritt stehen und laesst sich in der
    // Leiste zuruecknehmen — nichts verschwindet still (wie `versucheCoopPaket`).
    let fehlerImLauf: unknown = null;
    const vorDoc = useProject.getState().doc;
    try {
      ohneVerlauf(() => lauf((id, p) => useProject.getState().runCommand(id, p, { actor }), ergebnisse));
    } catch (e) {
      fehlerImLauf = e;
    }
    const patches = ergebnisse.flatMap((r) => r.patches);
    if (patches.length > 0) {
      merkeKiSchritt({ kennung: v.kennung, urheber: v.urheber, zusammenfassung: ergebnisse.map((r) => r.summary).join(' · '), patches, doc: vorDoc });
    }
    if (fehlerImLauf) {
      const e = fehlschlag(fehlerImLauf);
      return patches.length > 0
        ? { ...e, text: `FEHLGESCHLAGEN: ${fehlerImLauf instanceof Error ? fehlerImLauf.message : String(fehlerImLauf)} — teilweise angewendet; der Architekt nimmt es in der Leiste zurück.` }
        : e;
    }
  } else {
    const { history } = useProject.getState();
    let fertig = false;
    history.beginGroup();
    try {
      lauf((id, p) => useProject.getState().runCommand(id, p, { actor }), ergebnisse);
      fertig = true;
    } catch (e) {
      return fehlschlag(e);
    } finally {
      history.endGroup();
      if (!fertig && ergebnisse.some((r) => r.patches.length > 0)) useProject.getState().undo();
    }
  }
  const neu = neueKennungen(ergebnisse.flatMap((r) => r.patches));
  const betroffen = [...new Set(ergebnisse.flatMap((r) => r.patches).filter((p) => !isSettingsPatch(p)).map((p) => (p as { id: string }).id))];
  const teile = [
    ...neu.knoten.map((k) => `NEUE nodeId «${k.nodeId}» (${k.typ}) in graphId «${k.graphId}»`),
    ...neu.graphen.map((g) => `NEUE graphId «${g}»`),
    ...neu.kanten.map((k) => `NEUE edgeId «${k.edgeId}»`),
  ];
  const paket = v.schritte.length > 1 ? ` (Paket, ${v.schritte.length} Schritte, ein Rückgängig)` : '';
  return {
    kennung: v.kennung,
    ok: true,
    text: `${kopf}${paket}: ${ergebnisse.map((r) => r.summary).join(' · ')}${teile.length ? ` — ${teile.join('; ')}` : ''}${betroffen.length ? ` — betroffene Kennungen: ${betroffen.join(', ')}` : ''}`,
    daten: { neu, betroffen },
  };
}

// ---------------------------------------------------------------------------------- KI-Verlauf (Entscheid 114)

/** Ein KI-Schritt ohne Karte, mit seinen Patches — zuruecknehmbar, solange das Dokument dasselbe ist. */
export interface KiVerlaufSchritt extends KiSchrittKurz {
  patches: readonly AnyPatch[];
  /** Das Dokument, in dem der Schritt lief — nach einem Mappenwechsel zaehlt er nicht mehr. */
  doc: KosmoDoc;
  zurueckgenommen: boolean;
}

/** So viele KI-Schritte bleiben (wie `COOP_GRUPPEN_MAX` dort klein gehalten); aeltere fallen weg. */
export const KI_VERLAUF_MAX = 200;
const kiVerlauf: KiVerlaufSchritt[] = [];
let letzterKiEintrag: JournalEntry | null = null;

function merkeKiSchritt(s: Omit<KiVerlaufSchritt, 'zurueckgenommen'>): void {
  kiVerlauf.push({ ...s, zurueckgenommen: false });
  while (kiVerlauf.length > KI_VERLAUF_MAX) kiVerlauf.shift();
  letzterKiEintrag = useProject.getState().journal.at(-1) ?? null;
  meldeKiVerlauf();
}

/** Die stehenden KI-Schritte im offenen Dokument, aelteste zuerst. */
export function kiSchritte(): KiVerlaufSchritt[] {
  const doc = useProject.getState().doc;
  return kiVerlauf.filter((s) => !s.zurueckgenommen && s.doc === doc);
}

/** Der letzte stehende KI-Schritt — eines Urhebers oder ueberhaupt. */
export function letzterKiSchritt(urheber?: KiUrheber): KiSchrittKurz | null {
  const s = [...kiSchritte()].reverse().find((x) => urheber === undefined || x.urheber === urheber);
  return s ? { kennung: s.kennung, urheber: s.urheber, zusammenfassung: s.zusammenfassung } : null;
}

function meldeKiVerlauf(): void {
  melde({ art: 'kiverlauf', anzahl: kiSchritte().length, letzter: { claude: letzterKiSchritt('claude'), assistent: letzterKiSchritt('assistent') } });
}

/** Der Nettowert je Teil eines Schritts: vorher (erster `before`) und nachher (letzter `after`). */
function netto(patches: readonly AnyPatch[]): Map<string, { vor: unknown; nach: unknown }> {
  const n = new Map<string, { vor: unknown; nach: unknown }>();
  const setze = (k: string, vor: unknown, nach: unknown) => {
    const da = n.get(k);
    n.set(k, { vor: da ? da.vor : vor, nach });
  };
  for (const p of patches) {
    if (isSettingsPatch(p)) {
      const felder = new Set([...Object.keys(p.before ?? {}), ...Object.keys(p.after ?? {})]);
      for (const f of felder) setze(`settings:${f}`, (p.before as Record<string, unknown>)[f], (p.after as Record<string, unknown>)[f]);
    } else setze(p.id, p.before, p.after);
  }
  return n;
}

function jetzt(doc: KosmoDoc, k: string): unknown {
  if (k.startsWith('settings:')) return (doc.settings as unknown as Record<string, unknown>)[k.slice('settings:'.length)];
  return doc.get(k) ?? null;
}

/** Vergleich unabhaengig von der Reihenfolge der Felder; `undefined` und `null` gelten gleich. */
function gleich(a: unknown, b: unknown): boolean {
  return festText(a ?? null) === festText(b ?? null);
}

function festText(x: unknown): string {
  if (x === null || typeof x !== 'object') return JSON.stringify(x) ?? 'null';
  if (Array.isArray(x)) return `[${x.map(festText).join(',')}]`;
  const o = x as Record<string, unknown>;
  return `{${Object.keys(o)
    .filter((k) => o[k] !== undefined)
    .sort()
    .map((k) => `${JSON.stringify(k)}:${festText(o[k])}`)
    .join(',')}}`;
}

/** Ein Name fuer einen Teil in einem Satz: Graph oder Einstellung. */
function nameVon(doc: KosmoDoc, k: string): string {
  if (k.startsWith('settings:')) return `Einstellung ${k.slice('settings:'.length)}`;
  const e = doc.get(k) as { kind?: string; name?: string } | undefined;
  return e?.kind === 'visgraph' && e.name ? `Render-Graph «${e.name}»` : k;
}

export interface KiRuecknahme {
  ok: boolean;
  /** Der Satz fuer die Leiste. */
  satz: string;
  /** Die Kennung des zurueckgenommenen (oder angehaltenen) Schritts, `null`: keiner. */
  kennung: string | null;
}

/**
 * «Claudes letzten Schritt zurücknehmen» (Entscheid 114): nimmt den letzten stehenden KI-Schritt
 * (des Urhebers, ohne Angabe: irgendeines) zurueck — als EIN Schritt des Architekten, den er mit
 * Strg+Z wieder herstellen kann. Hat seither jemand an denselben Teilen gearbeitet, aendert sich
 * NICHTS, und der Satz sagt, woran es haengt: fremde Arbeit wird nie ueberschrieben.
 */
export function rueckgaengigKi(urheber?: KiUrheber): KiRuecknahme {
  const s = [...kiSchritte()].reverse().find((x) => urheber === undefined || x.urheber === urheber);
  if (!s) return { ok: false, satz: `Von ${urheber === 'assistent' ? 'dem Assistenten' : urheber === 'claude' ? 'Claude' : 'der KI'} gibt es nichts zurückzunehmen.`, kennung: null };
  const doc = useProject.getState().doc;
  for (const [k, w] of netto(s.patches)) {
    if (!gleich(jetzt(doc, k), w.nach)) {
      return {
        ok: false,
        satz: `«${s.zusammenfassung}» lässt sich nicht zurücknehmen: an ${nameVon(doc, k)} wurde seither weitergearbeitet. Nimm zuerst die spätere Änderung zurück.`,
        kennung: s.kennung,
      };
    }
  }
  const satz = `Zurückgenommen: «${s.zusammenfassung}» (${s.urheber === 'claude' ? 'Claude' : 'Assistent'}).`;
  wendeSchrittAn(invertPatches(s.patches), {
    ts: new Date().toISOString(),
    actor: 'benutzer',
    commandId: 'ki.zuruecknehmen',
    params: { kennung: s.kennung, urheber: s.urheber },
    summary: satz,
  });
  s.zurueckgenommen = true;
  meldeKiVerlauf();
  return { ok: true, satz, kennung: s.kennung };
}

/**
 * Die Wache fuer Strg+Z/Strg+Y des Architekten (`setzeVerlaufWache`, gesetzt vom WIRT): Ohne
 * stehende KI-Schritte prueft sie nichts. Sonst wird ein eigener Schritt nicht blind umgekehrt,
 * wenn die KI seither an denselben Teilen gearbeitet hat — die Umkehr ueberschriebe ihre Arbeit.
 * Ist der letzte Eintrag im Journal ein KI-Schritt, sagt ein Hinweis, warum Strg+Z ihn nicht trifft.
 */
export function kiVerlaufWache(richtung: 'undo' | 'redo', history: History): VerlaufWacheUrteil | null {
  const stehend = kiSchritte();
  if (stehend.length === 0) return null;
  const hinweis =
    richtung === 'undo' && letzterKiEintrag && useProject.getState().journal.at(-1) === letzterKiEintrag
      ? 'Strg+Z nimmt nur deine eigenen Schritte zurück. Claudes Schritte nimmst du in der Leiste zurück («Claudes letzten Schritt zurücknehmen»).'
      : undefined;
  const schritt = richtung === 'undo' ? history.naechsterUndo() : history.naechsterRedo();
  if (!schritt) return hinweis ? { hinweis } : null;
  const doc = useProject.getState().doc;
  for (const [k, w] of netto(schritt)) {
    const ziel = richtung === 'undo' ? w.nach : w.vor;
    if (gleich(jetzt(doc, k), ziel)) continue;
    const ki = [...stehend].reverse().find((x) => netto(x.patches).has(k));
    if (!ki) continue;
    return {
      sperre: `${richtung === 'undo' ? 'Rückgängig' : 'Wiederholen'} geht hier nicht: ${ki.urheber === 'claude' ? 'Claude' : 'Der Assistent'} hat danach an ${nameVon(doc, k)} gearbeitet («${ki.zusammenfassung}»). Nimm diesen Schritt zuerst in der Leiste zurück.`,
    };
  }
  return hinweis ? { hinweis } : null;
}

// ---------------------------------------------------------------------------------- Hilfen

function kopiereDoc(doc: KosmoDoc): KosmoDoc {
  return KosmoDoc.fromJSON(structuredClone(doc.toJSON()));
}

/** Was die Patches neu anlegen: Knoten und Kanten (im Graphen-Patch), ganze Graphen. */
export function neueKennungen(patches: readonly AnyPatch[]): KiNeueKennungen {
  const raus: KiNeueKennungen = { knoten: [], graphen: [], kanten: [] };
  for (const p of patches) {
    if (isSettingsPatch(p)) continue;
    const nach = p.after as VisGraph | null;
    if (!nach || nach.kind !== 'visgraph') continue;
    const vor = p.before as VisGraph | null;
    if (!vor) raus.graphen.push(nach.id);
    const alteKnoten = new Set((vor?.nodes ?? []).map((n) => n.id));
    const alteKanten = new Set((vor?.edges ?? []).map((e: VisEdge) => e.id));
    for (const n of nach.nodes) if (!alteKnoten.has(n.id)) raus.knoten.push({ nodeId: n.id, typ: n.typ, graphId: nach.id });
    for (const e of nach.edges) if (!alteKanten.has(e.id)) raus.kanten.push({ edgeId: e.id, graphId: nach.id });
  }
  return raus;
}

function sammleNeuVerweise(wert: unknown, raus: number[] = []): number[] {
  if (typeof wert === 'string') {
    const m = NEU_VERWEIS.exec(wert);
    if (m) raus.push(Number(m[1]));
  } else if (Array.isArray(wert)) for (const x of wert) sammleNeuVerweise(x, raus);
  else if (wert && typeof wert === 'object') for (const x of Object.values(wert)) sammleNeuVerweise(x, raus);
  return raus;
}

function ersetzeNeuVerweise(wert: unknown, ids: readonly string[]): unknown {
  if (typeof wert === 'string') {
    const m = NEU_VERWEIS.exec(wert);
    return m ? ids[Number(m[1])] || wert : wert;
  }
  if (Array.isArray(wert)) return wert.map((x) => ersetzeNeuVerweise(x, ids));
  if (wert && typeof wert === 'object') return Object.fromEntries(Object.entries(wert).map(([k, x]) => [k, ersetzeNeuVerweise(x, ids)]));
  return wert;
}

// ---------------------------------------------------------------------------------- fuer den Wirt

/**
 * Die Schnittstelle fuer einen Wirt in einem Satz: Visbox haengt sie als `window.visboxKi` an
 * (die Mac-App ruft sie ueber `evaluateJavaScript`) und reicht `abonniere` an
 * `webkit.messageHandlers.visboxKi.postMessage` weiter. Der Modus kommt bei jedem Aufruf mit —
 * eingestellt wird er in der Mac-App (Entscheid 108 A), nicht hier.
 */
export function kiSchnittstelle() {
  return {
    werkzeuge: () => visWerkzeuge(),
    rufe: (aufruf: KiAufruf, modus: KiModus = 'karte') => behandle(aufruf, modus),
    entscheide: (kennung: string, ja: boolean) => entscheide(kennung, ja),
    offene: () => offeneVorschlaege(),
    verwirf: (grund: string) => verwirfVorschlaege(grund),
    /** Entscheid 114: den letzten KI-Schritt ohne Karte zuruecknehmen (Knopf in der Leiste). */
    rueckgaengigKi: (urheber?: KiUrheber) => rueckgaengigKi(urheber),
    /** Je Urheber der letzte stehende KI-Schritt — ob der Knopf in der Leiste steht. */
    kiVerlauf: () => ({ anzahl: kiSchritte().length, letzter: { claude: letzterKiSchritt('claude'), assistent: letzterKiSchritt('assistent') } }),
    abonniere,
  };
}

/** Nur fuer Proben: offene Karten, KI-Verlauf und Zuhoerer leeren. */
export function leereKiZustand(): void {
  offen.clear();
  zuhoerer.clear();
  kiVerlauf.length = 0;
  letzterKiEintrag = null;
}
