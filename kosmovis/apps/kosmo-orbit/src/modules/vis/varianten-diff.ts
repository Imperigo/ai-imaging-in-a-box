import {
  topoReihenfolge,
  visPresetById,
  VIS_NODE_KATALOG,
  VIS_STIMMUNGEN,
  type VisGraph,
  type VisNode,
  type VisRenderAuftrag,
} from '@kosmo/kernel';
import type { RenderJob } from '@kosmo/contracts';
import { formularFeldText, type JobQa } from './vis-jobs';
import type { KurationEintrag, NodeLauf } from './vis-runtime';

/**
 * N2 (auf-20260826-49 Posten B5, Owner-Entscheid 03.09.2026) — `qa_je_kamera`
 * steht im Vertrag NEBEN `qa` (render-result.ts:375, Geschwisterfeld, kein
 * Kind) — `JobQa` (`vis-jobs.ts`, `NonNullable<RenderJob['result']>['qa']`)
 * deckt es darum NICHT ab. `vis-jobs.ts` selbst darf hier nicht angefasst
 * werden (paralleles Paket) — die Ableitung laeuft darum eigenstaendig ueber
 * denselben `RenderJob`-Import aus `@kosmo/contracts`, den `vis-jobs.ts`
 * bereits benutzt, statt einen Typ dort zu ergaenzen.
 */
export type JobQaJeKameraEintrag = NonNullable<
  NonNullable<RenderJob['result']>['qa_je_kamera']
>[number];

/** Bildquelle einer Kuratier-Karte — Bridge-Render (Job-Artefakt) ODER eine
 * Viewport-Aufnahme (dataURL, v0.6.7 P0). Identisch zur bestehenden
 * Unterscheidung in `bildQuelle()`/`BildKachel` (NodeCanvas.tsx) — kein
 * Sonderfall am Ziel, nur an einem Ort neu benannt.
 *
 * N2: `qaJeKamera` steht additiv NEBEN `qa`, genau wie im Vertrag selbst —
 * `qa` bleibt die Hauptauskunft, unveraendert. `undefined`/fehlend heisst:
 * kein Konsument oberhalb (`NodeCanvas.tsx`, ausserhalb dieses Dateikreises)
 * hat das Feld schon eingefaedelt — die Oberflaeche bleibt dann wie vor
 * diesem Paket, kein Kamera-Block erscheint. */
export type KuratierQuelle =
  | { jobId: string; bild: string; qa?: JobQa | undefined; qaJeKamera?: JobQaJeKameraEintrag[] | undefined }
  | { dataUrl: string };

/**
 * N4-Wache (ROADMAP 1340) — die Abbildung «fertiger Lauf → Kuratier-Quelle»,
 * herausgezogen aus `NodeCanvas.tsx`: `bildQuelle()` und die `renderKarten`-
 * Zuordnung bauten dasselbe Literal bisher JEDES an seiner eigenen Stelle neu
 * — identisch, aber ausserhalb jeder Probe, weil die Datei in dieser Suite nie
 * gerendert wird (Gegenprobe vor diesem Paket: alle drei Einfaedelstellen von
 * `qaJeKamera` probeweise entfernt, `n4-qa-je-kamera-zuleitung.test.ts` UND
 * `typecheck` blieben gruen). Jetzt gibt es nur noch DIESE eine Abbildung,
 * `NodeCanvas.tsx` ruft sie an beiden frueheren Stellen auf — eine Probe hier
 * bewacht damit direkt beide Konsumenten, ohne die `.tsx` zu rendern.
 *
 * `null`, wenn der Lauf (noch) kein fertiges Bild traegt — identische
 * Bedingung wie zuvor inline (`status==='fertig' && jobId && bild`).
 */
export function quelleAusLauf(
  lauf: Pick<NodeLauf, 'status' | 'jobId' | 'bild' | 'qa' | 'qaJeKamera'> | undefined,
): KuratierQuelle | null {
  if (!lauf || lauf.status !== 'fertig' || !lauf.jobId || !lauf.bild) return null;
  return {
    jobId: lauf.jobId,
    bild: lauf.bild,
    qa: lauf.qa,
    ...(lauf.qaJeKamera ? { qaJeKamera: lauf.qaJeKamera } : {}),
  };
}

/** N2 — Anzeige-Zeile fuer eine einzelne Kamera aus `qa_je_kamera`. Liest
 *  NUR die vom Worker bereits berechneten `passed`-Flaggen (Geometrie UND
 *  Stil, beide je Kamera optional) — `bestanden` ist die UND-Verknuepfung
 *  der vorhandenen Flaggen, keine neue Schwelle, keine Zahl-Rechnung. */
export interface KameraQaZeile {
  kamera: string;
  geometryBestanden?: boolean;
  styleBestanden?: boolean;
  /** `undefined`, wenn fuer diese Kamera weder Geometrie- noch Stil-QA
   *  vorliegt — keine erfundene Aussage ueber eine Kamera ohne Messung. */
  bestanden?: boolean;
}

/**
 * N2 — «Wer drei Ansichten bestellt und eine davon faellt durch, sieht heute
 * 'durchgefallen' und nicht, WELCHE» (render-result.ts:363, woertlich der
 * Absender). Diese Funktion ist der ganze Zweck von V2: je Kamera EIN
 * eigenes Urteil, statt eines einzigen Verdikts ueber den ganzen Lauf.
 */
export function kameraQaZeilen(eintraege: JobQaJeKameraEintrag[] | undefined): KameraQaZeile[] {
  if (!eintraege) return [];
  return eintraege.map((e) => {
    const geometryBestanden = e.geometry?.passed;
    const styleBestanden = e.style?.passed;
    const werte = [geometryBestanden, styleBestanden].filter((v): v is boolean => typeof v === 'boolean');
    return {
      kamera: e.kamera,
      ...(geometryBestanden !== undefined ? { geometryBestanden } : {}),
      ...(styleBestanden !== undefined ? { styleBestanden } : {}),
      ...(werte.length > 0 ? { bestanden: werte.every(Boolean) } : {}),
    };
  });
}

/** Eine Karte der Kuratierfläche — ein fertiger Render-Node ODER eine
 * gewählte Viewport-Aufnahme, plus die Laufzeit-Kuration (Stern/Ablage,
 * `vis-runtime.ts`) und (falls vorhanden) der ausgewertete Render-Auftrag für
 * den Parameter-Diff. */
export interface KuratierKartenDaten {
  node: VisNode;
  quelle: KuratierQuelle;
  kur: KurationEintrag;
  auftrag?: VisRenderAuftrag;
}

/**
 * Reine Ableitungs-Logik der Vis-Kuratierfläche (Welle 1, Soll-Bild
 * `Kosmo Viz Kuratierung.dc.html` §6.2) — KEIN React, KEIN DOM, unit-testbar.
 * Trennt die Datenaufbereitung (Kennung, Merkmale, Diff, Herkunft, Bewertung)
 * von der Darstellung in `KuratierFlaeche.tsx`/`KuratierInspektor.tsx`.
 */

/** Kompakte Anzeige-Kennung je Karte — 'V' für Render-Varianten, 'A' für
 * Viewport-Aufnahmen (v0.6.7 P0). Reine Positions-Nummerierung (stabile
 * Eingabereihenfolge), KEIN echter Renderer-Seed — das System kennt keinen. */
export function kartenId(typ: string, index: number): string {
  const praefix = typ === 'aufnahme' ? 'A' : 'V';
  return `${praefix}-${String(index + 1).padStart(2, '0')}`;
}

/** Kurze, stabile Kennung aus einer Bridge-Job-ID/Aufnahme-ID — ersetzt in der
 * Karten-Fusszeile ein "Seed" (das render-scene/v1-Protokoll kennt keinen);
 * bleibt trotzdem eindeutig genug, um zwei Karten auseinanderzuhalten. */
export function kurzKennung(id: string): string {
  return id.slice(-6).toUpperCase();
}

/** Menschenlesbare Merkmale einer Kuratier-Karte — Grundlage für Meta-Zeilen
 * (Inspektor), Karten-Fusszeile (Raster) und die Vergleichs-Diff-Tabelle. */
export interface VarianteMerkmale {
  typ: string;
  typLabel: string;
  szene: string;
  stimmung: string;
  faithful?: number;
  samples?: number;
  presetLabel?: string;
  qaBestanden?: boolean;
  /** Geeicht 23.08.2026 (P-EICHUNG, `render-result.ts` Nachtrag,
   *  `auftraege/von-homestation/auf-orbit-20260823-03.md`) — `rho_maske`
   *  gegen die Schwelle 0.80 verglichen. `undefined` heisst NICHT GEMESSEN
   *  (`rho_maske` fehlt oder ist `null`, P-NULLGEOMETRIE) — dieselbe
   *  Unterscheidung, die `ohneZahl()`/`nurAlteGeometrie()` unten schon fuer
   *  die Sterne-Bewertung treffen, hier fuer das Schwellen-Urteil. Bisher
   *  (Stand 27.08.2026, `docs/STAND-WORKERAUFTRAEGE-2026-08-27.md` Posten 1)
   *  verglich KEIN Konsument diesen Wert gegen die Zahl. */
  tiefenstaffelungBestanden?: boolean;
  /** `kante_an_maskengrenze` (`render-result.ts`, NEU 23.08.2026) — bereits
   *  vom Cloud-Worker als JA/NEIN geliefert (Schwelle 0.01 dort angewendet,
   *  nicht hier), darum reine Weitergabe, keine erneute Schwelle. Bisher
   *  (Stand 27.08.2026, s.o. Posten 2) zeigte KEINE Oberflaeche diesen Wert. */
  bauwerkVorhanden?: boolean;
  /**
   * Auftrag auf-20260827-62 (Posten 2, `docs/auftraege-kosmovis/
   * auf-20260827-62.md`) — `qa.verdict.reason`, reine Weitergabe. Der
   * Cloud-Worker setzt das Feld GENAU im Fall «Score besteht, Maskenweg
   * widerspricht» (`bestanden:true` UND Paarurteil widerspricht — z. B.
   * gemessen: Score 0.951, geom_iou 1.000, rho_maske −0.018 bei vollständig
   * verschwundenem Bauwerk); in jedem anderen Lauf bleibt das Feld weg
   * (`undefined`), also SELBSTLÖSCHEND auf Vertragsseite. Diese Oberfläche
   * führt dafür keine eigene Schwelle ein (Auflage) und kürzt/formuliert den
   * Satz nicht um (Auflage) — nur Weiterreichen an `qaBestanden`.
   */
  qaVorbehalt?: string;
  /**
   * N3 (`GeometryStatus`, render-result.ts:209) — trennt «gemessen» von
   * «nicht gemessen» von «nicht zustaendig». `undefined` heisst: der
   * Absender hat sich zu dieser Unterscheidung nicht geaeussert (KEIN
   * Default, wortgleich der Vertragskommentar) — dieselbe Nicht-Aussage,
   * die dieses Modul ueberall sonst schon fuer fehlende Felder trifft.
   */
  geometryStatus?: NonNullable<JobQa['geometry']>['status'];
  /**
   * N3 (R4, render-result.ts:219) — der NULLPROBEN-Anker: was ein Bild OHNE
   * JEDE Geometrie auf DIESER Szene bei `rho_maske` erreicht. Woertlich der
   * Absender: «ohne diese Zahl ist kein Score einzuordnen» (ROADMAP 1062,
   * leeres Grundstueck 0.9848 gegen 0.9703 fuers perfekte Bild bei
   * `geom_iou`). Reines Zeigen — KEINE Ableitung (kein Score-minus-Nullprobe
   * = Guete), solange niemand die Rechnung bestellt hat.
   */
  nullprobeRhoMaske?: number;
  /**
   * B148 (17.09.2026) — die Schwelle, gegen die das Geometrie-Urteil faellt
   * (`qa.geometry.threshold`, render-result.ts:215, Vertragsvorgabe 0.65).
   *
   * Sie kam bis heute im Vertrag an und wurde nirgends gezeigt. Eine Zahl
   * ohne ihre Schwelle ist nicht einzuordnen — das ist Regel 3 aus
   * `auf-20260826-52` woertlich: «Eine Zahl gehoert an die Bedingung, unter
   * der sie gemessen wurde.»
   *
   * `null` im Vertrag heisst «keine Schwelle angewendet» und zeigt sich wie
   * fehlend — dieselbe Nicht-Aussage wie ueberall sonst in diesem Modul.
   */
  geometrieSchwelle?: number;
}

/** Geeicht 23.08.2026 (P-EICHUNG, s. Feld-Kommentar oben). */
const RHO_MASKE_SCHWELLE = 0.8;

/** `undefined` heisst NICHT GEMESSEN (fehlend oder `null`) — dieselbe
 *  Behandlung wie `ohneZahl()` weiter unten, hier fuer das Schwellen-Urteil
 *  statt fuer die Sterne-Mittelung. Keine erfundene Schwelle auf einer
 *  Nicht-Messung. */
function tiefenstaffelungAusGeometrie(geometry: JobQa['geometry']): boolean | undefined {
  const wert = geometry?.rho_maske;
  if (wert === undefined || wert === null) return undefined;
  return wert >= RHO_MASKE_SCHWELLE;
}

export function varianteMerkmale(
  node: VisNode,
  auftrag: VisRenderAuftrag | undefined,
  qa: JobQa | undefined,
): VarianteMerkmale {
  const kat = VIS_NODE_KATALOG[node.typ];
  const szeneRoh = node.params?.['formSzene'];
  const szene = typeof szeneRoh === 'string' && szeneRoh ? formularFeldText('formSzene', szeneRoh) : '—';
  const presetRoh = node.params?.['preset'];
  const stimmung =
    typeof presetRoh === 'string' && presetRoh ? (VIS_STIMMUNGEN[presetRoh]?.label ?? presetRoh) : '—';
  const tiefenstaffelung = tiefenstaffelungAusGeometrie(qa?.geometry);
  const bauwerkVorhanden = qa?.geometry?.kante_an_maskengrenze;
  // N3: `status` — KEIN Default, `undefined` bedeutet «keine Aussage».
  const geometryStatus = qa?.geometry?.status;
  // N3: `nullprobe.rho_maske` — `null` heisst NICHT GEMESSEN (P-NULLGEOMETRIE,
  // wie ueberall sonst in diesem Modul), zeigt sich also wie fehlend.
  const nullprobeRho = qa?.geometry?.nullprobe?.rho_maske;
  // B148: die Schwelle, gegen die gemessen wurde. `null` heisst «keine
  // angewendet» und zeigt sich wie fehlend.
  const geometrieSchwelle = qa?.geometry?.threshold;
  return {
    typ: node.typ,
    typLabel: kat?.label ?? node.typ,
    szene,
    stimmung,
    ...(auftrag ? { faithful: auftrag.faithful, samples: auftrag.samples } : {}),
    ...(auftrag?.presetId ? { presetLabel: visPresetById(auftrag.presetId).name } : {}),
    ...(qa?.verdict ? { qaBestanden: qa.verdict.passed } : {}),
    ...(qa?.verdict.reason ? { qaVorbehalt: qa.verdict.reason } : {}),
    ...(tiefenstaffelung !== undefined ? { tiefenstaffelungBestanden: tiefenstaffelung } : {}),
    ...(bauwerkVorhanden !== undefined ? { bauwerkVorhanden } : {}),
    ...(geometryStatus !== undefined ? { geometryStatus } : {}),
    ...(nullprobeRho !== undefined && nullprobeRho !== null ? { nullprobeRhoMaske: nullprobeRho } : {}),
    ...(geometrieSchwelle !== undefined && geometrieSchwelle !== null
      ? { geometrieSchwelle }
      : {}),
  };
}

export interface DiffZeile {
  label: string;
  a: string;
  b: string;
  abweichend: boolean;
}

function fmtFaithful(v?: number): string {
  return v === undefined ? '—' : v.toFixed(2);
}
function fmtSamples(v?: number): string {
  return v === undefined ? '—' : String(v);
}
function fmtQa(v?: boolean): string {
  return v === undefined ? '—' : v ? 'bestanden' : 'verfehlt';
}
/** Auftrag auf-20260827-62 (Posten 2) — der Vertragswortlaut bleibt
 *  UNGEKÜRZT (Auflage); ohne Vorbehalt bleibt der Platzhalter der anderen
 *  Zeilen ('—'), kein erfundener Text. */
function fmtVorbehalt(v?: string): string {
  return v ?? '—';
}
function fmtJaNein(v?: boolean): string {
  return v === undefined ? '—' : v ? 'ja' : 'nein';
}
/** N3 — deutsche Uebersetzung der drei `GeometryStatus`-Werte. */
function fmtGeometryStatus(v?: NonNullable<JobQa['geometry']>['status']): string {
  if (v === 'measured') return 'gemessen';
  if (v === 'not_measured') return 'nicht gemessen';
  if (v === 'not_applicable') return 'nicht zuständig';
  return '—';
}
/** N3 — der Nullproben-Anker, reines Zeigen (Auflage: keine Ableitung). */
function fmtNullprobeRho(v?: number): string {
  return v === undefined ? '—' : v.toFixed(2);
}
/** B148 — die Schwelle, reines Zeigen. Kein Vergleich, kein eigenes Urteil. */
export function fmtGeometrieSchwelle(v?: number): string {
  return v === undefined ? '—' : v.toFixed(2);
}
/** B148 — die drei Geometrie-Zustaende, auch ausserhalb der A/B-Tabelle
 *  verwendbar (der Kurations-Inspektor zeigt sie seit B148 ebenfalls). */
export function geometrieStatusText(v?: NonNullable<JobQa['geometry']>['status']): string {
  return fmtGeometryStatus(v);
}
/** B148 — der Nullproben-Anker, ausserhalb der A/B-Tabelle verwendbar. */
export function nullprobeRhoText(v?: number): string {
  return fmtNullprobeRho(v);
}

/** A/B-Parameter-Diff (Soll-Bild §6.2) — abweichende Zeilen tragen
 * `abweichend: true`, die Darstellung macht daraus Fettschrift + Rollenfarbe. */
export function varianteDiff(a: VarianteMerkmale, b: VarianteMerkmale): DiffZeile[] {
  const zeile = (label: string, av: string, bv: string): DiffZeile => ({ label, a: av, b: bv, abweichend: av !== bv });
  return [
    zeile('Node-Typ', a.typLabel, b.typLabel),
    zeile('Szene', a.szene, b.szene),
    zeile('Stimmung', a.stimmung, b.stimmung),
    zeile('Preset', a.presetLabel ?? '—', b.presetLabel ?? '—'),
    zeile('Geometrie-Treue', fmtFaithful(a.faithful), fmtFaithful(b.faithful)),
    zeile('Samples', fmtSamples(a.samples), fmtSamples(b.samples)),
    zeile('QA-Verdikt', fmtQa(a.qaBestanden), fmtQa(b.qaBestanden)),
    // U11 (auf-20260827-62): der Vorbehalt bleibt IN DERSELBEN Tabelle,
    // direkt bei der Zahl, die er einschränkt — nicht auf einer anderen
    // Seite/in einem separaten Panel.
    zeile('QA-Vorbehalt', fmtVorbehalt(a.qaVorbehalt), fmtVorbehalt(b.qaVorbehalt)),
    // N3 — trennt «gemessen»/«nicht gemessen»/«nicht zustaendig» sichtbar,
    // statt beide Nichtmessungen gleich aussehen zu lassen.
    zeile('Geometrie-Status', fmtGeometryStatus(a.geometryStatus), fmtGeometryStatus(b.geometryStatus)),
    // P-BEFUNDSICHT (27.08.2026, `docs/STAND-WORKERAUFTRAEGE-2026-08-27.md`
    // Posten 1+2) — Labels wie in der Uebergabetabelle des Cloud-Workers
    // (`auf-orbit-20260823-03.md`): «Tiefenstaffelung» fuer rho_maske gegen
    // 0.80, «Bauwerk vorhanden» fuer kante_an_maskengrenze.
    zeile('Tiefenstaffelung', fmtQa(a.tiefenstaffelungBestanden), fmtQa(b.tiefenstaffelungBestanden)),
    // N3 — der Nullproben-Anker steht UNMITTELBAR neben seinem Hauptwert
    // (Tiefenstaffelung/rho_maske), damit ein Score neben seiner Nullprobe
    // gelesen wird (ROADMAP 1062). Reines Zeigen, keine Ableitung.
    zeile('Nullprobe (rho_maske)', fmtNullprobeRho(a.nullprobeRhoMaske), fmtNullprobeRho(b.nullprobeRhoMaske)),
    zeile('Bauwerk vorhanden', fmtJaNein(a.bauwerkVorhanden), fmtJaNein(b.bauwerkVorhanden)),
  ];
}

/**
 * v0.9.42 P-QA-ZAHLEN: erkennt, ob eine `GeometryQA` NUR die vier alten,
 * vom Cloud-Worker widerlegten Zahlen traegt (`geometry_fidelity`, `spearman`,
 * `geom_iou`, `threshold`) — also KEINES der additiven Felder
 * `rho_maske`/`kantenanteil`/`paarurteil` (EINBAU_CLOUDWORKER_2026-08-22 §1).
 * Ein `GeometryQA` ganz ohne jedes Feld (theoretisch moeglich, da jetzt alles
 * optional ist) faellt bewusst in denselben Fall: keine belastbare Grundlage,
 * also dieselbe Behandlung wie „nur alte Zahlen".
 *
 * **NACHTRAG 22.08.:** die Pruefung fragte nur nach `kante` — dem Namen, zu
 * dem ich das Feld in v0.9.42 abgekuerzt hatte. Der Cloud-Worker schickt
 * `kantenanteil`. Ein Ergebnis mit SEINEM Namen waere hier faelschlich als
 * «nur alte Zahlen» eingestuft worden und haette den Satz «Bewertung
 * zurueckgezogen» bekommen, obwohl die tragfaehigen Zahlen vorlagen. Jetzt
 * zaehlen beide Namen; `kantenanteil` ist der kanonische.
 */
/**
 * NACHTRAG 23.08. (P-NULLGEOMETRIE): seit die Zahlen-Masse der Geometrie-QA
 * `null` sein duerfen («null heisst NICHT GEMESSEN», s. `render-result.ts`),
 * reicht `=== undefined` hier nicht mehr. Ein Ergebnis mit
 * `rho_maske: null` haette sonst als «traegt neue Zahlen» gegolten und den
 * Satz «Bewertung zurueckgezogen» NICHT bekommen — obwohl nichts
 * Tragfaehiges gemessen wurde. **Fehlend und nicht-gemessen sind fuer diese
 * Frage dasselbe**, und genau darum steht hier ein eigener Helfer statt
 * viermal derselben Bedingung: die naechste Erweiterung soll ihn benutzen,
 * nicht die Bedingung neu erfinden.
 */
function ohneZahl(wert: number | null | undefined): boolean {
  return wert === undefined || wert === null;
}

function nurAlteGeometrie(geometry: JobQa['geometry']): boolean {
  if (!geometry) return false;
  return (
    ohneZahl(geometry.rho_maske) &&
    ohneZahl(geometry.kantenanteil) &&
    ohneZahl(geometry.kante) &&
    (geometry.paarurteil === undefined || geometry.paarurteil === null)
  );
}

/** Sterne-Bewertung (0–5), EHRLICH aus der QA abgeleitet — das Datenmodell
 * kennt kein manuelles Rating-Feld (vis-runtime.ts ist eingefroren). Ohne QA
 * bleibt die Bewertung 0 (leer) statt eine erfundene Zahl zu zeigen.
 *
 * v0.9.42 P-QA-ZAHLEN: `geometry_fidelity` fliesst NICHT MEHR in die Mittelung
 * ein — der Cloud-Worker hat es zwischen dem 20. und 22.08. als unbrauchbar
 * gemessen (nicht monoton: 2 m Versatz 0.1191, 4 m Versatz 0.2301), und die
 * neuen Felder (`rho_maske`/`kante`/`paarurteil`) sind bewusst NICHT auf eine
 * Ersatzzahl umgerechnet — «ein einzelner Score kann Existenz und Richtigkeit
 * nicht zugleich beantworten», wortgleich die Bauvorschrift des
 * Cloud-Workers. Traegt ein Ergebnis NUR die alten, widerlegten
 * Geometrie-Zahlen (`nurAlteGeometrie`), zeigt die Oberflaeche darum KEIN
 * Urteil mehr — auch dann nicht, wenn ein gueltiger `style_score` daneben
 * vorliegt: kein stilles Weiterrechnen mit der Haelfte der Grundlage. Das
 * ist dieselbe Sterne-Skala (0), ueber die die Oberflaeche bei fehlender QA
 * ohnehin schon "Keine QA-Bewertung vorhanden." zeigt (KuratierInspektor.tsx)
 * — ein leeres Feld ist ehrlicher als ein falsches Abzeichen. */
export function sterneAusQa(qa: JobQa | undefined): number {
  if (!qa) return 0;
  if (nurAlteGeometrie(qa.geometry)) return 0;
  const werte = [qa.style?.style_score].filter((v): v is number => typeof v === 'number');
  if (werte.length === 0) return qa.verdict.passed ? 4 : 2;
  const mittel = werte.reduce((s, v) => s + v, 0) / werte.length;
  return Math.max(0, Math.min(5, Math.round(mittel * 5)));
}

/** Herkunft-Chain (Soll-Bild §6.2 „Herkunft") — alle Vorfahren-Nodes eines
 * Ziels in Auswertungsreihenfolge (`topoReihenfolge`), reine Ableitung aus
 * dem Graphen selbst, keine erfundenen Zwischenschritte. */
/**
 * Warum die Sterne leer sind — die Unterscheidung, die `sterneAusQa()` allein
 * nicht ausdruecken kann (Nachtrag v0.9.42; Luecke in meinem eigenen
 * Dateikreis: die Anzeigedatei stand nicht in der Spez).
 *
 * **Null Sterne hatte bisher zwei ganz verschiedene Bedeutungen, und die
 * Oberflaeche sagte beide gleich:** «es kam nichts zurueck» und «es kam etwas
 * zurueck, aber seine Grundlage ist widerrufen». Fuer den Architekten am
 * Bildschirm ist das der Unterschied zwischen «noch nicht geprueft» und
 * «geprueft, aber das Ergebnis taugt nichts» — und der zweite Fall ist der
 * gefaehrlichere, weil er wie der erste aussieht.
 *
 * `widerrufen` heisst: es LIEGEN Geometrie-Zahlen vor, aber nur die vom
 * Cloud-Worker als unbrauchbar gemessenen (`geom_iou` belohnt die
 * Abwesenheit — leeres Grundstueck 0.9848 gegen 0.9703 fuers perfekte Bild;
 * `geometry_fidelity` ist nicht monoton). Keine erfundene Ersatzzahl, kein
 * Weiterrechnen — nur ein anderer Satz.
 *
 * N3-NACHTRAG: `status: 'not_applicable'` (render-result.ts:209) trug bis
 * hierhin KEIN eigenes Zeichen — «keine tragfaehigen Zahlen» fiel pauschal
 * in `widerrufen` (gemessen, aber die Grundlage ist widerlegt) oder
 * `ohne-qa` (nichts kam zurueck). Beides ist etwas anderes als «hier war
 * nichts zu messen» (z. B. steht hinter dem Bauwerk ein Nachbargebaeude statt
 * Himmel — die Messung LIEF, kann auf DIESER Szene aber nichts sagen). Der
 * vierte Fall `'nicht-zustaendig'` macht diesen Unterschied SICHTBAR statt
 * ihn intern zu verschlucken — und geht der `widerrufen`-Pruefung vor:
 * traegt ein Ergebnis `status:'not_applicable'` UND nur alte Geometrie-
 * Zahlen, ist es «hier war nichts zu messen», nicht «gemessen und widerlegt».
 */
export type BewertungsLage = 'bewertet' | 'ohne-qa' | 'widerrufen' | 'nicht-zustaendig';

export function bewertungsLage(qa: JobQa | undefined): BewertungsLage {
  if (!qa) return 'ohne-qa';
  if (qa.geometry?.status === 'not_applicable') return 'nicht-zustaendig';
  if (nurAlteGeometrie(qa.geometry)) return 'widerrufen';
  return sterneAusQa(qa) > 0 ? 'bewertet' : 'ohne-qa';
}

export function herkunftChain(graph: VisGraph, zielId: string): VisNode[] {
  const eingehend = new Map<string, string[]>();
  for (const e of graph.edges) {
    const liste = eingehend.get(e.to) ?? [];
    liste.push(e.from);
    eingehend.set(e.to, liste);
  }
  const vorfahren = new Set<string>();
  const stack = [zielId];
  while (stack.length > 0) {
    const cur = stack.pop()!;
    for (const von of eingehend.get(cur) ?? []) {
      if (!vorfahren.has(von)) {
        vorfahren.add(von);
        stack.push(von);
      }
    }
  }
  return topoReihenfolge(graph).filter((n) => vorfahren.has(n.id) || n.id === zielId);
}
