import { create } from 'zustand';
import {
  BESTELLFORMAT_VORGABE,
  evaluiereGraph,
  findeVariantenKnotenIn,
  gewaehlteAchsen,
  graphMitStimmung,
  KAMERA_RICHTUNGEN,
  richtungenAusWahl,
  setzeVariantenStandLeser,
  VARIANTEN_TYP,
  variantenLaufId,
  variantenRenderKnoten,
  VIS_STIMMUNGEN,
  verfuegbareEntwuerfe,
  verfuegbareStandpunkte,
  verfuegbareStimmungen,
  type JournalEntry,
  type KosmoDoc,
  type VariantenAchsen,
  type VariantenEntwurf,
  type VariantenStandpunkt,
  type VisGraph,
  type VisNode,
} from '@kosmo/kernel';
import { melde, meldeFehler } from '@kosmo/ui';
import { useProject } from '../../state/project-store';
import { entwuerfeOhneBestand, OHNE_BESTAND_MELDUNG_MS, ohneBestandSatz } from './kontext-hinweis';
import {
  abbrechenJob,
  bescheideBridgeCatch,
  freigebenJob,
  mappeJobStatus,
  renderBedienungAusParams,
  sendeGraphRenderAuftrag,
  varianteAufGrundlage,
  zeitText,
  zeitschaetzungSekunden,
} from './vis-jobs';
import { useVisRuntime, type NodeLauf } from './vis-runtime';
import { heimStandpunkte } from './heim-standpunkte';
import { kameraQaZeilen, qaUrteil, type LizenzAngabe, type QaUrteil } from './varianten-diff';
import { gueteAmKnoten, type Guete } from './guete';
import { freiesBildAmKnoten } from './freies-bild';
import type { LaufModus } from './modus';
import { modusFuerKamera } from './modus-marke';
import { mitZahl } from './einzahl';

/**
 * **«Varianten mit einem Klick» — die App-Seite** (Owner-Entscheide 92/92a/92b der Visbox,
 * Blatt 23; L24 Bildweg Varianten, E246). Rechnung der Achsen im Kern (`derive/varianten.ts`),
 * hier: was waehlbar ist, Senden, eine Freigabe fuer alle, das Raster und der Stand fuer Kosmo
 * und Claude.
 *
 * **Ein Weg zum Senden.** Der Knopf am Knoten ruft `vis.varianten` (Kern, ein
 * Rueckgaengig-Schritt), genauso wie Kosmo und Claude ueber ihre Karte. Gesendet wird, sobald
 * dieser Befehl im Journal steht (`beobachteJournal` unten) — nicht bei einem Patch, der ueber
 * den Abgleich von einem anderen Geraet kommt, und nicht bei Rueckgaengig/Wiederholen (die
 * schreiben kein Journal). Je Stimmung und Entwurf geht EIN Auftrag mit allen Standpunkten an
 * `sendeGraphRenderAuftrag` — dieselbe Bestellung wie «Ausführen» am Render-Knoten, mit der
 * Stimmung, den Kameras und dem Modell der Zelle (`VarianteDesAuftrags`).
 *
 * **Laufzeit ≠ Modell.** Die Laeufe stehen in `vis-runtime.ts` unter `variantenLaufId`; welche
 * Bestellung zu welchem Knoten gehoert, haelt der kleine Speicher `useVariantenBestellung`. Nichts
 * davon geht ins Dokument.
 */

/**
 * Ungefaehre Rechenzeit der KI-Veredelung je Bild, in Sekunden — ANNAHME, nicht am Gerät
 * gemessen: 47 s mit dem Vorgabemodell `z-image-turbo`, die Zahl der HomeStation aus
 * `auf-20260923-155` (Visbox, «349 s statt rund 47 s je Bild»). Dazu kommt der Cycles-Teil aus
 * `zeitschaetzungSekunden` (auf zwei Messpunkte der Chronik gerechnet). Warten auf das
 * Leerlauffenster ist nicht darin.
 */
export const KI_SEKUNDEN_JE_BILD_ANNAHME = 47;

/**
 * Visbox-Gegenprobe 330 (B2, 22.10.2026): Zuschlag je Bild, wenn die Variante OHNE Grundlage des
 * Render-Knotens rechnet — der Heim-PC rechnet dann Blender neu und waehlt aus drei Startwerten den mit
 * der besten Umrisstreue. Nachgeeicht, nicht hergeleitet: Bei zwei Bildern (1600 × 1000, 128 Abtastungen)
 * mass die Visbox 194 s (328) und 205 s (330), im Mittel rund 100 s je Bild; Cycles-Rechnung und 47 s
 * ergeben 91 s. Die 47 s allein trafen die Variante AUF der Grundlage (ein Startwert, kein Blender):
 * 92 s fuer zwei Bilder (330 S6).
 */
export const STARTWERTAUSWAHL_SEKUNDEN_JE_BILD_ANNAHME = 9;

/** Woher die Zahl kommt — steht neben der Warnung, damit niemand sie fuer gemessen haelt. */
export const DAUER_ANNAHME_SATZ =
  'Ungefähr: rund 47 s KI je Bild (Vorgabemodell, Angabe der HomeStation). Liegt am Render-Knoten die Grundlage, bleibt es dabei; sonst kommen Cycles (aus zwei gemessenen Läufen hochgerechnet) und die Wahl aus drei Startwerten dazu — Warten auf die GPU nicht eingerechnet.';

/** Die eine Zeile, wenn die Skizze das Bild fuehrt (Entscheid 96): ihr Standpunkt ist der der Mappe. */
export const SKIZZE_STANDPUNKT = 'Standpunkt der Skizze';

export interface VariantenAuswahl {
  render?: VisNode;
  /** Was waehlbar ist. Leer und `heim` gesetzt: die Gegenseite rechnet ihre eigenen Richtungen. */
  standpunkte: VariantenStandpunkt[];
  /** Visbox: die Richtungen des Heim-PCs, die mit `cameras: 'auto'` alle zusammen kommen. */
  heim?: string[];
  /**
   * Mac-Probe 0.3.66: Visbox, bestellt mit `standpunkte` (`vis_varianten`) — nur diese Richtungen (Kuerzel) gehen als
   * `cameras_auto.richtungen` hinaus, `heim` nennt nur sie.
   */
  richtungen?: string[];
  stimmungen: { id: string; label: string }[];
  entwuerfe: VariantenEntwurf[];
  achsen: VariantenAchsen;
  /** Zeilen des Rasters (Namen), in Reihenfolge. */
  zeilen: string[];
  anzahl: number;
  /**
   * Ungefaehre Sekunden je Bild (Annahme, s. `KI_SEKUNDEN_JE_BILD_ANNAHME`), gemittelt ueber die
   * Auftraege der Bestellung: einer auf der Grundlage des Render-Knotens zaehlt nur den KI-Schritt.
   */
  sekundenJeBild: number;
}

/**
 * Was der Knoten zeigt und bestellt — eine Stelle fuer Knoten, Befehl und Stand. `richtungen` (Mac-Probe 0.3.66): die
 * mit `vis.varianten` bestellten Richtungen, wenn der Kern keine eigenen Standpunkte kennt (Visbox).
 */
export function variantenAuswahl(doc: KosmoDoc, graph: VisGraph, node: VisNode, richtungen?: readonly string[]): VariantenAuswahl {
  const render = variantenRenderKnoten(graph, node.id);
  const standpunkte = verfuegbareStandpunkte(doc, graph, render?.id);
  const stimmungen = verfuegbareStimmungen(VIS_STIMMUNGEN);
  const entwuerfe = verfuegbareEntwuerfe(doc);
  const achsen = gewaehlteAchsen(
    node.params,
    standpunkte.map((s) => s.name),
    stimmungen.map((s) => s.id),
    entwuerfe.map((e) => e.id),
  );
  // Entscheid 96 (Visbox, «die Skizze fuehrt das Bild», eigener Zweig): haengt am Render-Knoten
  // eine Skizze (Eingang «skizze»), ist jedes Bild EINES vom Standpunkt der Mappe — eine
  // Kameraliste weist der Vertrag dann ab. Die Standpunkte-Achse hat dann genau eine Zeile.
  const mitSkizze = !!render && graph.edges.some((e) => e.to === render.id && e.toPort === 'skizze');
  if (mitSkizze) {
    return {
      ...(render ? { render } : {}),
      standpunkte: [],
      heim: [SKIZZE_STANDPUNKT],
      stimmungen,
      entwuerfe,
      achsen: { ...achsen, standpunkte: [] },
      zeilen: [SKIZZE_STANDPUNKT],
      anzahl: achsen.stimmungen.length * achsen.entwuerfe.length,
      sekundenJeBild: render ? sekundenJeBild(doc, graph, render, { achsen, standpunkte: [], entwuerfe, ohneKameraliste: true }) : 0,
    };
  }
  const nur = standpunkte.length === 0 && richtungen && richtungen.length > 0 ? [...richtungen] : undefined;
  const heim = nur ? nur.map(richtungsName) : standpunkte.length === 0 ? heimRichtungen(doc, graph, render) : undefined;
  const zeilen = heim && heim.length > 0 ? heim : achsen.standpunkte;
  return {
    ...(render ? { render } : {}),
    standpunkte,
    ...(heim && heim.length > 0 ? { heim } : {}),
    ...(nur ? { richtungen: nur } : {}),
    stimmungen,
    entwuerfe,
    achsen,
    zeilen,
    anzahl: zeilen.length * achsen.stimmungen.length * achsen.entwuerfe.length,
    sekundenJeBild: render ? sekundenJeBild(doc, graph, render, { achsen, standpunkte, entwuerfe, ohneKameraliste: !!heim, ...(nur ? { richtungen: nur } : {}) }) : 0,
  };
}

/** Der Name einer Richtung fuer das Raster — der des Heim-PCs, sonst der am Knoten «Kamera», sonst das Kuerzel. */
function richtungsName(kuerzel: string): string {
  return richtungsNamen().find((r) => r.kuerzel === kuerzel)?.name ?? kuerzel;
}

/**
 * Generalprobe 327 (S3, 22.10.2026): die Richtungen, die mit `cameras: 'auto'` zusammen kommen. Stellt
 * der Knoten «Kamera» (Auto) eigene Richtungen ein, gehen genau diese als `cameras_auto` hinaus — der
 * Knoten nannte trotzdem die drei der Vorgabe des Heim-PCs («Süd, Südost, Nordwest» bei SO + NW), und
 * im Raster stand für «Süd» «fehlgeschlagen — kein Bild». Ohne Modell (keine Heim-Standpunkte) bleibt
 * es wie bisher: keine Richtungen.
 */
function heimRichtungen(doc: KosmoDoc, graph: VisGraph, render: VisNode | undefined): string[] | undefined {
  const vorgabe = heimStandpunkte()?.standpunkte;
  if (!vorgabe) return undefined;
  const auto = render ? evaluiereGraph(doc, graph).renderAuftraege.get(render.id)?.kamerasAuto : undefined;
  if (!auto) return vorgabe.map((h) => h.name);
  return auto.richtungen.map(
    (k) => vorgabe.find((h) => h.kuerzel === k)?.name ?? KAMERA_RICHTUNGEN.find((r) => r.kuerzel === k)?.name ?? k,
  );
}

/** Kürzel → Name für das Raster: die des Heim-PCs, dazu alle Richtungen des Knotens «Kamera». */
function richtungsNamen(): { name: string; kuerzel: string }[] {
  return [...(heimStandpunkte()?.standpunkte ?? []), ...KAMERA_RICHTUNGEN];
}

/**
 * Visbox-Gegenprobe 330 (B2, 22.10.2026): Der Knoten schaetzte «ungefähr 3 min 2 s» fuer zwei Bilder,
 * gerechnet waren sie in 92 s — die Bestellung lief auf der Grundlage des Render-Knotens (kein Blender,
 * ein Startwert), die Schaetzung zaehlte trotzdem Cycles dazu. Jetzt fragt sie je Auftrag der Bestellung
 * (Entwurf × Stimmung, wie `sendeVarianten`) dieselbe Regel wie die Bestellung
 * (`varianteAufGrundlage`): auf der Grundlage nur der KI-Schritt, sonst Cycles, KI und die Wahl aus
 * drei Startwerten. Jeder Auftrag hat gleich viele Bilder, also ist das Mittel die Zahl je Bild.
 */
function sekundenJeBild(
  doc: KosmoDoc,
  graph: VisGraph,
  render: VisNode,
  auswahl: { achsen: VariantenAchsen; standpunkte: VariantenStandpunkt[]; entwuerfe: VariantenEntwurf[]; ohneKameraliste: boolean; richtungen?: string[] },
): number {
  const roh = evaluiereGraph(doc, graph).renderAuftraege.get(render.id);
  const bedienung = renderBedienungAusParams(render.params ?? {});
  const samples = bedienung.samples ?? roh?.samples ?? 128;
  const format = bedienung.resolution ?? roh?.resolution ?? BESTELLFORMAT_VORGABE;
  const cycles = zeitschaetzungSekunden(samples, format);
  if (roh?.nurCycles) return cycles;
  const ohneGrundlage = cycles + KI_SEKUNDEN_JE_BILD_ANNAHME + STARTWERTAUSWAHL_SEKUNDEN_JE_BILD_ANNAHME;
  const kameraVon = new Map(auswahl.standpunkte.map((s) => [s.name, s.kamera]));
  const kameras = auswahl.ohneKameraliste ? undefined : auswahl.achsen.standpunkte.map((n) => kameraVon.get(n)!).filter(Boolean);
  const entwuerfe = auswahl.entwuerfe.filter((e) => auswahl.achsen.entwuerfe.includes(e.id));
  const je: number[] = [];
  for (const entwurf of entwuerfe) {
    for (const stimmung of auswahl.achsen.stimmungen) {
      const mit = graphMitStimmung(graph, render.id, stimmung);
      const auf = varianteAufGrundlage(doc, mit.graph, render.id, {
        ...(kameras ? { kameras } : {}),
        ...(auswahl.richtungen ? { richtungen: auswahl.richtungen } : {}),
        ...(entwurf.kombination ? { entwurf: entwurf.kombination } : {}),
      });
      je.push(auf ? KI_SEKUNDEN_JE_BILD_ANNAHME : ohneGrundlage);
    }
  }
  return je.length === 0 ? ohneGrundlage : je.reduce((a, b) => a + b, 0) / je.length;
}

/** «ungefähr 4 min 30 s» — die Dauer einer Bestellung (Annahme, s. `DAUER_ANNAHME_SATZ`). */
export function ungefaehreDauer(anzahl: number, sekundenJeBild: number): string {
  return `ungefähr ${zeitText(Math.round(anzahl * sekundenJeBild))}`;
}

/** Entscheid 92b: der Satz der Warnung ab 12 Bildern, z. B. «12 Bilder dauern ungefähr 18 min». */
export function dauerSatz(anzahl: number, sekundenJeBild: number): string {
  return `${anzahl} Bilder dauern ${ungefaehreDauer(anzahl, sekundenJeBild)}`;
}

/* ─────────────────────────────── Bestellung ─────────────────────────────── */

/** Ein Auftrag der Bestellung: eine Stimmung, ein Entwurf, alle Standpunkte. */
export interface VariantenGruppe {
  laufId: string;
  stimmung: string;
  entwurf: string;
  /** Die bestellten Standpunkte in Reihenfolge; leer = die Gegenseite waehlt (`cameras: 'auto'`). */
  standpunkte: string[];
  /** Ging nicht hinaus (der Weg meldete schon warum). */
  nichtGesendet?: true;
}

export interface VariantenBestellung {
  graphId: string;
  nodeId: string;
  nr: number;
  zeilen: string[];
  stimmungen: string[];
  entwuerfe: { id: string; name: string }[];
  gruppen: VariantenGruppe[];
  anzahl: number;
}

interface BestellSpeicher {
  bestellungen: Record<string, VariantenBestellung>;
  setze: (b: VariantenBestellung) => void;
}

export const useVariantenBestellung = create<BestellSpeicher>((set) => ({
  bestellungen: {},
  setze: (b) => set((s) => ({ bestellungen: { ...s.bestellungen, [b.nodeId]: b } })),
}));

/**
 * Sendet die Bestellung des Knotens: je Entwurf und Stimmung einen Auftrag. Scheitert schon der
 * erste am Weg selbst (keine Szene, keine Geometrie, keine Kamera), gehen die uebrigen nicht
 * hinaus — sie scheiterten am selben Grund, und die Meldung stuende N-mal da.
 */
export function sendeVarianten(graphId: string, nodeId: string, wunsch?: { richtungen?: readonly string[] }): VariantenBestellung | null {
  const { doc } = useProject.getState();
  const graph = doc.get<VisGraph>(graphId);
  const node = graph?.nodes.find((n) => n.id === nodeId);
  if (!graph || !node || node.typ !== VARIANTEN_TYP) return null;
  const a = variantenAuswahl(doc, graph, node, wunsch?.richtungen);
  if (!a.render) {
    melde('Der Varianten-Knoten hängt an keinem Render-Knoten — verbinde Render «Bild» mit Varianten «Render».', { ton: 'fehler' });
    return null;
  }
  if (a.anzahl === 0) {
    melde('Nichts zu bestellen — mindestens ein Standpunkt, eine Stimmung und ein Entwurf.', { ton: 'fehler' });
    return null;
  }
  const kameraVon = new Map(a.standpunkte.map((s) => [s.name, s.kamera]));
  const kameras = a.heim ? undefined : a.achsen.standpunkte.map((n) => kameraVon.get(n)!).filter(Boolean);
  const entwuerfe = a.entwuerfe.filter((e) => a.achsen.entwuerfe.includes(e.id));
  // L4-5: blendet ein Entwurf den ganzen Bestand aus, steht das Bild ohne Nachbarn — gesagt beim Bestellen.
  const ohneBestand = ohneBestandSatz(entwuerfeOhneBestand(doc, entwuerfe));
  if (ohneBestand) melde(ohneBestand, { dauerMs: OHNE_BESTAND_MELDUNG_MS });
  // Entscheid 143 (Owner, 24.10.2026): Varianten rechnen voll — vom Grundbild, Bildeingang 0,7 (Visbox-Entscheid 149, vorher 0,5) nach
  // Entscheid 138. Bis hierhin ging der Varianten-Knoten ohne Feld hinaus (auch voll, aber nur, weil
  // die Gegenseite «fehlt» als voll liest); jetzt sagt die Bestellung es selbst. Eine am Knoten
  // ausdruecklich gewaehlte Vorschau (`guete: 'vorschau'`, ueber `vis.nodeParametrieren`) bleibt
  // Vorschau. Ohne KI-Schritt (Skizze, Strichzeichnung, «nur Cycles») laesst `sendeGraphRenderAuftrag`
  // das Feld weg — der Vertrag weist `vis.guete` mit `vis.skip` ab.
  const guete = gueteAmKnoten(node.params, 'variante');
  // Visbox-Entscheid 149: am Haken «Freies Bild (ohne Grundbild)» — sonst die Vorgabe (vom Grundbild, 0,7).
  const freiesBild = freiesBildAmKnoten(node.params);
  const gruppen: VariantenGruppe[] = [];
  let abbruch = false;
  for (const entwurf of entwuerfe) {
    for (const stimmung of a.achsen.stimmungen) {
      const laufId = variantenLaufId(nodeId, stimmung, entwurf.id);
      const bestellt = a.richtungen ? [...a.heim!] : a.heim ? (a.heim[0] === SKIZZE_STANDPUNKT ? [SKIZZE_STANDPUNKT] : []) : [...a.achsen.standpunkte];
      const gruppe: VariantenGruppe = { laufId, stimmung, entwurf: entwurf.id, standpunkte: bestellt };
      if (abbruch) {
        gruppen.push({ ...gruppe, nichtGesendet: true });
        continue;
      }
      const mit = graphMitStimmung(graph, a.render.id, stimmung);
      const vorher = useVisRuntime.getState().laeufe[laufId];
      try {
        sendeGraphRenderAuftrag(graphId, a.render.id, undefined, {
          guete,
          // Immer gesetzt: die Wahl des Varianten-Knotens gilt, nicht die am Render-Knoten.
          freiesBild,
          variante: {
            graph: mit.graph,
            laufId,
            ...(kameras ? { kameras } : {}),
            // Mac-Probe 0.3.66: nur die bestellten Richtungen (Visbox) — sonst rechnete der Heim-PC alle.
            ...(a.richtungen ? { richtungen: a.richtungen } : {}),
            ...(mit.ohneStimmungsKnoten ? { promptVorsatz: VIS_STIMMUNGEN[stimmung]?.prompt ?? '' } : {}),
            ...(entwurf.kombination ? { entwurf: entwurf.kombination } : {}),
          },
        });
      } catch (err) {
        meldeFehler(err);
      }
      const gesendet = useVisRuntime.getState().laeufe[laufId] !== vorher;
      if (!gesendet) abbruch = true;
      gruppen.push(gesendet ? gruppe : { ...gruppe, nichtGesendet: true });
    }
  }
  const nr = typeof node.params?.['bestellNr'] === 'number' ? node.params['bestellNr'] : 0;
  const bestellung: VariantenBestellung = {
    graphId,
    nodeId,
    nr,
    zeilen: a.zeilen,
    stimmungen: [...a.achsen.stimmungen],
    entwuerfe: entwuerfe.map((e) => ({ id: e.id, name: e.name })),
    gruppen,
    anzahl: a.anzahl,
  };
  useVariantenBestellung.getState().setze(bestellung);
  return bestellung;
}

/** Der Knopf am Knoten: derselbe Befehl wie bei Kosmo und Claude (ein Rueckgaengig-Schritt). */
export function variantenBestellenKlick(graphId: string, nodeId: string): void {
  try {
    void graphId; // der Knoten ist im ganzen Dokument eindeutig; der Befehl braucht nur ihn
    useProject.getState().runCommand('vis.varianten', { nodeId });
  } catch (err) {
    meldeFehler(err);
  }
}

/*
 * Das Journal beobachten: steht dort ein neues `vis.varianten` (ohne `stand`), wird gesendet. Der
 * Befehl selbst hat schon geschrieben (Achsen, `bestellNr`), das Dokument ist also auf dem Stand
 * der Bestellung. Rueckgaengig, Wiederholen und der Abgleich schreiben kein Journal — ein Strg+Z
 * holt keinen Auftrag zurueck (er laeuft drueben schon), und ein Strg+Y schickt keinen zweiten.
 */
const verarbeitet = new WeakSet<JournalEntry>();

export function verarbeiteJournal(neu: readonly JournalEntry[]): void {
  for (const e of neu) {
    if (verarbeitet.has(e)) continue;
    verarbeitet.add(e);
    if (e.commandId !== 'vis.varianten') continue;
    const p = (e.params ?? {}) as { graphId?: unknown; nodeId?: unknown; stand?: unknown; standpunkte?: unknown };
    if (p.stand === true) continue;
    const treffer = findeVariantenKnotenIn(
      useProject.getState().doc,
      typeof p.graphId === 'string' ? p.graphId : undefined,
      typeof p.nodeId === 'string' ? p.nodeId : undefined,
    );
    // Mac-Probe 0.3.66: kennt der Kern keine eigenen Standpunkte (Visbox), sind `standpunkte` Richtungen des
    // Heim-PCs — sie gelten fuer DIESE Bestellung (der Befehl hat sie geprueft; am Knoten stehen sie nicht).
    const wahl = Array.isArray(p.standpunkte) ? p.standpunkte.filter((x): x is string => typeof x === 'string') : [];
    const richtungen = treffer && wahl.length > 0 && verfuegbareStandpunkte(useProject.getState().doc, treffer.graph, variantenRenderKnoten(treffer.graph, treffer.node.id)?.id).length === 0
      ? richtungenAusWahl(wahl).richtungen
      : undefined;
    if (treffer) sendeVarianten(treffer.graph.id, treffer.node.id, richtungen && richtungen.length > 0 ? { richtungen } : undefined);
  }
}

let beobachtet = false;
/** Einmal je Seite; `NodeCanvas.tsx` bindet dieses Modul ein, also laeuft es mit der Vis-Station. */
export function beobachteJournal(): void {
  if (beobachtet) return;
  beobachtet = true;
  for (const e of useProject.getState().journal) verarbeitet.add(e);
  useProject.subscribe((s, vorher) => {
    if (s.journal === vorher.journal) return;
    const alt = new Set(vorher.journal);
    verarbeiteJournal(s.journal.filter((e) => !alt.has(e)));
  });
}

/* ─────────────────────────────── Freigabe ─────────────────────────────── */

/** Die Laeufe der Bestellung, die auf Freigabe warten. */
export function wartendeLaeufe(nodeId: string): { laufId: string; lauf: NodeLauf }[] {
  const b = useVariantenBestellung.getState().bestellungen[nodeId];
  const laeufe = useVisRuntime.getState().laeufe;
  return (b?.gruppen ?? [])
    .map((g) => ({ laufId: g.laufId, lauf: laeufe[g.laufId] }))
    .filter((x): x is { laufId: string; lauf: NodeLauf } => x.lauf?.status === 'wartetFreigabe' && !!x.lauf.jobId && !!x.lauf.approvalToken);
}

/**
 * EINE Freigabe fuer alle (Entscheid 92). Die Bruecke kennt die Freigabe je Auftrag (`/approve`
 * mit dem Token des Auftrags); dieser eine Klick gibt jeden wartenden Auftrag der Bestellung
 * frei. Gibt die Zahl der freigegebenen zurueck.
 */
export async function alleFreigeben(nodeId: string): Promise<number> {
  const { patchLauf } = useVisRuntime.getState();
  const offen = wartendeLaeufe(nodeId);
  const ergebnisse = await Promise.all(
    offen.map(({ laufId, lauf }) =>
      freigebenJob(lauf.jobId!, lauf.approvalToken!)
        .then((j) => {
          patchLauf(laufId, { status: mappeJobStatus(j), wartetGrund: j.message });
          return true;
        })
        .catch(async (err) => {
          await bescheideBridgeCatch(err);
          return false;
        }),
    ),
  );
  return ergebnisse.filter(Boolean).length;
}

const LAEUFT = ['gesendet', 'wartetFreigabe', 'wartetGpu', 'rendert'];

/** Bricht jeden noch offenen Auftrag der Bestellung ab. */
export async function alleAbbrechen(nodeId: string): Promise<number> {
  const b = useVariantenBestellung.getState().bestellungen[nodeId];
  const { laeufe, patchLauf } = useVisRuntime.getState();
  const offen = (b?.gruppen ?? []).filter((g) => {
    const l = laeufe[g.laufId];
    return !!l?.jobId && LAEUFT.includes(l.status);
  });
  const ergebnisse = await Promise.all(
    offen.map((g) =>
      abbrechenJob(laeufe[g.laufId]!.jobId!)
        .then((j) => {
          patchLauf(g.laufId, { status: mappeJobStatus(j), wartetGrund: j.message });
          return true;
        })
        .catch(async (err) => {
          await bescheideBridgeCatch(err);
          return false;
        }),
    ),
  );
  return ergebnisse.filter(Boolean).length;
}

/* ─────────────────────────────── Raster ─────────────────────────────── */

export type ZellenZustand = 'nicht-gesendet' | 'wartet' | 'rechnet' | 'fertig' | 'fehlgeschlagen';

export interface VariantenZelle {
  standpunkt: string;
  stimmung: string;
  entwurf: string;
  zustand: ZellenZustand;
  /** Ein Satz fuer die leere Zelle bzw. die Kurzhilfe. */
  satz: string;
  jobId?: string;
  bild?: string;
  urteil?: QaUrteil;
  /** Blatt 36: was das Ergebnis meldet — «Vorschau» und «Lizenz offen» stehen am Daumen wie am Render-Bild. */
  guete?: Guete;
  /** Wie dieses Bild entstand (Standpunkt-Angabe aus `NodeLauf.modus`) — «Ohne Grundlagenbild» am Daumen. */
  modus?: LaufModus;
  /** Visbox-Entscheid 149: das Ergebnis meldet ein freies Bild — die Marke steht am Daumen. */
  freiesBild?: boolean;
  lizenz?: LizenzAngabe;
}

/**
 * Welches Bild zu welchem Standpunkt gehoert. Der Vertrag liefert `images` als Liste, eines je
 * Kamera, in der Reihenfolge der Bestellung. Sagt das Ergebnis je Kamera, wie viele Bilder es
 * lieferte (`qa_je_kamera[].bilder_ist`), wird danach gezaehlt — so verrutscht nichts, wenn eine
 * Kamera ausfiel. Sonst gilt die Reihenfolge der Bestellung.
 */
export function bilderJeStandpunkt(lauf: NodeLauf | undefined, bestellt: readonly string[], heim?: readonly { name: string; kuerzel: string }[]): Map<string, string> {
  const out = new Map<string, string>();
  const bilder = lauf?.bilder ?? (lauf?.bild ? [lauf.bild] : []);
  const name = (k: string) => heim?.find((h) => h.kuerzel === k || h.name === k)?.name ?? k;
  // Ein einziger bestellter Standpunkt (eine Kamera, oder die Skizze): das erste Bild ist seines,
  // wie die Gegenseite die Kamera auch nennt.
  if (bestellt.length === 1 && bilder[0]) {
    out.set(bestellt[0]!, bilder[0]);
    return out;
  }
  const jeKamera = lauf?.qaJeKamera;
  if (jeKamera && jeKamera.length > 0) {
    let i = 0;
    for (const k of jeKamera) {
      const n = typeof k.bilder_ist === 'number' ? k.bilder_ist : k.lieferstatus === 'geliefert' || k.lieferstatus === undefined ? 1 : 0;
      const b = bilder[i];
      if (n > 0 && b) out.set(name(k.kamera), b);
      i += n;
    }
    return out;
  }
  const reihe = bestellt.length > 0 ? bestellt : (heim ?? []).map((h) => h.name);
  reihe.forEach((s, i) => {
    const b = bilder[i];
    if (b) out.set(s, b);
  });
  return out;
}

const ZUSTAND_SATZ: Record<string, string> = {
  gesendet: 'gesendet — die HomeStation nimmt den Auftrag an',
  wartetFreigabe: 'wartet auf Freigabe',
  wartetGpu: 'wartet auf die GPU',
  rendert: 'rechnet',
};

/** Der Modus-Vermerk einer Zelle: die Angabe ihrer Kamera (Name oder Kuerzel des Standpunkts). Auf die Angabe des
 *  ganzen Laufs faellt sie nur zurueck, wenn der Lauf kein Verzeichnis je Kamera hat. Fehlt die Kamera in einem
 *  vorhandenen Verzeichnis, bekommt die Zelle nichts, sonst truege sie die Marke einer anderen Kamera (Anmerkung KosmoVis). */
export function modusDerZelle(lauf: NodeLauf, standpunkt: string, heim: readonly { name: string; kuerzel: string }[] | undefined): { modus?: LaufModus } {
  if (!lauf.modus) return {};
  const kuerzel = heim?.find((h) => h.name === standpunkt)?.kuerzel;
  const eigen = modusFuerKamera(lauf.modus, kuerzel ? [standpunkt, kuerzel] : [standpunkt]);
  return eigen ? { modus: eigen } : {};
}

/** Die Zellen der letzten Bestellung, Zeile fuer Zeile (Standpunkt), je Stimmung und Entwurf. */
export function variantenZellen(b: VariantenBestellung, laeufe: Record<string, NodeLauf>): VariantenZelle[] {
  const heim = richtungsNamen();
  const zellen: VariantenZelle[] = [];
  for (const g of b.gruppen) {
    const lauf = laeufe[g.laufId];
    // Ohne Kameraliste (`cameras: 'auto'`) gilt die Reihenfolge der Zeilen — die Richtungen des Knotens «Kamera».
    const bilder = bilderJeStandpunkt(lauf, g.standpunkte.length > 0 ? g.standpunkte : b.zeilen, heim);
    const qaZeilen = kameraQaZeilen(lauf?.qaJeKamera);
    for (const standpunkt of b.zeilen) {
      const basis = { standpunkt, stimmung: g.stimmung, entwurf: g.entwurf };
      if (g.nichtGesendet || !lauf) {
        zellen.push({ ...basis, zustand: 'nicht-gesendet', satz: 'nicht gesendet — die Meldung dazu nennt den Grund' });
        continue;
      }
      const jobId = lauf.jobId;
      const mitJob = jobId ? { jobId } : {};
      if (lauf.status === 'fertig') {
        const bild = bilder.get(standpunkt);
        if (!bild) {
          zellen.push({ ...basis, ...mitJob, zustand: 'fehlgeschlagen', satz: 'fehlgeschlagen — für diesen Standpunkt kam kein Bild zurück' });
          continue;
        }
        const qa = qaZeilen.find((z) => z.kamera === standpunkt || heim?.find((h) => h.kuerzel === z.kamera)?.name === standpunkt);
        const urteil: QaUrteil = qa?.bestanden !== undefined ? (qa.bestanden ? 'bestanden' : 'durchgefallen') : qaUrteil(lauf.qa);
        zellen.push({
          ...basis,
          ...mitJob,
          zustand: 'fertig',
          satz: 'fertig',
          bild,
          urteil,
          ...(lauf.guete ? { guete: lauf.guete } : {}),
          ...(lauf.freiesBild === true ? { freiesBild: true } : {}),
          ...modusDerZelle(lauf, standpunkt, heim),
          ...(lauf.lizenzOffen === true
            ? { lizenz: { lizenzOffen: true, engineUsed: lauf.engineUsed, engineLicense: lauf.engineLicense } }
            : {}),
        });
        continue;
      }
      if (lauf.status === 'fehler' || lauf.status === 'zeitueberschreitung' || lauf.status === 'abgebrochen') {
        zellen.push({ ...basis, ...mitJob, zustand: 'fehlgeschlagen', satz: `fehlgeschlagen — ${lauf.fehler ?? (lauf.status === 'abgebrochen' ? 'abgebrochen' : 'ohne Grund')}` });
        continue;
      }
      zellen.push({
        ...basis,
        ...mitJob,
        zustand: lauf.status === 'wartetFreigabe' ? 'wartet' : 'rechnet',
        satz: ZUSTAND_SATZ[lauf.status] ?? 'rechnet',
      });
    }
  }
  return zellen;
}

/* ─────────────────────────────── Daumen am Knoten (Blatt 36) ─────────────────────────────── */

/**
 * Die gewaehlte Variante steht als Parameter im Knoten (`vis.nodeParametrieren`, ein
 * Rueckgaengig-Schritt, gespeichert mit dem Dokument): «Bestellnummer|Standpunkt|Stimmung|Entwurf».
 * Die Bestellnummer gehoert dazu, weil eine neue Bestellung dieselben Achsen mit neuen Bildern
 * fuellt — die Wahl gilt dem Bild, das gesehen wurde, nicht der Achse.
 */
export const VARIANTE_GEWAEHLT_PARAM = 'gewaehlt';

export function zellenSchluessel(nr: number, z: Pick<VariantenZelle, 'standpunkt' | 'stimmung' | 'entwurf'>): string {
  return `${nr}|${z.standpunkt}|${z.stimmung}|${z.entwurf}`;
}

/** Die gewaehlte Zelle der laufenden Bestellung, oder nichts (keine Wahl, oder die Wahl gehoert einer aelteren). */
export function gewaehlteZelle(
  params: Record<string, unknown> | undefined,
  b: VariantenBestellung | undefined,
  zellen: readonly VariantenZelle[],
): VariantenZelle | undefined {
  const wert = params?.[VARIANTE_GEWAEHLT_PARAM];
  if (!b || typeof wert !== 'string' || wert === '') return undefined;
  return zellen.find((z) => zellenSchluessel(b.nr, z) === wert);
}

/** «Abend · Süd», mit dem Entwurf, sobald mehr als einer bestellt ist. */
export function zellenTitel(z: VariantenZelle, b: VariantenBestellung): string {
  const teile = [VIS_STIMMUNGEN[z.stimmung]?.label ?? z.stimmung, z.standpunkt];
  if (b.entwuerfe.length > 1) teile.push(b.entwuerfe.find((e) => e.id === z.entwurf)?.name ?? z.entwurf);
  return teile.join(' · ');
}

/**
 * Gegenprobe 328 (S9): der Teil des Dateinamens, der eine Variante kennzeichnet — Bestellung, Stimmung und
 * (ab zwei Entwuerfen) der Entwurf. Die Kamera traegt der Dateiname des Bildes selbst («sSE.png»).
 */
export function exportZusatzDerZelle(z: VariantenZelle, b: VariantenBestellung): string {
  const teile = [`Varianten-${b.nr}`, VIS_STIMMUNGEN[z.stimmung]?.label ?? z.stimmung];
  if (b.entwuerfe.length > 1) teile.push(b.entwuerfe.find((e) => e.id === z.entwurf)?.name ?? z.entwurf);
  return teile.join('-');
}

/** Setzt oder hebt die Wahl auf — derselbe Befehl, den Kosmo und Claude ueber den Knoten rufen. */
export function varianteWaehlen(graphId: string, nodeId: string, schluessel: string): void {
  try {
    useProject.getState().runCommand('vis.nodeParametrieren', { graphId, nodeId, params: { [VARIANTE_GEWAEHLT_PARAM]: schluessel } });
  } catch (err) {
    meldeFehler(err);
  }
}

/* ─────────────────────────────── Stand fuer Kosmo und Claude ─────────────────────────────── */

const URTEIL_WORT: Record<QaUrteil, string> = {
  bestanden: 'Prüfung bestanden',
  durchgefallen: 'Prüfung durchgefallen',
  'nicht-beurteilbar': 'nicht beurteilbar',
  'ohne-qa': 'ohne Prüfurteil',
};

/** Der Text, den `vis.varianten` mit `stand: true` zurueckgibt. */
export function variantenStandText(graphId: string, nodeId: string): string {
  const b = useVariantenBestellung.getState().bestellungen[nodeId];
  const { doc } = useProject.getState();
  const graph = doc.get<VisGraph>(graphId);
  const node = graph?.nodes.find((n) => n.id === nodeId);
  if (!b) {
    if (!graph || !node) return `Varianten-Knoten «${nodeId}»: nicht gefunden.`;
    const a = variantenAuswahl(doc, graph, node);
    // Die Werkzeugbeschreibung ist mit Absicht knapp (Sperre fuer die Werkzeugliste, 15.10.2026);
    // was waehlbar ist, sagt darum dieser Text — Kosmo liest ihn mit `stand: true` vor dem Bestellen.
    return (
      `Varianten-Knoten «${nodeId}»: in dieser Sitzung noch nichts bestellt. Gewählt: ${mitZahl(a.anzahl, 'Bild', 'Bilder')} — ` +
      `Standpunkte ${a.zeilen.map((z) => `«${z}»`).join(', ') || 'keine'}; Stimmungen ${a.achsen.stimmungen.join(', ')}; ` +
      `Entwürfe ${a.achsen.entwuerfe.join(', ')}. Wählbar: standpunkte ` +
      `${a.heim ? `(die des Heim-PCs kommen zusammen: ${a.heim.join(', ')})` : a.standpunkte.map((x) => `«${x.name}»`).join(', ') || 'keine'}; ` +
      `stimmungen ${a.stimmungen.map((x) => x.id).join(', ')}; entwuerfe ${a.entwuerfe.map((x) => `${x.id} (${x.name})`).join(', ')}.`
    );
  }
  const zellen = variantenZellen(b, useVisRuntime.getState().laeufe);
  const zaehle = (z: ZellenZustand) => zellen.filter((c) => c.zustand === z).length;
  const entwurfName = (id: string) => b.entwuerfe.find((e) => e.id === id)?.name ?? id;
  const kopf =
    `Varianten-Knoten «${nodeId}», Bestellung ${b.nr}: ${mitZahl(zellen.length, 'Bild', 'Bilder')} — ${zaehle('fertig')} fertig, ` +
    `${mitZahl(zaehle('wartet'), 'wartet', 'warten')} auf Freigabe, ${mitZahl(zaehle('rechnet'), 'rechnet', 'rechnen')}, ` +
    `${zaehle('fehlgeschlagen')} fehlgeschlagen` +
    `${zaehle('nicht-gesendet') ? `, ${zaehle('nicht-gesendet')} nicht gesendet` : ''}. ${b.gruppen.length === 1 ? 'Auftrag' : 'Aufträge'}: ` +
    b.gruppen.map((g) => `${g.stimmung}/${entwurfName(g.entwurf)} = ${useVisRuntime.getState().laeufe[g.laufId]?.jobId ?? 'ohne Kennung'}`).join(', ') +
    '.';
  const zeilen = zellen.map(
    (c) =>
      `«${c.standpunkt}» · ${VIS_STIMMUNGEN[c.stimmung]?.label ?? c.stimmung} · ${entwurfName(c.entwurf)}: ${c.satz}` +
      `${c.bild ? `, Bild ${c.bild}` : ''}${c.urteil ? `, ${URTEIL_WORT[c.urteil]}` : ''}`,
  );
  const wahl = gewaehlteZelle(node?.params, b, zellen);
  const gewaehlt = wahl
    ? [`Gewählt: «${wahl.standpunkt}» · ${VIS_STIMMUNGEN[wahl.stimmung]?.label ?? wahl.stimmung} · ${entwurfName(wahl.entwurf)}${wahl.bild ? `, Bild ${wahl.bild}` : ''}.`]
    : [];
  return [kopf, ...gewaehlt, ...zeilen].join('\n');
}

setzeVariantenStandLeser(variantenStandText);
beobachteJournal();
