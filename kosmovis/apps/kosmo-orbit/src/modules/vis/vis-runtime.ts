import { create } from 'zustand';
import type { JobLieferstatus, JobQa } from './vis-jobs';
import type { RenderJob } from '@kosmo/contracts';
import type { LaufModus } from './modus';
import type { LaufAnweisung } from './skizze-quelle';

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
  /**
   * L24 Bildweg Varianten (E246): ALLE Bilder des Ergebnisses in der Reihenfolge des Vertrags
   * (`result.images`, je Kamera eines). Der Render-Knoten zeigt weiter nur `bild` (das erste);
   * das Raster der Varianten (`varianten.ts`) braucht jedes. Fehlt das Feld, war der Lauf noch
   * nicht fertig.
   */
  bilder?: string[];
  /**
   * Entscheid 117a (W-4, Blatt 35): das gerenderte Grundbild (`<kamera>__schoenbild.png` aus `result.ebenen`) zur
   * Kamera von `bild` — der Render-Knoten zeigt es neben dem KI-Bild. Fehlt es (aelterer Lauf, «Grundlage rendern»,
   * Heim-PC ohne Ebene), steht das KI-Bild allein. Im Poll immer ausdruecklich gesetzt, auch als `undefined`.
   */
  grundbild?: string | undefined;
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
  /**
   * kv-lieferstatus-null (KosmoVis L1): `lieferstatus` und
   * `lieferstatus_grund` des Ergebnisses, unveraendert weitergereicht. `null`
   * heisst «nicht festgestellt» und wird als Vorbehalt gezeigt
   * (`lieferVorbehalt`, `varianten-diff.ts`), nie als «geliefert». Fehlt das
   * Feld, war der Lauf noch nicht fertig: dann gibt es nichts zu zeigen.
   */
  lieferstatus?: JobLieferstatus;
  lieferstatusGrund?: string;
  /**
   * P-LIZENZMARKE Schritt 2 (Owner-Entscheid E154 (4), «Anzeigen, nicht
   * sperren»): `engine_license_open`, `engine_used` und `engine_license` des
   * Ergebnisses. Bis hierhin kam die Marke im Vertrag an (ROADMAP 1681) und
   * ging am Poll verloren, weil der Lauf nur Bild, QA und Lieferstatus
   * uebernahm. `true` heisst «Lizenz des gerechneten Modells offen» und wird
   * an Bild und Ablage als Hinweis gezeigt (`lizenzOffenGrund`,
   * `varianten-diff.ts`); `undefined` heisst «nichts gemeldet», kein Hinweis.
   * Explizit `| undefined` wie `wartetGrund`: `patchLauf` mischt, und ein
   * Ergebnis ohne Marke muss eine alte Marke aktiv leeren koennen.
   */
  lizenzOffen?: boolean | undefined;
  engineUsed?: string | undefined;
  engineLicense?: string | undefined;
  fehler?: string;
  /**
   * Runde 29 (Befund HomeStation, Auftrag 281): warum ein sichtbarer Splat
   * NICHT als Umgebung mitging (z.B. Dateipfad unbekannt). Bleibt am Lauf,
   * statt nur als fluechtige Meldung — fehlt das Feld, ging er mit oder es
   * gab keinen.
   */
  umgebungFehlt?: string;
  /** Freigabe-Token aus dem Create-Response — nötig für `/approve`. */
  approvalToken?: string;
  /**
   * Mac-Demolauf 0.3.33 (22.10.2026): warum «Freigeben» an diesem Lauf nichts bewirkt hat — ein
   * Satz am Knoten, solange der Lauf auf Freigabe wartet (`freigebenAmKnoten`, vis-jobs.ts). Bis
   * dahin blieb ein Klick ohne Kennung wortlos, und der Knoten stand weiter auf «wartet auf
   * Freigabe». Explizit `| undefined` wie `wartetGrund`: `patchLauf` mischt.
   */
  freigabeHinweis?: string | undefined;
  /** Wer den Job übernommen hat (z. B. "fake-worker" oder ein echter Worker). */
  worker?: string;
  /** Laufende Etappe des Workers — der Node zeigt Phase + Prozent (HS3-Auflage 5);
   *  R37-Felder (Kamera i/n, Zwischenbild, Restzeit) additiv, s. `RenderJobProgress`. */
  progress?: { phase: string; pct: number; kamera_i?: number | undefined; kamera_n?: number | undefined; vorschau?: string | undefined; rest_s?: number | null | undefined };
  /** R37 (Nr. 76): nach einem Abbruch das letzte fertige Zwischenbild, ausdrücklich unvollständig. */
  teilbild?: string;
  /** Zeitpunkt des Absendens (ms, Date.now) — Basis des Timeout-Wächters. */
  gestartetUm?: number;
  /**
   * Entscheid 68 / E174 (Verlauf am Render-Knoten): der Zeitpunkt (ms,
   * Date.now), an dem der Poll das fertige Ergebnis uebernommen hat. Der
   * Verlauf nennt ihn an jedem Daumenbild; fehlt er (Lauf von vor diesem
   * Feld, oder nie fertig), steht dort `gestartetUm`.
   */
  fertigUm?: number;
  /**
   * Verlauf-Nachgang (HomeStation-Pruefung 08.10.2026): die fortlaufende
   * Nummer dieses Laufs an seinem Knoten — gezaehlt werden die fertigen
   * Laeufe mit Bild, seit der Knoten in dieser Sitzung lebt (`laufZaehler`).
   * Sie bleibt am Lauf, auch wenn er aus der Reihe faellt; vorher zaehlte
   * die Anzeige nur innerhalb der Reihe, und nach dem fuenften Lauf stand
   * «LAUF 4» auf dem Hauptbild.
   */
  laufNummer?: number;
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
  /**
   * Demolauf Mac 22.10.2026 (Visbox 0.3.33): der Zeitpunkt (ms, Date.now), an dem DIESER
   * Client den Lauf zum ersten Mal auf `wartetGpu` sah — gesetzt allein von `patchLauf`
   * beim Wechsel dorthin, nicht beim Senden. `gestartetUm` taugt dafuer nicht: es ist die
   * Sendezeit, und zwischen Senden und Freigabe kann der Mensch beliebig lange stehen.
   * Fehlt das Feld (Lauf ohne beobachteten Wechsel), gilt die Beschriftung wie bisher.
   */
  wartetSeit?: number | undefined;
  /**
   * P11/B6 — ein STÖRUNGS-Hinweis, der den Lauf NICHT beendet. Der Poll in
   * `NodeCanvas.tsx` liess einen HTTP-Fehler der Bridge (z. B. 404/502,
   * `BridgeHttpError`) und einen echten Netzfehler (`TypeError`) bisher
   * bewusst still durchfallen — «ein einmaliger Aussetzer soll den Lauf
   * nicht töten» bleibt richtig (der nächste Poll fasst nach), aber der
   * GRUND war dabei nirgends zu sehen. Dieses Feld trägt ihn, OHNE den
   * `status` anzufassen — derselbe Unterschied wie bei `wartetGrund`: ein
   * Hinweis ist keine Zusicherung, dass der Lauf gescheitert ist.
   *
   * Explizit `| undefined` (wie `wartetGrund`) wegen `exactOptionalPropertyTypes`
   * — ein erfolgreicher Folge-Poll muss das Feld aktiv LEEREN können.
   */
  bridgeHinweis?: string | undefined;
  /** Parameter-Hash beim Absenden — weicht der Graph ab, ist das Bild «veraltet». */
  memoKey: string;
  /**
   * Nr. 85 Paket 2 (Entscheid 98): welcher der zwei Schritte dieser Lauf war — «Grundlage
   * rendern» oder «Variante erzeugen». Fehlt es, kam der Lauf ueber einen anderen Weg (Kosmo,
   * Insel) und ist ein gewoehnlicher Auftrag wie bisher.
   */
  stufe?: 'grundlage' | 'variante';
  /** Der Graph des Knotens — der Poll legt die eingetroffene Grundlage dort ab (`merkeGrundlage`). */
  graphId?: string;
  /**
   * KosmoVis-Entscheid 2 (v0.1.10): das Projekt, in dem der Lauf bestellt wurde (`setzeProjektLeser`,
   * gestempelt in `setzeLauf`). Nur damit unterscheidet der Poll «Graph entfernt» (gleiches Projekt)
   * von «Projekt gerade nicht vorne». Ohne Leser (Visbox) bleibt es leer.
   */
  projekt?: string;
  /** 98b: Stand der Eingaben beim Absenden einer Grundlage (`grundlageStand`, `grundlage.ts`). */
  grundlageStand?: string;
  /**
   * Die Grundlage, auf der dieses Bild steht: beim Senden einer Variante die bestellte, mit dem
   * Ergebnis die gemeldete (`result.grundlage.id`). Verlauf und Bildvergleich zeigen sie.
   * Explizit `| undefined` wie `wartetGrund`: `patchLauf` mischt.
   */
  grundlageId?: string | undefined;
  /** `result.grundlage.wiederverwendet` — wurde Blender uebersprungen? */
  grundlageWiederverwendet?: boolean | undefined;
  /** 98a: der bestellte Startwert (`vis.seed`); je Kamera meldet ihn `qaJeKamera[].seed`. */
  seed?: number;
  /**
   * Entscheide 104/104a: mit welcher Guete das Ergebnis gerechnet ist (`result.guete`); fehlt =
   * voll. Bei `'vorschau'` setzt die Plakette des UI-Workers (`GueteMarke`) den Vermerk an Bild und
   * Verlauf. Explizit `| undefined`: `patchLauf` mischt, eine alte Angabe darf nicht stehen bleiben.
   * Vor dem Ergebnis steht hier die BESTELLTE Guete (beim Absenden fest, `sendeGraphRenderAuftrag`),
   * damit die Anzeige nicht dem Schalter am Knoten folgt, solange der Lauf rechnet.
   */
  guete?: 'vorschau' | 'voll' | undefined;
  /**
   * Bitte UI «Modus-Marke» (21.10.2026, C17 A1): wie das KI-Bild entstand, aus dem ERGEBNIS
   * (`modusAusErgebnis`, `modus.ts`) — `angewandt.modus`, sonst der Satz «KI-BILD OHNE
   * GRUNDLAGENBILD» aus `qa.verdict.hinweise`. `abweichung: null` heisst «nicht gemeldet», nie
   * «wie bestellt». Fehlt = das Ergebnis sagt nichts dazu. Explizit `| undefined`: `patchLauf`
   * mischt, die Angabe eines frueheren Laufs darf nicht stehen bleiben.
   */
  modus?: LaufModus | undefined;
  /**
   * Befund F4 (Visbox-Demolauf 24.10.2026, Punkt d): das BESTELLTE Bildwerkzeug (`vis.backbone`),
   * beim Absenden fest — der Knoten zeigt es statt der Wahl an seinem Waehler, solange dieser Lauf
   * steht. Fehlt = die Vorgabe.
   */
  backbone?: string | undefined;
  /**
   * Befund F4 (Punkt c): welche Anweisung mit dem Bild ging — die Bemerkung der Skizze oder der
   * Prompt. Steht vor der Freigabe am Knoten (`freigabeZeile`).
   */
  anweisung?: LaufAnweisung | undefined;
  /**
   * Visbox-Entscheid 149: ein bewusst FREIES BILD (ohne Grundbild als Start). Vor dem Ergebnis das
   * Bestellte, danach, was das Ergebnis meldet (`freiesBildAusErgebnis`: `freies_bild: true` oder der
   * Satz «FREIES BILD»). Die Marke «freies Bild» (`FreiesBildMarke`) liest es. Explizit `| undefined`:
   * `patchLauf` mischt, die Angabe eines frueheren Laufs darf nicht stehen bleiben.
   */
  freiesBild?: boolean | undefined;
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
 * Demolauf Mac 22.10.2026 (Visbox 0.3.33, Grundbild vis-1792661785-1762e0): direkt nach der
 * Freigabe stand am Render-Knoten «wartet — nicht abgeholt (Grund unbekannt)», und Sekunden
 * spaeter holte der Abholer ab. «Nicht abgeholt» war in dem Moment keine Beobachtung, sondern
 * eine Vorhersage: Der Abholer schaut nur im Takt nach — seit 22.10.2026 alle 10 s
 * (`OnUnitInactiveSec=10s` am Heim-PC, gemessen Freigabe → «running» hoechstens 9,5 s; bis
 * dahin 30 s). Eine Meldung, dass niemand abholt, ist erst ehrlich, wenn er mehrere Takte lang
 * haette abholen koennen. Bis dahin heisst es: es wartet auf den Heim-PC.
 */
export const ABHOLER_TAKT_MS = 10_000;
/** Drei Takte Geduld: so lange gilt «noch nicht abgeholt» als gewoehnliches Warten. */
export const ABHOLER_GEDULD_MS = 3 * ABHOLER_TAKT_MS;
/** Die Beschriftung innerhalb der Geduld — sagt nur, was sicher ist: es wartet. */
export const WARTET_HEIMPC_LABEL = 'wartet auf den Heim-PC …';
/** Grossbuchstaben-Kurzform derselben Aussage fuer die Companion-Karte. */
export const WARTET_HEIMPC_KURZ = 'WARTET AUF HEIM-PC …';

/** Steht der Lauf noch innerhalb der Geduld? `wartetSeit` fehlt → nein (bisherige Anzeige). */
export function wartetNochImTakt(wartetSeit: number | undefined, jetzt: number): boolean {
  return wartetSeit !== undefined && jetzt - wartetSeit <= ABHOLER_GEDULD_MS;
}

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
export function wartetAbholerLabel(grund: string | undefined, imTakt = false): string {
  if (grund) return 'wartet — abgeholt, zurückgestellt';
  return imTakt ? WARTET_HEIMPC_LABEL : WARTET_ABHOLER_LABEL;
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
export function wartetAbholerKurz(grund: string | undefined, imTakt = false): string {
  if (grund) return WARTET_ABHOLER_KURZ_ZURUECK;
  return imTakt ? WARTET_HEIMPC_KURZ : WARTET_ABHOLER_KURZ;
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
  wartetSeit?: number,
): string {
  const seit = gestartetUm === undefined ? '' : ` seit ${formatDauer(jetzt - gestartetUm)}`;
  if (grund) {
    return `wartet${seit} — abgeholt, zurückgestellt: ${grund}`;
  }
  // Innerhalb der Geduld (s. `ABHOLER_GEDULD_MS`) keine Frage nach dem Abholer: er hatte noch
  // keine drei Takte Zeit.
  if (wartetNochImTakt(wartetSeit, jetzt)) {
    return `${WARTET_HEIMPC_LABEL} Der Abholer schaut alle ${ABHOLER_TAKT_MS / 1000} s nach.`;
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
  /**
   * Entscheid 68 / E174 — der VERLAUF am Render-Knoten: die fertigen Laeufe,
   * die ein neues «Ausfuehren» an diesem Knoten abgeloest hat, neuester
   * zuerst, hoechstens `VERLAUF_BEHALTEN`. Bis hierhin ersetzte `setzeLauf`
   * den Lauf einfach, und das vorige Ergebnis war fuer die Oberflaeche weg.
   *
   * Laufzeit wie `laeufe` (kein Doc, kein Yjs, kein Speicher): ein Eintrag
   * traegt nur Kennung, Bildname und Befund, das Bild selbst liegt weiter
   * im Auftragsspeicher der HomeStation und wird von dort geholt. Fallen
   * Eintraege hinten heraus, vergisst die Oberflaeche nur den Verweis;
   * geloescht wird nirgends etwas.
   */
  verlauf: Record<string, readonly NodeLauf[]>;
  /** Verlauf-Nachgang: wie viele fertige Laeufe mit Bild ein Knoten bisher
   *  hatte — die Quelle von `NodeLauf.laufNummer`. Laufzeit wie `laeufe`. */
  laufZaehler: Record<string, number>;
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

/**
 * Entscheid 68 / E174 — wie viele abgeloeste Laeufe je Knoten im `verlauf`
 * stehen. Der Knoten zeigt hoechstens vier Daumenbilder; vier fruehere plus
 * der aktuelle Lauf reichen, damit die Reihe auch WAEHREND eines neuen Laufs
 * (der noch kein Bild hat) voll bleibt.
 */
export const VERLAUF_BEHALTEN = 4;

/** Ein Lauf, dessen Bild man zeigen kann — dieselbe Bedingung wie
 *  `quelleAusLauf` (`varianten-diff.ts`). */
export function laufMitBild(lauf: Pick<NodeLauf, 'status' | 'jobId' | 'bild'> | undefined): boolean {
  return !!lauf && lauf.status === 'fertig' && !!lauf.jobId && !!lauf.bild;
}

/**
 * Verlauf-Nachgang: vergibt die fortlaufende Nummer, sobald ein Lauf ein
 * fertiges Bild hat. Derselbe Auftrag behaelt seine Nummer; ein Lauf, der
 * schon eine traegt, behaelt sie. Gibt den (evtl. nummerierten) Lauf und den
 * neuen Zaehlerstand zurueck.
 */
function nummeriere(
  zaehler: Record<string, number>,
  nodeId: string,
  lauf: NodeLauf,
  alt: NodeLauf | undefined,
): { lauf: NodeLauf; zaehler: Record<string, number> } {
  if (lauf.laufNummer !== undefined || !laufMitBild(lauf)) return { lauf, zaehler };
  if (alt && alt.jobId === lauf.jobId && alt.laufNummer !== undefined) {
    return { lauf: { ...lauf, laufNummer: alt.laufNummer }, zaehler };
  }
  const nummer = (zaehler[nodeId] ?? 0) + 1;
  return { lauf: { ...lauf, laufNummer: nummer }, zaehler: { ...zaehler, [nodeId]: nummer } };
}

export const useVisRuntime = create<VisRuntime>((set) => ({
  laeufe: {},
  verlauf: {},
  laufZaehler: {},
  kuration: {},
  gerechneteBilder: {},
  gehobeneBilder: {},
  aufnahmen: {},
  gespeicherteAnsichten: {},
  reviewPins: {},
  paletteOffen: false,
  // Entscheid 68 / E174: ein fertiger Lauf, den ein neuer abloest, wandert in
  // den `verlauf` statt zu verschwinden. Derselbe Auftrag (gleiche Kennung)
  // zaehlt nicht als Abloesung.
  setzeLauf: (nodeId, neu0) =>
    set((s) => {
      const alt = s.laeufe[nodeId];
      // KosmoVis-Entscheid 2: ein Lauf an einem Graphen merkt sich sein Projekt (s. `laufZugehoerigkeit`).
      const projekt = neu0.graphId !== undefined && neu0.projekt === undefined ? projektLeser() : undefined;
      const neu = projekt !== undefined ? { ...neu0, projekt } : neu0;
      const { lauf, zaehler } = nummeriere(s.laufZaehler, nodeId, neu, alt);
      const laeufe = { ...s.laeufe, [nodeId]: lauf };
      if (!alt || !laufMitBild(alt) || alt.jobId === lauf.jobId) return { laeufe, laufZaehler: zaehler };
      const frueher = (s.verlauf[nodeId] ?? []).filter((l) => l.jobId !== alt.jobId);
      return {
        laeufe,
        laufZaehler: zaehler,
        verlauf: { ...s.verlauf, [nodeId]: [alt, ...frueher].slice(0, VERLAUF_BEHALTEN) },
      };
    }),
  patchLauf: (nodeId, patch) =>
    set((s) => {
      const alt = s.laeufe[nodeId];
      if (!alt) return s;
      // Verlauf-Nachgang: wird der Lauf hier fertig (der Poll), bekommt er
      // seine Nummer.
      // Demolauf Mac 22.10.2026: wann der Lauf auf `wartetGpu` sprang, haelt der Client selbst
      // fest — die Beschriftung «nicht abgeholt» wartet darauf drei Abholer-Takte.
      const neu = { ...alt, ...patch };
      if (neu.status === 'wartetGpu' && alt.status !== 'wartetGpu' && patch.wartetSeit === undefined) {
        neu.wartetSeit = Date.now();
      } else if (neu.status !== 'wartetGpu' && neu.wartetSeit !== undefined) {
        neu.wartetSeit = undefined;
      }
      const { lauf, zaehler } = nummeriere(s.laufZaehler, nodeId, neu, undefined);
      return { laeufe: { ...s.laeufe, [nodeId]: lauf }, laufZaehler: zaehler };
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

/**
 * Feldmeldung v0.1.8 («Render-Graph «visgraph_…» existiert nicht», frisches Profil): `laeufe`
 * ist Laufzeit und ueberlebt den Projektwechsel. Der Poll im Knoten-Canvas fragte darum auch
 * den Lauf eines ANDEREN Projekts ab — und legte dessen Grundlage (`merkeGrundlage`) mit der
 * fremden Graph-Kennung im jetzigen Dokument ab. Ein Lauf gehoert zum Dokument, wenn sein
 * Graph darin liegt; ohne Kennung (aelterer Auftragsweg) wie bisher ja. Ein fremder Lauf
 * bleibt offen stehen und wird abgefragt, sobald sein Projekt wieder vorne ist.
 */
export function laufGehoertZumDokument(lauf: { graphId?: string | undefined }, hatGraph: (id: string) => boolean): boolean {
  return lauf.graphId === undefined || hatGraph(lauf.graphId);
}

/** Satz am Lauf, dessen Graph geloescht oder per Rueckgaengig entfernt wurde (KosmoVis-Entscheid 2). */
export const GRAPH_ENTFERNT_SATZ = 'Graph entfernt';

let projektLeser: () => string | undefined = () => undefined;
/**
 * Die App sagt hier, welches Projekt vorne ist (`App.tsx`, aus dem Projekt-Tresor). modules/vis kennt
 * den Tresor nicht (Visbox-Kopie); ohne Leser gilt jeder fehlende Graph wie bisher als «fremd».
 */
export function setzeProjektLeser(leser: () => string | undefined): void {
  projektLeser = leser;
}
export function aktuellesProjekt(): string | undefined {
  return projektLeser();
}

/**
 * KosmoVis-Entscheid 2 (v0.1.10): wohin gehoert ein offener Lauf? «hier» — sein Graph liegt im Dokument
 * (oder er hat keinen); «graph-entfernt» — er wurde in DIESEM Projekt bestellt, sein Graph ist aber weg
 * (geloescht, Rueckgaengig); «fremd» — er gehoert zu einem anderen Projekt und ruht, bis es wieder vorne
 * ist (Entscheid 1). Ohne bekanntes Projekt bleibt es bei «fremd»: lieber ruhen als falsch abbrechen.
 */
export function laufZugehoerigkeit(
  lauf: { graphId?: string | undefined; projekt?: string | undefined },
  hatGraph: (id: string) => boolean,
  projektJetzt: string | undefined,
): 'hier' | 'graph-entfernt' | 'fremd' {
  if (laufGehoertZumDokument(lauf, hatGraph)) return 'hier';
  return lauf.projekt !== undefined && lauf.projekt === projektJetzt ? 'graph-entfernt' : 'fremd';
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
