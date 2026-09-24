/**
 * KosmoOrbit Aura — Design-Tokens.
 *
 * Spiegel von aura.css — Änderungen IMMER zuerst dort. `aura.css` ist die
 * einzige Wahrheit (UI-KONZEPT-065 §2); dieses Modul liest ihre Werte NICHT
 * zur Laufzeit (kein CSS-Parser im Bundle), sondern hält sie als TS-Literale
 * nach — `packages/kosmo-ui/test/token-spiegel.test.ts` parst aura.css und
 * bricht mit einer sprechenden Meldung, sobald hier und dort etwas
 * auseinanderläuft. Wer eine Farbe/einen Radius/eine Skala ändert: zuerst
 * aura.css anfassen, dann hier den exakt gleichen Wert eintragen.
 *
 * Gestaltungshaltung (Owner-Mandat Q17–Q20): elegant, schlicht, für Architekten.
 * v0.7.3 D7 (Owner-Entscheid, Gestaltungs-Spez): Theme-PAAR Papier (hell) und
 * Kosmos/`orbit` (dunkel) — Tinte (`ink`) wurde ENTFERNT (Migration
 * `ink→orbit` in `App.tsx`, VOR dem `useState`). Standard-Akzent ist die
 * Teal-Familie (Papier `#3e96a2`, Kosmos `#57b6c2`) — wählbare Zweit-Akzente
 * (Kupfer, Signal, Blau, Grün) leben als `data-akzent`-Blöcke in aura.css.
 * Sekundär trägt jedes Modul einen eigenen, zurückhaltenden Farbton, der nur
 * in Zeichen, Badges und aktiven Zuständen erscheint — nie flächig.
 */

/** Kupfer/Terracotta — entspricht `[data-akzent='kupfer']` in aura.css. */
export const accent = {
  copper: '#C25E3A',
  copperDeep: '#A84B2B',
  copperBright: '#D9743F',
  copperWash: '#C25E3A22',
} as const;

/** Papier-Thema (`:root, [data-theme='paper']` in aura.css) — Hexwerte exakt gespiegelt. */
export const paper = {
  field: '#f5f3ee',
  surface: '#fbfaf6',
  raised: '#ffffff',
  ink: '#1a1815',
  inkSoft: '#5c574d',
  inkFaint: '#6b675c', // B138: war #8f897b, s. aura.css
  line: '#e4e0d6',
  lineStrong: '#c9c4b6',
  /** Standard-Akzent (kein `data-akzent` gesetzt) — Teal dunkel, v0.7.3 D7. */
  accent: '#3e96a2',
  accentInk: '#06141a',
  /**
   * v0.8.0B / W1 (Spez §1 B-26) — Flächenstufe Hover, Papier-Äquivalent.
   * Mittelwert zwischen `field` (#f5f3ee) und `line` (#e4e0d6): dunkler als
   * `raised`/`surface` (Hover braucht mehr Gewicht als die Ruhefläche),
   * heller als jede Linie. Kosmos geht bei Hover nach OBEN (heller, siehe
   * `orbit.hover`), Papier zwangsläufig nach UNTEN (dunkler) — `raised` ist
   * bereits reines Weiss, dort gibt es kein „heller" mehr.
   */
  hover: '#ede9e2',
} as const;

/** Semantische Töne — in beiden Themes lesbar (aura.css: paper-Werte, Referenz). */
export const semantic = {
  success: '#4e6d49',
  warning: '#a37b22',
  /**
   * v0.8.1 / P3 (Spez §4.3/C-16) — kanonisiert aus den vormals verstreuten
   * `var(--k-warning-wash, #f6f2e6)`/`var(--k-warning-line, #c9bfa0)`-
   * Fallback-Hexen (`design-panels.css` `.dp-hinweis`, `publish.css`).
   * Spiegelt `--k-warning-wash`/`--k-warning-line`, theme-invariant wie
   * `warning` selbst.
   */
  warningWash: '#f6f2e6',
  warningLine: '#c9bfa0',
  danger: '#a33d31',
  info: '#46617a',
} as const;

/**
 * Modul-Farbtöne — dezente Identität pro Werkzeug (nur Zeichen/Badges/Aktiv-Ring).
 * Deckt sich mit den `--k-mod-*`-Variablen in aura.css, plus Module, die
 * (noch) keine eigene aura-Variable haben (train/doc/sketch/speak/asset/dev)
 * — dort gilt dieser TS-Wert als Erstdefinition.
 */
export const moduleHue = {
  orbit: '#8f897b', // die Zentrale bleibt neutral
  design: '#c25e3a', // Entwerfen trägt die Markenfarbe
  draw: '#4e4a42', // Graphit — die Zeichnung
  data: '#46617a', // tiefes Blau — das Wissen
  vis: '#c79a3d', // Bernstein — das Licht
  publish: '#6f8b6a', // Salbei — das fertige Blatt
  prepare: '#7d5e78', // Pflaume — die Grundlagen
  kosmo: '#b06a8c', // Kosmo selbst: warmes Karmin-Rosé, die Stimme im Raum
  train: '#8c6d3f', // Ocker — das Lernen, Schicht um Schicht
  doc: '#5d7489', // Schiefer — Diagnose und Berichte
  sketch: '#96604a', // Sienna — der Stift auf Papier
  speak: '#4f7a7a', // Petrol — die Stimme im Raum
  asset: '#7a6a55', // Nussbaum — die Bibliothek der Dinge
  dev: '#5e6b52', // Tannengrün — die Werkstatt an der Software
  // v0.8.1 / P11 (docs/V081-SPEZ.md §7(a), C-29): Indigo — der Vertrauens-
  // Siegel-Ton fürs .kxp-Hyper-Modell + die Trust-Layer-Freigabe.
  trust: '#5b5a8a',
  // v0.8.1 / P14 (docs/V081-SPEZ.md §7(e), C-28/C-30): gedecktes Zinn —
  // der Export-Hub/KosmoPackage-Screen, der die sechs realen Formate + .kxp
  // an einem Ort bündelt.
  paket: '#6b7a8a',
  // P-SPEZ (`docs/KOSMOSPEZ-KONZEPT.md` §h7): KosmoSpez, das achte Haupttool
  // (Energie-/Klimadesign, Sonnenstudien). Endgültige Stationsfarbe war laut
  // Konzept ausdrücklich offen («wird mit ClaudeDesign bestimmt») — Owner-
  // Freigabe «KosmoSpez K37c UI-Sprache» (21.07.2026, ROADMAP 583,
  // `docs/owner-packages/2026-07-21-kosmospez-k37c/K37c-1_UI-Sprache.html`)
  // legt Spektralviolett fest: «Stationsfarbe: Spektralviolett #9C84C4 —
  // strikt getrennt von den Ergebnisfarben.» Löst den bisherigen
  // moosig-grauen Platzhalter ab (ROADMAP-Nachzug, kein Golden-Leser: `derive/`,
  // `plansvg.ts`, `stilblatt.ts` importieren kein `@kosmo/ui`/`tokens.ts`).
  spez: '#9C84C4',
} as const;

export type ModuleId = keyof typeof moduleHue;

export const typography = {
  /** UI-Schrift: präzise Grotesk über Systemstapel; Zahlen tabellarisch. */
  ui: "'Inter', 'SF Pro Text', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  /** Mass- und Wertangaben: Mono für Planlesbarkeit. */
  mono: "'IBM Plex Mono', ui-monospace, 'SF Mono', SFMono-Regular, Menlo, monospace",
  /**
   * Alte, feinere Anzeige-Skala (Legacy — vor der `type`-Skala unten
   * entstanden). Bleibt bestehen, damit keine bestehende Export-Form bricht;
   * neuer Code verwendet die `type`-Skala (spiegelt `--k-t-*`).
   */
  scale: {
    xs: '11px',
    sm: '12.5px',
    md: '14px',
    lg: '16px',
    xl: '20px',
    display: '28px',
  },
} as const;

/**
 * Typo-Skala (NEU, W0) — spiegelt `--k-t-xxs/-xs/-sm/-md/-lg/-plakat` aus
 * aura.css. Portlabels/Fussnoten/Chips (xs) bis Plakat-Versalien (plakat).
 * `xxs` (D-11, E-9 `GESTALTUNGS-ENTSCHEIDE-2026-08-10.md`) ist die feinste Stufe:
 * Insel-Werkzeugtitel, Badges, Raster-Meta.
 */
export const type = {
  xxs: '9px',
  xs: '10.5px',
  sm: '12px',
  md: '13.5px',
  lg: '16px',
  plakat: '20px',
} as const;

/**
 * Typo-Leiter nach oben (NEU, v0.8.0B / W1, Spez §1) — spiegelt
 * `--k-t-h3/-h2/-anzeige/-h1/-display/-code/-micro` aus aura.css.
 * Display/H-Ebenen NUR ausserhalb des CAD-Chromes (Onboarding, OrbitStart,
 * Report/Dossier, Leerzustände) — das CAD-Chrome bleibt bei `type` (der
 * kleinen Skala). `anzeige` (D-11, E-9) ist die grosse Instrumenten-Anzeige
 * zwischen h2 und h1: Stand-Zahlen der Inseln, Gruss-Titel.
 */
export const typeGross = {
  h3: '21px',
  h2: '28px',
  anzeige: '34px',
  h1: '42px',
  display: '60px',
  code: '13px',
  micro: '11px',
} as const;

/**
 * Sperrung (NEU, D-1, E-1 `GESTALTUNGS-ENTSCHEIDE-2026-08-10.md`) — spiegelt
 * `--k-sperrung/-eng/-titel` aus aura.css. Zwei Sperrwerte für `.k-label`
 * (freistehend/eingebettet) plus die enger begrenzte Titel-Sperrung, die
 * ausschliesslich `.k-titel` trägt.
 */
export const sperrung = {
  standard: '0.14em',
  eng: '0.06em',
  titel: '0.015em',
} as const;

/**
 * Gewichts-Skala (NEU, D-1/D-9, E-2 `GESTALTUNGS-ENTSCHEIDE-2026-08-10.md`) —
 * spiegelt `--k-gewicht-normal/-betont/-stark` aus aura.css. Real
 * ausgeliefert sind nur zwei Schnitte je Stimme (Font-Befund im
 * Kanon-Dokument) — `betont` gilt NUR in Mono-Kontexten (Lato würde 500
 * stumm auf 400 abrunden).
 */
export const gewicht = {
  normal: 400,
  betont: 500,
  stark: 700,
} as const;

/**
 * Breakpoint-Skala (NEU, D-1, E-3 `GESTALTUNGS-ENTSCHEIDE-2026-08-10.md`) — drei
 * kanonische Breiten-Grenzen als dokumentierte Konstanten (Media-Queries
 * können kein `var()`, darum Konvention + Wächter statt CSS-Token; kein
 * `--k-breakpoint-*` in aura.css). Referenz für `matchMedia` und die
 * `@media`-Wächter-Prüfung in `token-spiegel.test.ts`.
 */
export const breakpoint = {
  schmal: 700,
  mittel: 1100,
  weit: 1500,
} as const;

/**
 * Spacing-Skala (NEU, W0) — spiegelt `--k-s1`…`--k-s7` aus aura.css. Gilt für
 * ALLE gaps/paddings; rohe px-Literale sind ab jetzt ein Review-Befund.
 */
export const scale = {
  s1: '2px',
  s2: '4px',
  s3: '8px',
  s4: '12px',
  s5: '16px',
  s6: '24px',
  s7: '32px',
  /**
   * NEU (v0.8.0B / W1, Spez §1/§6) — `_ds`-Pflichtstufen additiv zu s1–s7
   * (2px bleibt Repo-Recht, testgesichert). Spiegelt `--k-s8/-s9/-s10`.
   */
  s8: '48px',
  s9: '64px',
  s10: '96px',
} as const;

/** Radien — spiegelt `--k-radius-sm/-md/-lg` aus aura.css. v0.7.3 D7: die
 * runden Werte 8/12/16px waren bis 0.7.2 ein reiner `orbit`-Override —
 * jetzt themenübergreifende Grammatik im `:root`-Block (Papier UND Kosmos).
 * `pill` bleibt als praktischer Zusatzwert (volle Rundung, keine
 * aura-Variable nötig) bestehen. */
export const radius = { sm: '8px', md: '12px', lg: '16px', pill: '999px' } as const;

/**
 * NEU (v0.8.0B / W1, Spez §1 B-27) — spiegelt `--k-radius-hub`
 * (OrbitStart/Orbit-Hub, themen-agnostisch wie die drei Radien oben).
 */
export const radiusHub = '26px';

export const motion = {
  /** Zurückhaltend-präzise (Owner Q20): kurz, physikalisch sauber, nie verspielt. */
  fast: '120ms cubic-bezier(0.3, 0, 0.2, 1)',
  base: '200ms cubic-bezier(0.3, 0, 0.2, 1)',
  settle: '320ms cubic-bezier(0.22, 0.9, 0.28, 1)',
  /**
   * NEU (v0.6.6 MOTION-KONZEPT-066 §2) — spiegelt `--k-feder`/-fallback/
   * `--k-druck-dauer`/-skala aus `aura.css` (dort die einzige Wahrheit,
   * `token-spiegel.test.ts` bricht bei Abweichung). Fünf Dauern bleiben die
   * Obergrenze im Konzept — eine sechste ändert das Konzept, nicht den
   * Einzelfall.
   */
  feder: '260ms linear(0, 0.32 12%, 0.72 28%, 0.95 46%, 1.02 64%, 1 82%, 1)',
  federFallback: '260ms cubic-bezier(0.3, 1.25, 0.4, 1)',
  druckDauer: '80ms',
  druckSkala: '0.97',
} as const;

/** Schatten — `raised`/`overlay` (Legacy-Form, unverändert exportiert) zeigen
 * die Papier-Werte, `paper` (NEU) dieselben nochmal benannt. v0.7.3 D7: der
 * `ink`-Zweig (dunklerer Schatten fürs entfernte Tinte-Thema) ist mit dem
 * Theme weggefallen. Bis v0.8.0B/W1 bekam `orbit` in aura.css keinen eigenen
 * `--k-shadow-*`-Override; W1 (Spez §1 B-24) führt die Schatten-Skala jetzt
 * NUR für Kosmos ein (`shadow.orbit` unten) — Papier bleibt bei `raised`/
 * `overlay`/`paper.*`, ausschliesslich an schwebenden Overlays (Menü, Dialog,
 * Palette) bzw. der einen flachen Blattkontur. */
export const shadow = {
  raised: '0 1px 0 rgba(26, 24, 21, 0.08)',
  overlay: '0 1px 0 rgba(26, 24, 21, 0.12), 0 12px 40px rgba(26, 24, 21, 0.18)',
  paper: {
    raised: '0 1px 0 rgba(26, 24, 21, 0.08)',
    overlay: '0 1px 0 rgba(26, 24, 21, 0.12), 0 12px 40px rgba(26, 24, 21, 0.18)',
  },
  /**
   * NEU (v0.8.0B / W1, Spez §1 B-24) — Schatten-Skala NUR im Kosmos-Theme
   * (spiegelt `--k-shadow-xs/-sm/-md/-lg/-xl` + `--k-inset-top` aus dem
   * `[data-theme='orbit']`-Block). Papier bekommt KEIN Gegenstück — «Papier
   * kennt kein Glas», es bleibt bei `paper.raised`/`paper.overlay` oben.
   */
  orbit: {
    xs: '0 1px 2px rgba(0, 0, 0, 0.30)',
    sm: '0 2px 8px rgba(0, 0, 0, 0.32)',
    md: '0 8px 24px rgba(0, 0, 0, 0.38)',
    lg: '0 18px 48px rgba(0, 0, 0, 0.46)',
    xl: '0 32px 80px rgba(0, 0, 0, 0.55)',
    insetTop: 'inset 0 1px 0 rgba(255, 255, 255, 0.08)',
  },
} as const;

/**
 * Orbit-Thema (`[data-theme='orbit']` in aura.css, v0.7.2 §1) — seit v0.7.3
 * D7 die «Kosmos»-Hälfte des Theme-Paars (Tinte entfernt). Hexwerte exakt
 * gespiegelt; der Grossteil ist NICHT vom `token-spiegel.test.ts`-Wächter
 * geprüft (der bleibt grundsätzlich auf paper+:root beschränkt, siehe
 * dort) — hier trotzdem als vollständiger TS-Spiegel für Code, das
 * orbit-Farben ausserhalb von CSS-Variablen braucht. AUSNAHME (v0.8.0B/W1):
 * die neuen `line*`/`hairline`/`hover`-Werte (Alpha-Border-Flip + Flächen-
 * stufe Hover, Spez §1/§6) bekommen gezielte Wächter-Tests, weil W1 sie
 * frisch einführt bzw. ändert — dort ist Drift am wahrscheinlichsten.
 */
export const orbit = {
  field: '#0b0d12',
  surface: '#14171f',
  raised: '#1a1e27',
  ink: '#f4f6fa',
  inkSoft: '#b6bdcb',
  inkFaint: '#7f8695', // B138: war #6e7686, s. aura.css
  /**
   * v0.8.0B / W1 (Spez §1/§6, Konfliktentscheid «Borders Alpha-Weiss») —
   * Alpha-Border-Flip: `line`/`lineStrong` waren bis 0.7.2 Volltöne
   * (`#222732`/`#2a3140`), jetzt Alpha-Weiss auf drei Stufen inkl. der
   * neuen `lineSubtil`. Einzige Stelle, an der dieses Paket das Repo
   * sticht (Begründung in aura.css beim `[data-theme='orbit']`-Block).
   */
  lineSubtil: 'rgba(255, 255, 255, 0.07)',
  line: 'rgba(255, 255, 255, 0.11)',
  lineStrong: 'rgba(255, 255, 255, 0.18)',
  /** NEU (W1, Spez §1) — Hintergrundraster, nur Backdrop, opacity ≤.5. */
  hairline: 'rgba(120, 140, 190, 0.14)',
  /** NEU (W1, Spez §1 B-26) — Flächenstufe Hover, komplettiert sunken→hover. */
  hover: '#222732',
  accent: '#57b6c2',
  accentHover: '#6cc4cf',
  accentInk: '#06141a',
} as const;

/**
 * KosmoSpez K37c (Owner-Freigabe 21.07.2026, `docs/owner-packages/
 * 2026-07-21-kosmospez-k37c/README.md` §«Token-Erweiterung») — TS-Spiegel
 * der `--spez-*`-Tokens aus aura.css (Papier + Kosmos, je fünf Stützwerte
 * Stufe 1→5 je Falschfarben-Skala). P2/v0.1.3 (Fund K37c-FALSCHFARBEN/
 * NS-K37C-TOKEN-NICHT-GESPIEGELT): die Tabelle stand seit 21.07.2026 nur im
 * Package-README, nie hier — 0 `--spez-`-Treffer im Code trotz Freigabe.
 * Stationsfarbe bleibt `moduleHue.spez` oben (unverändert, identisch zum
 * Papier-Wert hier); die drei Skalen sind additiv, kein Werkzeug konsumiert
 * sie in dieser Version (`falschfarben-skala`/`overlay-wahl` bleiben
 * `status:'neu'` im Spez-Katalog — Raster-Ergebnisse fehlen noch).
 */
export const spez = {
  paper: {
    station: '#9c84c4',
    stationInk: '#6b5691', // nur Papier — README nennt keinen Kosmos-Wert («—»)
    seqSonne: ['#f0e2ba', '#e2b95a', '#c9822f', '#a04a28', '#6b2a22'] as const,
    seqLicht: ['#e4e7dc', '#afcdbd', '#6ba491', '#337165', '#1b4547'] as const,
    divKomfort: ['#3f5f8f', '#8fa6bf', '#e9e4d8', '#ce9c66', '#af4e33'] as const,
  },
  orbit: {
    station: '#b4a0db',
    seqSonne: ['#46351b', '#8a5f25', '#c08630', '#e3a83e', '#f6cc71'] as const,
    seqLicht: ['#1f2e2b', '#2f5b50', '#478574', '#6fb39a', '#a8dec2'] as const,
    divKomfort: ['#8fb4e8', '#51719b', '#272c34', '#a06b3c', '#e08a5a'] as const,
  },
} as const;

/**
 * Boot-Screen (NEU, v0.9.28 / P-BOOT, D-3-Folge) — spiegelt
 * `--k-boot-grund` und die vier `--k-boot-schrift*`-Stufen aus dem
 * themen-unabhängigen `:root`-Block von aura.css. Themen-INVARIANT mit
 * Absicht: die Startsequenz läuft, bevor ein Thema gewählt ist, und bleibt
 * immer dunkel. Vier der fünf Werte sind byte-identisch mit
 * `orbit.field`/`inkSoft`/`--k-ink-muted`/`inkFaint` — bewusst NICHT
 * darauf verwiesen (dieselbe Entkopplungs-Begründung wie bei `--k-graph`/
 * `--k-svm-buehne`; ein `var()` auf die orbit-Tokens hätte im Papier-Thema
 * die falschen, hellen Werte geliefert). `schrift` (#dce0e8) hat gar kein
 * Gegenstück im Bestand. Reihenfolge = absteigende Helligkeit.
 */
export const boot = {
  grund: '#0b0d12',
  schrift: '#dce0e8',
  schriftSoft: '#b6bdcb',
  schriftMuted: '#8b92a2',
  schriftFaint: '#7f8695', // B138: folgt --k-ink-faint (orbit), s. aura.css
} as const;

/**
 * Marke (NEU, v0.9.36 / W-9, Token-Drift-Aufräumung — spiegelt
 * `--k-marke-neutral` aus dem themen-unabhängigen `:root`-Block von
 * aura.css). Eigenes, additiv angelegtes Token für die Neutral-Farbe der
 * StartSequenz-SVG (A-Spitze, stroke) — ZUFÄLLIG byte-identisch mit
 * `boot.schrift` (#dce0e8), aber ausdrücklich NICHT dasselbe Token: `boot.
 * schrift` ist eine Text-Rolle (Leitsatz-Lesbarkeit), `marke.neutral` eine
 * Geometrie-Rolle (SVG-Stroke der Marke). Bewusst getrennt gehalten, damit
 * eine spätere unabhängige Änderung der einen Rolle die andere nicht
 * mitreisst (dieselbe Koinzidenz-Begründung wie bei `boot` selbst
 * gegenüber `orbit`).
 */
export const marke = {
  neutral: '#dce0e8',
} as const;

/** Signal — die themeninvariante Markenfarbe (spiegelt `--k-signal*`). */
export const signal = {
  signal: '#57b6c2',
  hell: '#eaf6f8',
  tinte: '#06141a',
} as const;

/** Rollenfarben (spiegelt das themeninvariante `--k-rolle-*` im `:root`-Block,
 * Spec §1/§3) — WER handelt. Das sind die Kosmos-/`orbit`-Originalwerte
 * (Spec D7: «Rollenfarben Original»); Papier überschreibt sie in aura.css
 * eine Stufe dunkler (`[data-theme='paper']`, unter dem `:root`-Block) —
 * dieser TS-Spiegel bleibt bewusst bei den ungedimmten Originalwerten, wie
 * `orbit` oben auch keinen eigenen TS-Zweig für Radien/Fonts bekommt. */
export const rolle = {
  manuell: '#74c2a0',
  pn: '#6f9bcf',
  pna: '#c082b4',
  agent: '#cbb06a',
  memory: '#cf9466',
  generator: '#cd7670',
  ak: '#b08a6e',
  office: '#8a7b5a',
  /** v0.8.1 / P1 (Owner-Entscheid 16.07.2026, `docs/V081-SPEZ.md` §4.1
   * Entscheid 4/C-4) — neunte Rolle, additiv (mirrors `--k-rolle-doc` in
   * `aura.css`): die Doc-Station bekommt eine eigene Rollenfarbe statt
   * weiterhin `moduleHue.draw` mitzubenutzen (`modules/doc/DocWorkspace.tsx`). */
  doc: '#5d7489',
} as const;

/** v0.7.3 D7 (Owner-Entscheid): Tinte (`ink`) entfernt — nur noch das
 * Theme-Paar Papier/Kosmos. Migration bestehender `localStorage`-Werte
 * `ink` → `orbit` lebt in `App.tsx` (VOR dem `useState`, das diesen Typ
 * liest) und im Companion-Thema-Leser (`shell/Companion.tsx`). */
export type ThemeName = 'paper' | 'orbit';

/**
 * Ebenentafel (z-index) — W0 P-EBENENTAFEL (v0.9.51). Basis:
 * `docs/MESSUNG-EBENEN-2026-08-26.md` (93 erfasste Vergaben, 5 gemessene
 * Bestandsordnungen, 3 Dokumentations-Widersprüche). Anders als der Rest
 * dieser Datei ist dies KEIN Spiegel von `aura.css` — z-index-Werte sind im
 * ganzen Repo verstreut (CSS, `zIndex`-Inline-Props, sogar ein reines `z:`-
 * Objektfeld ohne jedes `z-index`/`zIndex` im Quelltext, s. `QUELLE_DOCK`
 * unten) und hatten vor dieser Tafel gar keine gemeinsame Quelle. Diese
 * Tafel BENENNT Bestandswerte (keine Neuvergabe) und macht den einen
 * Mechanismus sichtbar, der die meisten Überdeckungsfälle dieses Repos
 * erklärt — s. `MECHANISMUS` — plus den einen, der sie NICHT erklärt, obwohl
 * das naheliegend gewesen wäre — s. `EHRLICHER BEFUND` unten.
 *
 * MECHANISMUS (`aura.css:1037-1040`):
 *   #root { position: relative; z-index: 1; }
 * Jedes NICHT per `createPortal(..., document.body)` gerenderte
 * `position:fixed`-Element bleibt in DIESEM Stacking-Context gefangen: sein
 * `z-index` zählt nur gegen andere `#root`-Nachfahren, nie gegen einen
 * `document.body`-Portal-Geschwister — egal wie hoch die Zahl. Ein Element
 * mit `root:'aussen'` unten schlägt darum JEDES Element mit `root:'innen'`,
 * unabhängig vom Zahlenwert; unter Elementen mit demselben `root`-Wert
 * entscheidet der Zahlenvergleich normal.
 *
 * EHRLICHER BEFUND (Auftrags-Prämisse geprüft, nicht abgeschrieben): der
 * Auftrag zu diesem Paket nennt den `#root`-Mechanismus als „die Ursache
 * der bisher neun Überdeckungsfälle dieser Version" (ROADMAP 1137/1144 A/
 * 1146/1148 a-c/1151/1156). Nachgeprüft an JEDEM der neun Fälle (createPortal-
 * Grep in jeder beteiligten Komponente, s. Zeilenbelege unten): **keiner der
 * neun liegt tatsächlich am `#root`-Mechanismus.** Alle neun spielen sich
 * INNERHALB von `#root` ab:
 *   - 1137 (KSelect klappt unter den Fensterrand): reiner `top`/`bottom`-
 *     Rechenfehler in `berechnePopupLage()` — kein z-index beteiligt.
 *   - 1146 (Boden-Dock über dem Trust-Ausfuhr-Knopf): fehlender
 *     `padding-bottom`, kein z-index-Rang-Konflikt (behoben ohne z-index-
 *     Änderung, `BODEN_DOCK_RESERVE_PX`).
 *   - 1144 A/1148 a/b (Kosmo-Panel/Kosmo-Insel über Publish-Flächen/Dock-
 *     Inspector/Vis-Ausführen-Knopf): `.kp-panel` (KosmoPanel.tsx rendert es
 *     NICHT portalt — nur seine SCRIM-KINDER sind seit v0.9.6 eigene
 *     `createPortal`-Aufrufe, s. `KosmoPanel.tsx:797-808`) und
 *     `.isl-root--offen` (IslandShell.tsx: kein `createPortal`, grep-
 *     bestätigt) liegen BEIDE innerhalb `#root` — derselbe Kontext wie das,
 *     was sie verdecken. Der Konflikt ist eine fehlende Geometrie-
 *     Koordination zwischen global-fixiertem Chrome und lokalem Inhalt,
 *     nicht ein `#root`-Sprung.
 *   - 1148 c (Modus-Chipleiste über dem Übernehmen-Knopf im 3D-Werkzeug):
 *     zwei voneinander unabhängig verankerte, beide stationslokale
 *     Bodenleisten derselben Ansicht — kein globales Chrome beteiligt.
 *   - 1151 (siebter Deckel, `.vis-chrome-topright` 36 vs.
 *     `.isl-einstellungen-kreis` 42): BEIDE innerhalb `#root` (grep in
 *     `NodeCanvas.tsx`/`IslandShell.tsx`, kein `createPortal`) — ein
 *     korrekt auflösender GLEICHER-Kontext-Vergleich (42 > 36), zusätzlich
 *     durch einen lokalen, verschachtelten Stacking-Context gedeckelt
 *     (`.k-einblenden`, s. `design.css:185-197`). Der `#root`-Mechanismus
 *     ist hier NICHT die Ursache — selbst ein `.vis-chrome-topright`-Wert
 *     von 1000 würde am Klick-Problem nichts ändern, s. `AUSGESCHLOSSEN`.
 *   - 1156 (Fall 8/9, `.k-meldungen-host` 200 über Insel-Popup-Knöpfen):
 *     ROADMAP 1156 behauptet wörtlich, der Meldung-Toast hänge „per
 *     `createPortal(..., document.body)` ausserhalb von `#root`" — **das
 *     ist falsch, selbst geprüft:** `KMeldungen()` (`meldungen.tsx:85-117`)
 *     ruft `createPortal` NICHT auf (nur `KBestaetigung()`, Zeile 187, tut
 *     das) und wird direkt, unportalt, in `App.tsx:1666` gerendert. Fall 8/9
 *     ist ein korrekter GLEICHER-Kontext-Vergleich (200 > 100), der genau
 *     der dokumentierten Insel-Leiter entspricht (`island.css:86-100`:
 *     offene Insel 100 < Meldungs-Turm) — die eigentliche offene Frage aus
 *     1156 ("warum steht dort überhaupt ein Fehler-Toast in einem
 *     Erfolgsfall") bleibt richtig offen, ist aber keine z-index-Frage.
 * Der `#root`-Mechanismus ist real und historisch belegt (er erklärt den
 * ÄLTEREN, LÄNGST behobenen KBestaetigung-Fall — `meldungen.tsx:155-178` —
 * und begründet, warum `select.tsx`/`KBestaetigung`/`Einstellungen.tsx`
 * heute portalen) — er ist nur nicht die Ursache DIESER neun Fälle. Eine
 * Tafel, die das verschweigt, wäre die Kosmetik, vor der der Auftrag warnt.
 *
 * WAS DIESE TAFEL TUT (eng, s. Auftrag „nicht alle 93 Stellen"):
 *   1. Fünf Elemente aus den neun Fällen + dem Chrome, das sie verdeckt,
 *      MIGRIERT (Feld `governed:true`) — die zugehörige CSS-Datei trägt ab
 *      jetzt einen `W0-EBENENTAFEL <NAME>`-Kommentar direkt über der
 *      `z-index`-Zeile; der Riegel (`tools/z-ebenen-gate.mjs`) prüft Datei,
 *      Selektor, Marker UND Wert.
 *   2. Fünf weitere Werte (CursorEbene/KSelect-Portal/Dock-Solver-Leiter)
 *      als REFERENZ (`governed:false`) — Quelle ist eine `.tsx`-Datei oder
 *      `state/dock-kern.ts`, beide ausserhalb des Dateikreises dieses
 *      Pakets. Der Riegel LIEST sie trotzdem (nur lesend, keine Änderung)
 *      und vergleicht live gegen die hier dokumentierten Werte — das ist
 *      der Deckel für genau den Blindfleck aus `dock-kern.ts` (s. dort).
 *   3. Bewusst NICHT migriert: die drei stationslokalen „Verlierer"-Werte
 *      aus den Fällen 1137/1148 c/1151 (`.k-menu` 100, `.dw-modus-chip-wrap`
 *      6, `.vis-chrome-topright` 36) — s. `AUSGESCHLOSSEN` unten, jede mit
 *      Begründung, keine Sammelklausel.
 *   4. **84 der 93 gemessenen Vergaben bleiben unangetastet** (93 − 5
 *      migriert − 4 Referenz-Einzelwerte, die 4-Werte-Dock-Leiter zählt als
 *      EINE Fundstelle wie in der Kartierung — s. Kopf dort — minus die 3
 *      benannten Ausschlüsse = 93 − 5 − 4 − 3 = 81 rein stationslokale
 *      Zeilen, für die keine repo-weite Tafel gebraucht wird, s.
 *      `MESSUNG-EBENEN-2026-08-26.md` §3.4/§5). Aufgeschlüsselt: 5 migriert
 *      + 4 Referenz (Cursor, Portal-Popup, 2×Dock-Stufenpaar als 1
 *      Fundstelle) + 3 ausgeschlossen (benannt) + 81 unangetastet = 93.
 *
 * AUSGESCHLOSSEN (bewusst NICHT migriert, mit Begründung):
 *   - `.k-menu` (aura.css:2131, z:100, Fall 1137): stationslokal, gefangen
 *     im Stacking-Context der jeweiligen Insel (`island.css:86-100`-
 *     Kommentar) — UND der Bug in 1137 war ohnehin kein z-index-Problem
 *     (reiner `top`/`bottom`-Rechenfehler). Eine Tafel-Stufe hier würde
 *     einen z-index-Bezug behaupten, den der Fall nie hatte.
 *   - `.dw-modus-chip-wrap` (design.css:437, z:6, Fall 1148 c): stations-
 *     lokal, `position:relative` — der Konflikt ist Geometrie zwischen zwei
 *     gleichrangigen lokalen Bodenleisten, keine Tafel-Stufe passt.
 *   - `.vis-chrome-topright` (vis-visual.css:197, z:36, Fall 1151): station-
 *     slokal UND zusätzlich durch einen lokalen Stacking-Context gedeckelt
 *     (`.k-einblenden`, `design.css:185-197`) — jeder Zahlenwert hier wäre
 *     wirkungslos gegen `INSEL_BUEHNENKOPF` (42, global fixiert). Die
 *     einzigen echten Lösungen sind Portal oder eine geometrische
 *     Ausweichlösung (s. `design.css:185-197`) — das gehört in einen
 *     Bauauftrag, nicht in diese Tafel.
 *
 * NICHT TEIL DIESER TAFEL (bewusst, mit Begründung — s. auch Widerspruch
 * unten): die breitere „Modal-Scrim-Familie" (205/215/220/230/250,
 * `overlay.tsx:187-198`) und der „Meldungs-Turm" oberhalb (900/2000/9990).
 * Keines ihrer Mitglieder gehört zu einem der neun Fälle, und alle Quellen
 * sind `.tsx`-Dateien ausserhalb des Dateikreises dieses Pakets. Beim
 * Verifizieren fiel zusätzlich auf: die Familie ist NICHT einheitlich
 * portalt, wie `overlay.tsx`s Kommentar suggeriert — `Kurzbefehle.tsx`
 * (205) und `AppDeinstallieren.tsx` (230) rendern beide direkt in
 * `App.tsx:1664/1669` OHNE `createPortal` (grep bestätigt: kein Treffer in
 * beiden Dateien), while `WerkzeugSetup`s Scrim erst seit v0.9.6 über einen
 * `createPortal`-Aufruf IN `KosmoPanel.tsx` (nicht in `WerkzeugSetup.tsx`
 * selbst) nach aussen wandert und `Einstellungen.tsx` sein Scrim selbst
 * portalt (Zeile 611). Ein direkter Zahlenvergleich über die ganze Familie
 * (wie `overlay.tsx:279-292` ihn nahelegt) vergleicht damit teils `root:
 * 'innen'` gegen `root:'aussen'` — nicht notwendigerweise falsch (KEIN
 * bekannter Deckel-Fall in dieser Familie), aber ungeprüft und nicht Teil
 * dieses engen Pakets. Eigener, gemessener Auftrag.
 */
export interface ZEbenenQuelle {
  /** Repo-relativer Pfad ab `kosmo-orbit/`. */
  datei: string;
  /** Zeile der `z-index`/`zIndex`/`z:`-Deklaration, selbst nachgezählt. */
  zeile: number;
  /** Selektor/Feld, wie im Quelltext benannt. */
  selektor: string;
  /** `true` = diese Datei trägt jetzt einen `W0-EBENENTAFEL`-Marker-
   * Kommentar UND liegt im Dateikreis dieses Pakets; der Riegel prüft
   * Marker + Wert. `false` = reine, schreibgeschützte Referenzprüfung
   * (Quelle ausserhalb des Dateikreises), der Riegel liest nur. */
  governed: boolean;
}

export interface ZEbenenEintrag {
  /** Kurzname — vom Riegel referenziert (Marker-Text `W0-EBENENTAFEL <name>`). */
  name: string;
  /** Bestandswert(e) — keine Neuvergabe. Ein Array bei mehrgliedrigen
   * Leitern (Dock-Solver), sonst ein einzelner Wert. */
  wert: number | readonly number[];
  /** Was in diese Stufe gehört. */
  beschreibung: string;
  /** 'aussen' = per `createPortal(..., document.body)` ausserhalb von
   * `#root` — schlägt jede 'innen'-Stufe unabhängig vom Zahlenwert (s.
   * MECHANISMUS oben). 'innen' = normaler Renderbaum unter `#root`; der
   * Zahlenvergleich gilt nur gegen andere 'innen'-Stufen im selben
   * Stacking-Context. */
  root: 'aussen' | 'innen';
  quellen: readonly ZEbenenQuelle[];
  /** ROADMAP-Belege, falls an einem der neun Fälle beteiligt. */
  faelle?: readonly string[];
}

/** Die vier Dock-Solver-Stufen (s. `QUELLE_DOCK`-Kommentar am Riegel) —
 * `DockPanel.tsx:203`s eigener Kommentar nennt sie „Stack/Rail 14,
 * B-Streifen 16, verankerte Floats 30, FREI positionierte Floats … 32".
 * NICHT Teil der neun Fälle, aber die vom Auftrag ausdrücklich verlangte
 * Abdeckung des `dock-kern.ts`-Blindflecks (kein `z-index`/`zIndex` im
 * Quelltext dieser Datei, `grep -c` = 0 — nachgeprüft). */
export const zEbeneDock = {
  stackRail: 14,
  bStreifen: 16,
  verankert: 30,
  frei: 32,
} as const;

export const zEbene: readonly ZEbenenEintrag[] = [
  {
    name: 'CURSOR',
    wert: 2147483000,
    beschreibung: 'Die eine CursorEbene (Eigencursor-Overlay) — per Kommentar exklusiv gehalten, nichts sonst gehört hierher.',
    root: 'aussen',
    quellen: [{ datei: 'apps/kosmo-orbit/src/shell/cursor-ebene.css', zeile: 79, selektor: '.cursor-ebene-wrapper', governed: false }],
  },
  {
    name: 'PORTAL_POPUP',
    wert: 2147482000,
    beschreibung: 'Body-portalte Popups, die über jedem Fenster/Panel, aber unter CURSOR liegen müssen (KSelect-Listbox).',
    root: 'aussen',
    quellen: [{ datei: 'packages/kosmo-ui/src/select.tsx', zeile: 556, selektor: 'zIndex (KSelect-Listbox, body-Portal)', governed: false }],
  },
  {
    name: 'MELDUNGS_TOAST',
    wert: 200,
    beschreibung:
      'Der Meldungs-Turm (`KMeldungen`, Erfolg/Fehler/Hinweis-Toasts). Liegt INNERHALB #root (kein createPortal, App.tsx:1666) — schlägt OFFENE_INSEL nur, weil beide im selben #root-Kontext stehen und 200 > 100 ist, NICHT wegen des #root-Mechanismus. Fall 8/9 (ROADMAP 1156).',
    root: 'innen',
    quellen: [{ datei: 'packages/kosmo-ui/src/aura.css', zeile: 3062, selektor: '.k-meldungen-host', governed: true }],
    faelle: ['ROADMAP 1156 (Fall 8/9)'],
  },
  {
    name: 'BODEN_DOCK',
    wert: 108,
    beschreibung:
      'App-weite Bodenleiste (Navigations-Layer, `position:fixed`, INNERHALB #root). Deckte den Trust-Ausfuhr-Knopf — behoben über padding-bottom-Reserve, nicht über z-index (der Rang war nie das Problem).',
    root: 'innen',
    quellen: [{ datei: 'apps/kosmo-orbit/src/shell/boden-dock.css', zeile: 22, selektor: '.boden-dock', governed: true }],
    faelle: ['ROADMAP 1146'],
  },
  {
    name: 'OFFENE_INSEL',
    wert: 100,
    beschreibung:
      'Jede geöffnete Insel (Modifikator auf `.isl-root`, `position:fixed` geerbt). INNERHALB #root. Deckte den Vis-Ausführen-Knopf (Fall 1148 a) — fehlende Geometrie-Koordination, kein #root-Sprung.',
    root: 'innen',
    quellen: [{ datei: 'apps/kosmo-orbit/src/modules/design/island/island.css', zeile: 106, selektor: '.isl-root--offen', governed: true }],
    faelle: ['ROADMAP 1148 a'],
  },
  {
    name: 'KOSMO_PANEL',
    wert: 60,
    beschreibung:
      'Kosmo-Blase (`.kp-panel`, `position:fixed`, INNERHALB #root — nur seine Scrim-KINDER portalen seit v0.9.6, das Panel selbst nicht). Deckte Publish-Platzierungsflächen (1144 A) und den Dock-Inspector (1148 b).',
    root: 'innen',
    quellen: [{ datei: 'apps/kosmo-orbit/src/shell/kosmo-panel.css', zeile: 150, selektor: '.kp-panel', governed: true }],
    faelle: ['ROADMAP 1144 A', 'ROADMAP 1148 b'],
  },
  {
    name: 'INSEL_BUEHNENKOPF',
    wert: 42,
    beschreibung:
      'Bühnenkopf-Chrome der Insel (Einstellungs-Kreis/Logo/Orb, `position:fixed`, INNERHALB #root). Gewinnt gegen `.vis-chrome-topright` (36, stationslokal, AUSGESCHLOSSEN) — Fall 7/„der bekannte Deckel" (ROADMAP 1151); kein Zahlenwert von `.vis-chrome-topright` kann das je umkehren, s. Tafel-Kopfkommentar AUSGESCHLOSSEN.',
    root: 'innen',
    quellen: [{ datei: 'apps/kosmo-orbit/src/modules/design/island/island.css', zeile: 1118, selektor: '.isl-einstellungen-kreis', governed: true }],
    faelle: ['ROADMAP 1151 (siebter Deckel)'],
  },
  {
    name: 'DOCK_SOLVER',
    wert: [zEbeneDock.stackRail, zEbeneDock.bStreifen, zEbeneDock.verankert, zEbeneDock.frei],
    beschreibung:
      'Vier Dock-Solver-Stufen (Stack/Rail 14 < B-Streifen 16 < verankerte Floats 30 < frei gezogene Floats 32), `position:absolute` via `.k-dock-panel`, INNERHALB #root. Reine `z:`-Objektfelder in `state/dock-kern.ts` — WEDER `z-index` NOCH `zIndex` im Quelltext dieser Datei (grep -c = 0). Nicht Teil der neun Fälle; hier nur, weil der Auftrag die Abdeckung dieses Blindflecks ausdrücklich verlangt (s. Riegel).',
    root: 'innen',
    quellen: [
      { datei: 'apps/kosmo-orbit/src/state/dock-kern.ts', zeile: 410, selektor: 'z: 14 (Stack/Rail)', governed: false },
      { datei: 'apps/kosmo-orbit/src/state/dock-kern.ts', zeile: 436, selektor: 'z: 16 (B-Streifen)', governed: false },
      { datei: 'apps/kosmo-orbit/src/state/dock-kern.ts', zeile: 467, selektor: 'z: 30 (verankerte Floats)', governed: false },
      { datei: 'apps/kosmo-orbit/src/state/dock-kern.ts', zeile: 561, selektor: 'z: 32 (freie Floats)', governed: false },
    ],
  },
] as const;
