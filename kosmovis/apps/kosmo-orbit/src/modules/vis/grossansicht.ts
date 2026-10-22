/**
 * GROSSANSICHT UND VERGLEICH (Visbox-Video-Befunde L4-14 und L4-15, 21.10.2026; Entwurfsflaeche Blatt
 * «Grossansicht und Vergleich», gebaut nach den Empfehlungen A–C).
 *
 * WARUM: Im Demolauf erschien das fertige Bild nur als ≈ 160-px-Vorschau am Knoten oder in der grossen Ansicht mit
 * ≈ 330 × 200 px — die rechte Haelfte war Prueftext. Und wer auf EINER Grundlage mehrere Varianten rechnete (Nr. 85),
 * konnte sie nicht nebeneinander sehen: der Verlauf mischte die Grundlagen, und «Kuratieren» kannte nur den letzten
 * Lauf je Knoten («0 Varianten»).
 *
 * WAS DAFUER GESCHIEHT — reine Anzeige, kein neues Vertragsfeld, nichts am Heim-PC:
 *  A. Die grosse Ansicht ist so breit wie das Fenster erlaubt (`GROSS_BREITE`), das Bild nimmt die ganze Breite.
 *     Die Pruefung ist EINGEKLAPPT; das Urteil steht als Pille im Kopf, «Pruefung ▸» legt die Werte ueber den
 *     rechten Bildrand. Gilt fuer den Lauf, das Bildpaar (117a) und die Varianten gross.
 *  B. «Bei fertig gross oeffnen» ist ein Schalter in der grossen Ansicht, Knoten-Parameter `grossBeiFertig`,
 *     AB WERK AUS: ein Fenster, das sich von selbst ueber die Knoten legt, faengt den naechsten Klick ab. Mit
 *     Schalter oeffnet es genau einmal, wenn der Lauf DIESES Render-Knotens in der laufenden Sitzung fertig wird
 *     und kein anderes Fenster offen ist.
 *  C. Nebeneinander: die Laeufe DERSELBEN Grundlage (hoechstens die vier des Verlaufs) gleich gross in einer Reihe.
 *     Der Verlauf am Knoten ordnet seine Daumen nach Grundlage (neueste Grundlage links), ein Strich trennt sie.
 *     «Kuratieren» bekommt jeden Lauf mit Bild als Karte, nicht nur den letzten je Knoten.
 */
import { create } from 'zustand';
import type { NodeLauf } from './vis-runtime';
import type { VerlaufEintrag } from './render-verlauf';
import { kameraImSatz } from './modus';

/** Breite der grossen Ansichten (px); das Fenster deckelt sie (`min(…, 100vw − 48px)`). */
export const GROSS_BREITE = 1600;

/** Der Knoten-Parameter des Schalters (B), flach wie `bildAnsicht`. */
export const GROSS_BEI_FERTIG_PARAM = 'grossBeiFertig';

/** Ab Werk aus (B). */
export function grossBeiFertigAmKnoten(params: Record<string, unknown> | undefined): boolean {
  return params?.[GROSS_BEI_FERTIG_PARAM] === true;
}

export const GROSS_BEI_FERTIG_NAME = 'bei «fertig» gross öffnen';
export const GROSS_BEI_FERTIG_HILFE =
  'Öffnet diese Ansicht von selbst, sobald der nächste Lauf dieses Render-Knotens fertig ist — einmal, und nur, wenn kein anderes Fenster offen ist.';

export const PRUEFUNG_AUF = 'Prüfung ▸';
export const PRUEFUNG_ZU = 'Prüfung ◂';
export const PRUEFUNG_HILFE = 'Urteil, Grund und Werte der Prüfung — liegen über dem rechten Bildrand und nehmen dem Bild nichts weg.';

/**
 * PRAESENTATION (Owner-Entscheid 21.10.2026: «der Praesentationsmodus kommt automatisch, solange Claude oder Kosmo
 * bedient»). Die Naht fuer diesen Modus: wer ihn fuehrt (UI-Worker, Insel des Assistenten), setzt `praesentation`.
 * Solange er an ist, gilt der Schalter (B) als eingeschaltet — die Grossansicht bzw. das Bildpaar oeffnet bei «fertig»
 * von selbst, ohne dass jemand klickt; die Pruefung bleibt eingeklappt, das Urteil steht im Kopf. Der Knoten-Parameter
 * bleibt, wie er ist: der Modus aendert nichts am Dokument.
 */
interface GrossSteuerung {
  praesentation: boolean;
  setzePraesentation: (an: boolean) => void;
}
export const useGrossSteuerung = create<GrossSteuerung>((set) => ({
  praesentation: false,
  setzePraesentation: (an) => set({ praesentation: an }),
}));

/** B, wirksam: der Schalter am Knoten ODER der Praesentationsmodus. */
export function grossBeiFertigWirksam(params: Record<string, unknown> | undefined, praesentation: boolean): boolean {
  return praesentation || grossBeiFertigAmKnoten(params);
}

const LAEUFT: ReadonlySet<string> = new Set(['gesendet', 'wartetFreigabe', 'wartetGpu', 'rendert']);

/**
 * B: oeffnet die grosse Ansicht von selbst? Nur beim Uebergang «laeuft → fertig», den DIESER Knoten gesehen hat,
 * mit Bild, mit Schalter.
 */
export function sollGrossOeffnen(
  vorher: string | undefined,
  jetzt: string | undefined,
  hatBild: boolean,
  schalter: boolean,
): boolean {
  return schalter && hatBild && jetzt === 'fertig' && vorher !== undefined && LAEUFT.has(vorher);
}

/** Schluessel einer Grundlage im Verlauf; ein Lauf ohne Grundlage steht fuer sich (eigener Blender-Lauf). */
export function grundlageSchluessel(e: Pick<VerlaufEintrag, 'grundlageId' | 'jobId'>): string {
  return e.grundlageId ? `g:${e.grundlageId}` : `j:${e.jobId}`;
}

export interface VerlaufGruppe {
  schluessel: string;
  grundlageId: string | undefined;
  /** Die Laeufe dieser Grundlage, neuestes zuerst; `index` ist die Stelle in der Reihe. */
  eintraege: { eintrag: VerlaufEintrag; index: number }[];
}

/**
 * C: die Reihe nach Grundlage. Die Gruppen in der Reihenfolge ihres neuesten Laufs (neueste links), darin die
 * Laeufe neuestes zuerst. Nichts faellt weg, nichts wird doppelt gezeigt.
 */
export function verlaufGruppen(reihe: readonly VerlaufEintrag[]): VerlaufGruppe[] {
  const gruppen: VerlaufGruppe[] = [];
  const nach = new Map<string, VerlaufGruppe>();
  reihe.forEach((eintrag, index) => {
    const s = grundlageSchluessel(eintrag);
    let g = nach.get(s);
    if (!g) {
      g = { schluessel: s, grundlageId: eintrag.grundlageId, eintraege: [] };
      nach.set(s, g);
      gruppen.push(g);
    }
    g.eintraege.push({ eintrag, index });
  });
  return gruppen;
}

/** Die Reihe in der Reihenfolge der Gruppen — so blaettert die grosse Ansicht wie die Daumen stehen. */
export function gruppierteReihe(reihe: readonly VerlaufEintrag[]): VerlaufEintrag[] {
  return verlaufGruppen(reihe).flatMap((g) => g.eintraege.map((x) => x.eintrag));
}

/** C: die Laeufe auf derselben Grundlage wie `e` (mit `e`), neuestes zuerst. */
export function laeufeDerGrundlage(reihe: readonly VerlaufEintrag[], e: VerlaufEintrag): VerlaufEintrag[] {
  const s = grundlageSchluessel(e);
  return reihe.filter((x) => grundlageSchluessel(x) === s);
}

/** Kopfzeile des zugeklappten bzw. offenen Verlaufs: «4 Läufe · 2 Grundlagen» (die zweite Angabe nur ab zwei). */
export function grundlagenZusatz(reihe: readonly VerlaufEintrag[]): string {
  const n = verlaufGruppen(reihe).filter((g) => g.grundlageId !== undefined).length;
  return n >= 2 ? ` · ${n} Grundlagen` : '';
}

/**
 * C (Kuratieren kennt die Laeufe): der Schluessel einer Karte fuer einen FRUEHEREN Lauf eines Render-Knotens. Der
 * aktuelle Lauf bleibt beim Schluessel des Knotens (`node.id`) — so behalten Stern und Ablage, die schon gesetzt sind,
 * ihre Karte.
 */
export function laufKartenSchluessel(nodeId: string, jobId: string): string {
  return `${nodeId}#${jobId}`;
}

/**
 * Die frueheren Laeufe mit Bild, die als eigene Karte kommen (der aktuelle ist schon die Karte des Knotens) — aus
 * allem, was die Laufzeit behaelt (`verlauf`, nicht nur die vier Daumen), jeder Auftrag einmal, neuestes zuerst.
 */
export function fruehereLaeufeMitBild<T extends Pick<NodeLauf, 'jobId' | 'status' | 'bild'>>(
  lauf: Pick<NodeLauf, 'jobId'> | undefined,
  frueher: readonly T[] | undefined,
): T[] {
  const gesehen = new Set<string>(lauf?.jobId ? [lauf.jobId] : []);
  const aus: T[] = [];
  for (const e of frueher ?? []) {
    if (e.status !== 'fertig' || !e.jobId || !e.bild || gesehen.has(e.jobId)) continue;
    gesehen.add(e.jobId);
    aus.push(e);
  }
  return aus;
}

/**
 * L4-1 (mit der HomeStation abgestimmt, 21.10.2026): «deckungsgleich» heisst gleiche Grundlage UND gleiche Form (Kanten-
 * IoU des KI-Bilds gegen das Grundbild ueber einer Schwelle; Visbox-Kern `varianten.deckung`). Solange das Ergebnis die
 * Zahl noch nicht traegt, sagt die Vergleichsansicht nur, was belegt ist.
 */
export const DECKUNG_UNGEMESSEN_SATZ = 'gleiche Grundlage · Form ungeprüft';
export const DECKUNG_GLEICH_SATZ = 'deckungsgleich';
export const DECKUNG_ABWEICHEND_SATZ = 'gleiche Grundlage, Form weicht ab';
/**
 * Schwelle der Kanten-IoU — DIESELBE ZAHL WIE IM VISBOX-KERN (`varianten.DECKUNG_KANTEN_IOU_SCHWELLE`, Visbox-Entscheid
 * 138, 22.10.2026), gesetzt aus auf-20261022-337 und -339: Form nein (Variante ohne Bildeingang malt ein anderes Haus)
 * 0,142 / 0,213 / 0,216; Form ja (mit Bildeingang) 0,294 / 0,296 / 0,367 / 0,481 — 0,25 liegt in der Luecke. Die
 * fruehere Setzung 0,10 (auf-20261021-317, vier Laeufe) nannte in 339 ein anderes Haus «deckungsgleich».
 *
 * Nur die Rueckfallebene: traegt das Ergebnis sein eigenes Urteil (Satz `SATZ_FORM_WEICHT_AB` in
 * `qa.verdict.hinweise`), gilt das (`deckungUrteilDesLaufs`). Die Zahl steht nur hier; Hilfetext und Proben lesen sie.
 */
export const DECKUNG_SCHWELLE = 0.25;
export const DECKUNG_SCHWELLE_HERKUNFT =
  'Schwelle 0,25 wie im Visbox-Kern (Entscheid 138), gesetzt aus auf-20261022-337 und -339';
/** Der Anfang des Satzes im Ergebnis — wortgleich mit dem Visbox-Kern (`kosmo_szene.SATZ_FORM_WEICHT_AB`). */
export const SATZ_FORM_WEICHT_AB = 'FORM WEICHT VOM GRUNDBILD AB';

export type DeckungUrteil = 'deckungsgleich' | 'weicht-ab' | 'ungemessen';

/** Gehoert das gezeigte Bild zu dieser Kamera? (`<kamera>.png`, `<kamera>.…`, `<kamera>__…`) */
function bildDerKamera(bild: string, kamera: string): boolean {
  return bild === `${kamera}.png` || bild.startsWith(`${kamera}.`) || bild.startsWith(`${kamera}__`);
}

/**
 * Die Kanten-IoU des gezeigten Bildes (`qa_je_kamera[].deckung`): der Eintrag der Kamera, deren Name das Bild traegt,
 * sonst der einzige gemessene. `undefined`, wenn nichts gemessen ist.
 */
export function deckungDesLaufs(l: Pick<NodeLauf, 'qaJeKamera' | 'bild'>): number | undefined {
  const mit = (l.qaJeKamera ?? []).filter((k) => typeof k.deckung === 'number');
  if (mit.length === 0) return undefined;
  const bild = l.bild ?? '';
  const passend = mit.find((k) => bildDerKamera(bild, k.kamera));
  return (passend ?? (mit.length === 1 ? mit[0] : undefined))?.deckung;
}

/** Urteil aus der Zahl allein, mit `DECKUNG_SCHWELLE` — fuer Laeufe, deren Ergebnis kein eigenes Urteil traegt. */
export function deckungUrteil(iou: number | undefined): DeckungUrteil {
  if (iou === undefined) return 'ungemessen';
  return iou >= DECKUNG_SCHWELLE ? 'deckungsgleich' : 'weicht-ab';
}

/**
 * Sagt das ERGEBNIS selbst, dass die Form des gezeigten Bildes abweicht? Der Kern schreibt je Kamera den Satz
 * «FORM WEICHT VOM GRUNDBILD AB, Kamera '<name>': …» in `qa.verdict.hinweise`. Er gilt fuer das gezeigte Bild, wenn er
 * dessen Kamera nennt, keine Kamera nennt, oder der Lauf nur eine Kamera hat.
 */
export function formWeichtAbLautErgebnis(l: Pick<NodeLauf, 'qa' | 'qaJeKamera' | 'bild'>): boolean {
  const saetze = (l.qa?.verdict.hinweise ?? []).filter((h) => typeof h === 'string' && h.startsWith(SATZ_FORM_WEICHT_AB));
  if (saetze.length === 0) return false;
  const bild = l.bild ?? '';
  const eineKamera = (l.qaJeKamera?.length ?? 0) <= 1;
  return saetze.some((satz) => {
    const kamera = kameraImSatz(satz);
    return kamera === undefined || eineKamera || bildDerKamera(bild, kamera);
  });
}

/**
 * Das Urteil, das die Oberflaeche zeigt: zuerst das des Ergebnisses (Satz `SATZ_FORM_WEICHT_AB`), sonst aus der Zahl
 * mit derselben Schwelle wie der Kern. So kann die Anzeige nie «deckungsgleich» sagen, wo das Ergebnis «weicht ab» sagt.
 */
export function deckungUrteilDesLaufs(l: Pick<NodeLauf, 'qa' | 'qaJeKamera' | 'bild'>): DeckungUrteil {
  if (formWeichtAbLautErgebnis(l)) return 'weicht-ab';
  return deckungUrteil(deckungDesLaufs(l));
}

/** Die Marke ueber der Reihe: weicht eine Variante ab, sagt sie das; sind alle gemessen und gleich, «deckungsgleich». */
export function deckungDerReihe(laeufe: readonly Pick<NodeLauf, 'qa' | 'qaJeKamera' | 'bild' | 'stufe'>[]): {
  urteil: DeckungUrteil;
  satz: string;
} {
  const urteile = laeufe.filter((l) => l.stufe !== 'grundlage').map((l) => deckungUrteilDesLaufs(l));
  if (urteile.includes('weicht-ab')) return { urteil: 'weicht-ab', satz: `⚠ ${DECKUNG_ABWEICHEND_SATZ}` };
  if (urteile.length > 0 && urteile.every((u) => u === 'deckungsgleich')) {
    return { urteil: 'deckungsgleich', satz: `${DECKUNG_GLEICH_SATZ} · gleiche Grundlage` };
  }
  return { urteil: 'ungemessen', satz: DECKUNG_UNGEMESSEN_SATZ };
}
export const DECKUNG_HILFE =
  'Dieselbe Grundlage (Tiefe, Standpunkt, Startwert) heisst noch nicht dieselbe Form. Deckungsgleich, wenn die Kanten ' +
  `des KI-Bilds die des Grundbilds zu mindestens ${Math.round(DECKUNG_SCHWELLE * 100)} % treffen und das Ergebnis keine ` +
  'Abweichung meldet (Schwelle wie im Rechenkern, gesetzt aus sieben Läufen: ein Bild ohne Bildeingang, das ein anderes ' +
  'Haus malt, trifft 14–22 %, ein Bild mit Bildeingang 29–48 %); ohne Messung «Form ungeprüft».';

