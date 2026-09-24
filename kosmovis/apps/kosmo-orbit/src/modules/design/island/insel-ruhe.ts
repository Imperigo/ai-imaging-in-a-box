/**
 * P-RUHE (v0.9.33) — **die Insel räumt sich selbst weg.**
 *
 * Owner-Entscheid 12.08.2026, wörtlich: «grundsätzlich sollte sie
 * verschwinden nach einer zeit». Anlass war B43 §3: ZEICHNEN links und
 * PROJEKT rechts blieben zusammen offen und deckten die Bühne zu, weil ein
 * offenes Popup den Rückklapp-Timer festhielt (`stufe === 'popup' →
 * return` in `IslandShell.tsx`).
 *
 * **Der Entscheid ist bewusst KEIN Schiedsrichter.** Die naheliegende
 * Lösung — «öffnet eine Insel, schliessen alle anderen» — hätte dem
 * Architekten etwas weggenommen, das er womöglich will: ZEICHNEN und
 * PROJEKT gleichzeitig im Blick. Eine Zeit-Regel nimmt nichts weg, sie
 * räumt nur auf, was liegen geblieben ist.
 *
 * ---
 *
 * ## Die drei Stufen, und warum sie verschieden behandelt werden
 *
 * - **Leiste** (Stufe 1) — sie hat keinen Inhalt, nur Symbole. Wer den
 *   Zeiger wegnimmt, will sie nicht mehr. Eine Sekunde, wie bisher.
 * - **Popup** (Stufe 2) — es trägt Inhalt, den man liest. Es verschwindet
 *   jetzt ebenfalls, aber mit deutlich mehr Luft: der Blick soll zum Plan
 *   und zurück wandern können, ohne dass es dazwischen zuschnappt.
 * - **Fenster** (Stufe 3) — **verschwindet nie von selbst.** Ein Fenster
 *   hat man absichtlich geöffnet; es trägt halb getippte Kommentare,
 *   gesetzte Filter, einen Profil-Manager. Etwas unter den Händen des
 *   Architekten zu schliessen, wäre schlimmer als ein liegen gebliebenes
 *   Fenster — und es widerspräche der Regel, dass nichts Bleibendes ohne
 *   sein Zutun verschwindet.
 *
 * Die Zeit läuft erst, **nachdem der Zeiger die Insel verlassen hat**, und
 * jede Rückkehr stellt sie zurück. Ein Ruhe-Timer, der beim Lesen
 * mitläuft, wäre ein Ärgernis statt einer Hilfe.
 */

export type InselStufe = 'pill' | 'leiste' | 'popup' | 'fenster';

/** Bestand seit v0.8.3 (Owner: «nach 1s»), unverändert. */
export const RUECKKLAPP_LEISTE_MS = 1000;

/**
 * Ruhezeit eines offenen Popups, nachdem der Zeiger es verlassen hat.
 *
 * Acht Sekunden sind eine Wahl, kein Messwert, und darum steht der Grund
 * hier: ein Blick zum Plan und zurück dauert ein bis zwei Sekunden — vier
 * Mal so lang zu warten lässt Raum für ein zweites Hinsehen. Länger, und
 * das Popup steht wieder so lange herum, dass der Owner-Befund
 * zurückkäme.
 */
export const RUHE_POPUP_MS = 8000;

/**
 * Wie lange die Stufe nach dem Verlassen noch steht — `null` heisst «gar
 * nicht», also: der Architekt schliesst selbst.
 */
export function ruheVerzoegerung(stufe: InselStufe): number | null {
  switch (stufe) {
    case 'leiste':
      return RUECKKLAPP_LEISTE_MS;
    case 'popup':
      return RUHE_POPUP_MS;
    case 'fenster':
    case 'pill':
      return null;
  }
}

/** Räumt eine Stufe sich nach dem Verlassen von selbst weg? */
export function raeumtSichSelbst(stufe: InselStufe): boolean {
  return ruheVerzoegerung(stufe) !== null;
}
