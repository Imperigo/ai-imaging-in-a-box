/**
 * Visbox-eigen — Rendern ohne Klick in der Selbständigkeit «Voll» (Owner-Entscheid 146, 24.10.2026,
 * Klickfrage über die Zentrale, Variante A «Alles ohne Klick, Grenzen bleiben»; Wortlaut des Owners:
 * «bitte behebe das kartenproblem und ständige "ich muss bestätigen" mit karten wenn vollautomatik
 * läuft»).
 *
 * Bis 0.3.55 war jedes `vis_render`/`vis_varianten` auch in «Voll» eine Karte, und nach «Anwenden»
 * wartete der Lauf noch auf «Freigeben» am Knoten — vier Klicks für ein Bild aus der Skizze. Jetzt
 * entscheidet dieser Wirt je Aufruf, ob er ohne Karte laufen darf (`setzeVollRenderLeser` im
 * Werkzeugsatz), und die Bestellsätze sagen dann «rechnet ohne Freigabe, Vollautomatik»
 * (`setzeOhneFreigabeLeser` im Kern — derselbe Leser wie in KosmoOrbit, dort an der Vollautomatik).
 *
 * DIE GRENZEN BLEIBEN (und werden am Heim-PC durchgesetzt, nicht nur hier):
 *  - höchstens 5 Läufe je Stunde ohne Klick, über alle Geräte, gezählt am Heim-PC — auch
 *    «Grundlage rendern» (nur Blender) zählt mit und wartet bei erreichter Grenze (Ergebnis 351 B4)
 *    (`aiimaging.knotenweg.voll_stand`). Die Mac-App fragt ihn vor jedem Aufruf in «Voll»
 *    (`GET /bruecke/voll`) und reicht die Antwort als `lage` herein. Ist die Grenze erreicht, wird
 *    es eine Karte mit «wieder frei ab …».
 *  - nie ein Bildmodell mit Forschungs- oder offener Lizenz ohne Klick (heute Qwen-Image 2.1,
 *    `nur_forschung`/`lizenz_offen` im Register): Karte. AUSNAHME Entscheid 153 (Owner, 25.10.2026:
 *    «Ja, Qwen-Image darf für Skizzen in Vollautomatik ohne Klick laufen.»): ein Bild AUS EINER
 *    SKIZZE (Kante an den Eingang «skizze» des Render-Knotens) mit einem Modell aus
 *    `VOLL_SKIZZEN_BILDMODELLE` — gezählt wie jeder Lauf, markiert wie bisher (E128). Nie Vorgabe:
 *    gewählt werden muss es ausdrücklich.
 *  - Löschen bleibt eine Karte (der Werkzeugsatz lässt kein Paket mit Löschen ohne Karte durch).
 * Ob der Lauf danach wirklich ohne «Freigeben» startet, entscheidet der Heim-PC beim Anlegen des
 * Auftrags (Kopf `X-Visbox-Ohne-Klick`, den nur die Mac-App setzt) — mit denselben zwei Grenzen. Die
 * Seite selbst gibt nie etwas frei.
 */
import { setzeOhneFreigabeLeser, type KosmoDoc, type VisGraph } from '@kosmo/kernel';
import {
  befehlFuer,
  setzeVollRenderLeser,
  VIS_PAKET,
  type KiAntwort,
  type KiAufruf,
  type KiModus,
  type VollRenderUrteil,
} from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { setzeKlickVollLeser, type KlickBestellung, type KlickVollUrteil } from '../../kosmo-orbit/src/modules/vis/vis-jobs';
import { modusAus } from '../../kosmo-orbit/src/state/kosmo-coop';

/** Was die App vom Heim-PC weiss (`GET /bruecke/voll`), frisch vor jedem Aufruf in «Voll». */
export interface VollLage {
  /** Ob noch ein Lauf ohne Klick in die Stunde passt. */
  frei: boolean;
  /** Der Satz des Heim-PC, z. B. «Grenze erreicht: 5 Läufe ohne Klick in der letzten Stunde …». */
  satz?: string;
  laeufe?: number;
  grenze?: number;
  /** Ab wann wieder ein Lauf ohne Klick geht (ISO-Zeit), `null`: jetzt schon. */
  wiederFreiAb?: string | null;
}

/** Die Grenze je Stunde — dieselbe Zahl wie am Heim-PC (`knotenweg.VOLL_GRENZE`, Probe in pytest). */
export const VOLL_GRENZE_JE_STUNDE = 5;

/**
 * Die Bildmodelle, die in «Voll» ohne Klick rechnen dürfen: die im Vertrag bestellbaren, deren Lizenz
 * im Register zulässig ist (`pruefe_lizenz`). Nicht darin: `qwen-image-2.1` (offene Lizenz),
 * `flux-krea` (Forschung, nicht kommerziell), `sdxl` (im Register ausgeschlossen). Der Heim-PC prüft
 * dasselbe noch einmal (`knotenweg.voll_lizenz_mangel`); die Probe `test_voll_ohne_klick.py` hält
 * beide Listen gleich.
 */
export const VOLL_BILDMODELLE: readonly string[] = ['z-image-turbo', 'qwen', 'flux2-klein'];
/**
 * Entscheid 153 (25.10.2026): zusätzlich, NUR für ein Bild aus einer Skizze — dieselbe Liste wie am
 * Heim-PC (`knotenweg.VOLL_SKIZZE_LIZENZ_OFFEN`, Probe `test_voll_skizze_e153.py`).
 */
export const VOLL_SKIZZEN_BILDMODELLE: readonly string[] = ['qwen-image-2.1'];
/** Ohne Wahl rechnet der Auftrag mit diesem Bildmodell (`postRenderJob`, Vertrag). */
export const VOLL_VORGABE_BILDMODELL = 'z-image-turbo';

export const SATZ_KEINE_LAGE =
  'der Heim-PC hat den Stand der Vollautomatik nicht gemeldet (nicht erreicht oder nicht eingerichtet)';

function alsObjekt(x: unknown): Record<string, unknown> {
  return x && typeof x === 'object' && !Array.isArray(x) ? (x as Record<string, unknown>) : {};
}

/** Hängt am Render-Knoten (oder am Render-Knoten unter einem Varianten-Knoten) eine Skizze? */
function mitSkizzeAmKnoten(doc: KosmoDoc, graphId: unknown, nodeId: unknown): boolean {
  const graphen = typeof graphId === 'string' ? [doc.get<VisGraph>(graphId)].filter(Boolean) : doc.byKind<VisGraph>('visgraph');
  for (const g of graphen as VisGraph[]) {
    const n = g.nodes.find((x) => x.id === nodeId);
    if (!n) continue;
    const renderId = n.typ === 'varianten' ? g.edges.find((e) => e.to === n.id && e.toPort === 'render')?.from : n.id;
    return !!renderId && g.edges.some((e) => e.to === renderId && e.toPort === 'skizze');
  }
  return false;
}

function bildmodellAmKnoten(doc: KosmoDoc, graphId: unknown, nodeId: unknown): string | null {
  const graphen = typeof graphId === 'string' ? [doc.get<VisGraph>(graphId)].filter(Boolean) : doc.byKind<VisGraph>('visgraph');
  for (const g of graphen as VisGraph[]) {
    const n = g.nodes.find((x) => x.id === nodeId);
    if (!n) continue;
    if (n.typ === 'varianten') {
      // Der Varianten-Knoten rechnet mit dem Bildmodell des Render-Knotens, an dem er hängt.
      const kante = g.edges.find((e) => e.to === n.id && e.toPort === 'render');
      const r = kante ? g.nodes.find((x) => x.id === kante.from) : undefined;
      const bm = r?.params?.['backbone'];
      return typeof bm === 'string' ? bm : null;
    }
    const bm = n.params?.['backbone'];
    return typeof bm === 'string' ? bm : null;
  }
  return null;
}

/** Die Bildmodelle, mit denen ein Aufruf rechnen würde — je Schritt, der ein Bild bestellt. */
export function bildmodelleDesAufrufs(aufruf: Pick<KiAufruf, 'werkzeug' | 'argumente'>, doc: KosmoDoc): string[] {
  return bildschritteDesAufrufs(aufruf, doc).map((s) => s.modell);
}

/** Je Schritt, der ein Bild bestellt: das Bildmodell und ob eine Skizze das Bild führt (Entscheid 153). */
export function bildschritteDesAufrufs(aufruf: Pick<KiAufruf, 'werkzeug' | 'argumente'>, doc: KosmoDoc): { modell: string; mitSkizze: boolean }[] {
  const schritte: { befehl: string; argumente: Record<string, unknown> }[] =
    aufruf.werkzeug === VIS_PAKET
      ? (Array.isArray(alsObjekt(aufruf.argumente)['schritte']) ? (alsObjekt(aufruf.argumente)['schritte'] as unknown[]) : []).map((x) => ({
          befehl: befehlFuer(String(alsObjekt(x)['befehl'] ?? '')),
          argumente: alsObjekt(alsObjekt(x)['argumente']),
        }))
      : [{ befehl: befehlFuer(aufruf.werkzeug), argumente: alsObjekt(aufruf.argumente) }];
  const modelle: { modell: string; mitSkizze: boolean }[] = [];
  for (const s of schritte) {
    const mitSkizze = mitSkizzeAmKnoten(doc, s.argumente['graphId'], s.argumente['nodeId']);
    if (s.befehl === 'vis.render') {
      const gewaehlt = s.argumente['backbone'];
      modelle.push({
        modell: typeof gewaehlt === 'string' ? gewaehlt : (bildmodellAmKnoten(doc, s.argumente['graphId'], s.argumente['nodeId']) ?? VOLL_VORGABE_BILDMODELL),
        mitSkizze,
      });
    } else if (s.befehl === 'vis.varianten') {
      modelle.push({ modell: bildmodellAmKnoten(doc, s.argumente['graphId'], s.argumente['nodeId']) ?? VOLL_VORGABE_BILDMODELL, mitSkizze });
    }
    // vis.grundlage rechnet nur Blender (Cycles) — kein Bildmodell, also keine Lizenzfrage; zur
    // Grenze von 5 je Stunde zählt der Lauf trotzdem (Heim-PC, Ergebnis 351 B4).
  }
  return modelle;
}

/**
 * Darf dieser Aufruf in «Voll» ohne Karte laufen? Nur in «Voll», nur wenn der Heim-PC «frei» meldet,
 * und nur mit einem Bildmodell aus `VOLL_BILDMODELLE` — oder, aus einer Skizze, aus
 * `VOLL_SKIZZEN_BILDMODELLE` (Entscheid 153). Sonst Karte mit dem Grund.
 */
export function vollUrteil(aufruf: KiAufruf, modus: KiModus, lage: VollLage | null | undefined, doc: KosmoDoc = useProject.getState().doc): VollRenderUrteil {
  if (modus !== 'voll') return { frei: false, grund: 'nicht in der Vollautomatik' };
  for (const { modell: bm, mitSkizze } of bildschritteDesAufrufs(aufruf, doc)) {
    // Entscheid 153: Qwen-Image aus einer Skizze ohne Klick — nur ausdrücklich gewählt, gezählt am Heim-PC.
    if (mitSkizze && VOLL_SKIZZEN_BILDMODELLE.includes(bm)) continue;
    if (!VOLL_BILDMODELLE.includes(bm)) {
      return { frei: false, grund: `das Bildmodell «${bm}» hat eine offene oder Forschungs-Lizenz und rechnet nur nach einem Klick` };
    }
  }
  if (!lage || typeof lage.frei !== 'boolean') return { frei: false, grund: SATZ_KEINE_LAGE };
  if (!lage.frei) return { frei: false, grund: lage.satz && lage.satz.trim() ? lage.satz.trim() : `Grenze erreicht: ${VOLL_GRENZE_JE_STUNDE} Läufe ohne Klick in der letzten Stunde` };
  return { frei: true };
}

/** Das Urteil des laufenden Aufrufs — nur während `rufeMitVoll`, sonst `null`. */
let jetzt: VollRenderUrteil | null = null;

/**
 * Ein Aufruf an den Werkzeugsatz mit dem Urteil der Vollautomatik: Es gilt für die Dauer des
 * Aufrufs (Probelauf und Ausführen laufen darin, synchron) — der Satz «rechnet ohne Freigabe» und
 * «ohne Karte» kommen so aus derselben Antwort.
 */
export function rufeMitVoll(aufruf: KiAufruf, modus: KiModus, lage: VollLage | null | undefined, rufe: (a: KiAufruf, m: KiModus) => KiAntwort): KiAntwort {
  jetzt = modus === 'voll' ? vollUrteil(aufruf, modus, lage) : null;
  try {
    return rufe(aufruf, modus);
  } finally {
    jetzt = null;
  }
}

/**
 * **Entscheid 155 (Owner über die Zentrale, 27.10.2026): in «Voll» ist der Klick des Architekten die Freigabe.**
 * «Variante erzeugen», «Grundlage rendern», «Ausführen» und die Bestellung am Varianten-Knoten laufen ohne
 * zusätzliches «Freigeben». Ändert E146 für den Mausklick des Architekten (die KosmoMaus von Claude bleibt Karte).
 *
 * Die Grenze von 5 je Stunde setzt der Heim-PC durch: Die Mac-App sagt jeden Auftrag in «Voll» an (Kopf
 * `X-Visbox-Ohne-Klick`), der Heim-PC zählt die Klick-Läufe mit und lässt einen Auftrag an der Grenze mit «nicht ohne
 * Klick: Grenze erreicht … wieder frei ab …» warten — der Satz steht dann am Knoten. Hier wird nur die Lizenz geprüft
 * (wie beim Heim-PC): ein Bildmodell mit offener oder Forschungs-Lizenz rechnet nur nach «Freigeben», ausser einem
 * Bild aus einer Skizze mit ausdrücklich gewähltem Qwen-Image (Entscheid 153).
 */
export function klickUrteil(b: KlickBestellung, modus = modusAus()): KlickVollUrteil | null {
  if (modus !== 'voll') return null;
  if (b.backbone !== null && !VOLL_BILDMODELLE.includes(b.backbone) && !(b.mitSkizze && VOLL_SKIZZEN_BILDMODELLE.includes(b.backbone))) {
    return { frei: false, grund: `das Bildmodell «${b.backbone}» hat eine offene oder Forschungs-Lizenz und rechnet nur nach «Freigeben»` };
  }
  return { frei: true };
}

/** Meldet die drei Leser an (Werkzeugsatz, Kern und — E155 — der Klick). Liefert das Abmelden. */
export function haengeVollAn(): () => void {
  setzeVollRenderLeser(() => jetzt ?? { frei: false, grund: SATZ_KEINE_LAGE });
  // Der Bestellsatz der Werkzeuge gilt nur waehrend eines Aufrufs (Claude/Assistent); der Klick (E155) sagt es am Knoten.
  setzeOhneFreigabeLeser(() => jetzt?.frei === true);
  setzeKlickVollLeser((b) => klickUrteil(b));
  return () => {
    setzeVollRenderLeser(null);
    setzeOhneFreigabeLeser(null);
    setzeKlickVollLeser(null);
  };
}
