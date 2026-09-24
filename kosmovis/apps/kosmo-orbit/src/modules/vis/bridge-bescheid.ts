/**
 * P-BESCHEID (v0.9.33, B43 Teil 2 §10) — **ein 401 ist kein Offline.**
 *
 * Der Home-PC-Worker hat gemessen: die App meldet «RENDER FEHLER — Bridge
 * nicht erreichbar (Offline)», während `curl :8600/health` mit 200
 * antwortet und die Render-Endpunkte 401 geben, weil die Web-Instanz
 * keinen Bridge-Token hat. **Die Meldung schickt den Nutzer die Bridge
 * neustarten, statt den Token zu prüfen.**
 *
 * **Und die Nachprüfung zeigt, warum die App das bisher nicht besser
 * konnte:** sie hat den 401 gar nicht gesehen. Wird eine abgelehnte
 * Antwort vom Browser wegen fehlender CORS-Freigabe verworfen, kommt beim
 * `fetch` kein Status an, sondern ein `TypeError` «Failed to fetch» — für
 * die App nicht von einem toten Server unterscheidbar. Die alte Meldung
 * war also nicht nachlässig, sondern **blind**.
 *
 * **Die Reparatur ist darum keine bessere Formulierung, sondern eine
 * zweite Messung:** `/health` ist tokenfrei und CORS-offen. Antwortet es,
 * während der Render-Ruf scheitert, LÄUFT die Bridge — und der Fehler
 * liegt am Token oder an der CORS-Freigabe der geschützten Route, nicht an
 * der Erreichbarkeit. Antwortet es nicht, ist «offline» richtig.
 *
 * Diese Datei enthält nur den ENTSCHEID als reine Funktion — ohne `fetch`,
 * ohne DOM, damit jeder Fall geprüft werden kann, statt am Gerät
 * nachgestellt zu werden.
 */

/** Was die App über den gescheiterten Ruf weiss, bevor sie urteilt. */
export interface BescheidLage {
  /** Der `fetch` selbst ist geplatzt (Netzfehler ODER vom Browser
   *  verworfene Antwort) — die App hat KEINEN Statuscode gesehen. */
  netzfehler: boolean;
  /** Statuscode, falls die Antwort durchkam (401/403 = Ablehnung). */
  status?: number;
  /** Ergebnis der Gegenprobe auf `/health` (tokenfrei, CORS-offen).
   *  `undefined` = nicht geprüft (dann bleibt es beim alten Urteil). */
  healthErreichbar?: boolean;
  /** Liegt ein Bridge-Token in den Einstellungen? */
  tokenGesetzt: boolean;
  /** Die Bridge-Adresse liegt vermutlich ausserhalb der CSP-Freigabe. */
  cspVerdacht: boolean;
}

export type BescheidArt = 'csp' | 'token-fehlt' | 'token-abgelehnt' | 'offline' | 'roh';

export interface Bescheid {
  art: BescheidArt;
  text: string;
}

/**
 * Der Urteilsspruch über einen gescheiterten Bridge-Ruf.
 *
 * Reihenfolge der Prüfung, und jede Stufe hat einen Grund:
 *
 * 1. **CSP-Verdacht** zuerst — er erklärt den Netzfehler vollständig und
 *    ist die einzige Ursache, die die App an der eigenen Konfiguration
 *    ablesen kann (Bestand seit v0.9.21 P-E).
 * 2. **Ein gesehener 401/403** — eindeutig, kein Raten nötig.
 * 3. **Netzfehler, aber `/health` antwortet** — die Bridge läuft. Das ist
 *    der Fall aus B43 §10, und er war bisher unsichtbar.
 * 4. **Netzfehler und `/health` schweigt** — jetzt ist «offline» eine
 *    Messung statt einer Vermutung.
 * 5. Alles andere bleibt der Rohtext; eine erfundene Erklärung wäre
 *    schlechter als eine ehrliche Unklarheit.
 */
export function bridgeBescheid(lage: BescheidLage, rohtext: string): Bescheid {
  if (lage.netzfehler && lage.cspVerdacht) {
    return {
      art: 'csp',
      text:
        'Bridge-Adresse liegt vermutlich ausserhalb der CSP-Freigabe (nur http auf 8600/8700/11434, ' +
        'IP oder DNS-Name) — Port/Protokoll pruefen oder localhost nutzen. (Offline)',
    };
  }

  if (lage.status === 401 || lage.status === 403) {
    // Nachtrag zu auf-orbit-20260824-06.md Punkt 1: die Token-Pflicht wird
    // NICHT von der App entschieden, sondern von der Umgebungsvariable
    // KOSMO_BRIDGE_TOKEN auf dem Home-PC (`main.py:183,264` — gesetzt =
    // 401 ausser auf /health, leer = keine Pflicht). Wer nur «in den
    // Einstellungen hinterlegen» liest, kennt die halbe Wahrheit: die
    // Variable liesse sich dort ebenso gut ENTFERNEN.
    //
    // «Ein Neustart der Bridge hilft hier nicht» bleibt trotzdem wahr und
    // WOERTLICH stehen — sie gilt fuer einen Neustart OHNE eine der beiden
    // Aenderungen (Token eintragen ODER Variable entfernen). Erst WENN die
    // Variable entfernt wird, liest die Bridge sie beim naechsten Start neu
    // ein — dafuer ist ein Neustart dann Pflicht. Die beiden Saetze
    // widersprechen sich nicht: der eine sagt, was ein blosser Neustart
    // NICHT bewirkt, der andere, was zusaetzlich zum Entfernen noetig ist.
    return lage.tokenGesetzt
      ? {
          art: 'token-abgelehnt',
          text:
            `Die Bridge laeuft, hat den Ruf aber abgelehnt (${lage.status}). Der hinterlegte ` +
            'Bridge-Token passt nicht zur Variable KOSMO_BRIDGE_TOKEN auf dem Home-PC — in den Einstellungen ' +
            'den richtigen Bridge-Token hinterlegen. Ein Neustart der Bridge hilft hier nicht — wer stattdessen ' +
            'KOSMO_BRIDGE_TOKEN auf dem Home-PC entfernt, muss die Bridge danach neu starten.',
        }
      : {
          art: 'token-fehlt',
          text:
            `Die Bridge laeuft, verlangt aber einen Token (${lage.status}), weil auf dem Home-PC die Variable ` +
            'KOSMO_BRIDGE_TOKEN gesetzt ist. In den Einstellungen einen Bridge-Token hinterlegen. Ein Neustart ' +
            'der Bridge hilft hier nicht — wer stattdessen KOSMO_BRIDGE_TOKEN auf dem Home-PC entfernt, muss ' +
            'die Bridge danach neu starten.',
        };
  }

  if (lage.netzfehler && lage.healthErreichbar === true) {
    // Der Fall, den die App bisher als «Offline» ausgegeben hat. Sie kann
    // hier NICHT zwischen «Token fehlt» und «CORS auf der geschuetzten
    // Route» unterscheiden — und sagt das, statt sich fuer eines der
    // beiden zu entscheiden. Eine Vermutung, die als Tatsache auftritt,
    // hat den Owner in v0.9.30 einen Abend gekostet.
    // Dieselbe Aufloesung wie oben bei 401/403, s. Kommentar dort: «Nicht
    // die Bridge neustarten» bleibt WOERTLICH stehen (gilt fuer den Weg
    // «Token pruefen», kein Neustart noetig) — der letzte Satz nennt den
    // zweiten Weg (Variable entfernen), fuer den ein Neustart Pflicht ist.
    return {
      art: lage.tokenGesetzt ? 'token-abgelehnt' : 'token-fehlt',
      text:
        'Die Bridge ANTWORTET (Health-Probe erfolgreich) — der Render-Ruf wurde trotzdem abgewiesen. ' +
        (lage.tokenGesetzt
          ? 'Wahrscheinlich passt der hinterlegte Bridge-Token nicht zur Variable KOSMO_BRIDGE_TOKEN auf dem Home-PC, '
          : 'Wahrscheinlich fehlt der Bridge-Token in den Einstellungen — auf dem Home-PC ist KOSMO_BRIDGE_TOKEN gesetzt, ') +
        'oder die geschuetzte Route gibt keine CORS-Freigabe zurueck. Nicht die Bridge neustarten — den Token pruefen. ' +
        'Wer stattdessen KOSMO_BRIDGE_TOKEN auf dem Home-PC entfernt, muss die Bridge danach neu starten.',
    };
  }

  if (lage.netzfehler) {
    return {
      art: 'offline',
      text:
        lage.healthErreichbar === false
          ? 'Bridge nicht erreichbar — auch die Health-Probe antwortet nicht. Laeuft die HomeStation-Bridge? (Offline)'
          : 'Bridge nicht erreichbar — laeuft die HomeStation-Bridge? (Offline)',
    };
  }

  return { art: 'roh', text: rohtext };
}
