import { meldeFehler } from '@kosmo/ui';
import {
  BESTELLFORMAT_VORGABE,
  isVisPresetId,
  KAMERA_AUS_3D_TYP,
  kameraAus3dParams,
  visPresetById,
  type VisGraph,
} from '@kosmo/kernel';
import { useProject } from '../../state/project-store';
import { useSplatEbene } from '../../state/splat-ebene';
import { aktuelleKamera, type ViewportKamera } from '../../state/viewport-kamera';
import { splatRenderKontext, szeneMitSplatKontext } from '../design/splat-render-kontext';
import { freierKnotenPlatz, neuerGraphErstellen } from './vis-graph-aktionen';
import { renderBedienungAusParams } from './vis-jobs';
import { useVisRuntime } from './vis-runtime';

/**
 * **«Kamera aus 3D-Ansicht» — die App-Seite** (Owner-Entscheid 14.10.2026, über die Zentrale).
 *
 * Die Knotenansicht ist die einzige Arbeitsfläche zum Rendern. Der Block «Rendern» der 3D-Ansicht
 * wird zum Zulieferer: sein künftiger Knopf «In KosmoVis rendern» (UI-Worker) ruft
 * `kameraAus3dAnlegen()` und springt danach selbst in die Knotenansicht. Befund von KosmoDraw:
 * der alte Weg (`renderStarten`) schickte keine Kamera — er rechnete also nie den sichtbaren
 * Blick.
 *
 * QUELLE DER KAMERA: allein `aktuelleKamera()` (`state/viewport-kamera.ts`, KosmoDraw). Die Insel
 * muss nichts mitgeben. Gelesen wird beim Anlegen und auf «Kamera übernehmen», nie laufend; die
 * Kamera liegt danach als Knoten-Parameter im Dokument (rückgängig machbar).
 *
 * UMGEBUNG (Splat): `postRenderJob` hängt die sichtbare Splat-Ebene an JEDE Bestellung
 * (`splat-render-kontext.ts`, dieselbe Stelle wie für den Viewport-Render) — ein Render aus diesem
 * Knoten bekommt also dieselbe Umgebung. Der Knoten hält beim Übernehmen fest, was damals mitging
 * (als Satz, ohne Dateipfad), damit man es am Knoten sieht. Was beim Senden gilt, entscheidet
 * weiterhin die eine Stelle in `postRenderJob`, kein zweiter Weg.
 *
 * KEINE BEFEHLSREGISTRATUR: Die Kern-Befehle (`registerCommand`) sind rein auf dem Dokument und
 * können den Store der 3D-Ansicht nicht lesen; die `ui.*`-Registratur (`state/ui-befehle.ts`) ist
 * eingefroren und ausdrücklich ohne Dokument und ohne Rückgängig. Darum folgt der Befehl dem Muster
 * der übrigen Graph-Aktionen (`vis-graph-aktionen.ts`: `kameraVorschlagenAktion`,
 * `dreiStimmungenEinfuegen`): eine exportierte Funktion, die über `runCommand` schreibt.
 */

/** Am Knoten, wenn keine 3D-Ansicht offen ist (Wortlaut aus dem Auftrag). */
export const KEINE_3D_ANSICHT_SATZ = 'Keine 3D-Ansicht offen — erst die 3D-Ansicht öffnen, dann «Kamera übernehmen».';

/** Die Umgebung, wie sie beim Übernehmen stand — `null` ohne Splat-Ebene im Projekt. */
export function umgebungJetzt(): { mit: boolean; satz: string } | null {
  const { ebene, handLage } = useSplatEbene.getState();
  if (!ebene) return null;
  const kontext = splatRenderKontext({ ebene, handLage });
  const { hinweis } = szeneMitSplatKontext({}, kontext);
  if (hinweis) return { mit: false, satz: hinweis };
  if (!kontext.ok) return { mit: false, satz: kontext.grund };
  return { mit: true, satz: `Splat «${ebene.name}» geht als Umgebung mit — ${kontext.context.crs_note}` };
}

/** Knoten-Parameter für die jetzige Kamera, oder `null` ohne offene 3D-Ansicht. */
function paramsJetzt(): { kamera: ViewportKamera; params: Record<string, string | number | boolean> } | null {
  const kamera = aktuelleKamera();
  if (!kamera) return null;
  return { kamera, params: kameraAus3dParams(kamera, umgebungJetzt()) };
}

/**
 * «Kamera übernehmen» am Knoten: liest die Kamera JETZT und setzt sie (und die Umgebung) als
 * Parameter — EIN Befehl, also ein Rückgängig-Schritt. Ohne offene 3D-Ansicht bleibt der Knoten,
 * wie er ist (eine schon übernommene Kamera bleibt stehen), und die Antwort ist `null`.
 */
export function kameraUebernehmen(graphId: string, nodeId: string): ViewportKamera | null {
  const jetzt = paramsJetzt();
  if (!jetzt) return null;
  useProject.getState().runCommand('vis.nodeParametrieren', { graphId, nodeId, params: jetzt.params });
  return jetzt.kamera;
}

/** Parameter für einen NEUEN Knoten (Palette, Anlege-Befehl): beim Anlegen gelesen; `{}` ohne Ansicht. */
export function kameraAus3dStartParams(): Record<string, string | number | boolean> {
  return paramsJetzt()?.params ?? {};
}

/**
 * Bestellformat, mit dem der Knoten sein Blickfeld zeigt: die Auflösung des ersten verbundenen
 * Render-Knotens (gewählte Auflösung vor Voreinstellung vor der Vorgabe 1600 × 1000, dieselbe
 * Reihenfolge wie `sendeGraphRenderAuftrag`). `null`, wenn er an keinem Render-Knoten hängt —
 * dann gilt die Leinwand.
 */
export function bestellformatFuer(graph: VisGraph, nodeId: string): readonly [number, number] | null {
  const kante = graph.edges.find((e) => e.from === nodeId && e.fromPort === 'kameras');
  const render = kante ? graph.nodes.find((n) => n.id === kante.to && n.typ === 'render') : undefined;
  if (!render) return null;
  const params = render.params ?? {};
  const gewaehlt = renderBedienungAusParams(params).resolution;
  if (gewaehlt) return gewaehlt;
  const preset = isVisPresetId(params['preset']) ? visPresetById(params['preset']) : undefined;
  return preset?.render.resolution ?? BESTELLFORMAT_VORGABE;
}

/**
 * Antwort von `kameraAus3dAnlegen`.
 *
 * - `knotenId`/`graphId`: der Knoten «Kamera aus 3D-Ansicht» und sein Graph.
 * - `neu`: `true`, wenn er eben angelegt wurde; `false`, wenn es ihn schon gab.
 * - `kamera`: die übernommene Kamera — oder `null`, wenn KEINE 3D-Ansicht offen war. Das ist der
 *   Fehlerzustand: ein neuer Knoten steht dann ohne Kamera da (er sagt es selbst), ein vorhandener
 *   behält seine alte. Die Oberfläche sollte dann nicht in die Knotenansicht springen, sondern
 *   `KEINE_3D_ANSICHT_SATZ` zeigen.
 * - `verbunden`: die Render-Knoten, deren Eingang «Kamera-Standpunkte» jetzt an diesem Knoten
 *   hängt (nur beim Neuanlegen; leer, wenn es keinen gab).
 */
export interface KameraAus3dErgebnis {
  knotenId: string;
  graphId: string;
  neu: boolean;
  kamera: ViewportKamera | null;
  verbunden: string[];
}

function zielGraph(graphIdVorgabe: string | undefined): string | undefined {
  const { doc } = useProject.getState();
  const gueltig = (id: string | null | undefined): id is string => !!id && doc.get<VisGraph>(id)?.kind === 'visgraph';
  if (gueltig(graphIdVorgabe)) return graphIdVorgabe;
  const aktiv = useVisRuntime.getState().aktiverGraphId;
  if (gueltig(aktiv)) return aktiv;
  const graphen = doc.byKind<VisGraph>('visgraph');
  // Ein Graph mit Render-Knoten geht vor: dorthin gehört die Kamera.
  return (graphen.find((g) => g.nodes.some((n) => n.typ === 'render')) ?? graphen[0])?.id;
}

/**
 * **Der Anlege-Befehl** (für den Knopf «In KosmoVis rendern» des UI-Workers).
 *
 * - Gibt es im Ziel-Graphen noch keinen Knoten «Kamera aus 3D-Ansicht»: legt ihn an (freier Platz
 *   links der Render-Knoten), verbindet ihn mit dem Eingang «Kamera-Standpunkte» JEDES
 *   Render-Knotens dieses Graphen (eine bestehende Kamera-Linie dort wird ersetzt, wie beim
 *   Verbinden von Hand) und übernimmt die Kamera sofort — alles in EINER Rückgängig-Klammer.
 * - Gibt es ihn schon: setzt nur dessen Kamera und Umgebung neu (ein Rückgängig-Schritt), kein
 *   zweiter Knoten, keine neuen Linien.
 * - Ziel-Graph: `graphIdVorgabe`, sonst der aktive, sonst der erste mit Render-Knoten, sonst der
 *   erste. Gibt es gar keinen, entsteht ein leerer Graph mit NUR diesem Knoten — der fertige
 *   Anfang (Modell, Render …) wird nicht von selbst angelegt.
 * - Springt NICHT in die Knotenansicht; das macht die Oberfläche. Macht den Ziel-Graphen aber zum
 *   aktiven, damit die Knotenansicht ihn zeigt, wenn sie geöffnet wird.
 *
 * Antwort: `KameraAus3dErgebnis`, oder `null`, wenn ein Befehl scheiterte (die Meldung steht dann
 * schon, `meldeFehler`; die Klammer ist dann ganz zurückgenommen).
 */
export function kameraAus3dAnlegen(graphIdVorgabe?: string): KameraAus3dErgebnis | null {
  const { history } = useProject.getState();
  const vorhandenIn = (gid: string | undefined) =>
    gid ? useProject.getState().doc.get<VisGraph>(gid)?.nodes.find((n) => n.typ === KAMERA_AUS_3D_TYP) : undefined;

  const gidVorher = zielGraph(graphIdVorgabe);
  const vorhanden = vorhandenIn(gidVorher);
  if (gidVorher && vorhanden) {
    try {
      const kamera = kameraUebernehmen(gidVorher, vorhanden.id);
      useVisRuntime.getState().setAktiverGraphId(gidVorher);
      return { knotenId: vorhanden.id, graphId: gidVorher, neu: false, kamera, verbunden: [] };
    } catch (err) {
      meldeFehler(err);
      return null;
    }
  }

  const jetzt = paramsJetzt();
  let fertig = false;
  let geschrieben = false;
  history.beginGroup();
  try {
    let gid = gidVorher;
    if (!gid) {
      gid = neuerGraphErstellen();
      if (!gid) return null;
      geschrieben = true;
    }
    const { runCommand } = useProject.getState();
    const graph = useProject.getState().doc.get<VisGraph>(gid)!;
    const renders = graph.nodes.filter((n) => n.typ === 'render');
    // Wunschplatz: links neben dem ersten Render-Knoten, auf seiner Höhe; ohne Render oben links.
    const erster = renders[0];
    const wunsch = erster ? { x: erster.x - 260, y: erster.y } : { x: 40, y: 40 };
    const platz = freierKnotenPlatz(graph.nodes, KAMERA_AUS_3D_TYP, wunsch);
    runCommand('vis.nodeSetzen', {
      graphId: gid,
      typ: KAMERA_AUS_3D_TYP,
      x: platz.x,
      y: platz.y,
      ...(jetzt ? { params: jetzt.params } : {}),
    });
    geschrieben = true;
    const nachher = useProject.getState().doc.get<VisGraph>(gid)!;
    const knotenId = nachher.nodes[nachher.nodes.length - 1]!.id;
    for (const r of renders) {
      runCommand('vis.verbinden', { graphId: gid, from: knotenId, fromPort: 'kameras', to: r.id, toPort: 'kameras' });
    }
    useVisRuntime.getState().setAktiverGraphId(gid);
    fertig = true;
    return { knotenId, graphId: gid, neu: true, kamera: jetzt?.kamera ?? null, verbunden: renders.map((r) => r.id) };
  } catch (err) {
    meldeFehler(err);
    return null;
  } finally {
    history.endGroup();
    // Halb angelegt ist schlechter als gar nicht: scheitert ein Schritt, nimmt EIN Rückgängig
    // die ganze Klammer zurück (Muster `wendePaketAn`, `state/project-store.ts`).
    if (!fertig && geschrieben) useProject.getState().undo();
  }
}
