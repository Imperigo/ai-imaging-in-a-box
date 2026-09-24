/**
 * Governance-Speicher (v0.7.7 Stream B1, erweitert v0.7.8 Welle D/PD2 um den
 * ehrlichen Auto-Ablauf) — persistente localStorage-Allowlist für die
 * GovernanceGate-Stufe «Für den Job erlauben»
 * (`shell/GovernanceGate.tsx`, Props `onFuerJob`/`fuerJobAktiv`). Reiner
 * Laufzeit-/Einstellungs-Speicher, dasselbe Muster wie die bestehenden
 * `kosmo.*`-Keys (`kosmo.panelOffen` in `App.tsx`, `kosmo.eigencursor` in
 * `state/cursor-zustand.ts`) — läuft NIE durch Yjs/Undo, betrifft nie das
 * Doc. `shell/GovernanceGate.tsx` selbst bleibt eingefroren; die Persistenz
 * gehört bewusst in die beiden Aufrufer (`KosmoPanel.tsx`/`Companion.tsx`),
 * die hier lesen/schreiben.
 *
 * Zwei Aufrufer, zwei «Arten» von Job-Identität:
 *  - `'command'` — `KosmoPanel.tsx`: Schlüssel ist `commandId` eines echten
 *    Kosmo-Vorschlags (`proposal-card`), Auto-Anwenden über denselben
 *    `applyCard`-Weg wie «Einmal erlauben».
 *  - `'vis'`     — `Companion.tsx`: Schlüssel ist `nodeId` eines Vis-Render-
 *    Knotens (`companion-job-*`), Auto-Freigeben über denselben
 *    `freigebenJob`-Weg wie «Einmal erlauben».
 *
 * EHRLICHKEIT — wann eine Erlaubnis endet: weder ein Kosmo-`commandId` noch
 * ein Vis-`nodeId` ist im bestehenden Code ein EINZELVORGANG mit einem
 * einzigen, unzweideutigen Ende. Ein `commandId` ist ein wiederkehrender
 * Command-TYP, kein Einzelvorgang; ein `nodeId` bekommt laut
 * `Companion.tsx`-Kopfkommentar ausdrücklich «mehrere Render-Läufe
 * nacheinander» — genau DAS ist der Sinn von «für den Job erlauben»: für ALLE
 * künftigen Läufe/Vorschläge dieser Identität, nicht nur den gerade offenen.
 * Diese Datei erfindet darum KEIN vorgetäuschtes Verfallsdatum (keine TTL,
 * kein Timer) — eine Erlaubnis endet über GENAU ZWEI ehrliche Wege, je
 * nachdem, ob ein reales Terminal-Ereignis existiert:
 *
 *  - EXPLIZIT (beide Arten, IMMER verfügbar) — einzeln über
 *    `widerrufeFuerJob`, der bestehende «… · widerrufen»-Knopf im Gate
 *    (`fuerJobAktiv`/`onFuerJob`) bleibt dafür in beiden Aufrufern IMMER
 *    erreichbar, auch wenn ein Auto-Pfad gerade läuft; gesammelt über
 *    `alleWiderrufen`.
 *  - AUTOMATISCH, aber nur wo ein reales Ereignis existiert (v0.7.8 Welle D
 *    / PD2, ROADMAP 345 vertagt):
 *    · `'vis'` — `vis-runtime.ts` kennt pro `nodeId` einen `NodeLauf` mit
 *      echtem `NodeLaufStatus`; die vier Terminalstatus (`fertig`, `fehler`,
 *      `abgebrochen`, `zeitueberschreitung`, s. `OFFENE_LAUF_STATUS`
 *      Gegenteil) SIND ein zuverlässiges «Lauf fertig»-Ereignis — nicht
 *      vorgetäuscht, sondern von der Bridge/dem Timeout-Wächter geliefert.
 *      `Companion.tsx` widerruft darum automatisch, SOBALD ein Lauf, dessen
 *      `nodeId` auf der Allowlist steht, in einen Terminalstatus ÜBERGEHT
 *      und danach kein weiterer offener Lauf auf demselben Knoten liegt —
 *      via der reinen Entscheidung `pruefeAutoWiderruf` unten (keine
 *      localStorage-Seiteneffekte in der Funktion selbst, der Aufrufer
 *      widerruft bei `true`). Bewusst NUR beim ÜBERGANG, nie rückwirkend
 *      beim Mount mit bereits-terminalen Läufen — sonst würde ein Reload
 *      NACH Lauf-Ende die oben dokumentierte Reload-Überlebensgarantie ad
 *      absurdum führen (ein Nutzer, der die Seite neu lädt, nachdem sein
 *      erlaubter Render längst fertig ist, verlöre die Erlaubnis, obwohl er
 *      nie widerrufen hat — genau das unehrliche Verfallsdatum, das diese
 *      Datei vermeiden soll).
 *    · `'command'` — ein `commandId` hat WEITERHIN kein Äquivalent: er ist
 *      ein Command-TYP, kein Lauf mit Status. Statt das vorzutäuschen, gibt
 *      es einen EXPLIZITEN Sammel-Weg («Auftrag beendet» im `KosmoPanel`,
 *      `alleWiderrufen('command')`) — der Nutzer, nicht ein erratenes
 *      Ereignis, erklärt den Auftrag für beendet.
 *
 * Ein stillschweigendes Verfallsdatum vorzutäuschen wäre unehrlich, wenn es
 * keines gibt — s. auch `GovernanceGate.tsx`-Kopfkommentar («jede der vier
 * Aktionen muss echte Wirkung haben», «Risk-Level nur, wenn real ableitbar»,
 * dieselbe Ehrlichkeits-Leitplanke).
 */

import { OFFENE_LAUF_STATUS, type NodeLaufStatus } from '../modules/vis/vis-runtime';

export type GovernanceArt = 'command' | 'vis';

const SPEICHER_KEY = 'kosmo.governance.fuerJob';

interface GovernanceSpeicherForm {
  command: string[];
  vis: string[];
}

function leererSpeicher(): GovernanceSpeicherForm {
  return { command: [], vis: [] };
}

function istStringArray(x: unknown): x is string[] {
  return Array.isArray(x) && x.every((e) => typeof e === 'string');
}

function ladeSpeicher(): GovernanceSpeicherForm {
  try {
    if (typeof localStorage === 'undefined') return leererSpeicher();
    const raw = localStorage.getItem(SPEICHER_KEY);
    if (!raw) return leererSpeicher();
    const parsed = JSON.parse(raw) as Partial<GovernanceSpeicherForm> | null;
    return {
      command: istStringArray(parsed?.command) ? parsed.command : [],
      vis: istStringArray(parsed?.vis) ? parsed.vis : [],
    };
  } catch {
    // Kaputtes/fremdes JSON in diesem Key — ehrlich leer statt zu werfen
    // (dieselbe defensive Haltung wie `loadSettings()` in `KosmoPanel.tsx`).
    return leererSpeicher();
  }
}

function schreibeSpeicher(speicher: GovernanceSpeicherForm): void {
  try {
    if (typeof localStorage === 'undefined') return;
    localStorage.setItem(SPEICHER_KEY, JSON.stringify(speicher));
  } catch {
    // localStorage kann in seltenen Umgebungen werfen (privates Fenster,
    // Kontingent voll) — die Erlaubnis bleibt dann Laufzeit-only für diese
    // Sitzung (der Aufrufer hält ohnehin einen reaktiven UI-Spiegel), kein
    // harter Fehler für einen reinen Komfort-/Persistenz-Pfad.
  }
}

/** Ist `id` (commandId bei `'command'`, nodeId bei `'vis'`) aktuell «für den
 *  Job erlaubt»? Überlebt einen Reload, endet NIE von selbst — nur über
 *  `widerrufeFuerJob`/`alleWiderrufen` (s. Kopfkommentar «Ehrlichkeit»). */
export function istFuerJobErlaubt(art: GovernanceArt, id: string): boolean {
  return ladeSpeicher()[art].includes(id);
}

/** Alle aktuell erlaubten IDs einer Art — zum einmaligen Einlesen beim Mount
 *  eines reaktiven UI-Spiegels (s. `KosmoPanel.tsx`s `autoErlaubt`,
 *  `Companion.tsx`s `autoFreigabeNodes`). */
export function alleFuerJobErlaubt(art: GovernanceArt): readonly string[] {
  return ladeSpeicher()[art];
}

/** Trägt `id` in die Allowlist ein — wirkungslos, wenn schon erlaubt. */
export function erlaubeFuerJob(art: GovernanceArt, id: string): void {
  const speicher = ladeSpeicher();
  if (speicher[art].includes(id)) return;
  speicher[art] = [...speicher[art], id];
  schreibeSpeicher(speicher);
}

/** Entfernt `id` aus der Allowlist — der reguläre Weg, wie eine Erlaubnis vor
 *  einem gesammelten `alleWiderrufen()` endet (s. Kopfkommentar). */
export function widerrufeFuerJob(art: GovernanceArt, id: string): void {
  const speicher = ladeSpeicher();
  if (!speicher[art].includes(id)) return;
  speicher[art] = speicher[art].filter((x) => x !== id);
  schreibeSpeicher(speicher);
}

/** Räumt die Allowlist — ohne `art` BEIDE Arten in einem Zug (unverändertes
 *  Verhalten seit v0.7.7); mit `art` NUR diese eine Art (v0.7.8 Welle D/PD2:
 *  der «Auftrag beendet»-Knopf im `KosmoPanel` räumt bewusst nur `'command'`,
 *  eine laufende `'vis'`-Freigabe eines anderen Knotens bleibt unberührt). */
export function alleWiderrufen(art?: GovernanceArt): void {
  if (art === undefined) {
    schreibeSpeicher(leererSpeicher());
    return;
  }
  const speicher = ladeSpeicher();
  speicher[art] = [];
  schreibeSpeicher(speicher);
}

/**
 * Reine Entscheidung (v0.7.8 Welle D/PD2, s. Kopfkommentar «AUTOMATISCH»):
 * soll die `'vis'`-Erlaubnis für einen Knoten JETZT automatisch enden? KEINE
 * localStorage-Seiteneffekte hier — der Aufrufer (`Companion.tsx`) entscheidet
 * anhand des Rückgabewerts, ob er `widerrufeFuerJob('vis', nodeId)` wirklich
 * ausführt, und ist damit auch dafür verantwortlich, diese Funktion NUR beim
 * Übergang in einen Terminalstatus aufzurufen (nicht bei jedem Render, nicht
 * rückwirkend beim Mount).
 *
 * @param warAutoErlaubt   Stand die ID im Moment des Übergangs auf der
 *   `'vis'`-Allowlist? (Von `Companion.tsx` aus seinem reaktiven Spiegel
 *   `autoFreigabeNodes` gelesen — kein eigener `istFuerJobErlaubt`-Aufruf
 *   hier, das hielte die Funktion pur/testbar ohne `localStorage`.)
 * @param neuerStatus      Der NEU erreichte `NodeLaufStatus` dieses Knotens.
 * @param weitereOffeneLaeufe  Anzahl anderer, noch offener Läufe auf
 *   demselben Knoten. Aktuell hält `vis-runtime.ts` genau EINEN `NodeLauf`
 *   pro `nodeId` (kein Nebeneinander mehrerer Läufe im Datenmodell) — dieser
 *   Parameter ist darum heute immer `0`, bleibt aber Teil der Signatur, damit
 *   die Funktion ehrlich bleibt, sollte sich das Datenmodell einmal ändern
 *   (dann NICHT widerrufen, solange noch ein Lauf offen ist).
 */
export function pruefeAutoWiderruf(
  warAutoErlaubt: boolean,
  neuerStatus: NodeLaufStatus,
  weitereOffeneLaeufe = 0,
): boolean {
  if (!warAutoErlaubt) return false;
  if (OFFENE_LAUF_STATUS.includes(neuerStatus)) return false;
  return weitereOffeneLaeufe === 0;
}
