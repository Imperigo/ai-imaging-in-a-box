/**
 * **Tastennamen: «Strg» heisst auf dem Mac «⌘»** (U11, Owner B6, 01.10.2026).
 *
 * Wer auf einem Mac arbeitet, sucht «Strg+Z» vergeblich — dort heisst die
 * Taste Befehlstaste, geschrieben ⌘. Texte, die eine Tastenkombination
 * nennen, fragen darum diese Datei statt «Strg» fest zu schreiben:
 *
 *   taste('mod')            → «⌘» auf dem Mac, sonst «Strg»
 *   kuerzel('mod+z')        → «⌘Z» auf dem Mac, sonst «Strg+Z»
 *   kuerzel('mod+shift+z')  → «⇧⌘Z» bzw. «Strg+Umschalt+Z»
 *
 * **Was als Mac gilt:** Mac, iPhone und iPad — auch ein iPad mit Tastatur,
 * das sich als «MacIntel» meldet. Die Erkennung liest `navigator` bei jedem
 * Aufruf (nicht einmal beim Laden), damit sie sich testen lässt und ein
 * Gerätewechsel im Browser-Profil sofort gilt. Ohne `navigator` (Server,
 * Test) gilt «Strg».
 *
 * Nur Anzeige: welche Taste die App tatsächlich auslöst, entscheiden die
 * Tastenhorcher selbst (sie akzeptieren Strg und Befehl).
 */

type Nav = {
  platform?: string;
  userAgent?: string;
  maxTouchPoints?: number;
  userAgentData?: { platform?: string };
};

export function istMac(): boolean {
  const nav: Nav | undefined = typeof navigator === 'undefined' ? undefined : (navigator as Nav);
  if (!nav) return false;
  const kennung = `${nav.userAgentData?.platform ?? ''} ${nav.platform ?? ''}`.toLowerCase();
  if (/mac|iphone|ipad|ipod/.test(kennung)) return true;
  // Manche Browser melden die Plattform leer; dann zeigt der UA-String das Gerät.
  return /iphone|ipad|ipod|macintosh/.test((nav.userAgent ?? '').toLowerCase());
}

interface Name {
  mac: string;
  sonst: string;
}

const TASTEN: Record<string, Name> = {
  mod: { mac: '⌘', sonst: 'Strg' },
  shift: { mac: '⇧', sonst: 'Umschalt' },
  alt: { mac: '⌥', sonst: 'Alt' },
  enter: { mac: '↩', sonst: 'Eingabe' },
  esc: { mac: 'Esc', sonst: 'Esc' },
  escape: { mac: 'Esc', sonst: 'Esc' },
  tab: { mac: '⇥', sonst: 'Tab' },
  space: { mac: 'Leertaste', sonst: 'Leertaste' },
  delete: { mac: '⌫', sonst: 'Entf' },
};

/** Reihenfolge der Zeichen auf dem Mac (Apple: ⌃ ⌥ ⇧ ⌘, dann die Taste). */
const MAC_REIHENFOLGE = ['alt', 'shift', 'mod'];

/** Name einer einzelnen Taste (`mod`, `shift`, `alt`, `enter` …); alles andere kommt gross zurück. */
export function taste(name: string): string {
  const k = name.trim().toLowerCase();
  const eintrag = TASTEN[k];
  if (!eintrag) return name.trim().length === 1 ? name.trim().toUpperCase() : name.trim();
  return istMac() ? eintrag.mac : eintrag.sonst;
}

/**
 * Eine Tastenkombination, wie sie für die Person auf diesem Gerät heisst.
 * Mac: Zeichen ohne Trenner in Apple-Reihenfolge («⇧⌘Z»); sonst mit «+».
 */
export function kuerzel(kombination: string): string {
  const teile = kombination
    .split('+')
    .map((t) => t.trim())
    .filter((t) => t.length > 0);
  // «mod++» o. ä. gibt es nicht; ein leeres Kürzel bleibt leer.
  if (teile.length === 0) return '';
  const letzte = teile[teile.length - 1]!;
  const mods = teile.slice(0, -1).map((t) => t.toLowerCase());
  if (istMac()) {
    const sortiert = [...mods].sort((a, b) => MAC_REIHENFOLGE.indexOf(a) - MAC_REIHENFOLGE.indexOf(b));
    return [...sortiert, letzte].map(taste).join('');
  }
  return [...mods, letzte].map(taste).join('+');
}
