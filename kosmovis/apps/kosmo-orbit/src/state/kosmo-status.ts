import { create } from 'zustand';
import { useLaufRuntime, type LaufRuntimeState } from './lauf-runtime';

/**
 * Kosmo-Status (K11, Owner-Befund «Copilot-Symbol, nicht Dauerchat») —
 * reiner LAUFZEIT-Store: läuft nie durch Yjs/Undo, lebt nur im Prozess
 * (Laufzeit ≠ Modell, siehe CLAUDE.md — Muster wie `modules/vis/vis-runtime.ts`).
 * Treibt das schwebende Kosmo-Symbol (`shell/KosmoSymbol.tsx`) UND den
 * wiederverwendbaren Orb (`shell/KosmoOrb.tsx`), solange das grosse Panel
 * geschlossen ist bzw. wo immer der Orb sonst eingebettet wird.
 *
 * v0.7.2 §6 (Paket 06 — «Kosmo-Zustände»): additiv um eine echte
 * State-Machine erweitert. `beschaeftigt` bleibt als ABGELEITETES Feld
 * bestehen (Rückwärtskompatibilität — jeder bestehende Aufrufer/Selector
 * kompiliert und verhält sich unverändert), gespeist aus `zustand`.
 *
 * P-ST Welle 1 («Der Orb weiss, dass ein Lauf läuft», 29.07.2026) — Faktencheck
 * vor dem Bau bestätigte einen Befund, der im Bericht zu ROADMAP 670 fehlte:
 * `state/lauf-runtime.ts` kannte diesen Store bis hierhin GAR NICHT (kein
 * `useKosmoStatus`-Import dort) — ein laufender Lauf setzte `zustand` nie auf
 * `'dispatching'`, anders als `KosmoPanel.tsx#applyPaket`/`#applyCard`, die das
 * beim Karten-Anwenden ausdrücklich tun (`setzeZustand('dispatching')` vor dem
 * `runCommand`-Aufruf, `setzeZustand('done'|'error')` danach). `lauf-runtime.ts`
 * bleibt für dieses Paket NUR LESEND (dort arbeitet parallel ein anderes
 * Paket) — der Spiegel lebt darum HIER, als reiner Ausseneinklinker über
 * `useLaufRuntime.subscribe` (unten, Modul-Fuss), exakt das Muster, das
 * `shell/kosmo-zustand-bruecke.ts` für die umgekehrte Richtung (Status →
 * Tauri-Event) bereits nutzt: von AUSSEN anhängen, KEINE Änderung an der
 * Quelle. `schritt`/`schritteGesamt` sind reine Spiegelfelder aus
 * `LaufRunner#schritte` (dieselbe Zahl, die auch `KosmoPanel.tsx`s
 * Schrittliste zeigt) — keine zweite Fortschritts-Buchführung.
 */
export type KosmoZustand =
  | 'idle'
  | 'thinking'
  | 'listening'
  | 'speaking'
  | 'writing'
  | 'dispatching'
  | 'done'
  | 'error'
  | 'takeover';

/** `beschaeftigt = !['idle','done','error'].includes(zustand)` — wörtlich Spec §6. */
const NICHT_BESCHAEFTIGT: ReadonlySet<KosmoZustand> = new Set(['idle', 'done', 'error']);

function beschaeftigtAus(z: KosmoZustand): boolean {
  return !NICHT_BESCHAEFTIGT.has(z);
}

/**
 * Zustände, die `setzeBeschaeftigt(false)` NICHT stillschweigend nach
 * 'idle' zurückwirft:
 *  - 'done'/'error' laufen über ihren EIGENEN Decay-Timer aus (unten) — die
 *    ChatSession (`packages/kosmo-ai/src/chat.ts`) ruft nach jedem
 *    Sende-Zyklus IMMER `onBusy(false)`, auch direkt nachdem sie zuvor
 *    `onError(...)` gerufen hat (Reihenfolge: onBusy(true) → … →
 *    [onError] → onBusy(false)). Ohne diese Ausnahme würde das gerade erst
 *    gesetzte 'error' vom unmittelbar folgenden `onBusy(false)` sofort
 *    wieder auf 'idle' gestellt — die 4s-Fehleranzeige (§6 Punkt 7) wäre nie
 *    sichtbar. Dieselbe Überlegung gilt für 'done'.
 *  - 'takeover' ist ein eigenständiger Fensterrahmen-Modus (§6 Punkt 8),
 *    dem Chat-Sende-Lebenszyklus fachlich fremd — die ChatSession kennt ihn
 *    nicht und darf ihn nicht per Kompat-Pfad beenden.
 */
const BEHAELT_BEI_BESCHAEFTIGT_FALSE: ReadonlySet<KosmoZustand> = new Set(['done', 'error', 'takeover']);

/** Auto-Decay (Spec §6): done→idle nach 2s, error→idle nach 4s. */
const DECAY_MS: Partial<Record<KosmoZustand, number>> = { done: 2000, error: 4000 };

/**
 * Was die Karte am Orb von einem laufenden Auftrag zeigt (U1). `name` ist ein
 * kurzer, lesbarer Name («Grundriss zeichnen»), nie der Gedankentext des
 * Modells. `schritt`/`schritteGesamt` nur bei gezaehlten Schritten.
 */
export interface KosmoAuftrag {
  name: string;
  schritt?: number;
  schritteGesamt?: number;
}

function sindGleich(a: KosmoAuftrag, b: KosmoAuftrag): boolean {
  return a.name === b.name && a.schritt === b.schritt && a.schritteGesamt === b.schritteGesamt;
}

/**
 * **Der Stopp-Weg** (C21: «der Orb wird zum Stopp-Knopf, Esc geht auch»). Das
 * Kosmo-Panel haelt die `ChatSession` und den Lauf; es meldet hier eine
 * Funktion an, solange es gemountet ist. Orb, Karte, Fensterkopf und Esc rufen
 * dann EINEN Weg, `stoppeAuftrag()`. Ohne angemeldeten Weg tut der Aufruf
 * nichts und sagt es (`false`) — ein Stopp-Knopf ohne Wirkung waere schlimmer
 * als keiner.
 */
let stoppWeg: (() => void) | null = null;

export function registriereStopp(fn: () => void): () => void {
  stoppWeg = fn;
  return () => {
    if (stoppWeg === fn) stoppWeg = null;
  };
}

/** Bricht den laufenden Auftrag ab. `true`, wenn ein Weg angemeldet war. */
export function stoppeAuftrag(): boolean {
  if (!stoppWeg) return false;
  useKosmoStatus.getState().setzeAbbruchVerlangt(true);
  stoppWeg();
  return true;
}

interface KosmoStatus {
  /** Läuft gerade eine Antwort/ein Tool-Aufruf (Sende-Lebenszyklus)? — abgeleitet aus `zustand`. */
  beschaeftigt: boolean;
  /** Feingranularer Kosmo-Zustand fürs `KosmoOrb` (v0.7.2 §6). */
  zustand: KosmoZustand;
  /** Kurze Zusammenfassung der letzten Antwort/des letzten Vorschlags — oder noch nichts. */
  letzteAktivitaet: string | null;
  /**
   * P-ST Welle 1 (BLATT 04 §05 «LAUF LÄUFT») — NUR aussagekräftig, solange
   * `zustand === 'dispatching'` UND dieser Lauf-Spiegel (Modul-Fuss unten) ihn
   * gerade treibt. Reiner Spiegel aus `useLaufRuntime().schritte`/`.status` —
   * KEINE zweite Fortschritts-Quelle. `undefined`, solange kein Lauf läuft.
   */
  schritt: number | undefined;
  /** Siehe `schritt` — die Gesamtzahl der Schritte des laufenden Laufs. */
  schritteGesamt: number | undefined;
  /**
   * P-ST Welle 1 (BLATT 04 §06 «ETWAS OFFEN») — Spiegel der Zahl offener,
   * angehefteter Vorschlagskarten. Die tatsächliche Berechnung
   * (`offeneKartenSchluessel`) lebt in `shell/KosmoPanel.tsx` (TABU für dieses
   * Paket) — `setzeOffenAnzahl` unten ist die eine benannte Stelle, über die
   * das Panel seinen bereits berechneten Wert HIERHIN spiegelt, statt dass
   * dieser Store eine zweite, eigene Zählung führt. Default 0 (keine offenen
   * Karten bei Programmstart, bevor das Panel je gemountet hat).
   */
  offenAnzahl: number;
  /**
   * **Der laufende Auftrag** (U1/C21, Welle B, 01.10.2026) — nur, solange Kosmo
   * wirklich etwas tut: ein Chat-Zug, der laeuft, oder ein Lauf. `null` heisst
   * «Kosmo wartet auf dich»; nur dann gibt es keine Karte am Orb.
   *
   * Geschrieben wird er ausschliesslich vom Kosmo-Panel (es haelt die
   * `ChatSession` und kennt den Lauf). Der Orb liest ihn und sagt nur, was dort
   * steht — er rechnet nichts selbst. `schritt`/`schritteGesamt` stehen nur bei
   * GEZAEHLTEN Schritten (Owner G6: Fortschritt nur aus echten Schritten);
   * ohne sie heisst die Karte ehrlich «arbeitet».
   */
  auftrag: KosmoAuftrag | null;
  /**
   * Der Abbruch wurde verlangt, hat aber noch nicht gewirkt (Visbox-Regel:
   * «verlangt heisst noch nicht gewirkt»). Der Orb sagt dann «haelt an», nicht
   * «gestoppt» — bis der Auftrag wirklich endet und dieses Flag mit ihm faellt.
   */
  abbruchVerlangt: boolean;
  /**
   * Kurze Antwort fuer die Blase am Orb (C22): nur gesetzt, wenn Kosmo bei
   * geschlossenem Fenster kurz geantwortet hat. Lange Antworten oeffnen das
   * Fenster (Entscheid im Panel, `shell/kosmo-fenster/antwort-blase.ts`).
   */
  antwortBlase: { id: number; text: string } | null;
  /**
   * Pegel der Stimme, 0…1, alle ~50 ms (U2/U2-Anschluss). `undefined` ohne
   * Stimme: Text-Antwort, Browser-Sprachausgabe (die gibt keinen Ton heraus,
   * den man messen koennte) oder nichts gesprochen. Dann bleibt am Orb die
   * feste Animation — es wird kein Pegel erfunden.
   */
  pegel: number | undefined;
  setzeAuftrag: (a: KosmoAuftrag | null) => void;
  setzeAbbruchVerlangt: (v: boolean) => void;
  setzeAntwortBlase: (a: { id: number; text: string } | null) => void;
  setzePegel: (p: number | undefined) => void;
  /** Setzt den feingranularen Zustand — einzige Stelle, die `beschaeftigt` ableitet + den Decay-Timer plant. */
  setzeZustand: (z: KosmoZustand) => void;
  /**
   * Rückwärtskompatibler Kompakt-Setter (Bestand vor v0.7.2): `true` → 'thinking',
   * `false` → 'idle' — AUSSER der aktuelle Zustand ist 'done'/'error'/'takeover'
   * (siehe `BEHAELT_BEI_BESCHAEFTIGT_FALSE` oben). Alle bestehenden Aufrufer
   * (aktuell: `KosmoPanel.tsx` `onBusy`) bleiben ohne Anpassung korrekt.
   */
  setzeBeschaeftigt: (v: boolean) => void;
  setzeLetzteAktivitaet: (text: string) => void;
  /**
   * Spiegel-Setter (s. `offenAnzahl` oben) — von `shell/KosmoPanel.tsx` zu
   * rufen, sobald sich `offeneKartenSchluessel.length` ändert (Sammelpaket,
   * KosmoPanel.tsx ist für DIESES Paket TABU). `n` wird nicht geprüft/geklammert
   * — ein negativer oder gebrochener Aufruf wäre ein Fehler beim Aufrufer,
   * kein Fall, den der Store stillschweigend heilen sollte.
   */
  setzeOffenAnzahl: (n: number) => void;
}

/** Modul-weiter Decay-Timer-Handle — EIN Timer gleichzeitig reicht (ein Store, ein Zustand). */
let decayTimer: ReturnType<typeof setTimeout> | null = null;

export const useKosmoStatus = create<KosmoStatus>((set, get) => ({
  beschaeftigt: false,
  zustand: 'idle',
  letzteAktivitaet: null,
  schritt: undefined,
  schritteGesamt: undefined,
  offenAnzahl: 0,
  auftrag: null,
  abbruchVerlangt: false,
  antwortBlase: null,
  pegel: undefined,
  setzeAuftrag: (a) => set((s) => (a === null ? { auftrag: null, abbruchVerlangt: false } : s.auftrag && sindGleich(s.auftrag, a) ? s : { auftrag: a })),
  setzeAbbruchVerlangt: (v) => set({ abbruchVerlangt: v }),
  setzeAntwortBlase: (a) => set({ antwortBlase: a }),
  setzePegel: (p) => {
    const wert = p === undefined || !Number.isFinite(p) ? undefined : Math.min(1, Math.max(0, p));
    if (get().pegel !== wert) set({ pegel: wert });
  },
  setzeZustand: (z) => {
    if (decayTimer !== null) {
      clearTimeout(decayTimer);
      decayTimer = null;
    }
    set({ zustand: z, beschaeftigt: beschaeftigtAus(z) });
    const decayNachMs = DECAY_MS[z];
    if (decayNachMs !== undefined) {
      decayTimer = setTimeout(() => {
        decayTimer = null;
        get().setzeZustand('idle');
      }, decayNachMs);
    }
  },
  setzeBeschaeftigt: (v) => {
    if (v) {
      get().setzeZustand('thinking');
      return;
    }
    if (!BEHAELT_BEI_BESCHAEFTIGT_FALSE.has(get().zustand)) {
      get().setzeZustand('idle');
    }
  },
  setzeLetzteAktivitaet: (text) => set({ letzteAktivitaet: text }),
  setzeOffenAnzahl: (n) => set({ offenAnzahl: n }),
}));

/**
 * P-ST Welle 1 — der aktuell laufende Schritt (1-indiziert, wie die
 * Ring-Spec `KosmoOrbProps.schritt` verlangt), abgeleitet aus
 * `LaufRunner#schritte` (`lauf-runtime.ts`, NUR gelesen): entweder der
 * Schritt, der GERADE `status:'laeuft'` trägt, oder — falls momentan keiner
 * läuft (z.B. der kurze Moment zwischen zwei Schritten) — einer mehr als die
 * Zahl der bereits `'ok'` abgeschlossenen Schritte. `Math.min(...)` fängt den
 * Rand ab, in dem der letzte Schritt gerade `'ok'` wurde, bevor der
 * Gesamtstatus-Wechsel auf `'fertig'` diesen Store überhaupt erreicht.
 */
function laufSchrittZuOrbSchritt(schritte: LaufRuntimeState['schritte']): number {
  const laufIndex = schritte.findIndex((s) => s.status === 'laeuft');
  if (laufIndex !== -1) return laufIndex + 1;
  const erledigt = schritte.filter((s) => s.status === 'ok').length;
  return Math.min(erledigt + 1, schritte.length);
}

/**
 * Modul-weites Flag: war der AKTUELLE `'dispatching'`/`'done'`/`'error'`-
 * Aufenthalt dieses Stores von DIESEM Spiegel ausgelöst? Verhindert, dass der
 * Lauf-Spiegel einen FREMDEN `dispatching`-Aufenthalt (z.B.
 * `KosmoPanel.tsx#applyCard`/`#applyPaket`, unabhängig von jedem Lauf)
 * beendet, den er nie selbst begonnen hat.
 */
let laufTreibtDispatching = false;

/**
 * P-ST Welle 1 — der eine Ausseneinklinker, der `useLaufRuntime` (NUR
 * gelesen, s. Kopfkommentar oben) auf diesen Store spiegelt. Reagiert auf
 * JEDE Statusänderung des Lauf-Stores:
 *  - `'laeuft'`: `zustand` → `'dispatching'` (idempotent, `setzeZustand`
 *    verträgt Mehrfachaufruf desselben Werts), `schritt`/`schritteGesamt`
 *    live nachgezogen bei jedem Fortschritts-Tick.
 *  - jeder andere Status (`'fertig'|'fehler'|'abgebrochen'|'offen'`):
 *    `schritt`/`schritteGesamt` sofort geräumt (der Orb zeigt sie ohnehin nur
 *    bei `zustand==='dispatching'`); den `zustand` selbst räumt/überführt
 *    NUR, wer ihn selbst gesetzt hat (`laufTreibtDispatching`) UND nur,
 *    solange der Store noch tatsächlich auf `'dispatching'` steht (ein
 *    zwischenzeitlich von aussen gesetzter Fremdzustand — z.B. ein neuer
 *    Chat-Zug — wird NICHT überschrieben). Spiegelbild von
 *    `KosmoPanel.tsx#applyCard`/`applyPaket`: `'fertig'` → `'done'`,
 *    `'fehler'` → `'error'` (beide zerfallen über den bestehenden Decay-Timer
 *    von selbst auf `'idle'` — «nach dem Lauf fällt der Orb zurück»),
 *    `'abgebrochen'`/`'offen'` (z.B. nach `zuruecksetzen()`) → sofort `'idle'`,
 *    ohne erst einen Erfolgs-/Fehler-Anschein vorzutäuschen.
 */
useLaufRuntime.subscribe((state) => {
  if (state.status === 'laeuft') {
    laufTreibtDispatching = true;
    useKosmoStatus.setState({
      schritt: laufSchrittZuOrbSchritt(state.schritte),
      schritteGesamt: state.schritte.length,
    });
    if (useKosmoStatus.getState().zustand !== 'dispatching') {
      useKosmoStatus.getState().setzeZustand('dispatching');
    }
    return;
  }
  useKosmoStatus.setState({ schritt: undefined, schritteGesamt: undefined });
  if (!laufTreibtDispatching) return; // dieser Übergang kam nicht von diesem Spiegel
  laufTreibtDispatching = false;
  if (useKosmoStatus.getState().zustand !== 'dispatching') return; // ein Fremdzustand hat inzwischen übernommen
  if (state.status === 'fertig') useKosmoStatus.getState().setzeZustand('done');
  else if (state.status === 'fehler') useKosmoStatus.getState().setzeZustand('error');
  else useKosmoStatus.getState().setzeZustand('idle'); // 'abgebrochen' oder 'offen' (zuruecksetzen())
});

/**
 * Kürzt eine Kosmo-Antwort auf eine Mini-Popup-taugliche Zusammenfassung
 * (Owner-Vorgabe: «erste ~80 Zeichen der Antwort»). Zeilenumbrüche werden
 * geglättet, damit das Popup nie mehrzeilig aus dem Ruder läuft.
 */
export function kurzform(text: string, maxLaenge = 80): string {
  const einzeilig = text.replace(/\s+/g, ' ').trim();
  if (einzeilig.length <= maxLaenge) return einzeilig;
  return `${einzeilig.slice(0, maxLaenge).trimEnd()}…`;
}

/**
 * Test-Hook (Playwright) — Muster wie `window.__kosmoBlick`/`window.__kosmoChat`
 * (`shell/KosmoPanel.tsx`): rein lesend/schreibend, sonst nirgends im DOM
 * sichtbar. `e2e/kosmo-zustaende.spec.ts` treibt darüber gezielt einzelne
 * `KosmoZustand`-Werte, unabhängig davon, ob gerade das Symbol oder das Panel
 * gemountet ist — der Store selbst existiert immer (Modul-Singleton).
 */
if (typeof window !== 'undefined') {
  (window as never as Record<string, unknown>)['__kosmoStatus'] = {
    setzeZustand: (z: KosmoZustand) => useKosmoStatus.getState().setzeZustand(z),
    zustand: () => useKosmoStatus.getState().zustand,
    beschaeftigt: () => useKosmoStatus.getState().beschaeftigt,
    // Welle B (C-Kosmo): Sicht auf Auftrag, Pegel und Blase fuer Browserproben.
    auftrag: () => useKosmoStatus.getState().auftrag,
    // Nur fuer Proben, die eine Karte AM Orb brauchen, ohne einen echten Auftrag
    // zu starten (z. B. die Fokusring-Messung): setzt/loescht den Auftrag im Status.
    setzeAuftrag: (a: { name: string; schritt?: number; schritteGesamt?: number } | null) =>
      useKosmoStatus.getState().setzeAuftrag(a),
    pegel: () => useKosmoStatus.getState().pegel,
    setzePegel: (p: number | undefined) => useKosmoStatus.getState().setzePegel(p),
    antwortBlase: () => useKosmoStatus.getState().antwortBlase,
  };
}
