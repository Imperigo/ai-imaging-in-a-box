import {
  useRef,
  useState,
  type ButtonHTMLAttributes,
  type HTMLAttributes,
  type InputHTMLAttributes,
  type Ref,
  type ReactNode,
} from 'react';
import { KIcon } from './icons';

/**
 * KField/KInput/KChip/KToolbar/KToolGruppe (W0, UI-KONZEPT-065 §3) — ersetzt
 * die 10 lokalen `inputStyle`-Konstanten und die drei Badge-Implementierungen.
 */

// ── KField ──────────────────────────────────────────────────────────

export interface KFieldProps {
  label: string;
  hinweis?: string;
  fehler?: string;
  children: ReactNode;
  'data-testid'?: string;
}

/** Label über dem Kind; Hinweis ODER Fehler darunter (Fehler hat Vorrang). */
export function KField({ label, hinweis, fehler, children, ...rest }: KFieldProps) {
  return (
    <div className="k-field" {...rest}>
      <span className="k-field-label">{label}</span>
      {children}
      {fehler !== undefined ? (
        <span className="k-field-fehler">{fehler}</span>
      ) : hinweis !== undefined ? (
        <span className="k-field-hinweis">{hinweis}</span>
      ) : null}
    </div>
  );
}

// ── KInput ──────────────────────────────────────────────────────────

export interface KInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  size?: 'sm' | 'md';
  /** Mono-Variante (`--k-font-mono`) für Masse/Werte. */
  mono?: boolean;
  /**
   * NEU (v0.8.0B / P2, Spez §3 B-35) — `command`: Mono-Kommandozeile, 48px,
   * optionaler ⌘-Kbd-Chip (`kbd`-Prop). Additiv: bestehende Aufrufer ohne
   * `variant` rendern weiterhin GENAU ein `<input>`, byte-gleich zu vorher.
   */
  variant?: 'default' | 'command';
  /** Sichtbarer Tastenkürzel-Chip, NUR bei `variant="command"` (z.B. "⌘K"). */
  kbd?: string;
  /**
   * NEU (B20, 17.09.2026) — durchgereicht an das `<input>`. `InputHTMLAttributes`
   * kennt `ref` nicht (das steht in `ClassAttributes`), darum hier ausdrücklich;
   * rein additiv, kein bestehender Aufrufer setzt es. Gebraucht wird es heute
   * nur von `KNumberField` (s. dort `abgeleitet`).
   */
  ref?: Ref<HTMLInputElement>;
}

export function KInput({ size = 'md', mono = false, variant = 'default', kbd, className, ...rest }: KInputProps) {
  const klassen = [
    'k-input',
    `k-input--${size}`,
    mono || variant === 'command' ? 'k-input--mono' : '',
    variant === 'command' ? 'k-input--command' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');
  if (variant === 'command') {
    return (
      <span className="k-input-wrap k-input-wrap--command">
        <input {...rest} className={klassen} />
        {kbd !== undefined && (
          <span className="k-input-kbd" aria-hidden="true">
            {kbd}
          </span>
        )}
      </span>
    );
  }
  return <input {...rest} className={klassen} />;
}

// ── KNumberField ────────────────────────────────────────────────────

export interface KNumberFieldProps
  extends Omit<
    InputHTMLAttributes<HTMLInputElement>,
    'size' | 'value' | 'defaultValue' | 'type' | 'onChange' | 'onBlur' | 'onKeyDown'
  > {
  /** Der aktuelle Modellwert — NICHT der zuletzt getippte Text. Das Feld ist
   *  absichtlich unkontrolliert, s. Kopfkommentar der Komponente unten. */
  value: number;
  /** Wird NUR bei einer echten, gültigen, GEÄNDERTEN Zahl gerufen (nach
   *  Blur oder Enter) — nie bei leerem Feld, nie bei unverändertem Wert.
   *  Darf werfen (z. B. eine Kernel-Ablehnung) — das Feld fängt das ab,
   *  s. Kommentar bei `onBlur` unten. */
  onCommit: (next: number) => void;
  /** Einheit/Suffix, z. B. "mm", "°" — optional, rendert nichts, wenn nicht
   *  gesetzt (nicht jede Fundstelle hat eine sichtbare Einheit). */
  suffix?: string;
  /** Klasse für den Suffix-`<span>`, unabhängig von `className` (das Feld
   *  selbst). Nur wirksam, wenn `suffix` gesetzt ist. */
  suffixClassName?: string;
  size?: 'sm' | 'md';
  /** Mono-Ziffern (`--k-font-mono`) — Default AN, wie bei jedem Mass/Wert;
   *  abschaltbar für den seltenen Fall, dass ein Aufrufer es nicht will. */
  mono?: boolean;
  /**
   * NEU (B20, 17.09.2026) — «der angezeigte Wert ist ABGELEITET, nicht
   * gesetzt». Nur dort setzen, wo die Zahl im Feld auch OHNE Eingabe dasteht:
   * eine Hausregel, eine Rundung, eine Einheiten-Umrechnung, ein Fallback-
   * Default. Dann ist das Eintippen genau dieser Zahl eine BESTELLUNG («setz
   * das ausdrücklich fest»), kein Nichts — und `onCommit` läuft auch bei
   * `v === value`.
   *
   * DEFAULT `false`, und das ist Absicht: für die 47 gemessenen Fundstellen,
   * die ein Modellfeld 1:1 zeigen, bleibt «unverändert = kein Commit» richtig
   * (leere Schreibvorgänge, sinnlose Undo-Schritte). Die Zusicherung dazu
   * steht in `test/zahlfeld-f3-f4.test.tsx` und bleibt unangetastet.
   *
   * WAS ES NICHT TUT: bei jedem Verlassen schreiben. Gezählt wird die EINGABE
   * (nativer `input`-Lauscher), nicht der Fokuswechsel — blosses Durchtabben
   * bleibt auch mit diesem Merkmal folgenlos. Sonst wäre aus der stummen
   * Eingabe ein stiller Schreibvorgang geworden, nur andersherum.
   *
   * WER ES SETZEN MUSS, steht nicht hier: die betroffenen Felder liegen in
   * `Inspector.tsx` (Laufrichtung), `DesignWorkspace.tsx` (Ziel-GF),
   * `KvPanel.tsx` (Prozentwerte) und `PublishWorkspace.tsx` (Bildbreite) —
   * fremde Dateien, eigener Entscheid je Feld.
   */
  abgeleitet?: boolean;
}

/**
 * KNumberField (v0.1.2, Auftrag Z1 — docs/UI-UX-2026-09-08-FEHLER-DATENVERLUST.md
 * F3/F4) — EINE Bauart für ein Zahlfeld, dessen Commit ein Kernel/Modell
 * ablehnen kann, statt sie an jeder der heute >100 Fundstellen im Repo
 * (`Inspector.tsx`s frühere `NumberField` zuerst, seither hierher delegiert)
 * erneut von Hand abzuschreiben. Zwei unabhängige Fehler, beide hier EINMAL
 * behoben:
 *
 * F4 — `Number('')` ist `0`, `Number.isFinite(0)` ist wahr: ein geleertes
 * Feld ist keine Eingabe, keine Null. Der Leerfall wird darum VOR jeder
 * Umwandlung abgefangen und committet nichts (Gegenprobe: eine ECHT
 * eingegebene "0" bleibt eine gültige, committende Eingabe — sonst würde der
 * Fix den gültigen Fall miterschlagen).
 *
 * F3 — lehnt der Aufrufer/Kernel einen Wert ab (Exception oder schlicht kein
 * Zustands-Update), bleibt `value` unverändert. Das Feld ist ABSICHTLICH
 * unkontrolliert (`defaultValue`, kein `value`/`onChange`) — ein
 * kontrolliertes Feld würde bei JEDEM Tastenanschlag committen, nicht erst
 * beim Abschluss der Eingabe. Bliebe `value` gleich, bliebe ohne Gegenmass-
 * nahme auch `key` gleich, und React würde das Feld NICHT neu montieren —
 * der abgelehnte Text stünde sichtbar weiter da, obwohl sich am Modell
 * nichts geändert hat. `tick` ist der einzige eigene Zustand und dient NUR
 * dazu, das Feld nach JEDEM Blur-Versuch neu zu montieren — committet,
 * geworfen, unversucht (leer) oder unnötig (unverändert), macht keinen
 * Unterschied. `key={`${value}-${tick}`}` deckt beide Richtungen ab: ändert
 * sich `value` (Commit gelang), baut React ohnehin neu; bleibt er GLEICH
 * (F3-Ablehnung oder F4-Leerfall), erzwingt `tick` den Neubau trotzdem, und
 * `defaultValue={value}` zeigt danach garantiert wieder den echten
 * Modellwert, nie den zuletzt getippten oder abgelehnten Text.
 *
 * B20 (17.09.2026) — `abgeleitet`: die dritte, ABSCHALTBARE Regel neben F3/F4.
 * Anlass ist ein gemessener Schaden, kein Geschmack (73-BEFUNDE-OHNE-BESITZER
 * §18/§20): das Laufrichtungsfeld einer Decke zeigt die AUFGELÖSTE Achse — bei
 * 6 × 4 m sagt die Hausregel «der Balken nimmt den kürzeren Weg» 90°. Ein
 * unabhängiger Prüfer tippte genau diese 90 ein, `v !== value` war falsch, es
 * geschah nichts, und er hielt die ganze Fähigkeit für kaputt; sie wurde
 * deshalb nicht mitgezählt. Gemessen wirkt sie: 0° gegen 90° bewegt an einer
 * Brettstapeldecke rund 10 % der Bildpunkte. Ein Feld, das eine Eingabe stumm
 * verschluckt, ist Muster 11 der Anleitung in seiner unauffälligsten Form — es
 * sieht nicht kaputt aus, es tut nur nichts.
 *
 * WARUM NICHT «IMMER COMMITTEN»: gemessen an der ganzen Suite kostet das die
 * bestehende Zusicherung «ein unveränderter Wert ist kein Commit-Anlass»
 * (`test/zahlfeld-f3-f4.test.tsx`) — und die ist für die 47 Fundstellen
 * richtig, die ein Modellfeld 1:1 zeigen. Eine Zusicherung wird nicht
 * aufgeweicht, damit eine Änderung durchgeht.
 *
 * WARUM «BERÜHRT» UND NICHT «VERLASSEN»: schriebe ein `abgeleitet`-Feld bei
 * JEDEM Blur, machte schon das Durchtabben einen stillen Schreibvorgang samt
 * Undo-Schritt. `beruehrt` zählt darum die Eingabe. GEMESSEN, NICHT VERMUTET
 * (Sonde): tippt man denselben Text, den das Feld schon zeigt, sieht ein
 * NATIVER `input`-Lauscher das Ereignis (1×), Reacts `onChange` sieht es NICHT
 * (0×) — Reacts Wert-Merker unterdrückt es. `onChange` wäre hier also genau im
 * gesuchten Fall blind gewesen; darum der Lauscher am Element.
 */
export function KNumberField({
  value,
  onCommit,
  suffix,
  suffixClassName,
  size = 'sm',
  mono = true,
  abgeleitet = false,
  className,
  ...rest
}: KNumberFieldProps) {
  const [tick, setTick] = useState(0);
  // Nur bei `abgeleitet` gebraucht; sonst bleibt der Pfad unten unverändert.
  const beruehrt = useRef(false);
  const merker = (el: HTMLInputElement | null) => {
    if (el === null) return;
    const auf = () => {
      beruehrt.current = true;
    };
    el.addEventListener('input', auf);
    // React 19 ruft die Rückgabe eines Ref-Callbacks als Aufräumfunktion —
    // gebraucht, weil `key` das `<input>` nach JEDEM Blur neu montiert.
    return () => el.removeEventListener('input', auf);
  };
  return (
    <>
      <KInput
        {...rest}
        size={size}
        mono={mono}
        type="number"
        key={`${value}-${tick}`}
        defaultValue={value}
        className={className}
        {...(abgeleitet ? { ref: merker } : {})}
        onBlur={(e) => {
          const roh = e.target.value.trim();
          // F4: s. Kopfkommentar — der Leerfall wird VOR jeder Umwandlung
          // abgefangen, schreibt nichts. Gilt auch mit `abgeleitet`: ein
          // geleertes Feld ist keine Eingabe, keine Null.
          if (roh !== '') {
            const v = Number(roh);
            // B20: `abgeleitet` ersetzt den Vergleich NICHT durch «immer»,
            // sondern durch «wurde in dieses Feld etwas eingegeben» — s.
            // Kopfkommentar. Ohne das Merkmal bleibt die Zeile, was sie war.
            if (Number.isFinite(v) && (v !== value || (abgeleitet && beruehrt.current))) {
              // F3-Härtung: ein werfender `onCommit` darf den Neubau unten
              // nicht verhindern — sonst bliebe der abgelehnte Text stehen,
              // obwohl der Aufrufer die Ablehnung längst kennt. Das Melden
              // (Toast/Log) ist Sache des Aufrufers (s. `Inspector.tsx`s
              // `set()`), nicht dieses Feldes — hier zählt nur: nie stehen
              // bleiben.
              try {
                onCommit(v);
              } catch {
                /* bewusst leer, s. Kommentar oben */
              }
            }
          }
          // B20: der Berührt-Merker gilt je Aufenthalt im Feld, nicht je
          // Lebenszeit der Komponente — sonst wirkte `abgeleitet` genau
          // einmal und danach nie wieder (Gegenprobe «ZWEIMAL HINTEREINANDER»
          // in `b20-zahlfeld-abgeleitet.test.tsx`).
          beruehrt.current = false;
          // F3: nach JEDEM Blur-Versuch — committet, abgelehnt, leer oder
          // unverändert — das Feld auf den (dann aktuellen) Modellwert
          // zwingen, statt möglichen abgelehnten/leeren Text stehen zu
          // lassen.
          setTick((t) => t + 1);
        }}
        onKeyDown={(e) => e.key === 'Enter' && (e.target as HTMLInputElement).blur()}
      />
      {suffix !== undefined && <span className={suffixClassName}>{suffix}</span>}
    </>
  );
}

// ── KChip ───────────────────────────────────────────────────────────

export interface KChipProps {
  children: ReactNode;
  /** Zeichenfarbe (CSS-Farbwert) — NIE eine Füllfläche (ausser `tone:'fuellung'`,
   * die dann ausschliesslich `--k-accent-wash` verwendet, nicht den `hue`-Ton). */
  hue?: string;
  size?: 'sm' | 'md';
  tone?: 'linie' | 'fuellung';
  /**
   * NEU (v0.8.0B / P2, Spez §3 B-37) — additive Varianten. Default `'chip'`
   * rendert BYTE-GLEICH die bisherige `<span className="k-chip …">` (Alt-
   * Vertrag unverändert). `'status'` = Status-Chip (radius 999, Mono, 2px/8px
   * Padding, gleiche `hue`/`tone`-Optik). `'geschlossen'` = Closed-Chip
   * («+ NAME»), gestrichelter Glass-Rand, Mono 9.5px — rendert einen
   * `<button>` (klickbar, öffnet das eingeklappte Panel wieder), darum
   * eigenes `onClick` statt `onRemove`.
   */
  variant?: 'chip' | 'status' | 'geschlossen';
  onRemove?: () => void;
  onClick?: () => void;
  'data-testid'?: string;
}

export function KChip({ children, hue, size = 'md', tone = 'linie', variant = 'chip', onRemove, onClick, ...rest }: KChipProps) {
  const farbe = hue ?? 'var(--k-ink-soft)';

  if (variant === 'geschlossen') {
    return (
      <button type="button" className="k-chip-geschlossen k-uebergang-schnell" onClick={onClick} {...rest}>
        <span className="k-chip-geschlossen-plus" aria-hidden="true">
          +
        </span>
        {children}
      </button>
    );
  }

  if (variant === 'status') {
    return (
      <span className={`k-chip k-status-chip k-status-chip--${size}`} style={{ color: farbe, borderColor: farbe }} {...rest}>
        {children}
      </span>
    );
  }

  return (
    <span
      className={`k-chip k-chip--${size} k-chip--${tone}`}
      style={{ color: farbe, borderColor: farbe }}
      {...rest}
    >
      {children}
      {onRemove !== undefined && (
        <button type="button" aria-label="entfernen" className="k-chip-entfernen" onClick={onRemove}>
          <KIcon name="schliessen" size={14} />
        </button>
      )}
    </span>
  );
}

// ── KToolbar / KToolGruppe ──────────────────────────────────────────

export interface KToolbarProps extends HTMLAttributes<HTMLDivElement> {
  /** Kleineres Padding für Stationen mit wenig Platz. */
  dicht?: boolean;
}

/** EINE Werkzeugzeile — Gruppen (KToolGruppe) darin werden durch Hairlines
 * getrennt; Überlauf gehört in ein KMenu «Mehr», nicht in eine zweite Zeile. */
export function KToolbar({ dicht = false, className, ...rest }: KToolbarProps) {
  const klassen = ['k-toolbar', dicht ? 'k-toolbar--dicht' : '', className].filter(Boolean).join(' ');
  return <div className={klassen} {...rest} />;
}

export interface KToolGruppeProps extends HTMLAttributes<HTMLDivElement> {
  /** Kleinbeschriftung (`--k-t-xs`, VERSAL, `--k-ink-faint`) über der Gruppe. */
  label?: string;
}

export function KToolGruppe({ label, children, className, ...rest }: KToolGruppeProps) {
  const klassen = ['k-toolgruppe', className].filter(Boolean).join(' ');
  return (
    <div className={klassen} {...rest}>
      {label !== undefined && <span className="k-toolgruppe-label">{label}</span>}
      {children}
    </div>
  );
}

// ── KWerkzeugKreis ──────────────────────────────────────────────────

/**
 * KWerkzeugKreis (v0.8.0B / P2, Spez §3 B-39) — das Kreis-Werkzeug der
 * Rail-/Toolbar-Grammatik: 32px-Kreis, Icon-Stroke 1.75 (Standard-`KIcon`),
 * aktiv entweder INVERTIERT (Fläche/Text getauscht) oder 1.5px
 * Akzent-/Rollenrand + 4px-Rollenpunkt (bottom, Regel 1: Rollenfarbe nur als
 * Punkt/Hairline, nie flächig). Einsatz im Rail/BodenDock ist W3-Scope, hier
 * nur die Komponente + Tests.
 */
export interface KWerkzeugKreisProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  aktiv?: boolean;
  /** Rollen-/Modusfarbe (CSS-Farbwert) für Rand + Punkt bei `aktiv`. Default `--k-accent`. */
  rolle?: string;
  /** true = aktiv zeigt eine invertierte Fläche statt Rand+Punkt. */
  invertiert?: boolean;
  'data-testid'?: string;
}

export function KWerkzeugKreis({ aktiv = false, rolle, invertiert = false, className, style, children, ...rest }: KWerkzeugKreisProps) {
  const klassen = [
    'k-werkzeug-kreis',
    'k-druck',
    // D-8 (E-8 A): 32px-Kreis bleibt optisch exakt, die Trefferzone wächst
    // unsichtbar auf 44 (`.k-touch-ziel::after`, aura.css). Kollisionsfrei:
    // der Aktiv-Punkt ist ein <span>, kein `::after`; `.k-akzent-eckpunkt`
    // trägt diese Komponente nirgends (Kollisionsregel E-8).
    'k-touch-ziel',
    aktiv ? (invertiert ? 'k-werkzeug-kreis--invertiert' : 'k-werkzeug-kreis--aktiv') : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');
  return (
    <button
      type="button"
      aria-pressed={aktiv}
      className={klassen}
      style={rolle !== undefined ? { ['--_rolle' as string]: rolle, ...style } : style}
      {...rest}
    >
      {children}
      {aktiv && !invertiert && <span className="k-werkzeug-kreis-punkt" aria-hidden="true" />}
    </button>
  );
}
