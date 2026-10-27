/**
 * **Der letzte fertige Lauf eines Render-Knotens übersteht das Öffnen** (Visbox-Mac-Prüfliste 0.3.41,
 * 22.10.2026, Mappe «Haus am Hang»).
 *
 * ## Der Befund
 *
 * Nach dem Öffnen einer Mappe stand am Render-Knoten «Bild erscheint hier», obwohl das KI-Bild des
 * letzten Laufs in der Mappe lag. Die Ursache ist keine Regression, sondern ein Weg, den es nie gab:
 * Die Läufe (`useVisRuntime.laeufe`) sind reine Laufzeit — sie leben im Arbeitsspeicher der Seite,
 * kein Dokument, kein Speicher. Der Graph übersteht das Neuladen (in Visbox `graph-sichern.ts`, in
 * KosmoOrbit das Dokument), aber **nichts im Graph sagte, welcher Auftrag zu welchem Knoten gehört**.
 * Der Auftrag am Heim-PC kennt seinen Knoten nicht (der Vertrag trägt keine Knotenkennung), und die
 * Mappe am Mac kennt nur die Liste ihrer Aufträge. Nach dem Öffnen war der Knoten darum leer.
 *
 * ## Die Regel
 *
 * 1. **Merken:** Wird ein Lauf eines Render-Knotens mit Bild fertig, legt der Poll seine Kennung am
 *    Knoten ab (`LETZTER_LAUF_PARAM`, ein JSON-Text: Kennung, `memoKey`, Stufe, Grundlage-Stand) —
 *    **ohne Rückgängig-Schritt** (`ohneVerlauf`): Es ist kein Schritt des Architekten, und Strg+Z soll
 *    nicht das Bild vom Knoten nehmen. Der Graph wird damit wie jede andere Änderung gesichert.
 * 2. **Wiederholen:** Öffnet die Knotenansicht einen Graph, fragt sie für jeden Render-Knoten **ohne**
 *    Lauf, aber mit gemerkter Kennung, den Auftrag einmal ab (`holeJob` — in Visbox beantwortet die
 *    Mac-App das ohne Heim-PC aus dem Laufzettel der Mappe, die Bilder aus `bilder/<auftrag>/`). Ist er
 *    fertig mit Bild, steht der Lauf wieder am Knoten — mit denselben Feldern, die der Poll setzt
 *    (`ergebnisFelder`, EINE Quelle für beide).
 * 3. **Still, wenn nichts da ist:** Kennt die Gegenseite den Auftrag nicht mehr, ist er nicht fertig
 *    oder ohne Bild, bleibt der Knoten wie bisher leer — keine Meldung, kein «rendert …», keine
 *    Zeitüberschreitung. Ein schon laufender oder neuer Lauf am Knoten wird nie überschrieben.
 *
 * `memoKey` und Stufe gehen mit, damit «veraltet» nach dem Öffnen dasselbe sagt wie vorher: Hat sich
 * der Prompt oder (bei «Grundlage rendern») der Stand inzwischen geändert, steht das Bild als veraltet.
 *
 * Grenze: Läufe, die VOR dieser Regel fertig wurden, tragen keine Kennung am Knoten — ihr Bild kommt
 * nicht zurück; der nächste fertige Lauf wird gemerkt. Der ältere Verlauf eines Knotens wird nicht
 * wiederhergestellt.
 *
 * ## Nachtrag Generalprobe 373 (S8/B7, 27.10.2026)
 *
 * 4. **Ein Lauf ohne Bild verdrängt das gemerkte nicht.** Steht am Knoten schon ein Lauf, der (noch)
 *    kein Bild hat — bestellt, bevor das Wiederholen fertig war, abgebrochen oder gescheitert —, kommt
 *    der gemerkte Lauf in den Verlauf statt an den Knoten. Knoten, Bildvergleich und Blatt nehmen ihn
 *    von dort (`letzterFertigerLauf`, `vis-runtime.ts`). Bis hierhin blieb er dann ganz weg.
 * 5. **Varianten ebenso.** Der Varianten-Knoten merkt sich seine letzte Bestellung samt der Kennung
 *    jedes fertigen Auftrags (`LETZTE_BESTELLUNG_PARAM`, ohne Rückgängig-Schritt); nach dem Öffnen stehen
 *    Bestellung und fertige Bilder wieder an Knoten und Bildvergleich (`holeLetzteVarianten`). Vorher
 *    waren beide nach einem Neustart leer (B7).
 */
import type { VisGraph } from '@kosmo/kernel';
import type { RenderJob } from '@kosmo/contracts';
import { ohneVerlauf, useProject } from '../../state/project-store';
import { grundlageLaufFelder } from './grundlage';
import { gueteAusErgebnis } from './guete';
import { modusAusErgebnis } from './modus';
import { freiesBildAusErgebnis } from './freies-bild';
import { grundbildZumBild } from './nebeneinander';
import { laufMitBild, useVisRuntime, type NodeLauf } from './vis-runtime';

type Ergebnis = NonNullable<RenderJob['result']>;

/** Der Parameter am Render-Knoten, der den letzten fertigen Lauf nennt (JSON-Text). */
export const LETZTER_LAUF_PARAM = 'letzterLauf';

/** Form der Auftragskennung, wie im Vertrag (`RenderJob.job_id`). */
const KENNUNG = /^vis-\d+-[0-9a-f]{6}$/;

/** Was am Knoten über seinen letzten fertigen Lauf steht. */
export interface LetzterLauf {
  jobId: string;
  memoKey: string;
  stufe?: 'grundlage' | 'variante';
  grundlageStand?: string;
}

/** Der gemerkte letzte Lauf am Knoten — `null`, wenn keiner oder unlesbar. */
export function letzterLaufAmKnoten(params: Record<string, unknown> | undefined): LetzterLauf | null {
  const roh = params?.[LETZTER_LAUF_PARAM];
  if (typeof roh !== 'string' || roh === '') return null;
  let wert: unknown;
  try {
    wert = JSON.parse(roh);
  } catch {
    return null;
  }
  if (!wert || typeof wert !== 'object') return null;
  const w = wert as Record<string, unknown>;
  if (typeof w['jobId'] !== 'string' || !KENNUNG.test(w['jobId'])) return null;
  if (typeof w['memoKey'] !== 'string') return null;
  const stufe = w['stufe'] === 'grundlage' || w['stufe'] === 'variante' ? w['stufe'] : undefined;
  const stand = typeof w['grundlageStand'] === 'string' ? w['grundlageStand'] : undefined;
  return {
    jobId: w['jobId'],
    memoKey: w['memoKey'],
    ...(stufe ? { stufe } : {}),
    ...(stand ? { grundlageStand: stand } : {}),
  };
}

/** Der Text des Parameters (stabile Reihenfolge, nur gesetzte Felder). */
export function letzterLaufText(l: LetzterLauf): string {
  return JSON.stringify({
    jobId: l.jobId,
    memoKey: l.memoKey,
    ...(l.stufe ? { stufe: l.stufe } : {}),
    ...(l.grundlageStand ? { grundlageStand: l.grundlageStand } : {}),
  });
}

/**
 * Die Felder, die ein Ergebnis an den Lauf schreibt — EINE Quelle für den Poll (`NodeCanvas.tsx`)
 * und das Wiederholen nach dem Öffnen. `fertigUm` ist beim Poll «jetzt», beim Wiederholen die Zeit
 * des Auftrags.
 */
export function ergebnisFelder(
  r: Ergebnis,
  lauf: Pick<NodeLauf, 'stufe' | 'grundlageId'>,
  fertigUm: number = Date.now(),
): Partial<NodeLauf> {
  // P11/B7 — «fertig» nur MIT mindestens einem Bild. Ein eingebettetes Ergebnis ohne Bild
  // (vertragskonform, `images: []`) ist keine Erfolgsmeldung — s. `mappeJobStatus`-Kommentar
  // (`vis-jobs.ts`) für dieselbe Lehre am anderen Aufrufer.
  const hatBild = r.images.length > 0;
  return {
    status: hatBild ? 'fertig' : 'fehler',
    bild: r.images[0] ?? '',
    // L24 Bildweg Varianten (E246): alle Bilder, eines je Kamera — fuer das Raster.
    bilder: r.images,
    // Entscheid 117a (W-4): das Grundbild zur Kamera des Hauptbilds. Nach «Grundlage rendern» IST das Bild
    // das Grundbild — dann keines daneben. Immer gesetzt, auch als `undefined` (patchLauf mischt).
    grundbild: lauf.stufe === 'grundlage' ? undefined : grundbildZumBild(r.ebenen, r.images[0] ?? '', r.images, r.qa_je_kamera),
    // Entscheid 68 / E174: der Verlauf nennt die Uhrzeit des Ergebnisses.
    fertigUm,
    qa: r.qa,
    // N4 — additiv, nur wenn der Worker es geschickt hat. Kein Default: ein fehlendes Feld heisst
    // «je Kamera nichts gesagt».
    ...(r.qa_je_kamera ? { qaJeKamera: r.qa_je_kamera } : {}),
    // kv-lieferstatus-null (L1): der Lieferstatus geht mit, `null` eingeschlossen; die Anzeige macht
    // daraus den Vorbehalt, nie «geliefert».
    lieferstatus: r.lieferstatus,
    ...(r.lieferstatus_grund !== undefined ? { lieferstatusGrund: r.lieferstatus_grund } : {}),
    // P-LIZENZMARKE Schritt 2 (E154 (4)): die Lizenzmarke und die beiden Felder daneben gehen mit.
    // Immer ausdruecklich gesetzt, auch als `undefined`: `patchLauf` mischt, und eine alte Marke darf
    // nicht stehen bleiben.
    lizenzOffen: r.engine_license_open === true ? true : undefined,
    engineUsed: r.engine_used,
    engineLicense: r.engine_license,
    // Entscheid 104a: die Guete, die das Ergebnis meldet — immer gesetzt, auch als `undefined`, damit
    // der Vermerk «Vorschau» eines frueheren Laufs nicht stehen bleibt.
    guete: gueteAusErgebnis(r),
    // Bitte UI «Modus-Marke» (C17 A1): wie das KI-Bild entstand — immer gesetzt, auch als `undefined`.
    modus: modusAusErgebnis(r),
    // Visbox-Entscheid 149: das freie Bild, wie das Ergebnis es meldet — immer gesetzt, auch als `undefined`.
    freiesBild: freiesBildAusErgebnis(r),
    // Nr. 85 Paket 2: auf welcher Grundlage das Bild steht (und ob sie wiederverwendet wurde) —
    // Startwert und Pose je Kamera reisen in `qaJeKamera`.
    ...grundlageLaufFelder(r, lauf.grundlageId),
    ...(hatBild
      ? {}
      : {
          fehler: r.lieferstatus_grund ?? r.qa.verdict.reason ?? 'Ergebnis ohne Bild — die Bridge hat kein Bild geliefert.',
        }),
  };
}

/**
 * Merken (Regel 1): legt die Kennung eines eben fertigen Laufs mit Bild an seinem Render-Knoten ab.
 * Nur für einen Render-Knoten des Graphen (ein Varianten-Lauf hat eine eigene Lauf-Kennung, kein
 * Knoten); unverändert, wenn dieselbe Kennung schon dort steht. Gibt zurück, ob abgelegt wurde.
 */
export function merkeLetztenLauf(
  nodeId: string,
  lauf: Pick<NodeLauf, 'graphId' | 'memoKey' | 'stufe' | 'grundlageStand'>,
  jobId: string,
): boolean {
  if (!lauf.graphId || !KENNUNG.test(jobId)) return false;
  try {
    const { doc, runCommand } = useProject.getState();
    const knoten = doc.get<VisGraph>(lauf.graphId)?.nodes.find((n) => n.id === nodeId);
    if (!knoten || knoten.typ !== 'render') return false;
    const text = letzterLaufText({
      jobId,
      memoKey: lauf.memoKey,
      ...(lauf.stufe ? { stufe: lauf.stufe } : {}),
      ...(lauf.grundlageStand ? { grundlageStand: lauf.grundlageStand } : {}),
    });
    if (knoten.params?.[LETZTER_LAUF_PARAM] === text) return false;
    ohneVerlauf(() =>
      runCommand('vis.nodeParametrieren', { graphId: lauf.graphId, nodeId, params: { [LETZTER_LAUF_PARAM]: text } }),
    );
    return true;
  } catch {
    // Der Knoten kann inzwischen geloescht sein — dann gibt es nichts zu merken. Das Bild steht
    // trotzdem am Knoten; es fehlt nur nach dem naechsten Oeffnen.
    return false;
  }
}

/** Die Render-Knoten eines Graphen, deren letzter Lauf nach dem Öffnen wiederzuholen ist. */
export function wiederzuholen(
  graph: Pick<VisGraph, 'nodes'>,
  laeufe: Readonly<Record<string, unknown>>,
): { nodeId: string; letzter: LetzterLauf }[] {
  const aus: { nodeId: string; letzter: LetzterLauf }[] = [];
  const verlauf = useVisRuntime.getState().verlauf;
  for (const n of graph.nodes) {
    if (n.typ !== 'render') continue;
    // Regel 4 (S8): ein Lauf ohne Bild am Knoten verdraengt den gemerkten nicht — nur einer MIT Bild.
    const jetzt = laeufe[n.id] as NodeLauf | undefined;
    if (jetzt && laufMitBild(jetzt)) continue;
    const letzter = letzterLaufAmKnoten(n.params);
    if (!letzter) continue;
    if (jetzt?.jobId === letzter.jobId || (verlauf[n.id] ?? []).some((l) => l.jobId === letzter.jobId)) continue;
    aus.push({ nodeId: n.id, letzter });
  }
  return aus;
}

/** Ein Auftrag, wie ihn `holeJob` liefert — nur, was das Wiederholen liest. */
export interface GeholterAuftrag {
  status: string;
  created_at: string;
  updated_at?: string | undefined;
  result?: Ergebnis | undefined;
}

/**
 * Wiederholen (Regel 2/3): für jeden Render-Knoten ohne Lauf, aber mit gemerkter Kennung, den
 * Auftrag einmal abfragen und — fertig mit Bild — den Lauf wieder an den Knoten legen. Gibt die
 * Zahl der wiederhergestellten Läufe zurück. Wirft nie.
 */
export async function holeLetzteLaeufe(
  graph: Pick<VisGraph, 'id' | 'nodes'>,
  holen: (jobId: string) => Promise<GeholterAuftrag>,
): Promise<number> {
  let zahl = 0;
  for (const { nodeId, letzter } of wiederzuholen(graph, useVisRuntime.getState().laeufe)) {
    let j: GeholterAuftrag;
    try {
      j = await holen(letzter.jobId);
    } catch {
      continue; // Gegenseite kennt ihn nicht (mehr) oder ist nicht erreichbar — der Knoten bleibt leer.
    }
    if (j.status !== 'done' || !j.result || j.result.images.length === 0) continue;
    const zeit = Date.parse(j.updated_at ?? j.created_at);
    const felder = ergebnisFelder(
      j.result,
      letzter.stufe ? { stufe: letzter.stufe } : {},
      Number.isFinite(zeit) ? zeit : Date.now(),
    );
    const lauf: NodeLauf = {
      ...felder,
      status: 'fertig',
      jobId: letzter.jobId,
      graphId: graph.id,
      memoKey: letzter.memoKey,
      ...(letzter.stufe ? { stufe: letzter.stufe } : {}),
      ...(letzter.grundlageStand ? { grundlageStand: letzter.grundlageStand } : {}),
    };
    const jetzt = useVisRuntime.getState().laeufe[nodeId];
    if (!jetzt) {
      useVisRuntime.getState().setzeLauf(nodeId, lauf);
    } else if (laufMitBild(jetzt) || jetzt.jobId === letzter.jobId) {
      // Inzwischen ein Lauf mit Bild am Knoten (neu bestellt, oder ein zweiter Aufruf war schneller): nie überschreiben.
      continue;
    } else {
      // Regel 4 (S8): der Knoten hat einen Lauf ohne Bild — der gemerkte kommt in den Verlauf, nicht an den Knoten.
      useVisRuntime.getState().legeInVerlauf(nodeId, lauf);
    }
    zahl++;
  }
  return zahl;
}
