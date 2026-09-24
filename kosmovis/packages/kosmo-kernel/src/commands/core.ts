import { z } from 'zod';
import type { AnyPatch, KosmoDoc } from '../model/doc';
import { invertPatches, isSettingsPatch } from '../model/doc';

/**
 * Command-System — die eine Schreib-Schnittstelle des Kerns.
 *
 * Jeder Command trägt ein zod-Schema. Dasselbe Schema wird dreifach genutzt:
 * UI-Werkzeuge rufen Commands direkt, die Command-Palette listet sie, und
 * kosmo-ai exportiert sie als JSON-Schema-Tools an das LLM. Was Kosmo kann,
 * kann ein Mensch rückgängig machen, inspizieren und nachvollziehen.
 */

/**
 * B22 Hebel 2 (`docs/AUFTRAG-B22-MESSSTAND-II-BEFUNDE.md` §3 Muster 2, §5
 * Punkt 2): mm-Masse werden GERUNDET statt abgewiesen. Ein hartes
 * `z.number().int()` warf einem LLM, das 12000/4.5 = 2666.67 rechnet, den
 * GANZEN Zug um («outline.1.x: Invalid input: expected int, received number»)
 * — gemessen kostete allein das 2 von 10 Punkten. `mmGerundet(ziel)` rundet
 * jede Zahl VOR der eigentlichen Prüfung (`Math.round` via `z.preprocess`);
 * das Ziel-Schema (samt `.int()`, Grenzen, `.default()`, `.describe()`)
 * bleibt die eine Wahrheit — auch im LLM-Tool-JSON-Schema zeigt
 * `z.toJSONSchema(…, { io: 'input' })` bei `z.preprocess` weiterhin das ZIEL
 * inkl. Grenzen, Default und Beschreibung (geprüft gegen zod 4.4.3).
 * Grenzen gelten NACH der Rundung: 699.6 bei `.min(700)` wird zu 700 und
 * läuft — 2.5 bei `.min(700)` bleibt ein ehrlicher Fehler.
 *
 * NUR für mm-/Mass-Felder gedacht. Indizes und Anzahlen (punktIndex, kante,
 * anzahl, teilungN, varianteIndex, maxSpalten, scale, Pixel-Auflösung …)
 * bleiben harte `.int()`: ein «halber Index» ist ein Denkfehler des
 * Aufrufers, kein Rundungsfall.
 */
export function mmGerundet<T extends z.ZodType>(ziel: T) {
  return z.preprocess(
    (wert) => (typeof wert === 'number' && Number.isFinite(wert) ? Math.round(wert) : wert),
    ziel,
  );
}

export interface Command<P = unknown> {
  readonly id: string;
  /** Deutscher Anzeigename fürs UI und die Palette. */
  readonly title: string;
  /** Beschreibung für Menschen UND fürs LLM-Tool-Schema. */
  readonly description: string;
  readonly params: z.ZodType<P>;
  /**
   * Menschlesbare Zusammenfassung einer konkreten Ausführung (Diff-Karte,
   * Journal). `doc` ist additiv (D4, `docs/WETTBEWERB-KONZEPT.md` D-E9):
   * die meisten Commands fassen nur aus `params` zusammen und ignorieren
   * ihn; ein Command, dessen Zusammenfassung berechnete Ergebnisse braucht
   * (z.B. eine Kennzahl, die erst aus dem Doc ableitbar ist), darf ihn
   * lesen. `execute()` ruft `run()` zuerst auf — schlägt die Validierung
   * dort fehl, wird `summarize` gar nicht erreicht, darf sich also auf
   * bereits geprüfte Eingaben verlassen.
   */
  summarize(params: P, doc: KosmoDoc): string;
  /** Pur: liest den Doc, liefert Patches — mutiert nie selbst. */
  run(doc: KosmoDoc, params: P): AnyPatch[];
}

export class CommandError extends Error {
  constructor(
    message: string,
    readonly commandId?: string,
  ) {
    super(message);
    this.name = 'CommandError';
  }
}

export interface JournalEntry {
  ts: string;
  actor: 'benutzer' | 'kosmo' | 'kosmodev' | 'kosmodoc' | 'kosmotrain' | 'system';
  commandId: string;
  params: unknown;
  summary: string;
}

export interface ExecutionResult {
  patches: AnyPatch[];
  summary: string;
  journal: JournalEntry;
}

const registry = new Map<string, Command<never>>();

export function registerCommand<P>(cmd: Command<P>): Command<P> {
  if (registry.has(cmd.id)) throw new Error(`Command doppelt registriert: ${cmd.id}`);
  registry.set(cmd.id, cmd as Command<never>);
  return cmd;
}

export function getCommand(id: string): Command<unknown> | undefined {
  return registry.get(id) as Command<unknown> | undefined;
}

export function allCommands(): Command<unknown>[] {
  return [...registry.values()] as Command<unknown>[];
}

export interface ExecuteOptions {
  actor?: JournalEntry['actor'];
  /** Nur validieren + Patches berechnen, nicht anwenden (Diff-Karten-Vorschau). */
  dryRun?: boolean;
}

export function execute(
  doc: KosmoDoc,
  commandId: string,
  rawParams: unknown,
  opts: ExecuteOptions = {},
): ExecutionResult {
  const cmd = getCommand(commandId);
  if (!cmd) throw new CommandError(`Unbekannter Command: ${commandId}`, commandId);
  const parsed = cmd.params.safeParse(rawParams);
  if (!parsed.success) {
    throw new CommandError(
      `Ungültige Parameter für ${commandId}: ${parsed.error.issues
        .map((i) => `${i.path.join('.') || '(root)'} — ${i.message}`)
        .join('; ')}`,
      commandId,
    );
  }
  const patches = cmd.run(doc, parsed.data);
  if (!opts.dryRun) doc.apply(patches);
  const summary = cmd.summarize(parsed.data, doc);
  return {
    patches,
    summary,
    journal: {
      ts: new Date().toISOString(),
      actor: opts.actor ?? 'benutzer',
      commandId,
      params: parsed.data,
      summary,
    },
  };
}

/**
 * B83 (`docs/AUFTRAG-B83-RUECKGAENGIG-PRUEFT-NICHTS.md`, ROADMAP 1207):
 * Undo/Redo prüften bislang NICHT, ob die Ids eines Schritts überhaupt zu
 * DIESEM Dokument gehören. Der Undo-/Redo-Stapel überlebt einen
 * Dokumentwechsel (Demo laden, Projekt öffnen, Tresor) — `doc.apply()`
 * setzt eine Patch blind ein (`entities.set(p.id, p.after)`), ohne zu
 * fragen, ob die Id hier je existierte. Ein Ctrl+Z nach dem Wechsel
 * schleust damit Bauteile des VORHERIGEN Projekts ein.
 *
 * Entscheid A (statt einer Prüfung in `doc.apply()`, s. Auftragskopf):
 * die Prüfung sitzt auf BEFEHLSEBENE, genau wie der Kopier-Einfüge-Weg
 * (`commands/design.ts:3189`), und prüft den GANZEN Schritt VOR jeder
 * Mutation — atomar, kein halb umgekehrtes Dokument. Geprüft wird jede
 * Patch, die eine Entität SETZT (`p.after !== null` — Erzeugen, Ändern,
 * Wiederherstellen); eine reine Löschung (`p.after === null`) gegen eine
 * fremde Id ist ein wirkungsloses No-Op auf `Map.delete()` und braucht
 * keine Prüfung. `KosmoDoc.warJeTeilDesDokuments()` deckt dabei ALLE drei
 * Patch-Arten in einer einzigen Regel ab: Erzeugen (die Umkehr braucht die
 * Id NICHT vorher, das ist die entgegengesetzte, ungefährliche Richtung),
 * Ändern (die Id muss im aktuellen Dokument je entstanden sein) und
 * Löschen-rückgängig (dieselbe Regel — genau der Fall, der im Befundblatt
 * als «gelöschte Wand kehrt zurück» beschrieben ist).
 *
 * Ein abgewiesener Schritt wird VERWORFEN (vom Stapel entfernt), nicht
 * stillschweigend liegen gelassen: der `CommandError` unten IST die
 * Meldung, bei jedem Aufruf, nie nur beim ersten. Verworfen statt
 * zurückgestellt, weil es keinen sinnvollen Ablageort gibt — und statt die
 * Historie ganz zu leeren, weil ein einzelner Fremd-Schritt sonst JEDEN
 * älteren, echten Schritt darunter für immer unerreichbar machen würde.
 */
function pruefeSchrittGehoertZumDokument(doc: KosmoDoc, schritt: readonly AnyPatch[]): void {
  for (const p of schritt) {
    if (isSettingsPatch(p)) continue;
    if (p.after !== null && !doc.warJeTeilDesDokuments(p.id)) {
      throw new CommandError(
        `Element «${p.id}» gehört nicht zu diesem Dokument — rückgängig/wiederholen abgebrochen, ` +
          `nichts geändert. Vermutlich wurde das Dokument gewechselt (Demo geladen, Projekt geöffnet, ` +
          `Tresor), seit dieser Schritt entstand. Der betroffene Schritt wurde verworfen; frühere ` +
          `Schritte lassen sich weiterhin rückgängig machen.`,
      );
    }
  }
}

/** Undo/Redo über Patch-Inverse; Schritte können mehrere Commands gruppieren. */
export class History {
  private undoStack: AnyPatch[][] = [];
  private redoStack: AnyPatch[][] = [];
  private openGroup: AnyPatch[] | null = null;
  readonly limit = 500;

  beginGroup(): void {
    if (this.openGroup === null) this.openGroup = [];
  }

  endGroup(): void {
    if (this.openGroup && this.openGroup.length > 0) {
      this.undoStack.push(this.openGroup);
      if (this.undoStack.length > this.limit) this.undoStack.shift();
    }
    this.openGroup = null;
  }

  record(patches: AnyPatch[]): void {
    if (patches.length === 0) return;
    this.redoStack = [];
    if (this.openGroup) {
      this.openGroup.push(...patches);
    } else {
      this.undoStack.push(patches);
      if (this.undoStack.length > this.limit) this.undoStack.shift();
    }
  }

  get canUndo(): boolean {
    return this.undoStack.length > 0;
  }

  /** Anzahl rückgängig machbarer Schritte (Diagnose/Anzeige). */
  get depth(): number {
    return this.undoStack.length;
  }

  get canRedo(): boolean {
    return this.redoStack.length > 0;
  }

  undo(doc: KosmoDoc): AnyPatch[] | null {
    const step = this.undoStack.pop();
    if (!step) return null;
    const inverted = invertPatches(step);
    // B83: geprüft (und im Ablehnungsfall geworfen) BEVOR doc.apply()
    // überhaupt läuft — der Schritt ist oben bereits vom Stapel entfernt
    // (verworfen), das Dokument bleibt unangetastet.
    pruefeSchrittGehoertZumDokument(doc, inverted);
    doc.apply(inverted);
    this.redoStack.push(step);
    return inverted;
  }

  redo(doc: KosmoDoc): AnyPatch[] | null {
    const step = this.redoStack.pop();
    if (!step) return null;
    // B83, dieselbe Regel wie oben (`undo`) — s. Kommentar an
    // `pruefeSchrittGehoertZumDokument`.
    pruefeSchrittGehoertZumDokument(doc, step);
    doc.apply(step);
    this.undoStack.push(step);
    return step;
  }
}
