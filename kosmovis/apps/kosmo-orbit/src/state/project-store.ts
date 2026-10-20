import { create } from 'zustand';
import { merkeAgentSkizzen } from './agent-skizzen';
import {
  KosmoDoc,
  History,
  execute,
  isSettingsPatch,
  CommandError,
  type AnyPatch,
  type ExecuteOptions,
  type ExecutionResult,
  type JournalEntry,
  type Patch,
  type Storey,
} from '@kosmo/kernel';
import { melde, meldeFehler } from '@kosmo/ui';
import {
  meldeLokaleAenderung,
  rueckgaengigTraefeNichtDieLetzteSichtbareAenderung,
} from './fremd-aenderung';

/**
 * Projekt-Store — hält den lebenden KosmoDoc AUSSERHALB von React (grosse
 * Entity-Stores re-rendern nicht pro Mutation); React abonniert nur die
 * Revisionsnummer. Der three.js-Viewport hängt per transientem subscribe dran.
 */

export interface ProjectState {
  doc: KosmoDoc;
  history: History;
  journal: JournalEntry[];
  revision: number;
  activeStoreyId: string | null;
  selection: string[];
  /** Block 3 / E4: ID des FreeMesh im Viewport-Editiermodus (Vertex-Handles,
   * Flächen-Extrude) — null/undefined = kein Editiermodus aktiv. Bewusst im
   * Store (nicht lokaler DesignWorkspace-State), weil der Modus vom
   * Inspector (Knopf «Mesh bearbeiten») UND vom Viewport gemeinsam gelesen
   * werden muss, ohne Prop-Bohrung zwischen den Geschwister-Komponenten. */
  meshEditId: string | null;

  runCommand(commandId: string, params: unknown, opts?: ExecuteOptions): ExecutionResult;
  /**
   * B85 (`docs/HOMESTATION-2026-09-01-RUECKGAENGIG-MELDET.md`): liefert
   * jetzt zurück, OB der Schritt lief — `false` heisst «abgelehnt (`@kosmo/
   * kernel` `CommandError`, sichtbar gemeldet über `meldeFehler`) oder
   * nichts zum Rückgängigmachen vorhanden», `true` heisst «gelaufen». Vorher
   * `void`: ein `CommandError` (B83, fremdes Dokument) lief ungebremst bis
   * zum Aufrufer durch — ein Absturz statt eines Satzes.
   */
  undo(): boolean;
  redo(): boolean;
  setActiveStorey(id: string): void;
  select(ids: string[]): void;
  setMeshEditId(id: string | null): void;
}

/**
 * E157 KosmoMaus (lw-kosmo-maus) — Befehls-Wache. Löst eine Agenten-Handlung
 * (synthetischer Klick von Claude oder Kosmo, `state/kosmo-maus.ts`) einen
 * Befehl aus, darf er das Projekt nicht direkt ändern: die Wache legt eine
 * Vorschlagskarte an und liefert das Ergebnis einer Probe (`dryRun`) zurück.
 * `null` heisst «nicht abgefangen» — dann läuft alles wie immer.
 */
let befehlsWache: ((commandId: string, params: unknown, opts?: ExecuteOptions) => ExecutionResult | null) | null = null;
export function setzeBefehlsWache(fn: typeof befehlsWache): void {
  befehlsWache = fn;
}

/**
 * kosmo-maus-3 (08.10.2026, Befund KosmoDraw/Geräteprobe 575 «erfolg:
 * Dachfenster gesetzt», obwohl nichts gesetzt war): hält die Wache einen
 * Befehl an, liefert `runCommand` das Ergebnis einer Probe (`dryRun`) —
 * dieselbe Form wie ein echtes Ergebnis, aber das Projekt ist unverändert und
 * die Kennungen darin gibt es nicht. `istAngehalten(r)` sagt es ausdrücklich;
 * Aufrufer, die danach «erfolg» melden oder Kennungen wählen, fragen hier.
 * Die Wache (`kosmo-maus.ts`) merkt sich ihre Ergebnisse mit `merkeAngehalten`.
 */
const angehalteneErgebnisse = new WeakSet<object>();

/**
 * lw-maus-rad-vollbild (c): wer gerade handelt, über eine lange Ladezeit
 * hinweg. Die Wache erkennt eine Agenten-Handlung nur während `fuehreMausAus`
 * und kurz danach (`NACHLAUF_MS`); das Lesen einer Splat-Wolke dauert länger,
 * der schreibende Schritt kam dann als Handlung des Architekten durch.
 * `halteHandlungFest()` merkt JETZT (beim Auslösen), wer handelt, und
 * `lauf(fn)` lässt `fn` später im Namen genau dieses Handelnden laufen — die
 * Wache hält dann an wie in der Handlung selbst. Ohne Agent (der Architekt
 * bedient) ist `agent` `null` und `lauf` ruft `fn` unverändert.
 * `kosmo-maus.ts` setzt die Umsetzung (`setzeHandlungsFang`), wie die Wache.
 */
export interface FestgehalteneHandlung {
  readonly agent: string | null;
  lauf<T>(fn: () => T): T;
}
const OHNE_AGENT: FestgehalteneHandlung = { agent: null, lauf: (fn) => fn() };
let handlungsFang: (() => FestgehalteneHandlung) | null = null;
export function setzeHandlungsFang(f: typeof handlungsFang): void {
  handlungsFang = f;
}
export function halteHandlungFest(): FestgehalteneHandlung {
  return handlungsFang?.() ?? OHNE_AGENT;
}
export function merkeAngehalten<T extends object>(r: T): T {
  angehalteneErgebnisse.add(r);
  return r;
}
export function istAngehalten(r: unknown): boolean {
  return typeof r === 'object' && r !== null && angehalteneErgebnisse.has(r);
}

// ---------------------------------------------------------------------------
// Sammelweg: mehrere Befehle EINER Handlung werden unter der Wache EINE Karte
// (lw-lesend-wache, Folgeauftrag «Übernahme als EIN Paket», Geräte-Befund
// auf-272: eine IFC-Bestand-Übernahme unter der KosmoMaus zerfiel in 7
// Einzelkarten; die Wände fanden ihren angehaltenen Aufbau nicht, nach dem
// Anwenden gab es 0 Wände).
//
// `alsEinVorschlag(titel, fn)`: würde die Wache gerade anhalten, laufen alle
// `runCommand` in `fn` der Reihe nach auf einer KOPIE des Dokuments — spätere
// Schritte sehen so die Kennungen der früheren (Aufbau → Wand); `sammelDoc()`
// gibt `fn` diese Kopie zum Lesen. Danach legt die Wache EINE Karte an.
// «Anwenden» (`wendePaketAn`) prüft das Paket erst auf einer frischen Kopie
// und wendet es dann atomar als EINE Rückgängig-Gruppe an (Muster:
// `applyPaket` in `KosmoPanel.tsx`, `versucheCoopPaket` in `kosmo-coop.ts`).
// Ohne Wache (der Owner bedient selbst) läuft `fn` unverändert direkt.
// ---------------------------------------------------------------------------

/** Ein gesammelter Schritt: Befehl, Parameter und die Kennungen, die er in der Kopie anlegte. */
export interface PaketSchritt {
  commandId: string;
  params: unknown;
  zusammenfassung: string;
  /** Kennungen neu angelegter Entitäten (Reihenfolge der Patches) — für die Umschreibung beim Anwenden. */
  neuIds: string[];
  patchAnzahl: number;
}
export interface SammelWache {
  /** Würde die Wache einen Befehl JETZT anhalten (Agent handelt, kein Coop, kein Anwenden)? */
  haeltAn(): boolean;
  legePaketAn(titel: string, schritte: PaketSchritt[]): void;
}
let sammelWache: SammelWache | null = null;
export function setzeSammelWache(w: SammelWache | null): void {
  sammelWache = w;
}
let sammlung: { kopie: KosmoDoc; schritte: PaketSchritt[] } | null = null;
const gesammelteErgebnisse = new WeakSet<object>();
/** Lief dieses Ergebnis nur auf der Sammel-Kopie (das Projekt ist noch unverändert, eine Paket-Karte folgt)? */
export function istGesammelt(r: unknown): boolean {
  return typeof r === 'object' && r !== null && gesammelteErgebnisse.has(r);
}
/** Während `alsEinVorschlag` sammelt: die Kopie, auf der die Schritte laufen; sonst `null`. */
export function sammelDoc(): KosmoDoc | null {
  return sammlung?.kopie ?? null;
}

function kopiereDoc(doc: KosmoDoc): KosmoDoc {
  return KosmoDoc.fromJSON(structuredClone(doc.toJSON()));
}

function neueIds(patches: readonly AnyPatch[]): string[] {
  return patches
    .filter((p): p is Patch => !isSettingsPatch(p) && p.before === null && p.after !== null)
    .map((p) => p.id);
}

function ersetzeIds(wert: unknown, map: ReadonlyMap<string, string>): unknown {
  if (map.size === 0) return wert;
  if (typeof wert === 'string') return map.get(wert) ?? wert;
  if (Array.isArray(wert)) return wert.map((w) => ersetzeIds(w, map));
  if (wert && typeof wert === 'object') {
    return Object.fromEntries(Object.entries(wert as Record<string, unknown>).map(([k, v]) => [k, ersetzeIds(v, map)]));
  }
  return wert;
}

export function alsEinVorschlag<T>(titel: string, fn: () => T): T {
  // Verschachtelt oder ohne Wache: unverändert direkt.
  if (sammlung || !sammelWache?.haeltAn()) return fn();
  const s = { kopie: kopiereDoc(useProject.getState().doc), schritte: [] as PaketSchritt[] };
  sammlung = s;
  let wert: T;
  try {
    wert = fn();
  } finally {
    sammlung = null;
  }
  if (s.schritte.some((x) => x.patchAnzahl > 0)) sammelWache.legePaketAn(titel, s.schritte);
  return wert;
}

/**
 * Ein gesammeltes Paket anwenden: zuerst Probe auf einer frischen Kopie
 * (scheitert ein Schritt, wirft es, und am Projekt hat sich nichts geändert),
 * dann echt, als EINE Rückgängig-Gruppe. Die in der Sammel-Kopie vergebenen
 * Kennungen werden auf die echten umgeschrieben, damit spätere Schritte die
 * früheren treffen. Scheitert der echte Lauf doch, wird die Gruppe
 * zurückgenommen.
 */
export function wendePaketAn(schritte: readonly PaketSchritt[], opts: ExecuteOptions = {}): ExecutionResult[] {
  const lauf = (ausf: (commandId: string, params: unknown) => ExecutionResult, erg: ExecutionResult[]) => {
    const map = new Map<string, string>();
    for (const s of schritte) {
      const r = ausf(s.commandId, ersetzeIds(s.params, map));
      neueIds(r.patches).forEach((neu, i) => {
        const alt = s.neuIds[i];
        if (alt !== undefined && alt !== neu) map.set(alt, neu);
      });
      erg.push(r);
    }
  };
  const kopie = kopiereDoc(useProject.getState().doc);
  lauf((id, p) => {
    const kollision = geschossIndexKollision(kopie, id, p);
    if (kollision) throw new CommandError(kollision, id);
    return execute(kopie, id, p, opts);
  }, []);
  const { history } = useProject.getState();
  const ergebnisse: ExecutionResult[] = [];
  history.beginGroup();
  let fertig = false;
  try {
    lauf((id, p) => useProject.getState().runCommand(id, p, opts), ergebnisse);
    fertig = true;
  } finally {
    history.endGroup();
    if (!fertig && ergebnisse.some((r) => r.patches.length > 0)) useProject.getState().undo();
  }
  return ergebnisse;
}

/**
 * E158 Coop-Modus (lw-coop, `state/kosmo-coop.ts`), Owner-Nachentscheid
 * 07.10.2026: «Strg+Z nimmt NUR die eigenen Schritte des Owners zurück.»
 *
 * `ohneVerlauf(fn)`: Befehle, die `fn` über `runCommand` ausführt, laufen wie
 * immer (Dokument, Journal, Sync), landen aber NICHT im Undo-Stapel des
 * Owners — so führt `kosmo-coop.ts` die Schritte von Claude und Kosmo; die
 * nimmt der Owner gezielt im Verlauf zurück.
 *
 * `setzeVerlaufWache(fn)`: vor jedem Strg+Z/Strg+Y fragt der Store die Wache.
 * `sperre` heisst «nicht umkehren» (der eigene Schritt hängt mit einer
 * späteren Agenten-Änderung zusammen, blind umkehren hiesse deren Arbeit
 * überschreiben), `hinweis` ist eine reine Zusatz-Meldung. Ohne Wache, oder
 * wenn sie `null` sagt, läuft alles wie vor dem Coop.
 */
let verlaufAus = 0;
export function ohneVerlauf<T>(fn: () => T): T {
  verlaufAus++;
  try {
    return fn();
  } finally {
    verlaufAus--;
  }
}
export interface VerlaufWacheUrteil {
  sperre?: string;
  hinweis?: string;
}
let verlaufWache: ((richtung: 'undo' | 'redo', history: History) => VerlaufWacheUrteil | null) | null = null;
export function setzeVerlaufWache(fn: typeof verlaufWache): void {
  verlaufWache = fn;
}
/** Fragt die Wache; `false` = gesperrt (gemeldet). */
function verlaufErlaubt(richtung: 'undo' | 'redo', history: History): boolean {
  const urteil = verlaufWache?.(richtung, history) ?? null;
  if (urteil?.sperre) {
    melde(urteil.sperre, { ton: 'info' });
    return false;
  }
  if (urteil?.hinweis) melde(urteil.hinweis, { ton: 'info' });
  return true;
}

/** Sync-Haken: wird nach jeder lokalen Mutation mit den Patches gerufen. */
let patchListener: ((patches: readonly import('@kosmo/kernel').AnyPatch[]) => void) | null = null;
export function setPatchListener(fn: typeof patchListener): void {
  patchListener = fn;
}

/**
 * v0.9.4 P-GE2 (Owner-Befund Ursache 2, zweite Haelfte von 657): neu
 * angelegte Geschosse aus den PATCHES eines Befehlsergebnisses erkennen —
 * NIE per Namenssuche im Doc (H-38, `commands/design.ts`: ein Bestand darf
 * legitim zwei gleichnamige Geschosse auf verschiedenen Traken haben,
 * Geschossnamen sind kein Schluessel). Ein Patch ist eine NEU-Anlage genau
 * dann, wenn `before === null` und `after.kind === 'storey'` gilt (s.
 * `commands/design.ts` `added()`); `design.geschossKopieren` («Geschoss
 * stapeln») kann mehrere solche Patches in EINEM Befehlsergebnis liefern
 * (anzahl > 1) — davon zaehlt der mit dem groessten `index` (das oberste,
 * zuletzt gestapelte Geschoss), nicht einfach das letzte Array-Element,
 * damit die Wahl unabhaengig von der Patch-Reihenfolge bleibt.
 */
function neuestesGeschoss(patches: readonly AnyPatch[]): string | undefined {
  let treffer: { id: string; index: number } | undefined;
  for (const p of patches) {
    if (isSettingsPatch(p)) continue;
    if (p.before === null && p.after !== null && p.after.kind === 'storey') {
      if (!treffer || p.after.index > treffer.index) treffer = { id: p.after.id, index: p.after.index };
    }
  }
  return treffer?.id;
}

/**
 * P-GESCHOSS (Owner-Befund 11.08.2026, «EG · EG · 1.OG · 2.OG» in der
 * Geschossliste): BEWIESENE Ursache ist H-38 (`docs/SIM-BEFUNDE.md`,
 * dokumentiert seit 10.07.2026, Entscheid 0.6.8) — `design.geschossErstellen`
 * prüft NUR den Namen auf Kollision, und selbst das bloss als Warnung im
 * Zusammenfassungstext (Duplikate bleiben im Kernel ausdrücklich erlaubt,
 * weil ein Doppel-NAME legitim sein kann: verschiedene Trakte könnten
 * beide ein «EG» tragen). Der INDEX ist aber KEIN Name — er ist der
 * Schlüssel für Stapelreihenfolge, `storeyTop()` und jede index-basierte
 * Logik (u.a. `ui.geschossSetzen`, GeschossPille); zwei Geschosse mit
 * demselben Index sind kein legitimer Bestand, sondern ein
 * widersprüchlicher Zustand — das Storey-Modell kennt kein Trakt-Feld,
 * das sie unterscheiden könnte (`packages/kosmo-kernel/src/model/
 * entities.ts`, `Storey`).
 *
 * Die naheliegende Wettlauf-Hypothese (zwei Mountstellen,
 * `DesignWorkspace.tsx`/`PublishWorkspace.tsx`, legen beide beim
 * Leerdoc-Start an) erklärt die Beobachtung NICHT: `bootstrapProject()`
 * legt EG UND 1.OG in derselben synchronen, ununterbrochenen Aufrufkette
 * an (kein `await`, kein Yield-Punkt dazwischen) — ein echtes Zweitmal-
 * Durchlaufen müsste darum BEIDE verdoppeln, nie nur eines. Sequenziell
 * ist der zweite Aufruf ausserdem längst durch den bestehenden
 * `doc.byKind('storey').length > 0`-Guard abgefangen (belegt im Test
 * `geschoss-index-invariante.test.ts`: ein blosses zweites `bootstrapProject()`
 * war schon VOR diesem Fix folgenlos). Die einzige Konstruktion, die exakt
 * «EG doppelt, 1.OG nicht» erzeugt, ist ein GEWÖHNLICHER (nicht rasender)
 * zweiter Aufruf von `design.geschossErstellen({name:'EG', index:0, …})`
 * auf einem Doc, das EG/1.OG schon trägt — genau das H-38-Muster, und
 * genau das Muster, in dem Kosmo selbstständig Geschosse anlegt (der Auftrag
 * bestätigt: das ungewollte «2.OG» im selben Befund stammt nachweislich von
 * Kosmo, via `design.geschossKopieren`, dessen Index sich IMMER aus
 * `maxIndex+n` ergibt — hätte Kosmo das vom Owner verlangte «1.OG» anlegen
 * wollen, während `bootstrapProject()` das bereits erledigt hatte, landet
 * genau dieser Automatismus beim nächstfreien Index, nicht beim
 * gewünschten). Wer konkret den zweiten `geschossErstellen`-Ruf mit
 * Index 0 absetzte, ist ohne Sitzungsprotokoll nicht mehr einzeln
 * belegbar — dass der Mechanismus dafür ausreicht und schon einmal exakt
 * dieses Symptombild erzeugt hat («1.OG / EG / EG», H-38-Beobachtung), ist
 * es.
 *
 * Die Reparatur gehört an den EINEN zentralen Schreib-Weg (`runCommand`
 * unten — Kosmo, UI-Knöpfe, Bootstrap, IFC-Übernahme laufen ALLE
 * ausschliesslich hier durch, s. Kommentar dort), NICHT als Aufräumen
 * hinterher: ein Aufrufer, der mit einem bereits vergebenen Index
 * kollidiert, bekommt einen `CommandError` — bevor der Kernel den Patch
 * überhaupt anwendet. Der Kernel selbst bleibt UNVERÄNDERT (ausserhalb des
 * Dateikreises dieses Pakets) — `design.geschossErstellen` warnt bei
 * Direktaufruf weiterhin nur (Kernel-Test `kernel.test.ts` pinnt das H-38-
 * Verhalten unverändert); diese Klammer ist die zusätzliche, strengere
 * Schicht für den echten Anwendungspfad.
 */
function geschossIndexKollision(doc: KosmoDoc, commandId: string, params: unknown): string | undefined {
  if (commandId !== 'design.geschossErstellen') return undefined;
  if (typeof params !== 'object' || params === null || !('index' in params)) return undefined;
  const index = (params as { index: unknown }).index;
  if (typeof index !== 'number') return undefined;
  const kollidiert = doc.byKind<Storey>('storey').some((s) => s.index === index);
  if (!kollidiert) return undefined;
  return `Geschoss-Index ${index} ist bereits vergeben — jeder Index darf nur ein Geschoss tragen.`;
}

/**
 * P-GESCHOSS, zweite Hälfte («auch nicht bei gleichzeitigem Mount»):
 * `bootstrapProject()` darf für EIN UND DASSELBE Doc nie zweimal
 * durchlaufen, unabhängig von Aufrufreihenfolge/-quelle — der bestehende
 * `doc.byKind('storey').length > 0`-Guard weiter unten verlässt sich
 * darauf, dass zwischen Prüfung und Anlage nichts dazwischenfunkt; das
 * stimmt bei rein sequenziellen Aufrufen (bewiesen, s. Kommentar oben),
 * ist aber kein für alle Zeiten garantiertes Verhalten, sondern ein
 * Zufallsprodukt der heutigen synchronen Befehlskette. Ein `WeakSet`,
 * geschlüsselt auf die DOC-INSTANZ (nicht ein globales Bool!), macht die
 * Zusicherung robust UND überlebt `neuesProjekt()`
 * (`state/project-vault.ts`, setzt `doc` zur Laufzeit auf ein frisches
 * `KosmoDoc()`) sowie jeden Test-Reset (`useProject.setState({doc: new
 * KosmoDoc()})`) unfallfrei — ein frisches Doc verdient einen frischen
 * Bootstrap-Versuch, ein WeakSet vergisst alte Docs von selbst.
 */
const bootstrappteDocs = new WeakSet<KosmoDoc>();

export const useProject = create<ProjectState>((set, get) => {
  const doc = new KosmoDoc();
  const history = new History();

  return {
    doc,
    history,
    journal: [],
    revision: 0,
    activeStoreyId: null,
    selection: [],
    meshEditId: null,

    runCommand(commandId, params, opts) {
      // B49-Nachtrag (`docs/AUFTRAG-B49-ZONEN-BEURTEILUNG.md`, Urteil 2):
      // GEPRÜFT UND BEWUSST NICHT HIER ANGESCHLOSSEN, warum der Zonen-Zuruf
      // (`modules/design/zonen-zuruf.ts`, `zeigeZonenZurufFuerErgebnis`)
      // NICHT — auch nicht eng auf `commandId === 'design.zoneErstellen'`
      // gefiltert — an diesen zentralen Weg gehängt wird:
      //
      // 1. DOPPELMELDUNG, nicht Breite, ist das eigentliche Problem. Dieser
      //    `runCommand` ist der EINE Weg, den ALLE Aufrufer nehmen (Kommentar
      //    unten) — auch die vier direkten Aufrufer von `design.zoneErstellen`
      //    in `modules/design/DesignWorkspace.tsx` (Klick-Schluss,
      //    Doppelklick/Enter, IFC-Übernahme), `modules/design/
      //    skizze-uebernehmen.ts` und `modules/design/StandortSuche.tsx`
      //    (Parzellen-Import), die den Zuruf bereits an ihrer eigenen
      //    Aufrufstelle auslösen. Ein Filter auf die Befehls-ID hier würde
      //    JEDEN dieser bereits verdrahteten Fälle ein ZWEITES Mal auslösen
      //    — genau die Verdoppelung, die dieses Paket ausdrücklich verbietet.
      // 2. Selbst ohne die bereits verdrahteten Aufrufer bliebe ein zweiter,
      //    härterer Fund: der Eckgriff-Zug einer BESTEHENDEN Zone
      //    (`DesignWorkspace.tsx`, Griff-Ende bei `e.kind === 'zone'`) ruft
      //    INTERN denselben Befehl `design.zoneErstellen` (Erstellen+Löschen
      //    als Ersatz für einen fehlenden Kontur-Setter) — von HIER aus, nur
      //    an Befehls-ID und Parametern, ist das nicht von einer echten
      //    Neuanlage zu unterscheiden. Ein Filter auf die Befehls-ID hätte
      //    also bei JEDEM Ziehen einer Zonen-Ecke einen Zuruf ausgelöst,
      //    genau der Fall, den das Paket als Fehlurteil benennt.
      //
      // Erreichbar bliebe damit nur EIN echter Rest-Weg: Kosmo legt eine Zone
      // per LLM-Werkzeug an, OHNE dass ein UI-Aufrufer den Zuruf schon
      // gerufen hat (`shell/KosmoPanel.tsx` — `runCommand(card.commandId, ...,
      // { actor: 'kosmo' })` bei der Diff-Karte, dem Autopilot-Schritt und dem
      // Zuruf-Knopf selbst). Dieser Weg bleibt UNGEMESSEN offen: `KosmoPanel.
      // tsx` liegt ausserhalb des Dateikreises dieses Pakets, und ihn HIER
      // korrekt (ohne die zwei Fälle oben erneut auszulösen) zu schliessen,
      // bräuchte ein Signal, das ein Aufrufer „ich melde selbst" setzen kann
      // (z. B. ein `opts`-Flag) — das ist eine Erweiterung der `ExecuteOptions`
      // im Kernel, nicht «eng gefiltert innerhalb dieses Blocks», und damit
      // bewusst nicht in diesem Paket gebaut.
      //
      // P-GESCHOSS: Index-Invariante VOR jeder Kernel-Ausführung — s.
      // Kommentar an `geschossIndexKollision` oben. Greift bei JEDEM
      // Aufrufer (Kosmo, UI, Bootstrap, IFC-Übernahme), weil `runCommand`
      // der einzige Weg ist, den sie alle nehmen.
      // Sammelweg: in `alsEinVorschlag` unter der Wache laufen die Schritte
      // auf der Kopie (das Projekt bleibt unverändert, EINE Karte folgt).
      if (sammlung && !opts?.dryRun) {
        const s = sammlung;
        const kollisionKopie = geschossIndexKollision(s.kopie, commandId, params);
        if (kollisionKopie) throw new CommandError(kollisionKopie, commandId);
        const r = execute(s.kopie, commandId, params, { ...opts, actor: opts?.actor ?? 'kosmo' });
        s.schritte.push({ commandId, params, zusammenfassung: r.summary, neuIds: neueIds(r.patches), patchAnzahl: r.patches.length });
        gesammelteErgebnisse.add(r);
        return r;
      }
      const kollision = geschossIndexKollision(get().doc, commandId, params);
      if (kollision) throw new CommandError(kollision, commandId);
      const abgefangen = opts?.dryRun ? null : befehlsWache?.(commandId, params, opts); // E157 KosmoMaus
      if (abgefangen) return abgefangen;
      const result = execute(get().doc, commandId, params, opts);
      if (!opts?.dryRun) {
        // R37: Skizzen, die ein Agent per Werkzeug anlegt, sind keine iPad-Weisung (`agent-skizzen.ts`).
        if (commandId === 'design.skizzeErstellen' && opts?.actor && opts.actor !== 'benutzer') merkeAgentSkizzen(neueIds(result.patches));
        if (verlaufAus === 0) get().history.record(result.patches); // E158: Agenten-Schritte ausserhalb der Owner-Kette
        // v0.9.4 P-GE2 (Owner-Befund Ursache 2): JEDER Befehl laeuft hier
        // durch — Kosmos Diff-Karte, ein Autopilot-Schritt, ein Handgriff in
        // der Oberflaeche und die IFC-Bestandsuebernahme (alle vier rufen
        // ausschliesslich `runCommand`, s. `shell/KosmoPanel.tsx`,
        // `state/lauf-runtime.ts`, `modules/design/DesignWorkspace.tsx`).
        // Legt DIESER Aufruf ein neues Geschoss an, wird es sofort aktiv —
        // sonst landet die naechste Wand per `contextDefaults`
        // (`shell/KosmoPanel.tsx`) wieder im zuvor aktiven (meist untersten)
        // Geschoss, genau der Owner-Befund («wird nicht im Grundriss
        // angezeigt»). Legt der Aufruf KEIN Geschoss an, bleibt
        // `activeStoreyId` unangetastet — ein vorheriges, ausdrueckliches
        // Umschalten (`ui.geschossSetzen`) wird dadurch nie ueberschrieben.
        const neuesGeschossId = neuestesGeschoss(result.patches);
        set((s) => ({
          revision: s.revision + 1,
          journal: [...s.journal, result.journal].slice(-500),
          ...(neuesGeschossId !== undefined ? { activeStoreyId: neuesGeschossId } : {}),
        }));
        // P1 (v0.9.60, Auflage §3a/E): DIES ist eine lokale Änderung — der
        // Massstab für «Rückgängig trifft die zuletzt sichtbare Änderung»
        // (`fremd-aenderung.ts`).
        meldeLokaleAenderung();
        patchListener?.(result.patches);
      }
      return result;
    },

    undo() {
      // B85: B83 (`commands/core.ts` `pruefeSchrittGehoertZumDokument`)
      // wirft einen `CommandError`, wenn der rückgängig zu machende Schritt
      // zu einem fremden Dokument gehört (Dokument gewechselt, seit der
      // Schritt entstand) — der Schritt ist dabei im Kernel bereits vom
      // Stapel entfernt (core.ts, Kommentar an `History.undo`), hier gibt es
      // nichts nachzuräumen. Sichtbar gemeldet statt ungebremst
      // durchgereicht — derselbe Weg wie `project-io.ts`s Fehlerpfad
      // (`meldeFehler`, `@kosmo/ui`, Hausbrauch: vier Dateien unter
      // `state/` greifen bereits darauf zu). Ein anderer Wurf (nicht
      // `CommandError`, heute nicht bekannt) ist kein erwarteter
      // Ablehnungsfall — der reist weiter wie vorher.
      // P1 (v0.9.60, Auflage §3a/E): «wo nicht offensichtlich ist, was
      // Rückgängig treffen wird, sagt es die Oberfläche.» Zwei Ketten
      // bleiben (Entscheid E) — dieser Aufruf trifft IMMER nur die lokale
      // Kette; ist eine FREMDänderung (Sync, z.B. eine iPad-Zeichnung) neuer
      // als das letzte lokale Tun, wäre sie sonst die zuletzt SICHTBARE
      // Änderung, die der Nutzer irrtümlich erwartet. Reine Zusatz-Meldung —
      // der Undo-Schritt selbst läuft unverändert weiter, egal ob gewarnt
      // wurde.
      if (!verlaufErlaubt('undo', get().history)) return false; // E158 Coop
      const fremdWarnung = get().history.canUndo ? rueckgaengigTraefeNichtDieLetzteSichtbareAenderung() : null;
      if (fremdWarnung) {
        melde(
          `Rückgängig wirkt nur auf DIESES Gerät — die zuletzt sichtbare Änderung (${fremdWarnung}) kam vom ` +
            'gekoppelten Gerät und lässt sich hier nicht zurücknehmen.',
          { ton: 'info' },
        );
      }
      let patches: readonly AnyPatch[] | null;
      try {
        patches = get().history.undo(get().doc);
      } catch (err) {
        if (err instanceof CommandError) {
          meldeFehler(err);
          return false;
        }
        throw err;
      }
      if (!patches) return false;
      meldeLokaleAenderung();
      set((s) => {
        // v0.9.4 P-GE2: macht dieses Undo GENAU das Geschoss weg, auf das
        // `activeStoreyId` zeigt (heute nur moeglich beim Rueckgaengig-
        // machen von `design.geschossErstellen`/`design.geschossKopieren`
        // — der Kernel kennt bislang keinen Loesch-Befehl), bliebe ein
        // Verweis auf ein verschwundenes Geschoss stehen. Fallback nutzt
        // DIESELBE Vorkehrung wie die Anzeige (`GeschossPille.tsx`: „erstes
        // Geschoss, sonst nichts vortaeuschen") statt einer zweiten
        // Heuristik — nur eben im Store selbst, nicht nur beim Rendern.
        const nochDa = s.activeStoreyId !== null && s.doc.get(s.activeStoreyId)?.kind === 'storey';
        const activeStoreyId = nochDa ? s.activeStoreyId : (s.doc.storeysOrdered()[0]?.id ?? null);
        return { revision: s.revision + 1, activeStoreyId };
      });
      patchListener?.(patches);
      return true;
    },

    redo() {
      // B85, dieselbe Regel wie `undo` oben.
      if (!verlaufErlaubt('redo', get().history)) return false; // E158 Coop
      let patches: readonly AnyPatch[] | null;
      try {
        patches = get().history.redo(get().doc);
      } catch (err) {
        if (err instanceof CommandError) {
          meldeFehler(err);
          return false;
        }
        throw err;
      }
      if (!patches) return false;
      meldeLokaleAenderung();
      set((s) => ({ revision: s.revision + 1 }));
      patchListener?.(patches);
      return true;
    },

    setActiveStorey(id) {
      set({ activeStoreyId: id });
    },

    select(ids) {
      set({ selection: ids });
    },

    setMeshEditId(id) {
      set({ meshEditId: id });
    },
  };
});

/**
 * E158 Coop-Modus (lw-coop, `state/kosmo-coop.ts`) — einen fertigen Schritt
 * anwenden, der aus keinem Kernbefehl stammt: «Rückgängig Claude/Kosmo» setzt
 * die Umkehr-Patches der Coop-Änderungen eines Urhebers ein. Derselbe Weg wie
 * nach `execute` in `runCommand`: Dokument, EINE Undo-Stufe (der Architekt
 * kann das Zurücknehmen mit Strg+Z zurücknehmen), Journal, Sync-Haken,
 * Merker «lokale Änderung». Geprüft wird vorher in `kosmo-coop.ts` (nur Teile,
 * die noch so dastehen, wie der Agent sie hinterliess).
 */
export function wendeSchrittAn(patches: readonly AnyPatch[], eintrag: JournalEntry): void {
  if (patches.length === 0) return;
  const { doc, history } = useProject.getState();
  doc.apply(patches);
  history.record([...patches]);
  useProject.setState((s) => {
    const nochDa = s.activeStoreyId !== null && s.doc.get(s.activeStoreyId)?.kind === 'storey';
    return {
      revision: s.revision + 1,
      journal: [...s.journal, eintrag].slice(-500),
      selection: s.selection.filter((id) => s.doc.entities.has(id)),
      activeStoreyId: nochDa ? s.activeStoreyId : (s.doc.storeysOrdered()[0]?.id ?? null),
    };
  });
  meldeLokaleAenderung();
  patchListener?.(patches);
}

/**
 * Ereignis-Mitschnitt (v0.6.8 «Kosmo sieht mit», Commit 2) — bewusst KEIN
 * neuer Store: `journal` oben wird bereits bei JEDEM `runCommand()` gefüttert
 * (der EINE zentrale Schreib-Weg, CLAUDE.md), unabhängig vom Actor (Mensch/
 * Kosmo/…), und als Ring gehalten (`.slice(-500)`). Diese reine Funktion
 * liest nur die letzten `anzahl` Einträge und formatiert sie menschenlesbar —
 * Kosmos `ereignisse_lesen`-Werkzeug (`shell/KosmoPanel.tsx`) nutzt sie, so
 * "sieht" Kosmo auch nicht-visuell, was zuletzt im Projekt geschah.
 */
export function formatiereEreignisse(anzahl = 20): string {
  const letzte = useProject.getState().journal.slice(-anzahl);
  if (letzte.length === 0) return 'Noch keine Aktionen in dieser Sitzung.';
  return letzte
    .map((e) => {
      const aktor = e.actor === 'benutzer' ? 'nutzer' : e.actor;
      const uhrzeit = new Date(e.ts).toLocaleTimeString('de-CH', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
      return `[${uhrzeit}] (${aktor}) ${e.summary}`;
    })
    .join('\n');
}

/**
 * kosmo-maus-2 (Integrator-Freigabe 08.10.2026): läuft gerade die FESTE
 * Grundausstattung eines neuen Projekts (`bootstrapProject`)? Die
 * Befehls-Wache der KosmoMaus (`kosmo-maus.ts`) hält diese vier Befehle dann
 * nicht als Karten an — «Neues Projekt» mit fester Vorlage zählt als ein
 * UI-Schritt. Nur diese Vorlage: keine Parameter von einem Modell.
 */
let grundausstattungLaeuft = false;
export function legtGrundausstattungAn(): boolean {
  return grundausstattungLaeuft;
}

/** Startprojekt: EG + Standardaufbauten, damit sofort gezeichnet werden kann. */
export function bootstrapProject(): void {
  const { doc } = useProject.getState();
  // P-GESCHOSS: Riegel zuerst, VOR jeder Doc-Lesung — s. Kommentar an
  // `bootstrappteDocs` oben. Ein zweiter Aufruf für DASSELBE Doc endet
  // hier, egal von wo (Effekt, Renderaufruf, StrictMode-Doppelinvoke).
  if (bootstrappteDocs.has(doc)) return;
  bootstrappteDocs.add(doc);
  if (doc.byKind('storey').length > 0) return;
  grundausstattungLaeuft = true;
  try {
    legeGrundausstattungAn();
  } finally {
    grundausstattungLaeuft = false;
  }
}

function legeGrundausstattungAn(): void {
  const { runCommand } = useProject.getState();
  const eg = runCommand('design.geschossErstellen', {
    name: 'EG',
    index: 0,
    elevation: 0,
    height: 3000,
  });
  runCommand('design.geschossErstellen', {
    name: '1.OG',
    index: 1,
    elevation: 3000,
    height: 2800,
  });
  runCommand('design.aufbauErstellen', {
    name: 'AW Beton 36',
    target: 'wall',
    layers: [
      { material: 'putz', thickness: 20, function: 'bekleidung' },
      { material: 'daemmung-mw', thickness: 160, function: 'daemmung' },
      { material: 'beton', thickness: 180, function: 'tragend' },
    ],
  });
  runCommand('design.aufbauErstellen', {
    name: 'IW Beton 18',
    target: 'wall',
    layers: [{ material: 'beton', thickness: 180, function: 'tragend' }],
  });
  const storeyId = (eg.patches[0] as { id: string }).id;
  useProject.setState({ activeStoreyId: storeyId });
}
