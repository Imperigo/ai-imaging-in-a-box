import { create } from 'zustand';
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
      const kollision = geschossIndexKollision(get().doc, commandId, params);
      if (kollision) throw new CommandError(kollision, commandId);
      const result = execute(get().doc, commandId, params, opts);
      if (!opts?.dryRun) {
        get().history.record(result.patches);
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

/** Startprojekt: EG + Standardaufbauten, damit sofort gezeichnet werden kann. */
export function bootstrapProject(): void {
  const { doc, runCommand } = useProject.getState();
  // P-GESCHOSS: Riegel zuerst, VOR jeder Doc-Lesung — s. Kommentar an
  // `bootstrappteDocs` oben. Ein zweiter Aufruf für DASSELBE Doc endet
  // hier, egal von wo (Effekt, Renderaufruf, StrictMode-Doppelinvoke).
  if (bootstrappteDocs.has(doc)) return;
  bootstrappteDocs.add(doc);
  if (doc.byKind('storey').length > 0) return;
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
