import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode, Ref } from 'react';

/**
 * Aura-Basiskomponenten — bewusst schlank, CSS-Variablen-getrieben.
 * Alles Weitere wächst mit der App; keine Komponenten auf Vorrat.
 */

type Tone = 'accent' | 'quiet' | 'ghost' | 'danger';

export interface KButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  tone?: Tone;
  /**
   * NEU (v0.8.0B / P2, Spez §3 B-34) — `lg` (48px) additiv zu `sm`(32px)/
   * `md`(40px); bestehende Aufrufer ohne `size` bleiben bei `md`, byte-gleich.
   *
   * NEU (B89, `docs/AUFTRAG-B89-ZIELGROESSEN-GEMISCHT.md`) — `touch` (44px)
   * additiv. `.k-btn-sm` bleibt bei 32px und byte-gleich, WCAG-Tap-Target
   * (≥44px) gilt nur dort, wo ein Finger bedient — die Grenze verläuft nach
   * Bedienweg, nicht nach Datei (Owner-Entscheid 02.09.2026, «gemischt»).
   * `tools/zielgroessen-gate.mjs` prüft, dass die Grösse `touch` ausschliesslich
   * unter einem `island`-Ordner in `apps/kosmo-orbit/src` steht und dort keine
   * Stelle mit Grösse `sm` mehr vermischt liegt.
   */
  size?: 'sm' | 'md' | 'lg' | 'touch';
  /**
   * NEU (P-TASTATUR-LUECKEN Teil 2, 09.09.2026) — der Knopf war von aussen
   * **nicht ansprechbar**. Das klingt nach einer Feinheit und ist keine: wer
   * den Fokus gezielt auf einen Knopf setzen will (nach dem Schliessen eines
   * Fensters zurueck auf seinen Ausloeser, beim Rollfokus, nach einer
   * Fehlermeldung), braucht eine Handhabe darauf — und ohne sie bleibt
   * genau die Sorte Tastaturarbeit unmoeglich, an der dieses Vorhaben
   * gerade baut.
   *
   * **Kein `forwardRef`.** In React 19 ist `ref` fuer Funktionskomponenten
   * eine gewoehnliche Prop; sie wandert ueber `...rest` an den `<button>`.
   * Der frueher noetige `forwardRef`-Umweg (samt geaenderter
   * Komponenten-Identitaet und eigenem Anzeigenamen) waere hier
   * ueberfluessige Mechanik — gemeldet worden war «forwardRef fehlt», die
   * richtige Antwort ist eine Typzeile.
   */
  ref?: Ref<HTMLButtonElement>;
}

/**
 * v0.6.6 MOTION-KONZEPT-066 §3: Inline-Styles → CSS-Klassen (`.k-btn` +
 * `.k-btn-<tone>` + `.k-btn-<size>` in `aura.css`) + `.k-druck` (Knopfdruck-
 * simulation, `aura.css`). DOM-Struktur (ein `<button>`), Props-API,
 * `data-testid`-Durchreichung (via `...rest`) und disabled-Verhalten bleiben
 * identisch — nur die Style-QUELLE wandert, die Optik ist byte-gleich aus
 * den vorherigen Inline-Werten übernommen (siehe Git-Historie dieser Datei).
 *
 * v0.8.0B / P2 (Spez §3 B-34): die vier `TONE_KLASSE`-Klassennamen
 * (`k-btn-accent/-quiet/-ghost/-danger`) bleiben BYTE-GLEICH — nur ihre
 * CSS-Deklarationen in `aura.css` wechseln auf das 1px-Border-Prinzip
 * (accent = Wash+Line+Text, quiet = Glass, ghost = transparent→Hover,
 * danger = 12%/45%). `e2e/kurztasten-pan.spec.ts` prüft `k-btn-accent` per
 * `classList.contains` — der Klassenname selbst ist ein Vertrag.
 */
const TONE_KLASSE: Record<Tone, string> = {
  accent: 'k-btn-accent',
  quiet: 'k-btn-quiet',
  ghost: 'k-btn-ghost',
  danger: 'k-btn-danger',
};

export function KButton({ tone = 'quiet', size = 'md', className, style, disabled, ...rest }: KButtonProps) {
  const klassen = ['k-btn', TONE_KLASSE[tone], `k-btn-${size}`, 'k-druck', className].filter(Boolean).join(' ');
  return <button {...rest} disabled={disabled} className={klassen} style={style} />;
}

export interface PanelProps extends HTMLAttributes<HTMLDivElement> {
  pad?: boolean;
  /** Dieselbe Luecke wie bei `KButton` oben, dieselbe Antwort: eine Flaeche,
   *  die man nicht ansprechen kann, laesst sich weder scrollen noch messen
   *  noch als Fokusfalle verankern (`fokusfalle.ts` braucht genau so eine
   *  Handhabe). */
  ref?: Ref<HTMLDivElement>;
}

export function Panel({ pad = true, style, ...rest }: PanelProps) {
  return (
    <div
      {...rest}
      style={{
        background: 'var(--k-surface)',
        border: '1px solid var(--k-line)',
        borderRadius: 'var(--k-radius-md)',
        padding: pad ? 14 : 0,
        ...style,
      }}
    />
  );
}

export function Hairline({ vertical = false }: { vertical?: boolean }) {
  return (
    <div
      aria-hidden
      style={
        vertical
          ? { width: 1, alignSelf: 'stretch', background: 'var(--k-line)' }
          : { height: 1, width: '100%', background: 'var(--k-line)' }
      }
    />
  );
}

/** Alias-Hinweis (W0, UI-KONZEPT-065 §3): `KChip` (`field.tsx`) konsolidiert
 * Badge/Statusleisten-Chip/orbit-badge für NEUEN Code (Rand statt Punkt+Fläche,
 * Grössen, `onRemove`, `tone`). `Badge` selbst bleibt UNVERÄNDERT bestehen —
 * Bestandsschutz, viele Stationen binden ihn bereits ein. */
export interface BadgeProps {
  children: ReactNode;
  hue?: string;
}

export function Badge({ children, hue }: BadgeProps) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        fontSize: 11,
        fontWeight: 'var(--k-gewicht-stark)',
        letterSpacing: '0.05em',
        textTransform: 'uppercase',
        color: hue ?? 'var(--k-ink-faint)',
      }}
    >
      <span
        aria-hidden
        style={{
          width: 6,
          height: 6,
          borderRadius: 999,
          background: hue ?? 'var(--k-ink-faint)',
        }}
      />
      {children}
    </span>
  );
}

/** Massangabe in Mono mit tabellarischen Ziffern. */
export function Measure({ children, style }: { children: ReactNode; style?: React.CSSProperties }) {
  return (
    <span style={{ fontFamily: 'var(--k-font-mono)', fontSize: '12.5px', ...style }}>{children}</span>
  );
}

/** Werkplan-Karteikarte: geschnittene Ecke + Mono-Laufnummer (Referenzposter). */
export function Karteikarte({
  nr,
  style,
  children,
  ...rest
}: HTMLAttributes<HTMLDivElement> & { nr?: number }) {
  return (
    <div {...rest} className="k-karte" style={{ display: 'flex', alignItems: 'stretch', ...style }}>
      {nr !== undefined && (
        <div
          aria-hidden
          style={{
            fontFamily: 'var(--k-font-mono)',
            fontWeight: 'var(--k-gewicht-betont)',
            fontSize: 14,
            padding: '10px 8px 0 10px',
            borderRight: '1px solid var(--k-line-strong)',
            minWidth: 42,
            textAlign: 'right',
            color: 'var(--k-ink)',
          }}
        >
          {String(nr).padStart(2, '0')}.
        </div>
      )}
      <div style={{ padding: '10px 12px', flex: 1, minWidth: 0 }}>{children}</div>
    </div>
  );
}

/** D-7 (E-5, `GESTALTUNGS-ENTSCHEIDE-2026-08-10.md`) — Passermarke ⌖ als
 * Inline-SVG, NIE als Text-Glyph (U+2316 ist in Lato/Plex nicht verlässlich
 * abgedeckt — der System-Fallback sähe je Gerät anders aus). Kreis +
 * Fadenkreuz, Strichstärke 1, `currentColor`; die Farbe (--k-ink-faint) und
 * das Druck-Verbot (`@media print`) trägt `.k-passermarke` in aura.css.
 * Nur die zwei sanktionierten Grössen sind baubar: 12 (Listenkopf eines
 * Karteikarten-Bestands, genau 1 Stück, vor dem `.k-label`) und 16
 * (Messrahmen der Leerzustände, max. 2, diagonal gegenüber). Nie im
 * Plan-Viewport, nie in einem Export, nie mehr als 2 pro Ansicht. */
export function Passermarke({ size = 12, style }: { size?: 12 | 16; style?: React.CSSProperties }) {
  const c = size / 2;
  return (
    <svg
      className="k-passermarke"
      data-testid="k-passermarke"
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      aria-hidden="true"
      style={style}
    >
      <circle cx={c} cy={c} r={c - 2.5} fill="none" stroke="currentColor" strokeWidth="1" />
      <path d={`M${c} .5V${size - 0.5}M.5 ${c}H${size - 0.5}`} stroke="currentColor" strokeWidth="1" />
    </svg>
  );
}

/** Abstand der gestrichelten Rahmenlinie vom Messrahmen-Container (px) —
 * EINE Quelle für Zeichnung UND Masskettenzahl (Wahrheitsregel E-6). */
const MESSRAHMEN_RAND = 10;
/** Ab dieser Container-Höhe trägt der Messrahmen seine Zierde (Passermarke +
 * Masskette): darunter fehlt dem Blatt die Höhe für die vertikale
 * Beschriftung — und Klein-Instanzen (Vorschau-Kacheln, 80–140px) blieben
 * sonst eine Zier-Wiederholung weit über dem Mass «max. 2 pro Ansicht». */
const MESSRAHMEN_ZIER_AB = 160;
/** Breite der Spalte am rechten Rand, die die Zier-Masskette belegt (px):
 * `right: 22` plus die Zeilenbreite der senkrechten Beschriftung (gemessen
 * 14 px). B133 (11.09.2026): die Beschriftung des Rahmens steht MITTIG, sie
 * muss diese Spalte darum auf BEIDEN Seiten freihalten — sonst laeuft sie in
 * die Masszahl hinein, sobald der Rahmen schmal wird. Gemessen im Ablagefeld
 * der Infotafel (178x178): 9 px Ueberschnitt bei `maxWidth: 70%`, weil 15 %
 * von 178 nur 27 px sind. */
const MESSRAHMEN_MASSSPALTE = 36;

/** Bauzeichnungs-Leerzustand: Messrahmen mit Schnittmarken, Achsenkreuz und
 * Mono-Beschriftung — Gegenstand (noch) nicht vorhanden, Rahmen vermasst.
 *
 * D-7 (E-5/E-6): ab 160px Höhe trägt der Rahmen EINE Passermarke (16×16,
 * oben links — der zweite, diagonale Platz unten rechts bleibt frei) und
 * die Zier-Masskette rechts. Wahrheitsregel E-6: die Zahl ist das reale
 * Mass der gestrichelten Rahmenlinie (`height − 2·MESSRAHMEN_RAND`, px),
 * die Masslinie spannt exakt diese Strecke; bei nicht-numerischer Höhe
 * (`height="100%"`) entfällt die Masskette ganz — eine geschätzte Zahl
 * wäre eine erfundene, und erfundene Masse sind verboten. Vermasst wird
 * App-Geometrie (das Blatt), nie Bauwerks-Geometrie. */
export function Messrahmen({
  caption,
  height = 200,
  style,
}: {
  caption: string;
  height?: number | string;
  style?: React.CSSProperties;
}) {
  const zier = typeof height === 'number' && height >= MESSRAHMEN_ZIER_AB;
  const rahmenHoehe = typeof height === 'number' ? height - 2 * MESSRAHMEN_RAND : null;
  const mark = (rot: number, pos: React.CSSProperties) => (
    <svg aria-hidden width="14" height="14" style={{ position: 'absolute', ...pos, transform: `rotate(${rot}deg)` }}>
      <path d="M 13 6.5 H 6.5 V 13" fill="none" stroke="var(--k-technik)" strokeWidth="1" />
    </svg>
  );
  return (
    <div
      style={{
        position: 'relative',
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        ...style,
      }}
    >
      <div
        aria-hidden
        style={{ position: 'absolute', inset: MESSRAHMEN_RAND, border: '1px dashed var(--k-line-strong)' }}
      />
      {mark(0, { top: 0, left: 0 })}
      {mark(90, { top: 0, right: 0 })}
      {mark(270, { bottom: 0, left: 0 })}
      {mark(180, { bottom: 0, right: 0 })}
      {/* Achsenkreuz unten links */}
      <svg aria-hidden width="46" height="46" style={{ position: 'absolute', left: 20, bottom: 18 }}>
        <path d="M 6 40 V 10 M 6 10 l -3 5 h 6 z" fill="var(--k-technik)" stroke="var(--k-technik)" strokeWidth="1" />
        <path d="M 6 40 H 36 M 36 40 l -5 -3 v 6 z" fill="var(--k-technik)" stroke="var(--k-technik)" strokeWidth="1" />
        <text x="1" y="8" fontSize="8" fontFamily="var(--k-font-mono)" fill="var(--k-technik)">Z</text>
        <text x="39" y="43" fontSize="8" fontFamily="var(--k-font-mono)" fill="var(--k-technik)">X</text>
      </svg>
      {/* D-7 (E-5): die frühere 22×22-Passermarke in voller Tusche
          (rechts mittig) ist durch die kanonische Form ersetzt — 16×16,
          --k-ink-faint, oben links, druckfest per .k-passermarke. */}
      {zier && <Passermarke size={16} style={{ position: 'absolute', left: 16, top: 16 }} />}
      {/* D-7 (E-6): Zier-Masskette rechts — Masslinie von Rahmen-Oberkante
          zu Rahmen-Unterkante (exakt die Strecke, die die Zahl behauptet),
          Schrägstrich-Enden wie im Werkplan, Beschriftung in .k-label-
          Stimme, --k-ink-faint über .k-masskette, im Druck ausgeblendet. */}
      {zier && rahmenHoehe !== null && typeof height === 'number' && (
        <>
          <svg
            aria-hidden
            className="k-masskette"
            width="24"
            height={height}
            style={{ position: 'absolute', right: 0, top: 0 }}
          >
            <path
              d={`M8 ${MESSRAHMEN_RAND}V${height - MESSRAHMEN_RAND}`}
              stroke="currentColor"
              strokeWidth="1"
              fill="none"
            />
            <path
              d={`M5 ${MESSRAHMEN_RAND + 3}L11 ${MESSRAHMEN_RAND - 3}M5 ${height - MESSRAHMEN_RAND + 3}L11 ${
                height - MESSRAHMEN_RAND - 3
              }`}
              stroke="currentColor"
              strokeWidth="1"
              fill="none"
            />
          </svg>
          <span
            aria-hidden
            className="k-label k-masskette"
            style={{
              position: 'absolute',
              right: 22,
              top: '50%',
              writingMode: 'vertical-rl',
              transform: 'translateY(-50%) rotate(180deg)',
            }}
          >
            {rahmenHoehe} px
          </span>
        </>
      )}
      <div
        style={{
          fontFamily: 'var(--k-font-mono)',
          fontSize: 11.5,
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          color: 'var(--k-ink-soft)',
          textAlign: 'center',
          // 70 % bleibt die Regel fuer breite Rahmen; bei schmalen gewinnt die
          // Freihaltung der Masskette (+4 px Luft). Ohne Zier gibt es keine
          // Masszahl, dort bleibt es bei 70 %.
          maxWidth: zier
            ? `min(70%, calc(100% - ${2 * MESSRAHMEN_MASSSPALTE + 8}px))`
            : '70%',
        }}
      >
        {caption}
      </div>
    </div>
  );
}
