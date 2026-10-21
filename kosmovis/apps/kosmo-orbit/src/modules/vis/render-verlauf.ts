import type { JobQa } from './vis-jobs';
import { laufMitBild, type NodeLauf } from './vis-runtime';
import { bewertungsLage, qaUrteil, RHO_MASKE_SCHWELLE, type QaUrteil } from './varianten-diff';

/**
 * Entscheid 68 / E174 (Owner, 07.10.2026) — DER VERLAUF AM RENDER-KNOTEN.
 * Vorlage: Entwurfsblatt «15 · Verlauf am Render-Knoten».
 *
 * Bis hierhin hielt der Render-Knoten nur den letzten Lauf: ein neues
 * «Ausführen» ersetzte das Bild, und das vorige war für die Oberfläche weg.
 * Jetzt steht unter dem Hauptbild eine Reihe der letzten vier Läufe dieses
 * Knotens, das neueste links, jedes Daumenbild mit einem Punkt für sein
 * Urteil. Ein Klick zeigt den Lauf gross; das Hauptbild bleibt der letzte
 * Lauf, aufs Blatt geht nichts, ausgewählt wird nichts.
 *
 * Diese Datei ist die reine Rechnung dazu (kein React): welche Läufe in der
 * Reihe stehen, welches Urteil ein Lauf trägt und wie Zeit und Treue
 * geschrieben werden. Die Anzeige liegt in `RenderVerlauf.tsx`, die
 * Abloesung (ein neuer Lauf schiebt den alten in den Verlauf) in
 * `vis-runtime.ts#setzeLauf`.
 */

/** Höchstens so viele Daumenbilder stehen in der Reihe. */
export const VERLAUF_ZAHL = 4;

/** Ein Lauf in der Reihe — immer einer mit Bild (s. `laufMitBild`). */
export type VerlaufEintrag = NodeLauf & { jobId: string; bild: string };

/**
 * Die Reihe unter dem Hauptbild, NEUESTES ZUERST (links): der aktuelle Lauf,
 * wenn er ein Bild hat, dann die abgeloesten aus dem Verlauf. Doppelte
 * Kennungen zaehlen einmal, Laeufe ohne Bild gar nicht, und es sind
 * hoechstens `VERLAUF_ZAHL`. Nichts wird aufgefuellt: unter vier Laeufen ist
 * die Reihe kuerzer, nicht mit Platzhaltern gestreckt.
 */
export function verlaufReihe(
  lauf: NodeLauf | undefined,
  frueher: readonly NodeLauf[] | undefined,
): VerlaufEintrag[] {
  const reihe: VerlaufEintrag[] = [];
  const gesehen = new Set<string>();
  for (const l of [lauf, ...(frueher ?? [])]) {
    if (!l || !laufMitBild(l)) continue;
    const e = l as VerlaufEintrag;
    if (gesehen.has(e.jobId)) continue;
    gesehen.add(e.jobId);
    reihe.push(e);
    if (reihe.length === VERLAUF_ZAHL) break;
  }
  return reihe;
}

/**
 * Ob die Reihe steht. Nach dem ERSTEN Lauf gibt es noch keinen Verlauf — ein
 * einzelnes Daumenbild wiederholte nur das Hauptbild (Vorlage: «Nach dem
 * ersten Lauf gibt es noch keinen Verlauf; die Reihe wächst bis vier»).
 */
export function verlaufSichtbar(reihe: readonly unknown[]): boolean {
  return reihe.length >= 2;
}

/**
 * Das Urteil eines Laufs — DASSELBE wie an der Kachel (`qaUrteil`,
 * `varianten-diff.ts`), aus dem Verdikt allein.
 *
 * HomeStation-Pruefung 266/267 (08.10.2026): bis hierhin machte der Verlauf
 * aus `bewertungsLage` `widerrufen`/`nicht-zustaendig` ein «nicht
 * beurteilbar». Der echte Abholer liefert aber nie `rho_maske`/`kante`/
 * `paarurteil`, die Lage ist bei ihm immer `widerrufen` — und so stand jeder
 * echte Lauf als «nicht beurteilbar», auch ein echtes Durchfallen, neben
 * einer Kachel mit «QA ✗». Die Lage betrifft Zahlen und Sterne, nicht das
 * Verdikt. Vier Zustaende: bestanden, durchgefallen, nicht beurteilbar (der
 * Absender sagt «NICHT BEURTEILBAR», E189), ohne QA.
 */
export type LaufUrteil = QaUrteil;

/** Die Woerter der Vorlage. `bestanden`/`durchgefallen`/`ohne QA` sind
 *  dieselben wie in der Kamera-Zeile der Kuratier-Karte (`KuratierFlaeche.tsx`). */
export const URTEIL_LABEL: Record<LaufUrteil, string> = {
  bestanden: 'bestanden',
  durchgefallen: 'durchgefallen',
  'nicht-beurteilbar': 'nicht beurteilbar',
  'ohne-qa': 'ohne QA',
};

export function laufUrteil(qa: JobQa | undefined): LaufUrteil {
  return qaUrteil(qa);
}

/**
 * Der Grund zum Urteil, wie er in der grossen Ansicht steht. Zuerst der
 * Satz, den der Absender selbst mitgibt (`qa.verdict.reason`, ungekuerzt),
 * sonst der Satz, den der Kuratier-Inspektor fuer dieselbe Lage zeigt, sonst
 * der erste QA-Hinweis. Ohne alles: das wird gesagt, nichts erfunden.
 */
export function laufGrund(qa: JobQa | undefined): string {
  const reason = qa?.verdict.reason?.trim();
  if (reason) return reason;
  if (!qa) return 'Keine QA-Bewertung vorhanden.';
  const lage = bewertungsLage(qa);
  // `widerrufen` betrifft nur Zahlen und Sterne (HomeStation 266/267): kein
  // «zurueckgezogen» neben einem Urteil, das der Absender gefaellt hat.
  if (lage === 'nicht-zustaendig') {
    return 'Hier war nichts zu messen — diese Szene ist für die Prüfung nicht zuständig, keine Wertung.';
  }
  const hinweis = (qa.verdict.hinweise ?? []).find((h) => h.trim() !== '');
  return hinweis ?? 'Ohne Begründung geliefert.';
}

function zahl(v: number): string {
  return v.toFixed(2).replace('.', ',');
}

/**
 * «Treue zur Geometrie»: `rho_maske` gegen seine geeichte Schwelle
 * (`RHO_MASKE_SCHWELLE`, P-EICHUNG) — Wert und Schwelle nebeneinander, wie
 * in der Vorlage («0,41 / 0,65»). Die Vorlage zeigte als Schwelle 0,65: das
 * ist der Vorgabewert des Feldes `qa.geometry.threshold`, und der gehoert
 * zur ALTEN, widerrufenen Formel (`render-result.ts`, Nachtrag P-EICHUNG).
 * Die geeichte Schwelle fuer `rho_maske` ist 0,80.
 *
 * Verlauf-Nachgang (HomeStation, 08.10.2026): ohne Zahl gibt es DREI Saetze,
 * nicht einen. Bei Innenansichten stand «nicht gemessen», obwohl die Messung
 * lief und nur fuer diese Ansicht nicht zustaendig war — und der Grund-Satz
 * daneben nannte eine Geometrie-Zahl. Jetzt:
 * - keine QA zurueckgekommen → «nicht gemessen»;
 * - QA da, aber fuer diese Ansicht nicht zustaendig, oder der Absender sagt
 *   «NICHT BEURTEILBAR» → «nicht anwendbar — …» mit dem Grund kurz;
 * - sonst ohne `rho_maske` → «keine Gebäude-Zahl geliefert», mit dem Zusatz
 *   «Urteil und Zahl im Grund», wenn ein Grund-Satz da ist.
 * NACHTRAG HomeStation 266/267: `widerrufen` stand hier als «nicht anwendbar
 * — Grundlage widerrufen». Der echte Abholer liefert NIE `rho_maske`, also
 * war das bei jedem echten Lauf so, innen wie aussen — eine Aussage ueber
 * die Grundlage der Sterne, nicht ueber dieses Bild. Sie ist entfallen.
 */
export function treueText(qa: JobQa | undefined): string {
  if (!qa) return 'nicht gemessen';
  const lage = bewertungsLage(qa);
  if (lage === 'nicht-zustaendig') return 'nicht anwendbar — Ansicht nicht zuständig';
  // E189: der Grund-Satz des Absenders steht direkt darueber.
  if (lage === 'nicht-beurteilbar') return 'nicht anwendbar — siehe Grund';
  const rho = qa.geometry?.rho_maske;
  if (rho !== undefined && rho !== null) return `${zahl(rho)} / ${zahl(RHO_MASKE_SCHWELLE)}`;
  // HomeStation 266/267: der echte Abholer liefert kein `rho_maske`, sein
  // Urteil steht mit seiner eigenen Zahl im Grund. Kein «widerrufen» hier.
  return qa.verdict.reason?.trim()
    ? 'keine Gebäude-Zahl geliefert — Urteil und Zahl im Grund'
    : 'keine Gebäude-Zahl geliefert';
}

/**
 * Vorschlag C18 (Visbox, Video-Befund L4-2, 21.10.2026; Blatt «Hausanteil»): WIEVIEL DES
 * BILDES DAS HAUS FUELLT — an der Grundlage UND am KI-Bild, nebeneinander.
 *
 * Anlass: «Das Haus fuellt nur 2.9 %» stand neben einem KI-Bild mit sichtbar grossem Haus.
 * Gemessen war nur die Grundlage; die KI hatte den Ausschnitt naeher gewaehlt. Beide Zahlen
 * kommen vom Heim-PC (`qa.haus_anteil_grundlage`, `qa.haus_anteil_bild`); hier wird nur
 * geschrieben und verglichen, nichts gemessen. `anders` nach derselben Regel wie am Heim-PC
 * (`baumasse.rahmt_anders`): ein Wert mindestens doppelt so gross wie der andere UND
 * mindestens 5 Prozentpunkte Unterschied — gesetzt, nicht gemessen.
 * `undefined`, wenn keine der beiden Zahlen geliefert ist: dann fehlt die Zeile, wie bisher.
 */
export const HAUS_RAHMUNG_FAKTOR = 2;
export const HAUS_RAHMUNG_MINDEST = 0.05;
export const HAUS_ANTEIL_VORBEHALT =
  'Am KI-Bild aus der Tiefe geschätzt, nicht gezählt. Weichen beide stark ab, hat die KI den ' +
  'Ausschnitt verändert — Zahlen zur Grundlage sprechen dann nicht über dieses Bild.';

function prozent(v: number): string {
  return `${(v * 100).toFixed(1).replace('.', ',')} %`;
}

export function hausAnteilText(
  qa: JobQa | undefined,
): { text: string; anders: boolean } | undefined {
  const g = qa?.haus_anteil_grundlage;
  const b = qa?.haus_anteil_bild;
  if (g === undefined && b === undefined) return undefined;
  const text =
    `Grundlage ${g === undefined ? 'nicht gemeldet' : prozent(g)} · ` +
    `KI-Bild ${b === undefined ? 'nicht gemessen' : `≈ ${prozent(b)}`}`;
  let anders = false;
  if (g !== undefined && b !== undefined) {
    const klein = Math.min(g, b);
    const gross = Math.max(g, b);
    anders = gross - klein >= HAUS_RAHMUNG_MINDEST && (klein <= 0 || gross / klein >= HAUS_RAHMUNG_FAKTOR);
  }
  return { text, anders };
}

/**
 * Verlauf-Nachgang: die fortlaufende Nummer eines Laufs an seinem Knoten
 * (`NodeLauf.laufNummer`, vergeben in `vis-runtime.ts`). Nur ein Lauf ohne
 * Nummer (von vor diesem Feld) faellt auf seine Stelle in der Reihe zurueck,
 * von hinten gezaehlt.
 */
export function laufNummerVon(lauf: VerlaufEintrag, index: number, laenge: number): number {
  return lauf.laufNummer ?? laenge - index;
}

/** Wann der Lauf fertig wurde; fuer aeltere Laeufe ohne diese Angabe der
 *  Start. `undefined`, wenn keines von beiden bekannt ist. */
export function laufZeit(lauf: Pick<NodeLauf, 'fertigUm' | 'gestartetUm'>): number | undefined {
  return lauf.fertigUm ?? lauf.gestartetUm;
}

const zwei = (n: number): string => String(n).padStart(2, '0');

/**
 * «16:58» in ORTSZEIT, 24 Stunden. Verlauf-Nachgang (HomeStation, 08.10.2026):
 * hier stand UTC ohne Kennzeichnung («07:03» um 09:03 Ortszeit), waehrend die
 * uebrige Oberflaeche Ortszeit zeigt. Bewusst ueber `getHours`/`getMinutes`
 * statt `toLocale…`: das Format haengt so an keiner Spracheinstellung.
 */
export function uhrzeitText(ms: number | undefined): string {
  if (ms === undefined) return '—';
  const d = new Date(ms);
  return `${zwei(d.getHours())}:${zwei(d.getMinutes())}`;
}

/** «07.10.2026 · 16:58» — Kopf der grossen Ansicht, Ortszeit wie oben. */
export function zeitpunktText(ms: number | undefined): string {
  if (ms === undefined) return 'Zeitpunkt unbekannt';
  const d = new Date(ms);
  return `${zwei(d.getDate())}.${zwei(d.getMonth() + 1)}.${d.getFullYear()} · ${uhrzeitText(ms)}`;
}
