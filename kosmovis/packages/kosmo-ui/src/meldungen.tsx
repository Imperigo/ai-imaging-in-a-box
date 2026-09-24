import { useSyncExternalStore } from 'react';
import { createPortal } from 'react-dom';
import { KButton } from './components';

/**
 * Meldungen (V1-Finish P1) — das eine Sprachrohr der App: `melde()` ersetzt
 * jedes `alert()`, `bestaetigen()` jedes `confirm()`. Eigenbau ohne Store-
 * Abhängigkeit (useSyncExternalStore), Werkplan-Ästhetik, aria-live.
 * Regel: Fehler bleiben länger stehen und tragen, wo sinnvoll, eine Aktion.
 */

export interface Meldung {
  id: number;
  text: string;
  ton: 'info' | 'erfolg' | 'fehler';
  aktion?: { label: string; run: () => void };
}

let meldungen: Meldung[] = [];
/**
 * B82 #7 (`docs/AUFTRAG-B82-SECHS-VERDRAHTUNGEN.md`): ein reiner, GEISTIGES-
 * ARRAY-Nebenkanal für die Austritts-Bewegung — bewusst GETRENNT von
 * `meldungen` statt eines `verlassend`-Felds AUF `meldungen`-Einträgen (erster
 * Entwurf, verworfen). Grund, gemessen statt vermutet: `entferne()` entfernte
 * bislang SYNCHRON aus `meldungen`, und mindestens neun Bestandstests in
 * fremden Dateien (`w3-1-achsen-hinweis.test.tsx`,
 * `section-view-griff-mehrdeutig.test.tsx`, `section-view-griff-oeff-s-
 * luecke.test.tsx`, `publish-ansicht-schnitt-stille-ablehnung.test.tsx` u. a.,
 * ausserhalb dieses Dateikreises) klicken `.k-meldung-schliessen` SYNCHRON in
 * ihrem `afterEach` und erwarten `[data-testid="meldung-*"]` DANACH, ohne
 * einen Timer vorzuspulen, als `null` — eine erste Fassung mit verzögerter
 * Entfernung aus `meldungen` selbst liess genau diese neun rot werden
 * (`npm test`, elf Fehlschläge in sechs Dateien, gemessen). `meldungen`
 * bleibt darum BYTE-GLEICH synchron wie vorher; die schliessende Karte
 * wandert stattdessen für `EXIT_MS` in `geister` — eine reine Zusatz-Kopie
 * für die Optik, kein zweiter Wahrheits-Ort für Toast-Daten. Ihr Rendering
 * trägt ein ANDERES `data-testid` (`meldung-verlassend`, s. `KMeldungen`
 * unten) — kein Bestandstest, der `[data-testid="meldung-{ton}"]` sucht,
 * kann sie je finden.
 */
let geister: Meldung[] = [];
let naechsteId = 1;
const hoerer = new Set<() => void>();
const timer = new Map<number, ReturnType<typeof setTimeout>>();
const geistTimer = new Map<number, ReturnType<typeof setTimeout>>();

/** Muss zur Dauer von `--k-motion-settle` (`aura.css`) passen — dieselbe
 *  Zahl trägt die `k-meldung-aus`-Animation UND die `k-meldung-shake`-
 *  Verzögerung (`.k-meldung-shake` in `aura.css`), damit beide Bewegungen
 *  zur selben CSS-Variable synchron bleiben. */
const EXIT_MS = 320;

function benachrichtige(): void {
  for (const h of hoerer) h();
}

/**
 * Toast schliessen — entfernt WEITERHIN SOFORT aus `meldungen` (Bestands-
 * vertrag, unverändert: jeder existierende Aufrufer — Auto-Dismiss-Timer,
 * ✕-Knopf, Aktions-Knopf — sah das schon immer so). B82 #7 hängt NUR einen
 * Nebeneffekt an: die entfernte Karte lebt für `EXIT_MS` als Geist weiter
 * (`k-meldung--aus`, `aura.css`), rein optisch, ohne den `meldungen`-Vertrag
 * zu berühren.
 */
function entferne(id: number): void {
  const t = timer.get(id);
  if (t) clearTimeout(t);
  timer.delete(id);
  const weg = meldungen.find((m) => m.id === id);
  meldungen = meldungen.filter((m) => m.id !== id);
  if (weg) {
    geister = [...geister, weg];
    const gt = geistTimer.get(id);
    if (gt) clearTimeout(gt);
    geistTimer.set(
      id,
      setTimeout(() => {
        geistTimer.delete(id);
        geister = geister.filter((g) => g.id !== id);
        benachrichtige();
      }, EXIT_MS),
    );
  }
  benachrichtige();
}

/** Toast zeigen. Fehler stehen 8 s, alles andere 4 s; ✕ schliesst sofort. */
export function melde(
  text: string,
  opts?: { ton?: Meldung['ton']; dauerMs?: number; aktion?: Meldung['aktion'] },
): void {
  const ton = opts?.ton ?? 'info';
  // v0.9.0 Fehlermeldeweg (Owner-Auftrag 22.07.2026 «wenn kosmo
  // fehlermeldungen bekommt … an dich gesendet»): jede Fehler-Meldung wird
  // zusätzlich als DOM-Event publiziert — die App (state/fehlerberichte.ts)
  // sammelt sie und reicht sie an die HomeServer-Bridge weiter. Rein
  // additiv, feuert nur im Browser (Unit-Tests ohne DOM bleiben unberührt).
  if (ton === 'fehler' && typeof window !== 'undefined') {
    try {
      window.dispatchEvent(new CustomEvent('kosmo-fehlermeldung', { detail: { text } }));
    } catch {
      /* Event-Publikation darf nie die Meldung selbst verhindern. */
    }
  }
  const m: Meldung = { id: naechsteId++, text, ton, ...(opts?.aktion ? { aktion: opts.aktion } : {}) };
  meldungen = [...meldungen.slice(-3), m]; // nie mehr als 4 aufs Mal
  timer.set(m.id, setTimeout(() => entferne(m.id), opts?.dauerMs ?? (ton === 'fehler' ? 8000 : 4000)));
  benachrichtige();
}

/** Kurzform für Fehlerpfade (catch-Blöcke): nimmt Error oder Text. */
export function meldeFehler(err: unknown, aktion?: Meldung['aktion']): void {
  const text = err instanceof Error ? err.message : String(err);
  melde(text, { ton: 'fehler', ...(aktion ? { aktion } : {}) });
}

// ── Ansage (aria-live, ohne sichtbare Meldung) ───────────────────────

/**
 * `ansage()` (P-g / Tastatur-Rückgrat, `docs/UI-UX-2026-09-08-TASTATUR-
 * RUECKGRAT.md`) — das im Design-System fehlende Gegenstück zu `melde()`:
 * eine Ansage für Hilfstechnik (Screenreader), OHNE eine sichtbare
 * Toast-Karte zu erzeugen.
 *
 * ## Warum das etwas anderes ist als `melde()`
 *
 * `melde()`/`meldeFehler()` sind für SEHENDE Nutzung gedacht — eine Karte
 * erscheint, bleibt 4–8 s stehen, kann geschlossen werden. Das
 * `aria-live="polite"` auf `KMeldungen`s Host (`:159`) macht diese Karten
 * NEBENBEI auch für Screenreader hörbar, aber das ist ein Nebeneffekt der
 * sichtbaren Karte, keine eigene Fähigkeit. Es gibt Fälle, in denen etwas
 * angesagt werden muss, das NIE als Karte erscheinen soll — ein
 * Zustandswechsel, der optisch schon anders sichtbar ist (ein Rollfokus-
 * Sprung, ein sich öffnendes Panel, eine Fortschrittszahl, die sich pro
 * Sekunde ändert und als Toast-Flut nur nerven würde). Für diesen Fall gab
 * es im Design-System bislang KEINE Abstraktion — gemessen: genau EIN
 * `aria-live`-Attribut im ganzen Paket (`:159`, dieser Datei), dazu vier
 * handgesetzte Einzelstellen in der App, und keine `ansage()`-Funktion.
 * Gegenprobe deutsch (`lebendbereich`): null Treffer.
 *
 * ## API
 *
 * ```ts
 * ansage('Element 3 von 8 ausgewählt');           // hoeflichkeit: 'polite' (Default)
 * ansage('Eingabe ungültig', 'assertive');        // unterbricht laufende Ansagen
 * ```
 *
 * Zwei Höflichkeitsstufen, identisch zur `aria-live`-Spezifikation:
 * - `'polite'` (Default) — wartet, bis die Hilfstechnik eine Pause hat,
 *   bevor sie die Ansage vorliest. Für Statuswechsel ohne Dringlichkeit
 *   (Rollfokus-Position, ein abgeschlossener Hintergrundschritt).
 * - `'assertive'` — unterbricht sofort. Nur für Ansagen, die wirklich nicht
 *   warten dürfen (ein Fehler, der die aktuelle Eingabe ungültig macht).
 *
 * ## Wie sie technisch ankommt
 *
 * `KAnsageBereich` (unten) rendert ZWEI dauerhaft vorhandene, aber visuell
 * verborgene (`.k-nur-sr`, wie im Bestand üblich — reines Clip-Pattern,
 * keine `display:none`/`visibility:hidden`-Falle, die Hilfstechnik ebenso
 * ausblenden würde) Text-Container, einen je Höflichkeitsstufe — GETRENNT
 * von `KMeldungen`s Toast-`aria-live`-Bereich oben, damit eine `ansage()`
 * nie eine sichtbare Karte auslöst und umgekehrt. `ansage()` selbst
 * schreibt den Text in denselben `useSyncExternalStore`-Store-Takt
 * (`abonniere`/`hoerer`, s. oben) wie `melde()` — EIN Store-Muster für
 * beide Kanäle dieser Datei, kein zweiter Mechanismus.
 *
 * Ein Text, der zweimal HINTEREINANDER identisch ist, wird von manchen
 * Screenreadern beim zweiten Mal NICHT erneut vorgelesen (der DOM-Knoten
 * hat sich aus Sicht der Hilfstechnik nicht geändert) — ein bekanntes
 * `aria-live`-Verhalten, kein Fehler dieser Implementierung. Wer dieselbe
 * Ansage zweimal in Folge braucht, hängt einen unsichtbaren Zähler oder ein
 * Leerzeichen an (Bestandsmuster, hier nicht automatisiert, weil die
 * bisherigen vier Einzelstellen dieses Bedürfnis nicht zeigen).
 *
 * ## Rollout-Pflicht — wer diese Funktion wie braucht
 *
 * `KAnsageBereich` muss EINMAL in der Shell gemountet werden (wie
 * `KMeldungen`/`KBestaetigung`) — das gehört NICHT zum Dateikreis dieses
 * Pakets (`apps/**` ist ausgeschlossen) und wird im Bericht als offener
 * Posten an den Adressaten `ui` gemeldet. Die vier bestehenden
 * handgesetzten `aria-live`-Einzelstellen in der App sind ebenfalls NICHT
 * Teil dieses Pakets — ihr Ersatz durch `ansage()` ist eigene Folgearbeit.
 */
export type AnsageHoeflichkeit = 'polite' | 'assertive';

interface AnsageZustand {
  polite: string;
  assertive: string;
  /** Läuft bei jeder Ansage hoch — erzwingt einen React-Reconciliation-Diff
   *  auch dann, wenn zwei Ansagen DERSELBEN Stufe zufällig denselben Text
   *  tragen (ohne dies würde React den DOM-Text unverändert lassen und der
   *  Screenreader läse ihn u.U. gar nicht erneut vor, s. Kopfkommentar). */
  taktPolite: number;
  taktAssertive: number;
}

let ansageZustand: AnsageZustand = { polite: '', assertive: '', taktPolite: 0, taktAssertive: 0 };
const ansageHoerer = new Set<() => void>();

function ansageBenachrichtige(): void {
  for (const h of ansageHoerer) h();
}

function ansageAbonniere(cb: () => void): () => void {
  ansageHoerer.add(cb);
  return () => ansageHoerer.delete(cb);
}

/**
 * Sagt `text` an Hilfstechnik an, OHNE eine sichtbare Meldung zu erzeugen —
 * das Gegenstück zu `melde()`. Siehe Datei-Kopfkommentar für die volle
 * Begründung/API-Doku. `hoeflichkeit` default `'polite'`.
 */
export function ansage(text: string, hoeflichkeit: AnsageHoeflichkeit = 'polite'): void {
  ansageZustand =
    hoeflichkeit === 'assertive'
      ? { ...ansageZustand, assertive: text, taktAssertive: ansageZustand.taktAssertive + 1 }
      : { ...ansageZustand, polite: text, taktPolite: ansageZustand.taktPolite + 1 };
  ansageBenachrichtige();
}

/* NACHGEZOGEN AM 09.09.2026 (P-TASTATUR-LUECKEN Teil 2). Hier stand ein
   `VERBORGEN_STYLE`-Inline-Objekt mit dem Clip-Muster, und der Kommentar
   daneben nannte den Grund selbst: «eine `.k-nur-sr`-Regel wäre die
   naheliegendere Form, ist aber gemeldet statt gebaut», weil `aura.css`
   ausserhalb des damaligen Dateikreises lag. Der Kreis ist offen, die Regel
   steht (`aura.css`, `.k-nur-sr`), und die Verdopplung ist weg — mit ihr die
   Gefahr, dass jemand die zweite Kopie später zu `display:none` «vereinfacht»
   und damit genau das abschaltet, wofür sie da ist. */

/** Host für `ansage()` — einmal in der Shell mounten (Rollout-Pflicht s.
 *  Kopfkommentar). Zwei dauerhaft vorhandene, visuell verborgene
 *  `aria-live`-Container, GETRENNT vom Toast-Host `KMeldungen` oben. */
export function KAnsageBereich() {
  const zustand = useSyncExternalStore(ansageAbonniere, () => ansageZustand, () => ansageZustand);
  return (
    <>
      <div aria-live="polite" aria-atomic="true" className="k-nur-sr" data-testid="ansage-polite">
        {zustand.polite}
      </div>
      <div aria-live="assertive" aria-atomic="true" className="k-nur-sr" data-testid="ansage-assertive">
        {zustand.assertive}
      </div>
    </>
  );
}

function abonniere(cb: () => void): () => void {
  hoerer.add(cb);
  return () => hoerer.delete(cb);
}

const TON_FARBE: Record<Meldung['ton'], string> = {
  info: 'var(--k-ink-soft)',
  erfolg: 'var(--k-success)',
  fehler: 'var(--k-danger)',
};

/** Höchstens so viele volle Meldungskarten gleichzeitig — P-TOASTDECKEL
 * (`docs/UI-2026-08-27-B72-MELDUNG-UEBER-FENSTER.md` §3a, gemessen im
 * Browser am unveränderten Testobjekt Lichthof): der Host wächst je Toast um exakt +67,2px
 * nach oben (`bottom:160px` bleibt fix, `.k-meldungen-host` unten) — ab dem
 * DRITTEN gleichzeitig stehenden Toast erreicht der Stapel die «Ausführen»-
 * Knöpfe, die ihn selbst ausgelöst haben. Ursache ist die Stapelgeometrie
 * (wie viele volle Karten gleichzeitig übereinanderstehen), nicht der
 * einzelne Toast — darum deckelt dies die SICHTBARE Kartenzahl, statt Text,
 * Ton oder Lebensdauer eines Toasts zu ändern. Bei 1 und 2 Toasts ändert
 * sich dadurch nichts (Pflicht-Gegenprobe, `meldungen-stapel-deckel.test.tsx`).
 */
const SICHTBARE_TOASTS_MAX = 2;

/** Host — einmal in der Shell mounten.
 *
 * v0.8.0B / P2 (Spez §3: KSelect/KDialog/KMenu/Meldungen → Glass-/
 * Flächenstufen-Optik, Verhalten unverändert) — die Inline-Styles wandern in
 * `.k-meldungen-host`/`.k-meldung-karte`/… (`aura.css`); `aria-live`,
 * `data-testid="meldung-{ton}"` und die Ton-Farbe (weiterhin ein CSS-
 * Variablen-Wert, `TON_FARBE`, kein rohes Hex) bleiben byte-gleich.
 */
export function KMeldungen() {
  const liste = useSyncExternalStore(abonniere, () => meldungen, () => meldungen);
  // B82 #7: eigener externer Store für den Geister-Nebenkanal — dieselbe
  // `abonniere`-Funktion (derselbe `hoerer`-Satz), zwei unabhängige
  // Ausschnitte desselben Benachrichtigungs-Takts.
  const geisterListe = useSyncExternalStore(abonniere, () => geister, () => geister);
  if (liste.length === 0 && geisterListe.length === 0) return null;
  const versteckt = Math.max(0, liste.length - SICHTBARE_TOASTS_MAX);
  const sichtbare = versteckt > 0 ? liste.slice(-SICHTBARE_TOASTS_MAX) : liste;
  return (
    <div aria-live="polite" className="k-meldungen-host">
      {versteckt > 0 && (
        <div className="k-meldung-stapel-hinweis" data-testid="meldung-stapel-hinweis">
          +{versteckt} weitere {versteckt === 1 ? 'Meldung' : 'Meldungen'}
        </div>
      )}
      {sichtbare.map((m) => (
        <div
          key={m.id}
          data-testid={`meldung-${m.ton}`}
          // B82 #6: die Ruettel-Bewegung fuer Fehler-Toasts — eigene Bewegung
          // in `aura.css` (`.k-meldung-shake`), Begruendung im Kopfkommentar
          // dort.
          className={`k-meldung k-meldung-karte${m.ton === 'fehler' ? ' k-meldung-shake' : ''}`}
          style={{ ['--_ton' as string]: TON_FARBE[m.ton] }}
        >
          <span className="k-meldung-text">{m.text}</span>
          {m.aktion && (
            <KButton
              size="sm"
              tone="quiet"
              onClick={() => {
                m.aktion!.run();
                entferne(m.id);
              }}
            >
              {m.aktion.label}
            </KButton>
          )}
          <button aria-label="Meldung schliessen" className="k-meldung-schliessen" onClick={() => entferne(m.id)}>
            ✕
          </button>
        </div>
      ))}
      {/* B82 #7: reine Optik, kein zweiter Daten-Ort (Begründung bei `geister`
          oben) — eigenes `data-testid`, `aria-hidden` (die Ansage lief schon
          beim Erscheinen der echten Karte über `aria-live` oben), kein
          Schliessen-Knopf/keine Aktion, weil die Karte ohnehin schon auf dem
          Weg hinaus ist. */}
      {geisterListe.map((g) => (
        <div
          key={`geist-${g.id}`}
          data-testid="meldung-verlassend"
          aria-hidden="true"
          className="k-meldung-geist k-meldung--aus"
          style={{ ['--_ton' as string]: TON_FARBE[g.ton] }}
        >
          <span className="k-meldung-text">{g.text}</span>
        </div>
      ))}
    </div>
  );
}

// ── Bestätigung (ersetzt confirm) ────────────────────────────────────

interface BestaetigungAnfrage {
  titel: string;
  text?: string;
  bestaetigen?: string;
  gefaehrlich?: boolean;
  resolve: (ok: boolean) => void;
}

let anfrage: BestaetigungAnfrage | null = null;
const dialogHoerer = new Set<() => void>();

function dialogBenachrichtige(): void {
  for (const h of dialogHoerer) h();
}

/** Promise-basierter Bestätigungsdialog — `if (!(await bestaetigen({...}))) return;` */
export function bestaetigen(opts: {
  titel: string;
  text?: string;
  bestaetigen?: string;
  gefaehrlich?: boolean;
}): Promise<boolean> {
  return new Promise((resolve) => {
    anfrage?.resolve(false); // eine offene Anfrage aufs Mal
    anfrage = { titel: opts.titel, resolve, ...(opts.text ? { text: opts.text } : {}), ...(opts.bestaetigen ? { bestaetigen: opts.bestaetigen } : {}), ...(opts.gefaehrlich ? { gefaehrlich: true } : {}) };
    dialogBenachrichtige();
  });
}

function dialogAbonniere(cb: () => void): () => void {
  dialogHoerer.add(cb);
  return () => dialogHoerer.delete(cb);
}

/**
 * Host — einmal in der Shell mounten. Esc = abbrechen.
 *
 * E-K5 (`docs/V0812-SPEZ.md`, Sanktion 4, 21.07.2026, Bauagenten-Fund): der
 * neue Phasen-«Transformieren»-Weg ruft `bestaetigen()` erstmals AUS einem
 * bereits offenen Panel heraus (Projekt-Einstellungen). Ohne `createPortal`
 * rendert dieser Host irgendwo im normalen React-Baum (unter `App.tsx`s
 * `.app-wurzel`) — `aura.css`s `#root { position: relative; z-index: 1; }`
 * (dort für den Papier-Korn-Hintergrund `body::before` nötig) spannt damit
 * einen eigenen Stacking-Context auf: JEDES `position:fixed`-Kind von
 * `#root`, egal wie hoch sein EIGENER `z-index`, bleibt auf Rang «1»
 * gegenüber Body-Geschwistern gefangen. `Einstellungen.tsx`s Scrim portalt
 * dagegen direkt nach `document.body` (`z-index:250`) — gewann darum immer,
 * `bestaetigung-nein`/`-ja` waren unklickbar («subtree intercepts pointer
 * events»). Ein höherer `zIndex` allein (erster, unzureichender Versuch:
 * 210→900) behebt das NICHT, weil er nur INNERHALB des `#root`-Stacking-
 * Context zählt. Richtiger Fix: derselbe `createPortal(..., document.body)`-
 * Weg wie `Einstellungen.tsx` — dann vergleicht der Browser die z-index-Werte
 * wirklich auf oberster Ebene, `900` schlägt jeden heute existierenden
 * INTERAKTIVEN Overlay (`kosmo-panel.css`s `.kp-export-scrim`/
 * `.kp-vollbild-scrim` 500 sind die nächsthöchsten; die beiden Overlays über
 * 900 — `kosmo-feedback.css` 2000, `cursor-ebene.css` ~2.1 Mrd. — sind
 * `pointer-events:none` und blockieren ohnehin keinen Klick).
 */
export function KBestaetigung() {
  const offen = useSyncExternalStore(dialogAbonniere, () => anfrage, () => anfrage);
  if (!offen) return null;
  const schliesse = (ok: boolean) => {
    offen.resolve(ok);
    anfrage = null;
    dialogBenachrichtige();
  };
  return createPortal(
    <div
      role="dialog"
      aria-modal
      aria-label={offen.titel}
      data-testid="bestaetigung"
      className="k-dialog-scrim k-bestaetigung-scrim"
      onKeyDown={(e) => e.key === 'Escape' && schliesse(false)}
      style={{ zIndex: 900 }}
      onClick={() => schliesse(false)}
    >
      <div
        className="k-dialog-box k-skalieren-ein k-dialog k-bestaetigung-box"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="k-titel k-bestaetigung-titel">{offen.titel}</div>
        {offen.text && <div className="k-bestaetigung-text">{offen.text}</div>}
        <div className="k-bestaetigung-aktionen">
          <KButton size="sm" tone="ghost" data-testid="bestaetigung-nein" onClick={() => schliesse(false)}>
            Abbrechen
          </KButton>
          <KButton
            size="sm"
            tone={offen.gefaehrlich ? 'danger' : 'accent'}
            data-testid="bestaetigung-ja"
            autoFocus
            onClick={() => schliesse(true)}
          >
            {offen.bestaetigen ?? 'Bestätigen'}
          </KButton>
        </div>
      </div>
    </div>,
    document.body,
  );
}
