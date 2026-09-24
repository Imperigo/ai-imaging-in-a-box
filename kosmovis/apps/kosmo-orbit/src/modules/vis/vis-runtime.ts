import { create } from 'zustand';
import type { JobQa } from './vis-jobs';
import type { RenderJob } from '@kosmo/contracts';

/**
 * N4 (die Zuleitung, 03.09.2026) — ein Eintrag aus `qa_je_kamera`.
 *
 * Der Typ wird hier LOKAL aus `RenderJob` abgeleitet und NICHT aus
 * `varianten-diff.ts` importiert, obwohl er dort unter demselben Namen
 * steht: `varianten-diff.ts:12` importiert seinerseits aus dieser Datei
 * (`KurationEintrag`) — ein Import zurueck waere ein Ringschluss. Dieselbe
 * Ableitung an zwei Orten ist hier der billigere Preis; sie kann nicht
 * auseinanderlaufen, weil beide aus demselben Vertrag lesen.
 */
export type JobQaJeKamera = NonNullable<
  NonNullable<RenderJob['result']>['qa_je_kamera']
>[number];

/**
 * Laufzeit-Zustand des Render-Graphen (P2) — BEWUSST ausserhalb des Doc:
 * Job-Status und Bilder wandern nie durch Undo oder Yjs (kein Base64 im
 * Sync). Memo-Schlüssel = Hash der Render-Parameter: ändert sich nichts,
 * bleibt das Bild gültig und der Node zeigt «aktuell».
 */

/**
 * Lebenszyklus eines Node-Laufs (V2-Technik Block 1 / HS3). Spiegelt den
 * Bridge-Job-Zustand EHRLICH:
 *  - `gesendet`        — lokal abgesendet, noch keine Bridge-Antwort
 *  - `wartetFreigabe`  — Bridge verlangt Freigabe (awaiting_approval)
 *  - `wartetGpu`       — Bridge-Status `queued`: angenommen, noch nicht
 *    begonnen. **Der Name ist historisch — der Grund ist es NICHT.**
 *    HOMESTATION-2026-08-19-PUBLISH-UND-KOSMO.md §11 (Nachtrag «der Auftrag
 *    bleibt liegen») hat am echten Gerät gemessen: die GPU war frei (0 %
 *    Last, 15,5 W Ruhe), der Auftrag stand trotzdem elf Stunden auf
 *    `queued` — «wartet auf GPU-Leerlauf» nannte einen Grund, der
 *    nachweislich nicht vorlag, und schickte die Suche an die Grafikkarte
 *    statt an den fehlenden Abholer. Geprüft (erg-20260819-17.md): `/health`
 *    liefert das `gpu`-Feld ausserhalb des `--fake`-Betriebs überhaupt
 *    nicht (`tools/homestation-bridge/kosmo_bridge/main.py`, `GpuStatus.tsx`-
 *    Kopfkommentar), und es gibt keinen Bridge-Endpunkt, der meldet, ob
 *    überhaupt ein Abholer (Blender-/ComfyUI-Worker) läuft — der Client
 *    kann das schlicht nicht wissen. Die Beschriftung (`WARTET_ABHOLER_LABEL`
 *    / `wartetAbholerText` unten) behauptet darum keinen Grund mehr, nennt
 *    aber die Wartezeit, wenn sie bekannt ist.
 *  - `rendert`         — Worker rechnet (running)
 *  - `fertig`          — Ergebnis da (done + result)
 *  - `fehler`          — error / Netz-/Bridge-Fehler
 *  - `abgebrochen`     — vom Nutzer abgebrochen (cancelled)
 *  - `zeitueberschreitung` — lokaler Wächter: zu lange ohne Ergebnis
 */
export type NodeLaufStatus =
  | 'gesendet'
  | 'wartetFreigabe'
  | 'wartetGpu'
  | 'rendert'
  | 'fertig'
  | 'fehler'
  | 'abgebrochen'
  | 'zeitueberschreitung';

export interface NodeLauf {
  status: NodeLaufStatus;
  jobId?: string;
  bild?: string;
  qa?: JobQa;
  /**
   * N4 — `qa_je_kamera` aus dem Vertrag, additiv NEBEN `qa`. `qa` bleibt die
   * Hauptauskunft, unveraendert. Fehlt das Feld, heisst das «der Worker hat
   * je Kamera nichts gesagt» — kein Default, keine erfundene Liste.
   *
   * WARUM ES HIER STEHT: N2 hat die Anzeige gebaut (`varianten-diff.ts`,
   * `KuratierFlaeche.tsx`) und dabei selbst gemeldet, dass sie leer bleibt,
   * solange niemand das Feld einfaedelt — `NodeCanvas.tsx` reichte nur
   * `qa: j.result.qa` weiter. Eine Anzeige ohne Zuleitung ist genau die
   * Klasse «gebaut und nicht bestellt» (ROADMAP 1063), gegen die dieses
   * Paket ueberhaupt angetreten ist.
   */
  qaJeKamera?: JobQaJeKamera[];
  fehler?: string;
  /** Freigabe-Token aus dem Create-Response — nötig für `/approve`. */
  approvalToken?: string;
  /** Wer den Job übernommen hat (z. B. "fake-worker" oder ein echter Worker). */
  worker?: string;
  /** Laufende Etappe des Workers — der Node zeigt Phase + Prozent (HS3-Auflage 5). */
  progress?: { phase: string; pct: number };
  /** Zeitpunkt des Absendens (ms, Date.now) — Basis des Timeout-Wächters. */
  gestartetUm?: number;
  /**
   * Auftrag auf-20260901-70 (Posten 1) — der Grund, den der Bridge-Job im
   * Vertragsfeld `RenderJob.message` mitliefert, WÄHREND er `queued` bleibt
   * (z. B. «Karte nicht frei»). `undefined`/leer heisst: kein Grund bekannt,
   * NICHT «es gibt keinen» — die Anzeige erfindet dafür nichts, dieselbe
   * Regel wie beim Vertrag selbst.
   *
   * Explizit `| undefined` (statt nur `?:`) wegen `exactOptionalPropertyTypes`:
   * `patchLauf` MISCHT (`{ ...alt, ...patch }`), löscht also kein Feld von
   * selbst. Ohne den expliziten `undefined`-Typ könnte der Poll das Feld beim
   * nächsten Statuswechsel nicht aktiv LEEREN — ein längst laufender Job
   * zeigte sonst weiter den Wartegrund von vorhin.
   */
  wartetGrund?: string | undefined;
  /** Parameter-Hash beim Absenden — weicht der Graph ab, ist das Bild «veraltet». */
  memoKey: string;
}

/** Zustände, in denen ein Lauf noch «offen» ist (der Poll fragt sie ab). */
export const OFFENE_LAUF_STATUS: readonly NodeLaufStatus[] = [
  'gesendet',
  'wartetFreigabe',
  'wartetGpu',
  'rendert',
];

/**
 * Default-Wächter — v0.9.21 P-E (`docs/V0921-SPEZ.md` §3 P-E,
 * `docs/BEFUND-FERNRENDER.md` §2.3 Punkt 3): die alten 10 min waren für eine
 * per Azure-GPU-Ausfallschutz erreichte Maschine laut Befund «knapp».
 * GEPRÜFT statt übernommen, in zwei Teilen:
 *
 * 1. Zählt `wartetFreigabe` mit? NEIN, schon heute nicht (`istZeitUeberschritten`
 *    unten — «der Mensch entscheidet», offener Code, keine Lücke) — das
 *    bleibt unverändert richtig und wurde NICHT angefasst.
 * 2. Ist eine Erhöhung trotzdem nötig? JA, und zwar unabhängig vom WAN: der
 *    einzige im Repo dokumentierte reale Render-Beleg nennt für die
 *    HomeStation-5090 selbst **20 Minuten** reine Rechenzeit für einen
 *    anspruchsvollen Auftrag (`docs/RECHERCHE-AZURE-STARTUP.md:222-223`) —
 *    das allein läge schon über dem alten 10-Minuten-Limit, OHNE jede
 *    WAN-Zusatzzeit. Dazu kommt bei einer bedarfsweise hochgefahrenen
 *    Azure-GPU (Kaltstart, Checkpoint laden) eine Warteschlangenzeit, die
 *    IN diesem Fenster mitzählt (`wartetGpu`) und die der Befund selbst
 *    nicht misst (§3 «was diese Messung NICHT feststellen konnte»).
 *
 * Neuer Wert: 30 min = 20 min dokumentierter Rechenaufwand + 10 min Marge
 * für Warteschlange/Kaltstart/WAN-Upload. Die Marge ist eine Schätzung
 * (keine Kaltstart-Zahl im Repo belegt), bewusst nicht grösser gewählt: ein
 * wirklich hängender Job soll den Nutzer nicht eine halbe Stunde lang im
 * Unklaren lassen.
 */
export const RENDER_TIMEOUT_MS_DEFAULT = 30 * 60 * 1000;

/**
 * Reine, unit-getestete Timeout-Entscheidung. Ein Lauf ist überschritten, wenn
 * er noch offen ist (kein Endzustand), einen Startzeitpunkt trägt und seit
 * `gestartetUm` mehr als `limitMs` vergangen sind. `wartetFreigabe` zählt NICHT
 * als überschritten — dort wartet die Kette bewusst auf den Menschen.
 */
export function istZeitUeberschritten(
  lauf: Pick<NodeLauf, 'status' | 'gestartetUm'>,
  jetzt: number,
  limitMs: number,
): boolean {
  if (lauf.gestartetUm === undefined) return false;
  if (lauf.status === 'wartetFreigabe') return false;
  const offen =
    lauf.status === 'gesendet' || lauf.status === 'wartetGpu' || lauf.status === 'rendert';
  if (!offen) return false;
  return jetzt - lauf.gestartetUm > limitMs;
}

/**
 * HOMESTATION-2026-08-19-PUBLISH-UND-KOSMO.md §11 — die ehrliche Beschriftung
 * für `wartetGpu`, s. Kopfkommentar an `NodeLaufStatus`. DREI Formen derselben
 * EINEN Quelle (kein Handkopie-Risiko wie beim «Draw»-Fund vom selben Tag):
 * `WARTET_ABHOLER_LABEL` für die kompakte Status-Badge (Viewport3D.tsx,
 * NodeCanvas.tsx), `wartetAbholerText` für die grosse Platzhalter-Fläche
 * (NodeCanvas.tsx) — sie nennt zusätzlich die Wartezeit, wenn `gestartetUm`
 * bekannt ist (elf Stunden „wartet …" ohne Zeitangabe wäre selbst eine
 * Irreführung), und was der Architekt prüfen kann. Was sie NIE tut: einen
 * Grund nennen, den der Client nicht kennt (keine GPU, kein „Leerlauf").
 *
 * Die dritte Form kam als Nachtrag desselben Pakets: das Companion-Widget
 * trug in `shell/companion-daten.ts` unabhängig davon «WARTET AUF GPU» —
 * dieselbe erfundene Ursache an einer vierten Stelle. Sie bekommt keine
 * eigene Formulierung, sondern `WARTET_ABHOLER_KURZ` von hier. Die
 * Klammer «(Grund unbekannt)» fällt dort weg, weil das Kartenlabel in
 * Grossbuchstaben-Mono neben Werten wie «WARTET AUF FREIGABE» (19 Zeichen)
 * steht und die volle Fassung mit 40 Zeichen die Zeile sprengt — was
 * bleibt, ist die Aussage, die zählt: es wartet, und niemand hat es
 * geholt. Ein Grund wird auch hier nicht genannt.
 */
export const WARTET_ABHOLER_LABEL = 'wartet — nicht abgeholt (Grund unbekannt)';

/** Grossbuchstaben-Kurzform für das Companion-Kartenlabel — s. oben. */
export const WARTET_ABHOLER_KURZ = 'WARTET — NICHT ABGEHOLT';

/**
 * Auftrag auf-20260901-70 (Posten 1, `docs/auftraege-kosmovis/
 * auf-20260901-70.md`) — die HomeStation-Bridge schreibt den Wartegrund seit
 * 01.09.2026 in `RenderJob.message`, solange der Job `queued` bleibt (Karte
 * belegt/`idle_window_only`, Freigabe gilt nicht). Bis dahin galt der
 * Kopfkommentar oben uneingeschränkt: «behauptet keinen Grund, den der
 * Client nicht kennt» — das war richtig, SOLANGE er ihn nicht kannte. Kennt
 * der Client ihn (Feld gesetzt, nicht leer), zeigt die kompakte Badge das
 * jetzt — ohne den Grund selbst zu erfinden oder zu deuten, reine
 * Weitergabe. Bleibt `grund` leer/`undefined`, unverändert `WARTET_ABHOLER_
 * LABEL` — ein fehlender Grund wird NICHT zu einem erfundenen (Auflage des
 * Auftrags).
 */
export function wartetAbholerLabel(grund: string | undefined): string {
  return grund ? 'wartet — abgeholt, zurückgestellt' : WARTET_ABHOLER_LABEL;
}

/**
 * Die Grossbuchstaben-Kurzform desselben Entscheids, fuer die Companion-Karte
 * (`shell/companion-daten.ts`) — Nachtrag zu auf-20260901-70, Posten 1.
 *
 * **Die Platzfrage, die der Kopfkommentar an `WARTET_ABHOLER_KURZ` aufwirft,
 * ist hier gemessen und faellt weg:** «WARTET — ZURÜCKGESTELLT» ist mit **23
 * Zeichen exakt so lang** wie «WARTET — NICHT ABGEHOLT». Die Karte wird also
 * nicht breiter, als sie im Wartefall ohnehin schon ist. Der dort genannte
 * Vergleichswert «WARTET AUF FREIGABE» (19) ist kuerzer als BEIDE Fassungen —
 * die 23 Zeichen sind seit v0.9.36 der Bestand, nicht eine neue Zumutung.
 *
 * Wie bei der langen Fassung wird **kein Grund genannt**, nur der Wechsel der
 * Aussage: nicht mehr «niemand hat abgeholt», sondern «abgeholt und
 * zurueckgestellt». Der Wortlaut aus `message` steht in der grossen Flaeche
 * (`wartetAbholerText`) — auf einer Karte in Grossbuchstaben-Mono waere er
 * unlesbar, und ihn dort zu kuerzen hiesse, ihn umzuformulieren. Das verbietet
 * der Auftrag ausdruecklich.
 */
export const WARTET_ABHOLER_KURZ_ZURUECK = 'WARTET — ZURÜCKGESTELLT';

/** Kurzform-Gegenstueck zu `wartetAbholerLabel` — dieselbe Verzweigung, damit
 *  Karte und Badge nie auseinanderlaufen koennen. */
export function wartetAbholerKurz(grund: string | undefined): string {
  return grund ? WARTET_ABHOLER_KURZ_ZURUECK : WARTET_ABHOLER_KURZ;
}

/** Minuten/Stunden lesbar — ohne eine Sekunden-Genauigkeit vorzutäuschen,
 *  die der 2,5-Sekunden-Poll nicht liefert. */
export function formatDauer(ms: number): string {
  const minuten = Math.floor(ms / 60_000);
  if (minuten < 1) return '< 1 Min.';
  if (minuten < 60) return `${minuten} Min.`;
  const stunden = Math.floor(minuten / 60);
  const restMinuten = minuten % 60;
  return restMinuten === 0 ? `${stunden} h` : `${stunden} h ${restMinuten} min`;
}

/**
 * Volltext für die Platzhalter-Fläche: nennt nur, was messbar ist — dass
 * noch nicht begonnen wurde, seit wann (lokale Sendezeit `gestartetUm`,
 * `undefined` bleibt ohne Zeitangabe statt einen Wert zu erfinden), und was
 * der Architekt prüfen kann.
 *
 * `grund` (Auftrag auf-20260901-70, Posten 1) — mit gesetztem `RenderJob.
 * message` ist die Frage «Läuft auf der HomeStation ein Render-Abholer?»
 * FALSCH: der Abholer läuft nachweislich, denn nur er schreibt dieses Feld
 * (der Auftrag selbst nennt genau diese Unterscheidung — «niemand holt ab»
 * gegen «es wurde abgeholt und bewusst nicht gerechnet»). Die Frage steht
 * darum nur noch im Fall OHNE Grund; mit Grund tritt der Wortlaut aus
 * `message` an ihre Stelle, unverändert (keine Kürzung/Umformulierung).
 */
export function wartetAbholerText(
  gestartetUm: number | undefined,
  jetzt: number,
  grund?: string,
): string {
  const seit = gestartetUm === undefined ? '' : ` seit ${formatDauer(jetzt - gestartetUm)}`;
  if (grund) {
    return `wartet${seit} — abgeholt, zurückgestellt: ${grund}`;
  }
  return `wartet${seit} — noch nicht abgeholt (Grund unbekannt). Läuft auf der HomeStation ein Render-Abholer?`;
}

/**
 * V-H5 (Welle 3, Kuratier-Fläche): Kuration eines Renderbilds am Node —
 * «markiert» (Stern) und «verworfen» (Ablage statt Löschen, VORFORM-UI-
 * KONZEPT §1.5 «Layout 02» als Ablage, nichts geht verloren). BEWUSST hier
 * in vis-runtime, nicht im Doc: die Kuration hängt am AKTUELLEN Bild eines
 * Nodes (Laufzeit), nicht an einer Modell-Eigenschaft — kein Undo, kein
 * Yjs-Sync, wie `laeufe` selbst («Laufzeit ≠ Modell»).
 */
export interface KurationEintrag {
  markiert: boolean;
  verworfen: boolean;
}

/**
 * Ein GERECHNETES Bild zu einer Kuratier-Karte (12.09.2026) — das Ergebnis von
 * `farbangleich` bzw. `nachbearbeitung` aus `@kosmo/kernel`.
 *
 * WARUM ES DIESEN EINTRAG BRAUCHT, gemessen: bevor er da war, gab es in
 * dieser Anwendung keinen Ort für ein bearbeitetes Bild. Ein fertiger Lauf
 * traegt `NodeLauf.bild` — das ist ein DATEINAME auf der Bruecke, kein
 * Bildinhalt; eine Viewport-Aufnahme traegt `Aufnahme.dataUrl`, aber die
 * gehoert dem Aufnahme-Node. Ein Rechenergebnis am fertigen Bild passte in
 * keines von beiden. Ohne diesen Eintrag koennte man die zwei Kernmodule
 * zwar aufrufen, aber ihr Ergebnis nirgends hinlegen — und genau das ist der
 * Unterschied zwischen «gebaut» und «angeschlossen».
 *
 * BEWUSST LAUFZEIT, wie `kuration`/`laeufe` darueber: `entities.ts:500-505`
 * haelt fest, dass Render-Graph-Bilder NIE durch Undo/Yjs/`.kosmo` gehen
 * (Base64 im Sync ist die ausdruecklich untersagte Eigenschaft). Ein
 * gerechnetes Bild ist genauso ein Bild — es faellt unter dieselbe Regel und
 * ueberlebt einen Neustart darum NICHT. Das ist keine Luecke, sondern
 * dieselbe Grenze wie beim Bild, aus dem es entstand.
 */
export interface GerechnetesBild {
  /** Das Ergebnis als PNG-dataURL. */
  dataUrl: string;
  /**
   * Welches Werkzeug — steht im Inspektor ueber dem Bericht.
   *
   * `'uebernahme'` kam am 17.09.2026 dazu (Abnahmeliste Zeile 54). Sie gehoert
   * in DIESE Ablage und nicht in eine eigene, weil sie in DERSELBEN Schicht
   * liegt wie die zwei anderen: sie ERSETZT den Farbangleich, sie stapelt
   * sich nicht darauf. Lagen beide in getrennten Ablagen, bliebe der
   * Farbangleich darunter liegen und kaeme beim Zuruecknehmen der Uebernahme
   * wieder zum Vorschein — ein Bild, das niemand zurueckgeholt hat.
   *
   * Der Unterschied zu `gehobeneBilder`: die Belichtung liegt wirklich
   * DARUEBER und rechnet auf dem Ergebnis der drei hier. Darum hat SIE eine
   * eigene Ablage und diese drei teilen sich eine.
   */
  art: 'farbangleich' | 'nachbearbeitung' | 'uebernahme';
  /**
   * Was GEMESSEN wurde, zeilenweise im Klartext (Maskenflaechen, Werte vorher/
   * nachher, Kennlinien-Kennzahlen). Beide Kernmodule liefern diesen Bericht
   * mit, und beide begruenden ausdruecklich, warum: «eine unsichtbare Maske
   * ist eine Behauptung». Ihn wegzulassen machte das Werkzeug wieder zur
   * Blackbox, die man nur am Bild beurteilen kann.
   */
  bericht: string[];
  /** Die Zusage, die die Rechnung aus ihrer Bauart heraus gibt. */
  zusage: string;
  /**
   * Kurzform fuer die Kopfzeile: was uebernommen wurde und woher.
   * Nur die Uebernahme fuellt es — die zwei anderen haben nichts zu nennen,
   * was nicht schon in `art` steht.
   */
  kopfzeile?: string;
  /**
   * Die Karte, zu der dieses Ergebnis gehoert — GUERTEL UND HOSENTRAEGER
   * neben dem Schluessel der Ablage.
   *
   * Warum doppelt: der Kurations-Inspektor wird beim Kartenwechsel NICHT neu
   * aufgebaut. Ein Eintrag, der unter einem Schluessel liegt aber eine andere
   * Karte nennt, zeigte sonst das Bild der vorigen Karte als das der
   * naechsten — und zwar mit deren Bericht. Eine Probe haelt das fest.
   *
   * Optional, weil die zwei aelteren Griffe es nicht fuehren; wer es setzt,
   * wird darauf geprueft.
   */
  nodeId?: string;
}

/**
 * Das GEHOBENE Bild (Abnahmeliste Zeile 49) — eigene Ablage, nicht dieselbe
 * wie `gerechneteBilder`.
 *
 * WARUM EIGEN UND NICHT EIN DRITTER WERT IN `art`: die Belichtung ersetzt den
 * Farbangleich bzw. die Nachbearbeitung nicht, sie liegt DARUEBER und rechnet
 * auf deren Ergebnis — der Zuruf lautet «DANACH bitte bild noch minimal
 * grundsaetzlich heller als aktuell». Schriebe sie in dieselbe Ablage, waere
 * die Schicht darunter weg und «Belichtung zuruecknehmen» koennte nicht mehr
 * zurueck.
 *
 * WARUM UEBERHAUPT IM STORE (17.09.2026): das Ergebnis lag in einem `useState`
 * des Kurations-Inspektors und ueberlebte darum keinen Neuaufbau der
 * Komponente — die zwei Nachbarn schon. Wer das Bedienfeld schliesst und
 * wieder oeffnet, stand ohne sein Ergebnis da, ohne dass ihm jemand sagte,
 * warum.
 */
export interface GehobenesBild {
  /** Die Karte, zu der dieses Ergebnis gehoert — sonst zeigte es an der naechsten weiter. */
  nodeId: string;
  /** Das Ergebnis als PNG-dataURL. */
  dataUrl: string;
  /** Was gemessen wurde, zeilenweise im Klartext — wie bei `GerechnetesBild`. */
  bericht: string[];
  /** Die Zusage, die die Rechnung aus ihrer Bauart heraus gibt. */
  zusage: string;
  /** Worauf gerechnet wurde — steht in der Kopfzeile des Berichts. */
  grundlage: string;
}

/**
 * Viewport-Aufnahme (v0.6.7 Phase 0) — ein Schnappschuss des 3D-Viewports
 * («Für Vis aufnehmen»-Knopf in Viewport3D.tsx), als dataURL. Wie `laeufe`
 * BEWUSST reine Laufzeit: entities.ts:500-505 hält fest, dass Render-Graph-
 * Bilder nie durch Undo/Yjs/.kosmo gehen — dieselbe Regel gilt für den
 * `aufnahme`-Node. Mehrere Aufnahmen können nebeneinander leben (id = eigener
 * Schlüssel), der `aufnahme`-Node zeigt per Default die jüngste.
 */
export interface Aufnahme {
  id: string;
  dataUrl: string;
  /** Date.now() beim Aufnehmen — bestimmt die «jüngste» Aufnahme. */
  zeit: number;
  /** Dokumentarisch: welcher Standpunkt gemeint war (Node-Param `kamera`). */
  kamera: string;
}

/**
 * v0.8.1 / P8 (0.7.2-Rest «Viz gespeicherte Ansichten + Review-Pins», Spec
 * §6.2, B-92/B-105) — DREI feste Slots (ISO/NORD/DETAIL, wie im Kosmo-Viz-
 * Handoff benannt), jeder verweist auf eine bestehende `Aufnahme` (kein
 * zweites Bild-Format). Reiner LAUFZEIT-Zustand wie `aufnahmen`/`laeufe`
 * selbst — eine gespeicherte Ansicht ist ein Snapshot-Zeiger, kein Doc-Feld.
 *
 * Laufzeit- statt Doc-Entscheid (begründet): eine `Aufnahme` selbst lebt
 * schon bewusst ausserhalb des Doc (`entities.ts:500-505`, «Render-Graph-
 * Bilder gehen nie durch Undo/Yjs/.kosmo»); ein Zeiger AUF eine Laufzeit-
 * Ressource kann nicht plötzlich Doc-/Yjs-fähig sein, ohne die Aufnahme
 * selbst mitzuziehen (Base64 im Sync ist die genau untersagte Eigenschaft).
 * Bleibt ein Slot leer oder verwaist (referenzierte Aufnahme inzwischen
 * weg), zeigt die UI ehrlich «kein Snapshot» statt eines toten Verweises.
 *
 * `version` ist ein reiner Speicher-Zähler (kein Zeitstempel-Vorwand) — der
 * «AUTOSAVE · vNNN»-Badge im Kosmo-Viz-Soll wird damit wörtlich, aber
 * ehrlich: er zählt echte Speicher-Aktionen, keine erfundene Automatik.
 */
export type AnsichtSlotId = 'iso' | 'nord' | 'detail';
export const ANSICHT_SLOTS: readonly AnsichtSlotId[] = ['iso', 'nord', 'detail'];
export const ANSICHT_SLOT_LABEL: Record<AnsichtSlotId, string> = {
  iso: 'ISO',
  nord: 'NORD',
  detail: 'DETAIL',
};

export interface GespeicherteAnsicht {
  aufnahmeId: string;
  /** Fortlaufender Speicher-Zähler dieses Slots, beginnt bei 1. */
  version: number;
  /** Date.now() der letzten Speicherung. */
  zeit: number;
}

/**
 * Review-Kommentar-Pin auf einer `Aufnahme` (Spec §6.2 «Kommentar-Pins auf
 * dem Viewport»). Eine `Aufnahme` ist ein flaches Bild (dataURL, kein
 * navigierbarer 3D-Raum in diesem Modul) — die Pin-Position ist darum
 * ehrlich eine NORMIERTE Bild-Position (0..1 je Achse relativ zur gezeigten
 * Aufnahme), keine echte 3D-Weltkoordinate.
 */
export interface ReviewPin {
  id: string;
  x: number;
  y: number;
  text: string;
  wer: string;
  zeit: number;
}

let pinZaehler = 0;

/** V1-Welle Commit 2 (Kanten-Routing) — Wert-Union, PC1 lebt hier weiter
 *  (bisher nur lokal in `NodeCanvas.tsx` deklariert). */
export type VisRoutingModus = 'ortho' | 'kurve';

/**
 * PC1 (`docs/V084-SPEZ.md` §5 W2, C-15) — der Vis-Island-Katalog braucht
 * Zugriff auf einen Teil des bisher NodeCanvas-lokalen UI-Zustands (Zoom/
 * Snap/Routing/aktiver Graph/Auswahlgrösse/Report/Stimmungs-Preset — die
 * Minimap-Übersteuerung `canvasMinimapManuell` ist mit K35 mitsamt der
 * Minimap entfallen),
 * weil `island/inhalte/*.tsx` (dasselbe Muster wie `design/island/inhalte/
 * *.tsx`) NUR globale Stores lesen dürfen, keine NodeCanvas-Closures. Additiv
 * neben `laeufe`/`kuration`/… — NodeCanvas.tsx liest/schreibt dieselben Felder
 * jetzt STATT lokaler `useState`s (Verhalten byte-gleich, nur die Quelle
 * wechselt); Zoom/Ausrichten bleiben dagegen NodeCanvas-lokal berechnet (sie
 * brauchen die gemessene Canvas-Pixelgrösse/Node-Bounds) — ein «Befehl»-Feld
 * (`canvasBefehl`/`sendeCanvasBefehl`) trägt den AUSLÖSER von aussen (Island-
 * Popup) rein, die eigentliche Rechnung bleibt dort, wo die Geometrie lebt.
 */
export type VisCanvasBefehlTyp =
  | 'zoom-in'
  | 'zoom-out'
  | 'zoom-fit'
  | 'ausrichten-x'
  | 'ausrichten-y'
  | 'vertikal-verteilen';

interface VisRuntime {
  laeufe: Record<string, NodeLauf>;
  kuration: Record<string, KurationEintrag>;
  /** Gerechnete Bilder je Node-Id — s. `GerechnetesBild`. */
  gerechneteBilder: Record<string, GerechnetesBild>;
  /** Gehobene Bilder je Node-Id — s. `GehobenesBild`, liegt UEBER dem obigen. */
  gehobeneBilder: Record<string, GehobenesBild>;
  aufnahmen: Record<string, Aufnahme>;
  gespeicherteAnsichten: Partial<Record<AnsichtSlotId, GespeicherteAnsicht>>;
  /** Review-Pins je `Aufnahme`-Id (aufnahmeId → Liste, jüngste zuletzt). */
  reviewPins: Record<string, readonly ReviewPin[]>;
  /**
   * v0.7.8 Welle 3 (P6, Dock-Migration) — Sichtbarkeit der Node-Palette
   * (`NodeCanvas.tsx`, Knopf `vis-palette-toggle`). Lebte bisher als
   * lokaler `useState` in `NodeCanvas.tsx`; für `DockFlaeche` (das die
   * Palette jetzt als `visPalette`-Dock-Panel rendert) minimal-invasiv
   * hierher gehoben — reiner In-Memory-Zustand wie `kuration`/`laeufe`
   * oben, KEIN neues `localStorage` (bewusst KEINE Persistenz über einen
   * Neustart hinweg, wie das alte `useState` es auch nicht hatte).
   */
  paletteOffen: boolean;
  setzeLauf: (nodeId: string, lauf: NodeLauf) => void;
  patchLauf: (nodeId: string, patch: Partial<NodeLauf>) => void;
  markiereBild: (nodeId: string) => void;
  verwerfeBild: (nodeId: string) => void;
  /** Legt das Rechenergebnis an dieser Karte ab (ersetzt ein vorheriges). */
  setzeGerechnetesBild: (nodeId: string, bild: GerechnetesBild) => void;
  setzeGehobenesBild: (nodeId: string, bild: GehobenesBild) => void;
  verwirfGehobenesBild: (nodeId: string) => void;
  /** Wirft es weg — das Original war nie veraendert, es lag nur darunter. */
  verwirfGerechnetesBild: (nodeId: string) => void;
  fuegeAufnahmeHinzu: (a: Aufnahme) => void;
  paletteUmschalten: () => void;
  paletteSchliessen: () => void;
  /** v0.8.0 (PD2, Dock-Presets) — expliziter Setter statt nur Toggle/Schliessen:
   *  `dock-preset-anwendung.ts` kennt das ZIEL eines Presets (`offen`/`zu`),
   *  nicht den aktuellen Zustand, kann also `paletteUmschalten()` nicht
   *  sicher nutzen (das würde bei bereits passendem Zustand ins Gegenteil
   *  kippen). Additiv, `paletteUmschalten`/`paletteSchliessen` bleiben
   *  unverändert für ihre bestehenden Aufrufer (`NodeCanvas.tsx`). */
  paletteOffenSetzen: (offen: boolean) => void;
  /** Speichert/aktualisiert den Slot — Version zählt hoch (1 beim ersten
   *  Speichern), `zeit` = Date.now(). */
  speichereAnsicht: (slot: AnsichtSlotId, aufnahmeId: string) => void;
  entferneAnsicht: (slot: AnsichtSlotId) => void;
  /** Legt einen neuen Pin an (id/zeit werden hier vergeben) und liefert ihn
   *  zurück — der Aufrufer (UI) braucht die `id` für den Bearbeiten-Zustand. */
  fuegeReviewPinHinzu: (aufnahmeId: string, pin: { x: number; y: number; text: string; wer: string }) => ReviewPin;
  entferneReviewPin: (aufnahmeId: string, pinId: string) => void;

  // ---- PC1 (Island-UI, V084-SPEZ C-15/C-17) — s. Kopfkommentar oben ----
  /** Aktiver Render-Graph (`VisWorkspace.tsx`s bisheriges lokales `aktiverGraph`,
   *  hier gespiegelt) — GRAPH-Island-Inhalte (Node-Palette/Stimmung/Austausch)
   *  lesen ihn, ohne einen Prop-Pfad durch die Insel-Registry zu brauchen. */
  aktiverGraphId: string | null;
  setAktiverGraphId: (id: string | null) => void;
  /** V1-Welle Commit 1 — Default AN, wie das bisherige NodeCanvas-lokale `useState`. */
  canvasSnapAktiv: boolean;
  toggleCanvasSnap: () => void;
  /** V1-Welle Commit 2 — Default 'kurve', wie das bisherige NodeCanvas-lokale `useState`. */
  canvasRoutingModus: VisRoutingModus;
  toggleCanvasRouting: () => void;
  /** Anzahl ausgewählter Nodes (NICHT die volle Auswahl-Menge — die bleibt
   *  NodeCanvas-lokal, hier nur der für die Ausrichten-Insel nötige Zähler). */
  canvasAuswahlGroesse: number;
  setCanvasAuswahlGroesse: (n: number) => void;
  /** W3-a (`docs/ENTSCHEID-KNOTENPLATZ-2026-08-26.md` Weg c) — der aktuelle
   *  Sicht-Mittelpunkt (`view.cx/cy` aus `NodeCanvas.tsx`), hier gespiegelt
   *  nach demselben Muster wie `canvasAuswahlGroesse` oben. Ersetzt den bis
   *  dahin FESTEN Welt-Anker (`START_X=100, START_Y=60`) der Spiral-Platz-
   *  suche in `vis-graph-aktionen.ts` durch einen VIEW-relativen: die
   *  SVG-viewBox bildet `(view.cx, view.cy)` immer exakt auf die Bildschirm-
   *  mitte ab (Zeile 862ff.), eine an einer Fensterecke fest verankerte
   *  Insel (`.isl-rand-sonne`) kann diese Mitte strukturell nicht erreichen.
   *  `null`, solange `NodeCanvas.tsx` (noch) nicht gemountet hat — Aufrufer
   *  fallen dann auf den bisherigen `view`-Default `{x:560,y:300}` zurück. */
  canvasSichtMitte: { x: number; y: number } | null;
  setCanvasSichtMitte: (p: { x: number; y: number }) => void;
  /** B69 (`docs/UI-UX-2026-09-07-B69-ENTSCHEID-HINWEIS.md` §3.2) — dasselbe
   *  Muster wie `canvasSichtMitte` direkt darüber, nur das ganze sichtbare
   *  Weltrechteck statt nur seiner Mitte: `canvasSichtMitte` allein reicht
   *  `nodeHinzufuegen()` nicht, um zu entscheiden, ob ein per Spiral-Suche
   *  gefundener Platz WIRKLICH im Bild liegt — dafür braucht es auch Breite/
   *  Höhe des Ausschnitts, und die hängen vom Zoom (`view.scale`) ab, den
   *  `canvasSichtMitte` nicht trägt. `x`/`y` = linke obere Ecke in Welt-
   *  Koordinaten, `b`/`h` = Breite/Höhe (bei `view.scale=1` `flaeche.w/h`
   *  identisch, sonst durch `view.scale` geteilt — `NodeCanvas.tsx`s
   *  viewBox-Formel, Zeile ~1011ff., hier nur gespiegelt). `null`, solange
   *  `NodeCanvas.tsx` (noch) nicht gemountet hat — derselbe Fall wie bei
   *  `canvasSichtMitte`; Aufrufer, die diesen Fall antreffen, lassen die
   *  Ausserhalb-Prüfung dann aus (kein falscher Hinweis aus einer geratenen
   *  Fenstergrösse). */
  canvasSichtRechteck: { x: number; y: number; b: number; h: number } | null;
  setCanvasSichtRechteck: (r: { x: number; y: number; b: number; h: number }) => void;
  /** Fernauslöser für Zoom/Ausrichten aus einem Island-Popup — NodeCanvas.tsx
   *  beobachtet dieses Feld (Nonce erzwingt IMMER einen neuen Effekt-Lauf,
   *  auch bei zweimal demselben Typ hintereinander) und führt die eigentliche
   *  Rechnung lokal aus (braucht `flaeche`/Node-Bounds). */
  canvasBefehl: { typ: VisCanvasBefehlTyp; nonce: number } | null;
  sendeCanvasBefehl: (typ: VisCanvasBefehlTyp) => void;
  /** AUSTAUSCH-Insel «Report» — ersetzt `VisWorkspace.tsx`s bisheriges lokales
   *  `reportOffen`, damit die Insel denselben Schalter lesen/setzen kann. */
  reportOffen: boolean;
  setReportOffen: (v: boolean) => void;
  /**
   * STIMMUNG-Insel (C-17): der zuletzt gewählte Stimmungs-Preset — fliesst als
   * `render.environment.preset` in JEDEN nächsten Render-Job (Graph-Ausführen
   * UND die Einfach-Ansicht, `vis-jobs.ts`/`VisWorkspace.tsx`). `null` = keine
   * Auswahl getroffen → kein `environment`-Feld im Job (byte-gleich zum
   * bisherigen Verhalten, wie bisher IMMER ausserhalb des Island-Modus).
   */
  renderStimmungPreset: 'morgen' | 'abend' | 'weiss' | null;
  setRenderStimmungPreset: (p: 'morgen' | 'abend' | 'weiss' | null) => void;
}

export const useVisRuntime = create<VisRuntime>((set) => ({
  laeufe: {},
  kuration: {},
  gerechneteBilder: {},
  gehobeneBilder: {},
  aufnahmen: {},
  gespeicherteAnsichten: {},
  reviewPins: {},
  paletteOffen: false,
  setzeLauf: (nodeId, lauf) => set((s) => ({ laeufe: { ...s.laeufe, [nodeId]: lauf } })),
  patchLauf: (nodeId, patch) =>
    set((s) => {
      const alt = s.laeufe[nodeId];
      if (!alt) return s;
      return { laeufe: { ...s.laeufe, [nodeId]: { ...alt, ...patch } } };
    }),
  markiereBild: (nodeId) =>
    set((s) => {
      const alt = s.kuration[nodeId] ?? { markiert: false, verworfen: false };
      return { kuration: { ...s.kuration, [nodeId]: { ...alt, markiert: !alt.markiert } } };
    }),
  verwerfeBild: (nodeId) =>
    set((s) => {
      const alt = s.kuration[nodeId] ?? { markiert: false, verworfen: false };
      return { kuration: { ...s.kuration, [nodeId]: { ...alt, verworfen: !alt.verworfen } } };
    }),
  setzeGerechnetesBild: (nodeId, bild) =>
    set((s) => ({ gerechneteBilder: { ...s.gerechneteBilder, [nodeId]: bild } })),
  verwirfGerechnetesBild: (nodeId) =>
    set((s) => {
      const rest = { ...s.gerechneteBilder };
      delete rest[nodeId];
      // Die Schicht DARUEBER faellt mit: ihr Bericht gehoerte zu einer
      // Grundlage, die es nicht mehr gibt. Ein Bild mit fremdem Bericht ist
      // schlechter als kein Bild.
      const restGehoben = { ...s.gehobeneBilder };
      delete restGehoben[nodeId];
      return { gerechneteBilder: rest, gehobeneBilder: restGehoben };
    }),
  setzeGehobenesBild: (nodeId, bild) =>
    set((s) => ({ gehobeneBilder: { ...s.gehobeneBilder, [nodeId]: bild } })),
  verwirfGehobenesBild: (nodeId) =>
    set((s) => {
      const rest = { ...s.gehobeneBilder };
      delete rest[nodeId];
      return { gehobeneBilder: rest };
    }),
  fuegeAufnahmeHinzu: (a) => set((s) => ({ aufnahmen: { ...s.aufnahmen, [a.id]: a } })),
  speichereAnsicht: (slot, aufnahmeId) =>
    set((s) => {
      const bisher = s.gespeicherteAnsichten[slot];
      return {
        gespeicherteAnsichten: {
          ...s.gespeicherteAnsichten,
          [slot]: { aufnahmeId, version: (bisher?.version ?? 0) + 1, zeit: Date.now() },
        },
      };
    }),
  entferneAnsicht: (slot) =>
    set((s) => {
      const rest = { ...s.gespeicherteAnsichten };
      delete rest[slot];
      return { gespeicherteAnsichten: rest };
    }),
  fuegeReviewPinHinzu: (aufnahmeId, pin) => {
    pinZaehler += 1;
    const neuerPin: ReviewPin = { id: `pin-${pinZaehler}`, zeit: Date.now(), ...pin };
    set((s) => ({
      reviewPins: { ...s.reviewPins, [aufnahmeId]: [...(s.reviewPins[aufnahmeId] ?? []), neuerPin] },
    }));
    return neuerPin;
  },
  entferneReviewPin: (aufnahmeId, pinId) =>
    set((s) => {
      const bisher = s.reviewPins[aufnahmeId];
      if (!bisher) return s;
      return { reviewPins: { ...s.reviewPins, [aufnahmeId]: bisher.filter((p) => p.id !== pinId) } };
    }),
  paletteUmschalten: () => set((s) => ({ paletteOffen: !s.paletteOffen })),
  paletteSchliessen: () => set({ paletteOffen: false }),
  paletteOffenSetzen: (offen) => set({ paletteOffen: offen }),

  // ---- PC1 (Island-UI) ----
  aktiverGraphId: null,
  setAktiverGraphId: (id) => set({ aktiverGraphId: id }),
  canvasSnapAktiv: true,
  toggleCanvasSnap: () => set((s) => ({ canvasSnapAktiv: !s.canvasSnapAktiv })),
  canvasRoutingModus: 'kurve',
  toggleCanvasRouting: () =>
    set((s) => ({ canvasRoutingModus: s.canvasRoutingModus === 'ortho' ? 'kurve' : 'ortho' })),
  canvasAuswahlGroesse: 0,
  setCanvasAuswahlGroesse: (n) => set({ canvasAuswahlGroesse: n }),
  canvasSichtMitte: null,
  setCanvasSichtMitte: (p) => set({ canvasSichtMitte: p }),
  canvasSichtRechteck: null,
  setCanvasSichtRechteck: (r) => set({ canvasSichtRechteck: r }),
  canvasBefehl: null,
  sendeCanvasBefehl: (typ) => set((s) => ({ canvasBefehl: { typ, nonce: (s.canvasBefehl?.nonce ?? 0) + 1 } })),
  reportOffen: false,
  setReportOffen: (v) => set({ reportOffen: v }),
  renderStimmungPreset: null,
  setRenderStimmungPreset: (p) => set({ renderStimmungPreset: p }),
}));

/**
 * Wählt die zu einem `aufnahme`-Node-Param passende Aufnahme: ein Treffer
 * nach `kamera` gewinnt, sonst (oder bei 'aktuell'/ohne Param) die jüngste
 * insgesamt. `null` ohne jede Aufnahme — ehrlich, kein Platzhalterbild.
 */
export function waehleAufnahme(aufnahmen: Record<string, Aufnahme>, kamera?: string): Aufnahme | null {
  const alle = Object.values(aufnahmen).sort((a, b) => b.zeit - a.zeit);
  if (alle.length === 0) return null;
  if (kamera && kamera !== 'aktuell') {
    const treffer = alle.find((a) => a.kamera === kamera);
    if (treffer) return treffer;
  }
  return alle[0]!;
}

/**
 * P-BUEHNE (14.08.2026) — Extraktion der bisher in `VisWorkspace.tsx` inline
 * liegenden Auswahl-Formel («welchen Graphen zeigt die Bühne gerade?»),
 * mechanisch UNVERÄNDERT (byte-gleiches Verhalten): `aktiverGraphId` gewinnt,
 * wenn er auf einen NOCH bestehenden Graphen zeigt (ein gelöschter/undo'ter
 * Graph darf keinen toten Verweis hinterlassen); sonst fällt die Bühne auf
 * den ERSTEN Graphen des Docs zurück (Map-Einfügereihenfolge, `doc.byKind`),
 * NIE auf `null` bei mindestens einem vorhandenen Graphen — eine leere
 * Bühne trotz vorhandenem Graph wäre die stille Lüge, die dieser ganze
 * Auftrag beheben soll.
 *
 * Eigener, testbarer Ort statt Inline-Ternary in der Komponente: der
 * Pflichttest («nach dem Anwenden zeigt die Bühne diesen Graphen»,
 * `test/kosmo-vis-graph-buehne.test.tsx`) prüft GENAU diese Formel gegen den
 * echten `applyCard`/`applyPaket`-Weg, ohne `VisWorkspace.tsx` isoliert
 * mounten zu müssen (dafür gibt es in diesem Repo bewusst keinen
 * Präzedenzfall, s. `pc2-vis-render-executor.test.ts`-Kopfkommentar — die
 * volle Komponente bleibt E2E-Gebiet).
 */
export function waehleGezeigtenGraphen(graphen: readonly { id: string }[], aktiverGraphId: string | null): string {
  if (aktiverGraphId && graphen.some((g) => g.id === aktiverGraphId)) return aktiverGraphId;
  return graphen[0]?.id ?? '';
}

/** Memo-Schlüssel eines Render-Auftrags — billig und deterministisch.
 * `nurCycles` MUSS mit rein (HS5): sonst zeigt der Node nach dem Umschalten
 * fälschlich «aktuell», obwohl ein anderer Job bestellt würde. `presetId`
 * (K20/A10) genauso: ein Preset-Wechsel ändert Samples/Auflösung/Sonne, ohne
 * das im Schlüssel würde der Node fälschlich «aktuell» bleiben. */
export function memoKey(a: {
  prompt: string;
  faithful: number;
  samples: number;
  nurCycles?: boolean;
  presetId?: string;
}): string {
  return `${a.faithful}|${a.samples}|${a.nurCycles ? 'cycles' : 'ki'}|${a.presetId ?? 'kein-preset'}|${a.prompt}`;
}

/**
 * Test-Hook (Playwright) — Muster `window.__kosmoCompanion`/`window.
 * __kosmoAbspiel`: rein lesend/schreibend, ruft NUR bestehende Store-
 * Funktionen auf. v0.8.1 / P8 (0.7.2-Rest «Viz gespeicherte Ansichten»):
 * `e2e/vis-ansichten.spec.ts` seedet darüber eine `Aufnahme`, ohne den
 * echten 3D-Viewport-Aufnahme-Knopf (`Viewport3D.tsx`, anderes Paket)
 * durchklicken zu müssen.
 */
if (typeof window !== 'undefined') {
  (window as never as Record<string, unknown>)['__kosmoVisRuntime'] = {
    fuegeAufnahmeHinzu: (a: Aufnahme) => useVisRuntime.getState().fuegeAufnahmeHinzu(a),
  };
}
