/**
 * Entscheide 104/104a (Owner, 20.10.2026; Entwurfsflaeche Blatt 29 «Fortschritt und Vorschau»).
 *
 * Am Render-Knoten waehlt der Schalter «Güte: Vorschau | Voll», wie der KI-Schritt einer Variante
 * rechnet. **Vorgabe ist Vorschau**: schnell, mit z-image-turbo, einem Startwert, weniger Schritten
 * und einem kleineren KI-Bild (so rechnet die Gegenseite eine Vorschau, egal welches Bildwerkzeug
 * am Knoten steht). Die Vorschau wird geprueft (104a) und traegt den Vermerk «Vorschau» am Bild und
 * im Verlauf — die Plakette baut der UI-Worker (`GueteMarke`); sie liest `NodeLauf.guete`, also
 * was das ERGEBNIS meldet (`result.guete`), nicht was bestellt war: eine Gegenseite, die das Feld
 * nicht kennt, rechnet voll, und dann steht auch kein Vermerk da.
 *
 * Die Wahl ist ein flacher Parameter am Knoten (`vis.nodeParametrieren`) — sie ueberlebt ein
 * Neuladen und laesst sich zuruecknehmen. Fehlt er, gilt die Vorgabe Vorschau. Bestellt wird die
 * Guete NUR mit «Variante erzeugen» (Stufe 2); «Grundlage rendern» hat keinen KI-Schritt (der
 * Vertrag weist `vis.guete` mit `vis.skip` ab), und Kosmo und die Insel bestellen wie bisher
 * ohne Feld, also voll — ausser `vis.render` bestellt ausdruecklich eine Guete.
 */

export type Guete = 'vorschau' | 'voll';

/** Der Parameter am Render-Knoten. */
export const GUETE_PARAM = 'guete';

/** Vorgabe am Knoten (Entscheid 104). */
export const GUETE_VORGABE: Guete = 'vorschau';

/** Die Wahl am Knoten; alles ausser ausdruecklich «voll» ist die Vorgabe. */
export function gueteAmKnoten(params: Record<string, unknown> | undefined): Guete {
  return params?.[GUETE_PARAM] === 'voll' ? 'voll' : GUETE_VORGABE;
}

/** Was die zwei Stufen heissen und was sie tun — die Kurzhilfe am Schalter. Keine Zeitangabe:
 *  fuer die Vorschau ist keine gemessen (Ziel ≤ 2 Min, Blatt 29), und eine erfundene Zahl
 *  waere schlimmer als keine. */
export const GUETE_TEXTE: Record<Guete, { readonly name: string; readonly hinweis: string }> = {
  vorschau: {
    name: 'Vorschau',
    hinweis:
      'Vorschau: schnell — immer Z-Image Turbo, ein Startwert, weniger Schritte, kleineres KI-Bild. Wird geprüft; Bild und Verlauf tragen den Vermerk «Vorschau». Gefällt sie, rechnet «Voll» dieselbe Variante gross.',
  },
  voll: {
    name: 'Voll',
    hinweis: 'Voll: das gewählte Bildwerkzeug in voller Grösse — dauert länger.',
  },
};

/** Vorerst: mit angehaengter Skizze rechnet der Heim-PC ohne Guete (Skizzen-Weg); die Owner-Frage
 *  dazu ist offen. Der Schalter steht dann grau mit diesem Satz, und es geht keine Guete hinaus. */
export const GUETE_OHNE_SKIZZE_SATZ = 'Vorschau gilt noch nicht für Skizzen';

/**
 * Die Guete, die ein Ergebnis meldet (`result.guete`), fuer den Lauf (`NodeLauf.guete`). Seit R40
 * (55fa86901) kennt der Vertrag das Feld; gelesen wird es trotzdem ohne den Vertragstyp, damit ein
 * unbekannter Wert nie als Vorschau gilt — fehlt oder unbekannt = voll, nie eine geratene Vorschau.
 */
export function gueteAusErgebnis(r: unknown): Guete | undefined {
  const g = typeof r === 'object' && r !== null ? (r as { guete?: unknown }).guete : undefined;
  return g === 'vorschau' || g === 'voll' ? g : undefined;
}
