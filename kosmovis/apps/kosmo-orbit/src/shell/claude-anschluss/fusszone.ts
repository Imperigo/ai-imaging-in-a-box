/**
 * **Fusszone der Claude-Zeile** (Demolauf 16.10.2026 Nr. 56: «Links unten überlagern
 * sich Darstellungen/Bedienelemente»).
 *
 * Die Zeile unten links («Im Projekt: Du · Claude · Kosmo», «Vollautomatik · Alle
 * anhalten», «Claude verbunden») haengt fest am Fensterrand, ueber allen Flaechen. In
 * der geteilten Ansicht lag sie gemessen auf der Navi-Insel der linken Flaeche
 * (Zoom/Einpassen/Vollbild), bei schmalem Fenster auch auf der Blicke-Leiste.
 *
 * Die Zeile meldet darum, wie weit sie vom unteren Fensterrand in die Flaechen
 * hineinreicht, als `--claude-fusszone` am Wurzelelement. Wer am Boden einer Flaeche
 * sitzt, weicht mit `max(<eigener Abstand>, var(--claude-fusszone, 0px))` aus; ohne
 * Claude ist das Token nicht gesetzt und alles bleibt, wo es war.
 */

export const CLAUDE_FUSSZONE_TOKEN = '--claude-fusszone';

/**
 * Der ganze Stapel unten links (offene Vorschlagskarten, Schalter, Coop-Fläche UND die Zeile), Befund LW 20.10.2026:
 * das Kärtchen «Ersatzdarstellung» weicht der Zeile aus, lag aber über einer offenen Vorschlagskarte. Wer in DERSELBEN
 * Spalte unten links sitzt, weicht mit `var(--claude-stapel, …)` dem ganzen Stapel aus; die Navi-Insel (andere Spalte)
 * bleibt an `--claude-fusszone`, sonst spränge sie bei jeder offenen Karte grundlos hoch.
 */
export const CLAUDE_STAPEL_TOKEN = '--claude-stapel';

/** Abstand zwischen der Oberkante der Zeile und dem, was darueber ausweicht. */
export const CLAUDE_FUSSZONE_LUFT_PX = 8;

/**
 * Wie weit die Zeile vom unteren Fensterrand hineinreicht, plus Luft — oder `null`,
 * wenn sie nichts belegt (keine Hoehe, ausserhalb des Fensters, ungueltige Masse).
 */
export function claudeFusszonePx(fensterHoehe: number, oberkante: number, hoehe: number): number | null {
  if (![fensterHoehe, oberkante, hoehe].every(Number.isFinite) || hoehe <= 0) return null;
  const reicht = fensterHoehe - oberkante;
  if (reicht <= 0 || reicht > fensterHoehe) return null;
  return Math.ceil(reicht + CLAUDE_FUSSZONE_LUFT_PX);
}

/**
 * Beobachtet die Zeile und haelt das Token aktuell; gibt die Aufraeumfunktion zurueck,
 * die das Token wieder entfernt (Zeile weg = keine Fusszone).
 */
export function beobachteClaudeFusszone(
  zeile: HTMLElement,
  wurzel: HTMLElement = document.documentElement,
  token: string = CLAUDE_FUSSZONE_TOKEN,
): () => void {
  const setze = () => {
    const r = zeile.getBoundingClientRect();
    const px = claudeFusszonePx(window.innerHeight, r.top, r.height);
    if (px === null) wurzel.style.removeProperty(token);
    else wurzel.style.setProperty(token, `${px}px`);
  };
  setze();
  const ro = typeof ResizeObserver === 'function' ? new ResizeObserver(setze) : null;
  ro?.observe(zeile);
  window.addEventListener('resize', setze);
  return () => {
    ro?.disconnect();
    window.removeEventListener('resize', setze);
    wurzel.style.removeProperty(token);
  };
}
