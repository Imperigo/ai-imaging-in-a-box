import { create } from 'zustand';

/**
 * Cursor-Zustand (v0.7.2 §8, Paket 08) — reiner LAUFZEIT-Store (Muster wie
 * `state/kosmo-status.ts`): läuft nie durch Yjs/Undo, lebt nur im Prozess.
 * Treibt `shell/CursorEbene.tsx` — das eigentliche Zeichnen (SVG/CSS) lebt
 * dort, hier nur der Zustand + die Eigencursor-An/Aus-Ermittlung.
 *
 * Bewusst OHNE Import aus `shell/**` (Schichtregel: `state/` kennt `shell/`
 * nicht, umgekehrt schon — `CursorEbene.tsx` importiert diesen Store, nicht
 * andersherum). Die Werkzeug-Glyphen-Art für den `tool`-Zustand wird darum
 * hier nur als loser String gehalten; `CursorEbene.tsx` validiert ihn gegen
 * `WerkzeugGlyphenArt`, bevor sie ihn rendert.
 */
/** v0.8.4 PA1 (D1-Fix) — Zonen-FORMEN: `CursorEbene.tsx` liest den COMPUTED
 *  cursor der Elementkette unter dem Zeiger und MAPPT ihn auf eine dieser
 *  Formen, statt die Ebene (wie die alte `hatEigenenComputedCursor()`-
 *  Heuristik) zu verstecken. Rein zonen-abgeleitet — nie über `setzeZustand`
 *  gesetzt, genau wie `precision` schon vorher (s. `CursorStore.zustand`
 *  unten). Siehe `CSS_CURSOR_ZU_FORM`/`formVonComputedCursor` für die
 *  eigentliche (reine, unit-getestete) Abbildung. */
/** v0.9.5 P-MF2 / C-21 (Owner-Befund O-7c, `docs/V095-SPEZ.md`:193-196) —
 *  vier NEUE Formen: `kante`/`knoten` sagen im Grundriss, was ein Klick hier
 *  täte (Kante fassen bzw. Eckpunkt fassen); `diagonale-ab`/`diagonale-auf`
 *  vervollständigen die Resize-Familie, von der bisher nur `spalte` (ew) und
 *  `zeile` (ns) eine gezeichnete Form hatten — die beiden diagonalen
 *  CSS-Werte fielen bis hierher stumm auf neutral zurück. */
export type ZonenForm =
  | 'greifen'
  | 'greift'
  | 'fadenkreuz'
  | 'spalte'
  | 'zeile'
  | 'gesperrt'
  | 'kante'
  | 'knoten'
  | 'diagonale-ab'
  | 'diagonale-auf';

export type CursorZustand = 'default' | 'loading' | 'kosmo' | 'tool' | 'precision' | ZonenForm;

export interface ToolCursorInfo {
  /** Werkzeug-Glyphen-Art (`shell/werkzeug-glyphen.tsx`, z.B. "draw"). */
  art: string;
  /** CSS-Custom-Property-NAME einer Rollenfarbe (z.B. `--k-rolle-manuell`), OHNE `var()`. */
  rolle?: string;
}

interface CursorStore {
  /** Programmatisch gesetzter Grundzustand — `precision`/die `ZonenForm`-
   *  Werte werden NIE direkt hierüber gesetzt (das ist reine Zonen-Erkennung
   *  in `CursorEbene.tsx`, siehe dortiger Kopfkommentar), nur
   *  `default/loading/kosmo/tool`. */
  zustand: Exclude<CursorZustand, 'precision' | ZonenForm>;
  tool: ToolCursorInfo | null;
  /**
   * v0.9.5 P-MF2 / C-21 — die TREFFER-gesteuerte Form: eine Zonenform, die
   * nicht aus einer CSS-Regel am Element stammt, sondern aus einem
   * geometrischen Treffertest (heute: `PlanView`s Hover über Kante/Ecke im
   * Grundriss). `null` = kein Treffersignal, die bisherige Kette entscheidet.
   *
   * **Warum ein Store-Feld und nicht `style.setProperty('--k-zeiger', …)`
   * (Muster `Viewport3D.tsx`:2737).** Der `--k-zeiger`-Weg ist kein
   * Geschmacksurteil schlechter, er ist hier strukturell untauglich — aus
   * zwei unabhängigen Gründen, beide im Code belegbar:
   *
   *  1. `CursorEbene.tsx` liest die Property NUR bei ZIEL-Wechsel oder nach
   *     einem pointerdown/-up (`if (ziel === letztesZiel &&
   *     !zonenPruefungFaellig) return;` — die v0.9.1-Optimierung gegen das
   *     «laggt»). Beim Fahren über EIN Plan-SVG wechselt `e.target` nie: von
   *     der Wandmitte auf die Wandkante ist derselbe Knoten. Die Form würde
   *     schlicht nie nachgeführt.
   *  2. Selbst wenn sie gelesen würde, käme sie nicht durch: das Plan-SVG
   *     trägt `data-cursor-zone="praezision"` (`PlanView.tsx`), und
   *     `istPraezisionsZone` gewinnt in `CursorEbene` VOR jeder
   *     computed-cursor-Form. Über dem Grundriss ist die
   *     `--k-zeiger`-Schiene also ohnehin abgeschattet.
   *
   * Der Store-Weg umgeht beides: React rendert bei jeder Wertänderung, und
   * die Ebene gibt dem Treffersignal Vorrang vor der Präzisions-Zusage (das
   * Konkretere schlägt das Allgemeine — die Fläche sagt «hier wird genau
   * gezeigt», der Treffer sagt «und zwar auf diese Kante»).
   */
  trefferForm: ZonenForm | null;
  setzeZustand: (z: Exclude<CursorZustand, 'precision' | ZonenForm>) => void;
  setzeToolCursor: (info: ToolCursorInfo) => void;
  /** Setzt/löscht die treffer-gesteuerte Form. Schreibt NUR bei echter
   *  Änderung — der Aufrufer sitzt im Hover-Pfad (rAF-gedrosselt, aber
   *  trotzdem heiss), und ein `set` mit gleichem Wert wäre ein Re-Render
   *  ohne Anlass. */
  setzeTrefferForm: (form: ZonenForm | null) => void;
  zurueckAufDefault: () => void;
  /**
   * P-KOSMOFENSTER (v0.9.35, O-T11): Anforderungs-Zähler «bewerte die
   * Cursor-Zone neu». Die `CursorEbene` cacht ihr letztes Ziel und prüft
   * die Zone nur bei Zielwechsel/Klick — ändert sich die UI unter dem
   * STEHENDEN Zeiger (Kosmo-Fenster öffnet/schliesst), ist das nächste
   * Ziel oft wieder dasselbe Element und die alte Form bleibt hängen.
   * Ein Zähler statt eines Booleans: zwei schnelle Anforderungen dürfen
   * sich nicht verschlucken.
   */
  neuBewertung: number;
  fordereNeubewertung: () => void;
}

export const useCursorZustand = create<CursorStore>((set, get) => ({
  zustand: 'default',
  tool: null,
  trefferForm: null,
  setzeZustand: (z) => set({ zustand: z }),
  setzeToolCursor: (info) => set({ zustand: 'tool', tool: info }),
  setzeTrefferForm: (form) => {
    if (get().trefferForm !== form) set({ trefferForm: form });
  },
  zurueckAufDefault: () => set({ zustand: 'default', tool: null, trefferForm: null }),
  neuBewertung: 0,
  fordereNeubewertung: () => set((s) => ({ neuBewertung: s.neuBewertung + 1 })),
}));

const EIGENCURSOR_KEY = 'kosmo.eigencursor';

/** pointer:fine = Maus/Trackpad (kein Touch-only-Gerät). */
function zeigtPointerFine(): boolean {
  try {
    return typeof window !== 'undefined' && typeof window.matchMedia === 'function'
      ? window.matchMedia('(pointer: fine)').matches
      : false;
  } catch {
    return false;
  }
}

/**
 * Eigenständige Plattform-Probe: läuft dieser Prozess als Tauri-Desktop-App
 * unter Linux (nicht Android, nicht Browser/PWA, nicht Windows/macOS)?
 *
 * **Geschichte, damit sie nicht verloren geht:** v0.9.5.1 (Owner-Befund
 * 29.07.2026, Ubuntu 26.04, RTX 5090, Wayland, WebKitGTK 2.52 — wörtlich:
 * «dann lagged das ganze system wenn ich 3d bewege und maus hinterlässt
 * artefakte») liess `eigencursorVorgabe()` unten auf genau dieser Probe eine
 * Default-AUS-Ausnahme bauen. Diese Ausnahme ist mit ROADMAP 872
 * zurückgenommen (s. `eigencursorVorgabe` unten und
 * `docs/CURSOR-URSACHENANALYSE.md` §6) — die Probe selbst bleibt aber
 * bestehen: sie ist eine allgemeine Plattform-Auskunft, kein Artefakt der
 * zurückgenommenen Entscheidung, und `shell/CursorEbene.tsx` referenziert sie
 * weiterhin als Hintergrund zu einer ANDEREN, unabhängigen Frage (P-Z,
 * unzuverlässige Pointer-Event-Zustellung unter WebKitGTK+NVIDIA+Wayland —
 * s. `docs/CURSOR-URSACHENANALYSE.md` §6, dort weiterhin offen).
 *
 * **Bewusst OHNE Import aus `shell/**`** (Schichtregel, s. Kopfkommentar
 * dieser Datei: «state/ kennt shell/ nicht»). `istTauriDesktop()`
 * (`shell/cloud-login.ts`) wird darum NICHT importiert, sondern dieselbe
 * Probe (`'__TAURI_INTERNALS__' in window`) eigenständig dupliziert — exakt
 * das Muster, das `shell/sicherer-modus.ts` an anderer Stelle mit
 * `texturenAktiv()` schon vormacht (dort eine Paket-Grenze statt einer
 * Schicht-Grenze als Grund, gleiches Duplizierungs-Muster als Lösung).
 *
 * `navigator.userAgent` enthält `Linux` sowohl auf echten Linux-Desktops als
 * auch auf Android — Android wird explizit ausgeschlossen, sonst würde ein
 * (heute nicht existierendes) Tauri-Android-Ziel fälschlich mitgefangen.
 */
export function istTauriDesktopUnterLinux(): boolean {
  try {
    if (typeof window === 'undefined') return false;
    if (!('__TAURI_INTERNALS__' in window)) return false;
    const ua = typeof navigator === 'undefined' ? '' : navigator.userAgent;
    return ua.includes('Linux') && !ua.includes('Android');
  } catch {
    return false;
  }
}

/**
 * Vorgabe OHNE gespeicherten Wert: `pointer:fine` — auf ALLEN Plattformen
 * gleich, auch auf Tauri-Desktop unter Linux.
 *
 * **War nicht immer so.** v0.9.5.1 (ROADMAP 706 Teil 3) baute hier eine
 * Linux-Ausnahme (immer AUS, unabhängig vom Zeigertyp) auf zwei
 * Begründungen: der Eigencursor verstärke Ruckeln UND Compositing-Artefakte
 * auf WebKitGTK+NVIDIA+Wayland. **Mit ROADMAP 872 zurückgenommen, weil
 * beide Begründungen gefallen sind:**
 *  - Die Ruckel-Hälfte war bereits widerlegt (`docs/handoff/studienmodell/
 *    HANDOFF.md` §4: 62,6 fps mit UND ohne die begleitenden Flags, auf
 *    genau dieser Maschine).
 *  - Die Artefakt-Hälfte galt laut `docs/CURSOR-URSACHENANALYSE.md` §6 als
 *    „unwiderlegt, aber auch nicht bestätigt" — der Owner hat sie am
 *    11.08.2026 auf derselben Maschine von Hand geprüft (Eigencursor an,
 *    3D-Schwenk): «nein ruckelt nichts». Eine Handbeobachtung, kein
 *    Messstand — s. dortige Grenze —, aber die einzige Prüfung, die diese
 *    Ausnahme je erhalten hat.
 *
 * `istTauriDesktopUnterLinux()` bleibt als eigenständige Plattform-Probe
 * bestehen (s. dortiger Kommentar), wird hier aber bewusst NICHT mehr
 * abgefragt.
 */
function eigencursorVorgabe(): boolean {
  return zeigtPointerFine();
}

/**
 * Ist der Eigencursor aktiv? Spec §8: **Default AN nur bei `pointer:fine`**,
 * gleich auf allen Plattformen (die v0.9.5.1-Linux-Ausnahme ist mit
 * ROADMAP 872 zurückgenommen, s. `eigencursorVorgabe` oben) — ein
 * gespeicherter Wert (der Schalter selbst kommt erst mit W4-H,
 * `Einstellungen.tsx`) gewinnt weiterhin IMMER, in beide Richtungen; hier
 * wird `kosmo.eigencursor` nur GELESEN, nie geschrieben. `'1'` = an, `'0'`
 * = aus, jeder andere/fehlende Wert fällt auf die Vorgabe zurück.
 */
export function eigencursorAktiv(): boolean {
  try {
    if (typeof localStorage === 'undefined') return eigencursorVorgabe();
    const gespeichert = localStorage.getItem(EIGENCURSOR_KEY);
    if (gespeichert === '1') return true;
    if (gespeichert === '0') return false;
    return eigencursorVorgabe();
  } catch {
    return eigencursorVorgabe();
  }
}

/** Event-Name (v0.7.2 W4-H, Einstellungs-Verdrahtung): `CursorEbene.tsx`
 *  liest `eigencursorAktiv()` nur beim RENDER, nicht reaktiv aus einem
 *  Store — ein Schreiben aus `Einstellungen.tsx` (ein separater Komponenten-
 *  baum) löst dort sonst keinen Re-Render aus. Statt die bewusst store-freie
 *  Architektur dieser Datei umzubauen (Kopfkommentar: «kein Import aus
 *  shell/**»), ein simples DOM-Event — `CursorEbene.tsx` hört zu und
 *  erzwingt einen Re-Render, der `eigencursorAktiv()` dann frisch liest. */
export const EIGENCURSOR_EINSTELLUNG_EVENT = 'kosmo:eigencursor-einstellung';

/** Schreibt `kosmo.eigencursor` (Einstellungen.tsx, Schalter
 *  `einstellung-eigencursor`) UND benachrichtigt `CursorEbene.tsx` sofort
 *  (s. `EIGENCURSOR_EINSTELLUNG_EVENT` oben) — der Schalter wirkt ohne
 *  Reload. */
export function setEigencursorEingestellt(an: boolean): void {
  try {
    if (typeof localStorage !== 'undefined') localStorage.setItem(EIGENCURSOR_KEY, an ? '1' : '0');
  } catch {
    /* localStorage kann in seltenen Umgebungen (privates Fenster o.ä.) werfen — Einstellung ist optional */
  }
  try {
    if (typeof window !== 'undefined') window.dispatchEvent(new Event(EIGENCURSOR_EINSTELLUNG_EVENT));
  } catch {
    /* kein window (SSR/Test) — nichts zu benachrichtigen */
  }
}

const ZEIGER_MORPH_AUS_KEY = 'kosmo.zeiger-morph-aus';

/**
 * P-ZEIGER-SOFORT (v0.9.44, Owner-Ventil «das problem besteht nach wie vor
 * das der delay bemerkbar ist») — reiner localStorage-Spiegel, exakt das
 * Muster von `eigencursorAktiv()` oben: `'1'` = Morph AUS (Zeiger wechselt
 * die Form sofort, ohne Kollaps/Entfalten-Zyklus), jeder andere/fehlende
 * Wert = Vorgabe AN (Morph bleibt an — niemandem wird etwas weggenommen,
 * der nicht danach fragt, Owner-Vorgabe wörtlich).
 */
export function zeigerMorphAusAktiv(): boolean {
  try {
    if (typeof localStorage === 'undefined') return false;
    return localStorage.getItem(ZEIGER_MORPH_AUS_KEY) === '1';
  } catch {
    return false;
  }
}

/** Event-Name — exakt das `EIGENCURSOR_EINSTELLUNG_EVENT`-Muster oben:
 *  `CursorEbene.tsx` liest `zeigerMorphAusAktiv()` nur beim Render, ein
 *  Schreiben aus `Einstellungen.tsx` (separater Komponentenbaum) braucht
 *  darum ein DOM-Event, um dort einen Re-Render zu erzwingen. */
export const ZEIGER_MORPH_EINSTELLUNG_EVENT = 'kosmo:zeiger-morph-einstellung';

/** Schreibt `kosmo.zeiger-morph-aus` UND benachrichtigt `CursorEbene.tsx`
 *  sofort (s. `ZEIGER_MORPH_EINSTELLUNG_EVENT` oben) — der Schalter wirkt
 *  ohne Reload. */
export function setZeigerMorphAusEingestellt(aus: boolean): void {
  try {
    if (typeof localStorage !== 'undefined') localStorage.setItem(ZEIGER_MORPH_AUS_KEY, aus ? '1' : '0');
  } catch {
    /* localStorage kann in seltenen Umgebungen (privates Fenster o.ä.) werfen — Einstellung ist optional */
  }
  try {
    if (typeof window !== 'undefined') window.dispatchEvent(new Event(ZEIGER_MORPH_EINSTELLUNG_EVENT));
  } catch {
    /* kein window (SSR/Test) — nichts zu benachrichtigen */
  }
}

/**
 * v0.8.4 PA1 (D1-Fix, docs/V084-SPEZ.md §2 D1) — die Zonen-Tabelle: welcher
 * COMPUTED `cursor`-Wert einer Elementkette auf welche `ZonenForm` mappt.
 * Bewusst NUR echte CSS-Schlüsselwörter (v0.8.4: die sechs vertraglich
 * verlangten crosshair/grab/grabbing/col-resize/row-resize/not-allowed;
 * v0.9.5 P-MF2: sieben weitere, s. unten) — alles andere (inkl. `auto`/
 * `default`/`pointer`/leer) bleibt neutral (Morph-Default, kein Zonen-Layer).
 *
 * **Wichtig — die eigentliche Fund-Ursache von D1:** `:root[data-eigencursor
 * ='an'] { cursor: none }` (`cursor-ebene.css`) steht auf `<html>`. `cursor`
 * ist eine VERERBTE CSS-Eigenschaft — jedes Element OHNE eigene `cursor`-
 * Deklaration erbt darum, sobald der Eigencursor an ist, den COMPUTED Wert
 * `"none"` (live mit Playwright/Chromium nachgemessen: ein `<div>` ohne
 * eigene Cursor-Regel unter `html{cursor:none}` liefert `getComputedStyle
 * (div).cursor === "none"`, NICHT `"auto"`). Die alte Heuristik
 * (`hatEigenenComputedCursor`, jetzt entfernt) schloss nur `''`/`auto`/
 * `default`/`pointer` aus — `"none"` fiel NICHT unter den Ausschluss und
 * wurde fälschlich als "Element hat einen eigenen Cursor-Wunsch" gewertet:
 * die Ebene versteckte sich darum nicht nur über den paar explizit
 * gestylten Zonen (crosshair/grab/…), sondern über praktisch JEDEM
 * unbestylten Element der App — UND weil `cursor:none` gleichzeitig den
 * echten System-Zeiger unsichtbar machte, verschwand der Zeiger dort
 * komplett (die vom Owner beschriebene "buggt weg"). `"none"` taucht darum
 * bewusst NICHT in dieser Tabelle auf — es ist kein Zonen-Signal, sondern
 * ein reines Vererbungs-Artefakt des eigenen `cursor:none`-Riegels.
 *
 * v0.9.5 P-MF2 / C-21 — die Tabelle wächst um SIEBEN Werte, und zwar ohne
 * ihren Vertrag zu brechen: es sind ausschliesslich echte CSS-Schlüsselwörter
 * (kein erfundener Wert, kein `--k-*`-Name als Tarnung).
 *
 *  · `cell` → `knoten`. Der einzige Standardwert, der einen fassbaren PUNKT
 *    meint statt einer Richtung — in CAD-Oberflächen der übliche Zeiger über
 *    einem Eckpunkt/Fangpunkt.
 *  · `n/e/s/w-resize` → `kante`. Die vier EINSEITIGEN Resize-Werte heissen
 *    wörtlich «diese eine Kante wird bewegt» — genau die Aussage der
 *    Kanten-Form. Alle vier auf EINE Form, weil eine Grundriss-Kante in
 *    beliebigem Winkel liegt: eine Richtung zu zeichnen, die das Modell gar
 *    nicht hergibt, wäre eine Behauptung statt einer Auskunft.
 *  · `nwse-resize`/`nesw-resize` → `diagonale-ab`/`diagonale-auf`. Sie
 *    schliessen die Resize-Familie, von der bisher nur `col-resize` und
 *    `row-resize` eine Form hatten; die beiden diagonalen fielen still auf
 *    neutral zurück.
 */
const CSS_CURSOR_ZU_FORM: Readonly<Record<string, ZonenForm>> = {
  crosshair: 'fadenkreuz',
  grab: 'greifen',
  grabbing: 'greift',
  'col-resize': 'spalte',
  'row-resize': 'zeile',
  'not-allowed': 'gesperrt',
  cell: 'knoten',
  'n-resize': 'kante',
  'e-resize': 'kante',
  's-resize': 'kante',
  'w-resize': 'kante',
  'nwse-resize': 'diagonale-ab',
  'nesw-resize': 'diagonale-auf',
};

/** Reine Funktion (unit-getestet in `test/cursor-zustand.test.ts`): bildet
 *  einen COMPUTED-`cursor`-String auf eine `ZonenForm` ab, oder `null` für
 *  alles, was neutral bleiben soll (`CursorEbene.tsx` fällt dann auf den
 *  Store-/Morph-Zustand zurück). Kennt keine DOM-APIs — `CursorEbene.tsx`
 *  liest `getComputedStyle(el).cursor` und reicht nur den String rein. */
export function formVonComputedCursor(cursorWert: string): ZonenForm | null {
  return CSS_CURSOR_ZU_FORM[cursorWert] ?? null;
}

/** `prefers-reduced-motion: reduce`? — reiner Lese-Helfer, siehe `CursorEbene.tsx`
 *  Kopfkommentar dazu, WARUM diese Datei ihn kaum je selbst braucht (die
 *  komplette Zeitsteuerung des Cursors läuft über CSS, das der globale
 *  `aura.css`-Riegel bereits auf 0.01ms zwingt). */
export function bevorzugtReduzierteBewegung(): boolean {
  try {
    return typeof window !== 'undefined' && typeof window.matchMedia === 'function'
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false;
  } catch {
    return false;
  }
}
